import torch
import numpy as np


class MaskDetectBBox:
    """Mask区域检测工具节点：检测mask中的白色区域并生成边界框。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Mask": ("MASK",),
                "Threshold": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "number",
                }),
            },
        }

    RETURN_TYPES = ("BBOX", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("BBox", "X", "Y", "宽度", "高度")
    FUNCTION = "detect_bbox"
    CATEGORY = "mask/analysis"

    @staticmethod
    def _get_bbox_from_mask(mask: torch.Tensor, threshold: float) -> tuple[int, int, int, int]:
        """
        从mask中检测边界框。
        返回: (x_min, y_min, width, height)
        """
        # 如果是多batch，取第一个
        if mask.dim() == 3:
            mask = mask[0]

        # 转换为numpy并转为二值化
        mask_np = mask.cpu().numpy()
        binary_mask = (mask_np > threshold).astype(np.uint8)

        # 找到所有非零点
        y_indices, x_indices = np.where(binary_mask > 0)

        if len(x_indices) == 0 or len(y_indices) == 0:
            # 如果mask为空，返回默认值
            return 0, 0, 0, 0

        # 计算边界框
        x_min = int(np.min(x_indices))
        x_max = int(np.max(x_indices))
        y_min = int(np.min(y_indices))
        y_max = int(np.max(y_indices))

        width = x_max - x_min + 1
        height = y_max - y_min + 1

        return x_min, y_min, width, height

    def detect_bbox(self, **kwargs) -> tuple:
        """检测mask中的边界框。"""
        mask = kwargs["Mask"]
        threshold = kwargs["Threshold"]

        x_min, y_min, width, height = self._get_bbox_from_mask(mask, threshold)

        # 创建bbox张量 (格式: [x_min, y_min, x_max, y_max])
        bbox = torch.tensor([x_min, y_min, x_min + width - 1, y_min + height - 1], dtype=torch.float32)

        return (bbox, x_min, y_min, width, height)


NODE_CLASS_MAPPINGS = {
    "MaskDetectBBox": MaskDetectBBox,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskDetectBBox": "Mask检测边界框",
}
