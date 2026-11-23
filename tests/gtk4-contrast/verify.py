"""Check native widget captures and render a local comparison from staging."""
import html
import json
import re
import struct
import subprocess
import sys
import unittest
from pathlib import Path

SCENARIOS = {
    "original": (0, "Original · sin preferencia, CSS actual"),
    "A": (2, "A · claro, CSS actual"),
    "B": (1, "B · oscuro, CSS actual · candidato A"),
    "C": (2, "C · claro, sin CSS de usuario"),
    "D": (1, "D · oscuro, sin CSS de usuario"),
    "ablation": (2, "Control · claro, sin imagen de cabecera"),
}
BACKDROP = 1 << 6
FOCUSED = 1 << 5


def luminance(color):
    channels = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    linear = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in channels]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(foreground, background):
    low, high = sorted(map(luminance, (foreground, background)))
    return (high + 0.05) / (low + 0.05)


def png_pixels(path):
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path.name}")
    width, height = struct.unpack(">II", header[16:24])
    pixels = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-threads", "1",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    if len(pixels) != width * height * 3:
        raise ValueError(f"Invalid PNG dimensions: {path.name}")

    def color_at(x, y):
        start = 3 * (y * width + x)
        return "#" + pixels[start:start + 3].hex()

    return color_at


def measure(directory, scenario, toolkit):
    metrics = {}
    log = (directory / f"{scenario}-{toolkit}.log").read_text()
    for state in ("focus", "backdrop"):
        _, section = log.split(f"[{state}]\n", 1)
        widgets = {
            match[0]: (match[1], int(match[2]), int(match[3]))
            for match in re.findall(
                r"^(\w+) color=(#[0-9a-f]{6}).*? y=(\d+).*? flags=(\d+)$", section.split("[backdrop]")[0], re.M
            )
        }
        pixel = png_pixels(directory / f"{scenario}-{toolkit}-{state}.png")
        title, title_y, header_state = widgets["title"]
        entry, entry_y, entry_state = widgets["entry"]
        selection, selection_y, _ = widgets["row"]
        header = pixel(80, title_y + 23)
        metrics[state] = {
            "header": header, "title": title, "title_ratio": contrast(title, header),
            "window": pixel(400, 325), "entry": pixel(500, entry_y + 14),
            "entry_ratio": contrast(entry, pixel(500, entry_y + 14)),
            "entry_border": pixel(495, entry_y), "header_state": header_state,
            "entry_state": entry_state, "selection": pixel(500, selection_y + 12),
            "selection_ratio": contrast(selection, pixel(500, selection_y + 12)),
        }
    return metrics


def gallery(directory, results):
    parts = ["""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carbon · Contraste GTK 4</title>
<style>
body{background:#121212;color:#f5f5f5;font:16px/1.5 sans-serif;max-width:1300px;margin:2rem auto;padding:0 1rem}
section{border-top:1px solid #333333;margin-top:2rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr));gap:1rem}
figure{margin:0;background:#1b1b1b;border:1px solid #333333}img{display:block;width:100%;height:auto}figcaption{padding:.6rem 1rem}
a:focus-visible{outline:2px solid #d6d6d6}summary{cursor:pointer;margin-top:1rem}
</style><h1>Carbon · Contraste GTK 4</h1>
<p>Widgets GTK y libadwaita renderizados en Broadway aislado con texto ficticio.
Las capturas de fondo usan el estado GTK <code>BACKDROP</code>.
El contraste calculado usa el color del título y una muestra del fondo de cabecera en foco.</p>"""]

    def figure(file, caption):
        return (f'<figure><a href="{file}"><img loading="lazy" src="{file}" alt="{html.escape(caption)}">'
                f'</a><figcaption>{html.escape(caption)}</figcaption></figure>')

    for name, (code, label) in SCENARIOS.items():
        sample = results[name, "gtk"]["focus"]
        parts.append(f'<section><h2>{label}</h2><p>Portal {code}. Cabecera GTK 4 '
                     f'{sample["title"]} sobre {sample["header"]} · {sample["title_ratio"]:.2f}:1.</p><div class="grid">')
        for toolkit, title in (("gtk", "GTK 4"), ("adw", "libadwaita")):
            for state, desc in (("focus", "foco"), ("backdrop", "fondo")):
                parts.append(figure(f"{name}-{toolkit}-{state}.png", f"{title} · {desc}"))
        parts.append('</div><details><summary>Menús y diálogos</summary><div class="grid">')
        for toolkit, title in (("gtk", "GTK 4"), ("adw", "libadwaita")):
            for state, desc in (("menu", "menú"), ("dialog", "diálogo")):
                parts.append(figure(f"{name}-{toolkit}-{state}.png", f"{title} · {desc}"))
        parts.append("</div></details></section>")
    parts.append('<section><h2>GTK 3</h2><div class="grid">')
    for name, title in (("original", "Sin preferencia"), ("B", "Preferencia oscura")):
        parts.append(figure(f"{name}-gtk3.png", title))
    parts.append("</div></section></html>")
    (directory / "comparacion.html").write_text("\n".join(parts), encoding="utf-8")


class EvidenceChecks(unittest.TestCase):
    def test_portal_and_adwaita(self):
        for scenario, (code, _) in SCENARIOS.items():
            for toolkit in ("gtk", "adw"):
                log = (directory / f"{scenario}-{toolkit}.log").read_text()
                self.assertIn(f"portal={code}\n", log)
                self.assertIn("font=Adwaita Sans 11", log)
                self.assertNotRegex(log, r"Theme parser error|Gtk-CRITICAL")
                for state in ("menu", "dialog"):
                    png_pixels(directory / f"{scenario}-{toolkit}-{state}.png")
                if toolkit == "gtk":
                    self.assertIn(f"interface={code + 1}\n", log)
                else:
                    self.assertIn(f"adw-dark={int(code == 1)} policy=0 platform-support=1", log)

    def test_factorial_contrast(self):
        for scenario in SCENARIOS:
            sample = results[scenario, "gtk"]["focus"]
            if scenario in ("original", "A"):
                self.assertLess(sample["title_ratio"], 2)
            else:
                self.assertGreaterEqual(sample["title_ratio"], 4.5)
            self.assertGreaterEqual(sample["entry_ratio"], 4.5)
        self.assertEqual(results["original", "gtk"], results["A", "gtk"])

    def test_selection_focus_and_backdrop(self):
        for sample in results.values():
            self.assertFalse(sample["focus"]["header_state"] & BACKDROP)
            self.assertTrue(sample["backdrop"]["header_state"] & BACKDROP)
            self.assertTrue(sample["focus"]["entry_state"] & FOCUSED)
            self.assertFalse(sample["backdrop"]["entry_state"] & FOCUSED)
        original, candidate = (results[name, "gtk"]["focus"] for name in ("original", "B"))
        self.assertEqual(original["selection"], candidate["selection"])
        self.assertGreaterEqual(candidate["selection_ratio"], 4.5)
        self.assertNotEqual(candidate["entry_border"], results["B", "gtk"]["backdrop"]["entry_border"])

    def test_candidate_preserves_css_and_tokens(self):
        source = stage / "input/gtk4/gtk.css"
        candidate = stage / "B/conf/gtk-4.0/gtk.css"
        self.assertEqual(source.read_bytes(), candidate.read_bytes())
        tokens = json.loads((stage / "input/theme.json").read_text())
        sample = results["B", "gtk"]["focus"]
        self.assertEqual(sample["title"], tokens["colors"]["text"])
        self.assertEqual(sample["selection"], tokens["colors"]["selection"])
        self.assertEqual(sample["window"], results["original", "gtk"]["focus"]["window"])

    def test_gtk3_regression(self):
        self.assertEqual((directory / "B-gtk3.png").read_bytes(), (directory / "original-gtk3.png").read_bytes())
        self.assertIn("dark True", (directory / "B-gtk3.log").read_text())


if __name__ == "__main__":
    stage = Path(sys.argv[1]).resolve(strict=True)
    if stage.parent != Path("/tmp") or not stage.name.startswith("carbon-gtk4."):
        raise SystemExit("Se esperaba el staging creado por run.sh.")
    directory = stage / "results"
    results = {(name, toolkit): measure(directory, name, toolkit)
               for name in SCENARIOS for toolkit in ("gtk", "adw")}
    unittest.main(argv=[sys.argv[0]], exit=False).result.wasSuccessful() or sys.exit(1)
    gallery(directory, results)
    for name in SCENARIOS:
        sample = results[name, "gtk"]["focus"]
        print(f'{name}: {sample["title"]} / {sample["header"]} = {sample["title_ratio"]:.2f}:1')
    print(directory / "comparacion.html")
