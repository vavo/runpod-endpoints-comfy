import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// A custom renderer deliberately bypasses ComfyUI's persisted setting values.
function renderKeySettings() {
    const root = document.createElement("div");
    root.style.cssText = "display:flex;flex-direction:column;gap:12px;min-width:280px;max-width:540px";
    const help = document.createElement("p");
    help.textContent = "Create a key at forma.cam → Account settings → API keys. Paste it below and save. No restart needed.";
    const input = document.createElement("input");
    input.type = "password";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.maxLength = 70;
    input.placeholder = "forma_…";
    input.setAttribute("aria-label", "Forma API key");
    input.style.cssText = "padding:10px;width:100%;box-sizing:border-box";
    const status = document.createElement("p");
    status.setAttribute("role", "status");
    const controls = document.createElement("div");
    controls.style.cssText = "display:flex;gap:12px";
    const save = document.createElement("button");
    save.textContent = "Save and test key";
    const remove = document.createElement("button");
    remove.textContent = "Remove saved key";
    for (const button of [save, remove]) {
        button.type = "button";
        button.style.cssText = "padding:8px 12px;cursor:pointer;border:1px solid var(--border-color);border-radius:6px";
    }
    const note = document.createElement("p");
    note.textContent = "Saved privately on this ComfyUI server, outside workflows and browser storage. Everyone who can use this instance can spend the connected account's balance. Protect access to your ComfyUI server. Removing the saved key does not revoke it in Forma.";
    controls.append(save, remove);
    root.append(help, input, controls, status, note);
    let managed = false;
    let configured = false;
    function buttons(busy = false) {
        input.disabled = busy || managed;
        save.disabled = busy || managed;
        remove.disabled = busy || managed || !configured;
    }
    async function request(method = "GET", key) {
        const response = await api.fetchApi("/forma/settings/key", {
            method, cache: "no-store",
            headers: { "Content-Type": "application/json", "X-Forma-Settings": "1" },
            ...(key === undefined ? {} : { body: JSON.stringify({ key }) }),
        });
        const body = await response.json();
        if (!response.ok) throw new Error(body.error || "Could not update Forma settings.");
        managed = body.managed;
        configured = body.configured;
        status.textContent = managed ? "Key managed by your host's environment settings."
            : configured ? "A Forma key is saved on this server." : "No Forma key saved.";
    }
    save.onclick = async () => {
        const key = input.value.trim();
        input.value = "";
        buttons(true);
        status.textContent = "Checking key with Forma…";
        try {
            await request("POST", key);
            status.textContent = "Key verified and saved. Ready to generate.";
        } catch (error) { status.textContent = error.message; }
        finally { buttons(); }
    };
    remove.onclick = async () => {
        input.value = "";
        buttons(true);
        try { await request("DELETE"); }
        catch (error) { status.textContent = error.message; }
        finally { buttons(); }
    };
    buttons(true);
    request().catch(() => { status.textContent = "Could not read Forma status. Restart ComfyUI after installing this update."; })
        .finally(() => buttons());
    return root;
}

app.registerExtension({
    name: "Forma.AccountSettings",
    settings: [{
        id: "Forma.Account.APIKey",
        name: "API key",
        category: ["Forma", "Account", "API key"],
        defaultValue: null,
        type: renderKeySettings,
        telemetry: { trackChanges: false },
    }],
});
