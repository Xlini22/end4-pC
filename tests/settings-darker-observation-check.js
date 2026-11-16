// Run: node tests/settings-darker-observation-check.js. Temporary files and parsing only; no rendering.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const repo = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'darker-observation-'));
try {
    const names = ['modules/common/widgets/FrostedGlass.qml', 'modules/common/widgets/WindowGlass.qml', 'modules/ii/settings/Settings.qml'];
    for (const name of names) {
        const destination = path.join(temporary, name);
        fs.mkdirSync(path.dirname(destination), {recursive: true});
        fs.copyFileSync(path.join(repo, name), destination);
    }
    const patch = fs.readFileSync(path.join(repo, 'patches/settings-darker-observation.patch'), 'utf8');
    if (fs.readFileSync(path.join(temporary, names[0]), 'utf8').includes('function darkeningStatus()')) {
        execFileSync('git', ['apply', '--reverse', path.join(repo, 'patches/settings-darker-observation.patch')], {cwd: temporary});
    }
    execFileSync('git', ['apply', path.join(repo, 'patches/settings-darker-observation.patch')], {cwd: temporary});
    const [frosted, window, settings] = names.map(name => fs.readFileSync(path.join(temporary, name), 'utf8'));
    const body = frosted.match(/function status\(\) \{([\s\S]*?)\n            \}/)[1];
    const state = {motionSerial: 5, sampleSerial: 3, busy: false, settled: {running: true},
        fade: {running: false}, blend: .4, target: {live: false}, previous: {live: false}};
    const before = JSON.stringify(state);
    const status = vm.runInNewContext('(function() {' + body + '})()', state);
    assert.equal(status.waiting, true);
    assert.equal(status.targetLive, false);
    assert.equal(status.motionSerial, 5);
    assert.equal(status.blend, .4);
    assert.equal(JSON.stringify(state), before, 'Inspecting state must have no side effects');
    state.settled.running = false;
    state.fade.running = true;
    assert.equal(vm.runInNewContext('(function() {' + body + '})()', state).fading, true);
    const functionBody = frosted.match(/function darkeningStatus\(\) \{([\s\S]*?)\n    \}/)[1];
    const root = {debounceDarkening: true, automaticDarkening: 1, sourceRect: {x: 12, y: 20, width: 980, height: 720}};
    const query = item => vm.runInNewContext('(function() {' + functionBody + '})()', {root, lumaState: {item}});
    assert.equal(query(null).detail, null, 'A closed/unloaded material must be reported explicitly');
    assert.equal(query({status: () => status}).detail, status);
    assert.match(window, /fallbackGlass\.item\?\.glassMaterial\?\.darkeningStatus\(\)/);
    assert.match(settings, /darker: settingsGlass\.darkeningStatus\(\)/);
    const added = patch.split('\n').filter(line => line.startsWith('+') && !line.startsWith('+++')).join('\n');
    assert.doesNotMatch(added, /Timer\s*\{|Animation\s*\{|scheduleUpdate\(|console\./);
    for (const name of names) {
        execFileSync('/usr/lib/qt6/bin/qmlformat', [path.join(temporary, name)], {stdio: ['ignore', 'ignore', 'pipe']});
    }
    console.log('PASS: status exposes waiting/fade/texture flags without side effects; unloaded state handled; QML parses. No live files changed.');
} finally {
    fs.rmSync(temporary, {recursive: true, force: true});
}
