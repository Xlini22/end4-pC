// Run: node tests/topbar-popup-check.js (no compositor or GPU access).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname, '..', name), 'utf8');
const island = read('modules/ii/bar/DynamicIsland.qml');
const popup = read('modules/common/widgets/StyledPopup.qml');
const expression = source => source.match(/readonly property bool popupInteractionReady: ([^\n]*(?:\n +&&[^\n]*)*)/)[1];
const islandReady = expression(island);
const slotReady = expression(island.slice(island.indexOf('component SideWidgetDelegate:')));
const groupsReady = expression(island.slice(island.indexOf('component SideWidgets:')));
const mediaReady = expression(island.slice(island.indexOf('id: mediaSideRoot')));
const clockReady = expression(read('modules/ii/bar/ClockWidget.qml'));
const resourcesReady = expression(read('modules/ii/bar/Resources.qml'));
const ancestorReady = popup.match(/readonly property bool barInteractionReady: \{([\s\S]*?)\n    \}/)[1];
const canOpen = popup.match(/readonly property bool canOpen: ([^\n]+)/)[1];
const openChanged = popup.match(/onCanOpenChanged: ([^\n]+)/)[1];
const requestChanged = popup.match(/onShouldShowChanged: ([^\n]+)/)[1];
const changed = popup.match(/onCanShowChanged: \{([\s\S]*?)\n    \}/)[1];
const run = (source, context) => vm.runInNewContext(source, context);
const animation = running => ({animation: {running}});
const root = {shouldShow: true, barInteractionReady: false, canShow: false, popupCreated: false, item: null, closing: false};

function check({interaction = true, layout = false, reveal = false, width = false,
    media = false, clock = false, resources = false, primary = false, bar = true, center = true} = {}, expected) {
    const clockWidget = {popupInteractionReady: run(clockReady, {dateAnimation: animation(clock)})};
    const resourcesWidget = {popupInteractionReady: run(resourcesReady, {valueAnimation: animation(resources)})};
    const mediaWidget = {popupInteractionReady: run(mediaReady, {mediaWidthAnimation: animation(media)})};
    const widgets = [clockWidget, resourcesWidget, mediaWidget].map(widget => ({
        popupInteractionReady: run(slotReady, {
            layoutAnimation: animation(layout), revealAnimation: animation(reveal), slotWidthAnimation: animation(width),
            regularLoader: {item: widget}, mediaLoader: {item: null},
        }),
    }));
    const groups = run(groupsReady, {leftGroup: {children: widgets}, rightGroup: {children: []}});
    const ready = run(islandReady, {root: {componentInteractionReady: interaction},
        primaryWidthAnimation: animation(primary), leftWidgets: {popupInteractionReady: groups}, rightWidgets: {popupInteractionReady: true}, centerLoader: {item: {popupInteractionReady: center}}});
    root.hoverTarget = {parent: {popupInteractionReady: ready, parent: {popupInteractionReady: bar, parent: null}}};
    root.barInteractionReady = run(`(function() {${ancestorReady}})()`, {root});
    root.canOpen = run(canOpen, {root});
    run(openChanged, {root});
    run(changed, {root});
    assert.equal(root.canShow, expected, 'Popup must await all expansion phases and widget animations');
    assert.equal(root.popupCreated, expected, 'Do not allocate a popup window during expansion');
}

check({interaction: false}, false); // Incoming pointer, before the original 350ms interaction timer.
check({layout: true, reveal: true}, false); // First phase of staged expansion.
check({layout: false, reveal: true}, false); // 350ms passed; the content is still expanding.
for (const name of ['width', 'media', 'clock', 'resources', 'primary']) check({[name]: true}, false);
check({center: false}, false); // Centered widget is still expanding.
check({bar: false}, false); // Auto-hidden bar still sliding into view.
check({}, true); // Both phases and all actual animations have finished.
root.barInteractionReady = false;
root.canOpen = run(canOpen, {root});
run(openChanged, {root});
assert(root.canShow, 'A later track/layout update must not close an already opened popup');
root.shouldShow = false;
root.item = {};
run(requestChanged, {root});
run(changed, {root});
assert(!root.canShow && root.closing, 'Leaving the target must preserve animated close');
assert.match(popup, /visible: root\.canShow \|\| root\.closing/);
assert.match(popup, /function onCanShowChanged\(\)/, 'Cached popup animations must use the same gate');
assert(!/visible: root\.shouldShow|when: [^\n]*root\.shouldShow|function onShouldShowChanged\(\)/.test(popup),
    'MediaPopup overrides must not bypass the gate in visibility, geometry or animation');
root.shouldShow = true;
root.barInteractionReady = false;
root.canOpen = run(canOpen, {root});
run(openChanged, {root});
assert(!root.canShow, 'Cached popups must also wait when re-entering from outside the bar');
root.barInteractionReady = true;
root.canOpen = run(canOpen, {root});
run(openChanged, {root});
assert(root.canShow, 'A stationary pointer must open the popup when expansion completes');
console.log('Top bar: staged/simultaneous expansion, centered widgets, deferred creation, cached reopening and normal close passed.');
