"""Verify Wofi theme candidates and mockups without contacting the desktop."""

from ctypes import CDLL, CFUNCTYPE, c_char_p, c_int, c_ulong, c_void_p
from ctypes.util import find_library
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

REPO = Path(__file__).resolve().parents[2]
CARBON = REPO / "dotfiles/.config/carbon"
ENGINE = CARBON / "scripts/generate-theme.py"
THEME = CARBON / "theme.json"
VARIANTS = {"compact": ("440", "324"), "segmented": ("540", "396")}
GTK3 = find_library("gtk-3")


class WofiThemeTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="carbon-wofi-test-")
        self.addCleanup(temporary.cleanup)
        self.stage = Path(temporary.name)

    def generate(self, variant, name, *, theme=THEME, env=None):
        return subprocess.run(
            [sys.executable, "-B", str(ENGINE), "--input", str(theme),
             "--target", f"wofi-{variant}", "--output", str(self.stage / name)],
            cwd=self.stage, capture_output=True, text=True, env=env, timeout=10,
        )

    def bundle(self, variant, name=None):
        name = name or variant
        result = self.generate(variant, name)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.stage / name
        self.assertEqual({item.name for item in path.iterdir()}, {"config", "style.css", "preview.html"})
        return path

    def test_geometry_and_presentation_only_config(self):
        for variant, (width, height) in VARIANTS.items():
            config = dict(line.split("=", 1) for line in
                          (self.bundle(variant) / "config").read_text().splitlines() if line)
            self.assertEqual(config, {
                "width": width, "height": height, "location": "center", "prompt": "Buscar",
                "allow_images": "true", "image_size": "24", "line_wrap": "word_char",
            })

    def test_documented_selectors_and_distinct_layouts(self):
        allowed = {"window", "outer-box", "input", "scroll", "entry", "text", "img"}
        styles = {v: (self.bundle(v) / "style.css").read_text() for v in VARIANTS}
        for css in styles.values():
            selectors = re.findall(r"([^{}]+)\{[^{}]*\}", css)
            self.assertEqual(set(re.findall(r"#([a-z-]+)", " ".join(selectors))), allowed)
            self.assertIn("#entry:hover", selectors_text := " ".join(selectors))
            self.assertIn("#entry:selected", selectors_text)
            self.assertIn("#input:focus", selectors_text)
            self.assertIn("border-radius: 0px;", css)
        self.assertIn("background-color: #121212;", styles["compact"].split("#input {")[1].split("}")[0])
        self.assertIn("background-color: #252525;", styles["segmented"].split("#input {")[1].split("}")[0])
        self.assertNotEqual(styles["compact"], styles["segmented"])

    def test_deterministic_and_idempotent_bundles(self):
        for variant in VARIANTS:
            first = self.bundle(variant)
            before = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in first.iterdir()}
            second = self.bundle(variant, f"again-{variant}")
            self.bundle(variant)
            for filename, identity in before.items():
                artifact = first / filename
                self.assertEqual((artifact.stat().st_ino, artifact.stat().st_mtime_ns), identity)
                self.assertEqual(artifact.read_bytes(), (second / filename).read_bytes())

    def test_shared_token_validation_and_html_font_escaping(self):
        theme = json.loads(THEME.read_text())
        altered = self.stage / "theme.json"
        theme["typography"]["family"] = 'Family </style><script>invalid</script>'
        altered.write_text(json.dumps(theme))
        result = self.generate("compact", "escaped", theme=altered)
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = (self.stage / "escaped/preview.html").read_text()
        self.assertNotIn("</style><script>invalid", preview)
        self.assertIn(r"Family \3c /style>", preview)

        theme["colors"]["background"] = "invalid"
        altered.write_text(json.dumps(theme))
        result = self.generate("segmented", "invalid", theme=altered)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("colors.background", result.stderr)
        self.assertFalse((self.stage / "invalid").exists())

    def test_protected_paths_and_fake_history_remain_untouched(self):
        config = self.stage / "config-home"
        config.mkdir()
        data = self.stage / "data-home/cliphist"
        data.mkdir(parents=True)
        history = data / "db"
        sentinel = b"fictional-sentinel-not-for-export"
        history.write_bytes(sentinel)
        link = self.stage / "alias"
        link.symlink_to(config, target_is_directory=True)
        env = {**os.environ, "XDG_CONFIG_HOME": str(config), "XDG_DATA_HOME": str(data.parent)}
        for path in ("config-home/wofi", "alias/wofi"):
            self.assertNotEqual(self.generate("compact", path, env=env).returncode, 0)
        self.assertEqual(list(config.iterdir()), [])
        result = self.generate("segmented", "isolated", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(history.read_bytes(), sentinel)
        for artifact in (self.stage / "isolated").iterdir():
            self.assertNotIn(sentinel, artifact.read_bytes())

    def test_modes_shortcuts_and_commands_are_preserved(self):
        hyprland = (REPO / "dotfiles/.config/hypr/hyprland.lua").read_text()
        auxiliary = (REPO / "dotfiles/.local/bin/cliphist-menu.sh").read_text()
        self.assertIn('local mainMod = "SUPER"', hyprland)
        self.assertIn('local menu = "wofi --show drun"', hyprland)
        self.assertIn('hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd(menu))', hyprland)
        self.assertRegex(hyprland, r'hl\.bind\(mainMod \.\. " \+ SHIFT \+ V".*\.local/bin/cliphist-menu\.sh')
        self.assertIn('local fileManager = "$HOME/.local/bin/dolphin-carbon"', hyprland)
        self.assertIn('wofi --dmenu', auxiliary)
        self.assertIn('cliphist decode', auxiliary)
        self.assertIn('wl-copy', auxiliary)

    def test_prototypes_include_all_fictional_scenarios_without_external_resources(self):
        for variant in VARIANTS:
            document = (self.bundle(variant) / "preview.html").read_text()
            for scenario in ("apps", "long", "empty", "few", "clipboard"):
                self.assertIn(f'data-example="{scenario}"', document)
            self.assertIn("publicaciones multilingües", document)
            self.assertIn("overflow-wrap: anywhere", document)
            self.assertIn("aria-selected", document)
            self.assertIn("imagen ficticia", document)
            self.assertNotRegex(document, r'(?:href|src)=|@import\b|\burl\(|navigator\.clipboard')

    @unittest.skipUnless(GTK3, "GtkCssProvider de GTK 3 no disponible")
    def test_gtk3_parses_both_native_stylesheets(self):
        gtk = CDLL(GTK3)
        gtk.gtk_css_provider_new.restype = c_void_p
        gtk.gtk_css_provider_load_from_path.argtypes = (c_void_p, c_char_p, c_void_p)
        gtk.gtk_css_provider_load_from_path.restype = c_int
        gtk.g_object_unref.argtypes = (c_void_p,)
        gtk.g_object_unref.restype = None
        callback_type = CFUNCTYPE(None, c_void_p, c_void_p, c_void_p, c_void_p)
        gtk.g_signal_connect_data.argtypes = (c_void_p, c_char_p, callback_type,
                                             c_void_p, c_void_p, c_int)
        gtk.g_signal_connect_data.restype = c_ulong
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                css = self.bundle(variant) / "style.css"
                errors = []
                callback = callback_type(lambda *_: errors.append(True))
                provider = gtk.gtk_css_provider_new()
                try:
                    gtk.g_signal_connect_data(provider, b"parsing-error", callback, None, None, 0)
                    self.assertTrue(gtk.gtk_css_provider_load_from_path(provider, os.fsencode(css), None))
                    self.assertEqual(errors, [])
                finally:
                    gtk.g_object_unref(provider)
