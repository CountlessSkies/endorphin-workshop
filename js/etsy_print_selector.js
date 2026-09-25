import { app } from "../../../scripts/app.js";

const COLORS = [
    ["White", "WHI", "#FFFFFF"], ["Black", "BLK", "#25282A"],
    ["Sport Grey", "SGR", "#97999B"], ["Dark Heather", "DKH", "#425563"],
    ["Navy", "NAV", "#263147"], ["Royal Blue", "RYB", "#224D8F"],
    ["Light Blue", "LTB", "#A4C8E1"], ["Light Pink", "LTP", "#E4C6D4"],
    ["Red", "RED", "#D50032"], ["Maroon", "MRN", "#5B2B42"],
    ["Forest Green", "FRG", "#273B33"], ["Military Green", "MLG", "#5E7461"],
    ["Sand", "SAN", "#CABFAD"], ["Natural", "NAT", "#E7CEB5"],
    ["Dark Chocolate", "DCC", "#382F2D"], ["Purple", "PPL", "#470A68"],
];
const MODELS = [["MAN", "Man"], ["WOM", "Woman"], ["BOY", "Boy"], ["GIRL", "Girl"]];
const OCCASIONS = ["Everyday", "Match Artwork", "Christmas", "Halloween", "Valentine", "Easter", "Custom"];
const EMPTY_PREVIEW_HEIGHT = 300;
const today = new Date();
const currentPeriod = `${String(today.getFullYear()).slice(-2)}${String(today.getMonth() + 1).padStart(2, "0")}`;
const DEFAULT = {
    root_folder: "G:\\My Drive\\_Etsy\\_Listing",
    workflow_type: "artwork", project_id: "", id_period: currentPeriod, model_code: "WOM", color_code: "BLK",
    print_size: "Standard", occasion: "Everyday", custom_occasion: "",
    color_hexes: Object.fromEntries(COLORS.map(([, code, hex]) => [code, hex])),
};
const inputStyle = "box-sizing:border-box;width:100%;min-width:0;height:28px;padding:4px 6px;border:1px solid #666;border-radius:3px;background:#171717;color:#eee;font:12px sans-serif;";

function parseProject(value) {
    try {
        const supplied = typeof value === "string" ? JSON.parse(value) : value;
        const hexes = Object.fromEntries(COLORS.map(([, code, hex]) => [code, /^#[0-9a-f]{6}$/i.test(supplied?.color_hexes?.[code]) ? supplied.color_hexes[code].toUpperCase() : hex]));
        const model = MODELS.some(([code]) => code === supplied?.model_code) ? supplied.model_code : DEFAULT.model_code;
        const period = /^\d{4}$/.test(String(supplied?.id_period || "")) ? supplied.id_period : DEFAULT.id_period;
        return { ...DEFAULT, ...supplied, model_code: model, id_period: period, color_hexes: hexes };
    } catch { return structuredClone(DEFAULT); }
}
function stopCanvasEvents(element) {
    for (const name of ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "keydown", "keyup", "keypress"])
        element.addEventListener(name, (event) => event.stopPropagation());
}
function label(value) {
    const element = document.createElement("div"); element.textContent = value;
    element.style.cssText = "margin:7px 0 3px;color:#b9c7d5;font-weight:600;";
    return element;
}
function button(value, action, active = false) {
    const element = document.createElement("button"); element.type = "button"; element.textContent = value;
    element.style.cssText = `height:28px;padding:3px 7px;border:1px solid ${active ? "#8ed0ff" : "#666"};border-radius:3px;background:${active ? "#29526f" : "#303030"};color:#d9f0ff;cursor:pointer;font:12px sans-serif;`;
    element.onclick = (event) => { event.stopPropagation(); action(); };
    return element;
}
function cards(options, current, action) {
    const row = document.createElement("div"); row.style.cssText = `display:grid;grid-template-columns:repeat(${options.length},minmax(0,1fr));gap:5px;`;
    for (const [value, title] of options) row.append(button(title, () => action(value), value === current));
    return row;
}

function createPrintSelector(node, name, inputData) {
    let project = parseProject(inputData?.[1]?.default), projects = [], loading = false, status = "", previewRevision = 0;
    const root = document.createElement("div"); root.style.cssText = "box-sizing:border-box;width:100%;padding:7px;background:#202020;color:#ddd;font:12px sans-serif;";
    root.addEventListener("pointerdown", (event) => event.stopPropagation());
    const widget = node.addDOMWidget(name, "ENDORPHIN_ETSY_PRINT_SELECTOR", root, {
        getValue: () => JSON.stringify(project),
        setValue: (value) => { project = parseProject(value); render(); resize(); },
        getMinHeight: () => Math.max(800, root.scrollHeight + 20),
        getMinWidth: () => 500,
    });
    function resize() { const size = node.computeSize(); node.setSize([Math.max(500, node.size[0], size[0]), Math.max(root.scrollHeight + 20, size[1])]); node.graph?.setDirtyCanvas(true, true); }
    function commit() { widget.value = JSON.stringify(project); node.graph?.setDirtyCanvas(true, true); requestAnimationFrame(resize); }
    function refreshPreview() { previewRevision += 1; render(); requestAnimationFrame(resize); }
    function stepProject(delta) {
        if (!projects.length) return;
        const current = projects.indexOf(project.project_id);
        const index = current < 0 ? (delta < 0 ? projects.length - 1 : 0) : Math.max(0, Math.min(projects.length - 1, current + delta));
        if (index === current) return;
        project.project_id = projects[index]; commit(); refreshPreview();
    }
    async function refreshProjects() {
        loading = true; status = "Scanning project folders…"; render();
        try {
            const response = await fetch(`/endorphin/etsy/projects?${new URLSearchParams({ root_folder: project.root_folder, workflow_type: project.workflow_type, period: project.id_period })}`, { cache: "no-store" });
            const data = await response.json(); if (!response.ok) throw new Error(data.error || "Could not scan projects.");
            projects = Array.isArray(data.projects) ? data.projects : [];
            if (project.project_id && !projects.includes(project.project_id)) { project.project_id = ""; commit(); }
            status = `${projects.length} ID${projects.length === 1 ? "" : "s"} in ${project.id_period}.`;
        } catch (error) { projects = []; status = error.message || "Could not scan projects."; }
        finally { loading = false; refreshPreview(); resize(); }
    }
    function render() {
        root.replaceChildren();
        root.append(label("Project root"));
        const path = document.createElement("input"); path.value = project.root_folder; path.style.cssText = inputStyle;
        path.onchange = () => { project.root_folder = path.value.trim() || DEFAULT.root_folder; project.project_id = ""; commit(); refreshProjects(); };
        stopCanvasEvents(path); root.append(path);

        root.append(label("Source"));
        root.append(cards([["artwork", "Artwork"], ["redesign", "Redesign reference"]], project.workflow_type, (value) => {
            project.workflow_type = value; project.project_id = ""; projects = []; commit(); refreshProjects();
        }));

        root.append(label("ID year / month"));
        const periodRow = document.createElement("div"); periodRow.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:5px;";
        const year = document.createElement("select"); year.style.cssText = inputStyle;
        const selectedYear = Number(`20${project.id_period.slice(0, 2)}`);
        const years = Array.from({ length: 9 }, (_, index) => today.getFullYear() - 4 + index);
        if (!years.includes(selectedYear)) years.push(selectedYear);
        for (const value of years.sort((a, b) => a - b)) { const option = document.createElement("option"); option.value = String(value).slice(-2); option.textContent = `Year ${value}`; year.append(option); }
        year.value = project.id_period.slice(0, 2); stopCanvasEvents(year);
        const month = document.createElement("select"); month.style.cssText = inputStyle;
        for (let value = 1; value <= 12; value += 1) { const option = document.createElement("option"); option.value = String(value).padStart(2, "0"); option.textContent = `Month ${option.value}`; month.append(option); }
        month.value = project.id_period.slice(2, 4); stopCanvasEvents(month);
        const updatePeriod = () => { project.id_period = `${year.value}${month.value}`; project.project_id = ""; projects = []; commit(); refreshProjects(); };
        year.onchange = updatePeriod; month.onchange = updatePeriod; periodRow.append(year, month); root.append(periodRow);

        root.append(label("ID"));
        const idRow = document.createElement("div"); idRow.style.cssText = "display:grid;grid-template-columns:minmax(0,1fr) 28px 28px 28px;gap:5px;";
        const select = document.createElement("select"); select.style.cssText = inputStyle;
        const placeholder = document.createElement("option"); placeholder.value = ""; placeholder.textContent = loading ? "Scanning…" : "Select ID…"; select.append(placeholder);
        for (const id of projects) { const option = document.createElement("option"); option.value = id; option.textContent = id; select.append(option); }
        select.value = project.project_id || ""; select.onchange = () => { project.project_id = select.value; commit(); refreshPreview(); };
        stopCanvasEvents(select);
        const previous = button("↑", () => stepProject(-1)); previous.title = "Previous ID"; previous.style.padding = "0"; previous.disabled = loading || !projects.length;
        const next = button("↓", () => stepProject(1)); next.title = "Next ID"; next.style.padding = "0"; next.disabled = loading || !projects.length;
        const refresh = button("↻", refreshProjects); refresh.title = "Rescan project folders"; refresh.style.padding = "0"; refresh.disabled = loading;
        idRow.append(select, previous, next, refresh); root.append(idRow);
        const hint = document.createElement("div"); hint.textContent = status; hint.style.cssText = "min-height:16px;margin-top:3px;color:#aab8c5;font-size:11px;"; root.append(hint);

        root.append(label("Model")); root.append(cards(MODELS, project.model_code, (value) => { project.model_code = value; commit(); render(); }));
        root.append(label("Gildan 5000 shirt color"));
        const colorGrid = document.createElement("div"); colorGrid.style.cssText = "display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;";
        for (const [colorName, code] of COLORS) {
            const selected = project.color_code === code;
            const tile = button("", () => { project.color_code = code; commit(); render(); }, selected);
            tile.title = `${colorName} — ${code} — ${project.color_hexes[code]}`;
            tile.setAttribute("aria-label", tile.title);
            tile.style.cssText = `box-sizing:border-box;display:flex;align-items:center;gap:7px;min-width:0;width:100%;height:34px;padding:3px 6px;text-align:left;border:1px solid ${selected ? "#8ed0ff" : "#666"};border-radius:3px;background:${selected ? "#29526f" : "#303030"};color:#eee;cursor:pointer;font:12px sans-serif;`;
            const swatch = document.createElement("span"); swatch.style.cssText = `flex:none;width:25px;height:24px;border:1px solid #999;border-radius:3px;background:${project.color_hexes[code]};`;
            const title = document.createElement("span"); title.textContent = colorName; title.style.cssText = "min-width:0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
            const tag = document.createElement("span"); tag.textContent = code; tag.style.cssText = "flex:none;color:#b9c7d5;font:10px monospace;";
            tile.append(swatch, title, tag); colorGrid.append(tile);
        }
        root.append(colorGrid);
        const selectedColor = COLORS.find(([, code]) => code === project.color_code) || COLORS[0];
        const hexRow = document.createElement("div"); hexRow.style.cssText = "display:grid;grid-template-columns:minmax(0,1fr) 100px;gap:5px;align-items:center;margin-top:5px;";
        const hexLabel = document.createElement("span"); hexLabel.textContent = `${selectedColor[0]} HEX`; hexLabel.style.color = "#b9c7d5";
        const hex = document.createElement("input"); hex.value = project.color_hexes[project.color_code]; hex.title = "Adjust this shirt color HEX"; hex.style.cssText = inputStyle;
        hex.onchange = () => { if (/^#[0-9a-f]{6}$/i.test(hex.value.trim())) { project.color_hexes[project.color_code] = hex.value.trim().toUpperCase(); commit(); render(); } else hex.value = project.color_hexes[project.color_code]; };
        stopCanvasEvents(hex); hexRow.append(hexLabel, hex); root.append(hexRow);

        root.append(label("Print size"));
        root.append(cards([["Small", "Small"], ["Standard", "Standard"], ["Large", "Large"]], project.print_size, (value) => { project.print_size = value; commit(); render(); }));
        root.append(label("Occasion"));
        const occasion = document.createElement("select"); occasion.style.cssText = inputStyle;
        for (const value of OCCASIONS) { const option = document.createElement("option"); option.value = value; option.textContent = value; occasion.append(option); }
        occasion.value = project.occasion; occasion.onchange = () => { project.occasion = occasion.value; commit(); render(); }; stopCanvasEvents(occasion); root.append(occasion);
        if (project.occasion === "Custom") {
            const custom = document.createElement("input"); custom.value = project.custom_occasion; custom.placeholder = "Describe the occasion or scene"; custom.style.cssText = `${inputStyle}margin-top:5px;`;
            custom.onchange = () => { project.custom_occasion = custom.value.trim(); commit(); }; stopCanvasEvents(custom); root.append(custom);
        }

        root.append(label("Source preview"));
        if (project.project_id) {
            const preview = document.createElement("img"); preview.alt = "Selected print source";
            preview.style.cssText = "display:block;box-sizing:border-box;width:100%;height:auto;background:#171717;border:1px solid #666;border-radius:3px;";
            preview.onload = () => requestAnimationFrame(resize);
            preview.onerror = () => { const message = document.createElement("div"); message.textContent = "Source image not found. Check the artwork file or redesign/source folder."; message.style.cssText = `height:${EMPTY_PREVIEW_HEIGHT}px;display:grid;place-items:center;text-align:center;border:1px dashed #666;color:#aab8c5;`; preview.replaceWith(message); requestAnimationFrame(resize); };
            root.append(preview);
            preview.src = `/endorphin/etsy/print/source-preview?${new URLSearchParams({ root_folder: project.root_folder, workflow_type: project.workflow_type, project_id: project.project_id, v: String(previewRevision) })}`;
        } else {
            const empty = document.createElement("div"); empty.textContent = "Select an ID to preview its source image."; empty.style.cssText = `height:${EMPTY_PREVIEW_HEIGHT}px;display:grid;place-items:center;border:1px dashed #666;color:#aab8c5;`; root.append(empty);
        }
        const outputHeader = document.createElement("div"); outputHeader.style.cssText = "display:flex;align-items:center;justify-content:space-between;gap:6px;";
        outputHeader.append(label(`Output preview — ${project.model_code} / ${project.color_code}`));
        const outputRefresh = button("↻", refreshPreview); outputRefresh.title = "Refresh saved print mockup"; outputRefresh.style.cssText += "width:28px;padding:0;margin-top:6px;";
        outputHeader.append(outputRefresh); root.append(outputHeader);
        if (project.project_id) {
            const output = document.createElement("img"); output.alt = "Saved print mockup";
            output.style.cssText = "display:block;box-sizing:border-box;width:100%;height:auto;background:#171717;border:1px solid #666;border-radius:3px;";
            output.onload = () => requestAnimationFrame(resize);
            output.onerror = () => { const message = document.createElement("div"); message.textContent = "No saved mockup for this model and color yet."; message.style.cssText = `height:${EMPTY_PREVIEW_HEIGHT}px;display:grid;place-items:center;text-align:center;border:1px dashed #666;color:#aab8c5;`; output.replaceWith(message); requestAnimationFrame(resize); };
            root.append(output);
            output.src = `/endorphin/etsy/print/output-preview?${new URLSearchParams({ root_folder: project.root_folder, workflow_type: project.workflow_type, project_id: project.project_id, model_code: project.model_code, color_code: project.color_code, v: String(previewRevision) })}`;
        } else {
            const empty = document.createElement("div"); empty.textContent = "Select an ID to preview its saved print mockup."; empty.style.cssText = `height:${EMPTY_PREVIEW_HEIGHT}px;display:grid;place-items:center;border:1px dashed #666;color:#aab8c5;`; root.append(empty);
        }
    }
    render(); refreshProjects(); resize();
    return { widget, minWidth: 500, minHeight: 800 };
}

app.registerExtension({ name: "endorphin.EtsyPrintSelector", getCustomWidgets() { return { ENDORPHIN_ETSY_PRINT_SELECTOR: createPrintSelector }; } });
