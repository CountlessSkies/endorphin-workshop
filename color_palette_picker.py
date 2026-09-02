import json

from .etsy_color_palette import suggest_color_code


DEFAULT_PALETTE = {
    "selected": 0,
    "colors": [
        {"name": "Red", "hex": "#EF4444", "code": "RED", "value": 1},
        {"name": "Green", "hex": "#22C55E", "code": "GRN", "value": 2},
        {"name": "Blue", "hex": "#3B82F6", "code": "BLU", "value": 3},
    ],
}


class EndorphinColorPalettePicker:
    """Editable color palette with queue-time selection increment support."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "palette": ("ENDORPHIN_COLOR_PALETTE", {
                    "default": json.dumps(DEFAULT_PALETTE, separators=(",", ":")),
                    "tooltip": "Click a swatch to select it. The selected color supplies every output.",
                }),
                "auto_increment": ("BOOLEAN", {"default": False, "tooltip": "Advance the selected palette index for every queued batch item."}),
                "loop": ("BOOLEAN", {"default": True, "tooltip": "When auto increment reaches the final color, return to the first color."}),
            },
            "optional": {
                "index_value": ("INT", {"forceInput": True, "tooltip": "Optional 1-based palette index. When connected, overrides the selected row."}),
            },
        }

    RETURN_TYPES = ("INT", "STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("value", "color_name", "hex", "color_code", "selected_index")
    FUNCTION = "get_selected_value"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_selected_value(self, palette, auto_increment=False, loop=True, index_value=None):
        try:
            data = json.loads(palette) if isinstance(palette, str) else palette
            colors = data.get("colors", [])
            if not colors:
                return (0, "", "", "", 0)
            selected = int(data.get("selected", 0)) if index_value is None else int(index_value) - 1
            selected = max(0, min(selected, len(colors) - 1))
            color = colors[selected]
            return (
                int(color.get("value", 0)),
                str(color.get("name", "")),
                str(color.get("hex", "")).upper(),
                str(color.get("code") or suggest_color_code(color.get("name", ""))).upper(),
                selected + 1,
            )
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            return (0, "", "", "", 0)


NODE_CLASS_MAPPINGS = {
    "EndorphinColorPalettePicker": EndorphinColorPalettePicker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinColorPalettePicker": "Endorphin Color Palette Picker",
}
