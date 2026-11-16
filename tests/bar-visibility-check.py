"""Run: python3 tests/bar-visibility-check.py PATCHED_SOURCE_DIR (no compositor/GPU).
Check the actual native observer and QML event/snapshot parsers.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
source = (Path(sys.argv[1]) / 'src/main.cpp').read_text()
observer = re.search(r'static void publishBarVisibility\([\s\S]*?\n\}', source)[0]
cpp = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <format>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>
constexpr unsigned ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP=1, ZWLR_LAYER_SURFACE_V1_ANCHOR_BOTTOM=2;
constexpr unsigned ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT=4, ZWLR_LAYER_SURFACE_V1_ANCHOR_RIGHT=8;
struct Resource { struct { unsigned anchor=13; } m_current; };
struct Alpha { float alpha=0; float value() const { return alpha; } };
struct Layer {
    std::string m_namespace="quickshell:bar";
    int pid=123; bool m_mapped=true, m_fadingOut=false;
    std::shared_ptr<Alpha> m_alpha=std::make_shared<Alpha>();
    std::weak_ptr<Resource> m_layerSurface;
    int getPID() { return pid; }
};
struct Monitor { std::string m_name="eDP-1"; std::array<std::vector<std::shared_ptr<Layer>>,4> m_layerSurfaceLayers; };
using PHLMONITOR=std::shared_ptr<Monitor>;
struct State { unsigned long long barVisibilitySerial=0; std::unordered_map<int,std::unordered_map<std::string,bool>> barVisibility; } state;
auto* g_pGlobalState=&state;
struct Event { std::string event, data; };
struct Events { std::vector<Event> sent; void postEvent(Event e) { sent.push_back(e); } } events;
auto* g_pEventManager=&events;
OBSERVER
int main() {
    auto mon=std::make_shared<Monitor>();auto resource=std::make_shared<Resource>();auto bar=std::make_shared<Layer>();
    bar->m_layerSurface=resource;mon->m_layerSurfaceLayers[2].push_back(bar);
    publishBarVisibility(mon);assert(events.sent.size()==1 && !state.barVisibility.at(123).at("eDP-1"));
    for(int i=0;i<100;++i)publishBarVisibility(mon);
    assert(events.sent.size()==1); // Idle rendered frames send no additional events.
    bar->m_alpha->alpha=.1f;publishBarVisibility(mon); // Gesture begins while the workspace remains fullscreen.
    assert(events.sent.size()==2 && state.barVisibility.at(123).at("eDP-1"));
    assert(events.sent.back().data=="123,eDP-1,1,2");
    bar->m_alpha->alpha=1;publishBarVisibility(mon);assert(events.sent.size()==2);
    auto pill=std::make_shared<Layer>();auto pillResource=std::make_shared<Resource>();pillResource->m_current.anchor=1;
    pill->m_layerSurface=pillResource;pill->m_alpha->alpha=1;mon->m_layerSurfaceLayers[3].push_back(pill);
    bar->m_alpha->alpha=0;publishBarVisibility(mon); // Cancelled gesture; the overlay pill must not count as a bar.
    assert(events.sent.size()==3 && events.sent.back().data=="123,eDP-1,0,3");
    auto second=std::make_shared<Layer>();second->m_layerSurface=resource;second->m_alpha->alpha=1;
    mon->m_layerSurfaceLayers[2].push_back(second);publishBarVisibility(mon);
    assert(state.barVisibility.at(123).at("eDP-1")); // Overlapping old/new shells aggregate visibility.
    auto other=std::make_shared<Monitor>();other->m_name="HDMI-A-1";auto otherBar=std::make_shared<Layer>();
    otherBar->pid=456;otherBar->m_layerSurface=resource;otherBar->m_alpha->alpha=1;other->m_layerSurfaceLayers[2].push_back(otherBar);
    publishBarVisibility(other);assert(state.barVisibility.at(456).at("HDMI-A-1"));
    mon->m_layerSurfaceLayers[2].clear();publishBarVisibility(mon);
    assert(!state.barVisibility.contains(123) && state.barVisibility.contains(456));
    assert(events.sent.back().data.starts_with("123,eDP-1,0,"));
    const auto count=events.sent.size();publishBarVisibility(mon);assert(events.sent.size()==count);
    mon->m_name="bad,monitor";publishBarVisibility(mon);assert(events.sent.size()==count);
    publishBarVisibility(nullptr);assert(events.sent.size()==count);
}
'''.replace('OBSERVER', observer)
qml = (repo / 'services/GlassCompositor.qml').read_text()
handlers = '\n'.join(re.search(r'    function ' + name + r'\([\s\S]*?\n    \}', qml)[0]
                     for name in ('receiveBarVisibility', 'receiveBarSnapshot', 'receiveClockVisibility'))
js = r'''
const assert=require('node:assert/strict');
const root={barVisibility:{},barVisibilitySerial:0};const Quickshell={processId:123};
HANDLERS
receiveBarVisibility('123,eDP-1,1,2');assert.equal(root.barVisibility['eDP-1'],true);
for(const message of ['456,eDP-1,0,3','123,eDP-1,0,1','123,eDP-1,0,2','123,eDP-1,2,4',
    '123,,1,4','123,eDP-1,1,NaN','123,eDP-1,1,9007199254740992','123,eDP-1,1,5,extra',
    '123,bad\nmonitor,1,5'])receiveBarVisibility(message);
assert.deepEqual(root,{barVisibility:{'eDP-1':true},barVisibilitySerial:2});
receiveBarSnapshot(JSON.stringify({serial:1,bars:{'eDP-1':false}}));assert.equal(root.barVisibility['eDP-1'],true);
receiveBarSnapshot(JSON.stringify({serial:2,bars:{'eDP-1':true,'HDMI-A-1':false}}));assert.equal(root.barVisibility['HDMI-A-1'],false);
for(const sample of [{serial:4,bars:[]},{serial:4,bars:{'eDP-1':'false'}},{serial:-1,bars:{}},
    {serial:4,bars:{'bad,monitor':true}}])receiveBarSnapshot(JSON.stringify(sample));
assert.equal(root.barVisibilitySerial,2);
receiveBarVisibility('123,eDP-1,0,3');assert.equal(root.barVisibility['eDP-1'],false);
receiveBarSnapshot(JSON.stringify({serial:2,bars:{'eDP-1':true}}));assert.equal(root.barVisibility['eDP-1'],false);
assert.throws(()=>receiveBarSnapshot('invalid JSON'));
root.clockVisibility={};root.clockVisibilitySerial=0;
receiveClockVisibility('123,eDP-1,0,10');assert.equal(root.clockVisibility['eDP-1'],false);
for(const message of ['456,eDP-1,1,11','123,eDP-1,1,9','123,eDP-1,2,11','123,,1,11',
    '123,eDP-1,1,NaN','123,bad\nmonitor,1,11'])receiveClockVisibility(message);
assert.deepEqual(root.clockVisibility,{'eDP-1':false});assert.equal(root.clockVisibilitySerial,10);
receiveBarSnapshot(JSON.stringify({serial:11,bars:{},clocks:{'eDP-1':true}}));
assert.equal(root.clockVisibility['eDP-1'],true);assert.equal(root.clockVisibilitySerial,11);
receiveClockVisibility('123,eDP-1,0,10');assert.equal(root.clockVisibility['eDP-1'],true);
receiveBarSnapshot(JSON.stringify({serial:12,bars:{},clocks:{'eDP-1':'false'}}));
assert.equal(root.clockVisibility['eDP-1'],true);assert.equal(root.clockVisibilitySerial,11);
'''.replace('HANDLERS', handlers)
with tempfile.TemporaryDirectory(prefix='bar-visibility-check-') as directory:
    temp=Path(directory);(temp/'check.cpp').write_text(cpp);(temp/'check.js').write_text(js)
    subprocess.run(['c++','-std=c++23','-O0',str(temp/'check.cpp'),'-o',str(temp/'check')],check=True)
    subprocess.run([str(temp/'check')],check=True)
    subprocess.run(['node',str(temp/'check.js')],check=True)
assert 'render.pre.listen(publishBarVisibility)' in source
assert 'barVisibility.find(g_pHyprCtl->m_currentRequestParams.pid)' in source
print('Native bar opacity events, gesture cancellation, overlay exclusion, cleanup, ownership and stale-reply checks passed without compositor/GPU.')
