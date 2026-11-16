"""Prepare native GPU stage timers without running a compositor.

  python3 tests/native-glass-stage-profile.py prepare DIRECTORY
  python3 tests/native-glass-stage-profile.py self-test
  python3 tests/native-glass-stage-profile.py run DIRECTORY
  python3 tests/native-glass-stage-profile.py summarize DIRECTORY

The run command requires a dedicated TTY with no desktop compositor running.
GPU/driver faults can still freeze the machine. Preparation and self-test use no GPU.
"""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
REVISION = '22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5'
HEADER = r'''
#pragma once
#include <GLES3/gl32.h>
#include <GLES2/gl2ext.h>
#include <EGL/egl.h>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <unistd.h>
namespace End4GPU {
struct Ticket { GLuint q[2]{}; const char* stage=nullptr; unsigned long long frame=0,cpu=0; bool invalid=false; };
inline std::deque<Ticket> pending;
inline FILE* output=nullptr;
inline bool initialized=false,supported=false,selected=false;
inline unsigned long long frame=0;
inline PFNGLGENQUERIESEXTPROC gen=nullptr;
inline PFNGLDELETEQUERIESEXTPROC del=nullptr;
inline PFNGLQUERYCOUNTEREXTPROC stamp=nullptr;
inline PFNGLGETQUERYOBJECTUIVEXTPROC ready=nullptr;
inline PFNGLGETQUERYOBJECTUI64VEXTPROC result=nullptr;
inline unsigned long long now() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
inline void initialize() {
    if (initialized) return;
    initialized=true;
    const char* path=std::getenv("END4_STAGE_LOG");
    if (!path || !(output=std::fopen(path,"w"))) return;
    gen=(PFNGLGENQUERIESEXTPROC)eglGetProcAddress("glGenQueriesEXT");
    del=(PFNGLDELETEQUERIESEXTPROC)eglGetProcAddress("glDeleteQueriesEXT");
    stamp=(PFNGLQUERYCOUNTEREXTPROC)eglGetProcAddress("glQueryCounterEXT");
    ready=(PFNGLGETQUERYOBJECTUIVEXTPROC)eglGetProcAddress("glGetQueryObjectuivEXT");
    result=(PFNGLGETQUERYOBJECTUI64VEXTPROC)eglGetProcAddress("glGetQueryObjectui64vEXT");
    auto get=(PFNGLGETQUERYIVEXTPROC)eglGetProcAddress("glGetQueryivEXT");
    const auto ext=(const char*)glGetString(GL_EXTENSIONS);
    supported=ext && std::strstr(ext,"GL_EXT_disjoint_timer_query") && gen && del && stamp && ready && result && get;
    GLint bits=0;
    if (supported) get(GL_TIMESTAMP_EXT,GL_QUERY_COUNTER_BITS_EXT,&bits);
    supported=supported && bits>0;
    std::fprintf(output,"{\"supported\":%s,\"timestamp_bits\":%d,\"sampling\":8}\n",supported?"true":"false",bits);
    std::fflush(output);
}
inline void drain() {
    if (!supported) return;
    GLint disjoint=0;glGetIntegerv(GL_GPU_DISJOINT_EXT,&disjoint);
    if (disjoint) for (auto& t:pending) t.invalid=true;
    while (!pending.empty()) {
        auto& t=pending.front();GLuint available=0;
        ready(t.q[1],GL_QUERY_RESULT_AVAILABLE_EXT,&available);
        if (!available) break;
        GLuint64 a=0,b=0;result(t.q[0],GL_QUERY_RESULT_EXT,&a);result(t.q[1],GL_QUERY_RESULT_EXT,&b);
        std::fprintf(output,"{\"frame\":%llu,\"stage\":\"%s\",\"gpu_ns\":%llu,\"cpu_ns\":%llu,\"valid\":%s}\n",t.frame,t.stage,(unsigned long long)(b>=a?b-a:0),t.cpu,(!t.invalid && b>=a)?"true":"false");
        del(2,t.q);pending.pop_front();
    }
    std::fflush(output);
}
inline void newFrame(bool settings) {
    if (!settings) return;
    initialize();drain();
    const char* gate=std::getenv("END4_STAGE_ACTIVE");
    selected=supported && gate && !access(gate,F_OK) && (++frame%8==0);
}
struct Scope {
    Ticket ticket;unsigned long long start=0;bool active=false;
    Scope(const char* stage,bool settings=true) {
        // ponytail: one compositor GL thread, at most 2048 pending stage samples;
        // multiple GL contexts need separate queues. Never wait on a diagnostic query.
        active=settings && selected && pending.size()<2048;
        if (!active) return;
        ticket.stage=stage;ticket.frame=frame;gen(2,ticket.q);stamp(ticket.q[0],GL_TIMESTAMP_EXT);start=now();
    }
    ~Scope() {
        if (!active) return;
        ticket.cpu=now()-start;stamp(ticket.q[1],GL_TIMESTAMP_EXT);pending.push_back(ticket);
    }
};
}
'''


def instrument(text):
    text = text.replace('#include "LayerGeometry.hpp"', '#include "LayerGeometry.hpp"\n#include "End4GPUTiming.hpp"')
    start = text.index('void CGlassLayerSurface::sampleAndRedirect(')
    end = text.index('void CGlassLayerSurface::compositeAndRestore(', start)
    before, redirect, composite = text[:start], text[start:end], text[end:]
    needle = '    if (layerSurface->m_fadingOut && !m_hasCachedSample) return;'
    assert redirect.count(needle) == 1
    redirect = redirect.replace(needle, needle + '\n    const bool end4StageProfile=layerSurface->m_namespace=="quickshell:settings";\n'
        '    End4GPU::newFrame(end4StageProfile);\n    End4GPU::Scope totalTrace("redirect-total",end4StageProfile);')
    for stage, call in [('capture', 'GlassRenderer::sampleBackground('),
                        ('outer-blur', 'GlassRenderer::blurBackground(m_sampleFramebuffer'),
                        ('frost-copy', 'glBlitFramebuffer('),
                        ('frost-blur', 'GlassRenderer::blurBackground(m_frostFramebuffer')]:
        assert redirect.count(call) == 1, call
        pos = redirect.index(call)
        left, right = redirect.rfind('\n', 0, pos) + 1, redirect.index(';', pos) + 1
        original = redirect[left:right]
        indent = original[:len(original) - len(original.lstrip())]
        redirect = redirect[:left] + indent + '{ End4GPU::Scope stageTrace("' + stage + '",end4StageProfile);\n' + original + '\n' + indent + '}' + redirect[right:]
    needle = 'if (const auto* surface = enhancedSurface()) sampleContrast(source, transformBox, *surface);'
    assert redirect.count(needle) == 1
    redirect = redirect.replace(needle, 'if (const auto* surface = enhancedSurface()) { End4GPU::Scope contrastTrace("contrast",end4StageProfile); sampleContrast(source, transformBox, *surface); }')
    needle = '    auto target = g_pHyprRenderer->m_renderData.currentFB;'
    assert composite.count(needle) == 1
    composite = composite.replace(needle, '    End4GPU::Scope compositionTrace("refraction-and-composition",layerSurface->m_namespace=="quickshell:settings");\n' + needle)
    return before + redirect + composite


def prepare(base):
    base.mkdir(parents=True, exist_ok=True)
    source = base / 'source'
    assert not source.exists(), 'Use a new directory: existing sources will not be overwritten'
    subprocess.run(['git', 'clone', '--depth', '1', '--branch', 'v0.6.4', 'https://github.com/hyprnux/hyprglass.git', str(source)], check=True)
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    assert revision == REVISION
    subprocess.run(['git', '-C', str(source), 'apply', str(REPO / 'scripts/glass/native/live-background.patch')], check=True)
    for test in ('native-glass-buffer-check.py', 'native-glass-shader-check.py'):
        subprocess.run([sys.executable, str(REPO / 'tests' / test), str(source)], check=True)
    subprocess.run(['make', '-C', str(source), '-j1'], check=True)
    shutil.copy2(source / 'hyprglass.so', base / 'baseline.so')
    target = source / 'src/GlassLayerSurface.cpp'
    original = target.read_text()
    (base / 'GlassLayerSurface.before.cpp').write_text(original)
    target.write_text(instrument(original))
    (source / 'src/End4GPUTiming.hpp').write_text(HEADER)
    subprocess.run(['make', '-C', str(source), '-j1'], check=True)
    shutil.copy2(source / 'hyprglass.so', base / 'profile.so')
    (base / 'instrumentation.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), target.read_text().splitlines(True), fromfile='baseline/GlassLayerSurface.cpp', tofile='profile/GlassLayerSurface.cpp')))
    (base / 'build.json').write_text(json.dumps({'upstream': REVISION,
        'patch_sha256': hashlib.sha256((REPO / 'scripts/glass/native/live-background.patch').read_bytes()).hexdigest(),
        'hyprland': json.loads(subprocess.check_output(['Hyprland', '--version-json'], text=True)),
        'binaries': {name: hashlib.sha256((base / name).read_bytes()).hexdigest() for name in ('baseline.so', 'profile.so')}}, indent=2) + '\n')
    print('Prepared, no GPU executed:', base, flush=True)


def desktop_processes():
    result = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            name = (proc / 'comm').read_text().strip()
            if name in ('Hyprland', 'sway', 'kwin_wayland', 'gnome-shell', 'qs', 'quickshell') and proc.stat().st_uid == os.getuid():
                result.append((proc.name, name))
        except OSError:
            pass
    return result


SCROLL = '''
    function findScroll(item) {
        if (!item || item.visible === false || item.opacity === 0) return null
        let best = item.contentHeight !== undefined && item.contentY !== undefined ? item : null
        for (const child of item.children ?? []) {
            const found = findScroll(child)
            if (found && (!best || found.contentHeight-found.height > best.contentHeight-best.height)) best=found
        }
        return best
    }
    function selectScroll() {
        const region = GlassCompositor.glassItems.map(item=>item.nativeRegion()).find(r=>r?.name === "quickshell:settings")
        scroll.targetItem=findScroll(region?.win.contentItem)
    }
    SequentialAnimation {
        id: scroll
        property var targetItem: null
        property real extent: Math.min(1500,Math.max(0,(targetItem?.contentHeight ?? 0)-(targetItem?.height ?? 0)))
        loops: Animation.Infinite
        NumberAnimation { target:scroll.targetItem; property:"contentY"; from:0; to:scroll.extent; duration:4000 }
        NumberAnimation { target:scroll.targetItem; property:"contentY"; from:scroll.extent; to:0; duration:4000 }
    }
'''


def direct_fixture(source, base, index, fixture):
    """Adapt only complete indented lines, then compile before starting any process."""
    config_line = next(line for line in fixture.read_text().splitlines()
                       if line.strip().startswith("(directory / 'config.json').write_text"))
    changes = {
        config_line: "    (directory / 'config.json').write_text(Path(" + repr(str(base / 'config-snapshot.json')) + ").read_text())",
        "    nested_env = {**os.environ, 'XDG_RUNTIME_DIR': str(base), 'WAYLAND_DISPLAY': str(display)}":
            "    nested_env = {**os.environ, 'XDG_RUNTIME_DIR': str(base)}\n"
            "    nested_env.pop('WAYLAND_DISPLAY', None)\n    nested_env.pop('DISPLAY', None)",
    }
    for name, variable in (('hyprland.log', 'log'), ('fixture.log', 'fixture_log')):
        line = '    ' + variable + " = open(base / " + repr(name) + ", 'w')"
        changes[line] = '    (base / ' + repr(name) + ').symlink_to(Path(' + repr(str(base / f'{index}-{name}')) + '))\n' + line
    for old, new in changes.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    source = source.replace('960x640@60', '1920x1080@60')
    compile(source, str(fixture), 'exec')
    return source


def runner_source(base):
    """Reuse the existing fixture, but start its compositor directly on the TTY."""
    text = (REPO / 'tests/native-glass-performance.py').read_text()
    def change(old, new):
        nonlocal text
        assert text.count(old) == 1, (old[:90], text.count(old))
        text = text.replace(old, new)
    change('running:!root.partial', 'running:false')
    change('    IpcHandler {\n        target:"glass-check"', SCROLL + '''
    IpcHandler {
        target:"glass-check"
        function setScrolling(value: bool): void { root.selectScroll(); scroll.running=value }
        function scrollState(): string { root.selectScroll(); return JSON.stringify({extent:scroll.extent,y:scroll.targetItem?.contentY ?? -1}) }''')
    change("'END4_GL_WORK_LOG': str(log)", "'END4_GL_WORK_LOG': str(log), 'END4_STAGE_LOG': str(stage_base / f'stages-{index}.jsonl'), 'END4_STAGE_ACTIVE': str(flag)")
    change('for tick in range(50):', 'for tick in range(80):')
    change('            flag.touch()', "            assert json.loads(ipc('scrollState'))['extent'] > 100, 'No scrollable Interface page'\n            ipc('setScrolling','true')\n            flag.touch()")
    change('            clocks = []', '            clocks = []\n            power=[]')
    change('                    time.sleep(.1)', "                    power.append({key:Path(path).read_text().strip() for key,path in {'ac':'/sys/class/power_supply/ADP0/online','sclk':'/sys/class/drm/card1/device/pp_dpm_sclk','mclk':'/sys/class/drm/card1/device/pp_dpm_mclk'}.items()})\n                    time.sleep(.1)")
    change('            after = counters(pid)', "            ipc('setScrolling','false')\n            measurement['power']=power\n            after = counters(pid)")
    change("        scope = {'__file__':", "        source = direct_fixture(source, stage_base, index, fixture)\n        scope = {'__file__':")
    change("        work = json.loads(log.read_text())", "        (stage_base/f'measurement-{index}.json').write_text(json.dumps(measurement,indent=2))\n        work = json.loads(log.read_text())")
    change("Path('/tmp/end4-native-glass-performance.json')", 'stage_base / "performance.json"')
    # The harness invokes write_text directly on the report path.
    text = text.replace('stage_base / "performance.json".write_text', '(stage_base / "performance.json").write_text')
    compile(text, str(REPO / 'tests/native-glass-performance.py'), 'exec')
    return text


def run(base):
    raise SystemExit('Prova GPU sospesa dopo i blocchi ripetuti del 15 novembre. Non avviare altre prove hardware.')
    live = desktop_processes()
    if live or os.environ.get('WAYLAND_DISPLAY') or os.environ.get('DISPLAY'):
        raise SystemExit('Use a dedicated TTY with the desktop session closed. Existing processes: ' + repr(live))
    if not sys.stdin.isatty() or not os.ttyname(sys.stdin.fileno()).startswith('/dev/tty'):
        raise SystemExit('Run directly from an active TTY, not over SSH or from a desktop terminal')
    self_test()
    subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'end4-freeze-recorder.service'], check=True)
    subprocess.run(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=5',
                    'xlini@192.168.1.199', 'test -d .local/state/end4-pC'], check=True, timeout=8)
    for name in ('baseline.so', 'profile.so'):
        if not (base / name).is_file():
            raise SystemExit('Run prepare first: missing ' + name)
    build = json.loads((base / 'build.json').read_text())
    installed = json.loads(subprocess.check_output(['Hyprland', '--version-json'], text=True))
    if installed['abiHash'] != build['hyprland']['abiHash']:
        raise SystemExit('Hyprland ABI changed; rebuild the profiling plugin first')
    for name, digest in build['binaries'].items():
        if hashlib.sha256((base / name).read_bytes()).hexdigest() != digest:
            raise SystemExit('Profiling binary changed: ' + name)
    stage_base = base / 'runs' / str(time.time_ns())
    stage_base.mkdir(parents=True, mode=0o700)
    snapshot = json.loads((Path.home() / '.config/illogical-impulse/config.json').read_text())
    (stage_base / 'config-snapshot.json').write_text(json.dumps({'background': {'widgets': {'glass': snapshot['background']['widgets']['glass']}}}))
    text = runner_source(stage_base)
    (stage_base / 'runner.py').write_text(text)
    sys.argv = [str(REPO / 'tests/native-glass-performance.py'), '--settings-interface', str(base / 'baseline.so'), str(base / 'profile.so')]
    print('Persistent run output:', stage_base, flush=True)
    status = {'complete': False, 'error': None}
    (stage_base / 'status.json').write_text(json.dumps(status))
    try:
        exec(compile(text, sys.argv[0], 'exec'), {'__file__': sys.argv[0], '__name__': '__main__', 'stage_base': stage_base, 'direct_fixture': direct_fixture})
        for file in stage_base.glob('*-fixture.log'):
            if 'Quickshell has crashed' in file.read_text(errors='replace'):
                raise RuntimeError('Quickshell restarted after a crash; comparison invalid')
        status['complete'] = True
    except BaseException as error:
        status['error'] = repr(error)
        raise
    finally:
        (stage_base / 'status.json').write_text(json.dumps(status, indent=2) + '\n')


def stage_summary(records):
    if not records or records[0].get('supported') is not True:
        raise ValueError('GPU timestamp queries were not supported')
    groups = {}
    for row in records[1:]:
        if row.get('valid') is not True:
            continue
        stage, gpu, cpu = row['stage'], row['gpu_ns'], row['cpu_ns']
        if not isinstance(stage, str) or any(type(v) is not int or v < 0 for v in (gpu, cpu)):
            raise ValueError('Invalid timing record')
        groups.setdefault(stage, []).append((gpu / 1e6, cpu / 1e6))
    required = {'capture', 'frost-copy', 'frost-blur', 'refraction-and-composition', 'redirect-total'}
    if not required <= groups.keys() or any(len(groups[k]) < 5 for k in required):
        raise ValueError('Insufficient valid stage samples')
    result = {}
    for stage, rows in groups.items():
        result[stage] = {'samples': len(rows)}
        for index, label in enumerate(('gpu', 'cpu')):
            values = sorted(r[index] for r in rows)
            result[stage][label + '_median_ms'] = round(statistics.median(values), 4)
            result[stage][label + '_p95_ms'] = round(values[int(.95 * (len(values) - 1))], 4)
    return result


def summarize(base):
    if json.loads((base / 'status.json').read_text()).get('complete') is not True:
        raise ValueError('Acquisition did not complete successfully')
    records = [json.loads(line) for line in (base / 'stages-1.jsonl').read_text().splitlines()]
    result = stage_summary(records)
    (base / 'stage-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    print('redirect-total includes capture/blur stages; do not add it to its children. GPU timelines can include idle gaps between CPU submissions.')


MOCK = r'''
#include "End4GPUTiming.hpp"
#include <cassert>
#include <string>
static bool available=false,disjoint=false;static int reads=0;static GLuint nextId=1;
extern "C" void glGetIntegerv(GLenum,GLint* p) { *p=disjoint;disjoint=false; }
extern "C" const GLubyte* glGetString(GLenum) { return nullptr; }
extern "C" __eglMustCastToProperFunctionPointerType eglGetProcAddress(const char*) { return nullptr; }
int main() {
    using namespace End4GPU;
    initialized=true;supported=true;selected=true;frame=8;output=std::tmpfile();assert(output);
    gen=[](GLsizei n,GLuint* q){while(n--)*q++=nextId++;};del=[](GLsizei,const GLuint*){};
    stamp=[](GLuint,GLenum){};ready=[](GLuint,GLenum,GLuint* p){*p=available;};
    result=[](GLuint id,GLenum,GLuint64* p){reads++;*p=id*100;};
    { Scope s("capture"); }
    drain();assert(pending.size()==1 && reads==0);
    disjoint=true;drain();assert(pending.front().invalid && reads==0);
    available=true;drain();assert(pending.empty() && reads==2);
    { Scope s("frost"); } drain();assert(pending.empty() && reads==4);
    selected=false;{ Scope s("inactive"); } assert(pending.empty());
    std::rewind(output);char buffer[2048]{};auto n=std::fread(buffer,1,sizeof(buffer)-1,output);std::string log(buffer,n);
    assert(log.find("\"valid\":false")!=std::string::npos && log.find("\"valid\":true")!=std::string::npos);
    assert(log.find("inactive")==std::string::npos);std::fclose(output);
}
'''


def self_test():
    with tempfile.TemporaryDirectory(prefix='stage-timer-check-') as directory:
        p = Path(directory)
        (p / 'End4GPUTiming.hpp').write_text(HEADER)
        (p / 'check.cpp').write_text(MOCK)
        subprocess.run(['c++', '-std=c++23', str(p / 'check.cpp'), '-o', str(p / 'check')], check=True)
        subprocess.run([str(p / 'check')], check=True)
        # ponytail: execute the actual generation statements, never the compositor fixture.
        # This covers the second compilation layer that the original self-test missed.
        runner = ast.parse(runner_source(p))
        loop = next(n for n in ast.walk(runner) if isinstance(n, ast.For) and ast.unparse(n.target) == '(index, plugin)')
        start = next(i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'source')
        end = next(i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'scope')
        prefix_end = next(i for i,n in enumerate(runner.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0]) == 'plugins')
        scope = {'__file__': str(REPO / 'tests/native-glass-performance.py'), 'stage_base': p,
                 'index': 0, 'bench_env': {}, 'measure': lambda *a: None, 'direct_fixture': direct_fixture}
        with patch.object(sys, 'argv', ['check', '--settings-interface']), patch.object(subprocess, 'Popen', side_effect=AssertionError('No processes in fixture generation')):
            exec(compile(ast.Module(body=runner.body[:prefix_end], type_ignores=[]), '<runner-prefix>', 'exec'), scope)
            exec(compile(ast.Module(body=loop.body[start:end+1], type_ignores=[]), '<fixture-generation>', 'exec'), scope)
        compile(scope['source'], '<generated-fixture>', 'exec')
        assert "    nested_env.pop('DISPLAY', None)" in scope['source']
        assert 'symlink_to' in scope['source'] and '1920x1080@60' in scope['source']
        (p / 'scroll.qml').write_text('import QtQuick\nItem { id: root\n' + SCROLL + '\n}')
        formatter = '/usr/lib/qt6/bin/qmlformat'
        subprocess.run([formatter, str(p / 'scroll.qml')], check=True, stdout=subprocess.DEVNULL)
    valid = [{'supported': True}] + [{'stage': stage, 'gpu_ns': i * 1000000, 'cpu_ns': 1000, 'valid': True}
        for stage in ('capture', 'frost-copy', 'frost-blur', 'refraction-and-composition', 'redirect-total') for i in range(1, 6)]
    assert stage_summary(valid)['capture']['gpu_median_ms'] == 3
    for rows in ([{'supported': False}], valid[:4], valid + [{'stage': 'bad', 'gpu_ns': -1, 'cpu_ns': 0, 'valid': True}]):
        try:
            stage_summary(rows)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid measurement accepted')
    print('GPU-free checks passed: queries, disjoint results, runner AND generated fixture compile, scroll QML, summaries')


if __name__ == '__main__':
    if sys.argv[1:] == ['self-test']:
        self_test()
    elif len(sys.argv) == 3 and sys.argv[1] in ('prepare', 'run', 'summarize'):
        path = Path(sys.argv[2]).expanduser().resolve()
        {'prepare': prepare, 'run': run, 'summarize': summarize}[sys.argv[1]](path)
    else:
        raise SystemExit(__doc__)
