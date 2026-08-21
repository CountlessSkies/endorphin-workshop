"""Project-aware Etsy nodes for the new artwork/redesign workflow.

The nodes in this module deliberately keep project metadata separate from IMAGE
payloads.  ``ENDORPHIN_ETSY_CONTEXT`` is a small, versioned dictionary passed
between Etsy-aware nodes; the files and the project manifest remain the durable
source of truth.
"""

import json
import os
import re
from pathlib import Path

import numpy as np
from aiohttp import web
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
from server import PromptServer


CONTEXT_TYPE = "ENDORPHIN_ETSY_CONTEXT"
DEFAULT_ROOT = r"G:\My Drive\_Etsy\_Listing"
MANIFEST_NAME = "project.json"
CANDIDATE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@PromptServer.instance.routes.get("/endorphin/etsy/projects")
async def list_etsy_projects(request):
    """List direct project folders for the Project Selector's ID dropdown."""
    root_folder = str(request.query.get("root_folder", "")).strip()
    workflow_type = str(request.query.get("workflow_type", "")).strip().lower()
    if workflow_type not in {"artwork", "redesign"}:
        return web.json_response({"error": "workflow_type must be artwork or redesign."}, status=400)
    if not root_folder:
        return web.json_response({"projects": []})
    try:
        directory = Path(root_folder).expanduser() / workflow_type
        projects = sorted((path.name for path in directory.iterdir() if path.is_dir()), key=str.casefold) if directory.is_dir() else []
    except OSError as error:
        return web.json_response({"error": str(error)}, status=400)
    return web.json_response({"projects": projects})


def next_project_id(root_folder, workflow_type, period=None):
    """Return the next YYMMnnn ID for a selected period and workflow series."""
    import datetime
    prefix = str(period or datetime.date.today().strftime("%y%m")).strip()
    if not re.fullmatch(r"\d{4}", prefix):
        raise ValueError("ID period must use YYMM format, for example 2608.")
    month = int(prefix[2:])
    if not 1 <= month <= 12:
        raise ValueError("ID period month must be between 01 and 12.")
    directory = Path(root_folder).expanduser() / workflow_type
    pattern = re.compile(rf"^{re.escape(prefix)}(\d{{3}})$" if workflow_type == "artwork" else rf"^RD{re.escape(prefix)}(\d{{3}})$", re.IGNORECASE)
    used = []
    if directory.is_dir():
        for child in directory.iterdir():
            match = pattern.fullmatch(child.name) if child.is_dir() else None
            if match:
                used.append(int(match.group(1)))
    next_number = next((number for number in range(1, 1000) if number not in used), None)
    if next_number is None:
        raise ValueError(f"No remaining {prefix} IDs are available for {workflow_type}.")
    body = f"{prefix}{next_number:03d}"
    return body if workflow_type == "artwork" else f"RD{body}"


@PromptServer.instance.routes.post("/endorphin/etsy/projects")
async def create_etsy_project(request):
    """Create the next available project skeleton for the selected workflow."""
    try:
        data = await request.json()
        root_folder = str(data.get("root_folder", "")).strip()
        workflow_type = str(data.get("workflow_type", "")).strip().lower()
        source_type = str(data.get("source_type", "")).strip().lower()
        period = str(data.get("period", "")).strip()
        if not root_folder or workflow_type not in {"artwork", "redesign"}:
            raise ValueError("A root folder and valid workflow type are required.")
        if workflow_type == "redesign" and source_type not in {"embroidery_reference", "print_reference"}:
            raise ValueError("Choose an embroidery or print reference source before creating a redesign project.")
        project_id = next_project_id(root_folder, workflow_type, period)
        project_dir = project_path(root_folder, workflow_type, project_id)
        project_dir.mkdir(parents=True, exist_ok=False)
        if workflow_type == "artwork":
            (project_dir / "print").mkdir()
            (project_dir / "emb").mkdir()
        else:
            (project_dir / "source").mkdir()
            candidate_folder(project_dir).mkdir()
            write_manifest(project_dir, {
                "schema_version": 1,
                "project_id": project_id,
                "source_type": source_type,
                "approved_candidates": [],
            })
        return web.json_response({"project_id": project_id, "project_path": str(project_dir)})
    except (ValueError, OSError, json.JSONDecodeError) as error:
        return web.json_response({"error": str(error)}, status=400)


def normalize_identifier(value, label):
    normalized = str(value or "").strip().upper()
    if not normalized or not re.fullmatch(r"[A-Z0-9]+", normalized):
        raise ValueError(f"{label} must contain only letters and numbers.")
    return normalized


def normalize_letter(value):
    letter = normalize_identifier(value, "Candidate letter")
    if not re.fullmatch(r"[A-Z]+", letter):
        raise ValueError("Candidate letter must contain letters only.")
    return letter


def letters_from_index(index):
    """Convert 0-based indexes to spreadsheet-style letters: A..Z, AA.."""
    result = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def project_path(root_folder, workflow_type, project_id):
    root = Path(str(root_folder).strip() or DEFAULT_ROOT).expanduser()
    return root / workflow_type / project_id


def context_from_value(context):
    if not isinstance(context, dict):
        raise ValueError("Invalid Etsy context. Connect an Endorphin Etsy Project Context node.")
    if int(context.get("schema_version", 0)) != 1:
        raise ValueError("Unsupported Etsy context schema.")
    workflow_type = str(context.get("workflow_type", "")).strip().lower()
    if workflow_type not in {"artwork", "redesign"}:
        raise ValueError("Etsy context has an invalid workflow type.")
    project_id = normalize_identifier(context.get("project_id"), "Project ID")
    root_folder = str(context.get("root_folder", "")).strip() or DEFAULT_ROOT
    normalized = dict(context)
    normalized.update({
        "schema_version": 1,
        "workflow_type": workflow_type,
        "project_id": project_id,
        "root_folder": root_folder,
        "project_path": str(project_path(root_folder, workflow_type, project_id)),
    })
    if normalized.get("product_id"):
        normalized["product_id"] = normalize_identifier(normalized["product_id"], "Product ID")
    return normalized


def manifest_path(project_dir):
    return project_dir / MANIFEST_NAME


def load_manifest(project_dir, context):
    path = manifest_path(project_dir)
    if not path.exists():
        return {
            "schema_version": 1,
            "project_id": context["project_id"],
            "source_type": context.get("source_type", ""),
            "approved_candidates": [],
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {path}: {error}") from error
    if not isinstance(data, dict) or int(data.get("schema_version", 0)) != 1:
        raise ValueError(f"Unsupported project manifest: {path}")
    if normalize_identifier(data.get("project_id"), "Manifest project ID") != context["project_id"]:
        raise ValueError("Project manifest ID does not match the Etsy context.")
    data["approved_candidates"] = sorted({normalize_letter(letter) for letter in data.get("approved_candidates", [])})
    return data


def write_manifest(project_dir, manifest):
    project_dir.mkdir(parents=True, exist_ok=True)
    destination = manifest_path(project_dir)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def candidate_folder(project_dir):
    return project_dir / "candidates"


def candidate_file_stem(project_id, letter):
    return f"candidate_{project_id}{letter}"


def select_named_option(index, values, label):
    try:
        selected = int(index)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} index must be a number.") from error
    if selected < 1 or selected > len(values):
        raise ValueError(f"{label} index must be between 1 and {len(values)}.")
    value = str(values[selected - 1]).strip().lower()
    if not value:
        raise ValueError(f"Selected {label.lower()} is empty.")
    return value


def candidate_paths(project_dir, project_id):
    folder = candidate_folder(project_dir)
    if not folder.exists():
        return {}
    pattern = re.compile(rf"^candidate_{re.escape(project_id)}([A-Z]+)$", re.IGNORECASE)
    candidates = {}
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in CANDIDATE_EXTENSIONS:
            continue
        match = pattern.fullmatch(path.stem)
        if match:
            candidates[match.group(1).upper()] = path
    return candidates


def candidate_reservations(project_dir, project_id):
    folder = candidate_folder(project_dir)
    if not folder.exists():
        return set()
    pattern = re.compile(rf"^candidate_{re.escape(project_id)}([A-Z]+)\.reserve$", re.IGNORECASE)
    result = set()
    for path in folder.iterdir():
        match = pattern.fullmatch(path.name)
        if match:
            result.add(match.group(1).upper())
    return result


def reserve_next_candidate(project_dir, project_id, locked_letters):
    folder = candidate_folder(project_dir)
    folder.mkdir(parents=True, exist_ok=True)
    for index in range(10000):
        letter = letters_from_index(index)
        if letter in locked_letters or letter in candidate_paths(project_dir, project_id):
            continue
        reservation = folder / f"{candidate_file_stem(project_id, letter)}.reserve"
        try:
            with reservation.open("x", encoding="utf-8") as handle:
                handle.write("reserved\n")
            return letter, reservation
        except FileExistsError:
            continue
    raise RuntimeError("No candidate slot could be reserved.")


def save_png(image, destination, prompt=None, extra_pnginfo=None, compress_level=4):
    array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
    pil_image = Image.fromarray(array)
    metadata = PngInfo()
    if prompt is not None:
        metadata.add_text("prompt", json.dumps(prompt))
    if extra_pnginfo is not None:
        for key, value in extra_pnginfo.items():
            metadata.add_text(key, json.dumps(value))
    pil_image.save(destination, pnginfo=metadata, compress_level=compress_level)


def load_image(path):
    image = Image.open(path)
    image = ImageOps.exif_transpose(image).convert("RGB")
    array = np.asarray(image).astype(np.float32) / 255.0
    import torch
    return torch.from_numpy(array)[None,]


class EndorphinEtsyProjectContext:
    """Create the canonical project metadata connection for Etsy-aware nodes."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "root_folder": ("STRING", {"default": DEFAULT_ROOT}),
            "workflow_type": (["artwork", "redesign"], {"default": "redesign"}),
            "project_id": ("STRING", {"default": "RD2608001"}),
            "source_type": (["idea_artwork", "embroidery_reference", "print_reference"], {"default": "embroidery_reference"}),
        }}

    RETURN_TYPES = (CONTEXT_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("context", "project_id", "project_path")
    FUNCTION = "make_context"
    CATEGORY = "Endorphin Workshop/Etsy"

    def make_context(self, root_folder, workflow_type, project_id, source_type):
        project_id = normalize_identifier(project_id, "Project ID")
        context = context_from_value({
            "schema_version": 1,
            "workflow_type": workflow_type,
            "project_id": project_id,
            "source_type": source_type,
            "root_folder": root_folder,
            "asset_stage": "project",
        })
        return (context, project_id, context["project_path"])


class EndorphinEtsyProjectSelector:
    """Create Etsy context from the fixed clickable project-selector UI."""

    @classmethod
    def INPUT_TYPES(cls):
        default = {"root_folder": DEFAULT_ROOT, "project_id": "RD2608001", "workflow_type": "redesign", "source_type": "embroidery_reference"}
        return {"required": {"project": ("ENDORPHIN_ETSY_PROJECT_SELECTOR", {
            "default": json.dumps(default, separators=(",", ":")),
            "tooltip": "Choose Artwork or Redesign, then its applicable source. Artwork always uses artwork as its source.",
        })}}

    RETURN_TYPES = (CONTEXT_TYPE, "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("context", "workflow_type", "source_type", "project_id", "project_path")
    FUNCTION = "select"
    CATEGORY = "Endorphin Workshop/Etsy"

    def select(self, project):
        try:
            data = json.loads(project) if isinstance(project, str) else project
        except json.JSONDecodeError as error:
            raise ValueError("Invalid Etsy project selector value.") from error
        if not isinstance(data, dict):
            raise ValueError("Invalid Etsy project selector value.")
        root_folder = str(data.get("root_folder", "")).strip() or DEFAULT_ROOT
        workflow_type = str(data.get("workflow_type", "")).strip().lower()
        if workflow_type not in {"artwork", "redesign"}:
            raise ValueError("Workflow type must be artwork or redesign.")
        source_type = "idea_artwork" if workflow_type == "artwork" else str(data.get("source_type", "")).strip().lower()
        if source_type not in {"embroidery_reference", "print_reference"} and workflow_type == "redesign":
            raise ValueError("Redesign source type must be embroidery_reference or print_reference.")
        project_id = normalize_identifier(data.get("project_id"), "Project ID")
        if workflow_type == "redesign" and not project_id.startswith("RD"):
            raise ValueError("Redesign ID must start with RD.")
        context = context_from_value({
            "schema_version": 1,
            "workflow_type": workflow_type,
            "project_id": project_id,
            "source_type": source_type,
            "root_folder": root_folder,
            "asset_stage": "project",
        })
        return (context, workflow_type, source_type, project_id, context["project_path"])


MAX_SOURCE_TYPES = 5
MAX_WORKFLOW_TYPES = 5


def source_type_inputs():
    defaults = ["embroidery_reference", "print_reference"]
    return {
        f"source_type_{index:02d}": ("STRING", {"default": defaults[index - 1] if index <= len(defaults) else ""})
        for index in range(1, MAX_SOURCE_TYPES + 1)
    }


def workflow_type_inputs():
    defaults = ["artwork", "redesign"]
    return {
        f"workflow_type_{index:02d}": ("STRING", {"default": defaults[index - 1] if index <= len(defaults) else ""})
        for index in range(1, MAX_WORKFLOW_TYPES + 1)
    }


class EndorphinEtsyWorkflowTypeSelector:
    """Clickable card selector for artwork or redesign."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "workflow_type_count": ("INT", {"default": 2, "min": 1, "max": MAX_WORKFLOW_TYPES, "step": 1}),
            "workflow_type_index": ("INT", {"default": 2, "min": 1, "max": MAX_WORKFLOW_TYPES, "step": 1}),
            **workflow_type_inputs(),
        }}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("workflow_type", "workflow_type_index")
    FUNCTION = "select"
    CATEGORY = "Endorphin Workshop/Etsy"

    def select(self, workflow_type_count, workflow_type_index, **kwargs):
        if workflow_type_index > workflow_type_count:
            raise ValueError("workflow_type_index must not be higher than workflow_type_count.")
        workflow_type = str(kwargs.get(f"workflow_type_{workflow_type_index:02d}", "")).strip().lower()
        if workflow_type not in {"artwork", "redesign"}:
            raise ValueError("Workflow type must be artwork or redesign.")
        return (workflow_type, workflow_type_index)


class EndorphinEtsySourceTypeSelector:
    """Clickable card selector for redesign reference types."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "source_type_count": ("INT", {"default": 2, "min": 1, "max": MAX_SOURCE_TYPES, "step": 1}),
            "source_type_index": ("INT", {"default": 1, "min": 1, "max": MAX_SOURCE_TYPES, "step": 1}),
            **source_type_inputs(),
        }}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("source_type", "source_type_index")
    FUNCTION = "select"
    CATEGORY = "Endorphin Workshop/Etsy"

    def select(self, source_type_count, source_type_index, **kwargs):
        if source_type_index > source_type_count:
            raise ValueError("source_type_index must not be higher than source_type_count.")
        source_type = str(kwargs.get(f"source_type_{source_type_index:02d}", "")).strip().lower()
        if not source_type:
            raise ValueError("Choose a valid source type.")
        return (source_type, source_type_index)


class EndorphinEtsyProjectBuilder:
    """Build context from clickable workflow/source selectors and a project ID."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "root_folder": ("STRING", {"default": DEFAULT_ROOT}),
                "project_id": ("STRING", {"default": "RD2608001"}),
                "workflow_type": ("STRING", {"default": "redesign"}),
            },
            "optional": {"source_type": ("STRING", {"default": ""})},
        }

    RETURN_TYPES = (CONTEXT_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("context", "project_id", "project_path")
    FUNCTION = "build"
    CATEGORY = "Endorphin Workshop/Etsy"

    def build(self, root_folder, project_id, workflow_type, source_type=""):
        workflow_type = str(workflow_type).strip().lower()
        if workflow_type not in {"artwork", "redesign"}:
            raise ValueError("Workflow type must be artwork or redesign.")
        project_id = normalize_identifier(project_id, "Project ID")
        if workflow_type == "redesign" and not project_id.startswith("RD"):
            raise ValueError("Redesign ID must start with RD.")
        source_type = "idea_artwork" if workflow_type == "artwork" else str(source_type).strip().lower()
        if not source_type:
            raise ValueError("Redesign projects require a source type from Etsy Source Type Selector.")
        context = context_from_value({
            "schema_version": 1,
            "workflow_type": workflow_type,
            "project_id": project_id,
            "source_type": source_type,
            "root_folder": root_folder,
            "asset_stage": "project",
        })
        return (context, project_id, context["project_path"])


class EndorphinEtsyArtworkProjectSelector:
    """Selector for artwork projects; source type is always idea_artwork."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "root_folder": ("STRING", {"default": DEFAULT_ROOT}),
            "artwork_id": ("STRING", {"default": "2608001"}),
        }}

    RETURN_TYPES = (CONTEXT_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("context", "artwork_id", "project_path")
    FUNCTION = "select"
    CATEGORY = "Endorphin Workshop/Etsy"

    def select(self, root_folder, artwork_id):
        artwork_id = normalize_identifier(artwork_id, "Artwork ID")
        context = context_from_value({
            "schema_version": 1,
            "workflow_type": "artwork",
            "project_id": artwork_id,
            "source_type": "idea_artwork",
            "root_folder": root_folder,
            "asset_stage": "project",
        })
        return (context, artwork_id, context["project_path"])


class EndorphinEtsyRedesignProjectSelector:
    """Selector for redesign projects with legacy-style source type slots."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "root_folder": ("STRING", {"default": DEFAULT_ROOT}),
            "redesign_id": ("STRING", {"default": "RD2608001"}),
            "source_type_count": ("INT", {"default": 2, "min": 1, "max": MAX_SOURCE_TYPES, "step": 1}),
            "source_type_index": ("INT", {"default": 1, "min": 1, "max": MAX_SOURCE_TYPES, "step": 1}),
            **source_type_inputs(),
        }}

    RETURN_TYPES = (CONTEXT_TYPE, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("context", "redesign_id", "source_type", "project_path")
    FUNCTION = "select"
    CATEGORY = "Endorphin Workshop/Etsy"

    def select(self, root_folder, redesign_id, source_type_count, source_type_index, **kwargs):
        if source_type_index > source_type_count:
            raise ValueError("source_type_index must not be higher than source_type_count.")
        source_type = str(kwargs.get(f"source_type_{source_type_index:02d}", "")).strip().lower()
        if not source_type:
            raise ValueError("Choose a valid source type.")
        redesign_id = normalize_identifier(redesign_id, "Redesign ID")
        if not redesign_id.startswith("RD"):
            raise ValueError("Redesign ID must start with RD.")
        context = context_from_value({
            "schema_version": 1,
            "workflow_type": "redesign",
            "project_id": redesign_id,
            "source_type": source_type,
            "root_folder": root_folder,
            "asset_stage": "project",
        })
        return (context, redesign_id, source_type, context["project_path"])


class EndorphinEtsyWorkflowStage:
    """Select which Etsy workflow stage is allowed to execute."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"run_stage": (["Prepare", "Approve", "Colorway"], {"default": "Prepare"})}}

    RETURN_TYPES = ("BOOLEAN", "BOOLEAN", "BOOLEAN", "STRING")
    RETURN_NAMES = ("prepare_enabled", "approve_enabled", "colorway_enabled", "run_stage")
    FUNCTION = "select_stage"
    CATEGORY = "Endorphin Workshop/Etsy"

    def select_stage(self, run_stage):
        return (run_stage == "Prepare", run_stage == "Approve", run_stage == "Colorway", run_stage)


class EndorphinEtsyLazyWorkflowRouter:
    """Route only the selected workflow's image branch using lazy inputs."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "context": (CONTEXT_TYPE,),
            "artwork_image": ("IMAGE", {"lazy": True}),
            "redesign_image": ("IMAGE", {"lazy": True}),
        }}

    RETURN_TYPES = ("IMAGE", CONTEXT_TYPE)
    RETURN_NAMES = ("image", "context")
    FUNCTION = "route"
    CATEGORY = "Endorphin Workshop/Etsy"

    def check_lazy_status(self, context, artwork_image=None, redesign_image=None, **kwargs):
        context = context_from_value(context)
        return ["artwork_image" if context["workflow_type"] == "artwork" else "redesign_image"]

    def route(self, context, artwork_image=None, redesign_image=None):
        context = context_from_value(context)
        image = artwork_image if context["workflow_type"] == "artwork" else redesign_image
        return (image, context)


class EndorphinEtsySourceAssetLoader:
    """Resolve the source image from the selected Etsy project convention."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"context": (CONTEXT_TYPE,)}}

    RETURN_TYPES = ("IMAGE", CONTEXT_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("image", "source_context", "file_name", "source_path")
    FUNCTION = "load"
    CATEGORY = "Endorphin Workshop/Etsy"

    def load(self, context):
        context = context_from_value(context)
        project_dir = Path(context["project_path"])
        if context["workflow_type"] == "artwork":
            expected_stem = f"artwork_{context['project_id']}".lower()
            candidates = [path for path in project_dir.iterdir() if path.is_file() and path.suffix.lower() in CANDIDATE_EXTENSIONS and path.stem.lower() == expected_stem] if project_dir.exists() else []
        else:
            source_dir = project_dir / "source"
            candidates = sorted((path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in CANDIDATE_EXTENSIONS), key=lambda path: path.name.casefold()) if source_dir.exists() else []
        if not candidates:
            if context["workflow_type"] == "artwork":
                expected = project_dir / f"artwork_{context['project_id']}.png"
            else:
                expected = project_dir / "source"
            raise ValueError(f"No source image found. Expected: {expected}")
        source_path = candidates[0]
        source_context = dict(context)
        source_context.update({"asset_stage": "source", "source_path": str(source_path)})
        return (load_image(source_path), source_context, source_path.name, str(source_path))


class EndorphinCandidateSave:
    """Save generated redesign candidates into the next safe letter slot."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "enabled": ("BOOLEAN", {"default": True}),
                "images": ("IMAGE", {"lazy": True}),
                "context": (CONTEXT_TYPE,),
                "png_compress_level": ("INT", {"default": 4, "min": 0, "max": 9, "step": 1}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("images", "candidate_letters", "product_ids", "candidate_paths")
    FUNCTION = "save_candidates"
    OUTPUT_NODE = True
    CATEGORY = "Endorphin Workshop/Etsy"

    def check_lazy_status(self, enabled, context=None, images=None, **kwargs):
        if not enabled:
            return []
        return ["images"] if isinstance(context, dict) and context.get("workflow_type") == "redesign" else []

    def save_candidates(self, enabled, images=None, context=None, png_compress_level=4, prompt=None, extra_pnginfo=None):
        context = context_from_value(context)
        if not enabled or context["workflow_type"] != "redesign":
            return {"result": (images, "", "", "")}
        project_dir = Path(context["project_path"])
        manifest = load_manifest(project_dir, context)
        project_dir.mkdir(parents=True, exist_ok=True)
        if not manifest.get("source_type"):
            manifest["source_type"] = context.get("source_type", "")
        write_manifest(project_dir, manifest)

        letters, product_ids, paths = [], [], []
        for image in images:
            letter, reservation = reserve_next_candidate(project_dir, context["project_id"], set(manifest["approved_candidates"]))
            destination = candidate_folder(project_dir) / f"{candidate_file_stem(context['project_id'], letter)}.png"
            try:
                save_png(image, destination, prompt, extra_pnginfo, png_compress_level)
            finally:
                reservation.unlink(missing_ok=True)
            letters.append(letter)
            product_ids.append(f"{context['project_id']}{letter}")
            paths.append(str(destination))

        return {"ui": {"saved": paths}, "result": (images, ",".join(letters), ",".join(product_ids), "\n".join(paths))}


class EndorphinApproveRedesignCandidate:
    """Persistently approve one existing candidate letter for downstream work."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "enabled": ("BOOLEAN", {"default": False}),
            "context": (CONTEXT_TYPE,),
            "candidate_letter": ("STRING", {"default": "A"}),
        }}

    RETURN_TYPES = (CONTEXT_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("approved_context", "product_id", "candidate_path")
    FUNCTION = "approve"
    OUTPUT_NODE = True
    CATEGORY = "Endorphin Workshop/Etsy"

    def approve(self, enabled, context, candidate_letter):
        context = context_from_value(context)
        if not enabled:
            return (context, "", "")
        if context["workflow_type"] != "redesign":
            raise ValueError("Approve Redesign Candidate is available only for redesign projects.")
        letter = normalize_letter(candidate_letter)
        project_dir = Path(context["project_path"])
        manifest = load_manifest(project_dir, context)
        candidates = candidate_paths(project_dir, context["project_id"])
        candidate = candidates.get(letter)
        if candidate is None:
            raise ValueError(f"Candidate {letter} does not exist on disk and cannot be approved.")
        approved = set(manifest["approved_candidates"])
        approved.add(letter)
        manifest["approved_candidates"] = sorted(approved)
        write_manifest(project_dir, manifest)

        product_id = f"{context['project_id']}{letter}"
        product_folder = project_dir / product_id
        product_folder.mkdir(parents=True, exist_ok=True)
        approved_context = dict(context)
        approved_context.update({
            "product_id": product_id,
            "candidate_letter": letter,
            "asset_stage": "approved_candidate",
            "candidate_path": str(candidate),
            "product_path": str(product_folder),
        })
        return (approved_context, product_id, str(candidate))


class EndorphinApprovedCandidateLoader:
    """Load one approved candidate from disk; never trusts stale graph images."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "context": (CONTEXT_TYPE,),
            "candidate_letter": ("STRING", {"default": "A"}),
        }}

    RETURN_TYPES = ("IMAGE", CONTEXT_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("image", "approved_context", "product_id", "candidate_path")
    FUNCTION = "load"
    CATEGORY = "Endorphin Workshop/Etsy"

    def load(self, context, candidate_letter):
        context = context_from_value(context)
        if context["workflow_type"] != "redesign":
            raise ValueError("Approved Candidate Loader is available only for redesign projects.")
        letter = normalize_letter(candidate_letter)
        project_dir = Path(context["project_path"])
        manifest = load_manifest(project_dir, context)
        if letter not in manifest["approved_candidates"]:
            raise ValueError(f"Candidate {letter} is not approved.")
        candidate = candidate_paths(project_dir, context["project_id"]).get(letter)
        if candidate is None:
            raise ValueError(f"Approved candidate {letter} is missing from disk.")
        product_id = f"{context['project_id']}{letter}"
        loaded_context = dict(context)
        loaded_context.update({
            "product_id": product_id,
            "candidate_letter": letter,
            "asset_stage": "approved_candidate",
            "candidate_path": str(candidate),
            "product_path": str(project_dir / product_id),
        })
        return (load_image(candidate), loaded_context, product_id, str(candidate))


NODE_CLASS_MAPPINGS = {
    "EndorphinEtsyProjectContext": EndorphinEtsyProjectContext,
    "EndorphinEtsyProjectSelector": EndorphinEtsyProjectSelector,
    "EndorphinEtsyWorkflowStage": EndorphinEtsyWorkflowStage,
    "EndorphinEtsyLazyWorkflowRouter": EndorphinEtsyLazyWorkflowRouter,
    "EndorphinEtsySourceAssetLoader": EndorphinEtsySourceAssetLoader,
    "EndorphinEtsyCandidateSave": EndorphinCandidateSave,
    "EndorphinEtsyApproveRedesignCandidate": EndorphinApproveRedesignCandidate,
    "EndorphinEtsyApprovedCandidateLoader": EndorphinApprovedCandidateLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinEtsyProjectContext": "Endorphin Etsy Project Context (Advanced)",
    "EndorphinEtsyProjectSelector": "Endorphin Etsy Project Selector",
    "EndorphinEtsyWorkflowStage": "Endorphin Etsy Workflow Stage",
    "EndorphinEtsyLazyWorkflowRouter": "Endorphin Etsy Lazy Workflow Router",
    "EndorphinEtsySourceAssetLoader": "Endorphin Etsy Source Asset Loader",
    "EndorphinEtsyCandidateSave": "Endorphin Etsy Candidate Save",
    "EndorphinEtsyApproveRedesignCandidate": "Endorphin Etsy Approve Redesign Candidate",
    "EndorphinEtsyApprovedCandidateLoader": "Endorphin Etsy Approved Candidate Loader",
}
