"""Run only inside the private namespaces prepared by wayland.sh."""
import contextlib
import hashlib
import html
import json
import os
import re
import select
import subprocess
import time
from pathlib import Path

from gi.repository import Gio, GLib

from verify import contrast, png_pixels

root = Path.cwd()
results = root / "results"
fixture = root / "fixtures"
key = "/org/gnome/desktop/interface/color-scheme"
test_socket = Path(os.environ["WAYLAND_DISPLAY"])
if (test_socket.parent != root / "r" or not test_socket.is_socket()
        or Path(f"/run/user/{os.getuid()}/bus").exists()
        or os.environ.get("XDG_CONFIG_HOME") != str(root / "conf")):
    raise RuntimeError("La sonda requiere el bus y socket del entorno Wayland aislado.")

bus = Gio.bus_get_sync(Gio.BusType.SESSION)
portal = "org.freedesktop.portal.Desktop"
portal_path = "/org/freedesktop/portal/desktop"
settings = "org.freedesktop.portal.Settings"
chooser = "org.freedesktop.portal.FileChooser"
request = "org.freedesktop.portal.Request"
no_activate = Gio.DBusCallFlags.NO_AUTO_START
scheme_signals = []


def run(*command):
    return subprocess.check_output(command, text=True, timeout=5).strip()


def portal_code():
    reply = bus.call_sync(portal, portal_path, settings, "Read",
                          GLib.Variant("(ss)", ("org.freedesktop.appearance", "color-scheme")),
                          None, no_activate, 3000, None).unpack()[0]
    if isinstance(reply, GLib.Variant):
        reply = reply.unpack()
    return reply


def record_preference(_bus, _sender, _path, _interface, _name, values, _data):
    namespace, name, code = values.unpack()
    if (namespace, name) == ("org.freedesktop.appearance", "color-scheme"):
        scheme_signals.append(code)


bus.signal_subscribe(portal, settings, "SettingChanged", portal_path, None,
                     Gio.DBusSignalFlags.NONE, record_preference, None)


def wait_for(action, description):
    end = time.monotonic() + 7
    while time.monotonic() < end:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        value = action()
        if value:
            return value
        time.sleep(.10)
    raise RuntimeError(f"Tiempo agotado: {description}. Ventanas: " +
                       str([w.get("title") for w in hypr("clients")]))


def hypr(action):
    return json.loads(run("hyprctl", "-j", action))


monitor = next(x for x in hypr("monitors") if x["name"].startswith("WAYLAND-"))
geometry = [monitor[n] for n in ("width", "height", "scale")]


def capture(name, crop=None):
    assert next([m[n] for n in ("width", "height", "scale")]
                for m in hypr("monitors") if m["name"] == monitor["name"]) == geometry
    flags = ["-g", crop] if crop else ["-o", monitor["name"]]
    run("grim", *flags, str(results / f"{name}.png"))


def active(title):
    return wait_for(lambda: (win if (win := hypr("activewindow")).get("title") == title else None), title)


@contextlib.contextmanager
def process(args, name, *, text=None, env=None, stdout=subprocess.DEVNULL):
    with (results / f"{name}.log").open("w") as log:
        child = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=stdout,
                                 stderr=log, text=True, env=env)
        try:
            if text is not None:
                child.stdin.write(text)
                child.stdin.close()
            yield child
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()


def tell(child, action):
    child.stdin.write(action + "\n")
    child.stdin.flush()


def report(child):
    tell(child, "report")
    if not select.select([child.stdout], [], [], 3)[0]:
        raise RuntimeError("La sonda no devolvió estado GTK.")
    return json.loads(child.stdout.readline())


def native_state(child, toolkit, expected):
    state = report(child)
    assert state["display"] == str(test_socket) and state["surface_scale"] == geometry[2]
    if toolkit == "gtk4" and state["native_scheme"] != expected + 1:
        return None
    if toolkit == "adw" and state["adw_dark"] != bool(expected):
        return None
    return state


def snapshot(child, toolkit, label, code, details=True):
    tell(child, "focus")
    win = active(f"Carbon {toolkit}")
    def focused_state():
        state = native_state(child, toolkit, code)
        return state if state and state["active"] and state["entry_focus"] else None

    state = wait_for(focused_state, f"foco GTK de {toolkit}")
    assert not win["xwayland"], state
    time.sleep(.25)
    capture(f"{label}-{toolkit}")
    if toolkit != "gtk3":
        pixel = png_pixels(results / f"{label}-{toolkit}.png")
        channels = re.findall(r"\d+", state["title"])
        title_color = "#" + "".join(f"{int(x):02x}" for x in channels[:3])
        x, y = win["at"]
        state["header"] = pixel(x + 90, y + 22)
        state["contrast"] = round(contrast(title_color, state["header"]), 2)
    if not details or toolkit == "gtk3":
        return state
    tell(child, "cover")
    active("Carbon auxiliar")
    time.sleep(.25)
    assert not report(child)["active"]
    capture(f"{label}-{toolkit}-unfocused")
    tell(child, "close-cover")
    tell(child, "focus")
    active(f"Carbon {toolkit}")
    tell(child, "menu")
    time.sleep(.28)
    capture(f"{label}-{toolkit}-menu")
    tell(child, "close-menu")
    tell(child, "dialog")
    active("Carbon diálogo")
    time.sleep(.25)
    capture(f"{label}-{toolkit}-dialog")
    tell(child, "close-dialog")
    active(f"Carbon {toolkit}")
    return state


def preference(value, serialized=None):
    if value:
        variant = serialized or {1: "prefer-dark", 2: "prefer-light"}[value]
        run("gsettings", "set", "org.gnome.desktop.interface", "color-scheme", variant)
    else:
        run("gsettings", "reset", "org.gnome.desktop.interface", "color-scheme")
    wait_for(lambda: portal_code() == value and scheme_signals[-1:] == [value],
             f"SettingsChanged del portal con valor {value}")


def fresh_gtk(toolkit, label, code, extras=True):
    with process(["python", "-B", "wayland-probe.py", toolkit], f"{label}-{toolkit}",
                 stdout=subprocess.PIPE) as child:
        state = snapshot(child, toolkit, label, code, details=extras)
        tell(child, "quit")
        child.wait(timeout=3)
        return state


def dynamic_gtk(toolkit):
    with process(["python", "-B", "wayland-probe.py", toolkit], f"dynamic-{toolkit}",
                 stdout=subprocess.PIPE) as child:
        a = snapshot(child, toolkit, "A", 0)
        preference(1)
        b = snapshot(child, toolkit, "B", 1)
        preference(0)
        rollback = snapshot(child, toolkit, "rollback", 0, details=False)
        assert a["pid"] == b["pid"] == rollback["pid"] and child.poll() is None
        assert a["header"] == rollback["header"]
        assert a["contrast"] == rollback["contrast"]
        assert b["contrast"] >= 4.5
        if toolkit == "gtk4":
            assert a["contrast"] < 2 and (a["native_scheme"], b["native_scheme"]) == (1, 2)
        else:
            assert (a["adw_dark"], b["adw_dark"], rollback["adw_dark"]) == (False, True, False)
        tell(child, "quit")
        child.wait(timeout=3)
        return {"A": a, "B": b, "rollback": rollback}


def check_dolphin(label):
    env = dict(os.environ, LD_PRELOAD=str(root / "qt-probe.so"))
    with process([str(root / "dolphin-carbon"), str(fixture)], f"{label}-dolphin", env=env):
        def qt_window():
            window = hypr("activewindow")
            return window if window.get("class") == "org.kde.dolphin" else None

        window = wait_for(qt_window, "Dolphin Wayland")
        path = results / f"{label}-dolphin.log"
        text = wait_for(lambda: (lines if (lines := [
            line for line in path.read_text().splitlines() if line.startswith("CARBON_")
        ]) and len(lines) == 2 else None), "telemetría de Qt")
        assert not window["xwayland"]
        assert "platformtheme=gtk3 GTK_THEME=Adwaita:dark" in text[0]
        assert "qpa=wayland style=fusion" in text[1]
        assert all(x in text[1] for x in ("iconTheme=breeze-dark", "base=#171717",
                                         "text=#ffffff", "inactiveText=#ffffff"))
        capture(f"{label}-dolphin")
        return text


def check_wofi(label):
    for mode, text in (("drun", None), ("dmenu", "1\tDocumento ficticio\n2\tCarpeta de prueba\n")):
        command = (["wofi", "--show", "drun", "--search", "Carbon aplicación ficticia"]
                   if mode == "drun" else ["wofi", "--dmenu"])
        with process(command, f"{label}-wofi-{mode}", text=text):
            wait_for(lambda: "wofi" in run("hyprctl", "layers"), "superficie Wayland de Wofi")
            time.sleep(.3)
            capture(f"{label}-wofi-{mode}")
        wait_for(lambda: "wofi" not in run("hyprctl", "layers"), "cierre de Wofi")


def check_chooser(label):
    options = {
        "handle_token": GLib.Variant("s", f"carbon_{label}"),
        "current_folder": GLib.Variant("ay", os.fsencode(fixture) + b"\0"),
        "modal": GLib.Variant("b", False),
    }
    handle, = bus.call_sync(portal, portal_path, chooser, "OpenFile",
                           GLib.Variant("(ssa{sv})", ("", "Carbon selector", options)),
                           None, no_activate, 4000, None).unpack()
    try:
        window = active("Carbon selector")
        assert not window["xwayland"]
        time.sleep(.5)
        x, y = window["at"]
        width, height = window["size"]
        # The sidebar can display the account label. Capture only the main pane.
        capture(f"{label}-filechooser", f"{x + 170},{y} {width - 170}x{height}")
    finally:
        bus.call_sync(portal, handle, request, "Close", None, None, no_activate, 3000, None)
    wait_for(lambda: all(w.get("title") != "Carbon selector" for w in hypr("clients")),
             "cancelación de FileChooser")


def gallery(state):
    pairs = (
        ("GTK 4 · ventana existente", "A-gtk4", "B-gtk4"),
        ("GTK 4 · desenfocada", "A-gtk4-unfocused", "B-gtk4-unfocused"),
        ("GTK 4 · menú", "A-gtk4-menu", "B-gtk4-menu"),
        ("GTK 4 · diálogo", "A-gtk4-dialog", "B-gtk4-dialog"),
        ("libadwaita · ventana existente", "A-adw", "B-adw"),
        ("libadwaita · desenfocada", "A-adw-unfocused", "B-adw-unfocused"),
        ("libadwaita · menú", "A-adw-menu", "B-adw-menu"),
        ("libadwaita · diálogo", "A-adw-dialog", "B-adw-dialog"),
        ("GTK 3", "A-new-gtk3", "B-new-gtk3"),
        ("FileChooser · GTK 3", "A-filechooser", "B-filechooser"),
        ("Dolphin · Qt 6 y KDE Frameworks 6", "A-dolphin", "B-dolphin"),
        ("Wofi Segmented · aplicaciones", "A-wofi-drun", "B-wofi-drun"),
        ("Wofi Segmented · historial ficticio", "A-wofi-dmenu", "B-wofi-dmenu"),
        ("Rollback · GTK 4 y libadwaita", "rollback-gtk4", "rollback-adw"),
    )
    width, height, scale = state["geometry"]
    content = ["""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carbon · Validación Wayland</title>
<style>
body{background:#121212;color:#f5f5f5;font:16px/1.5 'Noto Sans',sans-serif;max-width:1400px;margin:2rem auto;padding:0 1rem}
section{border-top:1px solid #333333;margin-top:2rem}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}
figure{margin:0;background:#1b1b1b;border:1px solid #333333}img{display:block;width:100%;height:auto}figcaption{padding:.6rem 1rem}
a:focus-visible{outline:2px solid #d6d6d6}
</style><h1>Carbon · Validación Wayland</h1>
<p>Capturas del compositor Hyprland anidado. Datos ficticios. Pulsa una imagen para abrirla a tamaño original.</p>""",
        f"<p>Salida de {width} × {height} px, escala {scale:g}. FileChooser muestra solo el panel principal.</p>"]
    for title, left, right in pairs:
        content.append(f'<section><h2>{html.escape(title)}</h2><div class="grid">')
        labels = ("A · sin preferencia", "B · prefer-dark") if left.startswith("A-") else ("GTK 4", "libadwaita")
        for name, label in zip((left, right), labels):
            filename = f"{name}.png"
            with (results / filename).open("rb") as image:
                assert image.read(8) == b"\x89PNG\r\n\x1a\n"
            content.append(f'<figure><a href="{filename}"><img src="{filename}" alt="{label}" loading="lazy"></a>'
                           f'<figcaption>{label}</figcaption></figure>')
        content.append("</div></section>")
    (results / "comparacion.html").write_text("\n".join(content) + "</html>\n", encoding="utf-8")


before = run("dconf", "read", key)
assert before == "" and portal_code() == 0
state = {toolkit: dynamic_gtk(toolkit) for toolkit in ("gtk4", "adw")}
state["fresh"] = {}
for label, code in (("A", 0), ("B", 1)):
    if label == "B":
        preference(1)
    state["fresh"][label] = {
        toolkit: fresh_gtk(toolkit, label + "-new", code, extras=False)
        for toolkit in ("gtk4", "adw", "gtk3")
    }
    state["fresh"][label]["dolphin"] = check_dolphin(label)
    check_wofi(label)
    check_chooser(label)

preference(0)
assert run("dconf", "read", key) == before and portal_code() == 0
# The absent and explicit rollback paths are distinct.
preference(2)
explicit = run("dconf", "read", key)
assert explicit == "'prefer-light'"
preference(1)
preference(2, explicit)
assert run("dconf", "read", key) == explicit and portal_code() == 2
preference(0)
assert run("dconf", "read", key) == before and portal_code() == 0
assert state["fresh"]["A"]["dolphin"] == state["fresh"]["B"]["dolphin"]
for toolkit in ("gtk4", "adw"):
    for label in ("A", "B"):
        assert state["fresh"][label][toolkit]["contrast"] == state[toolkit][label]["contrast"]
for toolkit in ("gtk4", "adw", "gtk3"):
    assert state["fresh"]["A"][toolkit]["font"] == state["fresh"]["B"][toolkit]["font"]

state["geometry"] = geometry
state["signals"] = scheme_signals
for name in ("gtk-3.0/settings.ini", "gtk-3.0/gtk.css", "gtk-4.0/settings.ini", "gtk-4.0/gtk.css"):
    state.setdefault("css", {})[name] = hashlib.sha256((root / "conf" / name).read_bytes()).hexdigest()
(results / "validation.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
gallery(state)
print("Wayland A/B, ventanas nuevas y existentes, FileChooser y rollback verificados.")
