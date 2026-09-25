"""Dedicated project selector, routing, prompt, and saving for printed shirts."""

import json
import re
from pathlib import Path

from aiohttp import web
from comfy_execution.graph_utils import ExecutionBlocker
from server import PromptServer

from .etsy_project_nodes import (
    CANDIDATE_EXTENSIONS,
    CONTEXT_TYPE,
    DEFAULT_ROOT,
    context_from_value,
    filename_sort_key,
    first_matching_asset,
    load_image,
    normalize_identifier,
    project_path,
)


PRINT_ROUTES = ("artwork_print", "redesign_print")
PRINT_MODELS = {
    "MAN": "an adult man",
    "WOM": "an adult woman",
    "BOY": "a boy",
    "GIRL": "a girl",
}
PRINT_SIZES = {
    "Small": "a modest chest print, around half the usable front chest width",
    "Standard": "a clearly visible chest print, around two thirds of the usable front chest width",
    "Large": "a bold chest print, around four fifths of the usable front chest width",
}
PRINT_COLORS = (
    ("White", "WHI", "#FFFFFF"),
    ("Black", "BLK", "#25282A"),
    ("Sport Grey", "SGR", "#97999B"),
    ("Dark Heather", "DKH", "#425563"),
    ("Navy", "NAV", "#263147"),
    ("Royal Blue", "RYB", "#224D8F"),
    ("Light Blue", "LTB", "#A4C8E1"),
    ("Light Pink", "LTP", "#E4C6D4"),
    ("Red", "RED", "#D50032"),
    ("Maroon", "MRN", "#5B2B42"),
    ("Forest Green", "FRG", "#273B33"),
    ("Military Green", "MLG", "#5E7461"),
    ("Sand", "SAN", "#CABFAD"),
    ("Natural", "NAT", "#E7CEB5"),
    ("Dark Chocolate", "DCC", "#382F2D"),
    ("Purple", "PPL", "#470A68"),
)
PRINT_OCCASIONS = {
    "Everyday": "A natural, attractive everyday lifestyle setting without seasonal props.",
    "Match Artwork": "Build the background, props, and lighting to match the mood, theme, and visual character of the printed artwork. Draw inspiration only from the design itself, not from a source photo's background. Keep the scene supportive and the shirt print dominant.",
    "Christmas": "A subtle Christmas atmosphere in the background, with tasteful seasonal decor and warm light.",
    "Halloween": "A subtle Halloween atmosphere in the background, with tasteful autumn or spooky props.",
    "Valentine": "A subtle Valentine's Day atmosphere in the background, with warm romantic accents.",
    "Easter": "A subtle Easter or spring atmosphere in the background, with soft seasonal accents.",
}


def print_source_path(root_folder, workflow_type, project_id):
    project_id = normalize_identifier(project_id, "Project ID")
    if workflow_type not in {"artwork", "redesign"}:
        raise ValueError("Choose Artwork or Redesign.")
    if (workflow_type == "redesign") != project_id.startswith("RD"):
        raise ValueError("The selected ID does not match the Print workflow type.")
    directory = project_path(root_folder, workflow_type, project_id)
    if not directory.is_dir():
        raise ValueError(f"Print project folder was not found: {directory}")
    if workflow_type == "artwork":
        path = first_matching_asset(directory, [f"artwork_{project_id}", f"artwork_{project_id}_transparent"])
        expected = directory / f"artwork_{project_id}.png"
    else:
        source_dir = directory / "source"
        files = sorted(
            (path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in CANDIDATE_EXTENSIONS),
            key=filename_sort_key,
        ) if source_dir.is_dir() else []
        path = files[0] if files else None
        expected = source_dir
    if path is None:
        raise ValueError(f"Print source image is missing. Expected: {expected}")
    return path


def print_output_path(root_folder, workflow_type, project_id, model_code, color_code):
    project_id = normalize_identifier(project_id, "Project ID")
    if workflow_type not in {"artwork", "redesign"} or (workflow_type == "redesign") != project_id.startswith("RD"):
        raise ValueError("The selected ID does not match the Print workflow type.")
    if model_code not in PRINT_MODELS or color_code not in {item[1] for item in PRINT_COLORS}:
        raise ValueError("Choose a valid model and Gildan 5000 color.")
    return project_path(root_folder, workflow_type, project_id) / "print" / f"mockup_{project_id}_print_{model_code}_{color_code}.png"


@PromptServer.instance.routes.get("/endorphin/etsy/print/source-preview")
async def print_source_preview(request):
    try:
        source = print_source_path(
            str(request.query.get("root_folder", "")).strip() or DEFAULT_ROOT,
            str(request.query.get("workflow_type", "")).strip().lower(),
            str(request.query.get("project_id", "")).strip(),
        )
        return web.FileResponse(source, headers={"Cache-Control": "no-store"})
    except (ValueError, OSError) as error:
        return web.json_response({"error": str(error)}, status=404)


@PromptServer.instance.routes.get("/endorphin/etsy/print/output-preview")
async def print_output_preview(request):
    try:
        expected = print_output_path(
            str(request.query.get("root_folder", "")).strip() or DEFAULT_ROOT,
            str(request.query.get("workflow_type", "")).strip().lower(),
            str(request.query.get("project_id", "")).strip(),
            str(request.query.get("model_code", "")).strip().upper(),
            str(request.query.get("color_code", "")).strip().upper(),
        )
        path = expected if expected.is_file() else expected.with_name(f"{expected.stem}_01.png")
        if not path.is_file():
            raise ValueError(f"Print output has not been created yet. Expected: {expected}")
        return web.FileResponse(path, headers={"Cache-Control": "no-store"})
    except (ValueError, OSError) as error:
        return web.json_response({"error": str(error)}, status=404)


def print_context(value):
    context = context_from_value(value)
    route = context.get("route")
    if route not in PRINT_ROUTES or route != f"{context['workflow_type']}_print":
        raise ValueError("Print context has an invalid route.")
    model = context.get("model_code")
    color = context.get("color_code")
    if model not in PRINT_MODELS:
        raise ValueError("Print context has an invalid model code.")
    if color not in {item[1] for item in PRINT_COLORS}:
        raise ValueError("Print context has an invalid Gildan 5000 color code.")
    if context.get("print_size") not in PRINT_SIZES:
        raise ValueError("Print context has an invalid artwork size.")
    return context


class EndorphinEtsyPrintSelector:
    @classmethod
    def INPUT_TYPES(cls):
        default = {
            "root_folder": DEFAULT_ROOT,
            "workflow_type": "artwork",
            "project_id": "",
            "model_code": "WOM",
            "color_code": "BLK",
            "print_size": "Standard",
            "occasion": "Everyday",
            "custom_occasion": "",
            "color_hexes": {code: hex_value for _, code, hex_value in PRINT_COLORS},
        }
        return {"required": {"project": ("ENDORPHIN_ETSY_PRINT_SELECTOR", {"default": json.dumps(default)})}}

    RETURN_TYPES = (CONTEXT_TYPE, "IMAGE")
    RETURN_NAMES = ("context", "source_image")
    FUNCTION = "select"
    CATEGORY = "Endorphin Workshop/Etsy Print"

    @classmethod
    def IS_CHANGED(cls, project):
        return float("nan")

    def select(self, project):
        data = json.loads(project) if isinstance(project, str) else project
        if not isinstance(data, dict):
            raise ValueError("Invalid Etsy Print Selector value.")
        workflow_type = str(data.get("workflow_type", "artwork")).strip().lower()
        project_id = normalize_identifier(data.get("project_id"), "Project ID")
        root_folder = str(data.get("root_folder", "")).strip() or DEFAULT_ROOT
        model_code = str(data.get("model_code", "WOM")).strip().upper()
        color_code = str(data.get("color_code", "BLK")).strip().upper()
        print_size = str(data.get("print_size", "Standard")).strip()
        occasion = str(data.get("occasion", "Everyday")).strip()
        if model_code not in PRINT_MODELS or color_code not in {item[1] for item in PRINT_COLORS}:
            raise ValueError("Choose a valid model and Gildan 5000 color.")
        if print_size not in PRINT_SIZES:
            raise ValueError("Choose Small, Standard, or Large artwork size.")
        if occasion not in PRINT_OCCASIONS and occasion != "Custom":
            raise ValueError("Choose a valid print occasion.")
        color_name, _, default_hex = next(item for item in PRINT_COLORS if item[1] == color_code)
        hex_value = str((data.get("color_hexes") or {}).get(color_code, default_hex)).strip().upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", hex_value):
            raise ValueError(f"{color_name} needs a #RRGGBB HEX value.")
        source = print_source_path(root_folder, workflow_type, project_id)
        context = print_context({
            "schema_version": 1,
            "workflow_type": workflow_type,
            "project_id": project_id,
            "root_folder": root_folder,
            "route": f"{workflow_type}_print",
            "model_code": model_code,
            "color_name": color_name,
            "color_code": color_code,
            "color_hex": hex_value,
            "print_size": print_size,
            "occasion": occasion,
            "custom_occasion": str(data.get("custom_occasion", "")).strip(),
            "source_path": str(source),
        })
        return (context, load_image(source))


class EndorphinEtsyPrintPromptCompiler:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"context": (CONTEXT_TYPE,)}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "compile"
    CATEGORY = "Endorphin Workshop/Etsy Print"

    def compile(self, context):
        context = print_context(context)
        model = PRINT_MODELS[context["model_code"]]
        size = PRINT_SIZES[context["print_size"]]
        color = f"{context['color_name']} (hex {context['color_hex']})"
        occasion = context["custom_occasion"] if context["occasion"] == "Custom" else PRINT_OCCASIONS[context["occasion"]]
        source_instruction = (
            "Use the provided image as the original ARTWORK. Reproduce its composition, characters, colors, and all text accurately on the shirt; do not invent or rewrite the design."
            if context["route"] == "artwork_print" else
            "Use the provided printed-shirt reference as the design to clone. Recreate the same printed graphic, including its composition and all text, on a new shirt and model; do not copy watermarks or unrelated reference-background elements."
        )
        prompt = "\n".join((
            "Create one photorealistic apparel listing mockup from the provided image.",
            source_instruction,
            f"Show {model} wearing a Gildan 5000 T-shirt in {color}.",
            f"Place the complete printed artwork centrally on the front chest at {size}. Keep the artwork's proportions; never stretch, crop, or cover it with hands or props.",
            "Frame the model from around the chin or lower face to the hips or upper thighs. Avoid a full-body view and visible feet. Make the shirt front and printed design the main focus, with a clear unobstructed chest area.",
            "Use a natural lifestyle pose, realistic fabric, folds, lighting, and believable printed ink that follows the shirt surface. Do not add embroidered stitches or patches.",
            occasion or "Keep the background natural and unobtrusive.",
            "The occasion changes only the surrounding scene, props, and light; it must not change the printed design. Do not add captions, labels, watermarks, logos, or promotional graphics.",
        ))
        return (prompt,)


class EndorphinEtsyPrintBranchGate:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "context": (CONTEXT_TYPE,),
            "route": (list(PRINT_ROUTES),),
            "image": ("IMAGE", {"lazy": True}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "gate"
    CATEGORY = "Endorphin Workshop/Etsy Print"

    def check_lazy_status(self, context, route, image=None):
        return ["image"] if print_context(context)["route"] == route and image is None else []

    def gate(self, context, route, image=None):
        if print_context(context)["route"] != route:
            return (ExecutionBlocker(None),)
        if image is None:
            return (ExecutionBlocker(f"Print route {route} requires a source image."),)
        return (image,)


class EndorphinEtsyPrintRouter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"context": (CONTEXT_TYPE,)},
            "optional": {route: ("IMAGE", {"lazy": True}) for route in PRINT_ROUTES},
        }

    RETURN_TYPES = ("IMAGE", CONTEXT_TYPE)
    RETURN_NAMES = ("image", "context")
    FUNCTION = "route"
    CATEGORY = "Endorphin Workshop/Etsy Print"

    def check_lazy_status(self, context, **kwargs):
        return [print_context(context)["route"]]

    def route(self, context, **images):
        context = print_context(context)
        selected = context["route"]
        image = images.get(selected)
        if image is None:
            raise ValueError(f"Print Router needs an image connected to {selected}.")
        return (image, context)


NODE_CLASS_MAPPINGS = {
    "EndorphinEtsyPrintSelector": EndorphinEtsyPrintSelector,
    "EndorphinEtsyPrintPromptCompiler": EndorphinEtsyPrintPromptCompiler,
    "EndorphinEtsyPrintBranchGate": EndorphinEtsyPrintBranchGate,
    "EndorphinEtsyPrintRouter": EndorphinEtsyPrintRouter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinEtsyPrintSelector": "Endorphin Etsy Print Selector",
    "EndorphinEtsyPrintPromptCompiler": "Endorphin Etsy Print Prompt Compiler",
    "EndorphinEtsyPrintBranchGate": "Endorphin Etsy Print Branch Gate (Lazy)",
    "EndorphinEtsyPrintRouter": "Endorphin Etsy Print Router (Lazy)",
}
