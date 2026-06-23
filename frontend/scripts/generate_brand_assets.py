from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
BRAND_SOURCE_DIR = ROOT / "brand-source"
LOGO_SOURCE = BRAND_SOURCE_DIR / "extrusion-console-logo-master.png"
ICON_SOURCE = BRAND_SOURCE_DIR / "extrusion-console-icon-master.png"
BRAND_DIR = ROOT / "public" / "brand"
PUBLIC_DIR = ROOT / "public"
LAUNCHER_ASSET_DIR = REPO_ROOT / "launcher" / "assets"
PACKAGING_ASSET_DIR = REPO_ROOT / "packaging" / "assets"

WHITE = (255, 255, 255, 255)
SPLASH_BG = WHITE
MUTED = "#6B7280"


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def contain(image: Image.Image, size: tuple[int, int], background: tuple[int, int, int, int] = WHITE) -> Image.Image:
    target_w, target_h = size
    canvas = Image.new("RGBA", size, background)
    scale = min(target_w / image.width, target_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    x = (target_w - resized.width) // 2
    y = (target_h - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def crop_near_white(image: Image.Image, threshold: int = 245, padding: int = 36) -> Image.Image:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            if min(r, g, b) < threshold:
                xs.append(x)
                ys.append(y)
    if not xs:
        return image.convert("RGBA")
    left = max(0, min(xs) - padding)
    top = max(0, min(ys) - padding)
    right = min(image.width, max(xs) + 1 + padding)
    bottom = min(image.height, max(ys) + 1 + padding)
    return image.crop((left, top, right, bottom)).convert("RGBA")


def write_embedded_svg(svg_path: Path, png_path: Path, width: int, height: int, label: str) -> None:
    data = base64.b64encode(png_path.read_bytes()).decode("ascii")
    svg_path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{label}">
  <image href="data:image/png;base64,{data}" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet"/>
</svg>
""",
        encoding="utf-8",
    )


def save_logo_assets(logo_master: Image.Image) -> None:
    logo = crop_near_white(logo_master, padding=48)

    variants = {
        "logo-horizontal": logo,
        "logo-sidebar": contain(logo, (960, 240)),
        "logo-stacked": contain(logo, (1320, 340)),
        "logo-horizontal-dark": contain(logo, (1320, 340)),
    }

    for name, image in variants.items():
        png_path = BRAND_DIR / f"{name}.png"
        save_png(image, png_path)
        write_embedded_svg(BRAND_DIR / f"{name}.svg", png_path, image.width, image.height, f"Extrusion Console {name}")


def save_icon_assets(icon_master: Image.Image) -> None:
    icon = icon_master.convert("RGBA")
    save_png(icon, BRAND_DIR / "app-icon.png")

    for size in (180, 192, 512):
        save_png(contain(icon, (size, size)), BRAND_DIR / f"app-icon-{size}.png")

    logo_mark = Image.open(BRAND_DIR / "app-icon-512.png").convert("RGBA")
    save_png(logo_mark, BRAND_DIR / "logo-mark.png")
    write_embedded_svg(BRAND_DIR / "app-icon.svg", BRAND_DIR / "app-icon-512.png", 512, 512, "Extrusion Console app icon")
    write_embedded_svg(BRAND_DIR / "logo-mark.svg", BRAND_DIR / "logo-mark.png", 512, 512, "Extrusion Console logo mark")

    ico_source = contain(icon, (256, 256))
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    favicon_path = PUBLIC_DIR / "favicon.ico"
    favicon_path.parent.mkdir(parents=True, exist_ok=True)
    ico_source.save(favicon_path, sizes=ico_sizes)

    brand_ico_path = BRAND_DIR / "app-icon.ico"
    ico_source.save(brand_ico_path, sizes=ico_sizes)

    LAUNCHER_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGING_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    launcher_icon_path = LAUNCHER_ASSET_DIR / "extrusion-console.ico"
    installer_icon_path = PACKAGING_ASSET_DIR / "installer.ico"
    ico_source.save(launcher_icon_path, sizes=ico_sizes)
    ico_source.save(installer_icon_path, sizes=ico_sizes)


def save_splash(logo_master: Image.Image) -> None:
    logo = crop_near_white(logo_master, padding=48)
    image = Image.new("RGBA", (1600, 900), SPLASH_BG)
    logo_fit = contain(logo, (980, 250), background=(0, 0, 0, 0))
    image.alpha_composite(logo_fit, ((image.width - logo_fit.width) // 2, 314))

    draw = ImageDraw.Draw(image)
    subtitle = "Local upload operations console"
    subtitle_font = font(24)
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(((image.width - (bbox[2] - bbox[0])) / 2, 584), subtitle, fill=MUTED, font=subtitle_font)
    save_png(image, BRAND_DIR / "splash.png")
    write_embedded_svg(BRAND_DIR / "splash.svg", BRAND_DIR / "splash.png", 1600, 900, "Extrusion Console splash image")


def main() -> None:
    if not LOGO_SOURCE.exists():
        raise FileNotFoundError(f"Missing logo master image: {LOGO_SOURCE}")
    if not ICON_SOURCE.exists():
        raise FileNotFoundError(f"Missing icon master image: {ICON_SOURCE}")

    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    logo_master = Image.open(LOGO_SOURCE)
    icon_master = Image.open(ICON_SOURCE)
    save_logo_assets(logo_master)
    save_icon_assets(icon_master)
    save_splash(logo_master)


if __name__ == "__main__":
    main()
