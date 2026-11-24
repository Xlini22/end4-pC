#!/usr/bin/env python3
"""CPU only: timing, actual GLSL arithmetic, shader compilation. No GL context.
Run: python tests/darker-temporal-check.py PATCHED_NATIVE_SOURCE [PATCHED_QML_ROOT | --qml-patch]
"""
from pathlib import Path
import json
import re
import resource
import shutil
import subprocess
import sys
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

native = Path(sys.argv[1]).resolve()
qml = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 and sys.argv[2] != '--qml-patch' else None
qml_temporary = None
if len(sys.argv) > 2 and sys.argv[2] == '--qml-patch':
    repo = Path(__file__).resolve().parents[1]
    qml_temporary = tempfile.TemporaryDirectory(prefix='qml-temporal-check-')
    qml = Path(qml_temporary.name)
    patches = [repo / 'patches' / name for name in ['glass-temporal-darkening-qml.patch', 'glass-initial-darkening-qml.patch', 'glass-darker-coherence-qml.patch']]
    for patch in patches:
        for name in re.findall(r'^diff --git a/(\S+) b/', patch.read_text(), re.M):
            if not (repo / name).is_file():
                continue
            path = qml / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / name, path)
    # Settings UI has its own CPU check; replay only material/IPC changes here.
    for patch in reversed(patches):
        applied = subprocess.run(['git', 'apply', '--exclude=modules/ii/settings/pages/GlassyConfig.qml', '--exclude=translations/it_IT.json', '--reverse', '--check', str(patch)], cwd=qml, capture_output=True)
        if applied.returncode == 0:
            subprocess.run(['git', 'apply', '--exclude=modules/ii/settings/pages/GlassyConfig.qml', '--exclude=translations/it_IT.json', '--reverse', str(patch)], cwd=qml, check=True)
    for patch in patches:
        subprocess.run(['git', 'apply', '--exclude=modules/ii/settings/pages/GlassyConfig.qml', '--exclude=translations/it_IT.json', str(patch)], cwd=qml, check=True)
header = (native / 'src/Shaders.hpp').read_text()
vertex = re.search(r'\{"darkening.vert", R"GLSL\((.*?)\)GLSL"\}', header, re.S)[1]
fragment = re.search(r'\{"liquidglass.frag", R"GLSL\((.*?)\)GLSL"\}', header, re.S)[1]

def body(source, marker):
    start = source.index('{', source.index(marker)) + 1
    depth = 1
    for end in range(start, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if depth == 0:
            return source[start:end]
    raise AssertionError('Unclosed block')

visible_box = 'vec4 visibleLumaBox(vec4 box) {' + body(vertex, 'vec4 visibleLumaBox(') + '}'
probe_source = body(vertex, 'float sampleMaterialLuma(')
assert 'vec4 clipped = visibleLumaBox(box);' in probe_source
assert 'if (clipped.z <= 0.0 || clipped.w <= 0.0) return -1.0;' in probe_source
assert 'box = clipped;' in probe_source and 'frost = 0.0;' in probe_source
layer_source = (native / 'src/GlassLayerSurface.cpp').read_text()
assert 'transformBox.intersection(CBox{0, 0, monitorWidth, monitorHeight})' in layer_source
assert 'maskInfo.darkeningClip =' in layer_source
capture = body(fragment, 'if (temporalMode == 1)')
for a, b in [('temporalStep.x','temporalStep.r'),('temporalStep.y','temporalStep.g'),('temporalStep.z','temporalStep.b'),('temporalStep.w','temporalStep.a')]:
    capture = capture.replace(a, b)
fallback = body((qml / 'modules/common/widgets/shaders/glassLumaTemporal.frag').read_text(), 'void main()') if qml else ''
fallback = fallback.replace('materialLuma', 'probe')
for a, b in [('temporalStep.x','temporalStep.r'),('temporalStep.y','temporalStep.g'),('temporalStep.z','temporalStep.b'),('temporalStep.w','temporalStep.a')]:
    fallback = fallback.replace(a, b)
native_darkness = body(fragment, 'vec3 darkenGlass(')
fallback_fragment = (qml / 'modules/common/widgets/shaders/liquidLens.frag').read_text() if qml else ''
fallback_darkness = fallback_fragment[fallback_fragment.index('    float darkness = darkening;'):fallback_fragment.index('    col += vec3(rimLight);')] if qml else ''
code = r'''
#include "DarkeningWindow.hpp"
#include <array>
#include <cassert>
#include <iostream>
struct vec2 {float x=0,y=0; explicit vec2(float v):x(v),y(v){};};
struct ivec2 {int x,y;ivec2(int a,int b):x(a),y(b){}};
struct vec4 {
 union {float r=0,x;}; union {float g=0,y;}; union {float b=0,z;}; union {float a=0,w;};
 vec4()=default;vec4(float x,float y,float z,float w):r(x),g(y),b(z),a(w){}
 float operator[](int i)const{return std::array{r,g,b,a}[i];}
};
vec2 gl_FragCoord(0);vec4 materialLuma[9],temporalStep,fragColor,pixel;
float mix(float a,float b,float t){return a+(b-a)*t;}
float probe=0,temporalBlend=0;int temporalHistory=0,historyLuma=0,temporalSlots[33]{};
float min(double a,double b){return std::min(a,b);}
float max(double a,double b){return std::max(a,b);}
vec4 darkeningClip(0,0,1,1);
VISIBLE_BOX
vec4 texelFetch(int,ivec2,int){return pixel;}
vec4 texture(int,vec2){return pixel;}
void nativeCapture(){NATIVE}
void fallbackCapture(){FALLBACK}
vec2 darkening(0);float darkeningStrength=1;
float nativeDarken(float color,int selected,float frost){NATIVE_DARKNESS}
float fallbackDarken(float col,float darkening,float automaticDarkening,float materialLuma,float automaticDarkeningStrength){FALLBACK_DARKNESS return col;}
void near(float a,float b){assert(std::abs(a-b)<.00001f);}
void sample(SDarkeningWindow& window,double now,float light,void(*shader)()){
 auto p=window.advance(now);temporalStep=vec4(p.before,p.after,float(p.windows),-1);
 materialLuma[0]=vec4(light,0,0,0);probe=light;shader();pixel=fragColor;
}
void check(void(*shader)()){
 // First appearance, including stale history from a different workspace, uses the current sample immediately.
 for(float light:{0.f,.2f,.8f,1.f}){
  pixel=vec4(.95f,.9f,.7f,.05f);temporalStep=vec4(0,0,-1,-1);
  materialLuma[0]=vec4(light,0,0,0);probe=light;shader();
  near(fragColor.r,0);near(fragColor.g,light);near(fragColor.b,light);near(fragColor.a,light);
 }

 // A scene change while continuously visible still holds the displayed tone.
 pixel=vec4(.99f,.8f,.2f,.05f);temporalStep=vec4(0,0,-1,.5f);
 materialLuma[0]=vec4(1,0,0,0);probe=1;shader();
 near(fragColor.r,0);near(fragColor.g,.5f);near(fragColor.b,.5f);near(fragColor.a,1);
 SDarkeningWindow resumed;resumed.advance(10);pixel=fragColor;
 sample(resumed,11.5,1,shader);near(pixel.g,1);near(pixel.b,.5f);

 SDarkeningWindow window;pixel={};
 sample(window,0,0,shader);
 sample(window,.25,1,shader);near(pixel.g,0);
 sample(window,1.4,0,shader);near(pixel.g,0); // Never publish intermediate frames.
 sample(window,1.5,1,shader);near(pixel.g,float(1.15/1.5));
 near(window.blend(1.5),0);near(window.blend(1.9),.5);near(window.blend(2.3),1);
 sample(window,1.75,0,shader);near(pixel.g,float(1.15/1.5));
 sample(window,3,1,shader);near(pixel.g,float(.25/1.5));
 sample(window,7.6,.3f,shader);near(pixel.g,1);near(window.blend(7.6),0); // A long static gap uses the held sample.
 sample(window,1,.8f,shader);assert(!window.published);near(pixel.g,.8f); // A reset seeds the current backdrop, never a neutral placeholder.
 window.reset();pixel={};sample(window,0,0,shader);
 for(int i=1;i<=24;++i){
  const float held=pixel.g;
  sample(window,i*.125,float(i%2),shader);
  if(i==12||i==24)near(pixel.g,.5f);else near(pixel.g,held);
 }
}
int main(){
 for(float light:{0.f,.2f,.38f,.6f,1.f})for(float strength:{0.f,.25f,.5f,1.f})for(float manual:{0.f,.7f})for(float automatic:{0.f,1.f}){
  darkening.x=manual;darkening.y=automatic;darkeningStrength=strength;materialLuma[0]=vec4(light,0,0,0);
  float expected=automatic>0 ? 1-strength*max(0.,1-.38/max(light,.38)) : 1-manual;
  near(nativeDarken(1,-1,0),expected);
  GAIN_FALLBACK
 }
 // Slide in from each edge: all four probes must land in the currently captured slice.
 for(auto clip:std::array{vec4(.98f,0,.02f,1),vec4(0,0,.02f,1),vec4(0,.98f,1,.02f),vec4(0,0,1,.02f),vec4(0,0,1,1)}){
  darkeningClip=clip;auto box=visibleLumaBox(vec4(0,0,1,1));
  near(box.x,clip.x);near(box.y,clip.y);near(box.z,clip.z);near(box.w,clip.w);
  for(float x:{.25f,.75f})for(float y:{.25f,.75f}){
   assert(box.x+box.z*x>=clip.x && box.x+box.z*x<=clip.x+clip.z);
   assert(box.y+box.w*y>=clip.y && box.y+box.w*y<=clip.y+clip.w);
  }
 }
 // In-bounds cards keep exact coordinates and the existing frosted-luma path.
 darkeningClip=vec4(0,0,1,1);auto inside=visibleLumaBox(vec4(.3f,.2f,.2f,.3f));
 assert(inside.x==.3f && inside.y==.2f && inside.z==.2f && inside.w==.3f);
 darkeningClip=vec4(.9f,0,.1f,1);
 near(visibleLumaBox(vec4(0,0,.5f,1)).z,0);
 auto clipped=visibleLumaBox(vec4(.8f,.2f,.2f,.5f));near(clipped.z,.1f);near(clipped.w,.5f);
 // Hidden cards never seed zero: their first visible sample initializes independently.
 pixel=vec4(.9f,.9f,.9f,.9f);temporalStep=vec4(.1f,0,0,-1);
 materialLuma[0]=vec4(-1,0,0,0);nativeCapture();pixel=fragColor;near(pixel.a,-1);
 temporalBlend=.75f;materialLuma[0]=vec4(.8f,0,0,0);nativeCapture();pixel=fragColor;
 near(pixel.r,.6f);near(pixel.g,.8f);near(pixel.b,.8f);near(pixel.a,.8f);
 // A scene reset cannot resume an invalid offscreen slot either.
 auto visible=pixel;pixel=vec4(0,0,0,-1);temporalStep=vec4(0,0,-1,.5f);
 nativeCapture();near(fragColor.g,.8f);near(fragColor.b,.8f);pixel=visible;
 // The existing fixed deadline still publishes a complete target, including the initialized fraction.
 temporalStep=vec4(.25f,0,1,-1);temporalBlend=0;nativeCapture();near(fragColor.g,.8f);
 check(nativeCapture);CHECK_FALLBACK
 SDarkeningWindow window;
 for(double t:std::array{0.,.1,.25,1.4,1.5,1.75,3.,7.6,7.7,1.}){
  const auto p=window.advance(t);std::cout<<p.before<<","<<p.after<<","<<p.windows<<"\n";
 }
}
'''.replace('CHECK_FALLBACK', 'check(fallbackCapture);' if qml else '').replace('GAIN_FALLBACK', 'near(fallbackDarken(1,manual,automatic,light,strength),expected);' if qml else '').replace('NATIVE_DARKNESS', native_darkness).replace('FALLBACK_DARKNESS', fallback_darkness).replace('VISIBLE_BOX', visible_box).replace('NATIVE', capture).replace('FALLBACK', fallback)
with tempfile.TemporaryDirectory(prefix='darkening-window-check-') as directory:
    tmp = Path(directory)
    cpp = tmp / 'check.cpp'; cpp.write_text(code)
    subprocess.run(['g++', '-std=c++23', '-O0', '-I', str(native / 'src'), str(cpp), '-o', str(tmp / 'check')], check=True)
    plans = subprocess.check_output([str(tmp / 'check')], text=True)
    native_plans = [[float(x) for x in row.split(',')] for row in plans.splitlines()]
    vert = tmp / 'check.vert'; frag = tmp / 'check.frag'
    vert.write_text('#version 300 es\nprecision highp float;precision highp int;\nout vec2 v_texcoord;\nvoid hyprglassMain(){v_texcoord=vec2(0);gl_Position=vec4(0);}\n' + vertex)
    frag.write_text(fragment.lstrip())
    subprocess.run(['glslangValidator', '-l', str(vert), str(frag)], check=True, stdout=subprocess.DEVNULL)
    if qml:
        helper = (qml / 'modules/common/functions/DarkeningWindow.js').read_text().replace('.pragma library', '')
        js = helper + '\nconst s=create();console.log(JSON.stringify([0,.1,.25,1.4,1.5,1.75,3,7.6,7.7,1].map(t=>advance(s,t))));'
        js_plans = json.loads(subprocess.check_output(['node', '-e', js], text=True))
        for actual, expected in zip(native_plans, js_plans, strict=True):
            assert all(abs(a - b) < .00001 for a, b in zip(actual, expected[:3], strict=True))
        for name in ['liquidLens.vert', 'glassLumaTemporal.vert', 'glassLumaTemporal.frag']:
            source = qml / 'modules/common/widgets/shaders' / name
            subprocess.run(['/usr/lib/qt6/bin/qsb', '--qt6', '-o', str(tmp / (name + '.qsb')), str(source)], check=True)
        source = (qml / 'modules/common/widgets/FrostedGlass.qml').read_text()
        assert 'settled.restart()' not in source and 'onSourceRectChanged' not in source
        assert 'repeat: true' in source and 'DarkeningWindow.advance(timeState' in source
        assert '        live: true' in source
        assert 'format: ShaderEffectSource.RGBA32F' in source
        assert 'blending: false' in source
        assert 'import qs.services' in source and 'GlassProfiles.darkeningStrength(opticalProfile)' in source
renderer = (native / 'src/GlassRenderer.cpp').read_text()
assert 'glReadPixels' not in renderer and 'glClientWaitSync' not in renderer
assert 'temporalSlots' in renderer and 'mask->temporalSample' in renderer
assert 'glUniform4fv(uniforms.darkeningClip, 1, lumaClip.data())' in renderer
assert 'glUniform1f(uniforms.temporalBlend, float((now - state.clock.start) / SDarkeningWindow::PERIOD))' in renderer
assert 'glBindSampler(3, oldSampler)' in renderer
assert 'glColorMask(colorMask[0], colorMask[1], colorMask[2], colorMask[3])' in renderer
print('temporal darker: OK (time-weighted means, fixed windows, held targets, smooth transitions, idle gaps, reset, offscreen entrance probes, per-card initialization, native/QML parity and offline shaders; no rendering)')

if qml_temporary:
    qml_temporary.cleanup()
