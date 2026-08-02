class EndorphinIntToString:
    """Convert an integer to text."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {"default": 1, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "convert"
    CATEGORY = "Endorphin Workshop/Utilities"

    def convert(self, value):
        return (str(value),)


NODE_CLASS_MAPPINGS = {"EndorphinIntToString": EndorphinIntToString}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinIntToString": "Endorphin Int to String"}
