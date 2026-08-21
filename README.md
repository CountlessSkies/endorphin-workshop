# endorphin-workshop Custom Nodes for ComfyUI

A custom node pack for ComfyUI.

## Nodes

### Endorphin Image To Prompt
Uses a locally-stored Qwen-VL model (e.g. Qwen2.5-VL-3B-Instruct) to describe an input image or generate prompts.

#### Inputs
* **model_path**: The absolute local directory path where the Qwen-VL model config & weights are located.
* **quantization**: Precision mode (`None (FP16)`, `8-bit`, `4-bit`).
* **prompt**: Text instructions sent to the model (e.g. "Describe this image in detail.").
* **max_tokens**: Maximum length of generated text.
* **keep_model_loaded**: If enabled, keeps the model in memory across runs for faster subsequent generations.
* **image** (Optional): Input ComfyUI image.

### Endorphin Switch Case (20)
Routes one of 20 optional inputs to `value`. Set **select** to the desired case number (1–20); connect only the cases your workflow needs. The node accepts and returns any ComfyUI data type.

### Endorphin Text Lines (20)
Splits multiline text into 20 string outputs (`line_01` through `line_20`). Empty lines are ignored and unused outputs are empty strings. Connect its outputs directly to matching cases on **Endorphin Switch Case (20)**.

### Endorphin Concatenate Text (3)
Concatenates `string_a`, `string_b`, and `string_c` in that order. Use **delimiter** to place text between each input (for example, a space, comma, or newline).

### Endorphin Auto Reset Int
An `INT` node with a default value of `1`. Enable **auto_increment** to increase `value` by one for each Queue Prompt batch item; disable it to keep the value fixed. Once the requested queue has been submitted, `value` is restored to the value that was present before queueing, without waiting for generation to finish.

### Endorphin Save Image Advanced
Saves images as PNG, JPEG, or WEBP with configurable quality. Choose an existing folder in `ComfyUI/output`, or enter an absolute `custom_output_folder` such as `D:\Images\Job_01` to save outside ComfyUI. Use **subfolder** for a relative nested destination. Set **suffix_digits** to control the numeric suffix, such as `2` for `01` or `5` for `00001`. Enable **overwrite** to omit the suffix and replace an existing file with the same name.

### Endorphin Cartesian Product (2D/3D)
An ordered counter for Queue Prompt batches. Set `min_value` and `max_value` for each dimension. In 2D mode, `value_2` advances first; after it reaches `max_value_2`, it returns to `min_value_2` and `value_1` advances. Set Queue Prompt's **Batch count** to the number of combinations to run. Turn off `auto_increment` to keep the current values for every batch.

### Endorphin CSV Loader
Loads one text value from a selected CSV column per Queue Prompt batch item. Use **Browse CSV** to select a local CSV file, enter an absolute path in `csv_path`, or choose a CSV placed in `ComfyUI/input`. The default reads column 2, skips the header, and loops after the final value. Turn off `auto_increment` to use the same row for every batch.

### Endorphin Folder Image Loader
Loads one image per Queue Prompt batch from an absolute folder path. Use **subfolder** to read a relative nested folder. Outputs the full filename and filename without extension. Sort by natural filename order, name, or modification time; turn off `auto_increment` to reuse the current image. The image index is restored after the requested queue has been submitted.

### Endorphin Color Palette Picker (Legacy)
Creates a flexible color palette directly in the node. Click a swatch to choose the active color, then edit its name, `#RRGGBB` HEX code, and integer output inline. Use **+ Add Color** to create more slots, or **Paste List** to import lines such as `mocha taupe (hex #977D67)`; add `= 10` to choose an integer other than the automatic sequence. The node resizes automatically and outputs the selected integer, color name, and HEX code.

## Etsy workflow nodes

The newer Etsy nodes use `G:\My Drive\_Etsy\_Listing` by default. They pass a
single `ENDORPHIN_ETSY_CONTEXT` between nodes so project IDs, source types, and
paths stay consistent. The architecture and naming conventions are documented
in [ETSY_WORKFLOW_ARCHITECTURE.md](ETSY_WORKFLOW_ARCHITECTURE.md).

### Endorphin Etsy Project Selector
Choose **Artwork** or **Redesign**, then select an existing project ID from a
folder scan. **Refresh** scans all direct project folders for the selected
workflow and removes an ID from the picker when its folder no longer exists.

The separate **Year** and **Month** dropdowns affect only **+ New**. That
button creates the lowest available `YYMMNNN` ID for Artwork, or
`RDYYMMNNN` for Redesign, plus its required folder skeleton. Existing-ID scans
are never filtered by date. Artwork always uses the `Artwork` source; Redesign
also lets you choose `Embroidery reference` or `Print reference`.

### Endorphin Etsy Source Asset Loader
Loads the canonical source selected by project context: `artwork_<ID>` directly
inside an Artwork project, or the first filename-sorted file in a Redesign
project's `source` folder.

### Endorphin Etsy Workflow Stage and Lazy Workflow Router
Use **Workflow Stage** to express Prepare, Approve, or Colorway flow. The Lazy
Workflow Router requests only the image input for the selected Artwork or
Redesign context, preventing the inactive branch from running.

### Endorphin Etsy Candidate Save / Approve / Approved Candidate Loader
Candidate Save writes redesign batches as `A`, `B`, `C`… slots without
overwriting occupied or approved candidates. Approve records an explicitly
selected candidate in `project.json`; approval never renames candidates. The
Approved Candidate Loader loads an approved letter for later colorway work.

### Endorphin Etsy Color Palette
The canonical palette for new Etsy workflows. Each editable row has a color
name, HEX value, integer value, and unique three-letter color code. Color codes
are suggested from a name only after that name is committed (blur/change), not
while typing; manually edited codes remain stable. It outputs `value`,
`color_name`, `hex`, and `color_code`.

### Legacy Etsy nodes
**Endorphin Etsy Listing Image Loader (Legacy)**, **Endorphin Etsy Listing Save
Image (Legacy)**, and **Endorphin Etsy Listing Selector (Legacy)** remain for
existing workflows. New Etsy workflows should use the project-context nodes
above instead.
