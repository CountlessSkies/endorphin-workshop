import { app } from "../../../scripts/app.js";

const NODE_CLASS = "EndorphinArtworkFolderLoader";

function getWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function advanceFolderIndex(node) {
    if (node.comfyClass !== NODE_CLASS || !getWidget(node, "auto_increment")?.value) return;
    const index = getWidget(node, "folder_index");
    if (!index) return;
    index.value += 1;
    index.callback?.(index.value);
    node.graph?.setDirtyCanvas(true, true);
}

function captureIndexesBeforeQueue() {
    const indexes = new Map();
    for (const node of app.graph?._nodes ?? []) {
        if (node.comfyClass !== NODE_CLASS) continue;
        const index = getWidget(node, "folder_index");
        if (index) indexes.set(node.id, index.value);
    }
    return indexes;
}

function restoreIndexesAfterQueueSubmission(indexesBeforeQueue) {
    for (const [nodeId, folderIndex] of indexesBeforeQueue) {
        const node = app.graph?.getNodeById(nodeId);
        const index = node && getWidget(node, "folder_index");
        if (!index) continue;
        index.value = folderIndex;
        index.callback?.(folderIndex);
        node.graph?.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "endorphin.ArtworkFolderLoader",
    setup() {
        const originalGraphToPrompt = app.graphToPrompt;
        app.graphToPrompt = async function () {
            const prompt = await originalGraphToPrompt.apply(this, arguments);
            for (const node of app.graph?._nodes ?? []) advanceFolderIndex(node);
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
