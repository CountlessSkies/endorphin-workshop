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
