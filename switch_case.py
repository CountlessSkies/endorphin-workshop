class _AnyType(str):
    """A ComfyUI socket type that can connect to any other socket type."""

    def __ne__(self, _other):
        return False


ANY_TYPE = _AnyType("*")
MAX_SLOTS = 100


class EndorphinSwitchCase20:
    """Pass through one of twenty optional inputs, selected by its case number."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "select": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": MAX_SLOTS,
                    "step": 1,
                    "tooltip": "The case number whose input will be returned.",
                }),
                "input_count": ("INT", {"default": 5, "min": 1, "max": MAX_SLOTS, "step": 1}),
            },
            # Optional sockets let a workflow connect only the cases it needs.
            "optional": {
                f"case_{index:02d}": (ANY_TYPE, {
                    "tooltip": f"Value returned when select is {index}.",
                })
                for index in range(1, MAX_SLOTS + 1)
            },
        }

    RETURN_TYPES = (ANY_TYPE,)
    RETURN_NAMES = ("value",)
    FUNCTION = "switch"
    CATEGORY = "Endorphin Workshop/Utilities"

    def switch(self, select, input_count, **kwargs):
        if select > input_count:
            raise ValueError(f"Switch Case: select ({select}) is higher than input_count ({input_count}).")
        case_name = f"case_{select:02d}"
        if case_name not in kwargs:
            raise ValueError(
                f"Switch Case 20: {case_name} is not connected. "
                f"Connect an input for case {select} or choose a connected case."
            )
        return (kwargs[case_name],)


NODE_CLASS_MAPPINGS = {
    "EndorphinSwitchCase20": EndorphinSwitchCase20,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinSwitchCase20": "Endorphin Switch Case (20)",
}
