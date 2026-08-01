import { app } from "../../../scripts/app.js";

function captureValuesBeforeQueue() {
    const values = new Map();
    for (const node of app.graph?._nodes ?? []) {
        if (node.comfyClass !== "EndorphinAutoResetInt") continue;
        const valueWidget = node.widgets?.find((widget) => widget.name === "value");
        if (valueWidget) values.set(node.id, valueWidget.value);
    }
    return values;
}

function advanceValue(node) {
    if (node.comfyClass !== "EndorphinAutoResetInt") return;
    if (!node.widgets?.find((widget) => widget.name === "auto_increment")?.value) return;
    const valueWidget = node.widgets?.find((widget) => widget.name === "value");
    if (!valueWidget) return;
    valueWidget.value += 1;
    valueWidget.callback?.(valueWidget.value);
    node.graph?.setDirtyCanvas(true, true);
}

function restoreValuesAfterQueueSubmission(valuesBeforeQueue) {
    for (const [nodeId, value] of valuesBeforeQueue) {
        const node = app.graph?.getNodeById(nodeId);
        const valueWidget = node?.widgets?.find((widget) => widget.name === "value");
        if (!valueWidget) continue;
        valueWidget.value = value;
        valueWidget.callback?.(value);
        node.graph?.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "endorphin.AutoResetInt",
    setup() {
        const originalGraphToPrompt = app.graphToPrompt;
        app.graphToPrompt = async function () {
            const prompt = await originalGraphToPrompt.apply(this, arguments);
            // Advance only after this batch item's original value has been
            // serialized into its prompt.
            for (const node of app.graph?._nodes ?? []) advanceValue(node);
            return prompt;
        };

        const originalQueuePrompt = app.queuePrompt;
        app.queuePrompt = async function () {
            const valuesBeforeQueue = captureValuesBeforeQueue();
            const result = await originalQueuePrompt.apply(this, arguments);
            // Queue Prompt has serialized and submitted every requested batch
            // item, so restore the editor state without waiting for generation.
            restoreValuesAfterQueueSubmission(valuesBeforeQueue);
            return result;
        };
    },
});
