"""Validate the Waybar redesign without a running test bar."""

import ctypes
from ctypes.util import find_library
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
CARBON = REPO / "dotfiles/.config/carbon"
ENGINE = CARBON / "scripts/generate-theme.py"
THEME = CARBON / "theme.json"
WAYBAR = REPO / "dotfiles/.config/waybar"
GTK3 = find_library("gtk-3")
VARIANTS = ("compact", "balanced")


class RedesignTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="carbon-waybar-redesign-")
        self.addCleanup(temporary.cleanup)
        self.stage = Path(temporary.name)
        self.config = json.loads((WAYBAR / "config.jsonc").read_text(encoding="utf-8"))

    def generate(self, target, output, *, env=None):
        return subprocess.run(
            [sys.executable, "-B", str(ENGINE), "--input", str(THEME),
             "--target", target, "--output", str(output)],
            env=env, cwd=self.stage, capture_output=True, text=True, timeout=10,
        )

    def stylesheet(self, variant, output=None):
        output = self.stage / (output or variant)
        result = self.generate(f"waybar-{variant}", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.name for p in output.iterdir()}, {"style.css"})
        return output / "style.css"

    def test_jsonc_preserves_bar_geometry_clock_and_modules(self):
        config = self.config
        self.assertEqual((config["layer"], config["position"], config["height"], config["spacing"]),
                         ("top", "top", 32, 2))
        self.assertIs(config["fixed-center"], True)
        self.assertEqual(config["modules-left"], ["hyprland/workspaces"])
        self.assertEqual(config["modules-center"], ["clock"])
        self.assertEqual(config["modules-right"],
                         ["network", "bluetooth", "pulseaudio", "backlight",
                          "battery", "custom/ai-usage", "tray"])
        self.assertEqual(config["clock"]["format"], " {:%a %d %b  %H:%M}")
        self.assertEqual(config["clock"]["tooltip-format"], "{:%A, %d de %B de %Y}")

    def test_workspace_persistence_and_numeric_order(self):
        module = self.config["hyprland/workspaces"]
        self.assertEqual(module["persistent-workspaces"], {"*": [1, 2, 3, 4, 5]})
        self.assertEqual(module["sort-by"], "number")
        self.assertEqual(module["format"], "{name}")
        self.assertEqual(module["on-click"], "activate")

    def test_dynamic_workspaces_remain_eligible_for_native_ipc_events(self):
        module = self.config["hyprland/workspaces"]
        # Waybar handles create/destroy. Keep 6–10 out of the placeholder list,
        # and leave off all filters that would hide their live workspace buttons.
        configured = {workspace for ids in module["persistent-workspaces"].values() for workspace in ids}
        self.assertTrue(configured.isdisjoint(range(6, 11)))
        for option in ("persistent-only", "active-only", "hide-active", "ignore-workspaces"):
            with self.subTest(option=option):
                self.assertFalse(module.get(option))

    def test_click_actions_status_and_icon_formats_are_intact(self):
        expected_clicks = {
            "network": "nm-connection-editor",
            "bluetooth": "blueman-manager",
            "pulseaudio": "pavucontrol",
            "custom/ai-usage": "~/.local/bin/ai-usage show",
        }
        for module, command in expected_clicks.items():
            with self.subTest(module=module):
                self.assertEqual(self.config[module]["on-click"], command)
        self.assertEqual(self.config["custom/ai-usage"]["on-click-middle"], "~/.local/bin/ai-usage refresh")
        self.assertEqual(self.config["custom/ai-usage"]["exec"], "~/.local/bin/ai-usage poll")
        self.assertEqual(self.config["custom/ai-usage"]["interval"], 30)
        self.assertEqual(self.config["network"]["format-wifi"], " {signalStrength}%")
        self.assertEqual(self.config["bluetooth"]["format-connected"], " {num_connections}")
        self.assertEqual(self.config["pulseaudio"]["format-icons"]["default"], ["", "", ""])
        self.assertEqual(self.config["backlight"]["format"], " {percent}%")
        self.assertEqual(self.config["battery"]["format-icons"], ["", "", "", "", ""])
        self.assertEqual(self.config["battery"]["states"], {"warning": 30, "critical": 15})
        self.assertEqual(self.config["tray"], {"icon-size": 16, "spacing": 6, "show-passive-items": True})

    def test_variants_have_the_same_rules_except_status_spacing(self):
        compact, balanced = (self.stylesheet(v).read_text(encoding="utf-8") for v in VARIANTS)
        # Only the outer status padding changes between layout targets.
        group = "#network, #bluetooth, #pulseaudio, #backlight, #battery, #tray, #custom-ai-usage"
        block = f"{group} {{\n    margin: 4px 0;\n    padding: 0 "
        self.assertIn(f"{block}4px;", compact)
        self.assertEqual(compact.replace(f"{block}4px;", f"{block}8px;"), balanced)
        for css in (compact, balanced):
            for text in ('"Noto Sans", "Font Awesome 7 Free Solid", "Font Awesome 7 Brands"',
                         "button:not(.empty):not(.active)", "button.active.urgent", "button.active:focus",
                         "#custom-ai-usage.error", "color: #4f9dff;", "border-radius: 0px;"):
                self.assertIn(text, css)
            self.assertNotIn("rgba(", css)

    def test_clock_is_raised_and_has_horizontal_padding_without_a_size_cap(self):
        css = self.stylesheet("balanced").read_text(encoding="utf-8")
        clock = css.split("#clock {\n", 1)[1].split("}", 1)[0]
        self.assertIn("margin: 4px 0;", clock)
        self.assertIn("padding: 0 12px;", clock)
        self.assertIn("background: #252525;", clock)
        self.assertNotRegex(clock, r"(?:width|height|overflow):")
        self.assertIs(self.config["fixed-center"], True)

    def test_status_groups_save_inner_space_without_constraining_text(self):
        css = self.stylesheet("balanced").read_text(encoding="utf-8")
        status = css[css.index("#network, #bluetooth, #pulseaudio, #backlight, #battery, #tray"):]
        self.assertIn("#network, #pulseaudio {\n    padding-right: 4px;", status)
        self.assertIn("#bluetooth, #backlight {\n    padding-left: 4px;", status)
        self.assertIn("#pulseaudio, #battery, #custom-ai-usage, #tray {\n    border-left: 1px solid #333333;",
                      status)
        self.assertIn("#custom-ai-usage {\n    background: #252525;", status)
        self.assertIn("#custom-ai-usage:focus {", status)
        self.assertNotRegex(status, r"(?:width|height|overflow):")
        for module in self.config["modules-right"]:
            self.assertNotIn("max-length", self.config[module])
            self.assertNotIn("min-length", self.config[module])

    def test_generation_is_deterministic_and_preview_compatible(self):
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                a = self.stylesheet(variant, f"{variant}-first")
                b = self.stylesheet(variant, f"{variant}-second")
                self.assertEqual(a.read_bytes(), b.read_bytes())
        result = self.generate("waybar", "pilot")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.stage / "pilot/style.css").read_bytes(), (WAYBAR / "style.css").read_bytes())

    def test_confined_output_rejects_active_xdg_path(self):
        fake_active = self.stage / "configuration"
        fake_active.mkdir()
        marker = fake_active / "unchanged"
        marker.write_text("keep")
        result = self.generate("waybar-balanced", fake_active / "waybar",
                               env={**os.environ, "XDG_CONFIG_HOME": str(fake_active)})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((fake_active / "waybar").exists())
        self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(list(self.stage.iterdir()), [fake_active])

    @unittest.skipUnless(GTK3, "GtkCssProvider de GTK 3 no disponible")
    def test_native_gtk3_validates_both_variants(self):
        # Loading an isolated provider parses the CSS without gtk_init or a display.
        gtk = ctypes.CDLL(GTK3)
        gtk.gtk_css_provider_new.restype = ctypes.c_void_p
        gtk.gtk_css_provider_load_from_path.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p)
        gtk.gtk_css_provider_load_from_path.restype = ctypes.c_int
        gtk.g_object_unref.argtypes = (ctypes.c_void_p,)
        gtk.g_object_unref.restype = None
        callback_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_void_p, ctypes.c_void_p)
        gtk.g_signal_connect_data.argtypes = (ctypes.c_void_p, ctypes.c_char_p, callback_type,
                                             ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int)
        gtk.g_signal_connect_data.restype = ctypes.c_ulong
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                style = self.stylesheet(variant)
                errors = []
                callback = callback_type(lambda *_: errors.append(True))
                provider = gtk.gtk_css_provider_new()
                try:
                    gtk.g_signal_connect_data(provider, b"parsing-error", callback, None, None, 0)
                    self.assertTrue(gtk.gtk_css_provider_load_from_path(provider, os.fsencode(style), None))
                    self.assertEqual(errors, [])
                finally:
                    gtk.g_object_unref(provider)


if __name__ == "__main__":
    unittest.main()
