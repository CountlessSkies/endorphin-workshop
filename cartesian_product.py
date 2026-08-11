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
                "max_value_1": ("INT", {"default": 1, "min": -1000000, "max": 1000000, "step": 1}),
                "max_value_2": ("INT", {"default": 1, "min": -1000000, "max": 1000000, "step": 1}),
                "max_value_3": ("INT", {
                    "default": 1,
                    "min": -1000000,
                    "max": 1000000,
                    "step": 1,
                    "tooltip": "Used only in 3D mode.",
                }),
                "min_value_1": ("INT", {"default": 1, "min": -1000000, "max": 1000000, "step": 1}),
                "min_value_2": ("INT", {"default": 1, "min": -1000000, "max": 1000000, "step": 1}),
                "min_value_3": ("INT", {
                    "default": 1,
                    "min": -1000000,
                    "max": 1000000,
                    "step": 1,
                    "tooltip": "Used only in 3D mode.",
                }),
                "value_1": ("INT", {"default": 1, "min": -1000000, "max": 1000000, "step": 1}),
                "value_2": ("INT", {"default": 1, "min": -1000000, "max": 1000000, "step": 1}),
                "value_3": ("INT", {
                    "default": 1,
                    "min": -1000000,
                    "max": 1000000,
                    "step": 1,
                    "tooltip": "Used only in 3D mode.",
                }),
                "auto_increment": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Advance to the next combination after every Queue Prompt batch item.",
                }),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT")
    RETURN_NAMES = ("value_1", "value_2", "value_3")
    FUNCTION = "get_values"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_values(
        self, dimensions, max_value_1, max_value_2, max_value_3, min_value_1,
        min_value_2, min_value_3, value_1, value_2, value_3, auto_increment,
    ):
        if min_value_1 > max_value_1 or min_value_2 > max_value_2 or min_value_3 > max_value_3:
            raise ValueError("Each min_value must be less than or equal to its max_value.")
        value_1 = min_value_1 if value_1 < min_value_1 or value_1 > max_value_1 else value_1
        value_2 = min_value_2 if value_2 < min_value_2 or value_2 > max_value_2 else value_2
        value_3 = min_value_3 if value_3 < min_value_3 or value_3 > max_value_3 else value_3
        return (value_1, value_2, value_3 if dimensions == "3D (triples)" else 0)


NODE_CLASS_MAPPINGS = {
    "EndorphinCartesianProduct": EndorphinCartesianProduct,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinCartesianProduct": "Endorphin Cartesian Product (2D/3D)",
}
