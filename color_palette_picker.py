import json


DEFAULT_PALETTE = {
    "selected": 0,
    "colors": [
        {"name": "Red", "hex": "#EF4444", "value": 1},
        {"name": "Green", "hex": "#22C55E", "value": 2},
        {"name": "Blue", "hex": "#3B82F6", "value": 3},
    ],
}


class EndorphinColorPalettePicker:
    """Legacy palette picker retained for existing workflows."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "palette": ("ENDORPHIN_COLOR_PALETTE", {
                    "default": json.dumps(DEFAULT_PALETTE, separators=(",", ":")),
                    "tooltip": "Legacy palette picker. Use Endorphin Etsy Color Palette for new Etsy workflows.",
                }),
            },
        }

    RETURN_TYPES = ("INT", "STRING", "STRING")
    RETURN_NAMES = ("value", "color_name", "hex")
    FUNCTION = "get_selected_value"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_selected_value(self, palette):
        try:
            data = json.loads(palette) if isinstance(palette, str) else palette
            colors = data.get("colors", [])
            selected = int(data.get("selected", 0))
            if not colors:
                return (0, "", "")
            selected = max(0, min(selected, len(colors) - 1))
            color = colors[selected]
            return (
                int(color.get("value", 0)),
                str(color.get("name", "")),
                str(color.get("hex", "")).upper(),
            )
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            return (0, "", "")


NODE_CLASS_MAPPINGS = {
    "EndorphinColorPalettePicker": EndorphinColorPalettePicker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinColorPalettePicker": "Endorphin Color Palette Picker (Legacy)",
}
