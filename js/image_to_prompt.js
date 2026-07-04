import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "endorphin.ImageToPrompt",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "EndorphinImageToPrompt") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                // Store a persistent reference to the original widgets array
                this.allWidgets = [...this.widgets];
                
                const modeWidget = this.widgets.find(w => w.name === "mode");
                const advancedWidgetNames = [
                    "temperature", 
                    "top_p", 
                    "num_beams", 
                    "repetition_penalty", 
                    "frame_count", 
                    "use_torch_compile", 
                    "device"
                ];
                
                const updateVisibility = () => {
                    if (!modeWidget) return;
                    const isAdvanced = modeWidget.value === "advanced";
                    
                    // Re-filter active widgets list. Hidden widgets are removed from active drawing list.
                    this.widgets = this.allWidgets.filter(w => {
                        if (advancedWidgetNames.includes(w.name)) {
                            return isAdvanced;
                        }
                        return true;
                    });
                    
                    // Resize node height dynamically and set dirty for redraw
                    const sz = this.computeSize();
                    sz[0] = Math.max(sz[0], 450); // Set minimum width to 450px for spacious layout
                    this.setSize(sz);
                    if (this.graph) {
                        this.graph.setDirtyCanvas(true, true);
                    }
                };
                
                if (modeWidget) {
                    const origCallback = modeWidget.callback;
                    modeWidget.callback = function (value) {
                        const cbResult = origCallback ? origCallback.apply(this, arguments) : undefined;
                        updateVisibility();
                        return cbResult;
                    };
                    
                    // Run initial check after loading
                    setTimeout(updateVisibility, 100);
                }
                
                return r;
            };
        }
    }
});
