import hashlib
import re
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps

from .folder_image_loader import IMAGE_EXTENSIONS, natural_sort_key


SORT_OPTIONS = [
    "Name (A-Z)",
    "Name (Z-A)",
    "Modified (oldest first)",
    "Modified (newest first)",
    "Natural (1, 2, 10)",
]


def _sort_paths(paths, sort_mode):
    if sort_mode == "Name (A-Z)":
        paths.sort(key=lambda path: path.name.casefold())
    elif sort_mode == "Name (Z-A)":
        paths.sort(key=lambda path: path.name.casefold(), reverse=True)
    elif sort_mode == "Modified (oldest first)":
        paths.sort(key=lambda path: path.stat().st_mtime)
    elif sort_mode == "Modified (newest first)":
        paths.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    else:
        paths.sort(key=natural_sort_key)


def get_subfolder_files(root_folder, file_prefix, file_suffix, sort_mode):
    root = Path(root_folder).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Artwork root folder was not found: {root}")

    prefix = str(file_prefix).strip().casefold()
    suffix = str(file_suffix).strip().casefold()
    folders = [path for path in root.rglob("*") if path.is_dir()]
    _sort_paths(folders, sort_mode)

    entries = []
    for folder in folders:
        files = [
            path for path in folder.iterdir()
            if path.is_file()
            and path.suffix.casefold() in IMAGE_EXTENSIONS
            and (not prefix or path.name.casefold().startswith(prefix))
            and (not suffix or path.stem.casefold().endswith(suffix))
        ]
        if not files:
            continue
        _sort_paths(files, sort_mode)
        entries.append((folder, files[0]))

    if not entries:
        filters = []
        if prefix:
            filters.append(f"prefix '{file_prefix}'")
        if suffix:
            filters.append(f"suffix '{file_suffix}'")
        label = f" matching {' and '.join(filters)}" if filters else ""
        raise ValueError(f"No image files were found in subfolders of: {root}{label}")
    return root, entries


def strip_file_prefix(file_stem, file_prefix):
    prefix = str(file_prefix).strip()
    if not prefix or not file_stem.casefold().startswith(prefix.casefold()):
        return file_stem
    return re.sub(r"^[ _-]+", "", file_stem[len(prefix):])


def strip_file_prefix_and_suffix(file_stem, file_prefix, file_suffix):
    value = strip_file_prefix(file_stem, file_prefix)
    suffix = str(file_suffix).strip()
    if suffix and value.casefold().endswith(suffix.casefold()):
        value = value[:-len(suffix)]
    return re.sub(r"[ _-]+$", "", value)


class EndorphinArtworkFolderLoader:
    """Load the first prefix/suffix-matching file from each recursive subfolder."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "root_folder": ("STRING", {
                    "default": "",
                    "tooltip": "Root folder scanned recursively for artwork subfolders.",
                }),
                "file_prefix": ("STRING", {
                    "default": "",
                    "tooltip": "Only files whose name starts with this prefix are considered. Leave blank to allow every image.",
                }),
                "file_suffix": ("STRING", {
                    "default": "",
                    "tooltip": "Only files whose name (without extension) ends with this suffix are considered. Leave blank to allow every suffix.",
                }),
                "sort": (SORT_OPTIONS, {"default": "Name (A-Z)"}),
                "folder_index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000000,
                    "step": 1,
                    "tooltip": "Current matching folder number. Advances after each Queue Prompt batch item.",
                }),
                "auto_increment": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Move to the next matching folder after each Queue Prompt batch item.",
                }),
                "loop": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Return to the first matching folder after the final one.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = (
        "image", "file_name", "file_name_no_ext", "file_name_no_ext_no_prefix_no_suffix",
        "folder_name", "relative_path", "folder_index", "total_folders",
    )
    FUNCTION = "load_artwork"
    CATEGORY = "Endorphin Workshop/Utilities"

    @staticmethod
    def _selected_entry(root_folder, file_prefix, file_suffix, sort, folder_index, loop):
        root, entries = get_subfolder_files(root_folder, file_prefix, file_suffix, sort)
        index = (folder_index - 1) % len(entries) if loop else min(folder_index - 1, len(entries) - 1)
        return root, entries, index, entries[index]

    @classmethod
    def IS_CHANGED(cls, root_folder, file_prefix, file_suffix, sort, folder_index, auto_increment, loop):
        try:
            root, entries, index, (_folder, file_path) = cls._selected_entry(
                root_folder, file_prefix, file_suffix, sort, folder_index, loop
            )
            stat = file_path.stat()
            listing = "\n".join(str(path.relative_to(root)) for _, path in entries)
            listing_hash = hashlib.sha256(listing.encode("utf-8")).hexdigest()
            return f"{file_path}:{stat.st_mtime_ns}:{stat.st_size}:{index}:{listing_hash}"
        except (OSError, ValueError):
            return float("nan")

    def load_artwork(self, root_folder, file_prefix, file_suffix, sort, folder_index, auto_increment, loop):
        root, entries, index, (folder, file_path) = self._selected_entry(
            root_folder, file_prefix, file_suffix, sort, folder_index, loop
        )
        with Image.open(file_path) as source:
            source = ImageOps.exif_transpose(source)
            if source.mode == "I":
                source = source.point(lambda value: value * (1 / 255))
            image = source.convert("RGB")
            image_tensor = torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

        relative_path = str(file_path.relative_to(root))
        return (
            image_tensor,
            file_path.name,
            file_path.stem,
            strip_file_prefix_and_suffix(file_path.stem, file_prefix, file_suffix),
            folder.name,
            relative_path,
            index + 1,
            len(entries),
        )


NODE_CLASS_MAPPINGS = {"EndorphinArtworkFolderLoader": EndorphinArtworkFolderLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinArtworkFolderLoader": "Endorphin Subfolder Image Loader"}
