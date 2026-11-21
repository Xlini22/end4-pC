"""Run: python3 tests/glass-profiles-check.py PATH_TO_PATCHED_SOURCE (no GPU)."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]) / 'src'
notch = Path(__file__).resolve().parents[1] / 'modules/ii/onScreenDisplay/FullscreenVolume.qml'
notch_namespace = re.search(r'WlrLayershell.namespace: "([^"]+)"', notch.read_text())[1]
lookup = re.search(r'inline const SGlassOptics\* glassOptics\([\s\S]*?\n\}', (source / 'Globals.hpp').read_text())[0]
terminal = re.search(r'static const SGlassOptics\* terminalOptics\([\s\S]*?\n\}', (source / 'GlassDecoration.cpp').read_text())[0]
harness = r'''
#include "GlassRegions.hpp"
#include <cassert>
#include <memory>
#include <charconv>
struct State { std::unordered_map<int,SGlassProfiles> glassProfiles; } state;
auto* g_pGlobalState = &state;
LOOKUP
struct Tags { std::vector<std::string> values; auto getTags() const { return values; } };
struct Rules { Tags m_tagKeeper; };
struct Window { std::shared_ptr<Rules> m_ruleApplicator; };
using PHLWINDOW = std::shared_ptr<Window>;
TERMINAL
int main() {
    SGlassProfiles p;
    assert(parseGlassProfiles("end4profiles 123 1 6 bar 1 .24 2 1 .5 dock 1 .07 1.35 8 .5 sidebar 1 .07 1.35 8 .5 settings 1 .07 1.35 8 .5 lockscreen 1 .07 1.35 3 .5 terminal 0 .07 1.35 3 .5",p));
    const auto valid = p;
    for (const auto* bad : {
        "end4profiles 0 1 0", "end4profiles 123 2 0", "end4profiles 123 1 7", "end4profiles 123 1 -1",
        "end4profiles 123 1 1 unknown 1 .2 1 1 .5", "end4profiles 123 1 1 bar 2 .2 1 1 .5",
        "end4profiles 123 1 1 bar 1 nan 1 1 .5", "end4profiles 123 1 1 bar 1 .2 inf 1 .5",
        "end4profiles 123 1 1 bar 1 .41 1 1 .5", "end4profiles 123 1 1 bar 1 -.01 1 1 .5",
        "end4profiles 123 1 1 bar 1 .2 2.01 1 .5", "end4profiles 123 1 1 bar 1 .2 -1 1 .5",
        "end4profiles 123 1 1 bar 1 .2 1 8.5 .5", "end4profiles 123 1 1 terminal 1 .2 1 8.5 .5",
        "end4profiles 123 1 1 dock 1 .2 1 16.5 .5", "end4profiles 123 1 1 bar 1 .2 1 -1 .5",
        "end4profiles 123 1 1 bar 1 .2 1 1 1.01", "end4profiles 123 1 1 bar 1 .2 1 1 -.1",
        "end4profiles 123 1 2 bar 1 .2 1 1 .5 bar 1 .2 1 1 .5", "end4profiles 123 1 0 extra" }) {
        assert(!parseGlassProfiles(bad,p));
        assert(p.pid==valid.pid && p.values.size()==6 && p.values.at("bar").rim==.24f);
    }
    auto extended = std::string("end4profiles 123 1 2 bar 1 .24 2 1 .5 dock 1 .07 1.35 8 .5 darkening 1 bar .4 1 dock 1 0");
    SGlassProfiles dim;
    assert(parseGlassProfiles(extended,dim) && dim.darkeningActive);
    assert(dim.values.at("bar").darkening==.4f && dim.values.at("bar").automaticDarkening==1);
    assert(dim.values.at("dock").darkening==1 && dim.values.at("dock").automaticDarkening==0);
    assert(dim.values.at("bar").darkeningValue()[0]==.4f);
    for (const auto* tail : {"darkening 2 bar .4 1 dock 1 0", "darkening 1 bar -.1 1 dock 1 0",
        "darkening 1 bar 1.01 1 dock 1 0", "darkening 1 bar nan 1 dock 1 0", "darkening 1 bar .4 2 dock 1 0",
        "darkening 1 bar .4 1 bar .5 0", "darkening 1 bar .4 1 unknown .5 0", "darkening 1 bar .4 1", "darkening 1 bar .4 1 dock 1 0 extra"}) {
        assert(!parseGlassProfiles(extended.substr(0,extended.find("darkening"))+tail,dim));
        assert(dim.values.at("bar").darkening==.4f && dim.values.at("dock").darkening==1);
    }
    auto& optical = dim.values.at("bar");
    optical.darkeningChanged = std::chrono::steady_clock::now();
    assert(optical.darkeningTransition() && optical.darkeningValue()[0]<.001f);
    optical.darkeningChanged -= std::chrono::seconds(1);
    assert(!optical.darkeningTransition() && optical.darkeningValue()[0]==.4f);
    state.glassProfiles.emplace(123,p);
    assert(glassOptics(123,"bar")->refraction==2);
    assert(glassProfileKey("NOTCH_NAMESPACE")=="bar");
    assert(glassOptics(123,glassProfileKey("NOTCH_NAMESPACE"))==glassOptics(123,"bar"));
    assert(glassOptics(123,"dock")->refraction==1.35f);
    assert(!glassOptics(124,"bar") && !glassOptics(123,"unknown") && !glassOptics(123,"terminal"));
    state.glassProfiles.at(123).active=false;assert(!glassOptics(123,"bar"));
    state.glassProfiles.at(123).active=true;
    auto w=std::make_shared<Window>();w->m_ruleApplicator=std::make_shared<Rules>();
    assert(!terminalOptics(w));
    w->m_ruleApplicator->m_tagKeeper.values={"hyprglass_owner_123"};
    assert(!terminalOptics(w)); // Off until explicitly enabled.
    state.glassProfiles.at(123).values.at("terminal").enabled=true;
    assert(terminalOptics(w)->blur==3);
    for(const auto* tag : {"hyprglass_owner_124","hyprglass_owner_123garbage","hyprglass_owner_", "hyprglass_owner_999999999999999"}) {
        w->m_ruleApplicator->m_tagKeeper.values={tag};assert(!terminalOptics(w));
    }
    assert(glassProfileKey("quickshell:sidebarRight")=="sidebar");
    assert(glassProfileKey("quickshell:settings")=="settings");
    assert(glassProfileKey("quickshell:popup").empty());
}
'''.replace('LOOKUP', lookup).replace('TERMINAL', terminal).replace('NOTCH_NAMESPACE', notch_namespace)
with tempfile.TemporaryDirectory(prefix='glass-profiles-check-') as directory:
    cpp = Path(directory) / 'check.cpp'
    exe = Path(directory) / 'check'
    cpp.write_text(harness)
    subprocess.run(['g++', '-std=c++23', '-O0', '-I', str(source), str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
main = (source / 'main.cpp').read_text()
assert 'profiles.pid != g_pHyprCtl->m_currentRequestParams.pid' in main
assert 'clients.size() >= 16' in main
print('Glass profiles: bounded atomic parsing, owner isolation, independent targets and opt-in terminal passed.')

# Keep both renderers on the same material curve; native foreground composition remains outside darkenGlass.
repo = Path(__file__).resolve().parents[1]
native_shader = (source / 'Shaders.hpp').read_text()
qt_shader = (repo / 'modules/common/widgets/shaders/liquidLens.frag').read_text()
curve = "max(0.0, 1.0 - 0.38 / max(backdropLuma, 0.38))"
assert curve in native_shader and curve in qt_shader
assert '(surface || terminal || dimming) ? &material' in (source / 'GlassDecoration.cpp').read_text()
layer = (source / 'GlassLayerSurface.cpp').read_text()
assert 'glassDarkeningOptics(layerSurface->getPID(),' in layer
assert '(layerSurface->m_namespace == "quickshell:popup" || layerSurface->m_namespace == "quickshell:popupMorph") ? "bar" : glassProfileKey(layerSurface->m_namespace)' in layer
