class EndorphinTextLines20:
    """Split multiline text into up to twenty individual string outputs."""

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
            },
        }

    RETURN_TYPES = ("STRING",) * 20
    RETURN_NAMES = tuple(f"line_{index:02d}" for index in range(1, 21))
    FUNCTION = "split_lines"
    CATEGORY = "Endorphin Workshop/Utilities"

    def split_lines(self, text):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return tuple((lines + [""] * 20)[:20])


NODE_CLASS_MAPPINGS = {
    "EndorphinTextLines20": EndorphinTextLines20,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinTextLines20": "Endorphin Text Lines (20)",
}
