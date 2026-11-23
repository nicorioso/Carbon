"""Check the Waybar concept bundles without accessing the desktop."""

from html.parser import HTMLParser
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
ORIGINAL_CONFIG = REPO / "dotfiles/.config/waybar/config.jsonc"
BUILDER = REPO / "prototypes/waybar/build.py"
VARIANTS = ("segmented", "refined")


class PreviewFrames(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.frames = []
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        if tag == "iframe":
            self.frames.append(dict(attrs))


class WaybarConceptTests(unittest.TestCase):
    def setUp(self):
        stage = TemporaryDirectory(prefix="carbon-waybar-concepts-test-")
        self.addCleanup(stage.cleanup)
        self.stage = Path(stage.name)
        self.bundle = self.stage / "bundle"

    def build(self, output, *, env=None):
        return subprocess.run([sys.executable, "-B", str(BUILDER), "--output", str(output)],
                              cwd=self.stage, env=env, capture_output=True, text=True, timeout=10)

    def generate(self):
        result = self.build(self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_only_segmented_changes_the_configuration(self):
        self.generate()
        refined = (self.bundle / "refined.jsonc").read_bytes()
        self.assertEqual(refined, ORIGINAL_CONFIG.read_bytes())
        baseline = json.loads(refined)
        segmented = json.loads((self.bundle / "segmented.jsonc").read_bytes())
        groups = [
            ("connectivity", ["network", "bluetooth"]),
            ("media", ["pulseaudio", "backlight"]),
            ("energy", ["battery"]),
            ("productivity", ["custom/ai-usage"]),
            ("system", ["tray"]),
        ]
        self.assertEqual(segmented["modules-right"], [f"group/{name}" for name, _ in groups])
        for name, modules in groups:
            self.assertEqual(segmented.pop(f"group/{name}"), {
                "orientation": "horizontal", "modules": modules,
            })
        segmented["modules-right"] = [module for _, modules in groups for module in modules]
        self.assertEqual(segmented.pop("height"), 36)
        self.assertEqual(baseline.pop("height"), 32)
        # All module definitions, icons, device settings, click actions and tooltips survive.
        self.assertEqual(segmented, baseline)
        self.assertIs(baseline["fixed-center"], True)
        self.assertEqual(baseline["hyprland/workspaces"]["persistent-workspaces"], {"*": [1, 2, 3, 4, 5]})

    def test_workspace_styles_match_balanced_byte_for_byte(self):
        self.generate()
        balanced = self.stage / "balanced"
        result = subprocess.run([
            sys.executable, "-B", str(CARBON / "scripts/generate-theme.py"),
            "--input", str(CARBON / "theme.json"),
            "--target", "waybar-balanced", "--output", str(balanced),
        ], cwd=self.stage, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        pattern = rb"#workspaces[^{}]+\{[^{}]*\}"
        approved = re.findall(pattern, (balanced / "style.css").read_bytes())
        self.assertEqual(len(approved), 8)
        for variant in VARIANTS:
            self.assertEqual(re.findall(pattern, (self.bundle / f"{variant}.css").read_bytes()), approved)

    def test_each_layout_has_its_own_clock_and_status_treatment(self):
        self.generate()
        segmented, refined = [(self.bundle / f"{variant}.css").read_text()
                              for variant in VARIANTS]
        for css in (segmented, refined):
            clock = re.search(r"#clock \{([^}]+)}", css)[1]
            self.assertNotIn("background", clock)
            self.assertNotRegex(css, r"(?:max-width|text-overflow):")
            self.assertIn("color: #4f9dff;", css)
            self.assertIn("#custom-ai-usage:focus", css)
        self.assertIn("border-bottom: 1px solid #d6d6d6;", segmented)
        self.assertIn("#productivity {\n    background: #252525;", segmented)
        self.assertNotIn("#productivity", refined)
        self.assertIn("margin-left: 8px;", refined)

    def test_previews_show_fictional_normal_and_long_fixtures(self):
        self.generate()
        for variant in VARIANTS:
            document = (self.bundle / f"{variant}.html").read_text()
            normal, long = PreviewFrames(document).frames
            self.assertIn("datos ficticios", document)
            for frame in (normal, long):
                self.assertIn("sandbox", frame)
                self.assertNotIn("src", frame)
                for module in ("workspaces", "clock", "network", "bluetooth", "pulseaudio",
                               "backlight", "battery", "custom-ai-usage", "tray"):
                    self.assertIn(f'id="{module}"', frame["srcdoc"])
            self.assertEqual((normal["width"], long["width"]), ("1280", "1024"))
            self.assertRegex(normal["srcdoc"], r'class="active ">2</button>')
            self.assertRegex(long["srcdoc"], r'class="active ">7</button>')
            self.assertIn(">10</button>", long["srcdoc"])
            self.assertIn("C 100% · O 1234.5k", long["srcdoc"])

    def test_generation_is_deterministic_and_idempotent(self):
        self.generate()
        expected = {f"{variant}.{extension}" for variant in VARIANTS
                    for extension in ("css", "jsonc", "html")}
        self.assertEqual({path.name for path in self.bundle.iterdir()}, expected)
        another = self.stage / "another"
        for path in (self.bundle, another):
            result = self.build(path)
            self.assertEqual(result.returncode, 0, result.stderr)
        for filename in expected:
            self.assertEqual((self.bundle / filename).read_bytes(), (another / filename).read_bytes())

    def test_output_does_not_touch_a_protected_or_linked_destination(self):
        config_home = self.stage / "configuration"
        config_home.mkdir()
        linked = self.stage / "link"
        linked.symlink_to(config_home)
        env = {**os.environ, "XDG_CONFIG_HOME": str(config_home)}
        for output in (config_home / "direct", linked / "via-link"):
            result = self.build(output, env=env)
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(config_home.iterdir()), [])
        self.assertEqual(set(self.stage.iterdir()), {config_home, linked})
