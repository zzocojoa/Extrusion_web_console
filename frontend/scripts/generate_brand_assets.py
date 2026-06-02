from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "public" / "brand"
PUBLIC_DIR = ROOT / "public"

GRAPHITE = "#2B2F33"
BLUE = "#1E6FB8"
TEAL = "#00A79D"
AMBER = "#F5A623"
OFF_WHITE = "#F8FAFC"
MUTED = "#6B7280"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def scaled(points: list[tuple[float, float]], x: float, y: float, scale: float) -> list[tuple[float, float]]:
    return [(x + px * scale, y + py * scale) for px, py in points]


def draw_mark(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float, dark: bool = False) -> None:
    ink = WHITE if dark else GRAPHITE
    db_fill = None if dark else WHITE
    arrow_inner = "#111820" if dark else WHITE
    blue = "#6BB6FF" if dark else BLUE
    teal = "#22D3C5" if dark else TEAL
    amber = "#F7B23B" if dark else AMBER

    sw6 = max(2, int(6 * scale))
    sw7 = max(2, int(7 * scale))
    sw10 = max(3, int(10 * scale))

    draw.rounded_rectangle(
        [x + 72 * scale, y + 32 * scale, x + 160 * scale, y + 61 * scale],
        radius=5 * scale,
        fill=ink,
        outline=ink,
        width=sw6,
    )
    draw.line([x + 58 * scale, y + 76 * scale, x + 174 * scale, y + 76 * scale], fill=ink, width=sw10)
    draw.polygon(
        scaled([(86, 91), (147, 91), (132, 111), (132, 124), (107, 124), (107, 111)], x, y, scale),
        fill=ink,
    )

    left, top, right, bottom = x + 72 * scale, y + 152 * scale, x + 176 * scale, y + 224 * scale
    draw.rectangle([left, top + 15 * scale, right, bottom - 15 * scale], fill=db_fill)
    draw.ellipse([left, top, right, top + 34 * scale], fill=db_fill, outline=ink, width=sw7)
    draw.line([left, top + 17 * scale, left, bottom - 17 * scale], fill=ink, width=sw7)
    draw.line([right, top + 17 * scale, right, bottom - 17 * scale], fill=ink, width=sw7)
    draw.arc([left, bottom - 34 * scale, right, bottom], 0, 180, fill=ink, width=sw7)
    for yy in (176, 198):
        draw.arc([left, y + (yy - 17) * scale, right, y + (yy + 17) * scale], 0, 180, fill=ink, width=sw7)

    for cx, cy, color in [
        (154, 181, teal),
        (154, 207, teal),
        (96, 135, blue),
        (118, 134, teal),
        (108, 114, blue),
        (130, 116, teal),
        (96, 157, blue),
        (120, 157, teal),
    ]:
        r = 5 * scale
        draw.ellipse([x + cx * scale - r, y + cy * scale - r, x + cx * scale + r, y + cy * scale + r], fill=color)

    r = 18 * scale
    cx = x + 194 * scale
    cy = y + 136 * scale
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=teal)
    draw.line([cx, y + 146 * scale, cx, y + 124 * scale], fill=arrow_inner, width=sw7)
    draw.line([x + 184 * scale, y + 134 * scale, cx, y + 124 * scale, x + 204 * scale, y + 134 * scale], fill=arrow_inner, width=sw7)
    draw.arc([x + 202 * scale, y + 94 * scale, x + 250 * scale, y + 198 * scale], -62, 62, fill=amber, width=sw7)
    draw.arc([x + 199 * scale, y + 109 * scale, x + 230 * scale, y + 183 * scale], -62, 62, fill=amber, width=sw7)


def save_app_icon(size: int, filename: str) -> None:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = int(size * 0.047)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=int(size * 0.168),
        fill=OFF_WHITE,
        outline=BLUE,
        width=max(3, int(size * 0.035)),
    )
    draw_mark(draw, size * 0.17, size * 0.16, size / 350)
    image.save(BRAND_DIR / filename)


def save_logo_mark_png(size: int, filename: str) -> None:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_mark(draw, 0, 0, size / 256)
    image.save(BRAND_DIR / filename)


def save_horizontal_logo(filename: str, dark: bool = False) -> None:
    image = Image.new("RGBA", (1520, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_mark(draw, 24, 36, 0.5625, dark=dark)
    draw.line([368, 76, 368, 284], fill="#8A929A", width=6)
    draw.text((444, 64), "EXTRUSION", fill=WHITE if dark else GRAPHITE, font=font(100, True))
    draw.text((444, 164), "CONSOLE", fill="#6BB6FF" if dark else BLUE, font=font(100, True))
    image.save(BRAND_DIR / filename)


def save_splash() -> None:
    image = Image.new("RGB", (1600, 900), OFF_WHITE)
    draw = ImageDraw.Draw(image)
    draw_mark(draw, 514, 254, 190 / 256)
    draw.line([754, 299, 754, 404], fill="#8A929A", width=3)
    draw.text((799, 288), "EXTRUSION", fill=GRAPHITE, font=font(64, True))
    draw.text((799, 354), "CONSOLE", fill=BLUE, font=font(64, True))
    subtitle = "Local upload operations console"
    text_box = draw.textbbox((0, 0), subtitle, font=font(24))
    draw.text(((1600 - (text_box[2] - text_box[0])) / 2, 560), subtitle, fill=MUTED, font=font(24))
    image.save(BRAND_DIR / "splash.png")


def save_favicon() -> None:
    base = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    draw_mark(draw, 0, 0, 1)
    base.save(PUBLIC_DIR / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])


def main() -> None:
    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    save_logo_mark_png(256, "logo-mark.png")
    save_app_icon(180, "app-icon-180.png")
    save_app_icon(192, "app-icon-192.png")
    save_app_icon(512, "app-icon-512.png")
    save_horizontal_logo("logo-horizontal.png")
    save_horizontal_logo("logo-horizontal-dark.png", dark=True)
    save_splash()
    save_favicon()


if __name__ == "__main__":
    main()
