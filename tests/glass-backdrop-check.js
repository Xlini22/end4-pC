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
