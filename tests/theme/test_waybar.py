"""Check the Waybar candidate against Carbon's current stylesheet."""

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
TOKEN_FILE = CARBON / "theme.json"
STYLE = REPO / "dotfiles/.config/waybar/style.css"


class WaybarTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="carbon-waybar-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def generate(self, output="waybar", *, source=TOKEN_FILE, target="waybar", env=None):
        cmd = [sys.executable, "-B", str(ENGINE), "--input", str(source), "--output", str(output)]
        if target is not None:
            cmd.extend(("--target", target))
        return subprocess.run(cmd, cwd=self.root, env=env, capture_output=True, text=True, timeout=10)

    def assert_generated(self, *args, **kwargs):
        result = self.generate(*args, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_candidate_matches_all_selectors_declarations_values_and_order(self):
        self.assert_generated()
        directory = self.root / "waybar"
        self.assertEqual({p.name for p in directory.iterdir()}, {"style.css"})
        self.assertEqual((directory / "style.css").read_bytes(), STYLE.read_bytes())

    def test_tokenized_values_change_while_local_rules_stay_identical(self):
        source = self.root / "tokens.json"
        theme = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
        theme["semantic"]["textSecondary"] = "#bbbbbb"
        theme["typography"]["family"] = "Noto Sans Test"
        theme["opacity"]["surface"] = 0.25
        source.write_text(json.dumps(theme), encoding="utf-8")
        self.assert_generated(source=source)
        expected = STYLE.read_bytes().replace(b"#b3b3b3", b"#bbbbbb").replace(b'"Noto Sans"', b'"Noto Sans Test"')
        self.assertEqual((self.root / "waybar/style.css").read_bytes(), expected)

    def test_independent_generation_and_repeat_are_deterministic(self):
        self.assert_generated("first")
        self.assert_generated("second")
        first = self.root / "first/style.css"
        self.assertEqual(first.read_bytes(), (self.root / "second/style.css").read_bytes())
        mtime = first.stat().st_mtime_ns
        repeat = self.generate("first")
        self.assertEqual(repeat.returncode, 0, repeat.stderr)
        self.assertIn("sin cambios", repeat.stdout)
        self.assertEqual(first.stat().st_mtime_ns, mtime)

    def test_invalid_tokens_fail_without_publishing(self):
        source = self.root / "tokens.json"
        theme = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
        theme["colors"]["border"] = "transparent"
        source.write_text(json.dumps(theme), encoding="utf-8")
        result = self.generate(source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("colors.border", result.stderr)
        self.assertEqual({p.name for p in self.root.iterdir()}, {"tokens.json"})

    def test_output_is_confined_to_authorized_preview(self):
        config = self.root / "active-config"
        config.mkdir()
        (config / "style.css").write_bytes(b"unrelated style")
        alias = self.root / "alias"
        alias.symlink_to(config, target_is_directory=True)
        env = {**os.environ, "XDG_CONFIG_HOME": str(config)}

        for target in (config / "waybar", alias / "waybar", "preview/../outside"):
            with self.subTest(target=target):
                self.assertNotEqual(self.generate(target, env=env).returncode, 0)
        self.assert_generated(env=env)
        self.assertEqual({p.name for p in self.root.iterdir()}, {"active-config", "alias", "waybar"})
        self.assertEqual({p.name for p in config.iterdir()}, {"style.css"})
        self.assertEqual((config / "style.css").read_bytes(), b"unrelated style")

    def test_default_preview_remains_compatible_and_cannot_be_overwritten(self):
        self.assert_generated("default", target=None)
        self.assert_generated("explicit", target="preview")
        outputs = {"carbon-preview.css", "carbon-tokens.rasi"}
        self.assertEqual({p.name for p in (self.root / "default").iterdir()}, outputs)
        self.assertNotEqual(self.generate("default").returncode, 0)
        for filename in outputs:
            self.assertEqual((self.root / "default" / filename).read_bytes(),
                             (self.root / "explicit" / filename).read_bytes())


if __name__ == "__main__":
    unittest.main()
