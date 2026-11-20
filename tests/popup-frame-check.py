#!/usr/bin/env python3
"""No rendering: exercise the actual damage callback and QML animation handlers."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

root = Path(__file__).parents[1]
source = Path(sys.argv[1]) / 'src/main.cpp'
text = source.read_text()
callback = text[text.index('static void damageAdaptivePopups('):text.index('static void publishBarVisibility(')]
assert 'render.pre.listen(damageAdaptivePopups)' in text
assert not re.search(r'(?<!// )g_pHyprRenderer->damage|scheduleFrame', callback)
code = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <memory>
#include <string>
#include <utility>
#include <vector>
struct Vec { double x=0,y=0; Vec operator-()const{return {-x,-y};} };
struct CBox {
 double x,y,w,h;
 CBox(Vec p,Vec s):x(p.x),y(p.y),w(s.x),h(s.y){}
 CBox(double a,double b,double c,double d):x(a),y(b),w(c),h(d){}
 CBox& translate(Vec v){x+=v.x;y+=v.y;return *this;}
 CBox& scale(double v){x*=v;y*=v;w*=v;h*=v;return *this;}
 CBox& round(){x=std::round(x);y=std::round(y);w=std::round(w);h=std::round(h);return *this;}
 void expand(double v){x-=v;y-=v;w+=2*v;h+=2*v;}
};
struct Region {
 std::vector<CBox> boxes;
 bool empty()const{return boxes.empty();}
 Region copy()const{return *this;}
 Region& intersect(const CBox& b){std::erase_if(boxes,[&](const auto& a){return a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y;});return *this;}
};
struct Ring {Region incoming;std::vector<CBox> writes;Region getBufferDamage(int age){assert(age==1);return incoming;}void damage(CBox b){writes.push_back(b);}};
struct Monitor {int m_transform=0;double m_scale=1;Vec m_position;Ring m_damage;};
using PHLMONITOR=std::shared_ptr<Monitor>;
constexpr int WL_OUTPUT_TRANSFORM_NORMAL=0;
namespace GlassRenderer{constexpr int SAMPLE_PADDING_PX=60;}
struct Animated {Vec v;Vec value()const{return v;}};
struct Layer {
 bool m_mapped=true,m_fadingOut=false;std::weak_ptr<Monitor> m_monitor;std::string m_namespace="quickshell:popup";
 std::shared_ptr<Animated> m_realPosition=std::make_shared<Animated>(Animated{{100,200}}),m_realSize=std::make_shared<Animated>(Animated{{300,400}});
 int getPID()const{return 42;}
};
struct Surface {std::shared_ptr<Layer> layer;auto getLayerSurface(){return layer;}};
struct Global {std::vector<std::pair<int,std::shared_ptr<Surface>>> layerSurfaces;} global;
auto* g_pGlobalState=&global;
struct Dimming {float automatic=1;std::array<float,2> darkeningValue()const{return {0,automatic};}} dimming;
const Dimming* glassDarkeningOptics(int pid,const std::string& key){assert(pid==42&&key=="bar");return &dimming;}
'''+callback+r'''
int main(){
 auto m=std::make_shared<Monitor>();auto l=std::make_shared<Layer>();l->m_monitor=m;
 global.layerSurfaces={{1,std::make_shared<Surface>(Surface{l})}};
 damageAdaptivePopups(m);assert(m->m_damage.writes.empty()); // no idle frames
 m->m_damage.incoming.boxes={{120,220,10,10}};
 damageAdaptivePopups(m);assert(m->m_damage.writes.size()==1);
 auto b=m->m_damage.writes.back();assert(b.x==100&&b.y==200&&b.w==300&&b.h==400);
 m->m_damage.writes.clear();dimming.automatic=0;
 damageAdaptivePopups(m);assert(m->m_damage.writes.empty()); // manual unchanged
 dimming.automatic=1;m->m_damage.incoming.boxes={{1000,1000,10,10}};
 damageAdaptivePopups(m);assert(m->m_damage.writes.empty()); // unrelated area
 m->m_damage.incoming.boxes={{60,180,10,10}};
 damageAdaptivePopups(m);assert(m->m_damage.writes.size()==1); // sampling halo
 m->m_damage.writes.clear();m->m_position={50,100};m->m_scale=2;
 m->m_damage.incoming.boxes={{120,220,10,10}};l->m_namespace="quickshell:popupMorph";
 damageAdaptivePopups(m);assert(m->m_damage.writes.size()==1);
 b=m->m_damage.writes.back();assert(b.x==100&&b.y==200&&b.w==600&&b.h==800);
 m->m_damage.writes.clear();l->m_namespace="quickshell:settings";
 damageAdaptivePopups(m);assert(m->m_damage.writes.empty()); // other optimizations unchanged
}
'''
with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / 'check.cpp'
    exe = Path(directory) / 'check'
    cpp.write_text(code)
    subprocess.run(['g++', '-std=c++23', '-O0', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)

qml = (root / 'modules/common/widgets/StyledPopup.qml').read_text()
def block(marker):
    start = qml.index('{', qml.index(marker)) + 1
    depth = 1
    for index in range(start, len(qml)):
        depth += (qml[index] == '{') - (qml[index] == '}')
        if depth == 0:
            return qml[start:index]
assert 'running: !root.compositorAnimation' in qml
assert 'opacity: root.compositorAnimation ? 1 : 0' in qml
assert qml.count('Scale: root.compositorAnimation ? 1 :') == 2
subprocess.run(['node', '-e', '''
const assert=require('node:assert/strict');
const root={canShow:true,item:{},closing:false,popupCreated:false,compositorAnimation:false};
const GlassCompositor={active:true};
const change=new Function('root','GlassCompositor',process.argv[1]);
change(root,GlassCompositor);assert(root.compositorAnimation&&root.popupCreated);
root.canShow=false;change(root,GlassCompositor);assert(!root.closing);
root.canShow=true;GlassCompositor.active=false;change(root,GlassCompositor);
assert(!root.compositorAnimation);root.canShow=false;change(root,GlassCompositor);assert(root.closing);
let starts=0,stops=0;
const anim={start(){starts++;},restart(){starts++;},stop(){stops++;}};
const animate=new Function('root','openAnim','closeAnim',process.argv[2]);
root.compositorAnimation=true;animate(root,anim,anim);assert.equal(starts,0);assert.equal(stops,2);
root.compositorAnimation=false;root.canShow=true;animate(root,anim,anim);assert.equal(starts,1);
root.canShow=false;animate(root,anim,anim);assert.equal(starts,2);
''', block('onCanShowChanged:'), block('function onCanShowChanged()')], check=True)
print('popup frame: OK; local adaptive damage, no idle scheduling, coherent native fade, Qt animation retained')
