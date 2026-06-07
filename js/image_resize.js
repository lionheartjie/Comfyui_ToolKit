import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "Comfyui_ToolKit.ImageResizeTool",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "ImageResizeTool") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            // 按名称查找控件
            const getWidget = (name) => this.widgets.find((w) => w.name === name);

            const 缩放模式Widget = getWidget("缩放模式");
            const 缩放比例Widget = getWidget("缩放比例");
            const 长边尺寸Widget = getWidget("长边尺寸");

            if (!缩放模式Widget || !缩放比例Widget || !长边尺寸Widget) return result;

            const updateWidgets = () => {
                const mode = 缩放模式Widget.value;
                if (mode === "按比例缩放") {
                    缩放比例Widget.disabled = false;
                    长边尺寸Widget.disabled = true;
                } else if (mode === "按长边缩放") {
                    缩放比例Widget.disabled = true;
                    长边尺寸Widget.disabled = false;
                }
            };

            // 监听缩放模式变化
            const origCallback = 缩放模式Widget.callback;
            缩放模式Widget.callback = function (...args) {
                updateWidgets();
                if (origCallback) return origCallback.apply(this, args);
            };

            // 初始状态
            updateWidgets();

            return result;
        };
    },
});
