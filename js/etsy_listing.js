import { app } from "../../../scripts/app.js";

function installPalette(node) {
    const all = [...node.widgets];
    const count = all.find(w => w.name === "asset_folder_count");
    const index = all.find(w => w.name === "asset_folder_index");
    if (!count || !index) return;
    let root;
    const palette = node.addDOMWidget("asset_folder_palette", "custom", root = document.createElement("div"), {
        serialize: false,
        getMinHeight: () => Number(count.value) * 42 + 42,
    });
    root.style.cssText = "box-sizing:border-box;width:100%;min-width:0;padding:5px;display:grid;grid-template-columns:minmax(0,1fr);gap:5px;background:#202020;";
    const resize = () => { const size = node.computeSize(); node.setSize([Math.max(330, size[0]), size[1]]); node.graph?.setDirtyCanvas(true, true); };
    const render = () => {
        root.replaceChildren();
        const n = Number(count.value);
        for (let i = 1; i <= n; i++) {
            const field = all.find(w => w.name === `asset_folder_${String(i).padStart(2,"0")}`);
            const card = document.createElement("div");
            card.style.cssText = `min-width:0;height:34px;box-sizing:border-box;border:1px solid ${i === Number(index.value) ? "#8ed0ff" : "#666"};background:${i === Number(index.value) ? "#29526f" : "#303030"};padding:4px;display:flex;gap:4px;align-items:center;cursor:pointer;`;
            const select = document.createElement("button");
            select.type = "button";
            select.textContent = i === Number(index.value) ? `● ${i}. Selected` : `○ ${i}. Select`;
            select.style.cssText = "min-width:0;flex:1;height:24px;text-align:left;background:transparent;color:#bde3ff;border:0;cursor:pointer;padding:0;";
            select.onclick = event => { event.stopPropagation(); index.value = i; index.callback?.(i); render(); };
            const name = document.createElement("input"); name.value = field?.value || ""; name.placeholder = "folder name";
            name.style.cssText = "box-sizing:border-box;min-width:0;flex:0 0 120px;background:#171717;color:#eee;border:1px solid #666;padding:3px;";
            name.onchange = () => { if (field) { field.value = name.value.trim(); field.callback?.(field.value); } };
            name.addEventListener("pointerdown", event => event.stopPropagation());
            const remove = document.createElement("button"); remove.textContent = "×"; remove.title = "Remove folder";
            remove.style.cssText = "width:20px;height:22px;padding:0;background:#343434;color:#ddd;border:1px solid #666;border-radius:2px;cursor:pointer;font:14px sans-serif;";
            remove.onclick = event => {
                event.stopPropagation();
                if (n <= 1) return;
                for (let slot = i; slot < n; slot++) {
                    const current = all.find(w => w.name === `asset_folder_${String(slot).padStart(2,"0")}`);
                    const next = all.find(w => w.name === `asset_folder_${String(slot + 1).padStart(2,"0")}`);
                    if (current) { current.value = next?.value || ""; current.callback?.(current.value); }
                }
                const last = all.find(w => w.name === `asset_folder_${String(n).padStart(2,"0")}`);
                if (last) { last.value = ""; last.callback?.(""); }
                count.value = n - 1; count.callback?.(count.value);
                if (Number(index.value) > Number(count.value)) { index.value = count.value; index.callback?.(index.value); }
            };
            card.onclick = () => { index.value = i; index.callback?.(i); render(); };
            card.append(select, name, remove);
            root.append(card);
        }
        const add = document.createElement("button"); add.textContent = "+ Add Folder"; add.style.cssText = "height:30px;grid-column:1 / -1;";
        add.onclick = () => { count.value = Math.min(20, Number(count.value) + 1); count.callback?.(count.value); render(); resize(); };
        root.append(add);
    };
    node.widgets = node.widgets.filter(w => !/^asset_folder_\d\d$/.test(w.name));
    for (const w of all.filter(w => /^asset_folder_\d\d$/.test(w.name))) {
        const cb = w.callback; w.callback = function(v) { const out = cb?.apply(this, arguments); render(); return out; };
    }
    for (const w of [count, index]) { const cb = w.callback; w.callback = function(v) { const out = cb?.apply(this, arguments); render(); resize(); return out; }; }
    render(); requestAnimationFrame(resize);
}

app.registerExtension({ name: "endorphin.EtsyListing", async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!["EndorphinEtsyListingImageLoader", "EndorphinEtsyListingSaveImage"].includes(nodeData.name)) return;
    const created = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() { const result = created?.apply(this, arguments); installPalette(this); return result; };
}});
