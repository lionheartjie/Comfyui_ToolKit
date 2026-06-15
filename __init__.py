from .nodes.image_resize import NODE_CLASS_MAPPINGS as resize_mappings
from .nodes.image_resize import NODE_DISPLAY_NAME_MAPPINGS as resize_display_names
from .nodes.mask_detect_bbox import NODE_CLASS_MAPPINGS as mask_bbox_mappings
from .nodes.mask_detect_bbox import NODE_DISPLAY_NAME_MAPPINGS as mask_bbox_display_names
from .nodes.data_to_string import NODE_CLASS_MAPPINGS as data_to_string_mappings
from .nodes.data_to_string import NODE_DISPLAY_NAME_MAPPINGS as data_to_string_display_names
from .nodes.color_image_generator import NODE_CLASS_MAPPINGS as color_image_mappings
from .nodes.color_image_generator import NODE_DISPLAY_NAME_MAPPINGS as color_image_display_names
from .nodes.image_chunker import NODE_CLASS_MAPPINGS as image_chunker_mappings
from .nodes.image_chunker import NODE_DISPLAY_NAME_MAPPINGS as image_chunker_display_names

NODE_CLASS_MAPPINGS = {**resize_mappings, **mask_bbox_mappings, **data_to_string_mappings, **color_image_mappings, **image_chunker_mappings}
NODE_DISPLAY_NAME_MAPPINGS = {**resize_display_names, **mask_bbox_display_names, **data_to_string_display_names, **color_image_display_names, **image_chunker_display_names}

WEB_DIRECTORY = "js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
