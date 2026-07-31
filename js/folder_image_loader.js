import { app } from "../../../scripts/app.js";

function getWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function advanceImageIndex(node) {
    if (node.comfyClass !== "EndorphinFolderImageLoader") return;
    if (!getWidget(node, "auto_increment")?.value) return;
    const indexWidget = getWidget(node, "image_index");
    if (!indexWidget) return;
    indexWidget.value += 1;
    indexWidget.callback?.(indexWidget.value);
    node.graph?.setDirtyCanvas(true, true);
}

function captureIndexesBeforeQueue() {
    const indexes = new Map();
    for (const node of app.graph?._nodes ?? []) {
        if (node.comfyClass !== "EndorphinFolderImageLoader") continue;
        const indexWidget = getWidget(node, "image_index");
        if (indexWidget) indexes.set(node.id, indexWidget.value);
    }
    return indexes;
}

function restoreIndexesAfterQueueSubmission(indexesBeforeQueue) {
    for (const [nodeId, imageIndex] of indexesBeforeQueue) {
        const node = app.graph?.getNodeById(nodeId);
        const indexWidget = node && getWidget(node, "image_index");
        if (!indexWidget) continue;
        indexWidget.value = imageIndex;
        indexWidget.callback?.(imageIndex);
        node.graph?.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "endorphin.FolderImageLoader",
    setup() {
        const originalGraphToPrompt = app.graphToPrompt;
        app.graphToPrompt = async function () {
            const prompt = await originalGraphToPrompt.apply(this, arguments);
            for (const node of app.graph?._nodes ?? []) advanceImageIndex(node);
            return prompt;
        };

        const originalQueuePrompt = app.queuePrompt;
        app.queuePrompt = async function () {
            const indexesBeforeQueue = captureIndexesBeforeQueue();
            const result = await originalQueuePrompt.apply(this, arguments);
            restoreIndexesAfterQueueSubmission(indexesBeforeQueue);
            return result;
        };
    },
});
