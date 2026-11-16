"""Run: python3 tests/native-glass-visibility-check.py PATCHED_SOURCE_DIR (no compositor/GPU)."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

src=Path(sys.argv[1]).resolve()/'src'
layer=(src/'GlassLayerSurface.cpp').read_text()
visible=re.search(r'bool CGlassLayerSurface::hasVisibleMaterial\(\) const \{[\s\S]*?\n\}',layer)[0]
pre=(src/'GlassLayerPassElement.cpp').read_text()
bounds=re.search(r'std::optional<CBox> CGlassLayerPassElement::boundingBox\(\) \{[\s\S]*?\n\}',pre)[0]
main=(src/'main.cpp').read_text()
for name in ('GlassLayerPassElement','GlassPassElement'):
    text=(src/(name+'.cpp')).read_text()
    body=re.search(r'bool C'+name+r'::disableSimplification\(\) \{[\s\S]*?\n\}',text)[0]
    assert 'return false;' in body, name+' must not disable occlusion for the whole desktop'
for name in ('GlassLayerPassElement','GlassLayerCompositeElement'):
    text=(src/(name+'.cpp')).read_text()
    body=re.search(r'bool C'+name+r'::undiscardable\(\) \{[\s\S]*?\n\}',text)[0]
    assert 'return true;' in body, 'Redirect/restore passes must survive occlusion together'
assert 'if (damage.empty()) return;' in layer, 'An occluded pre-pass must not redirect the framebuffer'

assert 'alpha < 0.001f || !it->second->hasVisibleMaterial()' in main
assert layer.count('|| layerSurface->m_namespace == "quickshell:dock"') == 2, 'Dock needs both cropped damage and cropped sampling'
# Foreground outside a cropped sample must keep rendering, including raised dock icons/previews.
fragment=(src/'Shaders.hpp').read_text()
assert 'fragColor = surfacePixel;\n            return;' in fragment
harness=r'''
#include <cassert>
#include <memory>
#include <optional>
#include <hyprutils/math/Box.hpp>
#include "GlassRegions.hpp"
using CBox=Hyprutils::Math::CBox;
constexpr int WL_OUTPUT_TRANSFORM_NORMAL=0;
struct Monitor { float m_scale=1; int m_transform=0; };
auto monitor=std::make_shared<Monitor>();
struct { struct { std::weak_ptr<Monitor> pMonitor=monitor; } m_renderData; } renderer;
auto g_pHyprRenderer=&renderer;
namespace GlassRenderer { constexpr float SAMPLE_PADDING_PX=60; }
CBox sourceBox{0,902,1920,178};
namespace LayerGeometry {
std::optional<CBox> computeLayerBox(std::shared_ptr<int>,std::shared_ptr<Monitor>) { return sourceBox; }
}
struct CGlassLayerSurface {
    SGlassSurface* surface=nullptr;
    const SGlassSurface* enhancedSurface() const { return surface; }
    std::shared_ptr<int> layer=std::make_shared<int>(1);
    std::shared_ptr<int> getLayerSurface() { return layer; }
    bool hasVisibleMaterial() const;
};
VISIBLE
struct CGlassLayerPassElement {
    struct { std::shared_ptr<CGlassLayerSurface> layerState; } m_data;
    std::optional<CBox> boundingBox();
};
BOUNDS
int main() {
    auto state=std::make_shared<CGlassLayerSurface>();
    assert(state->hasVisibleMaterial()); // Unregistered/legacy geometry retains its fallback.
    SGlassSurface surface{"quickshell:dock","eDP-1",1920,178};
    state->surface=&surface;
    assert(!state->hasVisibleMaterial());
    SGlassRegion region; region.rect={782,186,356,60};region.frost=4;
    surface.regions={region};
    assert(!state->hasVisibleMaterial()); // The reported hidden dock.
    for (auto rect: {std::array<float,4>{-100,5,60,40},{1922,5,60,40},{20,-42,60,40},{20,180,60,40}}) {
        surface.regions[0].rect=rect;assert(!state->hasVisibleMaterial());
    }
    for (auto rect: {std::array<float,4>{-20,5,60,40},{1900,5,60,40},{20,-20,60,40},{20,160,60,40},
                    {20,178.25f,60,40},{20,-40.25f,60,40}}) {
        surface.regions[0].rect=rect;assert(state->hasVisibleMaterial());
    }
    surface.regions[0].opacity=0;assert(!state->hasVisibleMaterial());
    surface.regions.push_back(region);surface.regions.back().rect={782,80,356,60};
    assert(state->hasVisibleMaterial()); // A visible child keeps the pass even with a hidden parent.
    surface.regions={surface.regions.back()};
    CGlassLayerPassElement pre;pre.m_data.layerState=state;
    auto box=*pre.boundingBox();
    assert(box.x==722 && box.y==922 && box.w==476 && box.h==180);
    // Fractional output scales and opening/closing layer scales use current geometry.
    for (float scale: {1.f,1.25f,1.5f,2.f}) {
        monitor->m_scale=scale;sourceBox=CBox{0,902*scale,1920*scale,178*scale};
        box=*pre.boundingBox();
        assert(std::abs(box.x-(782-60/scale))<=1 && std::abs(box.w-(356+120/scale))<=2);
    }
    monitor->m_scale=1;sourceBox=CBox{0,902,1920,178};
    surface.regions[0].frost=32;
    box=*pre.boundingBox();assert(box.x<=686 && box.w>=548); // Full Gaussian support survives the tighter backdrop.
    // Rotated/unknown geometry keeps the old full-surface fallback.
    monitor->m_scale=1;sourceBox=CBox{0,902,1920,178};monitor->m_transform=1;
    box=*pre.boundingBox();assert(box.w==2040 && box.h==298);
    monitor->m_transform=0;state->surface=nullptr;
    box=*pre.boundingBox();assert(box.w==2040 && box.h==298);
}
'''.replace('VISIBLE',visible).replace('BOUNDS',bounds)
with tempfile.TemporaryDirectory(prefix='glass-visible-') as directory:
    path=Path(directory);(path/'check.cpp').write_text(harness)
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','hyprutils'],text=True).split()
    subprocess.run(['c++','-std=c++23','-I'+str(src),str(path/'check.cpp'),'-o',str(path/'check'),*flags],check=True)
    subprocess.run([str(path/'check')],check=True)
print('PASS: hidden dock skips glass, visible/antialiased opening and closing edges remain; material-sized backdrop bounds at fractional scales, rotated/legacy fallback, full foreground preserved.')
