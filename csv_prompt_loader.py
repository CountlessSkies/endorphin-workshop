import csv
from pathlib import Path

import folder_paths
from aiohttp import web
from server import PromptServer


@PromptServer.instance.routes.post("/endorphin/csv/upload")
async def upload_csv(request):
    """Accept a CSV selected in the browser and store it under ComfyUI/input."""
    form = await request.post()
    upload = form.get("csv")
    if upload is None or not getattr(upload, "file", None):
        return web.json_response({"error": "No CSV file was supplied."}, status=400)

    file_name = Path(upload.filename or "data.csv").name
    if Path(file_name).suffix.lower() not in {".csv", ".tsv"}:
        return web.json_response({"error": "Only .csv and .tsv files are supported."}, status=400)

    content = upload.file.read(50 * 1024 * 1024 + 1)
    if len(content) > 50 * 1024 * 1024:
        return web.json_response({"error": "CSV file must be 50 MB or smaller."}, status=400)

    input_root = Path(folder_paths.get_input_directory()).resolve()
    destination_dir = input_root / "endorphin_csv"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / file_name
    suffix = 1
    while destination.exists():
        destination = destination_dir / f"{Path(file_name).stem}_{suffix}{Path(file_name).suffix}"
        suffix += 1
    destination.write_bytes(content)

    return web.json_response({"csv_path": destination.relative_to(input_root).as_posix()})


def get_csv_files():
    input_root = Path(folder_paths.get_input_directory())
    if not input_root.exists():
        return ["(choose a CSV file)"]
    files = [
        path.relative_to(input_root).as_posix()
        for path in input_root.rglob("*.csv")
        if path.is_file()
    ]
    return ["(choose a CSV file)", *sorted(files, key=str.lower)]


def resolve_csv_path(csv_file, csv_path):
    requested = csv_path.strip() if csv_path and csv_path.strip() else csv_file
    if not requested or requested == "(choose a CSV file)":
        raise ValueError("Choose a CSV file or enter Custom CSV Path.")
    path = Path(requested).expanduser()
    if not path.is_absolute():
        path = Path(folder_paths.get_input_directory()) / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"CSV file was not found: {path}")
    return path


def load_values(csv_path, column, skip_header, delimiter, encoding):
    values = []
    with csv_path.open("r", encoding=encoding, newline="") as file:
        rows = csv.reader(file, delimiter=delimiter)
        if skip_header:
            next(rows, None)
        for row in rows:
            if len(row) >= column and (value := row[column - 1].strip()):
                values.append(value)
    if not values:
        raise ValueError(f"No non-empty values were found in column {column}.")
    return values


class EndorphinCSVLoader:
    """Load one text value per Queue Prompt batch from a CSV column."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "csv_path": ("STRING", {
                    "default": "",
                    "placeholder": "D:\\Prompts\\prompts.csv",
                    "tooltip": "Absolute path to the CSV file. Overrides CSV File when filled in.",
                }),
                "csv_file": (get_csv_files(), {
                    "default": "(choose a CSV file)",
                    "tooltip": "CSV files inside ComfyUI/input. Restart ComfyUI after adding a file.",
                }),
                "column": ("INT", {"default": 2, "min": 1, "max": 1000, "step": 1}),
                "skip_header": ("BOOLEAN", {"default": True}),
                "delimiter": ([",", ";", "tab"], {"default": ","}),
                "encoding": (["utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"], {"default": "utf-8-sig"}),
                "row": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000000,
                    "step": 1,
                    "tooltip": "Current row. Advances automatically after every Queue Prompt batch item.",
                }),
                "auto_increment": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Advance to the next CSV row after every Queue Prompt batch item.",
                }),
                "loop": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("value", "row_number")
    FUNCTION = "load_value"
    CATEGORY = "Endorphin Workshop/Utilities"

    def load_value(self, csv_path, csv_file, column, skip_header, delimiter, encoding, row, auto_increment, loop):
        csv_path = resolve_csv_path(csv_file, csv_path)
        values = load_values(csv_path, column, skip_header, "\t" if delimiter == "tab" else delimiter, encoding)
        index = (row - 1) % len(values) if loop else min(row - 1, len(values) - 1)
        return values[index], index + 1


NODE_CLASS_MAPPINGS = {"EndorphinCSVLoader": EndorphinCSVLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"EndorphinCSVLoader": "Endorphin CSV Loader"}
