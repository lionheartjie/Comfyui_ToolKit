import os
import re

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

# 系统字体目录（Windows 优先，兼容 macOS / Linux）
_FONT_DIRS = [
    os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
    "/System/Library/Fonts",
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
]

_FONT_CACHE = None


def _list_system_fonts() -> dict:
    """扫描系统字体目录，返回 {字体名: 字体文件路径}（结果缓存）。"""
    global _FONT_CACHE
    if _FONT_CACHE is not None:
        return _FONT_CACHE

    fonts = {}
    for font_dir in _FONT_DIRS:
        if not font_dir or not os.path.isdir(font_dir):
            continue
        for root, _, files in os.walk(font_dir):
            for name in files:
                if name.lower().endswith((".ttf", ".otf", ".ttc")):
                    display = os.path.splitext(name)[0]
                    # 同名时保留首个，避免覆盖
                    fonts.setdefault(display, os.path.join(root, name))

    if not fonts:
        fonts = {"default": ""}
    _FONT_CACHE = dict(sorted(fonts.items(), key=lambda kv: kv[0].lower()))
    return _FONT_CACHE


def _parse_color(color_str: str) -> tuple[int, int, int]:
    """解析颜色字符串，返回 0-255 的 (R, G, B)。支持 #RRGGBB / #RGB / 0xRRGGBB / RGB(R,G,B) / R,G,B。"""
    color_str = color_str.strip()

    hex_match = re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', color_str)
    if hex_match:
        hex_code = hex_match.group(1)
        if len(hex_code) == 3:
            hex_code = ''.join([c * 2 for c in hex_code])
        return int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)

    hex_match = re.match(r'^0x([0-9a-fA-F]{6})$', color_str, re.IGNORECASE)
    if hex_match:
        hex_code = hex_match.group(1)
        return int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)

    rgb_match = re.match(r'^(?:RGB\s*)?\(?\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)?$', color_str, re.IGNORECASE)
    if rgb_match:
        return (
            min(255, int(rgb_match.group(1))),
            min(255, int(rgb_match.group(2))),
            min(255, int(rgb_match.group(3))),
        )

    raise ValueError(f"无法解析颜色值: {color_str}。支持格式: #RRGGBB, #RGB, 0xRRGGBB, RGB(R,G,B), R,G,B")


class DebugInfoOnImage:
    """图像文字水印：将文本框内容作为水印合成到输入图像上，可设置字体、颜色、描边与位置。"""

    @classmethod
    def INPUT_TYPES(cls):
        font_names = list(_list_system_fonts().keys())
        return {
            "required": {
                "图像": ("IMAGE",),
                "文本": ("STRING", {
                    "default": "",
                    "multiline": True,
                }),
                "字体": (font_names,),
                "字体大小": ("INT", {
                    "default": 32,
                    "min": 1,
                    "max": 2048,
                    "step": 1,
                }),
                "文本颜色": ("STRING", {
                    "default": "#FFFFFF",
                    "multiline": False,
                }),
                "描边颜色": ("STRING", {
                    "default": "#000000",
                    "multiline": False,
                }),
                "描边宽度": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                }),
                "X坐标": ("INT", {
                    "default": 10,
                    "min": -8192,
                    "max": 8192,
                    "step": 1,
                }),
                "Y坐标": ("INT", {
                    "default": 10,
                    "min": -8192,
                    "max": 8192,
                    "step": 1,
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图像",)
    FUNCTION = "add_watermark"
    CATEGORY = "image"

    def add_watermark(self, 图像: torch.Tensor, 文本: str, 字体: str, 字体大小: int,
                      文本颜色: str, 描边颜色: str, 描边宽度: int,
                      X坐标: int, Y坐标: int) -> tuple[torch.Tensor]:
        """在图像上绘制文字水印。"""
        fill = _parse_color(文本颜色)
        stroke = _parse_color(描边颜色)

        font_path = _list_system_fonts().get(字体, "")
        try:
            font = ImageFont.truetype(font_path, 字体大小) if font_path else ImageFont.load_default()
        except (OSError, IOError):
            font = ImageFont.load_default()

        output_images = []
        for i in range(图像.shape[0]):
            # ComfyUI 的 IMAGE 为 BHWC、数值范围 0-1
            array = np.clip(图像[i].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
            img = Image.fromarray(array).convert("RGB")

            draw = ImageDraw.Draw(img)
            draw.text(
                (X坐标, Y坐标),
                文本,
                font=font,
                fill=fill,
                stroke_width=描边宽度,
                stroke_fill=stroke,
            )

            result = np.array(img).astype(np.float32) / 255.0
            output_images.append(torch.from_numpy(result)[None,])

        return (torch.cat(output_images, dim=0),)


NODE_CLASS_MAPPINGS = {
    "TK_DebugInfoOnImage": DebugInfoOnImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TK_DebugInfoOnImage": "TK_图像文字水印",
}
