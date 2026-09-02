import re
from io import BytesIO
from pathlib import Path

import numpy as np
import torch
from aiohttp import web
from PIL import Image, ImageOps
from server import PromptServer

IMAGE_EXTENSIONS = {".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}

try:
    from pillow_heif import register_heif_opener
except ImportError:
    # HEIC is optional: absence of its decoder must never prevent the whole
    # Endorphin node pack from loading.
    register_heif_opener = None
else:
    register_heif_opener()
    IMAGE_EXTENSIONS.update({".heic", ".heif"})


def filename_sort_key(path):
    """Sort by the visible filename before using the extension as a tie-breaker."""
    return (path.stem.casefold(), path.suffix.casefold())


def natural_sort_key(path):
    stem_parts = [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", path.stem)]
    return (stem_parts, path.suffix.casefold())


def resolve_subfolder(base_folder, subfolder):
    """Append a relative subfolder without allowing paths outside the base."""
    base = Path(base_folder).expanduser().resolve()
    if not subfolder or not subfolder.strip():
        return base
    requested = Path(subfolder.strip())
    if requested.is_absolute():
        raise ValueError("Subfolder must be a relative path.")
    folder = (base / requested).resolve()
    try:
        folder.relative_to(base)
    except ValueError as error:
        raise ValueError("Subfolder must stay inside Folder Path.") from error
    return folder


def get_image_files(folder_path, subfolder, sort_mode):
    folder = resolve_subfolder(folder_path, subfolder)
    if not folder.is_dir():
        raise ValueError(f"Image folder was not found: {folder}")

    files = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
    if not files:
        raise ValueError(f"No supported image files were found in: {folder}")

    if sort_mode == "Name (A-Z)":
        files.sort(key=filename_sort_key)
    elif sort_mode == "Name (Z-A)":
        files.sort(key=filename_sort_key, reverse=True)
    elif sort_mode == "Modified (oldest first)":
        files.sort(key=lambda path: path.stat().st_mtime)
    elif sort_mode == "Modified (newest first)":
        files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    else:
        files.sort(key=natural_sort_key)
    return files


def selected_image_file(folder_path, subfolder, sort_mode, image_index, loop):
    """Resolve the exact image that the loader would return."""
    files = get_image_files(folder_path, subfolder, sort_mode)
    image_index = max(1, int(image_index))
    index = (image_index - 1) % len(files) if loop else min(image_index - 1, len(files) - 1)
    return files[index], index + 1, len(files)


@PromptServer.instance.routes.get("/endorphin/folder-image-preview")
async def folder_image_preview(request):
    """Return metadata or a browser-safe preview image for the selected file."""
    try:
        folder_path = str(request.query.get("folder_path", ""))
        subfolder = str(request.query.get("subfolder", ""))
        sort_mode = str(request.query.get("sort", "Natural (1, 2, 10)"))
        image_index = int(request.query.get("image_index", "1"))
        loop = str(request.query.get("loop", "true")).lower() not in {"0", "false", "no"}
        path, resolved_index, total = selected_image_file(folder_path, subfolder, sort_mode, image_index, loop)
        if request.query.get("render") != "1":
            stat = path.stat()
            return web.json_response({"file_name": path.name, "resolved_index": resolved_index, "total": total, "version": f"{stat.st_mtime_ns}-{stat.st_size}"})
        with Image.open(path) as source:
            source = ImageOps.exif_transpose(source)
            source.thumbnail((1200, 1200))
            output = BytesIO()
            source.convert("RGBA" if "A" in source.getbands() else "RGB").save(output, format="PNG")
        return web.Response(body=output.getvalue(), content_type="image/png", headers={"Cache-Control": "no-store"})
    except (OSError, ValueError, Image.UnidentifiedImageError) as error:
        return web.json_response({"error": str(error)}, status=404)


class EndorphinFolderImageLoader:
    """Load one image per Queue Prompt batch from a folder."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {
                    "default": "",
                    "placeholder": "D:\\Images\\source_folder",
                    "tooltip": "Absolute path to a folder containing images.",
                }),
                "subfolder": ("STRING", {
                    "default": "",
                    "placeholder": "Optional subfolder, e.g. set_a/red",
                    "tooltip": "Optional relative subfolder inside Folder Path.",
                }),
                "sort": ([
                    "Natural (1, 2, 10)",
                    "Name (A-Z)",
                    "Name (Z-A)",
                    "Modified (oldest first)",
                    "Modified (newest first)",
                ], {"default": "Name (A-Z)"}),
                "image_index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000000,
                    "step": 1,
                    "tooltip": "Current image number. Advances after each Queue Prompt batch item.",
                }),
                "auto_increment": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Load the next image after each Queue Prompt batch item.",
                }),
                "loop": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Return to the first image after the final image.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "INT")
    RETURN_NAMES = ("image", "mask", "file_name", "file_name_no_ext", "image_number")
    FUNCTION = "load_image"
    CATEGORY = "Endorphin Workshop/Utilities"

    @classmethod
    def IS_CHANGED(cls, folder_path, subfolder, sort, image_index, auto_increment, loop):
        """Invalidate ComfyUI's cache if the selected file is changed or deleted."""
        try:
            file_path, _, _ = selected_image_file(folder_path, subfolder, sort, image_index, loop)
            stat = file_path.stat()
            return f"{file_path}:{stat.st_mtime_ns}:{stat.st_size}"
        except (OSError, ValueError):
            # NaN deliberately prevents reuse of a cached image and lets
            # load_image report the current missing-folder/file error.
            return float("nan")

    def load_image(self, folder_path, subfolder, sort, image_index, auto_increment, loop):
        file_path, resolved_index, _ = selected_image_file(folder_path, subfolder, sort, image_index, loop)

        with Image.open(file_path) as source:
            source = ImageOps.exif_transpose(source)
            if source.mode == "I":
                source = source.point(lambda value: value * (1 / 255))
            image = source.convert("RGB")
            image_tensor = torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

            if "A" in source.getbands():
                alpha = np.array(source.getchannel("A")).astype(np.float32) / 255.0
                mask_tensor = torch.from_numpy(1.0 - alpha).unsqueeze(0)
            else:
                mask_tensor = torch.zeros((1, image.height, image.width), dtype=torch.float32)

        return image_tensor, mask_tensor, file_path.name, file_path.stem, resolved_index


NODE_CLASS_MAPPINGS = {"EndorphinFolderImageLoader": EndorphinFolderImageLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinFolderImageLoader": "Endorphin Folder Image Loader"}
