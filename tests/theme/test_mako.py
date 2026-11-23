"""Check Mako candidates without accessing a compositor or the session bus."""

from ctypes import CDLL, c_char_p, c_int, c_uint, c_void_p
from ctypes.util import find_library
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

REPO = Path(__file__).resolve().parents[2]
CARBON = REPO / "dotfiles/.config/carbon"
ENGINE = CARBON / "scripts/generate-theme.py"
THEME = CARBON / "theme.json"
LAYOUTS = {"compact": (320, 112, 8, 1), "segmented": (376, 144, 12, 2)}
MAKO = shutil.which("mako")
PANGO = find_library("pango-1.0")


class MakoThemeTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="carbon-mako-test-")
        self.addCleanup(temporary.cleanup)
        self.stage = Path(temporary.name)

    def generate(self, target, name, *, env=None):
        return subprocess.run(
            [sys.executable, "-B", str(ENGINE), "--input", str(THEME),
             "--target", target, "--output", str(self.stage / name)],
            cwd=self.stage, env=env, capture_output=True, text=True, timeout=10,
        )

    def bundle(self, variant, name=None):
        name = name or variant
        generated = self.generate(f"mako-{variant}", name)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        output = self.stage / name
        self.assertEqual({entry.name for entry in output.iterdir()}, {"config", "preview.html"})
        return output

    def test_deterministic_and_idempotent_artifacts(self):
        for variant in LAYOUTS:
            first = self.bundle(variant)
            metadata = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in first.iterdir()}
            second = self.bundle(variant, f"repeat-{variant}")
            self.bundle(variant)
            for name, identity in metadata.items():
                path = first / name
                self.assertEqual(path.read_bytes(), (second / name).read_bytes())
                self.assertEqual((path.stat().st_ino, path.stat().st_mtime_ns), identity)

    def test_geometry_and_tokens(self):
        for variant, (width, height, spacing, border) in LAYOUTS.items():
            config = (self.bundle(variant) / "config").read_text()
            for name, value in {
                "width": width, "height": height, "margin": spacing, "padding": spacing,
                "border-size": border, "border-radius": 0, "text-color": "#f5f5f5",
                "background-color": "#1b1b1b" if variant == "compact" else "#252525",
            }.items():
                self.assertIn(f"\n{name}={value}\n", config)
            self.assertIn('foreground="#b3b3b3"', config)
            self.assertEqual('size="large"' in config, variant == "segmented")

    def test_only_visual_properties_override_mako_defaults(self):
        allowed = {"font", "background-color", "text-color", "border-color", "progress-color",
                   "width", "height", "padding", "margin", "border-size", "border-radius", "format"}
        for variant in LAYOUTS:
            config = (self.bundle(variant) / "config").read_text()
            lines = config.splitlines()
            keys = {line.split("=", 1)[0] for line in lines if line and not line.startswith(("#", "["))}
            self.assertEqual(keys, allowed)
            self.assertIn("[urgency=critical]\nborder-color=#d6d6d6\n", config)
            self.assertIn('[body="" !grouped !hidden]\nformat=', config)
            self.assertEqual(sum(line.startswith("[") for line in lines), 2)

    def test_protects_active_paths_and_kitty(self):
        configuration = self.stage / "protected"
        kitty = configuration / "kitty"
        kitty.mkdir(parents=True)
        sample = kitty / "kitty.conf"
        sample.write_text("background #202020\n")
        link = self.stage / "alias"
        link.symlink_to(configuration)
        env = {**os.environ, "XDG_CONFIG_HOME": str(configuration)}
        for output in (configuration / "mako", link / "mako", kitty):
            result = self.generate("mako-compact", output, env=env)
            self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(self.generate("kitty", "unused").returncode, 0)
        self.assertEqual(sample.read_text(), "background #202020\n")
        self.assertEqual(list(configuration.iterdir()), [kitty])
        self.assertEqual(list(kitty.iterdir()), [sample])

    def test_previews_are_self_contained_and_label_simulated_cases(self):
        for variant in LAYOUTS:
            html = (self.bundle(variant) / "preview.html").read_text()
            self.assertEqual(html.count('<article class="card'), 5)
            self.assertIn('class="card critical"', html)
            self.assertIn('class="icon"', html)
            self.assertIn("1920 × 1080", html)
            self.assertIn("contenido ficticio", html)
            self.assertIn("título excepcionalmente largo", html)
            self.assertNotRegex(html, r'<script|\bsrc=|\bhref=|\burl\(|@import\b')

    @unittest.skipUnless(MAKO, "Mako no instalado")
    def test_native_parser_before_bus_initialization(self):
        runtime = self.stage / "runtime"
        runtime.mkdir(mode=0o700)
        env = {k: v for k, v in os.environ.items()
               if k not in {"DISPLAY", "WAYLAND_SOCKET", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE"}}
        env.update(LANG="C", LC_ALL="C", XDG_RUNTIME_DIR=str(runtime),
                   WAYLAND_DISPLAY=str(runtime / "absent-wayland"),
                   DBUS_SESSION_BUS_ADDRESS=f"unix:path={runtime / 'absent-bus'}")

        def parse(path):
            return subprocess.run([MAKO, "-c", str(path)], env=env, capture_output=True,
                                  text=True, timeout=5)

        invalid = self.stage / "invalid"
        invalid.write_text("carbon-unknown-option=1\n")
        control = parse(invalid)
        self.assertEqual(control.returncode, 1)
        self.assertIn("Failed to parse config", control.stderr)
        for variant in LAYOUTS:
            result = parse(self.bundle(variant) / "config")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr.strip(), "Failed to connect to user bus: No such file or directory")

    @unittest.skipUnless(PANGO, "Pango no instalado")
    def test_pango_accepts_title_and_body_format_including_nested_markup(self):
        pango = CDLL(PANGO)
        pango.pango_parse_markup.argtypes = (
            c_char_p, c_int, c_uint, c_void_p, c_void_p, c_void_p, c_void_p,
        )
        pango.pango_parse_markup.restype = c_int
        for variant in LAYOUTS:
            config = (self.bundle(variant) / "config").read_text()
            for line in config.splitlines():
                if line.startswith("format="):
                    markup = line.removeprefix("format=").replace(r"\n", "\n")
                    markup = markup.replace("%s", "Informe &amp; ejemplo").replace("%b", "<i>Texto ficticio.</i>")
                    self.assertTrue(pango.pango_parse_markup(markup.encode(), -1, 0, None, None, None, None))
