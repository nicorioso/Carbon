"""Run the shell scripts with a closed PATH and synthetic inputs."""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

BIN = Path(__file__).resolve().parents[2] / "dotfiles/.local/bin"
ROW = "7\tfixture"
PAYLOAD = b"fixture\x00\n\n"
MOCK = f"#!{sys.executable}\n" + r'''
import json
import os
from pathlib import Path
import sys

env = os.environ
tool = Path(sys.argv[0]).name
args = sys.argv[1:]
with Path(env["CALLS"]).open("a") as log:
    log.write(json.dumps([tool, *args]) + "\n")

if tool == "hyprctl":
    if args == ["-j", "activeworkspace"]:
        print(env.get("WORKSPACE", '{"id": 4, "type": "normal"}'))
        sys.exit(int(env.get("IPC_STATUS", "0")))
    print(env.get("DISPATCH_OUTPUT", "ok"))
    sys.exit(int(env.get("DISPATCH_STATUS", "0")))
if tool == "cliphist":
    if args == ["list"]:
        print(env.get("HISTORY", "7\tfixture"))
        sys.exit(int(env.get("LIST_STATUS", "0")))
    assert args == ["decode"] and sys.stdin.read() == "7\tfixture\n"
    if env.get("DECODE_EMPTY") != "1":
        sys.stdout.buffer.write(b"fixture\x00\n\n")
    sys.exit(int(env.get("DECODE_STATUS", "0")))
if tool in ("wofi", "rofi"):
    data = sys.stdin.read()
    if tool == "wofi":
        assert args == ["--dmenu"] and data == "7\tfixture\n"
    else:
        assert args == ["-no-config", "-dmenu", "-theme",
                        str(Path(env["HOME"]) / ".config/rofi/power-menu.rasi"),
                        "-markup-rows", "-no-custom", "-format", "i"]
        rows = [row.rsplit("</span>   ", 1)[1] for row in data.splitlines()]
        assert rows == ["Apagar", "Reiniciar", "Suspender", "Cerrar sesión"], rows
    print(env.get("SELECTION", "7\tfixture" if tool == "wofi" else "0"))
    print(env.get("MENU_ERROR", ""), end="", file=sys.stderr)
    sys.exit(int(env.get("MENU_STATUS", "0")))
if tool == "wl-copy":
    assert not args
    Path(env["COPIED"]).write_bytes(sys.stdin.buffer.read())
    sys.exit(int(env.get("COPY_STATUS", "0")))
if tool == "dolphin":
    assert env["QT_QPA_PLATFORMTHEME"] == "gtk3"
    assert env["GTK_THEME"] == "Adwaita:dark"
    sys.exit(int(env.get("DOLPHIN_STATUS", "0")))
assert tool in ("systemctl", "hyprshutdown"), tool
'''


class Interactions(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="carbon interactions ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "bin"
        self.path.mkdir()
        self.calls = self.root / "calls"
        self.copied = self.root / "copied"
        self.home = self.root / "home"
        theme = self.home / ".config/rofi/power-menu.rasi"
        theme.parent.mkdir(parents=True)
        theme.touch()
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        for command in ("mktemp", "unlink", "python3"):
            (self.path / command).symlink_to(shutil.which(command))
        for command in ("hyprctl", "cliphist", "wofi", "wl-copy", "rofi", "systemctl",
                        "hyprshutdown", "dolphin"):
            file = self.path / command
            file.write_text(MOCK)
            file.chmod(0o700)

    def run_script(self, name, *args, **options):
        self.calls.write_text("")
        if self.copied.exists():
            self.copied.unlink()
        path = BIN / name
        interpreter = "/bin/bash" if path.read_bytes().startswith(b"#!/usr/bin/env bash") else "/bin/sh"
        env = {
            "PATH": str(self.path),
            "HOME": str(self.home),
            "XDG_RUNTIME_DIR": str(self.runtime),
            "CALLS": str(self.calls),
            "COPIED": str(self.copied),
            **options,
        }
        result = subprocess.run(
            [interpreter, str(path), *args], env=env, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(list(self.runtime.iterdir()), [])
        return result

    def log(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()]

    def workspace(self, direction="next", **options):
        return self.run_script("change-workspace-relative.sh", direction, **options)

    def clipboard(self, **options):
        return self.run_script("cliphist-menu.sh", **options)

    def power(self, **options):
        return self.run_script("power-menu.sh", **options)

    def test_workspace_numeric_dispatch_and_wrap(self):
        for active, direction, target in ((4, "next", 5), (4, "previous", 3),
                                          (1, "previous", 10), (10, "next", 1)):
            with self.subTest(active=active, direction=direction):
                result = self.workspace(direction, WORKSPACE=json.dumps({"id": active}))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.log(), [["hyprctl", "-j", "activeworkspace"],
                                              ["hyprctl", "dispatch", f"hl.dsp.focus({{ workspace = {target} }})"]])

    def test_workspace_rejects_invalid_and_special_values(self):
        for data in ("", 'junk {"id": 4}', '[{"id": 4}]', '{"nested": {"id": 4}}',
                     '{"id": "4"}', '{"id": true}', '{"id": 4.0}', '{"id": 0}',
                     '{"id": 11}', '{"id": -99, "type": "special"}',
                     '{"id": 4, "type": "special"}'):
            with self.subTest(data=data):
                result = self.workspace(WORKSPACE=data)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("escritorio numerado", result.stderr)
                self.assertEqual(self.log(), [["hyprctl", "-j", "activeworkspace"]])

    def test_workspace_ipc_failure_and_dispatch_rejection(self):
        result = self.workspace(IPC_STATUS="2")
        self.assertIn("No se pudo consultar", result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.log()), 1)
        for options in ({"DISPATCH_STATUS": "2"}, {"DISPATCH_OUTPUT": "rejected"}):
            with self.subTest(options=options):
                result = self.workspace(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(self.log()), 2)

    def test_workspace_rejects_unknown_direction_before_ipc(self):
        self.assertEqual(self.workspace("skip").returncode, 2)
        self.assertEqual(self.log(), [])

    def test_clipboard_selection_preserves_bytes(self):
        result = self.clipboard(SELECTION=ROW)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.copied.read_bytes(), PAYLOAD)
        self.assertEqual(self.log(), [["cliphist", "list"], ["wofi", "--dmenu"],
                                      ["cliphist", "decode"], ["wl-copy"]])

    def test_clipboard_cancel_or_empty_selection(self):
        for status in ("0", "1"):
            with self.subTest(status=status):
                result = self.clipboard(SELECTION="", MENU_STATUS=status)
                self.assertEqual((result.returncode, result.stderr), (0, ""))
                self.assertEqual(self.log(), [["cliphist", "list"], ["wofi", "--dmenu"]])
                self.assertFalse(self.copied.exists())

    def test_clipboard_empty_or_failed_history(self):
        for options, expected in (({"HISTORY": ""}, 0), ({"LIST_STATUS": "1"}, 1)):
            with self.subTest(options=options):
                self.assertEqual(self.clipboard(**options).returncode, expected)
                self.assertEqual(self.log(), [["cliphist", "list"]])

    def test_clipboard_wofi_failure_and_unlisted_selection(self):
        for options in ({"MENU_STATUS": "2"}, {"SELECTION": "99\tother"},
                        {"SELECTION": ROW + "\n99\tother"}):
            with self.subTest(options=options):
                result = self.clipboard(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.log(), [["cliphist", "list"], ["wofi", "--dmenu"]])
                self.assertFalse(self.copied.exists())

    def test_clipboard_status_one_preserves_wofi_diagnostic(self):
        result = self.clipboard(MENU_STATUS="1", SELECTION="", MENU_ERROR="mock display failure\n")
        self.assertIn("mock display failure", result.stderr)
        self.assertNotIn(["cliphist", "decode"], self.log())
        self.assertFalse(self.copied.exists())

    def test_clipboard_rejects_failed_or_empty_decode(self):
        for options in ({"DECODE_STATUS": "1"}, {"DECODE_EMPTY": "1"}):
            with self.subTest(options=options):
                result = self.clipboard(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.log()[-1], ["cliphist", "decode"])
                self.assertFalse(self.copied.exists())

    def test_clipboard_copy_failure(self):
        result = self.clipboard(COPY_STATUS="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No se pudo copiar", result.stderr)

    def test_power_escape_empty_and_unknown(self):
        for selection, status, expected in (("", "1", 0), ("", "0", 0),
                                            ("4", "0", 2), ("0\n1", "0", 2),
                                            ("0", "1", 1), ("0", "2", 2)):
            with self.subTest(selection=selection, status=status):
                result = self.power(SELECTION=selection, MENU_STATUS=status)
                self.assertEqual(result.returncode, expected)
                self.assertEqual([call[0] for call in self.log()], ["rofi"])

    def test_power_four_actions_and_logout_fallback(self):
        for index, action in enumerate(("poweroff", "reboot", "suspend")):
            with self.subTest(index=index):
                self.assertEqual(self.power(SELECTION=str(index)).returncode, 0)
                self.assertEqual(self.log()[-1], ["systemctl", action])
        self.assertEqual(self.power(SELECTION="3").returncode, 0)
        self.assertEqual(self.log()[-1], ["hyprshutdown"])
        (self.path / "hyprshutdown").unlink()
        self.assertEqual(self.power(SELECTION="3").returncode, 0)
        self.assertEqual(self.log()[-1], ["hyprctl", "dispatch", "hl.dsp.exit()"])

    def test_power_missing_dependencies_and_theme(self):
        (self.path / "systemctl").unlink()
        self.assertEqual(self.power(SELECTION="0").returncode, 127)
        self.assertEqual([call[0] for call in self.log()], ["rofi"])
        (self.home / ".config/rofi/power-menu.rasi").unlink()
        self.assertIn("tema Rofi", self.power().stderr)
        self.assertEqual(self.log(), [])
        (self.path / "rofi").unlink()
        self.assertEqual(self.power().returncode, 127)
        self.assertEqual(self.log(), [])

    def dolphin(self, *args, **options):
        content = (BIN / "dolphin-carbon").read_text()
        original = "exec /usr/bin/dolphin "
        self.assertEqual(content.count(original), 1)
        # Bind the fixed system path to the fake executable in a temporary copy.
        wrapper = self.root / "dolphin-carbon"
        wrapper.write_text(content.replace(original, "exec " + shlex.quote(str(self.path / "dolphin")) + " "))
        self.calls.write_text("")
        return subprocess.run(
            ["/bin/sh", str(wrapper), *args],
            env={"PATH": str(self.path), "CALLS": str(self.calls), **options},
            capture_output=True, text=True, timeout=10,
        )

    def test_dolphin_start_and_argument_boundaries(self):
        result = self.dolphin("--new-window", "/tmp/a folder", "file:///tmp/another path")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log(), [["dolphin", "--new-window", "/tmp/a folder", "file:///tmp/another path"]])

    def test_dolphin_exit_status_and_missing_executable(self):
        self.assertEqual(self.dolphin(DOLPHIN_STATUS="17").returncode, 17)
        (self.path / "dolphin").unlink()
        self.assertEqual(self.dolphin().returncode, 127)
        self.assertEqual(self.log(), [])


if __name__ == "__main__":
    unittest.main()
