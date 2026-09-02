"""Gera o ícone .ico da app a partir do logo.png (raster) com Pillow.

Sem dependência de cairo (que não está disponível no Windows), ao contrário da
versão anterior que usa cairosvg/rlPyCairo.

Uso: python tools/generate_ico.py
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "brand" / "logo.png"
ICO_OUT = ROOT / "assets" / "brand" / "maouse.ico"

SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main():
    if not SRC.exists():
        print(f"Logo nao encontrado: {SRC}")
        sys.exit(1)

    im = Image.open(SRC).convert("RGBA")

    # Recorta o conteudo para um quadrado centrado (o logo ja e quadrado).
    width, height = im.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    im = im.crop((left, top, left + side, top + side))

    icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    icon.paste(im.resize((256, 256), Image.LANCZOS), (0, 0))

    icon.save(
        ICO_OUT,
        format="ICO",
        sizes=SIZES,
    )
    print(f"Icone gerado: {ICO_OUT}")


if __name__ == "__main__":
    main()
