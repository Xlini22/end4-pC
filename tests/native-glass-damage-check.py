"""Check real partial redraws without screenshots forcing a full repaint.
Run: python3 tests/native-glass-damage-check.py --plugin /path/to/hyprglass.so
Reads two pixels directly after native composition in an isolated compositor.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

repo=Path(__file__).resolve().parents[1]
fixture=repo/'tests/native-glass-motion-check.py'
# ponytail: reuse the existing optical scene and GL tracer; never alter the desktop profile.
definitions={'__file__':str(repo/'tests/native-glass-close-check.py')}
exec((repo/'tests/native-glass-close-check.py').read_text().split('# ponytail:',1)[0],definitions)
qml=definitions['qml'].replace('    property bool red: false','    property bool red: false\n    property bool patchRed:false\n    property bool patchOutside:false')
qml=qml.replace('    property bool patchOutside:false', '    property bool patchOutside:false\n    property bool markerRed:false')
qml=qml.replace('    property bool markerRed:false', '    property bool markerRed:false\n    property real frostStrength:8')
qml=qml.replace('frost:8', 'frost:root.frostStrength')
qml=qml.replace('color:"white"', 'color:root.markerRed ? "#ff10ff" : "white"')
qml=qml.replace('    IpcHandler {', '''
    PanelWindow {
        id: patch
        anchors { top:true; left:true }
        margins { top:210; left:root.patchOutside ? patch.screen.width - 150 : 110 }
        implicitWidth:100; implicitHeight:100; exclusiveZone:0
        WlrLayershell.namespace:"glass-partial-backdrop"
        WlrLayershell.layer:WlrLayer.Top
        color: root.patchRed ? "#de1020" : "#20b0de"
    }
    IpcHandler {
        function patch(value: bool): void { root.patchRed=value }
        function outside(): void { root.patchOutside=true }
        function marker(value: bool): void { root.markerRed=value }
        function frost(value: real): void { root.frostStrength=value }
''')
tracer={}
exec((repo/'tests/native-glass-performance.py').read_text().split('repo = Path(__file__)',1)[0],tracer)
trace=tracer['TRACE'].replace('static GLuint blur, glass;', 'static GLuint blur, glass;\nstatic int currentRegions;')
trace=trace.replace('ORIGINAL(glUniform1i); real(location,value);','ORIGINAL(glUniform1i); real(location,value);\n    if (program==glass && location==regionCountLocation) currentRegions=value;')
needle='    if (!blur || (program != blur && program != glass)) return;'
assert trace.count(needle)==1
trace=trace.replace(needle, r'''
    if (program==glass && currentRegions>=2) {
        unsigned char center[4]={0}, marker[4]={0};
        int centerHit=!clipped || (scissor[0]<=160 && scissor[1]<=260 && scissor[0]+scissor[2]>160 && scissor[1]+scissor[3]>260);
        int markerHit=!clipped || (scissor[0]<=256 && scissor[1]<=276 && scissor[0]+scissor[2]>256 && scissor[1]+scissor[3]>276);
        if(centerHit) glReadPixels(160,260,1,1,GL_RGBA,GL_UNSIGNED_BYTE,center);
        if(markerHit) glReadPixels(256,276,1,1,GL_RGBA,GL_UNSIGNED_BYTE,marker);
        FILE *pixels=fopen(getenv("END4_GL_PIXEL_LOG"),"a");
        if(pixels) {
            fprintf(pixels,"%d %d %d %d %d %d %d %d\n",center[0],center[1],center[2],marker[0],marker[1],marker[2],centerHit,markerHit);
            fclose(pixels);
        }
    }
'''+needle)
source=fixture.read_text().split("if sys.argv[1] == '--plugin':\n    for attempt in range(150):",1)[0]
source=source.replace("(shell / 'shell.qml').write_text(FIXTURE)","(shell / 'shell.qml').write_text(qml)")
source=source.replace('str(config)], env=nested_env,','str(config)], env={**nested_env, **trace_env},')
if '--blur-rules' not in sys.argv:sys.argv.append('--blur-rules')
scope={'__file__':str(fixture),'__name__':'__main__','qml':qml}
with tempfile.TemporaryDirectory(prefix='glass-damage-',dir='/tmp') as temporary:
    directory=Path(temporary)
    (directory/'trace.c').write_text(trace)
    library=directory/'trace.so'
    subprocess.run(['cc','-shared','-fPIC','-O2',str(directory/'trace.c'),'-o',str(library),'-ldl'],check=True)
    flag=directory/'active'
    pixels=directory/'pixels'
    scope['trace_env']={'LD_PRELOAD':str(library),'END4_GL_BENCH_ACTIVE':str(flag),
        'END4_GL_WORK_LOG':str(directory/'work.json'),'END4_GL_PIXEL_LOG':str(pixels)}
    try:
        exec(compile(source,str(fixture),'exec'),scope)
        env,shell,base=(scope[name] for name in ['nested_env','shell','base'])
        def ipc(function,*args):
            return subprocess.check_output(['qs','-p',str(shell/'shell.qml'),'ipc','call','close-check',function,*args],env=env,text=True,timeout=10).strip()
        def rows():
            return [list(map(int,line.split())) for line in pixels.read_text().splitlines()] if pixels.exists() else []
        ipc('open')
        for _ in range(100):
            state=json.loads(ipc('state'))
            if state['enhanced'] and state['frosted']:break
            time.sleep(.1)
        assert state['enhanced'] and state['frosted'],state
        # Exercise the native margins rather than relying on a large compositor blur halo.
        assert scope['control']('eval','hl.config({decoration={blur={size=1,passes=1}}})')=='ok'
        time.sleep(2)
        flag.touch()
        checks=0
        for red in (True,False,True,False):
            count=len(rows())
            ipc('patch',str(red).lower())
            time.sleep(.3)
            changed=[row for row in rows()[count:] if row[6]]
            assert changed,'Partial frame was not rendered'
            r,g,b=changed[-1][:3]
            assert (r>150 and g<100) if red else (r<100 and g>120),('Live backdrop froze or the Gaussian sampled stale pixels',red,changed)
            checks+=len(changed)
        for red in (True,False):
            count=len(rows());ipc('marker',str(red).lower());time.sleep(.3)
            changed=[row for row in rows()[count:] if row[7]]
            assert changed, 'Qt control update was not rendered'
            r,g,b=changed[-1][3:6]
            assert (r>200 and g<80 and b>200) if red else min(r,g,b)>235, ('Qt control vanished or froze',red,changed)
        ipc('outside');time.sleep(.7)
        count=len(rows())
        for red in (True,False,True):
            ipc('patch',str(red).lower());time.sleep(.3)
        assert len(rows())==count,('Updates outside the glass still recompose it',rows()[count:])
        for strength in ('32','8'):
            count=len(rows());ipc('frost',strength);time.sleep(.3)
            assert any(row[6] for row in rows()[count:]), 'Material-only update did not invalidate the native glass'
        flag.unlink()
        assert scope['control']('dispatch','exit')=='ok'
        assert scope['processes'][0].wait(timeout=10)==0
        print(f'Partial redraw: {checks} live frost/control pixel checks; outside updates caused zero glass compositions; material-only changes repainted')
    finally:
        if 'cleanup' in scope:scope['cleanup']()
