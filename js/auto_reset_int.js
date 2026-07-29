import { app } from "../../../scripts/app.js";

function resetAfterQueueSubmission() {
    for (const node of app.graph?._nodes ?? []) {
        if (node.comfyClass !== "EndorphinAutoResetInt") continue;

        const enabledWidget = node.widgets?.find((widget) => widget.name === "reset_after_batch");
        if (!enabledWidget?.value) continue;

        const valueWidget = node.widgets?.find((widget) => widget.name === "value");
        const resetWidget = node.widgets?.find((widget) => widget.name === "reset_value");
        if (!valueWidget || !resetWidget) continue;

        valueWidget.value = resetWidget.value;
        valueWidget.callback?.(resetWidget.value);
        node.graph?.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "endorphin.AutoResetInt",
    setup() {
        const originalQueuePrompt = app.queuePrompt;
        app.queuePrompt = async function () {
            const result = await originalQueuePrompt.apply(this, arguments);
            // app.queuePrompt returns only after it has serialized and sent the
            // complete requested batch, so queued jobs keep their original values.
            resetAfterQueueSubmission();
            return result;
        };
    },
});
