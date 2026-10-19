import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function signature(node, seen = new Set()) {
    if (!node || seen.has(node.id) || seen.size >= 64) return null;
    seen.add(node.id);
    return [node.id, node.widgets?.filter(w => w.options?.serialize !== false).map(w => [w.name, w.value]),
        node.inputs?.map(input => {
            const link = node.graph?.links[input.link];
            return [input.name, link?.origin_slot, signature(node.graph?.getNodeById(link?.origin_id), seen)];
        })];
}

function showResult(message) {
    const dialog = document.createElement("dialog");
    dialog.style.cssText = "max-width:480px;padding:24px;background:var(--comfy-menu-bg,#222);color:var(--input-text,#eee);border:1px solid #666;border-radius:10px";
    const title = document.createElement("h3");
    title.textContent = "Forma price check";
    const text = document.createElement("p");
    text.style.whiteSpace = "pre-wrap";
    text.textContent = message;
    const close = document.createElement("button");
    close.textContent = "Close";
    close.onclick = () => dialog.close();
    dialog.append(title, text, close);
    document.body.append(dialog);
    dialog.addEventListener("close", () => dialog.remove(), { once: true });
    dialog.showModal();
}

// DynamicCombo rebuilds native sockets during graph configuration on some frontends.
// Restore only the links explicitly saved for Forma inputs, once configuration ends.
let savedLinks = [];
app.registerExtension({
    beforeConfigureGraph(data) {
        savedLinks = [];
        const links = new Map((data.links || []).filter(Array.isArray).map(link => [link[0], link]));
        for (const node of data.nodes || []) {
            if (!["FormaImage", "FormaVideo"].includes(node.type)) continue;
            for (const input of node.inputs || []) {
                const link = links.get(input.link);
                if (link) savedLinks.push({ target: node.id, name: input.name, type: input.type, source: link[1], slot: link[2] });
            }
        }
    },
    async afterConfigureGraph() {
        await new Promise(requestAnimationFrame);
        for (const link of savedLinks) {
            const target = app.graph.getNodeById(link.target), source = app.graph.getNodeById(link.source);
            const slot = target?.inputs?.findIndex(input => input.name === link.name && input.type === link.type);
            if (source && slot >= 0 && target.inputs[slot].link == null) source.connect(link.slot, target, slot);
        }
        savedLinks = [];
    },
    name: "Forma.PriceCheck",
    beforeRegisterNodeDef(nodeType, nodeData) {
        if (!["FormaImage", "FormaVideo"].includes(nodeData.name)) return;
        const created = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            created?.apply(this, arguments);
            let busy = false, checked = null, expires = 0;
            const price = this.addWidget("text", "Price (USD)", "Not checked", () => {}, { serialize: false });
            price.disabled = true;
            price.inputEl && (price.inputEl.readOnly = true);
            const checkPrice = async () => {
                if (busy) return;
                busy = true;
                checked = null;
                price.value = "Checking…";
                this.setDirtyCanvas(true);
                try {
                    const snapshot = JSON.stringify(signature(this));
                    const { output } = await app.graphToPrompt();
                    const target = output[String(this.id)];
                    if (!target) throw new Error("Enable this Forma node before checking its price.");
                    const sources = {};
                    const collect = inputs => {
                        for (const value of Object.values(inputs || {})) {
                            if (!Array.isArray(value) || value.length !== 2) continue;
                            const id = String(value[0]);
                            if (sources[id] || !output[id]) continue;
                            if (Object.keys(sources).length >= 64) throw new Error("Connect a Load node directly for this price check.");
                            sources[id] = output[id];
                            collect(output[id].inputs);
                        }
                    };
                    collect(target.inputs);
                    const response = await api.fetchApi("/forma/price", {
                        method: "POST", cache: "no-store",
                        headers: { "Content-Type": "application/json", "X-Forma-Settings": "1" },
                        body: JSON.stringify({ ...target, sources }),
                    });
                    let result;
                    try { result = await response.json(); }
                    catch { throw new Error("Restart ComfyUI after updating the Forma nodes, then refresh this page."); }
                    if (!response.ok) throw new Error(result.error || "Could not check the price.");
                    if (snapshot !== JSON.stringify(signature(this))) throw new Error("Inputs changed during the check. Check price again.");
                    checked = snapshot;
                    expires = result.expires;
                    const amount = `$${(result.cents / 100).toFixed(2)} USD`;
                    const cap = target.inputs.max_cost_cents;
                    price.value = `${amount} · ${result.cents <= cap ? "within limit" : "above limit"}`;
                    showResult(`${amount} for this node's current inputs.\nYour limit: $${(cap / 100).toFixed(2)} USD.\n\nNo inference was started or charged. Local references may have been uploaded to your Forma library. Run checks the price again before purchasing.`);
                } catch (error) {
                    price.value = "Check failed";
                    showResult(error.message);
                } finally {
                    busy = false;
                    this.setDirtyCanvas(true);
                }
            };
            const button = document.createElement("button");
            button.textContent = "Check price";
            button.setAttribute("aria-label", "Check Forma price");
            button.style.cssText = "width:100%;height:28px;cursor:pointer;border:1px solid #666;border-radius:5px;background:var(--comfy-input-bg,#333);color:var(--input-text,#eee)";
            button.onclick = checkPrice;
            const action = this.addDOMWidget("Check price", "forma_price_button", button, { serialize: false });
            action.computeSize = () => [0, 32];
            const configure = this.onConfigure;
            this.onConfigure = function () {
                const result = configure?.apply(this, arguments);
                checked = null;
                price.value = "Not checked";
                return result;
            };
            const draw = this.onDrawForeground;
            this.onDrawForeground = function () {
                if (checked && (Date.now() >= expires || JSON.stringify(signature(this)) !== checked)) {
                    price.value = "Changed / expired — check again";
                    checked = null;
                }
                return draw?.apply(this, arguments);
            };
        };
    },
});
