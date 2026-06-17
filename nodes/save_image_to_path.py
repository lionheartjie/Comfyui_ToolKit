import os

import numpy as np
import torch
from PIL import Image


class SaveImageToPath:
    """路径保存图像：将输入的 IMAGE 保存到指定的文件路径。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像": ("IMAGE",),
                "路径": ("STRING", {
                    "default": "output.png",
                    "multiline": False,
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("保存路径",)
    FUNCTION = "save_image"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def save_image(self, 图像: torch.Tensor, 路径: str) -> tuple[str]:
        """将图像保存到指定路径，多张图像时自动追加序号。"""
        save_path = 路径.strip().strip('"').strip("'")
        if not save_path:
            raise ValueError("路径不能为空。")

        # 拆分目录、文件名、扩展名（无扩展名时默认 .png）
        directory = os.path.dirname(save_path)
        base_name = os.path.basename(save_path)
        stem, ext = os.path.splitext(base_name)
        if not ext:
            ext = ".png"
        if not stem:
            stem = "output"
        if directory:
            os.makedirs(directory, exist_ok=True)

        batch_size = 图像.shape[0]
        saved_paths = []
        for i in range(batch_size):
            # ComfyUI 的 IMAGE 为 BHWC、数值范围 0-1
            array = 图像[i].cpu().numpy()
            array = np.clip(array * 255.0, 0, 255).astype(np.uint8)
            img = Image.fromarray(array)

            if batch_size > 1:
                file_name = f"{stem}_{i:05d}{ext}"
            else:
                file_name = f"{stem}{ext}"
            file_path = os.path.join(directory, file_name) if directory else file_name

            img.save(file_path)
            saved_paths.append(file_path)

        return ("\n".join(saved_paths),)


NODE_CLASS_MAPPINGS = {
    "TK_SaveImageToPath": SaveImageToPath,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TK_SaveImageToPath": "TK_路径保存图像",
}
