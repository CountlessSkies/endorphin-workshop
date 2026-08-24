import { app } from "../../../scripts/app.js";

const DEFAULT_PALETTE = { selected: 0, colors: [
    { name: "Red", hex: "#EF4444", code: "RED", value: 1 },
    { name: "Green", hex: "#22C55E", code: "GRN", value: 2 },
    { name: "Blue", hex: "#3B82F6", code: "BLU", value: 3 },
] };
const DEFAULT_PROJECT = { root_folder: "G:\\My Drive\\_Etsy\\_Listing", project_id: "RD2608001", workflow_type: "redesign", source_type: "embroidery_reference", route: "redesign_emb_candidate", candidate_letter: "", palette: DEFAULT_PALETTE, creation_period: new Date().toISOString().slice(2, 7).replace("-", "") };
const inputCss = "box-sizing:border-box;min-width:0;width:100%;height:28px;background:#171717;color:#eee;border:1px solid #666;border-radius:3px;padding:4px 6px;font:12px sans-serif;";

function stopCanvasEvents(input) { for (const eventName of ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "keydown", "keyup", "keypress"]) input.addEventListener(eventName, (event) => event.stopPropagation()); }
function normalizeHex(value) { return /^#[0-9a-f]{6}$/i.test(value) ? value.toUpperCase() : "#808080"; }
function suggestColorCode(name) {
    const words = String(name || "").toUpperCase().match(/[A-Z]+/g) || [];
    if (!words.length) return "CLR";
    if (words.length >= 3) return words.slice(0, 3).map((word) => word[0]).join("");
    if (words.length === 2) { const consonants = words[1].replace(/[AEIOU]/g, ""); return consonants.length >= 2 ? `${words[0][0]}${consonants.slice(0, 2)}` : `${words[0][0]}${words[1].slice(0, 2)}`.padEnd(3, words[0][0]); }
    const consonants = words[0].replace(/[AEIOU]/g, ""); return consonants.length >= 3 ? consonants.slice(0, 3) : words[0].slice(0, 3).padEnd(3, "X");
}
function normalizePalette(value) {
    const colors = Array.isArray(value?.colors) ? value.colors : DEFAULT_PALETTE.colors;
    const normalized = colors.map((color, index) => ({ name: String(color?.name || `Color ${index + 1}`), hex: normalizeHex(String(color?.hex || "")), code: /^[A-Z]{3}$/.test(String(color?.code || "").toUpperCase()) ? String(color.code).toUpperCase() : suggestColorCode(color?.name), code_auto: typeof color?.code_auto === "boolean" ? color.code_auto : !color?.code, value: Number.isInteger(Number(color?.value)) ? Number(color.value) : index + 1 }));
    return { selected: Math.max(0, Math.min(Number(value?.selected) || 0, Math.max(0, normalized.length - 1))), colors: normalized };
}
function parsePaletteList(text) {
    const colors = [], errors = [];
    for (const [index, rawLine] of String(text).split(/\r?\n/).entries()) {
        const line = rawLine.trim(); if (!line) continue;
        const hexes = line.match(/#[0-9a-f]{6}\b/gi) || [];
        if (hexes.length !== 1) { errors.push(index + 1); continue; }
        const valueMatch = line.match(/(?:^|\s)[=:|]\s*(-?\d+)\s*$/);
        const value = valueMatch ? Number(valueMatch[1]) : colors.length + 1;
        const name = line
            .replace(hexes[0], "")
            .replace(valueMatch?.[0] || "", "")
            .replace(/\bhex\b/gi, "")
            .replace(/[()[\]{}]/g, " ")
            .replace(/[,:;|]+/g, " ")
            .replace(/\s+/g, " ")
            .trim() || `Color ${colors.length + 1}`;
        colors.push({ name, hex: hexes[0].toUpperCase(), code: suggestColorCode(name), code_auto: true, value });
    }
    return { colors, errors };
}
function hexToHsl(hex) {
    const value = normalizeHex(hex).slice(1); const red = parseInt(value.slice(0, 2), 16) / 255, green = parseInt(value.slice(2, 4), 16) / 255, blue = parseInt(value.slice(4, 6), 16) / 255;
    const max = Math.max(red, green, blue), min = Math.min(red, green, blue), lightness = (max + min) / 2, delta = max - min;
    if (!delta) return { h: 0, s: 0, l: Math.round(lightness * 100) };
    const saturation = delta / (1 - Math.abs(2 * lightness - 1)); let hue;
    if (max === red) hue = 60 * (((green - blue) / delta) % 6); else if (max === green) hue = 60 * ((blue - red) / delta + 2); else hue = 60 * ((red - green) / delta + 4);
    return { h: Math.round((hue + 360) % 360), s: Math.round(saturation * 100), l: Math.round(lightness * 100) };
}
function hslToHex(hue, saturation, lightness) {
    const h = ((Number(hue) % 360) + 360) % 360 / 360, s = Number(saturation) / 100, l = Number(lightness) / 100;
    const chroma = (1 - Math.abs(2 * l - 1)) * s, second = chroma * (1 - Math.abs((h * 6) % 2 - 1)), match = l - chroma / 2;
    const [red, green, blue] = h < 1 / 6 ? [chroma, second, 0] : h < 2 / 6 ? [second, chroma, 0] : h < 3 / 6 ? [0, chroma, second] : h < 4 / 6 ? [0, second, chroma] : h < 5 / 6 ? [second, 0, chroma] : [chroma, 0, second];
    return `#${[red, green, blue].map((component) => Math.round((component + match) * 255).toString(16).padStart(2, "0")).join("").toUpperCase()}`;
}
function ensureHslSliderStyles() {
    if (document.getElementById("endorphin-hsl-slider-styles")) return;
    const style = document.createElement("style"); style.id = "endorphin-hsl-slider-styles";
    style.textContent = ".endorphin-hsl-range{appearance:none;-webkit-appearance:none;height:10px;border-radius:6px;outline:none}.endorphin-hsl-range::-webkit-slider-runnable-track{height:10px;background:transparent;border-radius:6px}.endorphin-hsl-range::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:16px;height:16px;margin-top:-3px;border:2px solid #e8f5ff;border-radius:50%;background:#2d82bb;box-shadow:0 0 0 1px #102331;cursor:pointer}.endorphin-hsl-range::-moz-range-track{height:10px;background:transparent;border-radius:6px}.endorphin-hsl-range::-moz-range-thumb{width:12px;height:12px;border:2px solid #e8f5ff;border-radius:50%;background:#2d82bb;box-shadow:0 0 0 1px #102331;cursor:pointer}.endorphin-palette-number{-moz-appearance:textfield}.endorphin-palette-number::-webkit-inner-spin-button,.endorphin-palette-number::-webkit-outer-spin-button{-webkit-appearance:none;margin:0}";
    document.head.append(style);
}
function parseProject(value) {
    try {
        const data = typeof value === "string" ? JSON.parse(value) : value;
        const workflow = data?.workflow_type === "artwork" ? "artwork" : "redesign";
        return { root_folder: String(data?.root_folder || DEFAULT_PROJECT.root_folder), project_id: String(data?.project_id || (workflow === "artwork" ? "2608001" : "RD2608001")), workflow_type: workflow, source_type: data?.source_type === "print_reference" ? "print_reference" : "embroidery_reference", route: String(data?.route || (workflow === "artwork" ? "artwork_foundation" : data?.source_type === "print_reference" ? "redesign_print_candidate" : "redesign_emb_candidate")), candidate_letter: /^[A-Z]+$/i.test(String(data?.candidate_letter || "")) ? String(data.candidate_letter).toUpperCase() : "", palette: normalizePalette(data?.palette), creation_period: /^\d{4}$/.test(String(data?.creation_period || "")) ? String(data.creation_period) : DEFAULT_PROJECT.creation_period };
    } catch { return { ...structuredClone(DEFAULT_PROJECT), palette: structuredClone(DEFAULT_PALETTE) }; }
}
function editableInput(value, placeholder, onCommit) { const input = document.createElement("input"); input.value = value; input.placeholder = placeholder; input.style.cssText = inputCss; stopCanvasEvents(input); input.onchange = () => onCommit(input.value.trim()); input.onblur = input.onchange; return input; }
function creationYears() { const now = new Date(); return Array.from({ length: 9 }, (_, index) => now.getFullYear() - 4 + index); }
function card(label, selected, onClick) { const button = document.createElement("button"); button.type = "button"; button.textContent = selected ? `● ${label}` : `○ ${label}`; button.style.cssText = `height:32px;text-align:left;padding:5px 8px;border:1px solid ${selected ? "#8ed0ff" : "#666"};border-radius:3px;background:${selected ? "#29526f" : "#303030"};color:${selected ? "#d9f0ff" : "#ddd"};cursor:pointer;font:12px sans-serif;`; button.onclick = (event) => { event.stopPropagation(); onClick(); }; return button; }

function createProjectSelector(node, inputName, inputData) {
    ensureHslSliderStyles();
    let project = parseProject(inputData?.[1]?.default), projects = [], candidates = [], loading = false, loadingCandidates = false, paletteImporter = false, colorEditorIndex = null, stagePreviewHeight = 240, status = "";
    const root = document.createElement("div"); root.style.cssText = "box-sizing:border-box;width:100%;height:auto;padding:7px;background:#202020;color:#ddd;font:12px sans-serif;"; root.addEventListener("pointerdown", (event) => event.stopPropagation());
    // This is deliberately derived from the controls we render, not from DOM
    // height. Comfy mounts DOM widgets with a full-height wrapper, so DOM geometry
    // can retain the previous stage's height after its controls are removed.
    const candidatePreviewHeight = (allowApproval) => {
        const selected = candidates.find((candidate) => candidate.letter === project.candidate_letter);
        let height = candidates.length ? 56 : 42; // Heading + candidate buttons/empty hint.
        if (selected) height += 82 + (allowApproval && !selected.approved ? 28 : 0);
        return height;
    };
    const contentMinHeight = () => {
        let height = 300; // Project root through Route, including root padding.
        if (["artwork_foundation", "artwork_stitchwork"].includes(project.route)) return height + stagePreviewHeight + 39;
        if (["redesign_emb_candidate", "redesign_print_candidate"].includes(project.route)) return height + candidatePreviewHeight(false);
        if (!project.route.endsWith("colorway")) return height;

        if (project.route === "redesign_colorway") {
            height += candidatePreviewHeight(true);
        }
        // Palette heading, its rows (38px + 5px gap), and Add Color.
        return height + 52 + project.palette.colors.length * 43 + (paletteImporter ? 190 : 0) + (colorEditorIndex === null ? 0 : 128);
    };
    const widget = node.addDOMWidget(inputName, "ENDORPHIN_ETSY_PROJECT_SELECTOR", root, { getValue: () => JSON.stringify(project), setValue: (value) => { project = parseProject(value); render(); requestAnimationFrame(resize); }, getMinHeight: contentMinHeight, getMinWidth: () => 500 });
    function resize() { const size = node.computeSize(); node.setSize([Math.max(500, node.size[0], size[0]), size[1]]); node.graph?.setDirtyCanvas(true, true); }
    function commit() { widget.value = JSON.stringify(project); node.graph?.setDirtyCanvas(true, true); resize(); }
    function label(text) { const element = document.createElement("div"); element.textContent = text; element.style.cssText = "margin:7px 0 3px;color:#b9c7d5;font-weight:600;"; return element; }
    function button(text, onClick, disabled = false) { const element = document.createElement("button"); element.type = "button"; element.textContent = text; element.disabled = disabled; element.style.cssText = "height:28px;padding:4px 8px;border:1px solid #666;border-radius:3px;background:#303030;color:#d9f0ff;cursor:pointer;font:12px sans-serif;"; element.onclick = (event) => { event.stopPropagation(); onClick(); }; return element; }
    function cards(items, selected, setSelected) { const row = document.createElement("div"); row.style.cssText = `display:grid;grid-template-columns:repeat(${items.length},minmax(0,1fr));gap:5px;`; for (const [value, title] of items) row.append(card(title, selected === value, () => { setSelected(value); render(); commit(); })); return row; }
    async function refreshProjects() {
        loading = true; status = "Loading IDs…"; render();
        try { const response = await fetch(`/endorphin/etsy/projects?${new URLSearchParams({ root_folder: project.root_folder, workflow_type: project.workflow_type })}`); const data = await response.json(); if (!response.ok) throw new Error(data.error || "Could not scan project folders."); projects = Array.isArray(data.projects) ? data.projects : []; if (project.project_id && !projects.includes(project.project_id)) { project.project_id = ""; project.candidate_letter = ""; commit(); } status = projects.length ? `${projects.length} existing ID${projects.length === 1 ? "" : "s"}.` : "No existing IDs."; } catch (error) { status = error.message || "Could not scan project folders."; projects = []; } finally { loading = false; render(); resize(); }
    }
    async function refreshCandidates() {
        if (project.workflow_type !== "redesign" || !project.project_id.startsWith("RD")) { candidates = []; return; }
        loadingCandidates = true; render();
        try { const response = await fetch(`/endorphin/etsy/candidates?${new URLSearchParams({ root_folder: project.root_folder, project_id: project.project_id })}`); const data = await response.json(); if (!response.ok) throw new Error(data.error || "Could not scan candidates."); candidates = Array.isArray(data.candidates) ? data.candidates : []; if (project.candidate_letter && !candidates.some((candidate) => candidate.letter === project.candidate_letter)) { project.candidate_letter = ""; commit(); } } catch (error) { candidates = []; status = error.message || "Could not scan candidates."; } finally { loadingCandidates = false; render(); resize(); }
    }
    async function createProject() {
        loading = true; status = "Creating project…"; render();
        try { const response = await fetch("/endorphin/etsy/projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ root_folder: project.root_folder, workflow_type: project.workflow_type, source_type: project.source_type, period: project.creation_period }) }); const data = await response.json(); if (!response.ok) throw new Error(data.error || "Could not create project."); project.project_id = data.project_id; project.candidate_letter = ""; commit(); await refreshProjects(); await refreshCandidates(); status = `Created ${data.project_id}.`; } catch (error) { status = error.message || "Could not create project."; } finally { loading = false; render(); resize(); }
    }
    async function approveCandidate() {
        if (!project.candidate_letter) { status = "Select a candidate first."; render(); return; }
        loadingCandidates = true; render();
        try { const response = await fetch("/endorphin/etsy/candidates/approve", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ root_folder: project.root_folder, project_id: project.project_id, candidate_letter: project.candidate_letter }) }); const data = await response.json(); if (!response.ok) throw new Error(data.error || "Could not approve candidate."); status = `Approved ${data.product_id}.`; await refreshCandidates(); } catch (error) { status = error.message || "Could not approve candidate."; } finally { loadingCandidates = false; render(); resize(); }
    }
    function renderHslEditor(color) {
        ensureHslSliderStyles();
        const hsl = hexToHsl(color.hex), panel = document.createElement("div"); panel.style.cssText = "box-sizing:border-box;margin:-1px 0 6px;padding:7px;border:1px solid #4b86aa;border-radius:3px;background:#1b2730;";
        const heading = document.createElement("div"); heading.textContent = "HSL color adjustment"; heading.style.cssText = "margin-bottom:5px;color:#bde3ff;font-weight:600;";
        const sample = document.createElement("div"); sample.style.cssText = `height:22px;margin-bottom:6px;border:1px solid #aaa;border-radius:3px;background:${color.hex};`;
        const hexValue = document.createElement("span"); hexValue.textContent = color.hex; hexValue.style.cssText = "margin-left:6px;color:#d9f0ff;font-family:monospace;";
        sample.append(hexValue); panel.append(heading, sample);
        const values = { h: hsl.h, s: hsl.s, l: hsl.l }, sliders = {};
        const paintTracks = () => {
            const hueColor = hslToHex(values.h, 100, 50);
            sliders.h.style.background = "linear-gradient(to right,#ff0000,#ffff00,#00ff00,#00ffff,#0000ff,#ff00ff,#ff0000)";
            sliders.s.style.background = `linear-gradient(to right,#808080,${hueColor})`;
            sliders.l.style.background = `linear-gradient(to right,#000000,${hueColor},#ffffff)`;
        };
        for (const [key, title, max] of [["h", "Hue", 360], ["s", "Saturation", 100], ["l", "Lightness", 100]]) {
            const line = document.createElement("div"); line.style.cssText = "display:grid;grid-template-columns:76px minmax(0,1fr) 42px;gap:6px;align-items:center;margin-top:4px;";
            const name = document.createElement("span"); name.textContent = title;
            const slider = document.createElement("input"); slider.type = "range"; slider.className = "endorphin-hsl-range"; slider.min = "0"; slider.max = String(max); slider.step = "1"; slider.value = String(values[key]); slider.style.cssText = "width:100%;"; sliders[key] = slider; stopCanvasEvents(slider);
            const number = document.createElement("input"); number.type = "number"; number.min = "0"; number.max = String(max); number.step = "1"; number.value = String(values[key]); number.style.cssText = inputCss; stopCanvasEvents(number);
            const update = () => { values[key] = Math.max(0, Math.min(max, Number(slider.value))); number.value = String(values[key]); color.hex = hslToHex(values.h, values.s, values.l); sample.style.background = color.hex; hexValue.textContent = color.hex; paintTracks(); };
            slider.oninput = update; slider.onchange = () => { update(); commit(); };
            number.onchange = () => { slider.value = number.value; update(); commit(); }; number.onblur = number.onchange;
            line.append(name, slider, number); panel.append(line);
        }
        paintTracks();
        return panel;
    }
    function renderPalette() {
        const section = document.createElement("div"); section.append(label("Color palette"));
        project.palette.colors.forEach((color, index) => {
            const selected = index === project.palette.selected, row = document.createElement("div"); row.style.cssText = `box-sizing:border-box;display:grid;grid-template-columns:44px minmax(90px,1fr) 72px 48px 42px 22px 22px 34px 26px;gap:5px;align-items:center;height:38px;margin-bottom:5px;padding:3px;border:1px solid ${selected ? "#8ed0ff" : "#666"};border-radius:3px;background:${selected ? "#29526f" : "#303030"};`;
            const swatch = button("", () => { project.palette.selected = index; commit(); render(); }); swatch.title = "Select color"; swatch.style.cssText = `height:25px;padding:0;border:1px solid #aaa;border-radius:3px;background:${color.hex};cursor:pointer;`;
            const name = editableInput(color.name, "Color name", (value) => { color.name = value || color.name; if (color.code_auto) color.code = suggestColorCode(color.name); commit(); render(); });
            const hex = editableInput(color.hex, "#RRGGBB", (value) => { if (/^#[0-9a-f]{6}$/i.test(value)) { color.hex = value.toUpperCase(); commit(); render(); } });
            const code = editableInput(color.code, "MTP", (value) => { if (/^[A-Z]{3}$/i.test(value)) { color.code = value.toUpperCase(); color.code_auto = false; commit(); } });
            const numberWrap = document.createElement("div"); numberWrap.style.cssText = "position:relative;height:25px;min-width:0;";
            const number = document.createElement("input"); number.type = "number"; number.className = "endorphin-palette-number"; number.step = "1"; number.value = String(color.value); number.style.cssText = "box-sizing:border-box;min-width:0;width:100%;height:25px;background:#171717;color:#eee;border:1px solid #666;border-radius:5px;padding:3px 17px 3px 5px;font:12px sans-serif;"; stopCanvasEvents(number); number.onchange = () => { if (Number.isInteger(Number(number.value))) { color.value = Number(number.value); commit(); } else number.value = String(color.value); };
            const adjustValue = (amount) => { color.value += amount; number.value = String(color.value); commit(); };
            const spinner = document.createElement("div"); spinner.style.cssText = "position:absolute;top:2px;right:2px;bottom:2px;width:13px;display:grid;grid-template-rows:1fr 1fr;gap:1px;";
            for (const [glyph, amount, title] of [["▲", 1, "Increase value"], ["▼", -1, "Decrease value"]]) { const control = document.createElement("button"); control.type = "button"; control.textContent = glyph; control.title = title; control.style.cssText = "padding:0;border:0;border-radius:3px;background:#31566e;color:#d9f0ff;cursor:pointer;font:7px sans-serif;line-height:8px;"; control.onclick = (event) => { event.stopPropagation(); adjustValue(amount); }; spinner.append(control); }
            numberWrap.append(number, spinner);
            const moveUp = button("↑", () => { if (index > 0) { [project.palette.colors[index - 1], project.palette.colors[index]] = [project.palette.colors[index], project.palette.colors[index - 1]]; project.palette.selected = index - 1; colorEditorIndex = null; commit(); render(); } }); moveUp.title = "Move color up"; moveUp.disabled = index === 0; moveUp.style.cssText = "height:25px;padding:0;border:1px solid #666;border-radius:5px;background:#303030;color:#d9f0ff;cursor:pointer;font:12px sans-serif;";
            const moveDown = button("↓", () => { if (index < project.palette.colors.length - 1) { [project.palette.colors[index], project.palette.colors[index + 1]] = [project.palette.colors[index + 1], project.palette.colors[index]]; project.palette.selected = index + 1; colorEditorIndex = null; commit(); render(); } }); moveDown.title = "Move color down"; moveDown.disabled = index === project.palette.colors.length - 1; moveDown.style.cssText = "height:25px;padding:0;border:1px solid #666;border-radius:5px;background:#303030;color:#d9f0ff;cursor:pointer;font:12px sans-serif;";
            const hsl = button("HSL", () => { project.palette.selected = index; colorEditorIndex = colorEditorIndex === index ? null : index; commit(); render(); }); hsl.title = "Adjust this color with HSL sliders"; hsl.style.cssText = "height:24px;padding:1px 6px;border:1px solid #5b9dcc;border-radius:12px;background:#244a63;color:#d9f0ff;cursor:pointer;font:10px sans-serif;";
            const remove = button("×", () => { project.palette.colors.splice(index, 1); project.palette.selected = Math.min(project.palette.selected, Math.max(0, project.palette.colors.length - 1)); colorEditorIndex = null; commit(); render(); }); remove.title = "Remove color"; remove.style.padding = "3px";
            row.onclick = () => { project.palette.selected = index; commit(); render(); }; row.append(swatch, name, hex, code, numberWrap, moveUp, moveDown, hsl, remove); section.append(row); if (colorEditorIndex === index) section.append(renderHslEditor(color));
        });
        const actions = document.createElement("div"); actions.style.cssText = "display:flex;gap:6px;margin-top:2px;";
        actions.append(button("+ Add Color", () => { const index = project.palette.colors.length + 1, name = `Color ${index}`, value = Math.max(0, ...project.palette.colors.map((color) => Number(color.value) || 0)) + 1; project.palette.colors.push({ name, hex: "#808080", code: suggestColorCode(name), code_auto: true, value }); project.palette.selected = project.palette.colors.length - 1; commit(); render(); }));
        actions.append(button(paletteImporter ? "Hide Paste" : "⇩ Paste List", () => { paletteImporter = !paletteImporter; render(); requestAnimationFrame(resize); })); section.append(actions);
        if (paletteImporter) {
            const hint = document.createElement("div"); hint.textContent = "One color per line. Any format with one #RRGGBB works; optional value: | 1"; hint.style.cssText = "margin:8px 0 4px;color:#b9c7d5;";
            const textarea = document.createElement("textarea"); textarea.placeholder = "mocha taupe (hex #977D67)\n#D9DADE soft white\ncream, #E0DCC8 | 3"; textarea.style.cssText = "box-sizing:border-box;width:100%;height:110px;resize:vertical;border:1px solid #666;border-radius:3px;padding:5px;background:#171717;color:#eee;font:12px monospace;"; stopCanvasEvents(textarea);
            const error = document.createElement("div"); error.style.cssText = "min-height:16px;margin-top:3px;color:#fca5a5;";
            const importActions = document.createElement("div"); importActions.style.cssText = "display:flex;gap:6px;margin-top:4px;";
            importActions.append(button("Import", () => { const { colors, errors } = parsePaletteList(textarea.value); if (errors.length || !colors.length) { error.textContent = errors.length ? `Could not read line: ${errors.join(", ")}.` : "Paste at least one color with a #RRGGBB code."; return; } project.palette = { selected: 0, colors }; paletteImporter = false; colorEditorIndex = null; commit(); render(); }));
            importActions.append(button("Cancel", () => { paletteImporter = false; render(); requestAnimationFrame(resize); })); section.append(hint, textarea, error, importActions);
        }
        return section;
    }
    function renderStagePreview() {
        const names = { artwork_foundation: "base_<ID>_transparent", artwork_stitchwork: "base_<ID>_emb" };
        const section = document.createElement("div"); section.append(label(`Stage output preview — ${names[project.route]}`));
        stagePreviewHeight = 240;
        const preview = document.createElement("img"); preview.src = `/endorphin/etsy/stage-preview?${new URLSearchParams({ root_folder: project.root_folder, project_id: project.project_id, route: project.route })}`; preview.alt = `${project.route} output preview`; preview.style.cssText = "display:block;box-sizing:border-box;width:100%;height:auto;background:#171717;border:1px solid #666;border-radius:3px;";
        preview.onload = () => { stagePreviewHeight = Math.max(120, preview.offsetHeight); requestAnimationFrame(resize); };
        preview.onerror = () => { const message = document.createElement("div"); message.textContent = `No output yet — this stage has not created ${names[project.route]}.`; message.style.cssText = `box-sizing:border-box;width:100%;height:${stagePreviewHeight}px;padding:8px;display:flex;align-items:center;background:#171717;border:1px dashed #666;border-radius:3px;color:#aab8c5;font-size:11px;`; preview.replaceWith(message); requestAnimationFrame(resize); };
        section.append(preview); return section;
    }
    function renderCandidateSelector(allowApproval = false) {
        const section = document.createElement("div"); section.append(label(allowApproval ? "Redesign candidate" : "Generated candidates preview"));
        if (loadingCandidates) section.append(document.createTextNode("Loading candidates…"));
        else if (!candidates.length) section.append(document.createTextNode("No candidate output yet — this stage has not run."));
        else { const row = document.createElement("div"); row.style.cssText = "display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;"; for (const candidate of candidates) row.append(card(`${candidate.letter} ${candidate.approved ? "✓" : ""}`, project.candidate_letter === candidate.letter, () => { project.candidate_letter = candidate.letter; commit(); render(); })); section.append(row); const selected = candidates.find((candidate) => candidate.letter === project.candidate_letter); if (selected) { const details = document.createElement("div"); details.style.cssText = "display:grid;grid-template-columns:100px minmax(0,1fr);gap:8px;margin-top:6px;align-items:center;"; const preview = document.createElement("img"); preview.src = selected.preview_url; preview.alt = `${selected.product_id} preview`; preview.style.cssText = "width:100px;height:76px;object-fit:contain;background:#171717;border:1px solid #666;border-radius:3px;"; const info = document.createElement("div"); info.textContent = allowApproval ? (selected.approved ? `${selected.product_id} is approved and ready for Colorway.` : `${selected.product_id} is unapproved. Approve it before Colorway can run.`) : `${selected.product_id} candidate output.`; details.append(preview, info); section.append(details); if (allowApproval && !selected.approved) section.append(button("Approve selected candidate", approveCandidate, loadingCandidates)); } }
        return section;
    }
    function render() {
        root.replaceChildren(); root.append(label("Project root")); root.append(editableInput(project.root_folder, "G:\\My Drive\\_Etsy\\_Listing", (value) => { project.root_folder = value || DEFAULT_PROJECT.root_folder; project.candidate_letter = ""; commit(); refreshProjects(); refreshCandidates(); }));
        root.append(label("Workflow")); root.append(cards([["artwork", "Artwork"], ["redesign", "Redesign"]], project.workflow_type, (value) => { project.workflow_type = value; project.route = value === "artwork" ? "artwork_foundation" : "redesign_emb_candidate"; project.project_id = ""; project.candidate_letter = ""; status = ""; projects = []; candidates = []; refreshProjects(); }));
        root.append(label("New ID date (used only by + New)")); const dateRow = document.createElement("div"); dateRow.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:5px;"; const yearSelect = document.createElement("select"); yearSelect.style.cssText = inputCss; const selectedYear = Number(`20${project.creation_period.slice(0, 2)}`), years = creationYears(); if (!years.includes(selectedYear)) years.push(selectedYear); for (const year of years.sort((a, b) => a - b)) { const option = document.createElement("option"); option.value = String(year).slice(-2); option.textContent = `Year ${year}`; yearSelect.append(option); } yearSelect.value = project.creation_period.slice(0, 2); const monthSelect = document.createElement("select"); monthSelect.style.cssText = inputCss; for (let month = 1; month <= 12; month += 1) { const option = document.createElement("option"); option.value = String(month).padStart(2, "0"); option.textContent = `Month ${String(month).padStart(2, "0")}`; monthSelect.append(option); } monthSelect.value = project.creation_period.slice(2, 4); const commitPeriod = () => { project.creation_period = `${yearSelect.value}${monthSelect.value}`; commit(); }; yearSelect.onchange = commitPeriod; monthSelect.onchange = commitPeriod; stopCanvasEvents(yearSelect); stopCanvasEvents(monthSelect); dateRow.append(yearSelect, monthSelect); root.append(dateRow);
        root.append(label("ID")); const idRow = document.createElement("div"); idRow.style.cssText = "display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:5px;"; const select = document.createElement("select"); select.style.cssText = inputCss; const placeholder = document.createElement("option"); placeholder.value = ""; placeholder.textContent = loading ? "Loading IDs…" : "Select existing ID…"; select.append(placeholder); for (const id of projects) { const option = document.createElement("option"); option.value = id; option.textContent = id; select.append(option); } select.value = project.project_id || ""; select.onchange = () => { project.project_id = select.value; project.candidate_letter = ""; commit(); refreshCandidates(); }; stopCanvasEvents(select); idRow.append(select, button("↻", refreshProjects, loading), button("+ New", createProject, loading)); root.append(idRow);
        const hint = document.createElement("div"); hint.textContent = status || `Pick an existing ID, or create the next ${project.creation_period}NNN ID automatically.`; hint.style.cssText = "min-height:15px;margin-top:3px;color:#aab8c5;font-size:11px;"; root.append(hint); root.append(label("Route"));
        if (project.workflow_type === "artwork") root.append(cards([["artwork_foundation", "Foundation"], ["artwork_stitchwork", "Stitchwork"], ["artwork_colorway", "Colorway"]], project.route, (value) => { project.route = value; project.source_type = "idea_artwork"; }));
        else root.append(cards([["redesign_emb_candidate", "Embroidery candidate"], ["redesign_print_candidate", "Print candidate"], ["redesign_colorway", "Colorway"]], project.route, (value) => { project.route = value; project.source_type = value === "redesign_print_candidate" ? "print_reference" : value === "redesign_emb_candidate" ? "embroidery_reference" : "approved_candidate"; refreshCandidates(); }));
        if (["artwork_foundation", "artwork_stitchwork"].includes(project.route)) root.append(renderStagePreview());
        if (["redesign_emb_candidate", "redesign_print_candidate"].includes(project.route)) root.append(renderCandidateSelector());
        if (project.route === "redesign_colorway") root.append(renderCandidateSelector(true)); if (project.route.endsWith("colorway")) root.append(renderPalette());
    }
    render(); requestAnimationFrame(resize); refreshProjects(); refreshCandidates(); return { widget, minWidth: 500, minHeight: 260 };
}

app.registerExtension({ name: "endorphin.EtsyProjectSelector", getCustomWidgets() { return { ENDORPHIN_ETSY_PROJECT_SELECTOR: createProjectSelector }; } });
