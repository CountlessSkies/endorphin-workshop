import math


# Exact option list/type of RH GPT Image 2 Image to Image Official Stable.
# A ComfyUI combo is represented as a list, so this output can connect directly
# to its aspectRatio input after the widget is converted to an input socket.
RH_G2_OFFICIAL_IMAGE_TO_IMAGE_RATIOS = [
    "1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4",
    "4:3", "4:5", "5:4", "9:16", "21:9", "9:21", "16:9",
]
SUPPORTED_RATIOS = tuple(RH_G2_OFFICIAL_IMAGE_TO_IMAGE_RATIOS)


def _ratio_value(ratio):
    width, height = ratio.split(":", 1)
    return int(width) / int(height)


class EndorphinRHAspectRatio:
    """Return the closest RunningHub image-to-image aspect ratio for an image."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE",)}}

    RETURN_TYPES = (RH_G2_OFFICIAL_IMAGE_TO_IMAGE_RATIOS,)
    RETURN_NAMES = ("aspect_ratio",)
    FUNCTION = "get_aspect_ratio"
    CATEGORY = "Endorphin Workshop/Utilities"

    def get_aspect_ratio(self, image):
        if image.ndim != 4 or image.shape[1] <= 0 or image.shape[2] <= 0:
            raise ValueError("Expected an IMAGE tensor shaped [batch, height, width, channels].")
        height, width = int(image.shape[1]), int(image.shape[2])
        image_ratio = width / height
        # Log-space distance treats equivalent landscape/portrait scale changes
        # consistently and selects the visually nearest supported ratio.
        closest = min(
            SUPPORTED_RATIOS,
            key=lambda ratio: abs(math.log(image_ratio / _ratio_value(ratio))),
        )
        return (closest,)


NODE_CLASS_MAPPINGS = {"EndorphinRHAspectRatio": EndorphinRHAspectRatio}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinRHAspectRatio": "Endorphin RH Aspect Ratio From Image"}
