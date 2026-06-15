from .mask_detect_bbox import NODE_CLASS_MAPPINGS as mask_bbox_mappings
from .mask_detect_bbox import NODE_DISPLAY_NAME_MAPPINGS as mask_bbox_display_names
from .data_to_string import NODE_CLASS_MAPPINGS as data_to_string_mappings
from .data_to_string import NODE_DISPLAY_NAME_MAPPINGS as data_to_string_display_names
from .color_image_generator import NODE_CLASS_MAPPINGS as color_image_mappings
from .color_image_generator import NODE_DISPLAY_NAME_MAPPINGS as color_image_display_names
from .image_chunker import NODE_CLASS_MAPPINGS as image_chunker_mappings
from .image_chunker import NODE_DISPLAY_NAME_MAPPINGS as image_chunker_display_names

NODE_CLASS_MAPPINGS = {
    **mask_bbox_mappings,
    **data_to_string_mappings,
    **color_image_mappings,
    **image_chunker_mappings,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    **mask_bbox_display_names,
    **data_to_string_display_names,
    **color_image_display_names,
    **image_chunker_display_names,
}
