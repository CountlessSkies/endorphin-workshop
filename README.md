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

### Endorphin Auto Reset Int
An `INT` node with a default value of `1`. Its **After Generate** control supports Fixed Value, Increment Value, Decrement Value, and Randomize Value. Once the requested queue has been submitted, `value` is restored to the selected `reset_value` (default: `1`) without waiting for generation to finish.

### Endorphin Save Image Advanced
Saves images as PNG, JPEG, or WEBP with configurable quality. Choose an existing subfolder in `ComfyUI/output`, or enter an absolute `custom_output_folder` such as `D:\Images\Job_01` to save outside ComfyUI.
