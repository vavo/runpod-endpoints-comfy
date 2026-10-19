import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
const code = readFileSync(new URL('../web/forma-pricing-v041.js', import.meta.url), 'utf8').replace(/^import .*;\n/gm, '');
function fixture() {
    let extension;
    const connected = [];
    const target = { inputs: [{ name: 'workflow.model.image.value', type: 'IMAGE', link: null }] };
    const source = { connect: (...args) => connected.push(args) };
    const app = { registerExtension: e => { extension = e; }, graph: { getNodeById: id => ({ 1: target, 3: source }[id]) } };
    vm.runInNewContext(code, { app, api: {}, requestAnimationFrame: cb => cb() });
    const graph = { nodes: [{ id: 1, type: 'FormaVideo', inputs: [{ ...target.inputs[0], link: 3 }] }], links: [[3, 3, 0, 1, 4, 'IMAGE']] };
    return { extension, target, connected, graph };
}
test('restore a saved Forma link by input name after dynamic slot reordering', async () => {
    const f = fixture(); f.extension.beforeConfigureGraph(f.graph); await f.extension.afterConfigureGraph();
    assert.equal(f.connected.length, 1); assert.equal(f.connected[0][2], 0);
    await f.extension.afterConfigureGraph(); assert.equal(f.connected.length, 1);
});
test('never replace a live connection or reconnect a changed media type', async () => {
    for (const change of [{ link: 9 }, { type: 'AUDIO' }]) {
        const f = fixture(); f.extension.beforeConfigureGraph(f.graph); Object.assign(f.target.inputs[0], change);
        await f.extension.afterConfigureGraph(); assert.equal(f.connected.length, 0);
    }
});
test('never restore links for unrelated node types', async () => {
    const f = fixture(); f.graph.nodes[0].type = 'OtherNode';
    f.extension.beforeConfigureGraph(f.graph); await f.extension.afterConfigureGraph(); assert.equal(f.connected.length, 0);
});
