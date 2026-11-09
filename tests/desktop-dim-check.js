// Run: node tests/desktop-dim-check.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname, '..', name), 'utf8');
const background = read('modules/ii/background/Background.qml');
const expression = background.match(/readonly property bool desktopDimmed: ([\s\S]*?)\n\n/)[1];
const win = {mapped: true, hidden: false, monitor: 1, size: [800, 600], workspace: {id: 3}, pinned: false};
const context = {
    Config: {options: {bar: {dimDesktopWhenWindowsOpen: true}}},
    WM: {compositor: 'hyprland'},
    GlobalStates: {screenLocked: false, startupLockPending: false},
    monitor: {id: 1, activeWorkspace: {id: 3}}, dimSpecialWorkspace: 0,
    HyprlandData: {windowList: []},
};
const dimmed = windows => {
    context.HyprlandData.windowList = windows;
    return vm.runInNewContext(expression, context);
};
assert.equal(dimmed([]), false, 'An unobstructed desktop keeps its original brightness');
assert.equal(dimmed([win]), true);
assert.equal(dimmed([{...win, hidden: true}]), false);
assert.equal(dimmed([{...win, mapped: false}]), false);
assert.equal(dimmed([{...win, size: [0, 600]}]), false);
assert.equal(dimmed([{...win, size: null}]), false);
assert.equal(dimmed([{...win, monitor: 2}]), false, 'Each monitor decides independently');
assert.equal(dimmed([{...win, workspace: {id: 4}}]), false);
assert.equal(dimmed([{...win, workspace: {id: 4}, pinned: true}]), true);
assert.equal(dimmed([{...win, workspace: {id: -99}}]), false);
context.dimSpecialWorkspace = -99;
assert.equal(dimmed([{...win, workspace: {id: -99}}]), true);
assert.equal(dimmed([{...win, workspace: {id: -98}}]), false);
context.monitor.activeWorkspace.id = 4;
assert.equal(dimmed([win]), false, 'Moving to an empty workspace restores brightness');
context.monitor.activeWorkspace.id = 3;
context.GlobalStates.screenLocked = true;
assert.equal(dimmed([win]), false);
context.GlobalStates.screenLocked = false;
context.GlobalStates.startupLockPending = true;
assert.equal(dimmed([win]), false);
context.GlobalStates.startupLockPending = false;
context.Config.options.bar.dimDesktopWhenWindowsOpen = false;
assert.equal(dimmed([win]), false, 'The setting disables the effect');
context.Config.options.bar.dimDesktopWhenWindowsOpen = true;
context.WM.compositor = 'niri';
assert.equal(dimmed([win]), false);
context.WM.compositor = 'hyprland';
context.monitor = null;
assert.equal(dimmed([win]), false);
const opacityExpression = background.match(/opacity: (bgRoot.desktopDimmed[^\n]+)/)[1];
for (const [percent, expected] of [[0, 0], [20, .2], [50, .5], [75, .75], [100, 1], [-10, 0], [120, 1]]) {
    context.Config.options.bar.desktopDimPercent = percent;
    context.bgRoot = {desktopDimmed: true};
    assert.equal(vm.runInNewContext(opacityExpression, context), expected);
    context.bgRoot.desktopDimmed = false;
    assert.equal(vm.runInNewContext(opacityExpression, context), 0);
}
const settings = read('modules/ii/settings/pages/BarConfig.qml');
assert.match(settings, /property bool groupedListCollapsed: !Config.options.bar.dimDesktopWhenWindowsOpen\s+visible: !groupedListCollapsed/);
assert.match(settings, /onMoved: Config.options.bar.desktopDimPercent = Math.round\(value\)/);
console.log('Desktop dim: empty/occupied workspaces, per-monitor visibility, pinned/special windows, lock, toggle and configurable 0–100% opacity passed.');
