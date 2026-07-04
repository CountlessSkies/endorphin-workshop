import sys
from pathlib import Path

# Add current folder to sys.path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from .image_to_prompt import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Export JS directory for frontend extensions
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
