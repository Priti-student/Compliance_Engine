"""Annotate a package image with detected declaration-zone boxes (PIL)."""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont

_ZONE_COLORS = {
    "mrp_block": "#d73a49",
    "net_qty_block": "#1a7f37",
    "mfg_date_block": "#9a6700",
    "expiry_date_block": "#9a6700",
    "batch_block": "#0969da",
    "fssai_block": "#8250df",
    "consumer_care_block": "#8250df",
    "manufacturer_address_block": "#57606a",
    "unit_sale_price_block": "#d73a49",
}


def annotate_image(image_bytes: bytes, zones: list[dict], max_side: int = 1200) -> bytes:
    """Draw coloured rectangles + labels over the zone bounding boxes.

    Returns JPEG bytes ready for embedding in PDFs or serving to the UI.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    for zone in zones or []:
        box = zone.get("bbox") or [0, 0, 0, 0]
        if len(box) != 4:
            continue
        x, y, w, h = (int(v) for v in box)
        color = _ZONE_COLORS.get(zone.get("zone_type", ""), "#0969da")
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        label = f"{zone.get('zone_type','')} {zone.get('confidence',0):.0f}%"
        draw.rectangle([x, max(0, y - 20), x + w, y], fill=color)
        draw.text((x + 2, max(0, y - 18)), label[:40], fill="white", font=font)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()