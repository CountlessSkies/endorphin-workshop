import json

from .etsy_color_palette import DEFAULT_PALETTE, fixed_palette_data


class EndorphinColorPalettePicker:
    """Fixed apparel palette with queue-time selection increment support."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "palette": ("ENDORPHIN_COLOR_PALETTE", {
                    "default": json.dumps(DEFAULT_PALETTE, separators=(",", ":")),
                    "tooltip": "Fixed 17-colour apparel catalogue. Click a swatch to select it; HEX remains editable.",
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
            data = fixed_palette_data(palette)
            colors = data["colors"]
            selected = int(data["selected"]) if index_value is None else int(index_value) - 1
            selected = max(0, min(selected, len(colors) - 1))
            color = colors[selected]
            return (
                int(color["value"]),
                str(color["name"]),
                str(color.get("hex", "")).upper(),
                str(color["code"]).upper(),
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
