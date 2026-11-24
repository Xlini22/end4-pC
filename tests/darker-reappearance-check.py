#!/usr/bin/env python3
"""CPU only. Run: python tests/darker-reappearance-check.py PATCHED_NATIVE_SOURCE [PATCHED_QML_ROOT | --qml-patch]"""
from pathlib import Path
import json
import resource
import re
import shutil
import subprocess
import sys
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
src = Path(sys.argv[1]).resolve() / 'src'
qml_temporary = None
if sys.argv[2] == '--qml-patch':
    repo = Path(__file__).resolve().parents[1]
    qml_temporary = tempfile.TemporaryDirectory(prefix='qml-reappearance-check-')
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
else:
    qml = Path(sys.argv[2]).resolve()
layer = (src / 'GlassLayerSurface.cpp').read_text()

def body(source, marker):
    start = source.index('{', source.index(marker)) + 1
    depth = 1
    for end in range(start, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if not depth:
            return source[start:end]
    raise AssertionError(marker)

header = (src / 'GlassRenderer.hpp').read_text()
start = header.index('struct SAdaptiveDarkening {')
state = header[start:header.index('\n};', start) + 3].replace('std::chrono::steady_clock::now()', 'testNow()')
# Only the timer/visibility methods under test; no GL library or compositor.
methods = layer[layer.index('void CGlassLayerSurface::updateDarkeningVisibility()'):layer.index('void CGlassLayerSurface::damageMaterial()')]
# Inject a deterministic clock into the extracted production methods; no sleeps or rendering.
methods = methods.replace('std::chrono::steady_clock::now()', 'testNow()')
main = (src / 'main.cpp').read_text()
route = 'static void queueDarkeningSceneChange(SP<Monitor> monitor) {' + body(main, 'static void queueDarkeningSceneChange(') + '}'
code = r'''
#include "DarkeningWindow.hpp"
#include "GlassRegions.hpp"
#include <array>
#include <cassert>
#include <chrono>
#include <functional>
#include <memory>
#include <utility>
#include <unordered_map>
using GLuint=unsigned;
template<class T> using SP=std::shared_ptr<T>;
template<class T,class... A> auto makeShared(A&&... a){return std::make_shared<T>(std::forward<A>(a)...);}
namespace Time {using steady_dur=std::chrono::steady_clock::duration;}
double fakeTime=10;
static auto testNow(){return std::chrono::steady_clock::time_point(std::chrono::duration_cast<Time::steady_dur>(std::chrono::duration<double>(fakeTime)));}
struct CEventLoopTimer {
 std::function<void(SP<CEventLoopTimer>,void*)> callback;
 bool active=false,cancelled=false;int arms=0;double delay=0;
 CEventLoopTimer(std::optional<Time::steady_dur>,decltype(callback) cb,void*):callback(cb){}
 void updateTimeout(std::optional<Time::steady_dur> value){
  active=value.has_value();if(value){++arms;delay=std::chrono::duration<double>(*value).count();}
 }
 bool armed()const{return active;}
 void cancel(){active=false;cancelled=true;}
 void fire(){if(!active||cancelled)return;active=false;callback(nullptr,nullptr);}
};
struct Loop {int adds=0;void addTimer(SP<CEventLoopTimer>){++adds;}} loop;
auto g_pEventLoopManager=&loop;
STATE
SAdaptiveDarkening::~SAdaptiveDarkening()=default;
struct Alpha {float value()const{return 1;}};
struct Animated {bool active=false;bool isBeingAnimated()const{return active;}};
struct Workspace {SP<Animated> m_renderOffset=makeShared<Animated>(),m_alpha=makeShared<Animated>();};
struct Monitor {SP<Workspace> m_activeWorkspace=makeShared<Workspace>(),m_activeSpecialWorkspace;};
struct Layer {bool m_mapped=true,m_fadingOut=false;SP<Alpha> m_alpha=makeShared<Alpha>();std::weak_ptr<Monitor> m_monitor;};
struct CGlassLayerSurface {
 std::weak_ptr<Layer> m_layerSurface;
 SGlassSurface surface;
 bool m_darkeningVisible=false,materialVisible=true,m_darkeningScenePending=false;
 double m_darkeningSceneChanged=0;
 SAdaptiveDarkening m_temporalDarkening;
 SP<CEventLoopTimer> m_darkeningTimer;
 int damage=0;
 const SGlassSurface* enhancedSurface(){return &surface;}
 bool hasVisibleMaterial(){return materialVisible;}
 SP<Layer> getLayerSurface(){return m_layerSurface.lock();}
 void damageMaterial(){++damage;}
 void updateDarkeningVisibility();void scheduleDarkeningPublication();
 void noteDarkeningSceneChange(bool repaint=true);bool needsDarkeningPublication();
 ~CGlassLayerSurface(){if(m_darkeningTimer)m_darkeningTimer->cancel();}
};
METHODS
struct Global {std::unordered_map<int,SP<CGlassLayerSurface>> layerSurfaces;} global;
auto g_pGlobalState=&global;
ROUTE
static double now(){return fakeTime;}
// Publication-only scenarios mark their mocked fades settled; a separate block drives the full fade.
int main(){
 SGlassClient client;
 assert(parseGlassRegions("end4glass 42 3 1 quickshell:dock eDP-1 1920 100 1 1 7 0 100 50 10 10 10 10 0 0 0 0 1 1 8",client));
 assert(client.surfaces[0].darkeningVisible&&client.surfaces[0].regions[0].frost==8);
 const std::string head="end4glass 42 3 1 quickshell:dock eDP-1 1920 100 0 ";
 assert(parseGlassRegions(head+"0",client)&&!client.surfaces[0].darkeningVisible);
 assert(parseGlassRegions(head+"1",client)&&client.surfaces[0].darkeningVisible);
 for(auto invalid:{"-1","2","nan","","1 trailing"}){
  assert(!parseGlassRegions(head+invalid,client));assert(client.surfaces[0].darkeningVisible);
 }
 assert(parseGlassRegions("end4glass 42 2 1 quickshell:dock eDP-1 1920 100 0",client));
 assert(client.surfaces[0].darkeningVisible); // Old clients keep their current behaviour.
 SP<CEventLoopTimer> retained;
 {
  auto layer=makeShared<Layer>();CGlassLayerSurface view;view.m_layerSurface=layer;
  view.surface.darkeningVisible=false;view.updateDarkeningVisibility();
  assert(!view.m_darkeningVisible&&!view.m_darkeningTimer);
  view.surface.darkeningVisible=true;view.updateDarkeningVisibility();
  assert(view.m_darkeningVisible&&!view.m_temporalDarkening.clock.initialized);
  auto& history=view.m_temporalDarkening;history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  retained=view.m_darkeningTimer;assert(retained->armed()&&loop.adds==1);
  assert(retained->delay>1.4&&retained->delay<=1.5);
  for(int i=0;i<10;++i)view.scheduleDarkeningPublication();
  assert(retained->arms==1); // Continuous geometry changes never postpone the fixed deadline.
  retained->fire();assert(view.damage==1&&!retained->armed());
  history.clock.advance(history.clock.start+1.5);history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  assert(history.clock.published&&!retained->armed());
  for(int i=0;i<10;++i)view.scheduleDarkeningPublication();
  assert(retained->arms==1); // No idle periodic rendering after publication.
  history.clock.changed=now()-.4;
  view.surface.darkeningVisible=false;view.updateDarkeningVisibility();
  assert(!view.m_darkeningVisible&&!retained->armed());
  view.surface.darkeningVisible=true;view.updateDarkeningVisibility();
  assert(!history.clock.initialized&&history.resumeBlend<0); // Reappearance samples the new scene, not the old held tone.
  history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  assert(retained->armed()&&loop.adds==1); // Existing timer reused on reveal.
  view.surface.darkeningVisible=false;retained->fire();
  assert(view.damage==1&&!view.m_darkeningVisible); // Hidden while callback was pending.
  view.surface.darkeningVisible=true;view.updateDarkeningVisibility();
  history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  layer->m_mapped=false;retained->fire();assert(view.damage==1&&!view.m_darkeningVisible);
  layer->m_mapped=true;view.updateDarkeningVisibility();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  layer->m_fadingOut=true;view.updateDarkeningVisibility();assert(!retained->armed());
  layer->m_fadingOut=false;view.updateDarkeningVisibility();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  assert(retained->armed());
 }
 assert(retained->cancelled&&!retained->armed());retained->fire(); // Cannot call the destroyed owner.
 {
  auto layer=makeShared<Layer>();auto monitor=makeShared<Monitor>();layer->m_monitor=monitor;
  CGlassLayerSurface view;view.m_layerSurface=layer;view.updateDarkeningVisibility();
  auto& history=view.m_temporalDarkening;
  fakeTime=20;history.clock.advance(now());fakeTime=21.5;history.clock.advance(now());history.clock.changed=now()-1;
  view.scheduleDarkeningPublication();assert(!view.m_darkeningTimer); // Previously settled, continuously visible dock.
  fakeTime=30;view.noteDarkeningSceneChange();assert(view.damage==1&&view.m_darkeningScenePending);
  const auto held=history.resumeBlend;history.restart(now());assert(history.resumeBlend==held); // Multiple notifications cannot erase the held tone.
  history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();auto timer=view.m_darkeningTimer;
  assert(timer->armed()&&timer->arms==1&&timer->delay==1.5);
  // Scene keeps changing: publish at 1.5 s intervals instead of postponing the current deadline.
  for(double t:{30.1,30.2,30.5}){
   fakeTime=t;monitor->m_activeWorkspace->m_renderOffset->active=true;
   view.updateDarkeningVisibility();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
   assert(history.clock.start==30&&timer->arms==1&&view.damage==1);
  }
  monitor->m_activeWorkspace->m_renderOffset->active=false;
  fakeTime=31.5;timer->fire();assert(view.damage==2);history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  assert(history.clock.published&&history.clock.start==31.5&&timer->armed()&&timer->arms==2);
  assert(timer->delay==1.5); // One more complete window contains the settled scene.
  fakeTime=32;history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();assert(timer->arms==2);
  fakeTime=33;timer->fire();assert(view.damage==3);history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  assert(!view.m_darkeningScenePending&&!timer->armed());
  for(double t:{33.1,33.4,33.8,34.0}){fakeTime=t;view.updateDarkeningVisibility();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();}
  assert(timer->arms==2&&view.damage==3); // Darker/fade-only frames never dirty the scene or sustain a loop.
  // A cancelled workspace gesture also drains; no committed workspace event is required.
  fakeTime=40;monitor->m_activeWorkspace->m_renderOffset->active=true;view.updateDarkeningVisibility();
  history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();assert(timer->armed());
  fakeTime=40.3;view.updateDarkeningVisibility();history.clock.advance(now());
  monitor->m_activeWorkspace->m_renderOffset->active=false;
  fakeTime=41.5;timer->fire();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  fakeTime=43;timer->fire();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();assert(!timer->armed());
  // Continuous external changes still publish each fixed 1.5 s boundary (not a debounce).
  fakeTime=44;view.noteDarkeningSceneChange();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  for(int i=1;i<=9;++i){
   fakeTime=44+i*.5;view.noteDarkeningSceneChange(false);
   if(i%3==0)timer->fire();
   history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
   assert(history.clock.start==44+(i/3)*1.5&&timer->armed());
  }
  fakeTime=50;timer->fire();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  assert(!timer->armed()&&!view.m_darkeningScenePending);
  // Visibility loss still cancels pending scene work immediately.
  fakeTime=51;view.noteDarkeningSceneChange();history.clock.advance(now());history.clock.changed=now()-1;view.scheduleDarkeningPublication();
  view.surface.darkeningVisible=false;view.updateDarkeningVisibility();assert(!timer->armed()&&!view.m_darkeningScenePending);
 }
 {
  // A static desktop must display the fade even if damage requested inside a draw is consumed.
  fakeTime=60;auto layer=makeShared<Layer>();CGlassLayerSurface view;view.m_layerSurface=layer;
  view.updateDarkeningVisibility();auto& history=view.m_temporalDarkening;
  history.clock.advance(now());view.scheduleDarkeningPublication();auto timer=view.m_darkeningTimer;
  fakeTime=61.5;timer->fire();history.clock.advance(now());history.presentedBlend=0;view.scheduleDarkeningPublication();
  assert(timer->armed()&&timer->delay>0&&timer->delay<=1.0/60+.000001);
  const auto deadline=history.clock.start;const int before=view.damage;
  // Each tick arrives outside the draw and requests only this material; ordinary frames are simulated explicitly.
  for(int i=1;i<48;++i){
   fakeTime=61.5+i/60.0;timer->fire();history.clock.advance(now());
   history.presentedBlend=history.clock.blend(now());view.scheduleDarkeningPublication();
   assert(timer->armed()&&history.clock.start==deadline);
  }
  // The last tick still damages after the 800 ms deadline, so the final value is actually drawn.
  fakeTime=62.301;const int damage=view.damage;timer->fire();assert(view.damage==damage+1);
  history.clock.advance(now());history.presentedBlend=history.clock.blend(now());view.scheduleDarkeningPublication();
  assert(history.presentedBlend==1&&!timer->armed()&&view.damage==before+48);
  fakeTime=65;timer->fire();assert(!timer->armed()&&view.damage==before+48);
  // Hiding a material during its fade cancels the timer immediately.
  fakeTime=70;history.clock.advance(now());history.presentedBlend=0;view.scheduleDarkeningPublication();assert(timer->armed());
  view.surface.darkeningVisible=false;timer->fire();assert(!timer->armed());
 }
 {
  auto first=makeShared<Monitor>(),second=makeShared<Monitor>();
  auto firstLayer=makeShared<Layer>(),secondLayer=makeShared<Layer>(),hiddenLayer=makeShared<Layer>();
  firstLayer->m_monitor=first;secondLayer->m_monitor=second;hiddenLayer->m_monitor=first;
  auto a=makeShared<CGlassLayerSurface>(),b=makeShared<CGlassLayerSurface>(),hidden=makeShared<CGlassLayerSurface>();
  a->m_layerSurface=firstLayer;b->m_layerSurface=secondLayer;hidden->m_layerSurface=hiddenLayer;
  hidden->surface.darkeningVisible=false;
  global.layerSurfaces={{1,a},{2,b},{3,hidden}};
  queueDarkeningSceneChange(first);assert(a->damage==1&&b->damage==0&&hidden->damage==0);
  queueDarkeningSceneChange(nullptr);assert(a->damage==1&&b->damage==0);
  queueDarkeningSceneChange(second);assert(a->damage==1&&b->damage==1&&hidden->damage==0);
  global.layerSurfaces.clear();
 }


}
'''.replace('STATE', state).replace('METHODS', methods).replace('ROUTE', route)
with tempfile.TemporaryDirectory(prefix='darker-reappearance-') as directory:
    tmp = Path(directory)
    (tmp / 'check.cpp').write_text(code)
    subprocess.run(['g++', '-std=c++23', '-O0', '-I', str(src), str(tmp / 'check.cpp'), '-o', str(tmp / 'check')], check=True)
    subprocess.run([str(tmp / 'check')], check=True)
    frost = (qml / 'modules/common/widgets/FrostedGlass.qml').read_text()
    js = (qml / 'modules/common/functions/DarkeningWindow.js').read_text().replace('.pragma library', '')
    complete = body(frost, 'onScheduledUpdateCompleted:')
    script = js + '\n' + '\n'.join('function ' + name + '() {' + body(frost, 'function ' + name + '(') + '}' for name in ['sample', 'visibilityChanged'])
    script += '\nfunction complete() {' + complete + '}\n'
    script += r'''
let time=10,scheduled=0,stops=0,starts=0;
const context={DarkeningWindow:{create,advance},Qt:{vector4d:(...v)=>Object.assign(v,{z:v[2]})},
 Date:{now:()=>time*1000},timeState:create(),busy:false,samplingVisible:false,
 restartPending:false,initializing:false,blend:.4,
 history:{scheduleUpdate(){++scheduled}},fade:{pause(){},stop(){++stops},start(){++starts}}};
context.state=context;
vm.createContext(context);vm.runInContext(FUNCTIONS,context);
context.sample();assert.equal(scheduled,0);
context.visibilityChanged();assert(context.restartPending);assert.equal(scheduled,0);assert(!context.initializing);
context.samplingVisible=true;context.visibilityChanged();assert.equal(scheduled,1);
assert.equal(context.step[2],-1);assert.equal(context.step[3],-1);assert.equal(context.timeState.start,10);
assert(context.initializing);context.complete();assert.equal(context.blend,1);assert(!context.busy);assert(!context.initializing);
time=11.5;context.sample();assert.equal(context.step[2],1);context.complete();assert.equal(starts,1);
// A reveal arriving during an outstanding update must reset after that completion, not publish its old mean.
context.busy=true;context.samplingVisible=false;context.visibilityChanged();
time=20;context.samplingVisible=true;context.visibilityChanged();const before=scheduled;
assert(context.initializing);context.complete();assert.equal(scheduled,before+1);assert.equal(context.step[2],-1);assert(context.initializing);
assert.equal(context.timeState.start,20);assert.equal(starts,1);
'''
    # The extracted QML functions execute in their own property scope, just as in the component.
    first, checks = script.split('let time=10', 1)
    runner = "const vm=require('vm'),assert=require('assert/strict');\n" + js + '\nconst FUNCTIONS=' + json.dumps(first) + ';\nlet time=10' + checks
    sender = body((qml / 'services/GlassCompositor.qml').read_text(), 'function sendRegions(')
    runner += '\nconst SEND=' + json.dumps('function sendRegions(){' + sender + '}') + ';\n'
    runner += r'''
const region={id:123,win:{width:1920,height:100},name:'quickshell:dock',monitor:'eDP-1',priority:0,
 darkeningVisible:true,values:[7,0,100,50,10,10,10,10,0,0,0,0,1,1,8]};
const sender={regionsPending:true,enhancedAvailable:true,regionsBusy:false,enhancedActive:true,
 glassItems:[{nativeRegion:()=>region}],darkeningVisibilityAvailable:true,darkeningStrengthAvailable:false,frostedAvailable:true,sectionDarkeningAvailable:false,
 Quickshell:{processId:42},regionsApplied:'',regionsRejected:'',regionWrites:0,regionSocket:{connected:false}};
sender.root=sender;vm.createContext(sender);vm.runInContext(SEND,sender);sender.sendRegions();
let tokens=sender.regionsSent.split(' ');assert.equal(tokens[2],'3');assert.equal(tokens[9],'1');assert.equal(tokens[10],'7');
const size=tokens.length;region.darkeningVisible=false;sender.regionsBusy=false;sender.sendRegions();
assert.equal(sender.regionsSent.split(' ')[9],'0');
sender.darkeningVisibilityAvailable=false;sender.regionsBusy=false;sender.sendRegions();
tokens=sender.regionsSent.split(' ');assert.equal(tokens[2],'2');assert.equal(tokens[9],'7');assert.equal(tokens.length,size-1);
sender.darkeningVisibilityAvailable=true;sender.darkeningStrengthAvailable=true;sender.regionsBusy=false;sender.sendRegions();
tokens=sender.regionsSent.split(' ');assert.equal(tokens[2],'4');assert.equal(tokens[9],'0');assert.equal(tokens[10],'123');assert.equal(tokens[11],'7');assert.equal(tokens.length,size+1);
'''
    profiles_source = (qml / 'services/GlassProfiles.qml').read_text()
    runner += '\nfunction profileStrength(profile){' + body(profiles_source, 'function darkeningStrength(') + '}\n'
    runner += r"""
for(const [profile,expected] of [[null,1],[{},1],[{automaticDarkeningStrength:100},1],[{automaticDarkeningStrength:50},.5],[{automaticDarkeningStrength:0},0],[{automaticDarkeningStrength:-10},0],[{automaticDarkeningStrength:200},1],[{automaticDarkeningStrength:NaN},1]])assert.equal(profileStrength(profile),expected);
"""
    registration = body((qml / 'services/GlassCompositor.qml').read_text(), 'function registerGlass(')
    runner += '\nconst REGISTER=' + json.dumps('function registerGlass(item){' + registration + '}') + ';\n'
    runner += r"""
const registry={materialSerial:0,glassItems:[],queueRegions(){}};registry.root=registry;vm.createContext(registry);vm.runInContext(REGISTER,registry);
const a={nativeMaterialId:0},b={nativeMaterialId:0};registry.registerGlass(a);registry.registerGlass(b);
assert.equal(a.nativeMaterialId,1);assert.equal(b.nativeMaterialId,2);
registry.glassItems=[];registry.registerGlass(a);assert.equal(a.nativeMaterialId,1);assert.equal(registry.materialSerial,2);
registry.materialSerial=2147483647;assert.throws(()=>registry.registerGlass({nativeMaterialId:0}));
"""
    assert (qml / 'modules/common/Config.qml').read_text().count('property real automaticDarkeningStrength: 100') == 6
    (tmp / 'check.js').write_text(runner)
    subprocess.run(['node', str(tmp / 'check.js')], check=True)
assert 'queueDarkeningSceneChange(mon)' in body(main, 'auto bumpWindowMonitor =')
assert 'queueDarkeningSceneChange(mon)' in body(main, 'm_events.workspace.active.listen(')
assert 'if (m_darkeningTimer) m_darkeningTimer->cancel();' in body(layer, 'CGlassLayerSurface::~')
assert 'glassDamageBox' in body(layer, 'void CGlassLayerSurface::damageMaterial()')
assert 'automaticDarkeningVisible: reveal' in (qml / 'modules/ii/dock/Dock.qml').read_text()
assert 'running: state.samplingVisible' in frost
assert 'holdDarkening: lumaState.item && !lumaState.item.initializing ? 1 : 0' in frost
print('Darker lifecycle: OK (reappearance, continuously visible scene changes, fixed deadlines, settled-scene drain, gesture cancellation, per-monitor routing, no fade feedback, visibility protocol and QML pending updates; no rendering)')
