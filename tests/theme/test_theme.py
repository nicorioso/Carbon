"""Validate the preview engine independently of a graphical session."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
CARBON = REPO / "dotfiles/.config/carbon"
TEMPLATES = REPO / "templates/theme"
sys.path.insert(0, str(CARBON / "scripts"))

from carbon_theme import output
from carbon_theme.render import render_theme
from carbon_theme.schema import PALETTE, ThemeError, load_theme


class ThemeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="carbon-theme-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.input = self.root / "theme.json"
        self.destination = self.root / "preview"
        self.tokens = json.loads((CARBON / "theme.json").read_text())
        self.rendered = render_theme(load_theme(CARBON / "theme.json"), TEMPLATES)

    def load(self, data):
        self.input.write_text(json.dumps(data), encoding="utf-8")
        return load_theme(self.input)

    def assert_invalid(self, section, key, value, error):
        self.tokens[section][key] = value
        with self.assertRaisesRegex(ThemeError, error):
            self.load(self.tokens)

    def test_official_theme_loads(self):
        data = load_theme(CARBON / "theme.json")
        self.assertEqual(data["colors"], PALETTE)
        self.assertEqual(data["typography"]["family"], "Noto Sans")
        self.assertEqual(data["geometry"]["radius"], 0)

    def test_required_field(self):
        del self.tokens["colors"]["border"]
        with self.assertRaisesRegex(ThemeError, r"colors\.border.*obligatoria"):
            self.load(self.tokens)

    def test_unknown_field_and_version(self):
        self.assert_invalid("metadata", "custom", 1, r"metadata\.custom.*desconocida")
        del self.tokens["metadata"]["custom"]
        self.assert_invalid("metadata", "schemaVersion", 2, r"metadata\.schemaVersion")

    def test_invalid_and_unofficial_color(self):
        for color in ("#ff", "#ggff99", "#ffff0000", "red"):
            with self.subTest(color=color):
                self.assert_invalid("colors", "background", color, r"colors\.background.*hexadecimal")
        self.assert_invalid("colors", "background", "#121213", r"colors\.background.*oficial")

    def test_incorrect_types_and_semantic_references(self):
        self.assert_invalid("geometry", "radius", True, r"geometry\.radius")
        self.tokens["geometry"]["radius"] = 0
        self.assert_invalid("semantic", "focus", ["selection"], r"semantic\.focus")
        self.assert_invalid("semantic", "focus", "devicePath", r"semantic\.focus")

    def test_opacity_limits(self):
        for invalid in (-0.1, 1.1, True, "0.5", float("nan"), float("inf")):
            with self.subTest(invalid=invalid):
                self.assert_invalid("opacity", "surface", invalid, r"opacity\.surface")
        for valid in (0, 1, 0.42):
            self.tokens["opacity"]["surface"] = valid
            self.load(self.tokens)

    def test_numeric_constraints(self):
        for section, key, value in (("geometry", "radius", -1), ("geometry", "borderThin", 0),
                                    ("spacing", "unit", 0), ("spacing", "small", 7),
                                    ("spacing", "medium", -4), ("typography", "sizePx", 97)):
            with self.subTest(key=key):
                self.assert_invalid(section, key, value, f"{section}\\.{key}")
                self.tokens = json.loads((CARBON / "theme.json").read_text())

    def test_json_duplicates_and_invalid_input(self):
        for source, message in (('{"x":{"y":1,"y":2}}', r"theme\.x\.y.*duplicada"),
                                ("{invalid", "JSON inválido"), ('{"x": 1e99999999999999999999}', "JSON inválido")):
            with self.subTest(source=source):
                self.input.write_text(source)
                with self.assertRaisesRegex(ThemeError, message):
                    load_theme(self.input)

    def test_css_rendering(self):
        css = self.rendered["carbon-preview.css"].decode()
        self.assertIn("@define-color carbon_background #121212;", css)
        self.assertIn('font-family: "Noto Sans", "Font Awesome 7 Free Solid"', css)
        self.assertIn("background-color: rgba(27, 27, 27, 0.97);", css)
        self.assertIn(".carbon-preview:focus", css)

    def test_rasi_rendering(self):
        rasi = self.rendered["carbon-tokens.rasi"].decode()
        self.assertIn("carbon-selection: #d6d6d6;", rasi)
        self.assertIn('carbon-font: "Noto Sans 12px";', rasi)
        self.assertIn("carbon-radius: 0px;", rasi)
        self.assertNotIn("window {", rasi)

    def test_safe_string_escaping(self):
        for invalid in ("", "   ", "font\n}", "font\0}", "\ud800"):
            with self.subTest(invalid=invalid):
                self.assert_invalid("typography", "family", invalid, r"typography\.family")
        self.tokens["typography"]["family"] = 'Noto "Q" \\ }; $x'
        renders = render_theme(self.load(self.tokens), TEMPLATES)
        self.assertIn(rb'"Noto \"Q\" \\ }; $x"', renders["carbon-preview.css"])
        self.assertIn(rb'"Noto \"Q\" \\ }; $x 12px"', renders["carbon-tokens.rasi"])

    def test_deterministic_render_and_idempotent_publication(self):
        alternate = dict(reversed(list(self.tokens.items())))
        alternate["colors"]["text"] = "#F5F5F5"
        renders = render_theme(self.load(alternate), TEMPLATES)
        self.assertEqual(self.rendered, renders)
        self.assertTrue(output.write_preview(self.destination, renders))
        baseline = {p.name: p.stat().st_mtime_ns for p in self.destination.iterdir()}
        self.assertFalse(output.write_preview(self.destination, self.rendered))
        self.assertEqual(baseline, {p.name: p.stat().st_mtime_ns for p in self.destination.iterdir()})

    def test_missing_destination_and_missing_parent(self):
        with self.assertRaisesRegex(ThemeError, "directorio padre"):
            output.write_preview(self.root / "missing" / "preview", self.rendered)
        self.assertFalse((self.root / "missing").exists())
        self.assertTrue(output.write_preview(self.destination, self.rendered))
        self.assertEqual({p.name: p.read_bytes() for p in self.destination.iterdir()}, self.rendered)
        self.assertEqual(self.destination.stat().st_mode & 0o777, 0o700)

    def test_unsafe_paths_and_existing_content(self):
        symlink = self.root / "alias"
        symlink.symlink_to(self.root, target_is_directory=True)
        for path in (self.root / ".." / "cannot-write", symlink, symlink / "preview"):
            with self.subTest(path=path), self.assertRaises(ThemeError):
                output.write_preview(path, self.rendered)
        config = self.root / "custom-config"
        config.mkdir()
        with patch.dict(os.environ, XDG_CONFIG_HOME=str(config)):
            with self.assertRaisesRegex(ThemeError, "configuración"):
                output.write_preview(config / "preview", self.rendered)
        self.assertFalse(self.destination.exists())
        self.destination.mkdir()
        sentinel = self.destination / "keep"
        sentinel.write_text("unchanged")
        with self.assertRaisesRegex(ThemeError, "otros contenidos"):
            output.write_preview(self.destination, self.rendered)
        self.assertEqual(sentinel.read_text(), "unchanged")

    def test_symlink_artifact_and_path_like_artifact_rejected(self):
        output.write_preview(self.destination, self.rendered)
        file = self.destination / "carbon-preview.css"
        external = self.root / "outside"
        file.rename(external)
        file.symlink_to(external)
        with self.assertRaisesRegex(ThemeError, "archivo ajeno"):
            output.write_preview(self.destination, self.rendered)
        self.assertEqual(external.read_bytes(), self.rendered[file.name])
        with self.assertRaisesRegex(ThemeError, "nombres de artefactos"):
            output.write_preview(self.root / "other", {"../outside": b"unsafe"})

    def test_strict_template_failure_has_no_output(self):
        templates = self.root / "templates"
        shutil.copytree(TEMPLATES, templates)
        (templates / "rofi.rasi.tmpl").write_text("${unknownToken};")
        result = self.run_cli("--templates", templates)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknownToken", result.stderr)
        self.assertFalse(self.destination.exists())
        (templates / "rofi.rasi.tmpl").write_text("$!")
        self.assertIn("marcador inválido", self.run_cli("--templates", templates).stderr)
        self.assertFalse(self.destination.exists())

    def test_second_file_write_failure_leaves_no_partial_bundle(self):
        real_write = output._write_file
        def fail_on_rasi(fd, name, data):
            real_write(fd, name, data)
            if name.endswith(".rasi"):
                raise OSError(28, "simulated write failure")

        with patch.object(output, "_write_file", side_effect=fail_on_rasi):
            with self.assertRaisesRegex(ThemeError, "simulated write failure"):
                output.write_preview(self.destination, self.rendered)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_publication_collision_does_not_overwrite(self):
        def race(parent, staging, target):
            os.mkdir(target, dir_fd=parent)
            raise FileExistsError(17, "simulated collision")

        with patch.object(output, "_rename_new", side_effect=race):
            with self.assertRaisesRegex(ThemeError, "otros contenidos"):
                output.write_preview(self.destination, self.rendered)
        self.assertEqual(list(self.root.iterdir()), [self.destination])
        self.assertEqual(list(self.destination.iterdir()), [])

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(CARBON / "scripts/generate-theme.py"), "--input",
             str(CARBON / "theme.json"), "--output", "preview", *map(str, args)],
            cwd=self.root, capture_output=True, text=True, timeout=10,
        )

    def test_cli_runs_from_another_directory(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Vista previa generada", result.stdout)
        self.assertIn("sin cambios", self.run_cli().stdout)

    @unittest.skipUnless(shutil.which("rofi"), "validador Rasi de Rofi no disponible")
    def test_native_rasi_parser_without_display(self):
        # Also test a font name that contains quotes, backslashes and Rasi punctuation.
        self.tokens["typography"]["family"] = 'Noto "quoted" \\ };'
        output.write_preview(self.destination, render_theme(self.load(self.tokens), TEMPLATES))
        env = {key: value for key, value in os.environ.items()
               if key not in ("DISPLAY", "WAYLAND_DISPLAY", "WAYLAND_SOCKET")}
        env.update(HOME=str(self.root), XDG_CONFIG_HOME=str(self.root / "config"),
                   XDG_CACHE_HOME=str(self.root / "cache"))
        rofi = ["rofi", "-no-config", "-rasi-validate"]
        valid = subprocess.run([*rofi, self.destination / "carbon-tokens.rasi"], env=env,
                               capture_output=True, text=True, timeout=10)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        bad = self.root / "bad.rasi"
        bad.write_text("* { carbon-text: }")
        invalid = subprocess.run([*rofi, bad], env=env, capture_output=True, timeout=10)
        self.assertNotEqual(invalid.returncode, 0)


if __name__ == "__main__":
    unittest.main()
