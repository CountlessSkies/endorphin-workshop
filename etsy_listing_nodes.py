from pathlib import Path

from .folder_image_loader import EndorphinFolderImageLoader
from .save_image_advanced import EndorphinSaveImageAdvanced

MAX_ASSET_FOLDERS = 20


def asset_folder_inputs():
    defaults = ["original", "creative", "colors"]
    return {f"asset_folder_{index:02d}": ("STRING", {"default": defaults[index - 1] if index <= 3 else ""}) for index in range(1, MAX_ASSET_FOLDERS + 1)}


def get_selected_asset_folder(count, index, values):
    if index > count:
        raise ValueError("asset_folder_index must not be higher than asset_folder_count.")
    name = values.get(f"asset_folder_{index:02d}", "").strip()
    if not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("Choose a valid relative asset folder name.")
    return name


class EndorphinEtsyListingImageLoader(EndorphinFolderImageLoader):
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "INT")
    RETURN_NAMES = ("image", "file_name", "file_name_no_ext", "image_number")

    @classmethod
    def INPUT_TYPES(cls):
        data = EndorphinFolderImageLoader.INPUT_TYPES()["required"].copy()
        data.pop("folder_path")
        data.pop("subfolder")
        return {"required": {"project_root": ("STRING", {"default": r"G:\My Drive\_Etsy\_Listing"}), "listing_number": ("INT", {"default": 1, "min": 1, "max": 999999}), "asset_folder_count": ("INT", {"default": 3, "min": 1, "max": MAX_ASSET_FOLDERS}), "asset_folder_index": ("INT", {"default": 1, "min": 1, "max": MAX_ASSET_FOLDERS}), **asset_folder_inputs(), **data}}

    def load_image(self, project_root, listing_number, asset_folder_count, asset_folder_index, sort, image_index, auto_increment, loop, **kwargs):
        path = Path(project_root) / f"{listing_number:03d}" / get_selected_asset_folder(asset_folder_count, asset_folder_index, kwargs)
        image, _mask, file_name, file_name_no_ext, number = super().load_image(str(path), "", sort, image_index, auto_increment, loop)
        return image, file_name, file_name_no_ext, number

    @classmethod
    def IS_CHANGED(cls, project_root, listing_number, asset_folder_count, asset_folder_index, sort, image_index, auto_increment, loop, **kwargs):
        path = Path(project_root) / f"{listing_number:03d}" / get_selected_asset_folder(asset_folder_count, asset_folder_index, kwargs)
        return EndorphinFolderImageLoader.IS_CHANGED(str(path), "", sort, image_index, auto_increment, loop)


class EndorphinEtsyListingSaveImage(EndorphinSaveImageAdvanced):
    @classmethod
    def INPUT_TYPES(cls):
        data = EndorphinSaveImageAdvanced.INPUT_TYPES()["required"].copy()
        images = data.pop("images")
        data.pop("output_folder")
        data.pop("custom_output_folder")
        data.pop("subfolder")
        return {"required": {
            "images": images,
            "project_root": ("STRING", {"default": r"G:\My Drive\_Etsy\_Listing"}),
            "listing_number": ("INT", {"default": 1, "min": 1, "max": 999999}),
            "asset_folder_count": ("INT", {"default": 3, "min": 1, "max": MAX_ASSET_FOLDERS, "step": 1}),
            "asset_folder_index": ("INT", {"default": 1, "min": 1, "max": MAX_ASSET_FOLDERS, "step": 1}),
            **asset_folder_inputs(),
            **data,
        }, "hidden": EndorphinSaveImageAdvanced.INPUT_TYPES()["hidden"]}

    def save_images(self, images, project_root, listing_number, asset_folder_count, asset_folder_index, filename_prefix="ComfyUI", file_format="png", suffix_digits=3, overwrite=False, quality=95, png_compress_level=4, prompt=None, extra_pnginfo=None, **kwargs):
        asset_path = str(Path(project_root) / f"{listing_number:03d}" / get_selected_asset_folder(asset_folder_count, asset_folder_index, kwargs))
        return super().save_images(images, filename_prefix, "(output root)", asset_path, "", file_format, suffix_digits, overwrite, quality, png_compress_level, prompt, extra_pnginfo)


NODE_CLASS_MAPPINGS = {
    "EndorphinEtsyListingImageLoader": EndorphinEtsyListingImageLoader,
    "EndorphinEtsyListingSaveImage": EndorphinEtsyListingSaveImage,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinEtsyListingImageLoader": "Endorphin Etsy Listing Image Loader",
    "EndorphinEtsyListingSaveImage": "Endorphin Etsy Listing Save Image",
}
