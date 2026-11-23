"""Test Rofi power menu candidates without running an action."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

REPO = Path(__file__).resolve().parents[2]
CARBON = REPO / "dotfiles/.config/carbon"
ENGINE = CARBON / "scripts/generate-theme.py"
THEME = CARBON / "theme.json"
LAYOUTS = {"grid": (408, 2, 2), "list": (320, 1, 4)}
ROFI = shutil.which("rofi")


class PowerMenuThemeTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(prefix="carbon-power-test-")
        self.addCleanup(temp.cleanup)
        self.stage = Path(temp.name)

    def generate(self, variant, output, **kwargs):
        return subprocess.run(
            [sys.executable, "-B", str(ENGINE), "--input", str(THEME),
             "--target", f"power-{variant}", "--output", str(output)],
            cwd=self.stage, capture_output=True, text=True, timeout=10, **kwargs,
        )

    def bundle(self, variant, name=None):
        output = self.stage / (name or variant)
        result = self.generate(variant, output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path.name for path in output.iterdir()}, {"power-menu.rasi", "preview.html"})
        return output

    def test_layout_geometry_and_navigation_bindings(self):
        for variant, (width, columns, rows) in LAYOUTS.items():
            rasi = (self.bundle(variant) / "power-menu.rasi").read_text()
            self.assertIn(f"width: {width}px;", rasi)
            self.assertIn(f"columns: {columns};", rasi)
            self.assertIn(f"lines: {rows};", rasi)
            self.assertIn("layout: vertical;", rasi)
            self.assertIn("flow: horizontal;", rasi)
            self.assertIn("children: [ listview ];", rasi)
            self.assertNotRegex(rasi, r"auto-select|kb-accept|kb-cancel|hover-select")
            if variant == "grid":
                self.assertIn('kb-row-left: "Left,Control+Page_Up";', rasi)
                self.assertIn('kb-row-right: "Right,Control+Page_Down";', rasi)
                self.assertIn('kb-move-char-back: "Control+b";', rasi)
                self.assertIn('kb-move-char-forward: "Control+f";', rasi)
            else:
                self.assertNotIn("configuration {", rasi)

    def test_contrast_and_existing_icon_compatibility(self):
        for variant in LAYOUTS:
            rasi = (self.bundle(variant) / "power-menu.rasi").read_text()
            selected = rasi.split("element selected.normal {", 1)[1].split("}", 1)[0]
            self.assertIn("background-color: #252525;", selected)
            self.assertIn("border-color: #d6d6d6;", selected)
            self.assertIn("text-color: #f5f5f5;", selected)
            self.assertIn('font: "Noto Sans 11";', rasi)
            self.assertIn("border-radius: 0px;", rasi)

    def test_generation_is_deterministic_and_idempotent(self):
        for variant in LAYOUTS:
            a = self.bundle(variant)
            snapshot = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in a.iterdir()}
            b = self.bundle(variant, f"second-{variant}")
            self.bundle(variant)
            for name, metadata in snapshot.items():
                first = a / name
                self.assertEqual(first.read_bytes(), (b / name).read_bytes())
                self.assertEqual((first.stat().st_ino, first.stat().st_mtime_ns), metadata)

    def test_publication_rejects_protected_or_linked_paths(self):
        config = self.stage / "configuration"
        config.mkdir()
        link = self.stage / "linked"
        link.symlink_to(config)
        env = {**os.environ, "XDG_CONFIG_HOME": str(config)}
        for target in (config / "rofi", link / "rofi"):
            self.assertNotEqual(self.generate("grid", target, env=env).returncode, 0)
        self.assertEqual(list(config.iterdir()), [])

    def test_preview_has_four_options_and_simulated_cancel(self):
        for variant in LAYOUTS:
            html = (self.bundle(variant) / "preview.html").read_text()
            labels = re.findall(r'role="option"[^>]*><span[^>]*>[^<]+</span>([^<]+)', html)
            self.assertEqual(labels, ["Apagar", "Reiniciar", "Suspender", "Cerrar sesión"])
            self.assertIn('case "Escape":', html)
            self.assertIn("Selección cancelada", html)
            self.assertIn(".option:hover", html)
            self.assertNotRegex(html, r'src=|href=|@import\b|\burl\(|\bfetch\(|\bsystemctl\b')

    @unittest.skipUnless(ROFI, "Rofi no instalado")
    def test_native_rasi_parser_accepts_both_candidates(self):
        env = {k: v for k, v in os.environ.items()
               if k not in {"DISPLAY", "WAYLAND_DISPLAY", "WAYLAND_SOCKET"}}
        for variant in LAYOUTS:
            theme = self.bundle(variant) / "power-menu.rasi"
            result = subprocess.run([ROFI, "-no-config", "-rasi-validate", str(theme)],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([ROFI, "-no-config", "-theme", str(theme), "-dump-config"],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            if variant == "grid":
                self.assertRegex(result.stdout, r'(?m)^\s+kb-row-left\s*:\s*"Left,Control\+Page_Up";')
                self.assertRegex(result.stdout, r'(?m)^\s+kb-row-right\s*:\s*"Right,Control\+Page_Down";')
            else:
                self.assertNotIn('"Left,Control+Page_Up"', result.stdout)
