// Run: node tests/settings-backdrop-stability-check.js (CPU only; patches temporary copies).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const repo = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'settings-backdrop-check-'));
try {
    for (const name of ['modules/common/widgets/WindowGlass.qml', 'modules/ii/settings/Settings.qml']) {
        fs.mkdirSync(path.dirname(path.join(temporary, name)), {recursive: true});
        fs.copyFileSync(path.join(repo, name), path.join(temporary, name));
    }
    const file = 'modules/common/widgets/WindowGlass.qml';
    if (fs.readFileSync(path.join(temporary, file), 'utf8').includes('property bool stableBackdropCapture: false')) {
        execFileSync('git', ['apply', '--reverse', path.join(repo, 'patches/settings-backdrop-stability.patch')], {cwd: temporary});
    }
    const original = fs.readFileSync(path.join(temporary, file), 'utf8');
    execFileSync('git', ['apply', '--check', path.join(repo, 'patches/settings-backdrop-stability.patch')], {cwd: temporary});
    execFileSync('git', ['apply', path.join(repo, 'patches/settings-backdrop-stability.patch')], {cwd: temporary});
    const patched = fs.readFileSync(path.join(temporary, file), 'utf8');
    const settings = fs.readFileSync(path.join(temporary, 'modules/ii/settings/Settings.qml'), 'utf8');
    assert.match(settings, /id: settingsGlass\s+stableBackdropCapture: true/);
    assert.match(patched, /property bool stableBackdropCapture: false/);
    const helpers = patched.match(/function window(?:Visible|Intersects)\([^)]*\) \{[\s\S]*?\n    \}/g).join('\n');
    const functions = vm.runInNewContext(helpers + '\n({windowVisible, windowIntersects})');
    function included(source, client, x, stable = true, monitorX = 0, workspace = 3, special = 0) {
        const expression = source.match(/readonly property bool included: ([\s\S]*?)\n                        x:/)[1];
        const root = {...functions, stableBackdropCapture: stable, scr: {width: 1920, height: 1080},
            backdropMonitor: {x: monitorX, y: 0, activeWorkspace: {id: workspace}}, specialWorkspace: special,
            winX: 0, winY: 0, sceneRect: {x, y: 0, width: 200, height: 200}};
        return vm.runInNewContext('(' + expression + '\n)', {root, client,
            Quickshell: {processId: 100}, Qt: {rect: (x,y,width,height) => ({x,y,width,height})}});
    }
    const client = {mapped: true, hidden: false, pid: 42, workspace: {id: 3}, at: [500, 0], size: [400, 700]};
    // Reproduce the old detach/reattach at the edge; exercise the actual QML binding.
    assert.equal(included(original, client, 299), false);
    assert.equal(included(original, client, 301), true);
    for (const x of [0, 299, 300, 301, 700, 900, 1200, 700, 299, 0]) {
        assert.equal(included(patched, client, x), true, 'Dragging must not clear/restart a capture');
    }
    assert.equal(included(patched, client, 299, false), false, 'Other materials keep the existing culling');
    assert.equal(included(patched, client, 301, false), true);
    for (const excluded of [null, {...client, pid: 100}, {...client, hidden: true},
        {...client, mapped: false}, {...client, workspace: {id: 4}}, {...client, size: [0, 700]},
        {...client, at: [1920, 0]}, {...client, at: [-400, 0]}]) {
        assert.equal(included(patched, excluded, 301), false, 'Privacy and monitor filtering must remain');
    }
    assert.equal(included(patched, {...client, at: [2420, 0]}, 0, true, 1920), true);
    assert.equal(included(patched, {...client, pinned: true}, 0, true, 0, 4), true);
    assert.equal(included(patched, {...client, workspace: {id: -7}}, 0, true, 0, 3, -7), true);
    for (const name of ['modules/common/widgets/WindowGlass.qml', 'modules/ii/settings/Settings.qml']) {
        execFileSync(process.env.QMLFORMAT || '/usr/lib/qt6/bin/qmlformat', [path.join(temporary, name)], {stdio: ['ignore', 'ignore', 'pipe']});
    }
    console.log('PASS: old capture churn reproduced; staged QML keeps captures during drag, preserves filtering and parses. No live files changed.');
} finally {
    fs.rmSync(temporary, {recursive: true, force: true});
}
