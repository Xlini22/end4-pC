"""Run: python3 tests/settings-darker-debounce-check.py. Static checks only: no Qt window or rendering."""
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='settings-darker-check-') as directory:
    temporary = Path(directory)
    for name in ['modules/common/widgets/FrostedGlass.qml', 'modules/common/widgets/WindowGlass.qml',
                 'modules/common/widgets/shaders/liquidLens.vert', 'modules/common/widgets/shaders/liquidLens.frag',
                 'modules/common/widgets/shaders/glassLuma.vert', 'modules/common/widgets/shaders/glassLuma.frag',
                 'modules/common/widgets/shaders/glassLumaBlend.frag']:
        if not (repo/name).exists():
            continue
        destination = temporary / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((repo / name).read_bytes())
    widgets = temporary/'modules/common/widgets'
    if 'function darkeningStatus()' in (widgets/'FrostedGlass.qml').read_text():
        subprocess.run(['git', 'apply', '--reverse',
                        '--include=modules/common/widgets/FrostedGlass.qml',
                        '--include=modules/common/widgets/WindowGlass.qml',
                        str(repo/'patches/settings-darker-observation.patch')], cwd=temporary, check=True)
    patch = str(repo/'patches/settings-darker-debounce.patch')
    if 'property bool debounceDarkening: false' in (widgets/'FrostedGlass.qml').read_text():
        subprocess.run(['git', 'apply', '--reverse', patch], cwd=temporary, check=True)
    original_fragment = (widgets/'shaders/liquidLens.frag').read_text()
    original_vertex = (widgets/'shaders/liquidLens.vert').read_text()
    subprocess.run(['git', 'apply', patch], cwd=temporary, check=True)
    assert (widgets/'shaders/liquidLens.frag').read_text().replace(
        '    float holdDarkening;\n    float darkeningBlend;\n', '') == original_fragment, 'Optical fragment code must remain unchanged'
    assert (widgets/'shaders/liquidLens.vert').read_text().split('    float lod =')[1] == original_vertex.split('    float lod =')[1], 'Keep the optimized four-probe vertex path'
    for source in widgets.glob('*.qml'):
        subprocess.run(['/usr/lib/qt6/bin/qmlformat', str(source)], stdout=subprocess.DEVNULL, check=True)
    for source in (widgets/'shaders').iterdir():
        subprocess.run(['/usr/lib/qt6/bin/qsb', '--qt6', '-o', str(source)+'.qsb', str(source)], check=True)
    check = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const qml = fs.readFileSync(process.argv[1], 'utf8');
const moved = qml.match(/function moved\(\) \{([\s\S]*?)\n            \}/)[1];
const timer = qml.match(/onTriggered: \{([\s\S]*?)\n                \}/)[1];
function callback(id, end) {
    return qml.slice(qml.indexOf('id: ' + id), end ? qml.indexOf('id: ' + end) : undefined)
        .match(/onScheduledUpdateCompleted: \{([\s\S]*?)\n                \}/)[1];
}
let now = 0, deadline = 0, oldRequests = 0, newRequests = 0, fades = 0;
const state = {motionSerial: 0, sampleSerial: -1, busy: false, blend: .42};
const settled = {running: false, restart() {this.running = true; deadline = now + 1500;}};
const fade = {running: true, stop() {this.running = false;}, start() {this.running = true; fades++;}};
const context = vm.createContext({...state, settled, fade,
    previous: {scheduleUpdate() {oldRequests++;}}, target: {scheduleUpdate() {newRequests++;}}});
context.state = context;
context.restart = () => settled.restart();
function run(code) {vm.runInContext('(function() {' + code + '\n})()', context);}
function advance(ms) {
    now += ms;
    if (settled.running && now >= deadline) {settled.running = false; run(timer);}
}
const oldDone = callback('previous');
const newDone = callback('target', 'blended');
run(moved);
assert.equal(fade.running, false);
assert.equal(context.blend, .42, 'Movement freezes the current fade value');
advance(1400); assert.equal(oldRequests, 0);
run(moved); advance(1400); assert.equal(oldRequests, 0, 'Every movement restarts the wait');
advance(100); assert.equal(oldRequests, 1);
run(oldDone); assert.equal(context.blend, 0); assert.equal(newRequests, 1);
run(newDone); assert.equal(fades, 1);
advance(10000); assert.equal(oldRequests, 1, 'No periodic update');
// Ignore a sample that completes after movement resumes.
run(moved); advance(1500); run(moved); run(oldDone);
assert.equal(newRequests, 1); assert.equal(context.busy, false); assert.equal(fades, 1);
advance(1500); run(oldDone); run(moved); run(newDone);
assert.equal(fades, 1, 'A stale target must not restart a fade');
assert.equal(context.busy, false);
advance(1500); run(oldDone); run(newDone); assert.equal(fades, 2);
assert.match(qml, /id: capture[\s\S]*?live: true/);
assert.match(qml, /interval: 1500\s+repeat: false/);
assert.match(qml, /duration: 800/);
assert.match(qml, /recursive: true\s+live: false/);
assert.doesNotMatch(qml, /RGBA16F|FrameAnimation/);
assert.match(qml, /function onSourceRectChanged\(\) \{ state.moved\(\) \}/);
console.log('PASS: debounce/restart, interrupted fade, stale callbacks, no periodic timer; live optical capture preserved.');
"""
    subprocess.run(['node', '-e', check, str(widgets/'FrostedGlass.qml')], check=True)
    assert 'debounceDarkening: root.profileKey === "settings"' in (widgets/'WindowGlass.qml').read_text()
    print('PASS: patch applies, QML parses, five shader assets bake; optical fragment and original vertex sampling unchanged. No rendering performed.')
