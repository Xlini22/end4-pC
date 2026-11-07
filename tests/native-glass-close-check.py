"""Keep live refraction while native layer windows fade in/out.
Run: python3 tests/native-glass-close-check.py --plugin /path/to/hyprglass.so
Uses the existing isolated compositor; never changes desktop animations.
"""
import json
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image

fixture=Path(__file__).with_name('native-glass-motion-check.py')
qml='''//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
ShellRoot {
    id: root
    property bool shown: false
    property bool red: false
    component Scene: Window {
        visible: true; width: 1000; height: 1100; color: "#1659cf"
        Rectangle {
            x: 66; y: 166; width: 388; height: 248
            color: root.red ? "#d03040" : "#20d040"
        }
    }
    Scene { title: "glass-red" }
    Scene { title: "glass-blue" }
    PanelWindow {
        anchors { top:true; bottom:true; left:true; right:true }
        exclusiveZone: 0
        WlrLayershell.namespace: "quickshell:bar"
        color: "transparent"
        Item {
            width: parent.width; height: 48
            WindowGlass { anchors.fill:parent; cardRadius:16 }
            Rectangle { x:32; y:12; width:80; height:20; color:"#dddddd" }
        }
    }
    PanelWindow {
        visible: root.shown
        anchors { top:true; bottom:true; left:true; right:true }
        exclusiveZone: 0
        WlrLayershell.namespace: "quickshell:sidebarLeft"
        WlrLayershell.layer: WlrLayer.Overlay
        color: "transparent"
        Item {
            x: 50; y: 150; width: 420; height: 280
            WindowGlass { id: pane; anchors.fill:parent; cardRadius:20 }
            Item {
                x: 60; y: 60; width: 100; height: 100
                WindowGlass { anchors.fill:parent; cardRadius:16; frost:8 }
            }
            Rectangle { x:200; y:120; width:12; height:12; color:"white" }
        }
    }
    IpcHandler {
        target: "close-check"
        function open(): void {
            Config.options.background.widgets.glass.enhanced=true
            Config.options.background.widgets.glass.haze=1
            root.shown=true
        }
        function close(): void { root.shown=false }
        function background(value: bool): void { root.red=value }
        function state(): string { return JSON.stringify({active:GlassCompositor.active,
            enhanced:GlassCompositor.enhancedActive,frosted:GlassCompositor.frostedAvailable,
            regions:GlassCompositor.regionsApplied}) }
    }
}
'''
# ponytail: reuse the existing native test's isolated compositor lifecycle.
source=fixture.read_text().split("if sys.argv[1] == '--plugin':\n    for attempt in range(150):",1)[0]
needle="(shell / 'shell.qml').write_text(FIXTURE)"
assert source.count(needle)==1
source=source.replace(needle,"(shell / 'shell.qml').write_text(qml)")
scope={'__file__':str(fixture),'__name__':'__main__','qml':qml}
# Match the desktop's blur rules: close snapshots must not blur the whole output.
if '--legacy' not in sys.argv and '--blur-rules' not in sys.argv: sys.argv.append('--blur-rules')
try:
    exec(compile(source,str(fixture),'exec'),scope)
    env,shell,base=(scope[name] for name in ['nested_env','shell','base'])
    width,height=scope['width'],scope['height']
    control=scope['control']
    def ipc(function,*args):
        return subprocess.check_output(['qs','-p',str(shell/'shell.qml'),'ipc','call','close-check',function,*args],env=env,text=True,timeout=10).strip()
    def grab():
        path=base/'fade.png'
        subprocess.run(['grim',str(path)],env=env,check=True,timeout=10)
        return Image.open(path).convert('RGB')
    for _ in range(100):
        state=json.loads(ipc('state'))
        if state['active']: break
        time.sleep(.1)
    assert state['active'],state
    for leaf in ['layersIn','layersOut']:
        if '--legacy' in sys.argv:
            assert control('keyword','animation',leaf+',0')=='ok'
        else:
            assert control('eval',f'hl.animation({{leaf="{leaf}",enabled=false}})')=='ok'
    for leaf in ['fadeLayersIn','fadeLayersOut']:
        if '--legacy' in sys.argv:
            assert control('keyword','animation',leaf+',1,20,linear')=='ok'
        else:
            assert control('eval',f'hl.animation({{leaf="{leaf}",enabled=true,speed=20,bezier="linear"}})')=='ok'
    time.sleep(.4)
    bare=grab()
    background=bare.getpixel((55,290))
    markerBlue=bare.getpixel((256,276))[2]
    ipc('open');time.sleep(2.3)
    opened=grab();green=opened.getpixel((55,290))
    assert green[1]>background[1]+70,('Probe missed clear edge refraction',green,background)
    ipc('background','true');time.sleep(.2)
    red=grab().getpixel((55,290))
    assert red[0]>background[0]+100,('Reference missed the red background',red)
    ipc('background','false');time.sleep(.2)
    def checkFrame(frame,reference,stage):
        assert max(abs(a-b) for a,b in zip(frame.getpixel((width-30,height-30)),outside))<10, ('SCREEN FLASH',stage,frame.getpixel((width-30,height-30)),outside)
        actual=frame.getpixel((55,290))
        alpha=(frame.getpixel((256,276))[2]-markerBlue)/(255-markerBlue)
        if not .12<alpha<.92: return False
        expected=[b+(r-b)*alpha for b,r in zip(background,reference)]
        error=max(abs(a-b) for a,b in zip(actual,expected))
        assert error<20,(stage,'Refraction vanished or froze during animation',alpha,actual,expected,error)
        return True
    outside=opened.getpixel((width-30,height-30))
    ipc('close')
    frames=0
    for index in range(18):
        if index==4: ipc('background','true')
        time.sleep(.055)
        frame=grab()
        frame.save(f'/tmp/end4-close-native-{index}.png')
        frames+=checkFrame(frame,green if index<4 else red,'close')
    assert frames>=3,('No usable close frames',frames)
    assert 'quickshell:sidebarLeft' not in json.loads(ipc('state'))['regions'], 'Hidden Qt layer did not withdraw its regions'
    time.sleep(1)
    checkFrame(grab(),red,'closed')
    ipc('open')
    opening=0
    for index in range(18):
        time.sleep(.055)
        opening+=checkFrame(grab(),red,'open')
    assert opening>=3,('No usable opening frames',opening)
    time.sleep(1)
    checkFrame(grab(),red,'opened')
    print(f'Live refraction persisted across {frames} closing and {opening} opening frames, including a changing backdrop')
    assert control('dispatch','exit')=='ok'
    assert scope['processes'][0].wait(timeout=10)==0
finally:
    if 'cleanup' in scope: scope['cleanup']()
