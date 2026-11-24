#!/usr/bin/env python3
"""CPU only: python3 tests/bar-section-darkening-check.py NATIVE_SOURCE [QML_ROOT]."""
from pathlib import Path
import json
import re
import resource
import subprocess
import sys
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
native = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parents[1]
qml = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else repo
vertex = re.search(r'\{"darkening.vert", R"GLSL\((.*?)\)GLSL"\}', (native/'src/Shaders.hpp').read_text(), re.S)[1]

def body(text, marker):
    start = text.index('{', text.index(marker)) + 1
    depth = 1
    for end in range(start, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if depth == 0:
            return text[start:end]
    raise AssertionError(marker)

probe = body(vertex, 'if (points > 0)')
# Execute the actual mean-probe branch as C++, replacing only vector swizzles.
probe = probe.replace('box.xy', 'vec2(box.x,box.y)').replace('box.zw', 'vec2(box.z,box.w)').replace('.rgb', '')
cpp = r'''
#include "GlassRegions.hpp"
#include "DarkeningWindow.hpp"
#include <cassert>
#include <iostream>
#include <utility>
struct vec2 {float x,y;vec2(float x,float y):x(x),y(y){}};
vec2 operator+(vec2 a,vec2 b){return {a.x+b.x,a.y+b.y};}
vec2 operator-(float a,vec2 b){return {a-b.x,a-b.y};}
vec2 operator*(vec2 a,vec2 b){return {a.x*b.x,a.y*b.y};}
vec2 operator*(float a,vec2 b){return {a*b.x,a*b.y};}
struct vec3 {float r,g,b;explicit vec3(float v):r(v),g(v),b(v){};vec3(float r,float g,float b):r(r),g(g),b(b){}};
struct vec4 {float x,y,z,w;};
vec3 max(vec3 a,vec3 b){return {std::max(a.r,b.r),std::max(a.g,b.g),std::max(a.b,b.b)};}
float dot(vec3 a,vec3 b){return a.r*b.r+a.g*b.g+a.b*b.b;}
vec2 clamp(vec2 a,float low,float high){return {std::clamp(a.x,low,high),std::clamp(a.y,low,high)};}
vec2 uvPadding{0,0},sampleUVScale{1,1},sampleUVOffset{0,0};int tex=0;
std::vector<vec2> reads;std::vector<float> brightness;
vec3 textureLod(int,vec2 uv,float){reads.push_back(uv);return vec3(brightness.at(reads.size()-1));}
float sample(int points,vec4 box){PROBE}
bool close(float a,float b){return std::abs(a-b)<.00001;}
std::string request(int version,int group=1,std::string name="quickshell:bar",std::string box="10 0 100 20") {
 std::string s="end4glass 123 "+std::to_string(version)+" 1 "+name+" eDP-1 1000 40 1 1 9 10 0 100 20 0 0 0 0 0 0 0 0 0 1 0";
 if(version>=5)s+=" "+std::to_string(group)+" "+box;
 return s;
}
int main(){
 SGlassClient client;assert(parseGlassRegions(request(4),client));assert(client.surfaces[0].regions[0].darkeningGroup==0);
 assert(parseGlassRegions(request(5),client));assert(client.surfaces[0].regions[0].darkeningGroup==1);
 const auto valid=client.surfaces;
 for(auto bad:{request(6),request(5,4),request(5,-1),request(5,1,"quickshell:dock"),
    request(5,1,"quickshell:bar","0 0 0 20"),request(5,1,"quickshell:bar","nan 0 100 20"),
    request(5,0),request(5)+" extra"}) {
  assert(!parseGlassRegions(bad,client));assert(client.surfaces==valid);
 }
 assert(parseGlassRegions(request(5,0,"quickshell:dock","0 0 0 0"),client));
 std::vector<SGlassRegion> regions;
 for(int group=1;group<=3;++group)for(int nested=0;nested<5;++nested){
  SGlassRegion region;region.id=100*group+nested;region.darkeningGroup=group;
  region.darkeningBox={float(group*200),10,float(group*100),20};regions.push_back(region);
 }
 auto sections=glassBarDarkeningRegions(regions);assert(sections.size()==3);
 int total=0;for(int i=0;i<3;++i){assert(sections[i].id==-i-1);total+=sections[i].samplePoints;}
 assert(total==7&&sections[1].samplePoints==3);
 std::reverse(regions.begin(),regions.end());auto reordered=glassBarDarkeningRegions(regions);assert(sections==reordered);
 for(auto& region:regions){region.id+=1000;region.darkeningBox[2]+=17;}
 auto resized=glassBarDarkeningRegions(regions);for(int i=0;i<3;++i)assert(resized[i].id==sections[i].id);
 for(auto& region:regions)if(region.darkeningGroup==2)region.opacity=0;
 auto hidden=glassBarDarkeningRegions(regions);assert(hidden.size()==2&&hidden[0].id==-1&&hidden[1].id==-3);
 assert(glassBarDarkeningRegions({}).empty());
 for(int n:{2,3}) {
  reads.clear();brightness=n==2?std::vector<float>{0,1}:std::vector<float>{0,1,0};
  assert(close(sample(n,{.1f,.2f,.6f,.4f}),1.f/n));assert(reads.size()==size_t(n));
  for(int i=0;i<n;++i){assert(close(reads[i].x,.1f+.6f*(i+.5f)/n));assert(close(reads[i].y,.4f));}
 }
 // A common clock, separate accumulators: local means never leak into the other sections.
 SDarkeningWindow clock;clock.advance(0);assert(clock.advance(.75).windows==0);assert(clock.advance(1.5).windows==1);
 std::cout<<"Bar sections: parser v4/v5, atomic rejection, stable groups, 2/3/2 probe means and positions: OK\n";
}
'''.replace('PROBE',probe)
with tempfile.TemporaryDirectory(prefix='bar-sections-check-') as directory:
    path=Path(directory);(path/'check.cpp').write_text(cpp)
    subprocess.run(['g++','-std=c++23','-O0','-I',str(native/'src'),str(path/'check.cpp'),'-o',str(path/'check')],check=True)
    subprocess.run([str(path/'check')],check=True)
bar=(qml/'modules/ii/bar/BarContent.qml').read_text()
for item,group in [('leftSection',1),('absoluteCenter',2),('rightSection',3),('centerPill',2)]:
    assert f'id: {item}\n' in bar and re.search(r'id: '+item+r'\n\s*readonly property int glassDarkeningSection: '+str(group),bar)
window=(qml/'modules/common/widgets/WindowGlass.qml').read_text()
assert 'if (win?.WlrLayershell.namespace !== "quickshell:bar") return null' in window
assert 'darkeningSection.mapToItem(win.contentItem' in window
assert 'onDarkeningSectionGeometryChanged: GlassCompositor.queueRegions()' in window
owner = body(window, 'readonly property Item darkeningSection:')
node = r'''
const assert=require('assert/strict');
const choose=new Function('win','parent',OWNER);
const left={glassDarkeningSection:1,parent:null}, center={glassDarkeningSection:2,parent:null};
const win={WlrLayershell:{namespace:'quickshell:bar'}};
assert.equal(choose(win,{parent:{parent:left}}),left);
assert.equal(choose(win,{parent:center}),center);
const centerCarrier={glassDarkeningSection:2,glassDarkeningSectionReference:center,parent:null};
assert.equal(choose(win,{parent:centerCarrier}),center);
assert.equal(choose(win,{parent:null}),null);
assert.equal(choose({WlrLayershell:{namespace:'quickshell:verticalBar'}},left),null);
assert.equal(choose({WlrLayershell:{namespace:'quickshell:dock'}},left),null);
'''.replace('OWNER', json.dumps(owner))
subprocess.run(['node', '-e', node], check=True)
assert 'readonly property Item glassDarkeningSectionReference: absoluteCenter' in bar
compositor=(qml/'services/GlassCompositor.qml').read_text()
assert 'sectionDarkeningAvailable ? 5 : darkeningStrengthAvailable ? 4' in compositor
assert 'if (sectionDarkeningAvailable) values.push(...region.section)' in compositor
sender = body(compositor, 'function sendRegions()')
send_check = r'''
const assert=require('assert/strict'),vm=require('vm');
const win={width:1000,height:40};
const context={enhancedAvailable:true,enhancedActive:true,regionsBusy:false,sectionDarkeningAvailable:true,
    darkeningStrengthAvailable:true,darkeningVisibilityAvailable:true,frostedAvailable:true,
    Quickshell:{processId:123},regionsApplied:'',regionsRejected:'',regionWrites:0,regionSocket:{connected:false},
    glassItems:[{nativeRegion:()=>({win,name:'quickshell:bar',monitor:'eDP-1',id:9,priority:0,
        darkeningVisible:true,values:[10,0,100,20,0,0,0,0,0,0,0,0,0,1,0],section:[1,10,0,100,20]})}]};
vm.createContext(context);vm.runInContext('function send(){'+BODY+'}',context);
context.send();
assert.equal(context.regionsSent,'end4glass 123 5 1 quickshell:bar eDP-1 1000 40 1 1 9 10 0 100 20 0 0 0 0 0 0 0 0 0 1 0 1 10 0 100 20');
context.regionsBusy=false;context.sectionDarkeningAvailable=false;context.send();
assert.equal(context.regionsSent,'end4glass 123 4 1 quickshell:bar eDP-1 1000 40 1 1 9 10 0 100 20 0 0 0 0 0 0 0 0 0 1 0');
'''.replace('BODY', json.dumps(sender))
subprocess.run(['node', '-e', send_check], check=True)
renderer=(native/'src/GlassRenderer.cpp').read_text()
assert 'mask->sectionDarkening ? -material.darkeningGroup : material.id' in renderer
assert 'current.id != 0 ? old.id == current.id' in renderer
print('QML section inheritance, geometry refresh, capability-gated IPC and history routing: OK (no rendering)')
