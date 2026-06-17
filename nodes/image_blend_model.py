import torch
import torch.nn.functional as F

EPS = 1e-7

# ---------------------------------------------------------------------------
# 亮度 / 非分离（HSL）辅助函数 —— 参考 PDF/W3C 混合规范，Photoshop 同源
# ---------------------------------------------------------------------------

def _lum(c: torch.Tensor) -> torch.Tensor:
    """像素亮度，返回 (..., 1)。"""
    return 0.3 * c[..., 0:1] + 0.59 * c[..., 1:2] + 0.11 * c[..., 2:3]


def _sat(c: torch.Tensor) -> torch.Tensor:
    """像素饱和度（max-min），返回 (..., 1)。"""
    return c.max(dim=-1, keepdim=True).values - c.min(dim=-1, keepdim=True).values


def _clip_color(c: torch.Tensor) -> torch.Tensor:
    """将颜色裁剪回 [0,1]，同时保持亮度。"""
    L = _lum(c)
    n = c.min(dim=-1, keepdim=True).values
    x = c.max(dim=-1, keepdim=True).values
    c = torch.where(n < 0, L + (c - L) * L / (L - n + EPS), c)
    c = torch.where(x > 1, L + (c - L) * (1 - L) / (x - L + EPS), c)
    return c


def _set_lum(c: torch.Tensor, L: torch.Tensor) -> torch.Tensor:
    """将颜色 c 的亮度设为 L。"""
    return _clip_color(c + (L - _lum(c)))


def _set_sat(c: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
    """将颜色 c 的饱和度设为 s（保持最大/中间/最小通道的相对关系）。"""
    sorted_vals, sort_idx = torch.sort(c, dim=-1)
    vmin = sorted_vals[..., 0:1]
    vmid = sorted_vals[..., 1:2]
    vmax = sorted_vals[..., 2:3]
    denom = vmax - vmin
    new_mid = torch.where(denom > 0, (vmid - vmin) * s / (denom + EPS), torch.zeros_like(vmid))
    new_max = torch.where(denom > 0, s, torch.zeros_like(vmax))
    new_min = torch.zeros_like(vmin)
    new_sorted = torch.cat([new_min, new_mid, new_max], dim=-1)
    return torch.zeros_like(c).scatter(-1, sort_idx, new_sorted)


# ---------------------------------------------------------------------------
# 各混合模式：输入 base(底)、top(混合图)，均为 0-1 的 BHWC 张量
# ---------------------------------------------------------------------------

def _normal(b, s):       return s
def _darken(b, s):       return torch.minimum(b, s)
def _multiply(b, s):     return b * s
def _linear_burn(b, s):  return torch.clamp(b + s - 1, 0, 1)
def _lighten(b, s):      return torch.maximum(b, s)
def _screen(b, s):       return b + s - b * s
def _linear_dodge(b, s): return torch.clamp(b + s, 0, 1)
def _overlay(b, s):      return torch.where(b <= 0.5, 2 * b * s, 1 - 2 * (1 - b) * (1 - s))
def _hard_light(b, s):   return torch.where(s <= 0.5, 2 * b * s, 1 - 2 * (1 - b) * (1 - s))
def _linear_light(b, s): return torch.clamp(b + 2 * s - 1, 0, 1)
def _pin_light(b, s):    return torch.where(s <= 0.5, torch.minimum(b, 2 * s), torch.maximum(b, 2 * s - 1))
def _difference(b, s):   return torch.abs(b - s)
def _exclusion(b, s):    return b + s - 2 * b * s
def _subtract(b, s):     return torch.clamp(b - s, 0, 1)
def _divide(b, s):       return torch.clamp(b / (s + EPS), 0, 1)


def _color_burn(b, s):
    out = 1 - torch.clamp((1 - b) / (s + EPS), max=1.0)
    out = torch.where(s <= 0, torch.zeros_like(b), out)
    return torch.where(b >= 1, torch.ones_like(b), out)


def _color_dodge(b, s):
    out = torch.clamp(b / (1 - s + EPS), max=1.0)
    out = torch.where(s >= 1, torch.ones_like(b), out)
    return torch.where(b <= 0, torch.zeros_like(b), out)


def _soft_light(b, s):
    d = torch.where(b <= 0.25, ((16 * b - 12) * b + 4) * b, torch.sqrt(torch.clamp(b, min=0.0)))
    return torch.where(s <= 0.5, b - (1 - 2 * s) * b * (1 - b), b + (2 * s - 1) * (d - b))


def _vivid_light(b, s):
    out = torch.where(
        s <= 0.5,
        1 - torch.clamp((1 - b) / (2 * s + EPS), max=1.0),
        torch.clamp(b / (2 * (1 - s) + EPS), max=1.0),
    )
    return torch.clamp(out, 0, 1)


def _hard_mix(b, s):
    v = _vivid_light(b, s)
    return torch.where(v >= 0.5, torch.ones_like(b), torch.zeros_like(b))


def _darker_color(b, s):  return torch.where(_lum(b) <= _lum(s), b, s)
def _lighter_color(b, s): return torch.where(_lum(b) >= _lum(s), b, s)

def _hue(b, s):        return _set_lum(_set_sat(s, _sat(b)), _lum(b))
def _saturation(b, s): return _set_lum(_set_sat(b, _sat(s)), _lum(b))
def _color(b, s):      return _set_lum(s, _lum(b))
def _luminosity(b, s): return _set_lum(b, _lum(s))


# 显示顺序与 Photoshop 图层面板一致；"溶解" 单独处理
_BLEND_MODES = {
    "正常": _normal,
    "溶解": None,
    "变暗": _darken,
    "正片叠底": _multiply,
    "颜色加深": _color_burn,
    "线性加深": _linear_burn,
    "深色": _darker_color,
    "变亮": _lighten,
    "滤色": _screen,
    "颜色减淡": _color_dodge,
    "线性减淡(添加)": _linear_dodge,
    "浅色": _lighter_color,
    "叠加": _overlay,
    "柔光": _soft_light,
    "强光": _hard_light,
    "亮光": _vivid_light,
    "线性光": _linear_light,
    "点光": _pin_light,
    "实色混合": _hard_mix,
    "差值": _difference,
    "排除": _exclusion,
    "减去": _subtract,
    "划分": _divide,
    "色相": _hue,
    "饱和度": _saturation,
    "颜色": _color,
    "明度": _luminosity,
}


def _match(base: torch.Tensor, top: torch.Tensor):
    """将 top 缩放到 base 的尺寸，并对批次维做广播。"""
    if top.shape[1] != base.shape[1] or top.shape[2] != base.shape[2]:
        t = top.permute(0, 3, 1, 2)
        t = F.interpolate(t, size=(base.shape[1], base.shape[2]), mode="bilinear", align_corners=False)
        top = t.permute(0, 2, 3, 1)

    if top.shape[0] != base.shape[0]:
        if top.shape[0] == 1:
            top = top.repeat(base.shape[0], 1, 1, 1)
        elif base.shape[0] == 1:
            base = base.repeat(top.shape[0], 1, 1, 1)
        else:
            n = min(base.shape[0], top.shape[0])
            base, top = base[:n], top[:n]
    return base, top


class ImageBlendModel:
    """图像混合：按 Photoshop 图层混合模式混合两张图像，并带不透明度（混合强度）。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "底图": ("IMAGE",),
                "混合图": ("IMAGE",),
                "混合模式": (list(_BLEND_MODES.keys()),),
                "混合强度": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图像",)
    FUNCTION = "blend"
    CATEGORY = "image"

    def blend(self, 底图: torch.Tensor, 混合图: torch.Tensor, 混合模式: str,
              混合强度: float) -> tuple[torch.Tensor]:
        """混合两张图像。"""
        base = torch.clamp(底图[..., :3].float(), 0.0, 1.0)
        top = torch.clamp(混合图[..., :3].float(), 0.0, 1.0)
        base, top = _match(base, top)

        if 混合模式 == "溶解":
            # 溶解：以混合强度为概率随机选取混合图像素
            noise = torch.rand_like(base[..., :1])
            mask = (noise < 混合强度).float()
            out = top * mask + base * (1.0 - mask)
        else:
            fn = _BLEND_MODES.get(混合模式, _normal)
            blended = torch.clamp(fn(base, top), 0.0, 1.0)
            out = base * (1.0 - 混合强度) + blended * 混合强度

        return (torch.clamp(out, 0.0, 1.0),)


NODE_CLASS_MAPPINGS = {
    "TK_ImageBlendModel": ImageBlendModel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TK_ImageBlendModel": "TK_图像混合",
}
