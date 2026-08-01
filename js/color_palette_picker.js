import { app } from "../../../scripts/app.js";

const DEFAULT_PALETTE = {
    selected: 0,
    colors: [
        { name: "Red", hex: "#EF4444", value: 1 },
        { name: "Green", hex: "#22C55E", value: 2 },
        { name: "Blue", hex: "#3B82F6", value: 3 },
    ],
};
const MIN_NODE_WIDTH = 365;

function normalizeHex(value) {
    return /^#[0-9a-f]{6}$/i.test(value) ? value.toUpperCase() : "#808080";
}

function parsePalette(value) {
    try {
        const data = typeof value === "string" ? JSON.parse(value) : value;
        const colors = Array.isArray(data?.colors) ? data.colors : [];
        const normalized = colors.map((color, index) => ({
            name: String(color?.name || `Color ${index + 1}`),
            hex: normalizeHex(String(color?.hex || "")),
            value: Number.isInteger(Number(color?.value)) ? Number(color.value) : index + 1,
        }));
        return {
            selected: Math.max(0, Math.min(Number(data?.selected) || 0, Math.max(0, normalized.length - 1))),
            colors: normalized.length ? normalized : structuredClone(DEFAULT_PALETTE.colors),
        };
    } catch {
        return structuredClone(DEFAULT_PALETTE);
    }
}

function parsePaletteList(text) {
    const colors = [];
    const errors = [];
    for (const [index, rawLine] of text.split(/\r?\n/).entries()) {
        const line = rawLine.trim();
        if (!line) continue;
        const match = line.match(/^(.+?)\s*\(\s*hex\s*(#[0-9a-f]{6})\s*\)\s*(?:[=:]\s*(-?\d+))?\s*$/i);
        if (!match) errors.push(index + 1);
        else colors.push({ name: match[1].trim(), hex: match[2].toUpperCase(), value: match[3] === undefined ? colors.length + 1 : Number(match[3]) });
    }
    return { colors, errors };
}

function createPaletteWidget(node, inputName, inputData) {
    let palette = parsePalette(inputData?.[1]?.default);
    let showImporter = false;
    const root = document.createElement("div");
    root.style.cssText = "box-sizing:border-box;width:100%;padding:6px;background:#202020;color:#ddd;font:12px sans-serif;";
    root.addEventListener("pointerdown", (event) => event.stopPropagation());

    const widget = node.addDOMWidget(inputName, "ENDORPHIN_COLOR_PALETTE", root, {
        getValue: () => JSON.stringify(palette),
        setValue: (value) => {
            palette = parsePalette(value);
            render();
            requestAnimationFrame(resize);
        },
        getMinHeight: () => palette.colors.length * 34 + (showImporter ? 210 : 72),
        getMinWidth: () => 290,
    });

    function resize() {
        const computedSize = node.computeSize();
        node.setSize([
            Math.max(MIN_NODE_WIDTH, node.size[0], computedSize[0]),
            computedSize[1],
        ]);
        node.graph?.setDirtyCanvas(true, true);
    }

    function commit() {
        widget.value = JSON.stringify(palette);
        resize();
    }

    function button(text) {
        const element = document.createElement("button");
        element.textContent = text;
        element.style.cssText = "border:1px solid #566;background:#303030;color:#bde3ff;border-radius:3px;padding:4px 7px;cursor:pointer;font:12px sans-serif;";
        return element;
    }

    function render() {
        root.replaceChildren();
        palette.colors.forEach((color, index) => {
            const row = document.createElement("div");
            row.style.cssText = `display:grid;grid-template-columns:46px minmax(62px,1fr) 76px 44px 24px;gap:5px;align-items:center;height:31px;margin-bottom:4px;padding:2px;border:1px solid ${index === palette.selected ? "#8ed0ff" : "#555"};background:${index === palette.selected ? "#294b67" : "#292929"};`;
            const preview = document.createElement("button");
            preview.type = "button";
            preview.title = "Select this color. Edit the HEX field to change its color.";
            preview.style.cssText = `width:44px;height:25px;padding:0;border:1px solid #aaa;border-radius:2px;background:${color.hex};cursor:pointer;`;
            preview.onclick = (event) => {
                event.stopPropagation();
                palette.selected = index;
                commit();
            };
            const name = document.createElement("input");
            name.value = color.name;
            name.placeholder = "Color name";
            const hex = document.createElement("input");
            hex.value = color.hex;
            hex.placeholder = "#RRGGBB";
            const int = document.createElement("input");
            int.type = "number";
            int.step = "1";
            int.value = String(color.value);
            [name, hex, int].forEach((input) => {
                input.style.cssText = "min-width:0;box-sizing:border-box;width:100%;border:1px solid #666;border-radius:2px;padding:3px;background:#171717;color:#eee;font:12px sans-serif;";
                input.addEventListener("pointerdown", (event) => event.stopPropagation());
            });
            name.onchange = () => { color.name = name.value.trim() || color.name; commit(); };
            hex.onchange = () => {
                if (/^#[0-9a-f]{6}$/i.test(hex.value.trim())) { color.hex = hex.value.trim().toUpperCase(); preview.style.background = color.hex; commit(); }
                else hex.value = color.hex;
            };
            int.onchange = () => {
                if (Number.isInteger(Number(int.value))) { color.value = Number(int.value); commit(); }
                else int.value = String(color.value);
            };
            const remove = button("×");
            remove.title = "Remove color";
            remove.style.padding = "3px";
            remove.onclick = () => {
                if (palette.colors.length === 1) return;
                palette.colors.splice(index, 1);
                palette.selected = Math.min(palette.selected, palette.colors.length - 1);
                commit();
            };
            row.onclick = () => { palette.selected = index; commit(); };
            row.append(preview, name, hex, int, remove);
            root.appendChild(row);
        });
        const actions = document.createElement("div");
        actions.style.cssText = "display:flex;gap:6px;margin-top:5px;";
        const add = button("+ Add Color");
        add.onclick = () => {
            const value = Math.max(0, ...palette.colors.map((color) => color.value)) + 1;
            palette.colors.push({ name: `Color ${palette.colors.length + 1}`, hex: "#808080", value });
            palette.selected = palette.colors.length - 1;
            commit();
        };
        const paste = button("⇩ Paste List");
        paste.onclick = () => {
            showImporter = !showImporter;
            render();
            resize();
        };
        actions.append(add, paste);
        root.appendChild(actions);

        if (showImporter) {
            const hint = document.createElement("div");
            hint.textContent = "One per line: name (hex #RRGGBB). Optional: = integer";
            hint.style.cssText = "margin:8px 0 4px;color:#b9c7d5;";
            const textarea = document.createElement("textarea");
            textarea.placeholder = "mocha taupe (hex #977D67)\nsoft white (hex #D9DADE)\nblack navy (hex #272A37) = 10";
            textarea.style.cssText = "box-sizing:border-box;width:100%;height:120px;resize:vertical;border:1px solid #666;border-radius:3px;padding:5px;background:#171717;color:#eee;font:12px monospace;";
            textarea.addEventListener("pointerdown", (event) => event.stopPropagation());
            const error = document.createElement("div");
            error.style.cssText = "min-height:16px;margin-top:3px;color:#fca5a5;";
            const importActions = document.createElement("div");
            importActions.style.cssText = "display:flex;gap:6px;margin-top:4px;";
            const importButton = button("Import");
            const cancelButton = button("Cancel");
            importButton.onclick = () => {
                const { colors, errors } = parsePaletteList(textarea.value);
                if (errors.length || !colors.length) {
                    error.textContent = errors.length ? `Invalid line: ${errors.join(", ")}.` : "Paste at least one valid color.";
                    return;
                }
                palette = { selected: 0, colors };
                showImporter = false;
                commit();
            };
            cancelButton.onclick = () => { showImporter = false; render(); resize(); };
            importActions.append(importButton, cancelButton);
            root.append(hint, textarea, error, importActions);
        }
    }

    render();
    // DOM widgets calculate their layout after insertion. Resize on the next
    // frame so a freshly created or restored node cannot be narrower than its
    // row controls.
    requestAnimationFrame(resize);
    return { widget, minWidth: 290, minHeight: 174 };
}

app.registerExtension({
    name: "endorphin.ColorPalettePicker",
    getCustomWidgets() {
        return {
            ENDORPHIN_COLOR_PALETTE: createPaletteWidget,
        };
    },
});
