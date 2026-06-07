import torch
import torch.nn.functional as F


class ImageResizeTool:
    """图像缩放工具节点：支持按比例/长边缩放，可自定义宽高比，以及裁切、拉伸、等比例缩放三种适配模式。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像": ("IMAGE",),
                "缩放模式": (["按比例缩放", "按长边缩放"],),
                "缩放比例": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 10.0,
                    "step": 0.01,
                    "display": "number",
                }),
                "长边尺寸": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 8192,
                    "step": 8,
                    "display": "number",
                }),
                "宽度比值": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1,
                    "display": "number",
                }),
                "高度比值": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1,
                    "display": "number",
                }),
                "适配模式": (["裁切", "拉伸", "等比缩放"],),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "resize_image"
    CATEGORY = "image/transform"

    @staticmethod
    def _calc_target_size(h, w, resize_mode, scale, long_side, aspect_w, aspect_h):
        """根据缩放模式计算目标宽高，aspect_w/aspect_h 均>0时使用自定义宽高比，否则保持原始比例。"""
        use_custom_ratio = (aspect_w > 0 and aspect_h > 0)
        aspect_ratio = aspect_w / aspect_h if use_custom_ratio else 0.0

        if resize_mode == "按比例缩放":
            if use_custom_ratio:
                if w >= h:
                    new_w = int(round(w * scale))
                    new_h = int(round(new_w / aspect_ratio))
                else:
                    new_h = int(round(h * scale))
                    new_w = int(round(new_h * aspect_ratio))
            else:
                new_h = int(round(h * scale))
                new_w = int(round(w * scale))
        elif resize_mode == "按长边缩放":
            long_edge = max(h, w)
            raw_ratio = long_side / long_edge
            raw_h = int(round(h * raw_ratio))
            raw_w = int(round(w * raw_ratio))
            if use_custom_ratio:
                if w >= h:
                    new_w = raw_w
                    new_h = int(round(new_w / aspect_ratio))
                else:
                    new_h = raw_h
                    new_w = int(round(new_h * aspect_ratio))
            else:
                new_h, new_w = raw_h, raw_w
        else:
            raise ValueError(f"未知的缩放模式: {resize_mode}")

        new_h = max(1, new_h)
        new_w = max(1, new_w)
        return new_h, new_w

    @staticmethod
    def _resize_stretch(image: torch.Tensor, target_h: int, target_w: int) -> torch.Tensor:
        """拉伸模式：直接缩放至目标尺寸。"""
        # image: BHWC -> BCHW
        x = image.permute(0, 3, 1, 2)
        x = F.interpolate(x, size=(target_h, target_w), mode="bilinear", align_corners=False)
        return x.permute(0, 2, 3, 1)

    @staticmethod
    def _resize_letterbox(image: torch.Tensor, target_h: int, target_w: int) -> torch.Tensor:
        """等比例缩放模式：等比缩放并居中，不足部分填充黑色。"""
        b, h, w, c = image.shape
        scale_ratio = min(target_h / h, target_w / w)
        new_h = int(round(h * scale_ratio))
        new_w = int(round(w * scale_ratio))

        # 等比缩放
        x = image.permute(0, 3, 1, 2)
        x = F.interpolate(x, size=(new_h, new_w), mode="bilinear", align_corners=False)

        # 创建黑色画布并居中放置
        canvas = torch.zeros((b, c, target_h, target_w), device=image.device, dtype=image.dtype)
        top = (target_h - new_h) // 2
        left = (target_w - new_w) // 2
        canvas[:, :, top:top + new_h, left:left + new_w] = x

        return canvas.permute(0, 2, 3, 1)

    @staticmethod
    def _resize_crop(image: torch.Tensor, target_h: int, target_w: int) -> torch.Tensor:
        """裁切模式：等比缩放至覆盖目标尺寸，然后中心裁切。"""
        b, h, w, c = image.shape
        scale_ratio = max(target_h / h, target_w / w)
        new_h = int(round(h * scale_ratio))
        new_w = int(round(w * scale_ratio))

        # 等比缩放至覆盖目标区域
        x = image.permute(0, 3, 1, 2)
        x = F.interpolate(x, size=(new_h, new_w), mode="bilinear", align_corners=False)

        # 中心裁切
        top = (new_h - target_h) // 2
        left = (new_w - target_w) // 2
        x = x[:, :, top:top + target_h, left:left + target_w]

        return x.permute(0, 2, 3, 1)

    def resize_image(self, **kwargs) -> tuple[torch.Tensor]:
        # 从 UI 中文键名提取参数，内部使用英文变量名
        image = kwargs["图像"]
        resize_mode = kwargs["缩放模式"]
        scale = kwargs["缩放比例"]
        long_side = kwargs["长边尺寸"]
        aspect_w = kwargs["宽度比值"]
        aspect_h = kwargs["高度比值"]
        fit_mode = kwargs["适配模式"]

        b, h, w, c = image.shape

        new_h, new_w = self._calc_target_size(h, w, resize_mode, scale, long_side, aspect_w, aspect_h)

        if fit_mode == "拉伸":
            result = self._resize_stretch(image, new_h, new_w)
        elif fit_mode == "等比缩放":
            result = self._resize_letterbox(image, new_h, new_w)
        elif fit_mode == "裁切":
            result = self._resize_crop(image, new_h, new_w)
        else:
            raise ValueError(f"未知的适配模式: {fit_mode}")

        return (result,)


NODE_CLASS_MAPPINGS = {
    "ImageResizeTool": ImageResizeTool,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageResizeTool": "图像缩放工具",
}
