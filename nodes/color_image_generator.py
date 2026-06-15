import torch
import re


class ColorImageGenerator:
    """纯色图像生成器：根据指定的宽高和颜色生成纯色图像。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "宽度": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1,
                    "display": "number",
                }),
                "高度": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1,
                    "display": "number",
                }),
                "颜色值": ("STRING", {
                    "default": "#FF0000",
                    "multiline": False,
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "image/generation"

    @staticmethod
    def _parse_color(color_str: str) -> tuple[float, float, float]:
        """
        解析颜色字符串（支持RGB和十六进制两种格式）。

        支持格式：
        - 十六进制: #RRGGBB, #RGB, 0xRRGGBB
        - RGB: RGB(255,0,0), (255,0,0), 255,0,0

        返回: (R, G, B) 范围为 0-1 的浮点数
        """
        color_str = color_str.strip()

        # 处理十六进制颜色 #RRGGBB 或 #RGB
        hex_match = re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', color_str)
        if hex_match:
            hex_code = hex_match.group(1)
            if len(hex_code) == 3:
                # 扩展 #RGB 为 #RRGGBB
                hex_code = ''.join([c * 2 for c in hex_code])
            r = int(hex_code[0:2], 16) / 255.0
            g = int(hex_code[2:4], 16) / 255.0
            b = int(hex_code[4:6], 16) / 255.0
            return r, g, b

        # 处理 0xRRGGBB 格式
        hex_match = re.match(r'^0x([0-9a-fA-F]{6})$', color_str, re.IGNORECASE)
        if hex_match:
            hex_code = hex_match.group(1)
            r = int(hex_code[0:2], 16) / 255.0
            g = int(hex_code[2:4], 16) / 255.0
            b = int(hex_code[4:6], 16) / 255.0
            return r, g, b

        # 处理 RGB(R,G,B) 格式
        rgb_match = re.match(r'^RGB\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$', color_str, re.IGNORECASE)
        if rgb_match:
            r = int(rgb_match.group(1)) / 255.0
            g = int(rgb_match.group(2)) / 255.0
            b = int(rgb_match.group(3)) / 255.0
            return r, g, b

        # 处理 (R,G,B) 格式
        rgb_match = re.match(r'^\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\s*$', color_str)
        if rgb_match:
            r = int(rgb_match.group(1)) / 255.0
            g = int(rgb_match.group(2)) / 255.0
            b = int(rgb_match.group(3)) / 255.0
            return r, g, b

        # 处理 R,G,B 格式（直接逗号分隔）
        rgb_match = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$', color_str)
        if rgb_match:
            r = int(rgb_match.group(1)) / 255.0
            g = int(rgb_match.group(2)) / 255.0
            b = int(rgb_match.group(3)) / 255.0
            return r, g, b

        # 默认红色
        raise ValueError(f"无法解析颜色值: {color_str}。支持格式: #RRGGBB, #RGB, 0xRRGGBB, RGB(R,G,B), (R,G,B), R,G,B")

    def generate_image(self, 宽度: int, 高度: int, 颜色值: str) -> tuple[torch.Tensor]:
        """生成纯色图像。"""
        try:
            r, g, b = self._parse_color(颜色值)
        except ValueError as e:
            raise ValueError(str(e))

        # 创建图像张量 (batch=1, height, width, channels=3)
        # ComfyUI 的 IMAGE 格式是 BHWC，数值范围 0-1
        image = torch.ones((1, 高度, 宽度, 3), dtype=torch.float32)
        image[:, :, :, 0] = r  # R 通道
        image[:, :, :, 1] = g  # G 通道
        image[:, :, :, 2] = b  # B 通道

        return (image,)


NODE_CLASS_MAPPINGS = {
    "ColorImageGenerator": ColorImageGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ColorImageGenerator": "纯色图像生成器",
}
