import torch
import re


class ImageChunker:
    """图像分块器：获取输入图像的尺寸，并根据输入的宽高比输出对应的分块尺寸。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像": ("IMAGE",),
                "宽高比": ("STRING", {
                    "default": "3:4",
                    "multiline": False,
                }),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT")
    RETURN_NAMES = ("宽度", "高度", "分块宽", "分块高")
    FUNCTION = "chunk_image"
    CATEGORY = "image/analysis"

    @staticmethod
    def _parse_aspect_ratio(ratio_str: str) -> tuple[int, int]:
        """
        解析宽高比字符串。

        支持格式: 3:4 或 3,4

        返回: (分子, 分母)
        """
        ratio_str = ratio_str.strip()

        # 处理 3:4 格式
        colon_match = re.match(r'^(\d+)\s*:\s*(\d+)$', ratio_str)
        if colon_match:
            numerator = int(colon_match.group(1))
            denominator = int(colon_match.group(2))
            return numerator, denominator

        # 处理 3,4 格式
        comma_match = re.match(r'^(\d+)\s*,\s*(\d+)$', ratio_str)
        if comma_match:
            numerator = int(comma_match.group(1))
            denominator = int(comma_match.group(2))
            return numerator, denominator

        raise ValueError(f"无法解析宽高比: {ratio_str}。支持格式: 3:4 或 3,4")

    def chunk_image(self, 图像: torch.Tensor, 宽高比: str) -> tuple[int, int, int, int]:
        """
        分析图像尺寸并计算分块尺寸。

        输入图像格式: (batch, height, width, channels)

        逻辑：
        - 如果图像宽 > 高（横向），则交换宽高比的分子分母
        - 否则保持原始宽高比
        """
        # 获取图像的形状
        batch, height, width, channels = 图像.shape

        # 解析宽高比
        try:
            ratio_w, ratio_h = self._parse_aspect_ratio(宽高比)
        except ValueError as e:
            raise ValueError(str(e))

        # 判断图像的宽高关系
        if width > height:
            # 图像是横向的，交换比例
            chunk_w = ratio_h
            chunk_h = ratio_w
        else:
            # 图像是纵向或正方形的，保持原始比例
            chunk_w = ratio_w
            chunk_h = ratio_h

        return (width, height, chunk_w, chunk_h)


NODE_CLASS_MAPPINGS = {
    "ImageChunker": ImageChunker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageChunker": "图像分块器",
}
