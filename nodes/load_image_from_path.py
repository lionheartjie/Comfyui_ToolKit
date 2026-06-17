import os

import numpy as np
import torch
from PIL import Image, ImageOps, ImageSequence


class LoadImageFromPath:
    """路径加载图像：根据输入的文件路径从磁盘加载图像，输出 IMAGE 与 MASK。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "路径": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("图像", "遮罩")
    FUNCTION = "load_image"
    CATEGORY = "image"

    def load_image(self, 路径: str) -> tuple[torch.Tensor, torch.Tensor]:
        """从指定路径加载图像。"""
        image_path = 路径.strip().strip('"').strip("'")
        if not image_path:
            raise ValueError("路径不能为空。")
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"找不到文件: {image_path}")

        img = Image.open(image_path)

        output_images = []
        output_masks = []
        for frame in ImageSequence.Iterator(img):
            # 修正 EXIF 方向信息
            frame = ImageOps.exif_transpose(frame)
            rgb = frame.convert("RGB")

            # ComfyUI 的 IMAGE 格式是 BHWC，数值范围 0-1
            image = np.array(rgb).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            output_images.append(image)

            # 从 alpha 通道提取遮罩（无 alpha 时输出全零遮罩）
            if "A" in frame.getbands():
                mask = np.array(frame.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            else:
                mask = torch.zeros((rgb.height, rgb.width), dtype=torch.float32)
            output_masks.append(mask.unsqueeze(0))

        # 多帧（如动图）尺寸一致时合并为批次，否则仅取首帧
        if len(output_images) > 1 and all(i.shape == output_images[0].shape for i in output_images):
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        return (output_image, output_mask)


NODE_CLASS_MAPPINGS = {
    "TK_LoadImageFromPath": LoadImageFromPath,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TK_LoadImageFromPath": "TK_路径加载图像",
}
