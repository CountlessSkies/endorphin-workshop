import { app } from "../../../scripts/app.js";

const DEFAULT_PROJECT = {
    root_folder: "G:\\My Drive\\_Etsy\\_Listing",
    project_id: "RD2608001",
    workflow_type: "redesign",
    source_type: "embroidery_reference",
    route: "redesign_emb_candidate",
    creation_period: new Date().toISOString().slice(2, 7).replace("-", ""),
};

function parseProject(value) {
    try {
        const data = typeof value === "string" ? JSON.parse(value) : value;
        const workflow = data?.workflow_type === "artwork" ? "artwork" : "redesign";
        return {
            root_folder: String(data?.root_folder || DEFAULT_PROJECT.root_folder),
            project_id: String(data?.project_id || (workflow === "artwork" ? "2608001" : "RD2608001")),
            workflow_type: workflow,
            source_type: data?.source_type === "print_reference" ? "print_reference" : "embroidery_reference",
            route: String(data?.route || (workflow === "artwork" ? "artwork_foundation" : data?.source_type === "print_reference" ? "redesign_print_candidate" : "redesign_emb_candidate")),
            creation_period: /^\d{4}$/.test(String(data?.creation_period || "")) ? String(data.creation_period) : DEFAULT_PROJECT.creation_period,
        };
    } catch {
        return structuredClone(DEFAULT_PROJECT);
    }
}

function editableInput(value, placeholder, onCommit) {
    const input = document.createElement("input");
    input.value = value;
    input.placeholder = placeholder;
    input.style.cssText = "box-sizing:border-box;min-width:0;width:100%;height:28px;background:#171717;color:#eee;border:1px solid #666;border-radius:3px;padding:4px 6px;font:12px sans-serif;";
    for (const eventName of ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "keydown", "keyup", "keypress"]) {
        input.addEventListener(eventName, (event) => event.stopPropagation());
    }
    input.onchange = () => onCommit(input.value.trim());
    input.onblur = input.onchange;
    return input;
}

function creationYears() {
    const now = new Date();
    return Array.from({ length: 9 }, (_, index) => now.getFullYear() - 4 + index);
}

function card(label, selected, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = selected ? `● ${label}` : `○ ${label}`;
    button.style.cssText = `height:32px;text-align:left;padding:5px 8px;border:1px solid ${selected ? "#8ed0ff" : "#666"};border-radius:3px;background:${selected ? "#29526f" : "#303030"};color:${selected ? "#d9f0ff" : "#ddd"};cursor:pointer;font:12px sans-serif;`;
    button.onclick = (event) => { event.stopPropagation(); onClick(); };
    return button;
}

function createProjectSelector(node, inputName, inputData) {
    let project = parseProject(inputData?.[1]?.default);
    let projects = [];
    let loading = false;
    let status = "";
    const root = document.createElement("div");
    root.style.cssText = "box-sizing:border-box;width:100%;padding:7px;background:#202020;color:#ddd;font:12px sans-serif;";
    root.addEventListener("pointerdown", (event) => event.stopPropagation());
    const widget = node.addDOMWidget(inputName, "ENDORPHIN_ETSY_PROJECT_SELECTOR", root, {
        getValue: () => JSON.stringify(project),
        setValue: (value) => { project = parseProject(value); render(); requestAnimationFrame(resize); },
        getMinHeight: () => project.workflow_type === "artwork" ? 310 : 345,
        getMinWidth: () => 390,
    });

    function resize() {
        const size = node.computeSize();
        node.setSize([Math.max(390, node.size[0], size[0]), size[1]]);
        node.graph?.setDirtyCanvas(true, true);
    }
    function commit() {
        widget.value = JSON.stringify(project);
        node.graph?.setDirtyCanvas(true, true);
        resize();
    }
    function label(text) {
        const element = document.createElement("div");
        element.textContent = text;
        element.style.cssText = "margin:5px 0 3px;color:#b9c7d5;font-weight:600;";
        return element;
    }
    function cards(items, selected, setSelected) {
        const row = document.createElement("div");
        row.style.cssText = `display:grid;grid-template-columns:repeat(${items.length},minmax(0,1fr));gap:5px;`;
        for (const [value, title] of items) row.append(card(title, selected === value, () => { setSelected(value); render(); commit(); }));
        return row;
    }
    function button(text, onClick, disabled = false) {
        const element = document.createElement("button");
        element.type = "button";
        element.textContent = text;
        element.disabled = disabled;
        element.style.cssText = "height:28px;padding:4px 8px;border:1px solid #666;border-radius:3px;background:#303030;color:#d9f0ff;cursor:pointer;font:12px sans-serif;";
        element.onclick = (event) => { event.stopPropagation(); onClick(); };
        return element;
    }
    async function refreshProjects() {
        loading = true;
        status = "Loading IDs…";
        render();
        try {
            const query = new URLSearchParams({ root_folder: project.root_folder, workflow_type: project.workflow_type });
            const response = await fetch(`/endorphin/etsy/projects?${query.toString()}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Could not scan project folders.");
            projects = Array.isArray(data.projects) ? data.projects : [];
            if (project.project_id && !projects.includes(project.project_id)) {
                project.project_id = "";
                commit();
            }
            status = projects.length ? `${projects.length} existing ID${projects.length === 1 ? "" : "s"}.` : "No existing IDs.";
        } catch (error) {
            status = error.message || "Could not scan project folders.";
            projects = [];
        } finally {
            loading = false;
            render();
            resize();
        }
    }
    async function createProject() {
        loading = true;
        status = "Creating project…";
        render();
        try {
            const response = await fetch("/endorphin/etsy/projects", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ root_folder: project.root_folder, workflow_type: project.workflow_type, source_type: project.source_type, period: project.creation_period }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Could not create project.");
            project.project_id = data.project_id;
            commit();
            await refreshProjects();
            status = `Created ${data.project_id}.`;
        } catch (error) {
            status = error.message || "Could not create project.";
        } finally {
            loading = false;
            render();
            resize();
        }
    }
    function render() {
        root.replaceChildren();
        root.append(label("Project root"));
        root.append(editableInput(project.root_folder, "G:\\My Drive\\_Etsy\\_Listing", (value) => { project.root_folder = value || DEFAULT_PROJECT.root_folder; commit(); refreshProjects(); }));
        root.append(label("Workflow"));
        root.append(cards([["artwork", "Artwork"], ["redesign", "Redesign"]], project.workflow_type, (value) => {
            project.workflow_type = value;
            project.route = value === "artwork" ? "artwork_foundation" : "redesign_emb_candidate";
            project.project_id = "";
            status = "";
            projects = [];
            refreshProjects();
        }));
        root.append(label("New ID date (used only by + New)"));
        const dateRow = document.createElement("div");
        dateRow.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:5px;";
        const selectStyle = "box-sizing:border-box;min-width:0;width:100%;height:28px;background:#171717;color:#eee;border:1px solid #666;border-radius:3px;padding:3px 5px;font:12px sans-serif;";
        const yearSelect = document.createElement("select");
        yearSelect.style.cssText = selectStyle;
        const selectedYear = Number(`20${project.creation_period.slice(0, 2)}`);
        const years = creationYears();
        if (!years.includes(selectedYear)) years.push(selectedYear);
        for (const year of years.sort((a, b) => a - b)) {
            const option = document.createElement("option");
            option.value = String(year).slice(-2);
            option.textContent = `Year ${year}`;
            yearSelect.append(option);
        }
        yearSelect.value = project.creation_period.slice(0, 2);
        const monthSelect = document.createElement("select");
        monthSelect.style.cssText = selectStyle;
        for (let month = 1; month <= 12; month += 1) {
            const option = document.createElement("option");
            option.value = String(month).padStart(2, "0");
            option.textContent = `Month ${String(month).padStart(2, "0")}`;
            monthSelect.append(option);
        }
        monthSelect.value = project.creation_period.slice(2, 4);
        const commitPeriod = () => { project.creation_period = `${yearSelect.value}${monthSelect.value}`; commit(); };
        yearSelect.onchange = commitPeriod;
        monthSelect.onchange = commitPeriod;
        yearSelect.addEventListener("pointerdown", (event) => event.stopPropagation());
        monthSelect.addEventListener("pointerdown", (event) => event.stopPropagation());
        dateRow.append(yearSelect, monthSelect);
        root.append(dateRow);
        root.append(label("ID"));
        const idRow = document.createElement("div");
        idRow.style.cssText = "display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:5px;";
        const select = document.createElement("select");
        select.style.cssText = "box-sizing:border-box;min-width:0;width:100%;height:28px;background:#171717;color:#eee;border:1px solid #666;border-radius:3px;padding:3px 5px;font:12px sans-serif;";
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = loading ? "Loading IDs…" : "Select existing ID…";
        select.append(placeholder);
        for (const id of projects) {
            const option = document.createElement("option");
            option.value = id;
            option.textContent = id;
            option.selected = id === project.project_id;
            select.append(option);
        }
        select.value = project.project_id || "";
        select.onchange = () => { project.project_id = select.value; commit(); };
        select.addEventListener("pointerdown", (event) => event.stopPropagation());
        idRow.append(select, button("↻", refreshProjects, loading), button("+ New", createProject, loading));
        root.append(idRow);
        const hint = document.createElement("div");
        hint.textContent = status || `Pick an existing ID, or create the next ${project.creation_period}NNN ID automatically.`;
        hint.style.cssText = "min-height:15px;margin-top:3px;color:#aab8c5;font-size:11px;";
        root.append(hint);
        root.append(label("Route"));
        if (project.workflow_type === "artwork") {
            root.append(cards([["artwork_foundation", "Foundation"], ["artwork_stitchwork", "Stitchwork"], ["artwork_colorway", "Colorway"]], project.route, (value) => { project.route = value; project.source_type = "idea_artwork"; }));
        } else {
            root.append(cards([["redesign_emb_candidate", "Embroidery candidate"], ["redesign_print_candidate", "Print candidate"], ["redesign_colorway", "Colorway"]], project.route, (value) => { project.route = value; project.source_type = value === "redesign_print_candidate" ? "print_reference" : value === "redesign_emb_candidate" ? "embroidery_reference" : "approved_candidate"; }));
        }
    }
    render();
    requestAnimationFrame(resize);
    refreshProjects();
    return { widget, minWidth: 390, minHeight: 220 };
}

app.registerExtension({
    name: "endorphin.EtsyProjectSelector",
    getCustomWidgets() {
        return { ENDORPHIN_ETSY_PROJECT_SELECTOR: createProjectSelector };
    },
});
