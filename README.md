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
An `INT` node with a default value of `1`. Its **After Generate** control supports Fixed Value, Increment Value, Decrement Value, and Randomize Value. Once the requested queue has been submitted, `value` is restored to the selected `reset_value` (default: `1`) without waiting for generation to finish.

### Endorphin Save Image Advanced
Saves images as PNG, JPEG, or WEBP with configurable quality. Choose an existing subfolder in `ComfyUI/output`, or enter an absolute `custom_output_folder` such as `D:\Images\Job_01` to save outside ComfyUI.

### Endorphin Cartesian Product (2D/3D)
An ordered counter for Queue Prompt batches. In 2D mode, `value_2` advances first; after it reaches `max_value_2`, it returns to `1` and `value_1` advances. Set Queue Prompt's **Batch count** to the number of combinations to run. Turn off `auto_increment` to keep the current values for every batch.

### Endorphin CSV Loader
Loads one text value from a selected CSV column per Queue Prompt batch item. Use **Browse CSV** to select a local CSV file, enter an absolute path in `csv_path`, or choose a CSV placed in `ComfyUI/input`. The default reads column 2, skips the header, and loops after the final value. Turn off `auto_increment` to use the same row for every batch.

### Endorphin Folder Image Loader
Loads one image per Queue Prompt batch from an absolute folder path. Outputs the full filename and filename without extension. Sort by natural filename order, name, or modification time; turn off `auto_increment` to reuse the current image. The image index is restored after the requested queue has been submitted.
