class EndorphinPlusOne:
    """Add one to an integer."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {"default": 1, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value_plus_1",)
    FUNCTION = "add_one"
    CATEGORY = "Endorphin Workshop/Utilities"

    def add_one(self, value):
        return (value + 1,)


NODE_CLASS_MAPPINGS = {"EndorphinPlusOne": EndorphinPlusOne}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinPlusOne": "Endorphin Plus 1"}
