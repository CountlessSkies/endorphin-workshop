import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "endorphin.AutoResetInt",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "EndorphinAutoResetInt") return;

        const originalOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function () {
            const result = originalOnExecuted?.apply(this, arguments);
            const valueWidget = this.widgets?.find((widget) => widget.name === "value");

            if (valueWidget) {
                valueWidget.value = 1;
                this.graph?.setDirtyCanvas(true, true);
            }

            return result;
        };
    },
});
