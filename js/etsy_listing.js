import { app } from "../../../scripts/app.js";

function installPalette(node, prefix, itemLabel) {
    const all = [...node.widgets];
    const count = all.find(w => w.name === `${prefix}_count`);
    const index = all.find(w => w.name === `${prefix}_index`);
    if (!count || !index) return;

    const fieldName = slot => `${prefix}_${String(slot).padStart(2, "0")}`;
    const fieldPattern = new RegExp(`^${prefix}_\\d\\d$`);
    let root;
    node.addDOMWidget(`${prefix}_palette`, "custom", root = document.createElement("div"), {
        serialize: false,
        getMinHeight: () => Number(count.value) * 42 + 42,
    });
    root.style.cssText = "box-sizing:border-box;width:100%;min-width:0;padding:5px;display:grid;grid-template-columns:minmax(0,1fr);gap:5px;background:#202020;";
    const resize = () => {
        const size = node.computeSize();
        node.setSize([Math.max(330, size[0]), size[1]]);
        node.graph?.setDirtyCanvas(true, true);
    };
    const setWidgetValue = (widget, value) => {
        if (!widget) return;
        widget.value = value;
        widget.callback?.(value);
    };
    const render = () => {
        root.replaceChildren();
        const n = Number(count.value);
        for (let i = 1; i <= n; i++) {
            const field = all.find(w => w.name === fieldName(i));
            const selected = i === Number(index.value);
            const card = document.createElement("div");
            card.style.cssText = `min-width:0;height:34px;box-sizing:border-box;border:1px solid ${selected ? "#8ed0ff" : "#666"};background:${selected ? "#29526f" : "#303030"};padding:4px;display:flex;gap:4px;align-items:center;cursor:pointer;`;
            const select = document.createElement("button");
            select.type = "button";
            select.textContent = selected ? `● ${i}. Selected` : `○ ${i}. Select`;
            select.style.cssText = "min-width:0;flex:1;height:24px;text-align:left;background:transparent;color:#bde3ff;border:0;cursor:pointer;padding:0;";
            select.onclick = event => { event.stopPropagation(); setWidgetValue(index, i); render(); };
            const name = document.createElement("input");
            name.value = field?.value || "";
            name.placeholder = `${itemLabel.toLowerCase()} name`;
            name.style.cssText = "box-sizing:border-box;min-width:0;flex:0 0 120px;background:#171717;color:#eee;border:1px solid #666;padding:3px;";
            name.onchange = () => setWidgetValue(field, name.value.trim());
            name.addEventListener("pointerdown", event => event.stopPropagation());
            const remove = document.createElement("button");
            remove.textContent = "×";
            remove.title = `Remove ${itemLabel.toLowerCase()}`;
            remove.style.cssText = "width:20px;height:22px;padding:0;background:#343434;color:#ddd;border:1px solid #666;border-radius:2px;cursor:pointer;font:14px sans-serif;";
            remove.onclick = event => {
                event.stopPropagation();
                if (n <= 1) return;
                for (let slot = i; slot < n; slot++) {
                    const current = all.find(w => w.name === fieldName(slot));
                    const next = all.find(w => w.name === fieldName(slot + 1));
                    setWidgetValue(current, next?.value || "");
                }
                setWidgetValue(all.find(w => w.name === fieldName(n)), "");
                setWidgetValue(count, n - 1);
                if (Number(index.value) > n - 1) setWidgetValue(index, n - 1);
                render();
                resize();
            };
            card.onclick = () => { setWidgetValue(index, i); render(); };
            card.append(select, name, remove);
            root.append(card);
        }
        const add = document.createElement("button");
        add.textContent = `+ Add ${itemLabel}`;
        add.style.cssText = "height:30px;grid-column:1 / -1;";
        add.onclick = () => {
            setWidgetValue(count, Math.min(20, Number(count.value) + 1));
            render();
            resize();
        };
        root.append(add);
    };

    node.widgets = node.widgets.filter(w => !fieldPattern.test(w.name));
    for (const widget of all.filter(w => fieldPattern.test(w.name))) {
        const callback = widget.callback;
        widget.callback = function(value) { const result = callback?.apply(this, arguments); render(); return result; };
    }
    for (const widget of [count, index]) {
        const callback = widget.callback;
        widget.callback = function(value) { const result = callback?.apply(this, arguments); render(); resize(); return result; };
    }
    render();
    requestAnimationFrame(resize);
}

const paletteNodes = {
    EndorphinEtsyListingImageLoader: ["asset_folder", "Folder"],
    EndorphinEtsyListingSaveImage: ["asset_folder", "Folder"],
    EndorphinEtsyListingSelector: ["design_phase", "Phase"],
};

app.registerExtension({ name: "endorphin.EtsyListing", async beforeRegisterNodeDef(nodeType, nodeData) {
    const config = paletteNodes[nodeData.name];
    if (!config) return;
    const created = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
        const result = created?.apply(this, arguments);
        installPalette(this, config[0], config[1]);
        return result;
    };
}});
