MAX_SLOTS = 100


class EndorphinTextLines20:
    """Split multiline text into a configurable number of string outputs."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "dynamicPrompts": False,
                    "tooltip": "One value per line. Empty lines are ignored.",
                }),
                "output_count": ("INT", {"default": 5, "min": 1, "max": MAX_SLOTS, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",) * MAX_SLOTS
    RETURN_NAMES = tuple(f"line_{index:02d}" for index in range(1, MAX_SLOTS + 1))
    FUNCTION = "split_lines"
    CATEGORY = "Endorphin Workshop/Utilities"

    def split_lines(self, text, output_count):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return tuple((lines + [""] * MAX_SLOTS)[:MAX_SLOTS])


NODE_CLASS_MAPPINGS = {
    "EndorphinTextLines20": EndorphinTextLines20,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinTextLines20": "Endorphin Text Lines (20)",
}
