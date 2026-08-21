import { app } from "../../../scripts/app.js";

const DEFAULT_PALETTE = {
    selected: 0,
    colors: [
        { name: "Red", hex: "#EF4444", code: "RED", value: 1 },
        { name: "Green", hex: "#22C55E", code: "GRN", value: 2 },
        { name: "Blue", hex: "#3B82F6", code: "BLU", value: 3 },
    ],
};
const MIN_NODE_WIDTH = 540;

function normalizeHex(value) {
    return /^#[0-9a-f]{6}$/i.test(value) ? value.toUpperCase() : "#808080";
}

function suggestColorCode(name) {
    const words = String(name || "").toUpperCase().match(/[A-Z]+/g) || [];
    if (!words.length) return "CLR";
    if (words.length >= 3) return words.slice(0, 3).map((word) => word[0]).join("");
    if (words.length === 2) {
        const consonants = words[1].replace(/[AEIOU]/g, "");
        if (consonants.length >= 2) return `${words[0][0]}${consonants.slice(0, 2)}`;
        return `${words[0][0]}${words[1].slice(0, 2)}`.padEnd(3, words[0][0]);
    }
    const consonants = words[0].replace(/[AEIOU]/g, "");
    if (consonants.length >= 3) return consonants.slice(0, 3);
    return words[0].slice(0, 3).padEnd(3, "X");
}

function parsePalette(value) {
    try {
        const data = typeof value === "string" ? JSON.parse(value) : value;
        const colors = Array.isArray(data?.colors) ? data.colors : [];
        const normalized = colors.map((color, index) => ({
            name: String(color?.name || `Color ${index + 1}`),
            hex: normalizeHex(String(color?.hex || "")),
            code: /^[A-Z]{3}$/.test(String(color?.code || "").toUpperCase()) ? String(color.code).toUpperCase() : suggestColorCode(color?.name),
            code_auto: typeof color?.code_auto === "boolean" ? color.code_auto : !color?.code,
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
        else {
            const name = match[1].trim();
            colors.push({ name, hex: match[2].toUpperCase(), code: suggestColorCode(name), code_auto: true, value: match[3] === undefined ? colors.length + 1 : Number(match[3]) });
        }
    }
    return { colors, errors };
}

function createPaletteWidget(node, inputName, inputData, showCode = false) {
    const minNodeWidth = showCode ? MIN_NODE_WIDTH : 470;
    let palette = parsePalette(inputData?.[1]?.default);
    let showImporter = false;
    const root = document.createElement("div");
    root.style.cssText = "box-sizing:border-box;width:100%;padding:7px;background:#202020;color:#ddd;font:12px sans-serif;";
    root.addEventListener("pointerdown", (event) => event.stopPropagation());

    const widget = node.addDOMWidget(inputName, "ENDORPHIN_COLOR_PALETTE", root, {
        getValue: () => JSON.stringify(palette),
        setValue: (value) => {
            palette = parsePalette(value);
            render();
            requestAnimationFrame(resize);
        },
        getMinHeight: () => palette.colors.length * 34 + (showImporter ? 210 : 72),
        getMinWidth: () => minNodeWidth,
    });

    function resize() {
        const computedSize = node.computeSize();
        node.setSize([
            Math.max(minNodeWidth, node.size[0], computedSize[0]),
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
        element.style.cssText = "border:1px solid #666;background:#303030;color:#d9f0ff;border-radius:3px;padding:4px 7px;cursor:pointer;font:12px sans-serif;";
        return element;
    }

    function render() {
        root.replaceChildren();
        palette.colors.forEach((color, index) => {
            const row = document.createElement("div");
            const columns = showCode
                ? "48px minmax(100px,1fr) 90px 48px 42px 26px 26px 26px"
                : "48px minmax(110px,1fr) 90px 48px 26px 26px 26px";
            row.style.cssText = `display:grid;grid-template-columns:${columns};gap:5px;align-items:center;height:32px;margin-bottom:5px;padding:3px;border:1px solid ${index === palette.selected ? "#8ed0ff" : "#666"};border-radius:3px;background:${index === palette.selected ? "#29526f" : "#303030"};`;
            const preview = document.createElement("button");
            preview.type = "button";
            preview.title = "Select this color. Edit the HEX field to change its color.";
            preview.style.cssText = `width:44px;height:25px;padding:0;border:1px solid #aaa;border-radius:3px;background:${color.hex};cursor:pointer;`;
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
            const code = document.createElement("input");
            code.value = color.code;
            code.placeholder = "MTP";
            code.title = "Stable three-letter color code used by the image pipeline.";
            const int = document.createElement("input");
            int.type = "number";
            int.step = "1";
            int.value = String(color.value);
            [name, hex, code, int].forEach((input) => {
                input.style.cssText = "min-width:0;box-sizing:border-box;width:100%;border:1px solid #666;border-radius:2px;padding:3px;background:#171717;color:#eee;font:12px sans-serif;";
                // LiteGraph's canvas normally consumes these events. Stop all
                // of them on editable controls so typing works reliably.
                for (const eventName of ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "keydown", "keyup", "keypress"]) {
                    input.addEventListener(eventName, (event) => event.stopPropagation());
                }
            });
            name.onchange = () => {
                color.name = name.value.trim() || color.name;
                if (color.code_auto) {
                    color.code = suggestColorCode(color.name);
                    code.value = color.code;
                }
                commit();
            };
            name.onblur = name.onchange;
            hex.onchange = () => {
                if (/^#[0-9a-f]{6}$/i.test(hex.value.trim())) { color.hex = hex.value.trim().toUpperCase(); preview.style.background = color.hex; commit(); }
                else hex.value = color.hex;
            };
            hex.onblur = hex.onchange;
            code.onchange = () => {
                const normalized = code.value.trim().toUpperCase();
                if (/^[A-Z]{3}$/.test(normalized)) { color.code = normalized; color.code_auto = false; code.value = normalized; commit(); }
                else code.value = color.code;
            };
            code.onblur = code.onchange;
            int.onchange = () => {
                if (Number.isInteger(Number(int.value))) { color.value = Number(int.value); commit(); }
                else int.value = String(color.value);
            };
            int.onblur = int.onchange;
            const moveUp = button("↑");
            moveUp.title = "Move color up";
            moveUp.style.padding = "3px";
            moveUp.disabled = index === 0;
            moveUp.onclick = () => {
                if (index === 0) return;
                [palette.colors[index - 1], palette.colors[index]] = [palette.colors[index], palette.colors[index - 1]];
                palette.selected = index - 1;
                render();
                commit();
            };
            const moveDown = button("↓");
            moveDown.title = "Move color down";
            moveDown.style.padding = "3px";
            moveDown.disabled = index === palette.colors.length - 1;
            moveDown.onclick = () => {
                if (index === palette.colors.length - 1) return;
                [palette.colors[index], palette.colors[index + 1]] = [palette.colors[index + 1], palette.colors[index]];
                palette.selected = index + 1;
                render();
                commit();
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
            row.append(preview, name, hex);
            if (showCode) row.append(code);
            row.append(int, moveUp, moveDown, remove);
            root.appendChild(row);
        });
        const actions = document.createElement("div");
        actions.style.cssText = "display:flex;gap:6px;margin-top:5px;";
        const add = button("+ Add Color");
        add.onclick = () => {
            const value = Math.max(0, ...palette.colors.map((color) => color.value)) + 1;
            const name = `Color ${palette.colors.length + 1}`;
            palette.colors.push({ name, hex: "#808080", code: suggestColorCode(name), code_auto: true, value });
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
    return { widget, minWidth: minNodeWidth, minHeight: 174 };
}

app.registerExtension({
    name: "endorphin.ColorPalettePicker",
    getCustomWidgets() {
        return {
            ENDORPHIN_COLOR_PALETTE: (node, inputName, inputData) => createPaletteWidget(node, inputName, inputData, false),
            ENDORPHIN_ETSY_COLOR_PALETTE: (node, inputName, inputData) => createPaletteWidget(node, inputName, inputData, true),
        };
    },
});
