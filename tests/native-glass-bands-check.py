"""Run: python3 tests/native-glass-bands-check.py PATCHED_SOURCE_DIR.
Run the actual C++ band selection and compare native GLSL pixels on llvmpipe.
"""
from pathlib import Path
import json
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
source = (Path(sys.argv[1]) / 'src/GlassLayerSurface.cpp').read_text()
start = source.index('        const auto regions = maskInfo.regions;')
end = source.index('        return;\n    }', start)
selection = source[start:end]
harness = r'''
#include <iostream>
#include <optional>
#include <hyprutils/math/Region.hpp>
#include "GlassRegions.hpp"
using namespace Hyprutils::Math;
struct Mask { std::vector<SGlassRegion> regions; std::optional<CBox> clip; };
std::vector<SGlassRegion> original;
bool comma = false;
namespace GlassRenderer {
void applyGlassEffect(int, int, CBox&, CBox&, float, float, float, int, int, const Mask* mask) {
    if (comma) std::cout << ',';
    comma = true;
    std::cout << '[' << mask->clip->y << ',' << mask->clip->h << ",[";
    bool separator = false;
    for (const auto& region : mask->regions) {
        if (separator) std::cout << ',';
        separator = true;
        std::cout << std::distance(original.begin(), std::find(original.begin(), original.end(), region));
    }
    std::cout << "]]";
}
}
struct Renderer { struct { CRegion damage; } m_renderData; } renderer;
auto g_pHyprRenderer = &renderer;
int main() {
    int monitorWidth, monitorHeight, count;
    double offsetY, damageY, damageH;
    std::cin >> monitorWidth >> monitorHeight >> offsetY >> damageY >> damageH >> count;
    Mask maskInfo;
    for (int i = 0; i < count; ++i) {
        SGlassRegion region;
        for (auto& coordinate : region.rect) std::cin >> coordinate;
        region.edge = i; // Preserve identity even for duplicate test boxes.
        maskInfo.regions.push_back(region);
    }
    original = maskInfo.regions;
    renderer.m_renderData.damage = CRegion(CBox{0, damageY, double(monitorWidth), damageH});
    CBox rawBox{0,offsetY,double(monitorWidth),double(monitorHeight)}, transformBox = rawBox;
    int m_sampleFramebuffer = 0, target = 0, m_samplePaddingRatio = 0, ctx = 0;
    float alpha = 1, cornerRadius = 0, roundingPower = 2;
    std::cout << '[';
'''
# Reuse the existing CPU-only GL setup, including the actual native vertex/fragment shaders.
setup = (repo / 'tests/native-glass-shader-check.py').read_text().split('# A faint Qt shadow', 1)[0]
setup = setup.replace('width, height = 128, 96', 'width, height = 128, 384')
exec(compile(setup, str(repo / 'tests/native-glass-shader-check.py'), 'exec'), globals())
assert height == 384
checks = 0
with tempfile.TemporaryDirectory(prefix='glass-bands-', dir='/tmp') as temporary:
    directory = Path(temporary)
    (directory / 'check.cpp').write_text(harness + selection + '\nstd::cout << "]";\n}\n')
    flags = subprocess.check_output(['pkg-config','--cflags','--libs','hyprutils','pixman-1'], text=True).split()
    subprocess.run(['c++','-std=c++23','-Wno-narrowing','-I'+str(Path(sys.argv[1]).resolve()/'src'),str(directory/'check.cpp'),'-o',str(directory/'check'),*flags],check=True)
    for nested in (False, True):
        for count in (3, 11, 32):
            boxes = [(3, -5+i*9, 120-i*.7, 290-i*7) if nested else
                     (3, -5+i*14, 120, 13.25) for i in range(count)]
            radii = [(2,5,3,4)] * count
            features = [(0,0,0,0)] * count
            for offset, damage in ((0,(0,height)),(12.5,(0,height)),(-17.25,(97,171))):
                data = f'{width} {height} {offset} {damage[0]} {damage[1]} {count}\n' + '\n'.join(' '.join(map(str,box)) for box in boxes)
                bands = json.loads(subprocess.check_output([str(directory/'check')],input=data,text=True))
                assert bands and all(ids == sorted(ids) and ids for _,_,ids in bands), bands
                for fade in (1,.6,.02):
                    details = [(0,fade,8 if i%2 else 0,0) for i in range(count)]
                    for automatic in (0,1):
                        before = render(programs[1],boxes,radii,features,details,True,fade,.07,automatic=automatic)
                        after = bytearray(before)
                        for top, span, indices in bands:
                            selected = [[values[i] for i in indices] for values in (boxes,radii,features,details)]
                            band_pixels = render(programs[1],*selected,True,fade,.07,automatic=automatic)
                            for y in range(height):
                                if top <= y+.5+offset < top+span and damage[0] <= y+.5+offset < sum(damage):
                                    line = slice(y*width*4,(y+1)*width*4)
                                    after[line] = band_pixels[line]
                        error = max(abs(a-b) for a,b in zip(before,after))
                        assert error <= 1,(nested,count,offset,damage,fade,automatic,error)
                        checks += 1
print(f'PASS: {checks} C++/GLSL band comparisons within 1/255: nested/fading rows, auto darkening, partial damage and fractional/negative panel offsets.')
