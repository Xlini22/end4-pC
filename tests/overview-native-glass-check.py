"""Run python3 tests/overview-native-glass-check.py PATH_TO_PLUGIN in a Wayland session.
Uses a temporary nested compositor; the desktop plugin remains untouched.
"""
from pathlib import Path
import json
import subprocess
import sys
import time
import statistics

workspace_stress = '--workspaces' in sys.argv
plugin = Path(sys.argv[1]).resolve(strict=True)
repo = Path(__file__).resolve().parents[1]
fixture_path = repo / 'tests/native-glass-motion-check.py'
OVERVIEW_FIXTURE = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Io
import qs
import qs.services
import qs.modules.common
ShellRoot {
    id: root
    property bool measuring: false
    property int step: 0
    property double lastFrame: 0
    property var frames: []
    TestOverview { id: overview }
    Connections {
        target: overview.testPanel.contentItem.Window.window
        function onFrameSwapped() {
            if (!root.measuring) return
            const now = Date.now()
            if (root.lastFrame) root.frames.push(now - root.lastFrame)
            root.lastFrame = now
        }
    }
    Timer {
        id: paging; interval: 380; repeat: true
        onTriggered: {
            const span = Math.max(1, overview.testGrid.pageCount - 1)
            const next = root.step % (2 * span)
            overview.testGrid.showPage(next <= span ? next : 2 * span - next)
            if (++root.step >= 20) { stop(); finish.start() }
        }
    }
    Timer { id: finish; interval: 400; onTriggered: root.measuring = false }
    FloatingWindow {
        visible: true
        title: "overview-backdrop"
        implicitWidth: 960; implicitHeight: 640
        color: "#304050"
        Rectangle { x: 100; y: 100; width: 300; height: 400; color: "#336699" }
        Rectangle { x: 450; y: 100; width: 300; height: 400; color: "#449955" }
    }
    Timer {
        interval: 700; running: Config.ready
        onTriggered: {
            Config.options.background.widgets.glass.enable = true
            Config.options.background.widgets.glass.nativePlugin = true
            Config.options.background.widgets.glass.source = "windows"
            Config.options.background.widgets.glass.enhanced = true
            Config.options.overview.scale = .1
            GlobalStates.overviewOpen = true
        }
    }
    IpcHandler {
        target: "overview-check"
        function open(value: bool): void { GlobalStates.overviewOpen = value }
        function enabled(value: bool): void { Config.options.background.widgets.glass.elements.overview.enable = value }
        function globalEnabled(value: bool): void { Config.options.background.widgets.glass.enable = value }
        function search(value: string): void { overview.testPanel.searchingText = value }
        function page(value: int): void { overview.testGrid.showPage(value) }
        function fade(value: real): void { overview.testColumn.opacity = value }
        function restoreFade(): void {
            overview.testColumn.opacity = Qt.binding(() => overview.testPanel.contentShown || overview.preview ? 1 : 0)
        }
        function measure(): void { root.frames = []; root.lastFrame = 0; root.step = 0; root.measuring = true; paging.start() }
        function stressOptics(): void {
            Config.options.overview.scale = .18
            const p = Config.options.background.widgets.glass.elements.overview
            p.rim = 40; p.refraction = 170; p.blur = 2.5; p.automaticDarkening = true
        }
        function optics(): void {
            Config.options.background.widgets.glass.elements.overview.rim = 19
            Config.options.background.widgets.glass.elements.overview.blur = 12
            Config.options.background.widgets.glass.elements.overview.darkening = 25
        }
        function state(): string {
            return JSON.stringify({measuring:root.measuring,frames:root.frames,active:GlassCompositor.enhancedActive,
                profiles:GlassCompositor.overviewProfilesAvailable, applied:GlassCompositor.profilesApplied,
                captures:GlassLayers.backdropConsumers, writes:GlassCompositor.regionWrites,
                materials:GlassCompositor.glassItems.filter(g=>g.profileKey === "overview" && g.nativeRegion()).length,
                opacities:GlassCompositor.glassItems.filter(g=>g.profileKey === "overview").map(g=>g.nativeRegion()?.values[13]),
                regions:GlassCompositor.regionsApplied,
                overview:Config.options.background.widgets.glass.elements.overview.rim,
                bar:Config.options.background.widgets.glass.elements.bar.rim})
        }
    }
}
'''
# ponytail: reuse the existing nested-compositor lifecycle instead of maintaining a second launcher.
source = fixture_path.read_text().split("plugins = json.loads(control('plugin', 'list', '-j'))", 1)[0]
source = source.replace("(shell / 'shell.qml').write_text(FIXTURE)", '''overview_source = (repo / 'modules/ii/overview/Overview.qml').read_text()
    overview_source = overview_source.replace('import qs\\n', 'import qs\\nimport qs.modules.ii.overview\\n', 1)
    overview_source = overview_source.replace('id: overviewScope', 'id: overviewScope\\n    property alias testPanel: panelWindow\\n    property alias testGrid: applicationGrid\\n    property alias testColumn: columnLayout', 1)
    (shell / 'TestOverview.qml').write_text(overview_source)
    (shell / 'shell.qml').write_text(OVERVIEW_FIXTURE)''')
sys.argv = [str(fixture_path), '--plugin', str(plugin)]
namespace = {'__file__': str(fixture_path), 'OVERVIEW_FIXTURE': OVERVIEW_FIXTURE}
exec(compile(source, str(fixture_path), 'exec'), namespace)
env, shell = namespace['nested_env'], namespace['shell']

def ipc(name, *args):
    result = subprocess.run(['qs','-p',str(shell),'ipc','call','overview-check',name,*args],
                            env=env,capture_output=True,text=True,timeout=5)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()

def state():
    return json.loads(ipc('state'))

for _ in range(100):
    try:
        current = state()
        if current['active'] and current['profiles'] and current['materials'] == 3:
            break
    except (AssertionError, ValueError):
        pass
    time.sleep(.1)
assert current['active'] and current['profiles'] and current['materials'] == 3, (current, (namespace['base']/'fixture.log').read_text())
assert current['captures'] == 0, current
ipc('optics'); time.sleep(.5)
current = state()
assert current['overview'] == 19 and current['bar'] == 24 and 'overview 1 0.19' in current['applied'], current
for name in ['enabled', 'globalEnabled']:
    ipc(name,'false'); time.sleep(.4)
    assert state()['materials'] == 0, (name,state())
    ipc(name,'true'); time.sleep(.5)
    assert state()['materials'] == 3, (name,state())
ipc('search','fire'); time.sleep(.6)
assert state()['materials'] == 1, state()
ipc('search',''); time.sleep(.5)
assert state()['materials'] == 3, state()
# A transparent mapped frame must stay known; removing its regions activates legacy glass.
ipc('fade', '0'); time.sleep(.4)
current = state()
assert current['materials'] == 3 and current['opacities'] == [0, 0, 0], current
assert 'quickshell:overview' in current['regions'], current
ipc('restoreFade'); time.sleep(.4)
assert state()['materials'] == 3, state()
for page in ['1','2','0']:
    ipc('page',page); time.sleep(.4)
assert state()['materials'] == 3 and state()['captures'] == 0, state()
subprocess.run(['grim','/tmp/overview-native-open.png'],env=env,check=True,timeout=10)
for _ in range(3):
    ipc('open','false'); time.sleep(.6)
    current=state()
    assert current['materials'] == 0 and current['captures'] == 0, current
    time.sleep(.5)
    assert state()['writes'] == current['writes'], 'Hidden overview continues sending glass regions'
    ipc('open','true'); time.sleep(.6)
    assert state()['materials'] == 3, state()
log=(namespace['base']/'fixture.log').read_text()
assert not any(error in log for error in ['TypeError','ReferenceError','Binding loop','Unable to assign']), log
print('Native Overview: 3 materials, 7 profiles, independent optics, global/per-target toggles, search, paging, 3 reopen cycles and idle hidden state passed')
if workspace_stress:
    ipc('stressOptics'); time.sleep(.6)
    control = namespace['control']
    for case in ('window', 'empty', 'window-to-empty', 'empty-other-group'):
        ipc('open', 'false'); time.sleep(.4)
        control('dispatch', 'workspace', '1' if case.startswith('window') else '2' if case == 'empty' else '11')
        time.sleep(.5)
        ipc('open', 'true'); time.sleep(.7)
        if case == 'window-to-empty':
            control('dispatch', 'workspace', '2'); time.sleep(.5)
        before = state()
        ipc('measure')
        deadline = time.monotonic() + 20
        while state()['measuring']:
            assert time.monotonic() < deadline, case
            time.sleep(.3)
        current = state()
        frames = sorted(current['frames'])
        assert frames and current['materials'] == 3 and current['captures'] == 0, (case, current)
        assert current['writes'] == before['writes'], 'Stationary glass keeps updating during paging'
        print(case, json.dumps({'frames':len(frames),'medianMs':statistics.median(frames),
                               'p95Ms':frames[int(len(frames)*.95)],'maxMs':max(frames)}), flush=True)
    ipc('open', 'false')
