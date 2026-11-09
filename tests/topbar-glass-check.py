"""Run: python3 tests/topbar-glass-check.py PATH_TO_PATCHED_SOURCE (no GPU or compositor)."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]) / 'src'
layer = (source / 'GlassLayerSurface.cpp').read_text()
renderer = (source / 'GlassRenderer.cpp').read_text()
method = re.search(r'bool CGlassLayerSurface::calibratedTopBar\(\) const \{[\s\S]*?\n\}', layer)[0]
uniforms = '\n'.join(line for line in renderer.splitlines() if re.match(
    r'    glUniform1f\(uniforms\.(refractionStrength|edgeThickness|fresnelStrength|specularStrength),', line))
assert len(uniforms.splitlines()) == 4
scope = re.search(r'    const bool topBarOptics = [^\n]+', renderer)[0]
blur = re.search(r'        float blurRadius\s+= ([^;]+);', layer)[1]
assert 'topBarOptics ? 64 : 8' in layer
assert 'm_lastTopBarOptics = calibratedTopBar();' in layer
harness = r'''
#include <cassert>
#include <cmath>
#include <memory>
#include <string>
#include <array>
constexpr unsigned ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP = 1;
constexpr unsigned ZWLR_LAYER_SURFACE_V1_ANCHOR_BOTTOM = 2;
struct Resource { struct { unsigned anchor = 1; } m_current; };
struct Layer {
    std::string m_namespace = "quickshell:bar";
    bool m_fadingOut = false;
    std::weak_ptr<Resource> m_layerSurface;
};
struct CGlassLayerSurface {
    std::weak_ptr<Layer> m_layerSurface;
    bool m_lastTopBarOptics = false;
    bool enabled = true;
    bool enhanced() const { return enabled; }
    bool calibratedTopBar() const;
};
METHOD
struct SPresetValues { float refractionStrength, edgeThickness, fresnelStrength, specularStrength; };
struct SOverridableConfig { float refractionStrength, edgeThickness, fresnelStrength, specularStrength; };
float resolvePresetFloat(int, float SPresetValues::*, float SOverridableConfig::*) { return .123f; }
struct { int refractionStrength=0, edgeThickness=1, fresnelStrength=2, specularStrength=3; } uniforms;
struct Mask { bool topBarOptics; };
std::array<float,4> values;
void glUniform1f(int location, float value) { values[location] = value; }
void params(bool enhanced, const Mask* mask) {
    const int resolveContext=0;
SCOPE
UNIFORMS
}
float radius(bool topBarOptics, float scale) {
    struct Monitor { float m_scale; } mon{scale};
    auto monitor=&mon;
    const float blurStrength=.9f; const int downscale=2;
    return BLUR;
}
void same(float a, float b) { assert(std::abs(a-b)<.00001f); }
int main() {
    auto resource=std::make_shared<Resource>();
    auto layer=std::make_shared<Layer>();layer->m_layerSurface=resource;
    CGlassLayerSurface glass;glass.m_layerSurface=layer;
    assert(glass.calibratedTopBar());
    for (auto name : {"quickshell:verticalBar", "quickshell:dock", "quickshell:popup", "quickshell:popupMorph", "quickshell:settings", "quickshell:sidebarLeft", "quickshell:mediaControls"}) {
        layer->m_namespace=name;assert(!glass.calibratedTopBar());
    }
    layer->m_namespace="quickshell:bar";
    for (auto anchor : {0u,2u,3u}) { resource->m_current.anchor=anchor;assert(!glass.calibratedTopBar()); }
    resource->m_current.anchor=1;glass.enabled=false;assert(!glass.calibratedTopBar());glass.enabled=true;
    layer->m_fadingOut=true;glass.m_lastTopBarOptics=true;resource.reset();
    assert(glass.calibratedTopBar()); // Closing snapshots retain the same optics.
    glass.m_lastTopBarOptics=false;assert(!glass.calibratedTopBar());
    layer->m_fadingOut=false;assert(!glass.calibratedTopBar());layer.reset();assert(!glass.calibratedTopBar());
    Mask top{true}, other{false};
    params(true,&top);same(values[0],2);same(values[1],.24);same(values[2],.35);same(values[3],.5);
    for (const Mask* mask : {&other, static_cast<Mask*>(nullptr)}) {
        params(true,mask);same(values[0],1.35);same(values[1],.07);same(values[2],.35);same(values[3],.5);
    }
    params(false,&top);for(float value:values)same(value,.123);
    for(float scale : {1.f,1.25f,2.f}) {same(radius(true,scale)/3,scale);same(radius(false,scale),5.4);}
}
'''.replace('METHOD', method).replace('SCOPE', scope).replace('UNIFORMS', uniforms).replace('BLUR', blur)
with tempfile.TemporaryDirectory(prefix='topbar-glass-check-') as directory:
    cpp = Path(directory) / 'check.cpp'
    exe = Path(directory) / 'check'
    cpp.write_text(harness)
    subprocess.run(['g++', '-std=c++23', '-O0', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('Top bar: top-only scope, unchanged other surfaces, close retention, 24%/200%/50% and 1px Gaussian at each scale passed.')
