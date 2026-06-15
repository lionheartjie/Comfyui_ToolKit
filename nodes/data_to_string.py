import torch
import json


class DataToStringTool:
    """数据转字符串工具：将任意数据类型转换为有意义的字符串表示。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "数据": ("*",),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert_to_string"
    CATEGORY = "utils/conversion"

    @staticmethod
    def _safe_convert(data):
        """安全地将各种数据类型转换为字符串，避免内存地址。"""

        # 处理 torch.Tensor
        if isinstance(data, torch.Tensor):
            # 获取形状和数据类型信息
            shape = tuple(data.shape)
            dtype = str(data.dtype)
            device = str(data.device)

            # 如果张量很小，包含其值
            if data.numel() <= 10:
                values = data.flatten().tolist()
                return f"Tensor(shape={shape}, dtype={dtype}, device={device}, values={values})"
            else:
                # 显示前几个值和统计信息
                flat = data.flatten()
                first_values = flat[:5].tolist()
                mean_val = float(flat.mean().cpu()) if data.is_cuda else float(flat.mean())
                min_val = float(flat.min().cpu()) if data.is_cuda else float(flat.min())
                max_val = float(flat.max().cpu()) if data.is_cuda else float(flat.max())
                return f"Tensor(shape={shape}, dtype={dtype}, device={device}, first_values={first_values}..., stats={{mean:{mean_val:.4f}, min:{min_val:.4f}, max:{max_val:.4f}}})"

        # 处理字典
        elif isinstance(data, dict):
            try:
                return json.dumps(data, indent=2, default=str, ensure_ascii=False)
            except (TypeError, ValueError):
                return f"Dict(keys={list(data.keys())})"

        # 处理列表或元组
        elif isinstance(data, (list, tuple)):
            try:
                return json.dumps(data, indent=2, default=str, ensure_ascii=False)
            except (TypeError, ValueError):
                return f"{type(data).__name__}(length={len(data)}, items={str(data)[:200]}...)"

        # 处理基本数据类型
        elif isinstance(data, (str, int, float, bool, type(None))):
            return str(data)

        # 处理其他对象（包括SAMPLER等ComfyUI类型）
        else:
            type_name = type(data).__name__
            module_name = type(data).__module__

            # 获取对象的属性信息
            try:
                # 首先尝试获取对象的有用属性
                attrs_info = {}
                if hasattr(data, '__dict__'):
                    for key, value in data.__dict__.items():
                        if not key.startswith('_'):
                            # 避免无限递归，限制属性值长度
                            try:
                                value_str = str(value)[:100]
                                attrs_info[key] = value_str
                            except Exception:
                                attrs_info[key] = f"{type(value).__name__}"

                if attrs_info:
                    attrs_str = json.dumps(attrs_info, default=str, ensure_ascii=False)
                    return f"{module_name}.{type_name}({attrs_str})"

                # 如果没有属性，尝试获取repr
                repr_str = repr(data)
                if " object at 0x" not in repr_str:
                    return repr_str

                # 如果repr仍然是内存地址格式，尝试str()
                str_str = str(data)
                if " object at 0x" not in str_str:
                    return str_str

                # 最后返回类型信息
                return f"{module_name}.{type_name}(object)"
            except Exception as e:
                return f"{module_name}.{type_name}(无法获取详细信息: {str(e)[:50]})"

    def convert_to_string(self, 数据):
        """将输入数据转换为字符串。"""
        result = self._safe_convert(数据)
        return (result,)


NODE_CLASS_MAPPINGS = {
    "DataToStringTool": DataToStringTool,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DataToStringTool": "数据转字符串工具",
}
