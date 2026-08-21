import json
import re


DEFAULT_PALETTE = {
    "selected": 0,
    "colors": [
        {"name": "Red", "hex": "#EF4444", "code": "RED", "value": 1},
        {"name": "Green", "hex": "#22C55E", "code": "GRN", "value": 2},
        {"name": "Blue", "hex": "#3B82F6", "code": "BLU", "value": 3},
    ],
}


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


class EndorphinEtsyColorPalette:
    """Editable Etsy color palette with a stable three-letter color code."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"palette": ("ENDORPHIN_ETSY_COLOR_PALETTE", {
            "default": json.dumps(DEFAULT_PALETTE, separators=(",", ":")),
            "tooltip": "The canonical Etsy colorway palette. Each code must be unique and three uppercase letters.",
        })}}

    RETURN_TYPES = ("INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("value", "color_name", "hex", "color_code")
    FUNCTION = "get_selected_color"
    CATEGORY = "Endorphin Workshop/Etsy"

    def get_selected_color(self, palette):
        data = json.loads(palette) if isinstance(palette, str) else palette
        if not isinstance(data, dict):
            raise ValueError("Invalid Etsy color palette.")
        colors = data.get("colors", [])
        if not colors:
            return (0, "", "", "")
        seen_codes = set()
        normalized = []
        for index, color in enumerate(colors):
            if not isinstance(color, dict):
                raise ValueError(f"Palette color {index + 1} is invalid.")
            name = str(color.get("name", "")).strip()
            code = str(color.get("code") or suggest_color_code(name)).strip().upper()
            if not re.fullmatch(r"[A-Z]{3}", code):
                raise ValueError(f"Color code for '{name or index + 1}' must be exactly three letters A-Z.")
            if code in seen_codes:
                raise ValueError(f"Color code '{code}' is duplicated in the palette.")
            seen_codes.add(code)
            normalized.append((name, str(color.get("hex", "")).upper(), code, int(color.get("value", index + 1))))
        selected = max(0, min(int(data.get("selected", 0)), len(normalized) - 1))
        name, hex_value, code, value = normalized[selected]
        return (value, name, hex_value, code)


NODE_CLASS_MAPPINGS = {"EndorphinEtsyColorPalette": EndorphinEtsyColorPalette}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinEtsyColorPalette": "Endorphin Etsy Color Palette"}
