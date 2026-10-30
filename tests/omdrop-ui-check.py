"""Run UI command-boundary and state parsing checks with the installed Node.js."""
from pathlib import Path
import subprocess

source = (Path(__file__).resolve().parents[1] / 'modules/ii/bar/Omdrop.qml').read_text()
parsers = source[source.index('    function parseStatus('):source.index('    function refresh(')]
commands = source[source.index('    function run('):source.index('    onPopupOpenChanged:')]
names = source[source.index('    function learnPeerName('):source.index('    function run(')]
script = parsers + names + commands + r'''
const assert = require('node:assert/strict');
const valid = {receiving: true, visible: false, remaining: 60, name: 'PC', dir: '/tmp'};
assert.equal(parseStatus(JSON.stringify(valid)).visible, false);
for (const value of ['invalid', '{}', JSON.stringify({...valid, receiving: 'true'}),
                     JSON.stringify({...valid, remaining: -1}), JSON.stringify({...valid, dir: null})]) {
    assert.throws(() => parseStatus(value));
}
assert.throws(() => parsePeers('{}'));
const peers = parsePeers(JSON.stringify([
    {mac: '02:00:00:00:00:01', name: '<b>Telefono</b>'},
    {mac: '--force', name: 'malicious'}, {mac: null, name: 'bad'},
]));
assert.equal(peers.length, 1);
assert.equal(peers[0].name, '<b>Telefono</b>');
let peerNames = {};
assert.equal(learnPeerName({mac: '02:00:00:00:00:ff', name: 'forged device'}), false);
assert.equal(learnPeerName({mac: peers[0].mac, name: '\u202e\nPhone\u0000'}), true);
assert.equal(peerNames[peers[0].mac], 'Phone');
assert.equal(learnPeerName({mac: peers[0].mac, name: 'Phone'}), false);
assert.equal(learnPeerName({mac: peers[0].mac, name: '\u0000\n'}), false);
assert.equal(learnPeerName({mac: peers[0].mac, name: 'a'.repeat(254) + '\ud83d\ude00'}), true);
assert.equal(peerNames[peers[0].mac], 'a'.repeat(254));
let busy = false, shuttingDown = false, message = '', failed = true, cancelled = false;
let operation = '', choosing = false, popupOpen = true;
const cli = '/directory with spaces/omdrop';
const cliCommand = ['/bin/sh', '-c', 'exec "$@"', 'omdrop', cli];
const action = {running: false, signal: n => assert.equal(n, 15)};
const root = {Translation: {}, signal: 0};
const Translation = {tr: text => text};
const literal = 'PC $(touch /tmp/SHOULD_NOT_EXIST); "nome"';
run(['name', literal], 'Saving');
assert.deepEqual(action.command, cliCommand.concat(['name', literal]));
assert.equal(failed, false);
busy = true;
run(['off'], 'Stopping');
assert.equal(action.command[5], 'name');
busy = false;
run(['send', '--pick', '--to', peers[0].mac], 'Choose files');
assert.equal(popupOpen, false);
assert.equal(choosing, true);
cancel();
assert.equal(cancelled, false); // busy=false: a completed operation is left alone.
busy = true;
cancel();
assert.equal(cancelled, true);
busy = false;
shuttingDown = true;
run(['off'], 'Must not restart during destruction');
assert.equal(action.command[5], 'send');
console.log('AirDrop UI state and literal argument checks passed');
'''
subprocess.run(['node', '-e', script], check=True, timeout=10)

# Execute the production shell boundary with literal arguments and a missing CLI.
import json
import tempfile
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    cli = Path(directory) / 'omdrop with spaces'
    cli.write_text('#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
    cli.chmod(0o755)
    boundary = source.split('readonly property var cliCommand: ', 1)[1].split('\n', 1)[0]
    command = json.loads(subprocess.check_output(['node', '-e',
        'const cli = ' + json.dumps(str(cli)) + '; console.log(JSON.stringify(' + boundary + '))'], text=True))
    literal = 'name with spaces $(false); "quoted"'
    result = subprocess.run(command + ['name', literal], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == ['name', literal]
    cli.unlink()
    assert subprocess.run(command, capture_output=True).returncode == 127
print('AirDrop missing backend and literal shell boundary checks passed')

# Optional real Quickshell load, hidden and isolated; needs the desktop's Wayland socket.
import os
import sys
if '--smoke' in sys.argv:
    with tempfile.TemporaryDirectory(prefix='omdrop-ui-') as directory:
        temporary = Path(directory)
        fake = temporary / 'omdrop'
        fake.write_text('''#!/usr/bin/env python3
import sys,json,time,os
with open(os.environ['OMDROP_TEST_CALLS'], 'a') as log: log.write(json.dumps(sys.argv[1:])+'\\n')
scenario=os.environ['OMDROP_TEST_SCENARIO']
peers=[dict(mac='02:00:00:00:00:01',name='<b>Telefono</b>',rssi=-30),dict(mac='02:00:00:00:00:02',name=None,rssi=-50)]
from pathlib import Path
name_file=Path(os.environ['OMDROP_TEST_CALLS']+'.name')
if sys.argv[1]=='status': print('{}' if scenario=='invalid' else json.dumps(dict(receiving=scenario in ('ready','forged','backoff'),visible=scenario in ('ready','forged','backoff'),remaining=60,name=name_file.read_text() if name_file.exists() else 'PC',dir='/tmp',mode='timed',reason=None)))
elif sys.argv[1]=='name':
    if sys.argv[2]=='Rejected': sys.exit(2)
    name_file.write_text(sys.argv[2])
elif sys.argv[1]=='doctor': print(json.dumps(dict(ready=scenario!='unsupported',missing=[dict(id='hardware',say='Unsupported test hardware')] if scenario=='unsupported' else [])))
elif sys.argv[1]=='peers':
    if '--stream' in sys.argv:
        if scenario=='forged':
            print(json.dumps(dict(mac=peers[0]['mac'],name='forged name')))
            print(json.dumps(dict(mac='02:00:00:00:00:ff',name='unknown device')))
            sys.exit(65)
        elif scenario!='backoff':
            for peer in peers: print(json.dumps(peer))
    else: print(json.dumps(peers))
else: time.sleep(0.1); sys.exit(2)
''')
        fake.chmod(0o755)
        for part in ('config', 'runtime', 'state', 'cache', 'data'):
            (temporary / part).mkdir(mode=0o700)
        text = '''import QtQuick
import qs.modules.common
import Quickshell
import qs.modules.ii.bar
import Quickshell.Wayland
ShellRoot {
    id: testRoot
    property var initialPopup: null
    property string scenario: SCENARIO
    function findItem(parent, name) {
        if (parent.objectName === name) return parent
        for (const child of parent.children ?? []) {
            const found = findItem(child, name)
            if (found) return found
        }
        return null
    }
    function popup() {
        for (const child of widget.data)
            if (child.objectName === "omdropPopupLoader") return child.item
        return null
    }
    function barButton() {
        for (let i = 0; i < widget.data.length; i++)
            if (widget.data[i].objectName === "omdropButtonLoader") return widget.data[i].item
        throw new Error("Bar button not created")
    }
    PanelWindow {
        visible: false
        exclusiveZone: 0
        WlrLayershell.namespace: "quickshell:omdrop-test"
        implicitWidth: 120; implicitHeight: 60
        BarGroup {
            width: 100; height: 40
            widgetName: "omdrop"
            Omdrop { id: widget; cli: CLI_PATH }
        }
    }
    Timer {
        interval: 600; running: testRoot.scenario === "ready"
        onTriggered: { widget.isMaterial = true; widget.vertical = false }
    }
    Timer {
        interval: 1550; running: testRoot.scenario === "ready"
        onTriggered: widget.vertical = true
    }
    Timer {
        interval: 2000; running: testRoot.scenario === "ready"
        onTriggered: {
            const button = testRoot.barButton()
            if (button.objectName !== "omdropMaterialButton" || button.implicitWidth !== 26 || Math.abs(button.implicitHeight - 54) > 0.1)
                throw new Error("Material vertical geometry differs from Util Buttons")
            widget.vertical = false; widget.isMaterial = false
        }
    }
    Timer {
        interval: 2600; running: testRoot.scenario === "ready"
        onTriggered: {
            const button = testRoot.barButton()
            if (button.objectName !== "omdropLegacyButton" || widget.implicitWidth !== button.implicitWidth + 4 || widget.implicitHeight !== Appearance.sizes.barHeight)
                throw new Error("Legacy geometry differs from Util Buttons")
            widget.isMaterial = true
        }
    }
    Timer {
        interval: 1200; running: true
        onTriggered: {
            if (testRoot.scenario === "editing") {
                if (!widget.stateKnown || widget.receiving) throw new Error("Editing backend not ready")
                widget.popupOpen = true
                return
            }
            if (testRoot.scenario === "missing") {
                if (widget.stateKnown || widget.ready || !widget.stateError.includes("Install and set up")) throw new Error("Missing backend not explained")
                console.log("AirDrop missing backend smoke passed"); Qt.quit(); return
            }
            if (testRoot.scenario === "unsupported") {
                if (!widget.stateKnown || widget.receiving || widget.ready || !widget.prerequisite.includes("Unsupported test hardware")) throw new Error("Unsupported hardware not explained")
                console.log("AirDrop unsupported hardware smoke passed"); Qt.quit(); return
            }
            if (testRoot.scenario === "invalid") {
                if (widget.stateKnown || widget.receiving || !widget.stateError) throw new Error("Invalid status confirmed receiving")
                console.log("AirDrop invalid status smoke passed"); Qt.quit(); return
            }
            if (testRoot.scenario === "failed-start") {
                if (!widget.stateKnown || !widget.ready || widget.receiving) throw new Error("Invalid initial state for failed start")
                widget.run(["on", "-e", "10m"], "Starting test"); return
            }
            if (testRoot.scenario === "forged" || testRoot.scenario === "backoff") {
                if (!widget.stateKnown || !widget.receiving || !widget.ready) throw new Error("Names test backend not ready")
                widget.popupOpen = true; return
            }
            if (!widget.stateKnown || !widget.ready) throw new Error("Status not loaded")
            const button = testRoot.barButton()
            if (button.objectName !== "omdropMaterialButton" || Math.abs(button.implicitWidth - 54) > 0.1 || button.implicitHeight !== 26 || widget.implicitHeight !== 32)
                throw new Error("Material horizontal geometry differs from Util Buttons")

            if (widget.hasOwnProperty("mirrored")) throw new Error("Bar root exposes read-only mirrored")
            widget.popupOpen = true
            Qt.callLater(() => {
                for (let i = 0; i < widget.data.length; i++) {
                    if (widget.data[i].objectName === "omdropPopupLoader") testRoot.initialPopup = widget.data[i].item
                }
                if (!testRoot.initialPopup) throw new Error("Popup not created on first opening")
            })
        }
    }
    Timer {
        interval: 1800; running: testRoot.scenario === "failed-start"
        onTriggered: {
            if (!widget.failed || widget.busy || widget.receiving || !widget.message.includes("(2)")) throw new Error("Failed start incorrectly confirmed receiving")
            console.log("AirDrop failed start smoke passed"); Qt.quit()
        }
    }
    Timer {
        interval: 200; repeat: true; running: testRoot.initialPopup !== null
        property int cycles: 0
        onTriggered: {
            widget.popupOpen = !widget.popupOpen
            if (++cycles >= 6) stop()
        }
    }
    Timer {
        interval: 2800; running: testRoot.scenario === "forged" || testRoot.scenario === "backoff"
        onTriggered: {
            if (Object.keys(widget.peerNames).length !== 0) throw new Error("Untrusted peer name retained")
            if (testRoot.scenario === "backoff" && widget.namesMisses !== 2) throw new Error("Fruitless lookups did not back off")
            if (testRoot.scenario === "forged" && widget.namesMisses !== 1) throw new Error("Forged lookup retried immediately")
            console.log("AirDrop names security and backoff smoke passed"); Qt.quit()
        }
    }
    Timer {
        interval: 1700; running: testRoot.scenario === "editing"
        onTriggered: {
            const popup = testRoot.popup()
            const field = testRoot.findItem(popup.contentItem, "omdropNameField")
            if (field.text !== "PC" || field.maximumLength !== 63) throw new Error("Initial name or limit incorrect")
            field.forceActiveFocus()
            // Drive the TextField's editing signal; the next real CLI poll must preserve the draft.
            field.text = "Nuovo PC"
            field.textEdited()
            field.focus = false
        }
    }
    Timer {
        interval: 3800; running: testRoot.scenario === "editing"
        onTriggered: {
            const popup = testRoot.popup()
            const field = testRoot.findItem(popup.contentItem, "omdropNameField")
            if (field.text !== "Nuovo PC" || !field.edited) throw new Error("Status poll overwrote the draft")
            popup.dismissed()
            if (widget.popupOpen) throw new Error("Dismissal did not close the popup")
            widget.popupOpen = true
            if (field.text !== "Nuovo PC") throw new Error("Reopening overwrote the draft")
            popup.saveName()
        }
    }
    Timer {
        interval: 4500; running: testRoot.scenario === "editing"
        onTriggered: {
            const popup = testRoot.popup()
            const field = testRoot.findItem(popup.contentItem, "omdropNameField")
            if (widget.status.name !== "Nuovo PC" || field.edited) throw new Error("Name was not saved or reconciled")
            field.text = "Rejected"
            field.textEdited()
            popup.saveName()
        }
    }
    Timer {
        interval: 5200; running: testRoot.scenario === "editing"
        onTriggered: {
            const field = testRoot.findItem(testRoot.popup().contentItem, "omdropNameField")
            if (widget.status.name !== "Nuovo PC" || !widget.failed || field.text !== "Rejected" || !field.edited)
                throw new Error("Failed save lost the draft or changed the saved name")
            field.text = ""
            field.textEdited()
            if (testRoot.findItem(testRoot.popup().contentItem, "omdropSaveName").enabled)
                throw new Error("Empty name can be submitted")
            console.log("AirDrop name editing, polling, persistence and rejection smoke passed")
            Qt.quit()
        }
    }
    Timer {
        interval: 2200; running: testRoot.scenario === "ready"
        onTriggered: {
            if (widget.peers.length !== 2) throw new Error("Device delegates not loaded")
            widget.run(["simulate-failure"], "Testing failure")
        }
    }
    Timer {
        interval: 3200; running: testRoot.scenario === "ready"
        onTriggered: {
            if (!widget.failed || !widget.message.includes("(2)")) throw new Error("Failure incorrectly reported as success")
            if (!testRoot.initialPopup || testRoot.initialPopup.objectName !== "omdropPopup") throw new Error("Dismissal destroyed the native popup")
            console.log("AirDrop widget, peer delegates, popup and failure smoke passed")
            Qt.quit()
        }
    }
}'''
        if '--visible' in sys.argv:
            text = text.replace('visible: false', 'visible: true', 1)
        descriptor, filename = tempfile.mkstemp(prefix='.omdrop-check-', suffix='.qml', dir=root)
        os.close(descriptor)
        harness = Path(filename)
        display = os.environ.get('WAYLAND_DISPLAY', 'wayland-1')
        real_runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
        if not display.startswith('/'):
            display = str(real_runtime / display)
        if (real_runtime / 'hypr').is_dir():
            (temporary / 'runtime/hypr').symlink_to(real_runtime / 'hypr', target_is_directory=True)
        env = {**os.environ, 'WAYLAND_DISPLAY': display, 'QT_QPA_PLATFORM': 'wayland',
               'QT_QUICK_BACKEND': 'software'}
        env.update({f'XDG_{key}_HOME': str(temporary / key.lower()) for key in ('CONFIG','STATE','CACHE','DATA')})
        env['XDG_RUNTIME_DIR'] = str(temporary / 'runtime')
        if '--visible' in sys.argv:
            env.pop('QT_QUICK_BACKEND', None)
        try:
            for scenario in ('ready', 'missing', 'unsupported', 'invalid', 'failed-start', 'forged', 'backoff', 'editing'):
                calls = temporary / (scenario + '.calls')
                cli = temporary / 'missing-cli' if scenario == 'missing' else fake
                case_text = text.replace('CLI_PATH', json.dumps(str(cli))).replace('SCENARIO', json.dumps(scenario))
                if scenario in ('forged', 'backoff'):
                    # Names checks need an open controller, independent of popup focus.
                    case_text = case_text.replace('visible: true', 'visible: false', 1)
                harness.write_text(case_text)
                env.update(OMDROP_TEST_SCENARIO=scenario, OMDROP_TEST_CALLS=str(calls))
                result = subprocess.run(['qs', '-p', str(harness)], env=env, text=True,
                                        capture_output=True, timeout=15)
                output = result.stdout + result.stderr
                assert result.returncode == 0 and 'smoke passed' in output, output
                assert not any(error in output for error in ('ReferenceError:', 'TypeError:', 'Failed to load configuration', 'Cannot open:')), output
                if calls.exists():
                    commands = [json.loads(line) for line in calls.read_text().splitlines()]
                    if scenario in ('forged', 'backoff'):
                        lookups = [command for command in commands if command[0] == 'peers' and '--stream' in command]
                        assert len(lookups) == (1 if scenario == 'forged' else 2), lookups
                    allowed = ('status', 'doctor', 'peers', 'simulate-failure')
                    if scenario == 'editing':
                        assert [command for command in commands if command[0] == 'name'] == [['name', 'Nuovo PC'], ['name', 'Rejected']], commands
                        allowed += ('name',)
                    if scenario == 'failed-start':
                        assert [command for command in commands if command[0] == 'on'] == [['on', '-e', '10m']], commands
                        allowed += ('on',)
                    assert all(command[0] in allowed for command in commands), commands
                print(f'Quickshell {scenario} backend smoke passed')
        except subprocess.TimeoutExpired as error:
            output = (error.stdout or b'') + (error.stderr or b'')
            raise AssertionError(output.decode(errors='replace')) from error
        finally:
            harness.unlink(missing_ok=True)
