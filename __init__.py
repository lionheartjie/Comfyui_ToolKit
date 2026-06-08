from .nodes.image_resize import NODE_CLASS_MAPPINGS as resize_mappings
from .nodes.image_resize import NODE_DISPLAY_NAME_MAPPINGS as resize_display_names
from .nodes.mask_detect_bbox import NODE_CLASS_MAPPINGS as mask_bbox_mappings
from .nodes.mask_detect_bbox import NODE_DISPLAY_NAME_MAPPINGS as mask_bbox_display_names

NODE_CLASS_MAPPINGS = {**resize_mappings, **mask_bbox_mappings}
NODE_DISPLAY_NAME_MAPPINGS = {**resize_display_names, **mask_bbox_display_names}

WEB_DIRECTORY = "js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
