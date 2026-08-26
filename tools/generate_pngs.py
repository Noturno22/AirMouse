"""
Gera versoes PNG dos assets SVG para plataformas que nao suportam SVG.
Requer: pip install cairosvg
Uso: python tools/generate_pngs.py
"""
import sys
from pathlib import Path

try:
    import cairosvg
except ImportError:
    print("Instale: pip install cairosvg")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "brand"

ASSETS = {
    "logo-symbol.svg": [64, 128, 256, 512],
    "favicon.svg": [16, 32, 48],
    "social/avatar.svg": [200, 400, 800],
    "social/banner.svg": [750, 1500],
    "splash/splash.svg": [512, 1024],
}


def main():
    for rel, sizes in ASSETS.items():
        svg_path = BRAND / rel
        if not svg_path.exists():
            print(f"SKIP: {svg_path}")
            continue
        svg_data = svg_path.read_bytes()
        out_dir = svg_path.parent
        stem = svg_path.stem
        for size in sizes:
            out = out_dir / f"{stem}-{size}.png"
            cairosvg.svg2png(
                bytestring=svg_data,
                output_width=size,
                output_height=size,
                write_to=str(out),
            )
            print(f"  {out.name}")
    print("PNGs gerados.")


if __name__ == "__main__":
    main()
