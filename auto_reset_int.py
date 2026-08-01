class EndorphinAutoResetInt:
    """An integer that restores its pre-queue value after batch submission."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 0xFFFFFFFFFFFFFFFF,
                    "step": 1,
                }),
                "auto_increment": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Increase value by 1 for each Queue Prompt batch item.",
                }),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_value"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_value(self, value, auto_increment):
        return (value,)


NODE_CLASS_MAPPINGS = {
    "EndorphinAutoResetInt": EndorphinAutoResetInt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinAutoResetInt": "Endorphin Auto Reset Int",
}
