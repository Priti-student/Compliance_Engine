"""
Phase 6 - Regex patterns for declaration extraction (NLP layer 1).

Deterministic patterns that capture the LMPC-2011 mandatory declarations
from OCR'd zone text: MRP (incl. of all taxes), net quantity + allowed SI
units, month/year of manufacture, use-by/best-before dates, FSSAI licence
numbers, batch numbers, consumer-care phone/email, manufacturer/origin
phrases.

Each entry: (field_name, compiled_pattern, extractor_callable). Patterns are
compiled once at import time. These feed `declaration_extractor.py`; they are
the always-on baseline and also act as a validator for the spaCy/BERT layers
later (Phase 6 upgrade).
"""
import re
from typing import Callable, List, Tuple

_UNIT_MAP = {
    "g": "g", "gm": "g", "gr": "g", "gram": "g", "grams": "g",
    "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
    "ml": "ml", "millilitre": "ml", "millilitres": "ml",
    "milliliter": "ml", "milliliters": "ml",
    "l": "l", "ltr": "l", "litre": "l", "litres": "l",
    "liter": "l", "liters": "l",
    "cm": "cm", "centimetre": "cm", "centimetres": "cm",
    "m": "m", "metre": "m", "metres": "m",
    "sqcm": "sq cm", "sq.cm": "sq cm", "sq cm": "sq cm",
    "sqm": "sq m", "sq.m": "sq m", "sq m": "sq m",
    "number": "number", "no": "number", "nos": "number",
    "pcs": "number", "u": "U", "units": "U",
}

_QUALIFYING_WORDS = ("about", "approx", "approximately", "minimum",
                     "not less than", "more than")


def _norm(text: str) -> str:
    """Collapse whitespace for easier matching."""
    return re.sub(r"\s+", " ", text).strip()


def _find_unit(text: str) -> str:
    """Return a canonical unit if the text contains one of the allowed units.

    Works for both spaced ('52 g') and glued ('52g') unit tokens by using
    letter-boundary lookaround instead of \\b word boundaries.
    """
    lowered = text.lower()
    keys = sorted(_UNIT_MAP, key=len, reverse=True)
    for key in keys:
        if re.search(rf"(?<![a-z]){re.escape(key)}(?![a-z])", lowered):
            return _UNIT_MAP[key]
    return ""


# ---------------------------------------------------------------------------
# Individual declaration extractors
# ---------------------------------------------------------------------------
_MRP_LABEL_RE = re.compile(
    r"\bm\.?\s?r\.?\s?[pe]\b|maximum\s+retail\s+price",
    re.IGNORECASE,
)


def _extract_mrp(zone_text: str) -> List[dict]:
    """Extract MRP amount; order-agnostic (value may precede the label) and
    tolerant of OCR noise like '20.00 = MRP:'.

    Strategy: find each MRP-label occurrence and return the first amount found
    in a ±40-char window around it. This handles both 'MRP Rs. 20.00' and the
    reversed '20.00 = MRP:' produced by token-per-line OCR.
    """
    text = _norm(zone_text)
    for m in _MRP_LABEL_RE.finditer(text):
        lo = max(0, m.start() - 40)
        hi = min(len(text), m.end() + 40)
        win = text[lo:hi]
        amt = re.search(r"([0-9]{1,6}(?:\.[0-9]{1,2})?)", win)
        if amt:
            return [{"value": amt.group(1)}]
    return []


_NET_QTY_RE = re.compile(
    r"\bnet\s*(?:quantity|qty|weight|wt)*\.?\s*[:=\-]?\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)?",
    re.IGNORECASE,
)

# Reversed order variant: 'id 120g Weight: Net' -> number BEFORE the label,
# with a few words (OCR residue) allowed between the unit and 'net'.
_NET_QTY_REV_RE = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)"
    r"(?:\s+\w+){0,3}?\s*net\b(?![\w])",
    re.IGNORECASE,
)


def _clean_ocr(text: str) -> str:
    """Replace non-alphanumeric OCR junk (smart quotes, bars) with spaces."""
    cleaned = re.sub(r"[^\w\s.=/]", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_net_quantity(zone_text: str) -> List[dict]:
    out = []
    text = _clean_ocr(_norm(zone_text))

    def _match(m):
        value, raw_unit = m.group(1), m.group(2) or ""
        unit = _find_unit(raw_unit)
        if not unit:
            glued = re.search(rf"{re.escape(value)}([a-zA-Z]+)", text[m.start():m.end() + 4])
            if glued:
                unit = _find_unit(glued.group(1))
        return (value, unit, m.start())

    hits = list(_NET_QTY_RE.finditer(text))
    if not hits:
        hits = list(_NET_QTY_REV_RE.finditer(text))

    seen = set()
    for m in hits:
        value, unit, start = _match(m)
        if not unit or (value, unit) in seen:
            continue
        seen.add((value, unit))
        # qualifiers: misleading words only within a tight window BEFORE the
        # value (so nutrition-table 'Approx. per 100g' elsewhere doesn't flag).
        window = text[max(0, start - 40):start]
        qualifiers = [q for q in _QUALIFYING_WORDS if q in window.lower()]
        out.append({"value": f"{value} {unit}", "unit": unit, "amount": value,
                    "qualifiers": qualifiers})
    return out


_MFG_RE = re.compile(
    r"\b(?:mfd|med|mfg\.?\s*date|manufactur(?:ed|ing)\s+date|"
    r"month\s*&?\s*year\s+of\s+manufacture|"
    r"month\s+and\s+years?\s+of\s+manufacture)\b\s*[:\-]?\s*"
    r"([0-9]{1,2}[/\-][0-9]{4}|[A-Za-z]+\s+[0-9]{4})",
    re.IGNORECASE,
)


def _extract_mfg(zone_text: str) -> List[dict]:
    out = []
    text = _norm(zone_text)
    for m in _MFG_RE.finditer(text):
        out.append({"value": m.group(1)})
    # Relaxed: "MFD:" / "MED:" present but the date order got tokenized away
    # (e.g. "12/07/2024 MED:" from token-per-line OCR). Only accept when a
    # real date is also present so we don't invent manufactures.
    if not out and re.search(
        r"\b(?:mfd|med|mfg\.?\s*date|month\s+and\s+year|manufactur(?:ed|ing)\s+date)\b",
        text, re.IGNORECASE,
    ):
        date = re.search(r"\b([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})\b", text)
        if date:
            out.append({"value": date.group(1)})
    return out


_EXPIRY_RE = re.compile(
    r"\b(?:use\s*by|best\s*before|useby|expiry|exp\.?\s*date)\b\s*[:\-]?\s*"
    r"([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4})",
    re.IGNORECASE,
)


def _extract_expiry(zone_text: str) -> List[dict]:
    return [{"value": m.group(1)} for m in _EXPIRY_RE.finditer(_norm(zone_text))]


_FSSAI_RE = re.compile(
    r"\b(?:fssai\s*lic\.?\s*no\.?|lic\.?\s*no\.?)\s*[:\-]?\s*([0-9]{14})",
    re.IGNORECASE,
)


def _extract_fssai(zone_text: str) -> List[dict]:
    return [{"value": m.group(1)} for m in _FSSAI_RE.finditer(_norm(zone_text))]


_BATCH_RE = re.compile(
    r"\bbatch\s*(?:no\.?|number)?\s*[:\-]?\s*([A-Za-z0-9]{2,})",
    re.IGNORECASE,
)


def _extract_batch(zone_text: str) -> List[dict]:
    return [{"value": m.group(1)} for m in _BATCH_RE.finditer(_norm(zone_text))]


_PHONE_RE = re.compile(
    r"(?:\d[\s\-.]*){9,14}\d",
    re.IGNORECASE,
)

# Toll-free / std numbers often print in 3-4-4 or 4-2-4 chunks (e.g.
# '1800 22 4020'); the previous 3-5 digit-chunk pattern rejected 2-digit
# chunks. This matches any 10-15 digit run separated by spaces/dashes/dots;
# the caller keeps only 10-12 digit totals.


def _extract_phone(zone_text: str) -> List[dict]:
    out = []
    for m in _PHONE_RE.finditer(zone_text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 12:
            out.append({"value": digits})
    return out


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def _extract_email(zone_text: str) -> List[dict]:
    return [{"value": m.group(0)} for m in _EMAIL_RE.finditer(zone_text)]


_UNIT_SALE_PRICE_RE = re.compile(
    r"\bunit\s*(?:sale|sle)?\s*(?:price|pre)\s*[:=\-]?\s*(?:rs\.?|inr|₹|€)?\s*"
    r"([0-9]+(?:\.[0-9]{1,2})?)",
    re.IGNORECASE,
)


def _extract_unit_sale_price(zone_text: str) -> List[dict]:
    """Unit sale price (LMPC 2021-2023 amendment).

    Tolerates OCR like 'Unit Sle Pre: €60.00' -> 60.00.
    """
    out = []
    for m in _UNIT_SALE_PRICE_RE.finditer(_norm(zone_text)):
        out.append({"value": m.group(1)})
    return out


# ---------------------------------------------------------------------------
# Generic / commodity product name (MD-02)
# ---------------------------------------------------------------------------
# Common Indian packaged-commodity / generic-name words (lowercase).
_GENERIC_COMMODITY_WORDS = {
    "flour", "atta", "maida", "sooji", "rava", "wheat", "milk", "butter",
    "ghee", "curd", "dahi", "paneer", "cheese", "lassi", "oil", "olive",
    "tea", "coffee", "sugar", "salt", "rice", "pulses", "dal", "lentils",
    "chips", "potato", "crisps", "biscuit", "biscuits", "cookies", "cookie",
    "wafer", "wafers", "chocolate", "chocolates", "noodles", "pasta", "soup",
    "juice", "jam", "honey", "pickle", "pickles", "spices", "masala",
    "namkeen", "bhujia", "snacks", "cereal", "cereals", "oats", "cornflakes",
    "ketchup", "sauce", "tomato", "mango", "lemon", "onion", "besan", "dahi",
    "haldi", "dhania", "jeera", "garam", "papad", "atta", "suji", "seviyan",
    "biryani", "chutney", "vinegar", "baking", "yeast", "dates", "nuts",
    "almonds", "cashews", "raisins", "seeds", "flakes", "cream", "custard",
    "icecream", "water", "mineral", "beverage", "syrup", "toffee", "lollipop",
    "corn", "popcorn", "maize", "jaggery", "gur", "sattu", "kheer", "poha",
    "flakes", "frozen", "konjac", "chia", "quinoa", "sharbat", "roasted",
}

# Words that should never be picked as a product-name fallback.
_PRODUCT_NAME_NOISE = {
    "mrp", "mre", "retail", "price", "sale", "net", "quantity", "qty",
    "weight", "wt", "mfd", "med", "mfg", "month", "year", "manufacture",
    "manufactured", "manufacturer", "packed", "batch", "license", "lic",
    "fssai", "phone", "toll", "free", "email", "care", "customer", "consumer",
    "ingredients", "nutritional", "nutrition", "values", "approx", "per",
    "taxes", "incl", "inclusive", "best", "before", "use", "plot", "road",
    "street", "pincode", "pin", "india", "pvt", "ltd", "limited",
    "corporation", "co", "po", "box", "page", "total", "fat", "protein",
    "carbohydrate", "dietary", "fiber", "energy", "calories", "cholesterol",
    "iron", "calcium", "sodium", "potassium", "trans", "saturated", "logo",
    "ref", "code", "no", "lot", "exp", "tel", "epo", "tollfree", "website",
    "www", "com", "in", "contains", "shelf", "storage", "keep", "store",
    "direction", "directions", "warranty", "made",
}


def _extract_product_name(zone_text: str) -> List[dict]:
    """Best-effort generic/commodity product name (MD-02).

    Value = the longest consecutive run of known generic-commodity words
    (e.g. 'WHEAT FLOUR', 'Potato', 'MILK'). Falls back to the first short
    Title-Case token that isn't declaration noise.
    """
    toks = zone_text.split()
    if not toks:
        return []

    # 1) longest consecutive run of known commodity words (max 2, so an
    #    ingredients list like 'Wheat Flour Maida Sugar' doesn't merge).
    best = ""
    i = 0
    while i < len(toks):
        if re.sub(r"[^A-Za-z]", "", toks[i]).lower() in _GENERIC_COMMODITY_WORDS:
            run = []
            j = i
            while (j < len(toks) and len(run) < 2):
                core = re.sub(r"[^A-Za-z]", "", toks[j]).lower()
                if core not in _GENERIC_COMMODITY_WORDS:
                    break
                run.append(core.capitalize())
                j += 1
            candidate = " ".join(run)
            if len(candidate) > len(best):
                best = candidate
            i = j if j > i else i + 1
        else:
            i += 1
    if best:
        return [{"value": best}]

    # 2) title-case fallback (single token, short).
    for t in toks:
        core = re.sub(r"[^A-Za-z]", "", t)
        if (len(core) >= 3 and core[0].isupper() and core[1:].islower()
                and core.lower() not in _PRODUCT_NAME_NOISE
                and core.lower() not in _GENERIC_COMMODITY_WORDS
                and not core.isdigit()):
            return [{"value": core}]
    return []


# ---------------------------------------------------------------------------
# Zone -> LMPC field mapping + extractor registry
# ---------------------------------------------------------------------------
ZONE_TO_FIELD = {
    "mrp_block": "mrp",
    "unit_sale_price_block": "unit_sale_price",
    "net_qty_block": "net_quantity",
    "mfg_date_block": "month_year_of_manufacture",
    "expiry_date_block": "use_by_date",
    "batch_block": "batch_number",
    "fssai_block": "fssai_license",
    "consumer_care_block": "consumer_care_details",
    "manufacturer_address_block": "manufacturer_packer_importer",
}


EXTRACTORS: List[Tuple[str, Callable[[str], List[dict]]]] = [
    ("generic_name_of_commodity", _extract_product_name),
    ("unit_sale_price", _extract_unit_sale_price),
    ("mrp", _extract_mrp),
    ("net_quantity", _extract_net_quantity),
    ("month_year_of_manufacture", _extract_mfg),
    ("use_by_date", _extract_expiry),
    ("fssai_license", _extract_fssai),
    ("batch_number", _extract_batch),
    ("consumer_phone", _extract_phone),
    ("consumer_email", _extract_email),
]