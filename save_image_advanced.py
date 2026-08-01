import json
import os
from pathlib import Path

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths


def get_output_folders():
    """Return existing output subfolders for the folder selector."""
    output_root = Path(folder_paths.get_output_directory()).resolve()
    folders = ["(output root)"]
    if not output_root.exists():
        return folders

    for directory, subdirectories, _ in os.walk(output_root):
        subdirectories[:] = [name for name in subdirectories if not (Path(directory) / name).is_symlink()]
        relative = Path(directory).relative_to(output_root)
        if relative.parts:
            folders.append(relative.as_posix())

    return folders


def resolve_output_folder(selected_folder, custom_folder):
    """Resolve an output subfolder or a user-supplied absolute path."""
    output_root = Path(folder_paths.get_output_directory()).resolve()
    requested = custom_folder.strip() if custom_folder and custom_folder.strip() else selected_folder
    if requested == "(output root)" or not requested:
        return output_root, ""

    candidate_path = Path(requested).expanduser()
    if candidate_path.is_absolute():
        return candidate_path.resolve(), ""

    candidate = (output_root / candidate_path).resolve()
    try:
        relative = candidate.relative_to(output_root)
    except ValueError as error:
        raise ValueError("Invalid output folder path.") from error
    return candidate, relative.as_posix()


def append_subfolder(base_folder, subfolder):
    """Append a relative save subfolder without allowing traversal outside base."""
    base = Path(base_folder).resolve()
    if not subfolder or not subfolder.strip():
        return base
    requested = Path(subfolder.strip())
    if requested.is_absolute():
        raise ValueError("Subfolder must be a relative path.")
    destination = (base / requested).resolve()
    try:
        destination.relative_to(base)
    except ValueError as error:
        raise ValueError("Subfolder must stay inside the selected output folder.") from error
    return destination


def append_numbered_subfolder(base_folder, subfolder, subfolder_number, subfolder_digits):
    destination = append_subfolder(base_folder, subfolder)
    if subfolder_number == 0:
        return destination
    return append_subfolder(destination, f"{subfolder_number:0{subfolder_digits}d}")


class EndorphinSaveImageAdvanced:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Images to save."}),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "tooltip": "File name prefix. ComfyUI dynamic prompt formatting is supported.",
                }),
                "output_folder": (get_output_folders(), {
                    "default": "(output root)",
                    "tooltip": "Choose an existing folder inside ComfyUI/output.",
                }),
                "custom_output_folder": ("STRING", {
                    "default": "",
                    "placeholder": "Optional path, e.g. D:\\Images\\Job_01",
                    "tooltip": "Optional. Overrides Output Folder. Absolute paths may be outside ComfyUI/output.",
                }),
                "subfolder": ("STRING", {
                    "default": "",
                    "placeholder": "Optional subfolder, e.g. job_01/selected",
                    "tooltip": "Optional relative subfolder inside the selected output folder.",
                }),
                "subfolder_number": ("INT", {"default": 0, "min": 0, "max": 1000000000, "step": 1, "tooltip": "Optional numeric subfolder. Set 0 to disable."}),
                "subfolder_digits": ("INT", {"default": 3, "min": 1, "max": 12, "step": 1, "tooltip": "Digits for numeric subfolder: 3 makes 001."}),
                "file_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "suffix_digits": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 12,
                    "step": 1,
                    "tooltip": "Number of digits in the numeric suffix. Use 2 for 01, 02; use 5 for 00001, 00002.",
                }),
                "overwrite": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Save without a numeric suffix and overwrite an existing file with the same name.",
                }),
                "quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "JPEG and WEBP quality. PNG uses lossless compression.",
                }),
                "png_compress_level": ("INT", {
                    "default": 4,
                    "min": 0,
                    "max": 9,
                    "step": 1,
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Endorphin Workshop/Utilities"

    def save_images(
        self,
        images,
        filename_prefix="ComfyUI",
        output_folder="(output root)",
        custom_output_folder="",
        subfolder="",
        subfolder_number=0,
        subfolder_digits=3,
        file_format="png",
        suffix_digits=3,
        overwrite=False,
        quality=95,
        png_compress_level=4,
        prompt=None,
        extra_pnginfo=None,
    ):
        output_dir, _ = resolve_output_folder(output_folder, custom_output_folder)
        output_dir = append_numbered_subfolder(output_dir, subfolder, subfolder_number, subfolder_digits)
        output_dir.mkdir(parents=True, exist_ok=True)

        full_output_folder, filename, counter, _, _ = folder_paths.get_save_image_path(
            filename_prefix,
            str(output_dir),
            images[0].shape[1],
            images[0].shape[0],
        )
        for batch_number, image in enumerate(images):
            array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
            pil_image = Image.fromarray(array)

            current_filename = filename.replace("%batch_num%", str(batch_number))
            file_name = (
                f"{current_filename}.{file_format}"
                if overwrite
                else f"{current_filename}_{counter:0{suffix_digits}d}.{file_format}"
            )
            file_path = os.path.join(full_output_folder, file_name)

            if file_format == "png":
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for key, value in extra_pnginfo.items():
                        metadata.add_text(key, json.dumps(value))
                pil_image.save(file_path, pnginfo=metadata, compress_level=png_compress_level)
            elif file_format == "jpeg":
                pil_image.convert("RGB").save(file_path, quality=quality, optimize=True)
            else:
                pil_image.save(file_path, format="WEBP", quality=quality)

            counter += 1

        # Keep the IMAGE output available to downstream nodes without adding
        # ComfyUI's image-thumbnail preview to this save node.
        return {"result": (images,)}


NODE_CLASS_MAPPINGS = {
    "EndorphinSaveImageAdvanced": EndorphinSaveImageAdvanced,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinSaveImageAdvanced": "Endorphin Save Image Advanced",
}
