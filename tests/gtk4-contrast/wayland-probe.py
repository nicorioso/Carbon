"""Report live toolkit state from a native test window on private Wayland."""
import json
import os
import sys

import gi

toolkit = sys.argv[1]
modern = toolkit != "gtk3"
gi.require_version("Gtk", "4.0" if modern else "3.0")
gi.require_version("Gdk", "4.0" if modern else "3.0")
from gi.repository import Gdk, GLib, Gtk

if toolkit == "adw":
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    Adw.init()
else:
    Gtk.init() if modern else Gtk.init([])

settings = Gtk.Settings.get_default()
style = Adw.StyleManager.get_default() if toolkit == "adw" else None
display = Gdk.Display.get_default()
if display.get_name() != os.environ["WAYLAND_DISPLAY"] or "GTK_THEME" in os.environ:
    raise RuntimeError("La sonda debe usar el socket privado y no heredar GTK_THEME.")

win = Adw.Window() if style else Gtk.Window()
win.set_title(f"Carbon {toolkit}")
win.set_default_size(660, 410)
header = Adw.HeaderBar() if style else Gtk.HeaderBar()
title = Gtk.Label(label="Carbon · Título de prueba")
if modern:
    title.add_css_class("title")
    header.set_title_widget(title)
else:
    header.set_custom_title(title)
    header.set_title(f"Carbon {toolkit}")
    header.set_show_close_button(True)
body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=16, margin_bottom=16,
               margin_start=20, margin_end=20, spacing=10)


def add(container, child):
    container.append(child) if modern else container.pack_start(child, False, False, 0)


def label(text, dim=False):
    widget = Gtk.Label(label=text, xalign=0)
    if dim:
        if modern:
            widget.add_css_class("dim-label")
        else:
            widget.get_style_context().add_class("dim-label")
    return widget


heading = label("Texto principal")
secondary = label("Texto secundario · datos ficticios", dim=True)
entry = Gtk.Entry()
entry.set_text("Texto seleccionado")
button = Gtk.Button(label="Acción disponible")
disabled = Gtk.Button(label="Acción deshabilitada", sensitive=False)
symbol = (Gtk.Image.new_from_icon_name("folder-symbolic") if modern
          else Gtk.Image.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON))
actions = Gtk.Box(spacing=8)
menu = Gtk.MenuButton()
if modern:
    menu.set_label("Menú")
    popover = Gtk.Popover()
    popover.set_child(Gtk.Button(label="Opción de prueba"))
    menu.set_popover(popover)
for widget in (symbol, button, disabled, menu) if modern else (symbol, button, disabled):
    add(actions, widget)
listing = Gtk.ListBox()
for row in ("01 · Documento ficticio", "02 · Carpeta de prueba"):
    widget = label(row)
    widget.set_margin_top(6)
    widget.set_margin_bottom(6)
    listing.append(widget) if modern else listing.add(widget)
for widget in (heading, secondary, entry, actions, listing):
    add(body, widget)

if style:
    layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    for widget in (header, body):
        add(layout, widget)
    win.set_content(layout)
elif modern:
    win.set_titlebar(header)
    win.set_child(body)
else:
    win.set_titlebar(header)
    win.add(body)
    win.set_title(f"Carbon {toolkit}")
    win.show_all()
win.present()
listing.select_row(listing.get_row_at_index(0))
entry.grab_focus()
entry.select_region(0, 5)

cover = None
dialog = None


def report():
    color = (title.get_color() if modern
             else title.get_style_context().get_color(title.get_state_flags()))
    focus = win.get_focus()
    scheme = settings.get_property("gtk-interface-color-scheme") if modern else None
    print(json.dumps({
        "pid": os.getpid(), "display": display.get_name(), "active": win.is_active(),
        "surface_scale": win.get_scale_factor(), "entry_focus": focus is not None and (focus == entry or focus.is_ancestor(entry)),
        "native_scheme": int(scheme) if modern else None,
        "adw_dark": style.get_dark() if style else None,
        "adw_policy": int(style.get_color_scheme()) if style else None,
        "theme": settings.get_property("gtk-theme-name"),
        "font": settings.get_property("gtk-font-name"), "title": color.to_string(),
    }), flush=True)


def handle(command):
    global cover, dialog
    if command == "report":
        report()
    elif command == "focus":
        win.present()
        entry.grab_focus()
        entry.select_region(0, 5)
    elif command == "cover":
        cover = Gtk.Window(title="Carbon auxiliar", default_width=330, default_height=160)
        cover.set_transient_for(win)
        message = Gtk.Label(label="Ventana ficticia para comprobar el desenfoque")
        cover.set_child(message) if modern else cover.add(message)
        cover.present() if modern else cover.show_all()
    elif command == "close-cover" and cover is not None:
        cover.destroy()
        cover = None
    elif command == "menu" and modern:
        menu.popup()
    elif command == "close-menu" and modern:
        menu.popdown()
    elif command == "dialog" and modern:
        dialog = Gtk.Dialog(title="Carbon diálogo", transient_for=win, modal=True)
        dialog.get_content_area().append(Gtk.Label(label="Diálogo ficticio de contraste"))
        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.present()
    elif command == "close-dialog" and dialog is not None:
        dialog.destroy()
        dialog = None
    elif command == "quit":
        loop.quit()
        return False
    return True


pending = b""


def receive(source, _condition):
    global pending
    chunk = os.read(source.fileno(), 4096)
    if not chunk:
        loop.quit()
        return False
    pending += chunk
    while b"\n" in pending:
        message, pending = pending.split(b"\n", 1)
        if not handle(message.decode()):
            return False
    return True


loop = GLib.MainLoop()
GLib.io_add_watch(sys.stdin, GLib.PRIORITY_DEFAULT, GLib.IO_IN | GLib.IO_HUP, receive)
loop.run()
