// Run: node tests/glass-contrast-check.js (no compositor or GPU access).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../services/GlassCompositor.qml'), 'utf8');
const rgba = (r, g, b, a = 1) => ({r, g, b, a});
const sample = {name: 'quickshell:settings', monitor: 'test', width: 800, height: 600,
    rect: [0, 0, 800, 600], columns: 32, rows: 24, luma: Array(768).fill(0)};
const context = vm.createContext({Qt: {rgba, rect: (x, y, width, height) => ({x, y, width, height})},
    Config: {options: {background: {widgets: {glass: {elements: {settings: {darkening: 0, automaticDarkening: false}}}}}}},
    contrastMaterialSnapshot: {regions:[]}, uniformDarkeningAvailable: true, darkeningAvailable: true, contrastActive: true, contrastTick: 1, contrastSamples: [sample]});
for (const name of ['foreground', 'localLuminance', 'validContrast']) {
    const fn = source.match(new RegExp('    function ' + name + '\\([^]*?\\n    \\}'));
    assert.ok(fn, name);
    vm.runInContext(fn[0], context);
}
const win = {screen: {name: 'test'}, width: 800, height: 600, contentItem: {}, WlrLayershell: {namespace: 'quickshell:settings'}};
const label = {visible: true, width: 100, height: 20, QsWindow: {window: win},
    mapToItem: () => ({x: 40, y: 40, width: 100, height: 20})};
const base = rgba(.85, .92, .96, 1);
const ink = previous => context.foreground(label, base, previous);
assert.equal(context.validContrast(sample), true);
for (const bad of [{...sample, luma: [0]}, {...sample, luma: Array(768).fill(256)},
    {...sample, rect: [0, 0, 0, 600]}, {...sample, name: 'quickshell:bar'}, {...sample, width: NaN}])
    assert.equal(context.validContrast(bad), false);
assert.deepEqual(ink(), rgba(231 / 255, 237 / 255, 242 / 255), 'Black backdrop requires softened light ink');
sample.luma.fill(255);
assert.deepEqual(ink(), rgba(27 / 255, 34 / 255, 41 / 255), 'White backdrop requires softened dark ink');
const dimming = context.Config.options.background.widgets.glass.elements.settings;
dimming.darkening = 100;
assert.ok(ink().r > .9, 'Black manual wash requires light ink even over a white source');
dimming.darkening = 0;
dimming.automaticDarkening = true;
assert.ok(ink().r > .9, 'Automatic wash must not leave dark ink on the darkened background');
context.darkeningAvailable = false;
assert.ok(ink().r < .2, 'Old engine must not adjust ink for an unavailable background wash');
context.darkeningAvailable = true;
dimming.automaticDarkening = false;
base.a = .7;
assert.equal(ink().a, base.a, 'Preserve requested text opacity');
base.a = 1;
// A single panel must allow opposite inks simultaneously, without splitting an individual label.
for (let y = 0; y < 24; ++y) for (let x = 0; x < 32; ++x) sample.luma[y * 32 + x] = x < 16 ? 0 : 255;
assert.ok(ink().r > .9);
label.mapToItem = () => ({x: 640, y: 40, width: 100, height: 20});
assert.ok(ink().r < .2);
// A bright stripe between the global probes still needs dark ink; selecting its own card changes the wash.
for (let y=0; y<24; ++y) for (let x=0; x<32; ++x) sample.luma[y*32+x] = x >= 25 && x <= 30 ? 255 : 0;
dimming.automaticDarkening = true;
assert.ok(ink().r < .2, 'Mixed box must retain dark ink over the still-bright side');
context.uniformDarkeningAvailable = false;
assert.ok(ink().r > .9, 'Old per-pixel engine retains its original ink calculation');
context.uniformDarkeningAvailable = true;
context.contrastMaterialSnapshot = {regions:[{win, priority:0, values:[600,0,200,600]}]};
assert.ok(ink().r > .9, 'Foreground must use the selected card reference, not the entire window');
context.contrastMaterialSnapshot = {regions:[]};
dimming.automaticDarkening = false;
// Prefer AA when available; softened inks cannot cover every mid-grey at 4.5:1.
const linear = v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
const luma = c => .2126 * linear(c.r) + .7152 * linear(c.g) + .0722 * linear(c.b);
for (let value = 0; value <= 255; ++value) {
    sample.luma.fill(value);
    const color = ink(), bg = value / 255, fg = luma(color);
    const contrast = y => (Math.max(bg, y) + .05) / (Math.min(bg, y) + .05);
    const best = Math.max(contrast(luma(rgba(231 / 255, 237 / 255, 242 / 255))),
        contrast(luma(rgba(27 / 255, 34 / 255, 41 / 255))));
    assert.ok(contrast(fg) >= (best >= 4.5 ? 4.5 : best / 1.15), `Wrong ink at ${value}`);
    assert.equal(ink(color).r, color.r, `Ink oscillates on a static grey at ${value}`);
}
sample.luma.fill(50);
assert.ok(ink(rgba(.045, .065, .075)).r < .2);
assert.ok(ink(rgba(.92, .96, .98)).r > .9, 'Hysteresis must avoid threshold flicker');
context.contrastActive = false;
assert.equal(ink(), base);
context.contrastActive = true;
win.WlrLayershell.namespace = 'quickshell:bar';
assert.equal(ink(), base, 'Do not change unrelated surfaces');
win.WlrLayershell.namespace = 'quickshell:settings';
label.visible = false;
assert.equal(ink(), base, 'Do not process hidden labels');
console.log('Adaptive glass text: softened inks, black/white/mixed backgrounds, stable greys and fallback passed');
