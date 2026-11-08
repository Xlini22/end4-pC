"""Check production blur-buffer acquisition without a GPU: python3 tests/native-glass-buffer-check.py SOURCE_DIR."""
from pathlib import Path
import subprocess
import sys
import tempfile

source = (Path(sys.argv[1]) / 'src/GlassRenderer.cpp').read_text()
# Run the real allocation/early-return code; GL drawing starts after this marker.
acquire = source[source.index('void blurBackground('):].split('    // Fullscreen quad projection:', 1)[0] + '}\n'
layer = (Path(sys.argv[1]) / 'src/GlassLayerSurface.cpp').read_text()
# Run the production resource release against Hyprland's framebuffer-0 release behavior.
release = layer[layer.index('CGlassLayerSurface::~CGlassLayerSurface() {'):].split('    // Damage the area', 1)[0] + '}\n'
decoration = (Path(sys.argv[1]) / 'src/GlassDecoration.cpp').read_text()
release_window = decoration[decoration.index('CGlassDecoration::~CGlassDecoration() {'):].split('\nbool CGlassDecoration::resolveEnabled()', 1)[0]
harness = r'''
#include <cassert>
#include <memory>
template<class T> using SP = std::shared_ptr<T>;
using GLuint = unsigned int;
using GLint = int;
constexpr int GL_READ_FRAMEBUFFER_BINDING = 1, GL_DRAW_FRAMEBUFFER_BINDING = 2;
constexpr int GL_READ_FRAMEBUFFER = 3, GL_DRAW_FRAMEBUFFER = 4;
int readBinding = 0, drawBinding = 0;
int deletedFences = 0, deletedBuffers = 0;
void glDeleteSync(int) { ++deletedFences; }
void glDeleteBuffers(int count, GLuint*) { deletedBuffers += count; }
void glGetIntegerv(int target, int* value) { *value = target == GL_READ_FRAMEBUFFER_BINDING ? readBinding : drawBinding; }
void glBindFramebuffer(int target, int value) { (target == GL_READ_FRAMEBUFFER ? readBinding : drawBinding) = value; }
struct CBox {};
struct Size { int x = 0, y = 0; };
int allocations = 0;
namespace Render {
struct IFramebuffer {
    ~IFramebuffer() { readBinding = drawBinding = 0; }
    Size m_size;
    int m_drmFormat = 0;
    void alloc(int w, int h, int format) {
        m_size = {w, h}; m_drmFormat = format; ++allocations;
    }
};
}
struct Renderer {
    SP<Render::IFramebuffer> createFB(const char*) {
        return std::make_shared<Render::IFramebuffer>();
    }
} renderer;
auto g_pHyprRenderer = &renderer;
struct Globals {
    struct { bool isInitialized() { return true; } } shaderManager;
} globals;
auto g_pGlobalState = &globals;
'''
harness += r'''
struct CGlassLayerSurface {
    SP<Render::IFramebuffer> m_surfaceTempFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_sampleFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_frostFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_blurTempFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_frostTempFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_contrastFramebuffer = std::make_shared<Render::IFramebuffer>();
    int m_contrastFence = 1;
    GLuint m_contrastBuffer = 1;
    ~CGlassLayerSurface();
};
'''
harness += r'''
struct CGlassDecoration {
    SP<Render::IFramebuffer> m_sampleFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_blurTempFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_frostFramebuffer = std::make_shared<Render::IFramebuffer>();
    SP<Render::IFramebuffer> m_frostTempFramebuffer = std::make_shared<Render::IFramebuffer>();
    ~CGlassDecoration();
};
'''
harness += 'void blurBackground(SP<Render::IFramebuffer>, SP<Render::IFramebuffer>&, float, int, GLuint, int, int, const CBox* = nullptr, int = 8);\n'
harness += '#include ' + repr(str(Path(sys.argv[1]).resolve() / 'src/GlassRegions.hpp')).replace("'", '"') + '\n'
checks = r'''
int main() {
    readBinding = 17; drawBinding = 19;
    std::weak_ptr<Render::IFramebuffer> closed;
    { CGlassLayerSurface layer; closed = layer.m_sampleFramebuffer; }
    assert(closed.expired());
    assert(deletedFences == 1 && deletedBuffers == 1);
    assert(readBinding == 17 && drawBinding == 19); // Closing glass must not redirect the next desktop frame to framebuffer 0.
    { CGlassDecoration window; closed = window.m_frostFramebuffer; }
    assert(closed.expired() && readBinding == 17 && drawBinding == 19);
    SGlassSurface panel{"quickshell:settings", "eDP-1", 1920, 1080};
    SGlassRegion region; region.rect = {470, 180, 980, 720};
    panel.regions.push_back(region);
    assert((glassBounds(panel) == std::array<float, 4>{470, 180, 980, 720}));
    assert(!glassBounds(panel, true));
    panel.regions[0].frost = 8;
    assert((glassBounds(panel, true) == std::array<float, 4>{470, 180, 980, 720}));
    region.rect = {-20, 30, 100, 80}; panel.regions.push_back(region);
    assert((glassBounds(panel) == std::array<float, 4>{0, 30, 1450, 870}));
    for (auto& r : panel.regions) r.opacity = 0;
    assert(!glassBounds(panel));
    panel.regions = {region}; panel.regions[0].rect = {-100, -100, 10, 10};
    assert(!glassBounds(panel));

    SGlassClient client;
    const std::string valid = "end4glass 42 1 1 quickshell:bar eDP-1 1920 68 1 0 0 300 50 10 10 10 10 0 0 0 0 0 1";
    assert(parseGlassRegions(valid, client));
    assert(client.enhanced && client.pid == 42 && client.surfaces[0].regions.size() == 1);
    std::string satin = valid; satin.replace(satin.find("42 1"), 4, "42 2"); satin += " 8";
    assert(parseGlassRegions(satin, client) && client.surfaces[0].regions[0].frost == 8);
    for (const auto& value : {"nan", "-1", "33", ""}) {
        assert(!parseGlassRegions(satin.substr(0, satin.size() - 1) + value, client));
        assert(client.surfaces[0].regions[0].frost == 8);
    }
    assert(parseGlassRegions(valid, client) && client.surfaces[0].regions[0].frost == 0);
    for (const auto& invalid : {
        "end4glass 42 1 33", "end4glass 42 3 0", "end4glass -1 1 0",
        "end4glass 42 1 1 quickshell:bar eDP-1 nan 68 0",
        "end4glass 42 1 1 other-app eDP-1 1920 68 0",
        "end4glass 42 1 1 quickshell:bar eDP-1 1920 68 33",
        "end4glass 42 1 1 quickshell:bar eDP-1 1920 68 1"}) {
        assert(!parseGlassRegions(invalid, client));
        assert(client.pid == 42 && client.surfaces[0].regions.size() == 1);
    }
    assert(!parseGlassRegions(valid + " trailing", client));
    assert(!parseGlassRegions(std::string(32769, 'x'), client));
    assert(parseGlassRegions("end4glass 42 0 0", client) && !client.enhanced && client.surfaces.empty());

    auto bar = std::make_shared<Render::IFramebuffer>();
    auto popup = std::make_shared<Render::IFramebuffer>();
    bar->m_size = {1020, 94}; popup->m_size = {540, 380};
    bar->m_drmFormat = popup->m_drmFormat = 7;
    SP<Render::IFramebuffer> barScratch, popupScratch;
    for (int frame = 0; frame < 120; ++frame) {
        blurBackground(bar, barScratch, 8, 1, 0, 1920, 1080);
        blurBackground(popup, popupScratch, 8, 1, 0, 1920, 1080);
    }
    assert(allocations == 2); // Warm-up only, rather than two allocations every frame.
    assert(barScratch != popupScratch);
    assert(barScratch->m_size.x == 1020 && popupScratch->m_size.x == 540);
    popup->m_size = {600, 400};
    blurBackground(popup, popupScratch, 8, 1, 0, 1920, 1080);
    assert(allocations == 3);
    blurBackground(bar, barScratch, 8, 1, 0, 1920, 1080);
    assert(allocations == 3 && barScratch->m_size.x == 1020);
    SP<Render::IFramebuffer> unused;
    blurBackground(bar, unused, 0, 1, 0, 1920, 1080);
    blurBackground(bar, unused, 8, 0, 0, 1920, 1080);
    blurBackground({}, unused, 8, 1, 0, 1920, 1080);
    assert(!unused && allocations == 3);
    std::weak_ptr<Render::IFramebuffer> released = popupScratch;
    popupScratch.reset();
    assert(released.expired());
}
'''
with tempfile.TemporaryDirectory(prefix='glass-buffer-', dir='/tmp') as directory:
    path = Path(directory)
    (path / 'check.cpp').write_text(harness + acquire + release + release_window + checks)
    subprocess.run(['c++', '-std=c++23', str(path / 'check.cpp'), '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True)
print('PASS: two surfaces, 120 frames, two initial allocations; resize, close framebuffer restoration and geometry validation checked.')
