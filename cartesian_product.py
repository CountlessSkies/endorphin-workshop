class EndorphinCartesianProduct:
    """A 2D/3D counter advanced once for each Queue Prompt batch item."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "dimensions": (["2D (pairs)", "3D (triples)"], {
                    "default": "2D (pairs)",
                    "tooltip": "Choose whether to advance pairs or triples.",
                }),
                "max_value_1": ("INT", {"default": 1, "min": 1, "max": 1000000, "step": 1}),
                "max_value_2": ("INT", {"default": 1, "min": 1, "max": 1000000, "step": 1}),
                "max_value_3": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000,
                    "step": 1,
                    "tooltip": "Used only in 3D mode.",
                }),
                "value_1": ("INT", {"default": 1, "min": 1, "max": 1000000, "step": 1}),
                "value_2": ("INT", {"default": 1, "min": 1, "max": 1000000, "step": 1}),
                "value_3": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000,
                    "step": 1,
                    "tooltip": "Used only in 3D mode.",
                }),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT")
    RETURN_NAMES = ("value_1", "value_2", "value_3")
    FUNCTION = "get_values"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_values(self, dimensions, max_value_1, max_value_2, max_value_3, value_1, value_2, value_3):
        return (value_1, value_2, value_3 if dimensions == "3D (triples)" else 0)


NODE_CLASS_MAPPINGS = {
    "EndorphinCartesianProduct": EndorphinCartesianProduct,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinCartesianProduct": "Endorphin Cartesian Product (2D/3D)",
}
