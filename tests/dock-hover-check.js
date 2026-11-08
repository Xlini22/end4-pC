// Run: node tests/dock-hover-check.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../modules/common/widgets/DragApps.qml'), 'utf8');
const start = source.indexOf('onHoveredChanged: {') + 'onHoveredChanged: {'.length;
assert(start >= 'onHoveredChanged: {'.length, 'Pinned dock hover handler must exist');
let end = start, depth = 1;
while (depth && end < source.length) {
    const char = source[end++];
    if (char === '{') depth++;
    if (char === '}') depth--;
}
assert.equal(depth, 0, 'Hover handler must have balanced braces');
const hover = new Function('root', 'dockBtn', 'hovered', source.slice(start, end - 1));
const root = {lastHoveredButton: null, buttonHovered: false};
const open = {appToplevel: {toplevels: [{}]}};
const closed = {appToplevel: null};
const previewWanted = () => root.buttonHovered && (root.lastHoveredButton?.appToplevel?.toplevels.length ?? 0) > 0;

hover(root, open, true);
assert(previewWanted(), 'Hovering an open app must request its preview');
hover(root, closed, true);
hover(root, open, false);
assert.equal(root.lastHoveredButton, closed);
assert(root.buttonHovered, 'A late exit from the open app must not clear the closed app hover');
assert(!previewWanted(), 'A closed app must not show the previous app preview');
hover(root, open, true);
hover(root, closed, false);
assert.equal(root.lastHoveredButton, open);
assert(previewWanted(), 'Returning rapidly to the open app must request its preview despite a late exit from the closed app');
hover(root, open, false);
assert(!previewWanted(), 'Leaving the current app must dismiss its preview');
console.log('Dock hover: open/closed/open switching, late exit events and normal dismissal passed.');
