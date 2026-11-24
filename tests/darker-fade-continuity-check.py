#!/usr/bin/env python3
"""CPU only: python3 tests/darker-fade-continuity-check.py NATIVE_SOURCE [QML_ROOT]."""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import resource
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
native=Path(sys.argv[1]);qml=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).resolve().parents[1]
header=(native/'src/Shaders.hpp').read_text()
fragment=re.search(r'\{"liquidglass.frag", R"GLSL\((.*?)\)GLSL"\}',header,re.S)[1]
def body(source,marker):
 start=source.index('{',source.index(marker))+1;depth=1
 for end in range(start,len(source)):
  depth+=(source[end]=='{')-(source[end]=='}')
  if not depth:return source[start:end]
 raise AssertionError(marker)
capture=body(fragment,'if (temporalMode == 1)')
fallback=body((qml/'modules/common/widgets/shaders/glassLumaTemporal.frag').read_text(),'void main()')
fallback=fallback.replace('materialLuma','sampleLuma')
code=r'''
#include <array>
#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
struct vec2 {float x,y;explicit vec2(float v):x(v),y(v){}};
struct ivec2 {int x,y;ivec2(int x,int y):x(x),y(y){}};
struct vec4 {
 union{float r,x;};union{float g,y;};union{float b,z;};union{float a,w;};
 vec4(float v=0):r(v),g(v),b(v),a(v){};vec4(float r,float g,float b,float a):r(r),g(g),b(b),a(a){}
 float operator[](int i)const{return std::array{r,g,b,a}[i];}
};
float mix(float a,float b,float t){return a+(b-a)*t;}
vec4 materialLuma[9],temporalStep,pixel,fragColor,gl_FragCoord;
float temporalBlend=.5f,sampleLuma=.5f;int temporalSlots[33]{},temporalHistory=0,historyLuma=0;
vec4 texelFetch(int,ivec2,int){return pixel;};vec4 texture(int,vec2){return pixel;}
void nativeCapture(){NATIVE}
void fallbackCapture(){FALLBACK}
void near(float a,float b){assert(std::abs(a-b)<.00001f);}
void check(void(*shader)()){
 for(auto values:std::array{std::array{.2f,.9f},std::array{.9f,.2f}}){
  // A long idle gap may change the target, never the last displayed origin.
  pixel=vec4(0,values[0],values[0],values[1]);temporalStep=vec4(.1f,0,2,1);
  materialLuma[0]=vec4(.5f);sampleLuma=.5f;shader();
  near(fragColor.b,values[0]);near(fragColor.g,values[1]);
  near(mix(fragColor.b,fragColor.g,0),values[0]);near(mix(fragColor.b,fragColor.g,1),values[1]);
 }
 // Interrupting a fade starts at its actual drawn fraction, not its former destination.
 for(float shown:{0.f,.25f,.75f,1.f}){
  pixel=vec4(.4f,.9f,.1f,.5f);temporalStep=vec4(.2f,0,1,shown);shader();
  near(fragColor.b,mix(.1f,.9f,shown));
 }
 // First appearance still initializes immediately, ignoring old-workspace history.
 pixel=vec4(.1f,.9f,.1f,.9f);sampleLuma=.3f;materialLuma[0]=vec4(.3f);
 temporalStep=vec4(0,0,-1,-1);shader();near(fragColor.b,.3f);near(fragColor.g,.3f);
 // A scene restart preserves the last displayed value.
 pixel=vec4(.1f,.9f,.1f,.9f);temporalStep=vec4(0,0,-1,.25f);shader();
 near(fragColor.b,.3f);near(fragColor.g,.3f);
}
int main(){check(nativeCapture);check(fallbackCapture);std::cout<<"Fade continuity: long idle gaps in both directions, interrupted fades, appearance and scene restart: OK\n";}
'''.replace('NATIVE',capture).replace('FALLBACK',fallback)
with tempfile.TemporaryDirectory(prefix='fade-continuity-check-') as directory:
 p=Path(directory);(p/'check.cpp').write_text(code)
 subprocess.run(['g++','-std=c++23','-O0',str(p/'check.cpp'),'-o',str(p/'check')],check=True)
 subprocess.run([str(p/'check')],check=True)
bar=(qml/'modules/ii/bar/Bar.qml').read_text()
dock=(qml/'modules/ii/dock/Dock.qml').read_text()
bar_visibility=re.search(r'readonly property bool automaticDarkeningVisible: ([^\n]+)\n\s*(\|\|[^\n]+)',bar)
assert bar_visibility
dock_visibility=re.search(r'readonly property bool automaticDarkeningVisible: ([^\n]+)',dock)[1]
node=r'''
const assert=require('assert/strict');
const Config={options:{bar:{autoHide:{enable:true}}}};
let mustShow=false,reveal=false;
const barTopAnimation={animation:{running:false}},barBottomAnimation={animation:{running:false}},dockOffsetAnimation={animation:{running:false}};
assert.equal(eval(BAR),false);assert.equal(eval(DOCK),false);
// Closing is still visible; reversing it must never create a false hidden/reappearing cycle.
barTopAnimation.animation.running=true;dockOffsetAnimation.animation.running=true;
assert.equal(eval(BAR),true);assert.equal(eval(DOCK),true);
mustShow=reveal=true;assert.equal(eval(BAR),true);assert.equal(eval(DOCK),true);
barTopAnimation.animation.running=dockOffsetAnimation.animation.running=false;
assert.equal(eval(BAR),true);assert.equal(eval(DOCK),true);
mustShow=reveal=false;barBottomAnimation.animation.running=true;assert.equal(eval(BAR),true);
barBottomAnimation.animation.running=false;assert.equal(eval(BAR),false);assert.equal(eval(DOCK),false);
'''.replace('BAR',json.dumps(bar_visibility[1]+' '+bar_visibility[2])).replace('DOCK',json.dumps(dock_visibility))
subprocess.run(['node','-e',node],check=True)
print('Autohide visibility: animation remains visible, reversed closing preserves history, fully hidden ends sampling: OK')
