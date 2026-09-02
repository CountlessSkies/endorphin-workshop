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

function addFolderPreview(node) {
    let requestId = 0;
    let previewHeight = 58;
    const root = document.createElement("div");
    root.style.cssText = "box-sizing:border-box;width:100%;padding:7px;background:#202020;color:#ddd;font:12px sans-serif;";
    root.addEventListener("pointerdown", (event) => event.stopPropagation());
    const previewWidget = node.addDOMWidget("folder_preview", "custom", root, {
        serialize: false,
        getMinHeight: () => previewHeight,
        getMinWidth: () => 300,
    });

    function resize() {
        const size = node.computeSize();
        node.setSize([Math.max(300, node.size[0], size[0]), size[1]]);
        node.graph?.setDirtyCanvas(true, true);
    }

    function controls() {
        return {
            folder_path: String(getWidget(node, "folder_path")?.value || ""),
            subfolder: String(getWidget(node, "subfolder")?.value || ""),
            sort: String(getWidget(node, "sort")?.value || "Natural (1, 2, 10)"),
            image_index: String(getWidget(node, "image_index")?.value || 1),
            loop: String(Boolean(getWidget(node, "loop")?.value)),
        };
    }

    function showMessage(message) {
        root.replaceChildren();
        const label = document.createElement("div");
        label.textContent = message;
        label.style.cssText = "box-sizing:border-box;min-height:42px;padding:8px;display:flex;align-items:center;background:#171717;border:1px dashed #666;border-radius:3px;color:#aab8c5;font-size:11px;";
        root.append(label); previewHeight = 58; resize();
    }

    async function refreshPreview() {
        const current = ++requestId;
        const params = new URLSearchParams(controls());
        if (!params.get("folder_path")) { showMessage("Preview — enter a folder path."); return; }
        try {
            const response = await fetch(`/endorphin/folder-image-preview?${params}`);
            const info = await response.json();
            if (current !== requestId) return;
            if (!response.ok) { showMessage(`Preview unavailable — ${info.error || "could not resolve image"}`); return; }
            root.replaceChildren();
            const title = document.createElement("div");
            title.textContent = `Preview ${info.resolved_index}/${info.total} — ${info.file_name}`;
            title.style.cssText = "margin-bottom:5px;color:#bde3ff;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
            const image = document.createElement("img");
            const imageParams = new URLSearchParams({ ...controls(), render: "1", version: info.version });
            image.src = `/endorphin/folder-image-preview?${imageParams}`;
            image.alt = info.file_name;
            image.style.cssText = "display:block;box-sizing:border-box;width:100%;height:auto;background:#171717;border:1px solid #666;border-radius:3px;";
            image.onload = () => { if (current !== requestId) return; previewHeight = Math.max(90, image.offsetHeight + 32); resize(); };
            image.onerror = () => { if (current === requestId) showMessage("Preview unavailable — image could not be rendered."); };
            root.append(title, image); previewHeight = 220; resize();
        } catch (error) {
            if (current === requestId) showMessage(`Preview unavailable — ${error.message || "request failed"}`);
        }
    }

    for (const name of ["folder_path", "subfolder", "sort", "image_index", "loop"]) {
        const widget = getWidget(node, name);
        if (!widget) continue;
        const callback = widget.callback;
        widget.callback = function () { callback?.apply(this, arguments); refreshPreview(); };
    }
    const configured = node.onConfigure;
    node.onConfigure = function () { const result = configured?.apply(this, arguments); requestAnimationFrame(refreshPreview); return result; };
    requestAnimationFrame(refreshPreview);
    return previewWidget;
}

app.registerExtension({
    name: "endorphin.FolderImageLoader",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "EndorphinFolderImageLoader") return;
        const created = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = created?.apply(this, arguments);
            addFolderPreview(this);
            return result;
        };
    },
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
