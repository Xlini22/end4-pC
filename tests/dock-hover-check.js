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

const dock = fs.readFileSync(path.join(__dirname, '../modules/ii/dock/Dock.qml'), 'utf8');
const revealBody = dock.match(/property bool reveal: \{([\s\S]*?)\n            \}/)[1];
const dockRoot = {fullscreenOnThisMonitor: false, position: 'bottom', screen: {name: 'test'}};
const dockMouseArea = {containsMouse: false}, riseArea = {containsMouse: false};
const magnify = {entries: []};
const reveal = new Function('root', 'dockRoot', 'dockContextMenu', 'Config', 'dockMouseArea', 'riseArea',
    'GlobalStates', 'activeApps', 'dragSlots', 'ToplevelManager', 'DockMagnify', 'fullscreenOnThisMonitor', revealBody);
const visible = () => reveal({pinned: false}, dockRoot, {isOpen: false},
    {options:{dock:{hoverToReveal:true}}}, dockMouseArea, riseArea,
    {isFrameHovered:()=>false}, {requestDockShow:false}, {requestDockShow:false},
    {activeToplevel:{activated:true}}, magnify, dockRoot.fullscreenOnThisMonitor);
for (const fullscreen of [false, true]) {
    dockRoot.fullscreenOnThisMonitor = fullscreen;
    dockMouseArea.containsMouse = true;
    assert(visible());
    dockMouseArea.containsMouse = false;
    riseArea.containsMouse = true;
    assert(visible(), 'Moving over the magnified upper icons must not hide or move the dock');
    riseArea.containsMouse = false;
    assert(!visible());
    const item = {launching:true, QsWindow:{window:dockRoot}};
    magnify.entries = [{item}];
    assert(visible(), 'A launch animation must keep its own dock visible');
    item.QsWindow.window = {};
    assert(!visible(), 'A launch on another monitor must not reveal this dock');
    item.QsWindow.window = dockRoot;
    item.launching = false;
    assert(!visible(), 'Finishing the launch must release auto-hide');
    magnify.entries = [];
}
console.log('Dock reveal: expanded hover area, launch retention, fullscreen and monitor isolation passed.');
