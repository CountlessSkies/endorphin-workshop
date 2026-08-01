import { app } from "../../../scripts/app.js";

const MAX_SLOTS = 100;

function widget(node, name) {
    return node.widgets?.find((item) => item.name === name);
}

function resize(node) {
    node.setSize(node.computeSize());
    node.graph?.setDirtyCanvas(true, true);
}

function setCount(node, name, value) {
    const control = widget(node, name);
    if (!control) return;
    control.value = Math.max(1, Math.min(MAX_SLOTS, value));
    control.callback?.(control.value);
}

function syncTextOutputs(node, count) {
    while (node.outputs.length > count) node.removeOutput(node.outputs.length - 1);
    while (node.outputs.length < count) {
        const index = node.outputs.length + 1;
        node.addOutput(`line_${String(index).padStart(2, "0")}`, "STRING");
    }
    resize(node);
}

function syncSwitchInputs(node, count) {
    const cases = node.inputs?.filter((input) => input.name?.startsWith("case_")) ?? [];
    while (cases.length > count) {
        const input = cases.pop();
        node.removeInput(node.inputs.indexOf(input));
    }
    while (cases.length < count) {
        const index = cases.length + 1;
        node.addInput(`case_${String(index).padStart(2, "0")}`, "*");
        cases.push(node.inputs.at(-1));
    }
    resize(node);
}

function configure(node, countName, sync) {
    const control = widget(node, countName);
    if (!control || control._endorphinDynamicSlots) return;
    control._endorphinDynamicSlots = true;
    const original = control.callback;
    control.callback = function (value) {
        const result = original?.apply(this, arguments);
        sync(node, Number(value));
        return result;
    };
    requestAnimationFrame(() => sync(node, Number(control.value)));
}

function enlargeTextField(node) {
    const text = widget(node, "text");
    if (!text?.element || text._endorphinLargeTextField) return;
    text._endorphinLargeTextField = true;
    text.element.rows = 20;
    text.element.style.minHeight = "360px";
    text.options.getMinHeight = () => 360;
    requestAnimationFrame(() => resize(node));
}

app.registerExtension({
    name: "endorphin.DynamicSlots",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        const isText = nodeData.name === "EndorphinTextLines20";
        const isSwitch = nodeData.name === "EndorphinSwitchCase20";
        if (!isText && !isSwitch) return;
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);
            if (isText) {
                configure(this, "output_count", syncTextOutputs);
                enlargeTextField(this);
                this.addWidget("button", "add_output", "+ Add Output", () => setCount(this, "output_count", Number(widget(this, "output_count")?.value) + 1));
            } else {
                configure(this, "input_count", syncSwitchInputs);
                this.addWidget("button", "add_input", "+ Add Input", () => setCount(this, "input_count", Number(widget(this, "input_count")?.value) + 1));
            }
            return result;
        };
        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = originalOnConfigure?.apply(this, arguments);
            requestAnimationFrame(() => {
                configure(this, isText ? "output_count" : "input_count", isText ? syncTextOutputs : syncSwitchInputs);
                if (isText) enlargeTextField(this);
            });
            return result;
        };
    },
});
