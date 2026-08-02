class EndorphinIntAndNext:
    """Return an integer and its next value."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {"default": 1, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1}),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("value", "value_plus_1")
    FUNCTION = "get_values"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_values(self, value):
        return value, value + 1


NODE_CLASS_MAPPINGS = {"EndorphinIntAndNext": EndorphinIntAndNext}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinIntAndNext": "Endorphin Int and Next"}
