"""Check real Dashboard frosted cards in one isolated compositor.
Quarantined after a hard system freeze. Explicit reproduction only:
python3 tests/native-dashboard-check.py --plugin /path/to/hyprglass.so --reproduce-r18
"""
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from PIL import Image

if '--reproduce-r18' not in sys.argv:
    raise SystemExit('Dashboard native glass is quarantined after a system freeze; reproduction requires --reproduce-r18 and explicit approval for a GPU test.')

fixture = Path(__file__).with_name('native-glass-motion-check.py')
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.settings as Settings
ShellRoot {
    id: root
    property var probe: null
    Settings.Dashboard { id: dashboard }
    Window { id: red; visible:true; title:"glass-red"; color:"red"; width:1000; height:1100 }
    Window { id: blue; visible:true; title:"glass-blue"; color:"blue"; width:1000; height:1100 }
    PanelWindow {
        id: backdrop
        anchors { top:true; bottom:true; left:true; right:true }
        exclusiveZone:0; color:"black"
        WlrLayershell.namespace:"end4:dashboard-background"
        WlrLayershell.layer:WlrLayer.Bottom
        Repeater {
            id: stripes
            model: Math.ceil(parent.width / 8)
            Rectangle { required property int index; x:index*8; width:8; height:parent.height; color:index%2 ? "white" : "black" }
        }
    }
    Component {
        id: probeComponent
        DashboardCard { width:180; height:90; cardRadius:24; color:"transparent" }
    }
    function find(item, predicate) {
        if (!item) return null
        if (predicate(item)) return item
        if (item.item) { const found=find(item.item,predicate); if (found) return found }
        for (const child of item.children ?? []) { const found=find(child,predicate); if (found) return found }
        return null
    }
    function window() { return GlassCompositor.glassItems.find(item=>item.floating && item.win?.title === "illogical-impulse Settings")?.win ?? null }
    function materials(item, result) {
        if (item.nativeRegion !== undefined && item.frost>0) result.push(item)
        for (const child of item.children ?? []) materials(child,result)
    }
    IpcHandler {
        target:"dashboard-check"
        function open(): void {
            red.visible=false; blue.visible=false
            GlassCompositor.windowFrostedAvailable=true
            Config.options.settings.style="dashboard"
            Config.options.background.widgets.glass.enhanced=true
            Config.options.background.widgets.glass.haze=1
            GlobalStates.dashboardPage=0
            GlobalStates.settingsOpen=true
        }
        function settings(): void {
            const pane=find(window().contentItem,item=>item.pageBoxes !== undefined)
            pane.goToPage(4)
        }
        function scroll(): void {
            const pane=find(window().contentItem,item=>item.pageBoxes !== undefined)
            pane.scrollSettingsBy(300)
        }
        function burst(): string {
            const view=find(window().contentItem,item=>item.dashboardSettingsViewport === true)
            const before=GlassCompositor.regionWrites
            for (let i=0;i<80;i++) view.contentY+=1
            return JSON.stringify({before,after:GlassCompositor.regionWrites})
        }
        function probe(): void {
            const win=window()
            const pane=find(win.contentItem,item=>item.pageBoxes !== undefined)
            pane.visible=false
            root.probe=probeComponent.createObject(win.contentItem,{x:win.width/2-90,y:win.height/2-45})
        }
        function close(): void {
            if (root.probe) { root.probe.destroy(); root.probe=null }
            GlobalStates.settingsOpen=false
        }
        function state(): string {
            const win=window(), cards=[]
            if (win) materials(win.contentItem,cards)
            return JSON.stringify({ready:!!win, width:win?.width,height:win?.height,
                capable:GlassCompositor.windowFrostedAvailable, captures:GlassLayers.backdropConsumers,
                background:[backdrop.width,backdrop.height,stripes.count],
                rejected:GlassCompositor.regionsRejected, writes:GlassCompositor.regionWrites,
                cards:cards.map(item=>({live:item.live,native:item.nativeGlass,alpha:item.parent.color.a,
                    tracked:item.trackGeometry,scale:item.parent.scale,opacity:item.parent.opacity,
                    region:item.nativeRegion()?.values})),
                probe:root.probe ? {x:root.probe.x,y:root.probe.y,width:root.probe.width,height:root.probe.height}:null})
        }
    }
}
'''
# ponytail: reuse the existing fixture's bounded startup and teardown, replacing only its shell.
source = fixture.read_text().split("if sys.argv[1] == '--plugin':\n    for attempt in range(150):", 1)[0]
needle = "(shell / 'shell.qml').write_text(FIXTURE)"
assert source.count(needle) == 1
# Match the desktop rule: native glass already blurs, so Hyprland must not blur over it.
source = source.replace("    display = Path(os.environ.get", '''    with config.open('a') as rules:
        rules.write('hl.window_rule({match={title="^illogical-impulse Settings$"},no_blur=true})\\n')
    display = Path(os.environ.get''', 1)
scope = {'__file__': str(fixture), '__name__': '__main__', 'qml': qml}
try:
    exec(compile(source.replace(needle, "(shell / 'shell.qml').write_text(qml)"), str(fixture), 'exec'), scope)
    env, shell, base, control = (scope[name] for name in ('nested_env','shell','base','control'))

    def ipc(function):
        result=subprocess.check_output(['qs','-p',str(shell/'shell.qml'),'ipc','call','dashboard-check',function],env=env,text=True,timeout=5)
        return result.strip()

    ipc('open')
    for _ in range(100):
        state=json.loads(ipc('state'))
        clients=json.loads(control('clients','-j'))
        window=next((c for c in clients if c['title']=='illogical-impulse Settings'),None)
        if state['ready'] and state['capable'] and window and 'hyprglass_enabled' in window.get('tags',[]): break
        time.sleep(.1)
    assert state['ready'] and state['capable'] and window and 'hyprglass_enabled' in window.get('tags',[]), state
    address='address:'+window['address']
    control('dispatch','setfloating',address)
    control('dispatch','resizewindowpixel',f'exact {scope["width"]-40} {scope["height"]-80},'+address)
    control('dispatch','movewindowpixel','exact 20 40,'+address)

    def check_cards(page):
        state=json.loads(ipc('state'))
        visible=[c['region'] for c in state['cards'] if c.get('region')]
        assert not state['rejected'] and state['captures']==0, state
        assert visible and len(visible)<=32, state
        assert all(c['native'] and c['live'] and abs(c['alpha']-.72)<.01 for c in state['cards']),state
        if page.startswith('Settings'):
            assert all(not c['tracked'] for c in state['cards']), 'Settings tiles still track the entire scrolling ancestor tree'
            assert all(abs(c['scale']-1)<.01 and abs(c['opacity']-1)<.01 for c in state['cards'] if c.get('region')),state
        assert all(r[-1]>=7.9 for r in visible),visible
        assert all(r[0]>=0 and r[1]>=0 and r[0]+r[2]<=state['width']+1 and r[1]+r[3]<=state['height']+1 for r in visible),visible
        assert json.loads(control('end4glass'))['regions']==len(visible),state
        print(page,'visible frosted cards:',len(visible),'loaded:',len(state['cards']),flush=True)

    time.sleep(3)
    check_cards('Home')
    ipc('settings'); time.sleep(3)
    check_cards('Settings')
    ipc('scroll'); time.sleep(3)
    check_cards('Settings scrolled')
    burst=json.loads(ipc('burst'))
    assert burst['after']-burst['before']<=1,('Scroll events were not coalesced',burst)
    time.sleep(3)
    check_cards('Settings burst')
    ipc('probe'); time.sleep(3)
    state=json.loads(ipc('state'))
    before=state['writes']; time.sleep(.7)
    assert json.loads(ipc('state'))['writes']==before,'Stationary Dashboard keeps rewriting geometry'
    window=next(c for c in json.loads(control('clients','-j')) if c['title']=='illogical-impulse Settings')
    probe=state['probe']; path=base/'dashboard.png'
    subprocess.run(['grim',str(path)],env=env,check=True,timeout=5)
    with Image.open(path).convert('RGB') as frame:
        x,y=window['at']; row=round(y+probe['y']+probe['height']/2)
        frosted=statistics.pstdev(frame.getpixel((round(x+probe['x']+40+i),row))[0] for i in range(64))
        clear=statistics.pstdev(frame.getpixel((round(x+35+i),row))[0] for i in range(64))
        frame.save('/tmp/end4-dashboard-native.png')
        assert clear>40 and frosted<clear*.35,('Frosted material did not blur the live checkerboard',clear,frosted,state)
    print('Checkerboard deviation clear/frosted:',round(clear,2),round(frosted,2),flush=True)
    ipc('close')
    for _ in range(3):
        time.sleep(.08)
        subprocess.run(['grim',str(path)],env=env,check=True,timeout=5)
        with Image.open(path).convert('RGB') as frame:
            assert min(frame.getpixel((9,frame.height//2)))>230,'Closing Dashboard produced a black frame outside the window'
    assert control('dispatch','exit')=='ok'
    assert scope['processes'][0].wait(timeout=10)==0
    print('Dashboard native frost, tint, clipping, idle geometry and close passed')
except Exception:
    if 'base' in scope:
        Path('/tmp/end4-dashboard-fixture.log').write_text((scope['base']/'fixture.log').read_text())
        Path('/tmp/end4-dashboard-compositor.log').write_text((scope['base']/'hyprland.log').read_text())
    raise
finally:
    if 'cleanup' in scope: scope['cleanup']()
