class EndorphinAutoResetInt:
    """An integer value that the frontend resets to 1 after execution."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 0xFFFFFFFFFFFFFFFF,
                    "step": 1,
                    "tooltip": "Outputs this integer, then resets to 1 after the queue finishes this node.",
                }),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_value"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_value(self, value):
        return (value,)


NODE_CLASS_MAPPINGS = {
    "EndorphinAutoResetInt": EndorphinAutoResetInt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinAutoResetInt": "Endorphin Auto Reset Int",
}
