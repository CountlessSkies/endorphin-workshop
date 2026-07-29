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
                "file_format": (["png", "jpeg", "webp"], {"default": "png"}),
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
        file_format="png",
        quality=95,
        png_compress_level=4,
        prompt=None,
        extra_pnginfo=None,
    ):
        output_dir, subfolder = resolve_output_folder(output_folder, custom_output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)

        full_output_folder, filename, counter, _, _ = folder_paths.get_save_image_path(
            filename_prefix,
            str(output_dir),
            images[0].shape[1],
            images[0].shape[0],
        )
        results = []
        for batch_number, image in enumerate(images):
            array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
            pil_image = Image.fromarray(array)

            current_filename = filename.replace("%batch_num%", str(batch_number))
            file_name = f"{current_filename}_{counter:05}_.{file_format}"
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

            results.append({
                "filename": file_name,
                "subfolder": subfolder,
                "type": "output",
            })
            counter += 1

        return {"ui": {"images": results}, "result": (images,)}


NODE_CLASS_MAPPINGS = {
    "EndorphinSaveImageAdvanced": EndorphinSaveImageAdvanced,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinSaveImageAdvanced": "Endorphin Save Image Advanced",
}
