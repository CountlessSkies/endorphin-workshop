import os
import gc
import torch
import numpy as np
from PIL import Image
try:
    from transformers import AutoModelForImageTextToText as AutoModelForVision2Seq
except ImportError:
    from transformers import AutoModelForVision2Seq
from transformers import AutoProcessor, BitsAndBytesConfig

# Global cache for loaded model, processor, and metadata
_cached_model = None
_cached_processor = None
_cached_signature = None

def clear_cache():
    global _cached_model, _cached_processor, _cached_signature
    if _cached_model is not None:
        try:
            _cached_model = _cached_model.cpu()
        except:
            pass
        _cached_model = None
    _cached_processor = None
    _cached_signature = None
    
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

PREDEFINED_MODELS = {
    "Qwen2.5-VL-3B-Instruct": "Qwen/Qwen2.5-VL-3B-Instruct",
    "Qwen2.5-VL-7B-Instruct": "Qwen/Qwen2.5-VL-7B-Instruct",
    "Qwen3-VL-2B-Instruct": "Qwen/Qwen3-VL-2B-Instruct",
    "Qwen3-VL-4B-Instruct": "Qwen/Qwen3-VL-4B-Instruct",
    "Qwen3-VL-8B-Instruct": "Qwen/Qwen3-VL-8B-Instruct",
    "Qwen3-VL-2B-Thinking": "Qwen/Qwen3-VL-2B-Thinking",
    "Qwen3-VL-4B-Thinking": "Qwen/Qwen3-VL-4B-Thinking",
    "Qwen3-VL-8B-Thinking": "Qwen/Qwen3-VL-8B-Thinking",
}

PRESET_PROMPTS = [
    "🖼️ Detailed Description",
    "🏷️ Short Caption",
    "🎨 Stable Diffusion Prompt",
    "📝 Extract Text (OCR)"
]

PRESET_PROMPT_MAP = {
    "🖼️ Detailed Description": "Describe this image in detail.",
    "🏷️ Short Caption": "Generate a short, concise caption for this image.",
    "🎨 Stable Diffusion Prompt": "Generate a highly descriptive prompt for Stable Diffusion based on this image, focusing on subject, style, colors, and lighting.",
    "📝 Extract Text (OCR)": "Extract all text found in this image exactly as it is."
}

def get_model_list():
    import folder_paths
    llm_paths = folder_paths.get_folder_paths("LLM") if "LLM" in folder_paths.folder_names_and_paths else []
    default_base_dir = llm_paths[0] if llm_paths else os.path.join(folder_paths.models_dir, "LLM")
    
    local_models = []
    if os.path.exists(default_base_dir):
        for d in os.listdir(default_base_dir):
            if os.path.isdir(os.path.join(default_base_dir, d)):
                local_models.append(d)
                
    choices = list(PREDEFINED_MODELS.keys())
    for model in local_models:
        if model not in choices:
            choices.append(model)
            
    if not choices:
        choices = ["Qwen2.5-VL-3B-Instruct"]
    return choices

class EndorphinImageToPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (get_model_list(), {
                    "default": "Qwen2.5-VL-3B-Instruct",
                    "tooltip": "Select a predefined model or a folder scanned inside ComfyUI/models/LLM"
                }),
                "custom_model_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Optional: Type an absolute path or a custom Hugging Face repo ID to override the selection."
                }),
                "mode": (["standard", "advanced"], {
                    "default": "standard",
                    "tooltip": "Standard hides advanced settings. Advanced exposes full sampling parameters."
                }),
                "quantization": (["None (FP16)", "8-bit", "4-bit"], {
                    "default": "None (FP16)",
                    "tooltip": "Quantization mode. 4-bit/8-bit requires CUDA and bitsandbytes."
                }),
                "preset_prompt": (PRESET_PROMPTS, {
                    "default": "🖼️ Detailed Description",
                    "tooltip": "Select a built-in instruction template."
                }),
                "custom_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Optional: Type a custom prompt. If filled, it completely overrides the preset selection above."
                }),
                "max_tokens": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1,
                    "tooltip": "Maximum number of tokens to generate."
                })
            },
            "optional": {
                "image": ("IMAGE",),
                "video": ("IMAGE",),
                "temperature": ("FLOAT", {
                    "default": 0.6,
                    "min": 0.1,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "Sampling temperature. Higher values mean more creative outputs."
                }),
                "top_p": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "Nucleus sampling. Lower values keep only highly likely words."
                }),
                "num_beams": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 8,
                    "step": 1,
                    "tooltip": "Number of beams for beam search. Values > 1 disable temperature sampling."
                }),
                "repetition_penalty": ("FLOAT", {
                    "default": 1.2,
                    "min": 0.5,
                    "max": 2.0,
                    "step": 0.05,
                    "tooltip": "Penalty for repeating words/phrases."
                }),
                "frame_count": ("INT", {
                    "default": 16,
                    "min": 1,
                    "max": 64,
                    "step": 1,
                    "tooltip": "Number of frames to extract from video inputs."
                }),
                "use_torch_compile": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Enables PyTorch compilation to speed up generation (first run will be slow)."
                }),
                "device": (["auto", "cpu", "mps", "cuda"], {
                    "default": "auto",
                    "tooltip": "Choose target device (CPU, CUDA, or Apple Silicon MPS)."
                }),
                "keep_model_loaded": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Keep the model in memory between runs."
                })
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "Endorphin Workshop/Utilities"

    def tensor_to_pil(self, tensor):
        if tensor is None:
            return None
        if len(tensor.shape) == 4:
            tensor = tensor[0]
        array = (tensor.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(array)

    def generate_prompt(
        self, model_name, custom_model_path, mode, quantization, preset_prompt, custom_prompt, max_tokens,
        temperature=0.6, top_p=0.9, num_beams=1, repetition_penalty=1.2, frame_count=16, 
        use_torch_compile=False, device="auto", keep_model_loaded=True, image=None, video=None
    ):
        global _cached_model, _cached_processor, _cached_signature

        # Handle optional params falling back to defaults if not sent by front-end when hidden
        if temperature is None: temperature = 0.6
        if top_p is None: top_p = 0.9
        if num_beams is None: num_beams = 1
        if repetition_penalty is None: repetition_penalty = 1.2
        if frame_count is None: frame_count = 16
        if use_torch_compile is None: use_torch_compile = False
        if device is None: device = "auto"
        if keep_model_loaded is None: keep_model_loaded = True

        # Override advanced parameters to default if in standard mode
        if mode == "standard":
            temperature = 0.6
            top_p = 0.9
            num_beams = 1
            repetition_penalty = 1.2
            frame_count = 16
            use_torch_compile = False
            device = "auto"

        import folder_paths
        llm_paths = folder_paths.get_folder_paths("LLM") if "LLM" in folder_paths.folder_names_and_paths else []
        default_base_dir = llm_paths[0] if llm_paths else os.path.join(folder_paths.models_dir, "LLM")

        # Resolve paths
        path_or_repo = custom_model_path.strip()
        if not path_or_repo:
            if model_name in PREDEFINED_MODELS:
                path_or_repo = PREDEFINED_MODELS[model_name]
            else:
                path_or_repo = os.path.join(default_base_dir, model_name)

        if "/" in path_or_repo and not os.path.exists(path_or_repo):
            repo_id = path_or_repo
            folder_name = repo_id.split("/")[-1]
            path = os.path.join(default_base_dir, folder_name)
            
            is_downloaded = False
            if os.path.exists(path) and os.path.isdir(path):
                files = os.listdir(path)
                if any(f.endswith(".safetensors") or f.endswith(".bin") for f in files):
                    is_downloaded = True
            
            if not is_downloaded:
                print(f"[endorphin-workshop] Downloading model: {repo_id} -> {path}")
                os.makedirs(path, exist_ok=True)
                from huggingface_hub import snapshot_download
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=path,
                    local_dir_use_symlinks=False,
                    ignore_patterns=["*.md", ".git*"]
                )
        elif not os.path.isabs(path_or_repo):
            path = os.path.join(default_base_dir, path_or_repo)
        else:
            path = os.path.abspath(path_or_repo)

        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model path does not exist: {path}")
        if not os.path.exists(os.path.join(path, "config.json")):
            raise FileNotFoundError(f"No config.json found in model path: {path}")

        # Choose the optimal device
        device_choice = device
        if device_choice == "auto":
            device = "cpu"
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
        else:
            device = device_choice

        signature = (path, quantization, device, use_torch_compile)

        if _cached_model is None or _cached_processor is None or _cached_signature != signature:
            print(f"[endorphin-workshop] Loading model from: {path} on {device}")
            clear_cache()

            quantization_config = None
            torch_dtype = torch.float32 if device == "cpu" else torch.float16

            if quantization == "4-bit":
                if device != "cuda":
                    print("[endorphin-workshop] Warning: 4-bit quantization requires CUDA. Falling back to non-quantized.")
                else:
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True
                    )
                    torch_dtype = None
            elif quantization == "8-bit":
                if device != "cuda":
                    print("[endorphin-workshop] Warning: 8-bit quantization requires CUDA. Falling back to non-quantized.")
                else:
                    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                    torch_dtype = None

            load_kwargs = {
                "trust_remote_code": True,
                "local_files_only": True
            }

            if quantization_config is not None:
                load_kwargs["quantization_config"] = quantization_config
                load_kwargs["device_map"] = "auto"
            else:
                load_kwargs["torch_dtype"] = torch_dtype
                if device != "cpu":
                    load_kwargs["device_map"] = "auto"

            try:
                model = AutoModelForVision2Seq.from_pretrained(path, **load_kwargs)
                processor = AutoProcessor.from_pretrained(path, trust_remote_code=True, local_files_only=True)
                
                if quantization_config is None and device == "cpu":
                    model = model.to(device)
                
                if use_torch_compile and device.startswith("cuda"):
                    try:
                        model = torch.compile(model)
                        print("[endorphin-workshop] Torch compile enabled.")
                    except Exception as exc:
                        print(f"[endorphin-workshop] Torch compile skipped: {exc}")
                
                _cached_model = model
                _cached_processor = processor
                _cached_signature = signature
            except Exception as e:
                clear_cache()
                raise RuntimeError(f"Error loading Qwen-VL model: {str(e)}")
        else:
            print("[endorphin-workshop] Using cached Qwen-VL model")
            model = _cached_model
            processor = _cached_processor

        # Convert image and video
        pil_image = self.tensor_to_pil(image)
        pil_video = None
        if video is not None:
            frames = [self.tensor_to_pil(f) for f in video]
            if len(frames) > frame_count:
                indices = np.linspace(0, len(frames) - 1, frame_count, dtype=int)
                frames = [frames[i] for i in indices]
            pil_video = frames

        # Resolve prompt: Use custom_prompt if provided, otherwise use the selected preset_prompt mapping
        final_prompt = PRESET_PROMPT_MAP.get(preset_prompt, "Describe this image in detail.")
        if custom_prompt and custom_prompt.strip():
            final_prompt = custom_prompt.strip()

        # Prepare inputs
        conversation = [{"role": "user", "content": []}]
        if pil_image is not None:
            conversation[0]["content"].append({"type": "image", "image": pil_image})
        if pil_video is not None and len(pil_video) > 0:
            conversation[0]["content"].append({"type": "video", "video": pil_video})
            
        conversation[0]["content"].append({"type": "text", "text": final_prompt})

        # Apply chat template
        try:
            chat_text = processor.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
        except Exception as e:
            raise RuntimeError(f"Failed to apply chat template. Ensure your model is a Qwen-VL Instruct model: {str(e)}")

        images = [pil_image] if pil_image is not None else None
        videos = [pil_video] if pil_video is not None else None
        
        # Process and prepare tensors
        processed_inputs = processor(text=[chat_text], images=images, videos=videos, return_tensors="pt")
        
        # Move inputs to same device as model
        model_device = next(model.parameters()).device
        model_inputs = {
            k: v.to(model_device) if isinstance(v, torch.Tensor) else v
            for k, v in processed_inputs.items()
        }

        # Generate output
        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "pad_token_id": processor.tokenizer.pad_token_id,
            "eos_token_id": processor.tokenizer.eos_token_id,
            "repetition_penalty": repetition_penalty,
        }
        
        if num_beams > 1:
            gen_kwargs["num_beams"] = num_beams
            gen_kwargs["do_sample"] = False
        else:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = temperature
            gen_kwargs["top_p"] = top_p

        try:
            with torch.no_grad():
                generated_ids = model.generate(**model_inputs, **gen_kwargs)
            
            input_length = model_inputs["input_ids"].shape[-1]
            generated_ids_trimmed = [
                out_ids[input_length:] for out_ids in generated_ids
            ]
            
            output_text = processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
        except Exception as e:
            raise RuntimeError(f"Error during model generation: {str(e)}")
        finally:
            if not keep_model_loaded:
                clear_cache()

        return (output_text.strip(),)

NODE_CLASS_MAPPINGS = {
    "EndorphinImageToPrompt": EndorphinImageToPrompt
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EndorphinImageToPrompt": "Endorphin Image To Prompt"
}
