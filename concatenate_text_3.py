class EndorphinConcatenateText3:
    """Concatenate exactly three text values with an optional delimiter."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string_a": ("STRING", {"default": "", "multiline": True}),
                "string_b": ("STRING", {"default": "", "multiline": True}),
                "string_c": ("STRING", {"default": "", "multiline": True}),
                "delimiter": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "concatenate"
    CATEGORY = "Endorphin Workshop/Text"

    def concatenate(self, string_a, string_b, string_c, delimiter):
        return (delimiter.join((string_a, string_b, string_c)),)


NODE_CLASS_MAPPINGS = {
    "EndorphinConcatenateText3": EndorphinConcatenateText3,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinConcatenateText3": "Endorphin Concatenate Text (3)",
}
