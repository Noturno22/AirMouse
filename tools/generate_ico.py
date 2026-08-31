"""
Gera o icone .ico do desktop a partir do SVG do simbolo.
Requer: pip install cairosvg Pillow
Uso: python tools/generate_ico.py
"""
import sys
from pathlib import Path

try:
    import io

    import cairosvg
    from PIL import Image
except ImportError:
    print("Instale as dependencias: pip install cairosvg Pillow")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SVG_SRC = ROOT / "assets" / "brand" / "logo-symbol.svg"
ICO_OUT = ROOT / "assets" / "brand" / "maouse.ico"

SIZES = [16, 32, 48, 64, 128, 256]


def main():
    if not SVG_SRC.exists():
        print(f"SVG nao encontrado: {SVG_SRC}")
        sys.exit(1)

    svg_data = SVG_SRC.read_bytes()
    images = []

    for size in SIZES:
        png_data = cairosvg.svg2png(
            bytestring=svg_data,
            output_width=size,
            output_height=size,
        )
        img = Image.open(io.BytesIO(png_data))
        images.append(img)

    images[0].save(
        ICO_OUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=images[1:],
    )
    print(f"Icone gerado: {ICO_OUT}")


if __name__ == "__main__":
    main()
