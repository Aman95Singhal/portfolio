from pathlib import Path
# Import PIL lazily inside the function to make the package optional at import time


SIZES = {
    "thumb": 600,
    "detail": 1200,
    "hero": 1800,
}


def generate_responsive_images(src_path: Path, dest_dir: Path) -> dict:
    """Generate webp resized images for sizes in SIZES and return dict of size->relative-path"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = src_path.stem
    out = {}
    try:
        from PIL import Image
        with Image.open(src_path) as im:
            im = im.convert("RGB")
            for name, width in SIZES.items():
                ratio = width / im.width
                height = int(im.height * ratio)
                resized = im.resize((width, height), Image.LANCZOS)
                out_name = f"{base}-{width}.webp"
                out_path = dest_dir / out_name
                resized.save(out_path, "WEBP", quality=85)
                out[name] = f"/static/img/uploads/{out_name}"
    except Exception:
        # if conversion fails (no Pillow, etc.), return empty dict and leave file as-is
        return {}
    return out
