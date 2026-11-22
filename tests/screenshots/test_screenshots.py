"""Exercise the Bash entry point without accessing the desktop."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "dotfiles/.local/bin/save-screenshot.sh"
TIMESTAMP = "2026-11-22_15-00-00"
PAYLOAD = b"fixture: simulated PNG bytes"
MOCK = r"""#!/bin/bash
command=${0##*/}
printf '%s\n' "$command" >> "$CALLS"
case "$command" in
    slurp)
        printf '%s' "${SLURP_DIAGNOSTIC-}" >&2
        printf '%s' "${GEOMETRY--12,3 40x50}"
        exit "${SLURP_STATUS:-0}"
        ;;
    grim)
        [[ $# == 5 && $1 == -g && $2 == '-12,3 40x50' &&
           $3 == -t && $4 == png && $5 == - ]] || exit 90
        if [[ ${GRIM_EMPTY:-0} == 1 ]]; then
            exit
        fi
        printf 'fixture: simulated PNG bytes'
        exit "${GRIM_STATUS:-0}"
        ;;
    wl-copy)
        [[ $# == 2 && $1 == --type && $2 == image/png ]] || exit 91
        cat > "$CLIPBOARD"
        exit "${COPY_STATUS:-0}"
        ;;
    notify-send)
        printf '%s\n' "$@" > "$NOTIFICATION"
        exit "${NOTIFY_STATUS:-0}"
        ;;
    date)
        printf '2026-11-22_15-00-00\n'
        ;;
esac
"""


class Screenshots(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="carbon screenshots ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.destination = self.home / "imagenes/screenshots"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls"
        self.clipboard = self.root / "clipboard"
        self.notification = self.root / "notification"
        self.bash = shutil.which("bash")
        for name in ("mkdir", "mktemp", "ln", "rm", "cat"):
            (self.bin / name).symlink_to(shutil.which(name))
        for name in ("slurp", "grim", "wl-copy", "notify-send", "date"):
            tool = self.bin / name
            tool.write_text(MOCK)
            tool.chmod(0o700)

    def capture(self, **overrides):
        env = dict(
            HOME=str(self.home),
            PATH=str(self.bin),
            CALLS=str(self.calls),
            CLIPBOARD=str(self.clipboard),
            NOTIFICATION=str(self.notification),
            **overrides,
        )
        result = subprocess.run(
            [self.bash, str(SCRIPT)], env=env, capture_output=True, text=True, timeout=10
        )
        self.assertEqual(list(self.destination.glob(".capture.*")), [])
        return result

    def call_names(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def assert_saved(self, filename=f"{TIMESTAMP}.png"):
        path = self.destination / filename
        self.assertEqual(path.read_bytes(), PAYLOAD)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        return path

    def test_success_with_spaces_and_signed_coordinates(self):
        result = self.capture()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.call_names(), ["slurp", "date", "grim", "wl-copy", "notify-send"])
        image = self.assert_saved()
        self.assertEqual(self.clipboard.read_bytes(), PAYLOAD)
        self.assertIn(f"--icon={image}", self.notification.read_text())

    def test_escape_is_silent(self):
        result = self.capture(GEOMETRY="", SLURP_STATUS="1", SLURP_DIAGNOSTIC="selection cancelled\n")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(self.call_names(), ["slurp"])
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.clipboard.exists())

    def test_slurp_failure_with_same_exit_status(self):
        result = self.capture(GEOMETRY="", SLURP_STATUS="1", SLURP_DIAGNOSTIC="failed to create display\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed to create display", result.stderr)
        self.assertNotIn("grim", self.call_names())

    def test_invalid_geometry(self):
        for geometry in ("", "bad", "0,0 0x2", "0,0 2x0", "0,0 -2x1"):
            with self.subTest(geometry=geometry):
                result = self.capture(GEOMETRY=geometry)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("geometría inválida", result.stderr)
        self.assertNotIn("grim", self.call_names())
        self.assertFalse(self.destination.exists())

    def test_grim_error_removes_partial_file(self):
        result = self.capture(GRIM_STATUS="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Grim", result.stderr)
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertFalse(self.clipboard.exists())

    def test_empty_output_is_rejected(self):
        result = self.capture(GRIM_EMPTY="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertFalse(self.clipboard.exists())

    def test_unavailable_directory(self):
        self.destination.parent.mkdir()
        self.destination.touch()
        result = self.capture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("directorio de capturas", result.stderr)
        self.assertNotIn("grim", self.call_names())

    def test_write_error_reserving_temporary_space(self):
        tool = self.bin / "mktemp"
        tool.unlink()
        tool.write_text("#!/bin/bash\nexit 1\n")
        tool.chmod(0o700)
        result = self.capture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("directorio temporal", result.stderr)
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertNotIn("grim", self.call_names())

    def test_write_error_after_partial_output(self):
        tool = self.bin / "cat"
        tool.unlink()
        tool.write_text("#!/bin/bash\nprintf partial\nexit 1\n")
        tool.chmod(0o700)
        result = self.capture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escribir la captura", result.stderr)
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertFalse(self.clipboard.exists())

    def test_clipboard_failure_preserves_capture(self):
        result = self.capture(COPY_STATUS="1")
        self.assertNotEqual(result.returncode, 0)
        self.assert_saved()
        self.assertIn("no se pudo copiar", result.stderr)
        message = self.notification.read_text()
        self.assertIn("no se pudo copiar", message)
        self.assertNotIn("Guardada y copiada", message)

    def test_notification_failure_preserves_capture_and_copy(self):
        result = self.capture(NOTIFY_STATUS="1")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Falló la notificación", result.stderr)
        self.assert_saved()
        self.assertEqual(self.clipboard.read_bytes(), PAYLOAD)

    def test_missing_notifier_is_nonfatal(self):
        (self.bin / "notify-send").unlink()
        result = self.capture()
        self.assertEqual(result.returncode, 0)
        self.assertIn("Falta notify-send", result.stderr)
        self.assert_saved()
        self.assertEqual(self.clipboard.read_bytes(), PAYLOAD)

    def test_existing_file_and_symlink_are_untouched(self):
        self.destination.mkdir(parents=True)
        old = self.destination / f"{TIMESTAMP}.png"
        old.write_bytes(b"previous capture")
        link = self.destination / f"{TIMESTAMP}-1.png"
        link.symlink_to(self.root / "missing")
        self.assertEqual(self.capture().returncode, 0)
        self.assertEqual(old.read_bytes(), b"previous capture")
        self.assertEqual(link.readlink(), self.root / "missing")
        self.assert_saved(f"{TIMESTAMP}-2.png")

    def test_missing_critical_dependencies(self):
        for dependency in ("slurp", "grim", "wl-copy"):
            with self.subTest(dependency=dependency):
                mock = self.bin / dependency
                parked = mock.with_suffix(".parked")
                mock.rename(parked)
                try:
                    result = self.capture()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"Falta la dependencia {dependency}", result.stderr)
                finally:
                    parked.rename(mock)
        self.assertNotIn("slurp", self.call_names())
        self.assertFalse(self.destination.exists())

    def test_successive_captures_same_second(self):
        self.assertEqual(self.capture().returncode, 0)
        original = self.assert_saved()
        first_inode = original.stat().st_ino
        self.assertEqual(self.capture().returncode, 0)
        self.assertEqual(original.stat().st_ino, first_inode)
        self.assert_saved()
        self.assert_saved(f"{TIMESTAMP}-1.png")


if __name__ == "__main__":
    unittest.main()
