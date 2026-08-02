MAX_DESIGN_PHASES = 20


def design_phase_inputs():
    defaults = ["redesign", "colorway"]
    return {
        f"design_phase_{index:02d}": (
            "STRING",
            {"default": defaults[index - 1] if index <= len(defaults) else ""},
        )
        for index in range(1, MAX_DESIGN_PHASES + 1)
    }


def get_selected_design_phase(count, index, values):
    if index > count:
        raise ValueError("design_phase_index must not be higher than design_phase_count.")
    phase = values.get(f"design_phase_{index:02d}")
    if isinstance(phase, str) and phase.strip():
        return phase.strip()

    # Older workflows may not contain the hidden phase widgets yet. Keep them
    # executable while the frontend writes the values back on the next save.
    defaults = ["redesign", "colorway"]
    return defaults[index - 1] if index <= len(defaults) else f"phase_{index:02d}"


class EndorphinEtsyListingSelector:
    """Select a listing and a configurable design phase."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "project_root": ("STRING", {"default": r"G:\My Drive\_Etsy\_Listing"}),
                "listing_number": ("INT", {"default": 1, "min": 1, "max": 999999, "step": 1}),
                "design_phase_count": ("INT", {"default": 2, "min": 1, "max": MAX_DESIGN_PHASES, "step": 1}),
                "design_phase_index": ("INT", {"default": 1, "min": 1, "max": MAX_DESIGN_PHASES, "step": 1}),
                **design_phase_inputs(),
            },
        }

    RETURN_TYPES = ("STRING", "INT", "STRING", "INT")
    RETURN_NAMES = ("project_root", "listing_number", "design_phase", "design_phase_index")
    FUNCTION = "select"
    CATEGORY = "Endorphin Workshop/Etsy"

    def select(self, project_root, listing_number, design_phase_count, design_phase_index, **kwargs):
        phase = get_selected_design_phase(design_phase_count, design_phase_index, kwargs)
        return project_root, listing_number, phase, design_phase_index


NODE_CLASS_MAPPINGS = {"EndorphinEtsyListingSelector": EndorphinEtsyListingSelector}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinEtsyListingSelector": "Endorphin Etsy Listing Selector"}
