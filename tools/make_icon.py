"""Generuje ikonę EMKA (PNG, ICO, ICNS). Narzędzie deweloperskie - wymaga Pillow i numpy.

Użycie:  python3 tools/make_icon.py
Program EMKA nie potrzebuje tych bibliotek - korzysta z gotowych plików w emka/assets/.

Motyw: litera E, której ramiona rosną ku dołowi jak słupki wzrostu (waloryzacja).
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "emka" / "assets"
SIZE = 1024
SCALE = 2  # rysujemy w podwójnej rozdzielczości i zmniejszamy - gładkie krawędzie

NAVY_TOP, NAVY_BOTTOM = (31, 58, 96), (13, 25, 44)
WHITE = (255, 255, 255, 255)
ACCENT = (77, 163, 255, 255)


def background(size):
    """Zaokrąglony kwadrat z pionowym gradientem granatu."""
    s = size * SCALE
    gradient = np.linspace(0, 1, s)[:, None, None]
    top, bottom = np.array(NAVY_TOP), np.array(NAVY_BOTTOM)
    rgb = (top + (bottom - top) * gradient).repeat(s, axis=1).astype(np.uint8)
    image = Image.fromarray(rgb, "RGB").convert("RGBA")
    mask = Image.new("L", (s, s), 0)
    margin, radius = 64 * SCALE, 210 * SCALE
    ImageDraw.Draw(mask).rounded_rectangle((margin, margin, s - margin, s - margin), radius, fill=255)
    image.putalpha(mask)
    return image


def draw_letter(image):
    d = ImageDraw.Draw(image)
    k = SCALE
    corner = 34 * k
    stem_left, stem_right = 268 * k, 382 * k
    top, bottom = 268 * k, 756 * k
    d.rounded_rectangle((stem_left, top, stem_right, bottom), corner, fill=WHITE)
    # Trzy ramiona o rosnącej długości; najdłuższe (dolne) w kolorze akcentu.
    arms = [(268, 596, WHITE), (462, 680, WHITE), (656, 764, ACCENT)]
    for y, end, color in arms:
        d.rounded_rectangle((stem_left, y * k, end * k, (y + 100) * k), corner, fill=color)
    return image


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    master = draw_letter(background(SIZE)).resize((SIZE, SIZE), Image.LANCZOS)
    master.resize((512, 512), Image.LANCZOS).save(ASSETS / "icon.png")
    master.save(ASSETS / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])

    # macOS: .icns z zestawu ikon (narzędzie iconutil jest tylko na macOS).
    if shutil.which("iconutil"):
        with tempfile.TemporaryDirectory() as tmp:
            iconset = Path(tmp) / "EMKA.iconset"
            iconset.mkdir()
            for base in (16, 32, 128, 256, 512):
                master.resize((base, base), Image.LANCZOS).save(iconset / f"icon_{base}x{base}.png")
                master.resize((base * 2, base * 2), Image.LANCZOS).save(iconset / f"icon_{base}x{base}@2x.png")
            subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(ASSETS / "EMKA.icns")], check=True)
    print("Zapisano:", ", ".join(sorted(p.name for p in ASSETS.iterdir())))


if __name__ == "__main__":
    main()
