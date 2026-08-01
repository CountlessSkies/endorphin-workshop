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
    """Select a configurable color swatch and return its assigned integer."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "palette": ("ENDORPHIN_COLOR_PALETTE", {
                    "default": json.dumps(DEFAULT_PALETTE, separators=(",", ":")),
                    "tooltip": "Configure and select color slots directly in the node.",
                }),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_selected_value"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_selected_value(self, palette):
        try:
            data = json.loads(palette) if isinstance(palette, str) else palette
            colors = data.get("colors", [])
            selected = int(data.get("selected", 0))
            if not colors:
                return (0,)
            selected = max(0, min(selected, len(colors) - 1))
            return (int(colors[selected].get("value", 0)),)
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            return (0,)


NODE_CLASS_MAPPINGS = {
    "EndorphinColorPalettePicker": EndorphinColorPalettePicker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinColorPalettePicker": "Endorphin Color Palette Picker",
}
