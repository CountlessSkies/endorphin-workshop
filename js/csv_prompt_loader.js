import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

function advanceRow(node) {
    if (node.comfyClass !== "EndorphinCSVLoader") return;
    if (!node.widgets?.find((widget) => widget.name === "auto_increment")?.value) return;
    const rowWidget = node.widgets?.find((widget) => widget.name === "row");
    if (!rowWidget) return;
    rowWidget.value += 1;
    rowWidget.callback?.(rowWidget.value);
    node.graph?.setDirtyCanvas(true, true);
}

function captureRowsBeforeQueue() {
    const rows = new Map();
    for (const node of app.graph?._nodes ?? []) {
        if (node.comfyClass !== "EndorphinCSVLoader") continue;
        const rowWidget = node.widgets?.find((widget) => widget.name === "row");
        if (!rowWidget) continue;
        rows.set(node.id, rowWidget.value);
    }
    return rows;
}

function restoreRowsAfterQueueSubmission(rowsBeforeQueue) {
    for (const [nodeId, row] of rowsBeforeQueue) {
        const node = app.graph?.getNodeById(nodeId);
        const rowWidget = node?.widgets?.find((widget) => widget.name === "row");
        if (!rowWidget) continue;
        rowWidget.value = row;
        rowWidget.callback?.(row);
        node.graph?.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "endorphin.CSVLoader",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "EndorphinCSVLoader") return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);
            this.addWidget("button", "browse_csv", "Browse CSV", async () => {
                const fileInput = document.createElement("input");
                fileInput.type = "file";
                fileInput.accept = ".csv,.tsv,text/csv,text/tab-separated-values";
                fileInput.onchange = async () => {
                    const file = fileInput.files?.[0];
                    if (!file) return;
                    const formData = new FormData();
                    formData.append("csv", file);
                    try {
                        const response = await api.fetchApi("/endorphin/csv/upload", {
                            method: "POST",
                            body: formData,
                        });
                        const data = await response.json();
                        if (!response.ok) throw new Error(data.error || "CSV upload failed.");

                        const pathWidget = this.widgets?.find((widget) => widget.name === "csv_path");
                        if (!pathWidget) throw new Error("CSV path widget was not found.");
                        pathWidget.value = data.csv_path;
                        pathWidget.callback?.(data.csv_path);
                        this.graph?.setDirtyCanvas(true, true);
                    } catch (error) {
                        alert(`Could not load CSV: ${error.message}`);
                    }
                };
                fileInput.click();
            });
            return result;
        };
    },
    setup() {
        const originalGraphToPrompt = app.graphToPrompt;
        app.graphToPrompt = async function () {
            const prompt = await originalGraphToPrompt.apply(this, arguments);
            for (const node of app.graph?._nodes ?? []) advanceRow(node);
            return prompt;
        };

        const originalQueuePrompt = app.queuePrompt;
        app.queuePrompt = async function () {
            const rowsBeforeQueue = captureRowsBeforeQueue();
            const result = await originalQueuePrompt.apply(this, arguments);
            // Queue Prompt has now serialized and submitted every requested
            // batch item, so future queues resume at the original CSV row.
            restoreRowsAfterQueueSubmission(rowsBeforeQueue);
            return result;
        };
    },
});
