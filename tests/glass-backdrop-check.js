// Run: node tests/glass-backdrop-check.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../modules/common/widgets/WindowGlass.qml'), 'utf8');
const functions = source.match(/function window(?:Visible|Intersects|Order)\([^)]*\) \{[\s\S]*?\n    \}/g);
assert.equal(functions.length, 3);
const {windowVisible, windowIntersects, windowOrder} = vm.runInNewContext(
    functions.join('\n') + '\n({windowVisible, windowIntersects, windowOrder})');
const client = {mapped: true, hidden: false, pid: 42, workspace: {id: 3},
    at: [1920, 40], size: [500, 300], focusHistoryID: 0};
assert.equal(windowVisible(client, 3, 0, 100), true);
assert.equal(windowVisible(null, 3, 0, 100), false);
assert.equal(windowVisible({...client, hidden: true}, 3, 0, 100), false);
assert.equal(windowVisible({...client, mapped: false}, 3, 0, 100), false);
assert.equal(windowVisible(client, 3, 0, 42), false); // Never capture ourselves.
assert.equal(windowVisible(client, 4, 0, 100), false); // An inactive workspace stays private.
assert.equal(windowVisible({...client, pinned: true}, 4, 0, 100), true);
assert.equal(windowVisible({...client, workspace: {id: -7}}, 3, -7, 100), true);
assert.equal(windowVisible({...client, size: [0, 10]}, 3, 0, 100), false);
assert.equal(windowVisible({...client, size: null}, 3, 0, 100), false);
const area = {x: 20, y: 30, width: 200, height: 100};
assert.equal(windowIntersects(client, 1920, 0, area), true); // Second monitor origin.
assert.equal(windowIntersects({...client, at: [-1280, -200]}, -1280, -240, area), true);
assert.equal(windowIntersects(client, 0, 0, area), false);
assert.equal(windowIntersects({...client, at: [220, 40]}, 0, 0, area), false); // Touching is not overlapping.
assert.equal(windowIntersects({...client, at: [219, 40]}, 0, 0, area), true);
assert.equal(windowIntersects(null, 0, 0, area), false);
assert.ok(windowOrder(client, 0) > windowOrder({...client, focusHistoryID: 2}, 0));
assert.ok(windowOrder({...client, floating: true}, 0) > windowOrder(client, 0));
assert.ok(windowOrder({...client, fullscreen: 2}, 0) > windowOrder({...client, floating: true}, 0));
assert.ok(windowOrder({...client, workspace: {id: -7}}, -7) > windowOrder({...client, fullscreen: 2}, -7));
console.log('Glass backdrop: workspace filtering, self-exclusion, monitor alignment and window order passed');

const rect = (x, y, width, height) => ({x, y, width, height});
const regionSource = source.match(/    function nativeRegion\(\) \{[\s\S]*?\n    \}/)[0];
const geometry = vm.createContext({
    Qt: {rect}, enhancedNative: true, tracking: true, floating: false,
    width: 100, height: 80, win: {contentItem: {}, screen: {name: 'test'}, WlrLayershell: {namespace: 'test'}},
    root: {opacity: 1}, parent: null, nativeClip: null, mapToItem: () => rect(10, 20, 100, 80),
    topLeftRadius: 12, topRightRadius: 12, bottomRightRadius: 12, bottomLeftRadius: 12,
    flareLeft: 0, flareRight: 0, hangLeft: 0, hangRight: 0, edge: 0, frost: 8,
    GlassCompositor: {frostedAvailable: true},
});
vm.runInContext(regionSource, geometry);
function region(clip = null) {
    geometry.nativeClip = clip && {width: clip.width, height: clip.height, mapToItem: () => clip};
    const result = vm.runInContext('nativeRegion()', geometry);
    return result && Array.from(result.values);
}
assert.deepEqual(region().slice(0, 8), [10, 20, 100, 80, 12, 12, 12, 12]);
assert.deepEqual(region(rect(0, 40, 300, 200)).slice(0, 8), [10, 40, 100, 60, 0, 0, 12, 12]);
assert.deepEqual(region(rect(0, 0, 70, 200)).slice(0, 8), [10, 20, 60, 80, 12, 0, 0, 12]);
assert.equal(region(rect(0, 120, 300, 200)), null);
assert.equal(region(rect(110, 0, 300, 200)), null);
assert.equal(region(rect(0, 40, 300, 200)).at(-1), 8);
for (const height of [7.471, 7.4718, 7.472, 1.001]) {
    const slice = region(rect(0, 100 - height, 300, height));
    assert.ok(slice.slice(4, 8).every(radius => radius <= Math.min(slice[2], slice[3]) / 2),
        'IPC rounding must not push radii outside the visible slice');
}
assert.equal(region(rect(0, 99.9996, 300, .0004)), null);
geometry.mapToItem = () => rect(10, 20, 200, 160);
assert.equal(region(rect(0, 40, 300, 200)).at(-1), 16); // Cropping must not change material scale.
console.log('Native satin rows: viewport clipping, corner radii and preserved blur scale passed');

geometry.floating = true;
assert.equal(region(), null, 'Old backends must not receive floating-card regions');
geometry.GlassCompositor.windowFrostedAvailable = true;
assert.equal(vm.runInContext('nativeRegion().name', geometry), 'quickshell:dashboard');
assert.equal(region(rect(0, 40, 300, 200)).at(-1), 16);
geometry.frost = 0;
assert.equal(region(), null, 'The outer floating window retains compositor rounding, not a card rectangle');
console.log('Dashboard cards: capability gate, window-local namespace and clipped frost passed');
