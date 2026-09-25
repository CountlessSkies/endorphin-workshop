import json
import re


# The business color catalogue is intentionally ordered and immutable. HEX is
# user-editable because it may vary between a supplier's product variants.
FIXED_COLORS = (
    ("Military Green", "#4B5320", "MGR"),
    ("Carolina Blue", "#7BAFD4", "CBL"),
    ("Navy", "#1F2A44", "NVY"),
    ("Black", "#000000", "BLK"),
    ("Sand", "#D8C3A5", "SND"),
    ("Grey", "#8A8A8A", "GRY"),
    ("White", "#FFFFFF", "WHT"),
    ("Sport Grey", "#B7B7B7", "SGR"),
    ("Ash", "#D5D5D5", "ASH"),
    ("Orange", "#E87522", "ORG"),
    ("Light Blue", "#9BCBEB", "LBL"),
    ("Forest Green", "#1F4D36", "FGR"),
    ("Beige", "#D6C6A9", "BEI"),
    ("Maroon", "#7B2639", "MRN"),
    ("Light Pink", "#F4B6C2", "LPK"),
    ("Brown", "#6B4423", "BRN"),
    ("Chocolate", "#4A2C20", "CHC"),
)

DEFAULT_PALETTE = {
    "selected": 0,
    "colors": [
        {"name": name, "hex": hex_value, "code": code, "value": index}
        for index, (name, hex_value, code) in enumerate(FIXED_COLORS, start=1)
    ],
}


def fixed_palette_data(palette):
    """Return the fixed catalogue while retaining valid user-edited HEX values."""
    try:
        data = json.loads(palette) if isinstance(palette, str) else palette
    except json.JSONDecodeError:
        data = {}
    data = data if isinstance(data, dict) else {}
    supplied = data.get("colors") if isinstance(data.get("colors"), list) else []
    # A short/legacy palette is not this catalogue, so do not map its unrelated
    # swatches onto the new colours by index.
    preserve_hex = len(supplied) == len(FIXED_COLORS)
    colors = []
    for index, (name, default_hex, code) in enumerate(FIXED_COLORS):
        candidate = supplied[index] if preserve_hex and isinstance(supplied[index], dict) else {}
        hex_value = str(candidate.get("hex", default_hex)).strip().upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", hex_value):
            hex_value = default_hex
        colors.append({"name": name, "hex": hex_value, "code": code, "value": index + 1})
    selected = max(0, min(int(data.get("selected", 0) or 0), len(colors) - 1))
    return {"selected": selected, "colors": colors}


def suggest_color_code(name):
    words = re.findall(r"[A-Za-z]+", str(name or "").upper())
    if not words:
        return "CLR"
    if len(words) >= 3:
        return "".join(word[0] for word in words[:3])
    if len(words) == 2:
        consonants = "".join(letter for letter in words[1] if letter not in "AEIOU")
        return words[0][0] + consonants[:2] if len(consonants) >= 2 else (words[0][0] + words[1][:2]).ljust(3, words[0][0])
    consonants = "".join(letter for letter in words[0] if letter not in "AEIOU")
    return consonants[:3] if len(consonants) >= 3 else words[0][:3].ljust(3, "X")


def selected_color_data(palette):
    """Validate a palette and return its selected color as normalized metadata."""
    try:
        data = json.loads(palette) if isinstance(palette, str) else palette
    except json.JSONDecodeError as error:
        raise ValueError("Invalid Etsy color palette.") from error
    if not isinstance(data, dict):
        raise ValueError("Invalid Etsy color palette.")
    normalized = fixed_palette_data(data)
    selected = normalized["selected"]
    color = normalized["colors"][selected]
    name, hex_value, code = color["name"], color["hex"], color["code"]
    return {
        "colorway_index": selected + 1,
        "color_name": name,
        "color_hex": hex_value,
        "color_code": code,
        "prompt_color": f"{name} (hex {hex_value})",
    }


class EndorphinEtsyColorPalette:
    """Fixed Etsy apparel palette with editable HEX swatches."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"palette": ("ENDORPHIN_ETSY_COLOR_PALETTE", {
            "default": json.dumps(DEFAULT_PALETTE, separators=(",", ":")),
            "tooltip": "Fixed 17-colour apparel catalogue. Only HEX swatches are editable.",
        })}}

    RETURN_TYPES = ("INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("value", "color_name", "hex", "color_code")
    FUNCTION = "get_selected_color"
    CATEGORY = "Endorphin Workshop/Etsy"

    def get_selected_color(self, palette):
        colors = fixed_palette_data(palette)["colors"]
        selected = selected_color_data(palette)
        return (selected["colorway_index"], selected["color_name"], selected["color_hex"], selected["color_code"])


NODE_CLASS_MAPPINGS = {"EndorphinEtsyColorPalette": EndorphinEtsyColorPalette}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinEtsyColorPalette": "Endorphin Etsy Color Palette"}
