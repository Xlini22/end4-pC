#!/usr/bin/env python3
"""CPU only: python tests/glass-reflections-check.py PATCHED_NATIVE_SOURCE [QML_ROOT | --qml-patch]."""
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
native = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='glass-reflections-') as directory:
    tmp = Path(directory)
    qml = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 and sys.argv[2] != '--qml-patch' else repo
    if len(sys.argv) > 2 and sys.argv[2] == '--qml-patch':
        qml = tmp / 'qml'
        for name in ['liquidLens.frag', 'liquidLens.frag.qsb']:
            relative = Path('modules/common/widgets/shaders') / name
            (qml / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / relative, qml / relative)
        patch = repo / 'patches/glass-frost-reflections-qml.patch'
        pending = subprocess.run(['git', 'apply', '--check', str(patch)], cwd=qml, capture_output=True)
        subprocess.run(['git', 'apply', *([] if pending.returncode == 0 else ['--reverse', '--check']), str(patch)], cwd=qml, check=True)
    source = (native / 'src/Shaders.hpp').read_text()
    start = source.index('    color = darkenGlass(color, selected, frost);')
    end = source.index('    // INNER SHADOW', start)
    highlights = source[source.index('    if (', start):end]
    fragment = qml / 'modules/common/widgets/shaders/liquidLens.frag'
    fallback = fragment.read_text()
    assignment = re.search(r'rimLight = proximity \* proximity[^;]*;', fallback)[0]
    addition = re.search(r'[^\n]*col \+= vec3\(rimLight\);', fallback)[0]
    code = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
using std::max;using std::pow;
struct vec2 {float x,y;};
struct vec3 {
 float r,g,b;
 explicit vec3(float x):r(x),g(x),b(x){}
 vec3(float x,float y,float z):r(x),g(y),b(z){}
 vec3& operator+=(vec3 v){r+=v.r;g+=v.g;b+=v.b;return *this;}
};
vec3 operator*(vec3 v,float s){return vec3(v.r*s,v.g*s,v.b*s);}
vec3 nativeReflection(float frost,float reflection,float edgeProximity,float y){
 float fresnelStrength=reflection*.7f,specularStrength=reflection;vec2 opticUV{0,y};vec3 color(0);
 NATIVE
 return color;
}
vec3 fallbackReflection(float frosted,float sheen,float proximity,float topBias){
 float rimLight=0;vec3 col(0);
 ASSIGNMENT
 ADDITION
 return col;
}
void near(float a,float b){assert(std::abs(a-b)<.00001f);}
int main(){
 for(float frost:{0.f,1.5f,8.f,32.f}){
  near(nativeReflection(frost,0,1,0).r,0);
  near(nativeReflection(frost,.5f,1,0).r,.0925f);
  near(nativeReflection(frost,1,1,0).r,.185f);
  near(nativeReflection(frost,1,0,0).r,0); // Flat center stays unchanged.
  assert(nativeReflection(frost,1,1,0).r>nativeReflection(frost,1,1,1).r);
 }
 for(float frosted:{0.f,1.f})for(float sheen:{0.f,.5f,1.f}){
  near(fallbackReflection(frosted,sheen,1,1).r,nativeReflection(0,sheen,1,0).r);
  near(fallbackReflection(frosted,sheen,0,1).r,0);
 }
}
'''.replace('NATIVE', highlights).replace('ASSIGNMENT', assignment).replace('ADDITION', addition)
    (tmp / 'check.cpp').write_text(code)
    subprocess.run(['g++', '-std=c++23', '-O0', str(tmp / 'check.cpp'), '-o', str(tmp / 'check')], check=True)
    subprocess.run([str(tmp / 'check')], check=True)
    subprocess.run(['/usr/lib/qt6/bin/qsb', '--qt6', '-o', str(tmp / 'liquidLens.frag.qsb'), str(fragment)], check=True)
    assert 'opticSdf <= -bezelWidthPx' in source  # Preserve the optimized flat-center path.
    assert source.index('color = darkenGlass(color, selected, frost);') < source.index('if (fresnelStrength > 0.001)')
print('Edge reflections: OK (real shader arithmetic, frosted/clear materials, 0/50/100%, unchanged center, native/fallback parity and offline QSB; no rendering)')
