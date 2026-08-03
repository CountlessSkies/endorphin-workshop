import { app } from "../../../scripts/app.js";

function getWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function setWidgetValue(widget, value) {
    widget.value = value;
    widget.callback?.(value);
}

function advanceCounter(node) {
    if (node.comfyClass !== "EndorphinCartesianProduct") return;
    if (!getWidget(node, "auto_increment")?.value) return;

    const dimensions = getWidget(node, "dimensions")?.value;
    const min1 = getWidget(node, "min_value_1")?.value;
    const max1 = getWidget(node, "max_value_1")?.value;
    const min2 = getWidget(node, "min_value_2")?.value;
    const max2 = getWidget(node, "max_value_2")?.value;
    const min3 = getWidget(node, "min_value_3")?.value;
    const max3 = getWidget(node, "max_value_3")?.value;
    const value1 = getWidget(node, "value_1");
    const value2 = getWidget(node, "value_2");
    const value3 = getWidget(node, "value_3");
    if ([min1, max1, min2, max2, min3, max3, value1, value2, value3].some((value) => value === undefined)) return;
    if (min1 > max1 || min2 > max2 || min3 > max3) return;

    if (dimensions === "3D (triples)") {
        let next3 = value3.value + 1;
        let next2 = value2.value;
        let next1 = value1.value;
        if (next3 > max3) {
            next3 = min3;
            next2 += 1;
            if (next2 > max2) {
                next2 = min2;
                next1 = next1 >= max1 ? min1 : next1 + 1;
            }
        }
        setWidgetValue(value1, next1);
        setWidgetValue(value2, next2);
        setWidgetValue(value3, next3);
    } else {
        let next2 = value2.value + 1;
        let next1 = value1.value;
        if (next2 > max2) {
            next2 = min2;
            next1 = next1 >= max1 ? min1 : next1 + 1;
        }
        setWidgetValue(value1, next1);
        setWidgetValue(value2, next2);
    }
    node.graph?.setDirtyCanvas(true, true);
}

function captureValuesBeforeQueue() {
    const values = new Map();
    for (const node of app.graph?._nodes ?? []) {
        if (node.comfyClass !== "EndorphinCartesianProduct") continue;
        const value1 = getWidget(node, "value_1");
        const value2 = getWidget(node, "value_2");
        const value3 = getWidget(node, "value_3");
        if (!value1 || !value2 || !value3) continue;
        values.set(node.id, [value1.value, value2.value, value3.value]);
    }
    return values;
}

function restoreValuesAfterQueueSubmission(valuesBeforeQueue) {
    for (const [nodeId, values] of valuesBeforeQueue) {
        const node = app.graph?.getNodeById(nodeId);
        if (!node) continue;
        const value1 = getWidget(node, "value_1");
        const value2 = getWidget(node, "value_2");
        const value3 = getWidget(node, "value_3");
        if (!value1 || !value2 || !value3) continue;
        setWidgetValue(value1, values[0]);
        setWidgetValue(value2, values[1]);
        setWidgetValue(value3, values[2]);
        node.graph?.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "endorphin.CartesianProduct",
    setup() {
        const originalGraphToPrompt = app.graphToPrompt;
        app.graphToPrompt = async function () {
            const prompt = await originalGraphToPrompt.apply(this, arguments);
            // Queue Prompt calls graphToPrompt once per batch item. Advance only
            // after the current values have been serialized into that prompt.
            for (const node of app.graph?._nodes ?? []) advanceCounter(node);
            return prompt;
        };

        const originalQueuePrompt = app.queuePrompt;
        app.queuePrompt = async function () {
            const valuesBeforeQueue = captureValuesBeforeQueue();
            const result = await originalQueuePrompt.apply(this, arguments);
            restoreValuesAfterQueueSubmission(valuesBeforeQueue);
            return result;
        };
    },
});
