"""Compare native glass builds in isolated nested compositors.
Run: python3 tests/native-glass-performance.py OLD.so NEW.so
Add --sidebar to measure the real sidebar home; --partial/--outside limit background motion.
END4_GL_BENCH_WIDE=1 restores its old unused surface width for baseline measurements.
Reports actual blur fragment coverage and GPU time per rendered frame; does not reconfigure the desktop plugin.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

TRACE = r'''
#define _GNU_SOURCE
#include <GLES3/gl32.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static GLuint blur, glass;
static GLint regionCountLocation=-1;
static __thread GLuint program;
static __thread GLint viewport[4], scissor[4];
static __thread int clipped;
// ponytail: one compositor render thread; multiple GL render threads need per-thread aggregation.
static unsigned long long draws, frames, full_pixels, pixels, glass_pixels, allocations;
#define ORIGINAL(name) static __typeof__(&name) real; if (!real) real = dlsym(RTLD_NEXT, #name)
GLint glGetUniformLocation(GLuint p, const GLchar *name) {
    ORIGINAL(glGetUniformLocation);
    GLint result = real(p, name);
    if (!strcmp(name, "direction")) blur = p;
    if (!strcmp(name, "regionCount")) { glass = p; regionCountLocation = result; }
    return result;
}
void glUseProgram(GLuint p) { ORIGINAL(glUseProgram); program = p; real(p); }
// ponytail: this fixture has one multi-region panel and a one-region bar; multiple panels need presentation counters.
void glUniform1i(GLint location, GLint value) {
    ORIGINAL(glUniform1i); real(location,value);
    const char *flag=getenv("END4_GL_BENCH_ACTIVE");
    if(program==glass && location==regionCountLocation && value>1 && flag && !access(flag,F_OK)) frames++;
}
void glViewport(GLint x, GLint y, GLsizei w, GLsizei h) {
    ORIGINAL(glViewport); viewport[0]=x; viewport[1]=y; viewport[2]=w; viewport[3]=h; real(x,y,w,h);
}
void glScissor(GLint x, GLint y, GLsizei w, GLsizei h) {
    ORIGINAL(glScissor); scissor[0]=x; scissor[1]=y; scissor[2]=w; scissor[3]=h; real(x,y,w,h);
}
void glEnable(GLenum cap) { ORIGINAL(glEnable); if (cap==GL_SCISSOR_TEST) clipped=1; real(cap); }
void glDisable(GLenum cap) { ORIGINAL(glDisable); if (cap==GL_SCISSOR_TEST) clipped=0; real(cap); }
void glTexImage2D(GLenum target, GLint level, GLint format, GLsizei w, GLsizei h, GLint border, GLenum pf, GLenum type, const void *data) {
    ORIGINAL(glTexImage2D); real(target,level,format,w,h,border,pf,type,data);
    const char *flag=getenv("END4_GL_BENCH_ACTIVE"); if (flag && !access(flag,F_OK)) allocations++;
}
void glDrawArrays(GLenum mode, GLint first, GLsizei count) {
    ORIGINAL(glDrawArrays); real(mode,first,count);
    const char *flag = getenv("END4_GL_BENCH_ACTIVE");
    if (!flag || access(flag,F_OK)) return;
    if (!blur || (program != blur && program != glass)) return;
    int x=viewport[0], y=viewport[1], right=x+viewport[2], bottom=y+viewport[3];
    if (program == blur) full_pixels += (unsigned long long)viewport[2]*viewport[3];
    if (clipped) {
        if (scissor[0]>x) x=scissor[0]; if (scissor[1]>y) y=scissor[1];
        if (scissor[0]+scissor[2]<right) right=scissor[0]+scissor[2];
        if (scissor[1]+scissor[3]<bottom) bottom=scissor[1]+scissor[3];
    }
    if (right>x && bottom>y) {
        if (program==glass) glass_pixels += (unsigned long long)(right-x)*(bottom-y);
        else pixels += (unsigned long long)(right-x)*(bottom-y);
    }
    if (program==blur) draws++;
}
__attribute__((destructor)) static void report(void) {
    const char *path=getenv("END4_GL_WORK_LOG"); if (!path) return;
    FILE *out=fopen(path,"w"); if (!out) return;
    fprintf(out,"{\"draws\":%llu,\"frames\":%llu,\"full_pixels\":%llu,\"pixels\":%llu,\"allocations\":%llu,\"glass_pixels\":%llu}\n",draws,frames,full_pixels,pixels,allocations,glass_pixels);
    fclose(out);
}
'''


def counters(pid):
    proc = Path('/proc') / str(pid)
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    clients = {}
    for path in (proc / 'fdinfo').iterdir():
        try:
            data = path.read_text()
        except OSError:
            continue
        client = re.search(r'^drm-client-id:\s*(\d+)', data, re.M)
        if client:
            clients[client[1]] = sum(int(v) for v in re.findall(r'^drm-engine-gfx:\s*(\d+) ns', data, re.M))
    return int(stat[11]) + int(stat[12]), sum(clients.values())


SIDEBAR = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.sidebarLeft as Left
ShellRoot {
    id: root
    property bool partial: false
    property bool outside: false
    Left.SidebarLeft { id: sidebar }
    PanelWindow {
        anchors { top:true; left:true; right:true }
        implicitHeight:68; exclusiveZone:0; color:"transparent"
        WlrLayershell.namespace:"quickshell:bar"
        Item { width:parent.width; height:48; WindowGlass { anchors.fill:parent; cardRadius:20 } }
    }
    component Scene: Window {
        visible:true; width:1000; height:1100; color:"#1565c0"
        Repeater { model:16; Rectangle { required property int index; x:index*64; width:28; height:parent.height; color:"#99ffffff" } }
        Rectangle { width:8; height:parent.height; color:"yellow"; NumberAnimation on x { from:0; to:800; duration:1800; loops:Animation.Infinite; running:!root.partial } }
    }
    Scene { title:"glass-red" }
    Scene { title:"glass-blue" }
    PanelWindow {
        id: motionWindow
        visible:root.partial
        anchors { top:true; left:true }
        margins { top:400; left:root.outside ? motionWindow.screen.width - 160 : 80 }
        implicitWidth:120; implicitHeight:100; exclusiveZone:0; color:"#1565c0"
        WlrLayershell.namespace:"glass-partial-backdrop"
        WlrLayershell.layer:WlrLayer.Top
        Rectangle { width:8; height:parent.height; color:"yellow"; NumberAnimation on x { from:0; to:100; duration:800; loops:Animation.Infinite } }
    }
    IpcHandler {
        target:"glass-check"
        function benchmarkPanel(): void {
            Config.options.background.widgets.glass.enhanced=true
            Config.options.sidebar.mainPage="home"
            Config.options.sidebar.leftRememberPage=false
            Config.options.policies.ai=1
            Config.options.policies.weeb=1
            Config.options.sidebar.translator.enable=true
            Config.options.sidebar.football.enable=true
            Config.options.sidebar.media.enable=true
            GlobalStates.sidebarLeftOpen=true
        }
        function wideSurface(): void { sidebar.sidebarContent.QsWindow.window.implicitWidth=Appearance.sizes.sidebarWidthExtended + Appearance.sizes.elevationMargin }
        function partialMotion(outside: bool): void { root.outside=outside; root.partial=true }
        function setBlur(value: real): void { Config.options.background.widgets.glass.haze=value }
        function state(): string { return JSON.stringify({ready:GlassCompositor.enhancedActive && sidebar.sidebarContent?.currentKey === "home",
            width:sidebar.sidebarContent?.Window.window?.width ?? 0, cards:GlassCompositor.glassItems.filter(item=>item.nativeRegion()?.name === "quickshell:sidebarLeft").length}) }
    }
}
'''

repo = Path(__file__).resolve().parents[1]
fixture = repo / 'tests/native-glass-motion-check.py'
sidebar = '--sidebar' in sys.argv
outside = '--outside' in sys.argv
partial = '--partial' in sys.argv or outside
assert not partial or sidebar, '--partial requires --sidebar'
plugins = [Path(arg).resolve(strict=True) for arg in sys.argv[1:] if arg not in ('--sidebar','--partial','--outside')]
assert plugins, __doc__
haze = float(os.environ.get('END4_GL_BENCH_HAZE', '4'))
assert 1 <= haze <= 16, 'Benchmark haze must be between 1 and 16'
reports = []
with tempfile.TemporaryDirectory(prefix='glass-perf-', dir='/tmp') as temporary:
    directory = Path(temporary)
    (directory / 'trace.c').write_text(TRACE)
    library = directory / 'trace.so'
    subprocess.run(['cc', '-shared', '-fPIC', '-O2', str(directory / 'trace.c'), '-o', str(library), '-ldl'], check=True)
    for index, plugin in enumerate(plugins):
        flag, log = directory / 'active', directory / f'work-{index}.json'
        bench_env = {'LD_PRELOAD': str(library), 'END4_GL_BENCH_ACTIVE': str(flag), 'END4_GL_WORK_LOG': str(log)}
        measurement = {}

        def measure(pid, ipc):
            ipc('benchmarkPanel')
            ipc('setBlur', str(haze))
            if partial: ipc('partialMotion', 'true' if outside else 'false')
            if sidebar and os.environ.get('END4_GL_BENCH_WIDE') == '1': ipc('wideSurface')
            time.sleep(1)
            if sidebar: measurement['surface_width'] = json.loads(ipc('state'))['width']
            before = counters(pid)
            start = time.monotonic()
            flag.touch()
            clocks = []
            clock = next(Path('/sys/class/drm').glob('card*/device/hwmon/hwmon*/freq1_input'), None)
            try:
                for tick in range(50):
                    if tick % 10 == 0 and not sidebar:
                        ipc('jigglePanel')
                    if clock:
                        clocks.append(int(clock.read_text()) / 1e6)
                    time.sleep(.1)
            finally:
                flag.unlink(missing_ok=True)
            after = counters(pid)
            measurement.update(seconds=time.monotonic()-start,
                               cpu_seconds=(after[0]-before[0])/os.sysconf('SC_CLK_TCK'),
                               gpu_ns=after[1]-before[1], gpu_clock_mhz=round(sum(clocks)/len(clocks), 1) if clocks else None)

        # ponytail: reuse the production fixture setup; a separate fixture would duplicate compositor lifecycle code.
        source = fixture.read_text().split('    edge_colors = []', 1)[0]
        if sidebar:
            source = source.split("if sys.argv[1] == '--plugin':\n    for attempt in range(150):", 1)[0]
            source = source.replace("(shell / 'shell.qml').write_text(FIXTURE)", "(shell / 'shell.qml').write_text(SIDEBAR)")
            source += '''
def ipc(function, *args):
    return subprocess.check_output(['qs','-p',str(shell/'shell.qml'),'ipc','call','glass-check',function,*args],env=nested_env,text=True,timeout=10).strip()
ipc('benchmarkPanel')
for _ in range(100):
    state = json.loads(ipc('state'))
    if state['ready'] and state['cards'] == 7: break
    time.sleep(.1)
assert state['ready'] and state['cards'] == 7, state
'''
        needle = "str(config)], env=nested_env,"
        assert source.count(needle) == 1
        source = source.replace(needle, "str(config)], env={**nested_env, **bench_env},")
        source += "\nbench_version = json.loads(control('plugin','list','-j'))[0]['version']\nmeasure(processes[0].pid,ipc)\nassert control('dispatch','exit') == 'ok'\nassert processes[0].wait(timeout=10) == 0\n"
        scope = {'__file__': str(fixture), '__name__': '__main__', 'bench_env': bench_env, 'measure': measure, 'SIDEBAR': SIDEBAR}
        previous_args = sys.argv
        try:
            sys.argv = [str(fixture), '--plugin', str(plugin)] + (['--blur-rules'] if sidebar else [])
            exec(compile(source, str(fixture), 'exec'), scope)
        finally:
            sys.argv = previous_args
            if 'cleanup' in scope:
                scope['cleanup']()
        work = json.loads(log.read_text())
        assert outside or work['draws'] > 20, ('No usable blur frames', work)
        frames = work['frames']
        assert outside or frames > 20, ('No panel frames', work)
        report = {'plugin': str(plugin), 'version': scope['bench_version'], 'panel': 'sidebar' if sidebar else 'settings', 'output': [scope['width'], scope['height']], 'surface_width': measurement.get('surface_width'), 'partial': partial, 'outside': outside, 'haze': haze, 'frames': frames,
                  'blur_pixels_per_draw': round(work['pixels']/work['draws']) if work['draws'] else 0,
                  'blur_coverage': round(work['pixels']/work['full_pixels'], 4) if work['full_pixels'] else 0,
                  'blur_pixels_per_frame': round(work['pixels']/frames) if frames else 0,
                  'glass_pixels_per_frame': round(work['glass_pixels']/frames) if frames else 0,
                  'gpu_ms_per_frame': round(measurement['gpu_ns']/1e6/frames, 3) if frames else None,
                  'cpu_ms_per_frame': round(measurement['cpu_seconds']*1000/frames, 3) if frames else None,
                  'gpu_busy_percent': round(measurement['gpu_ns']/1e9/measurement['seconds']*100, 2),
                  'cpu_percent': round(measurement['cpu_seconds']/measurement['seconds']*100, 2),
                  'gpu_clock_mhz': measurement['gpu_clock_mhz'], 'texture_allocations': work['allocations']}
        reports.append(report)
        print(json.dumps(report), flush=True)
Path('/tmp/end4-native-glass-performance.json').write_text(json.dumps(reports, indent=2)+'\n')
