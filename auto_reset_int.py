class EndorphinAutoResetInt:
    """An integer with After Generate controls and a queue-end reset value."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 0xFFFFFFFFFFFFFFFF,
                    "step": 1,
                    "control_after_generate": True,
                    "tooltip": "Use the After Generate control to keep, increment, decrement, or randomize the value after a run.",
                }),
                "reset_value": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 0xFFFFFFFFFFFFFFFF,
                    "step": 1,
                    "tooltip": "Value restored immediately after the queue has been submitted.",
                }),
                "reset_after_batch": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Restore value to reset_value immediately after the queue is submitted.",
                }),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_value"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_value(self, value, reset_value, reset_after_batch):
        return (value,)


NODE_CLASS_MAPPINGS = {
    "EndorphinAutoResetInt": EndorphinAutoResetInt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinAutoResetInt": "Endorphin Auto Reset Int",
}
