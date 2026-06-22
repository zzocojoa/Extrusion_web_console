from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "brand-source" / "logo-lockup-options.png"
BRAND_DIR = ROOT / "public" / "brand"
PUBLIC_DIR = ROOT / "public"

OFF_WHITE = "#F8FAFC"
MUTED = "#6B7280"


CROPS = {
    "logo-horizontal": (44, 18, 622, 90),
    "logo-stacked": (46, 238, 466, 407),
    "logo-sidebar": (1250, 630, 1665, 726),
    "logo-mark": (945, 198, 1142, 430),
    "logo-horizontal-dark": (1256, 250, 1655, 405),
    "app-icon": (586, 590, 774, 780),
}


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


def contain(image: Image.Image, size: tuple[int, int], pad: int = 0, background=None) -> Image.Image:
    target_w, target_h = size
    canvas = Image.new("RGBA", size, background or (0, 0, 0, 0))
    fit_w = target_w - pad * 2
    fit_h = target_h - pad * 2
    scale = min(fit_w / image.width, fit_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    x = (target_w - resized.width) // 2
    y = (target_h - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def crop_source(source: Image.Image, name: str) -> Image.Image:
    return source.crop(CROPS[name])


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def png_data_uri(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def write_svg_wrapper(svg_path: Path, png_path: Path, width: int, height: int, title: str) -> None:
    href = png_data_uri(png_path)
    svg_path.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">',
                f'  <image href="{href}" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet"/>',
                "</svg>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def save_logo_assets(source: Image.Image) -> None:
    horizontal = crop_source(source, "logo-horizontal")
    stacked = crop_source(source, "logo-stacked")
    sidebar = crop_source(source, "logo-sidebar")
    mark = crop_source(source, "logo-mark")
    mono = crop_source(source, "logo-horizontal-dark")

    save_png(contain(horizontal, (1156, 144), pad=0, background=(255, 255, 255, 255)), BRAND_DIR / "logo-horizontal.png")
    save_png(contain(stacked, (840, 338), pad=0, background=(255, 255, 255, 255)), BRAND_DIR / "logo-stacked.png")
    save_png(contain(sidebar, (830, 192), pad=0, background=(255, 255, 255, 255)), BRAND_DIR / "logo-sidebar.png")
    save_png(contain(mark, (512, 512), pad=0, background=(255, 255, 255, 255)), BRAND_DIR / "logo-mark.png")
    save_png(contain(mono, (1024, 398), pad=0, background=(255, 255, 255, 255)), BRAND_DIR / "logo-horizontal-dark.png")

    write_svg_wrapper(BRAND_DIR / "logo-horizontal.svg", BRAND_DIR / "logo-horizontal.png", 1156, 144, "Extrusion Console logo")
    write_svg_wrapper(BRAND_DIR / "logo-stacked.svg", BRAND_DIR / "logo-stacked.png", 840, 338, "Extrusion Console stacked logo")
    write_svg_wrapper(BRAND_DIR / "logo-sidebar.svg", BRAND_DIR / "logo-sidebar.png", 830, 192, "Extrusion Console sidebar logo")
    write_svg_wrapper(BRAND_DIR / "logo-mark.svg", BRAND_DIR / "logo-mark.png", 512, 512, "Extrusion Console logo mark")
    write_svg_wrapper(
        BRAND_DIR / "logo-horizontal-dark.svg",
        BRAND_DIR / "logo-horizontal-dark.png",
        1024,
        398,
        "Extrusion Console monochrome logo",
    )


def save_app_icons(source: Image.Image) -> None:
    icon_source = crop_source(source, "app-icon").convert("RGBA")

    for size in (180, 192, 512):
        icon = contain(icon_source, (size, size), pad=0, background=(255, 255, 255, 255))
        save_png(icon, BRAND_DIR / f"app-icon-{size}.png")

    save_png(contain(icon_source, (512, 512), pad=0, background=(255, 255, 255, 255)), BRAND_DIR / "app-icon.png")
    write_svg_wrapper(BRAND_DIR / "app-icon.svg", BRAND_DIR / "app-icon-512.png", 512, 512, "Extrusion Console app icon")

    favicon = contain(icon_source, (256, 256), pad=0, background=(255, 255, 255, 255))
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    favicon.save(PUBLIC_DIR / "favicon.ico", sizes=sizes)


def save_splash() -> None:
    logo = Image.open(BRAND_DIR / "logo-sidebar.png").convert("RGBA")
    image = Image.new("RGB", (1600, 900), OFF_WHITE)
    logo_fit = contain(logo, (640, 150), pad=0)
    image.paste(logo_fit, ((1600 - logo_fit.width) // 2, 328), logo_fit)

    draw = ImageDraw.Draw(image)
    subtitle = "Local upload operations console"
    subtitle_font = font(24)
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(((1600 - (bbox[2] - bbox[0])) / 2, 548), subtitle, fill=MUTED, font=subtitle_font)
    image.save(BRAND_DIR / "splash.png", optimize=True)
    write_svg_wrapper(BRAND_DIR / "splash.svg", BRAND_DIR / "splash.png", 1600, 900, "Extrusion Console splash image")


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing brand source image: {SOURCE}")

    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGBA")
    save_logo_assets(source)
    save_app_icons(source)
    save_splash()


if __name__ == "__main__":
    main()
