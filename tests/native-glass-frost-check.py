"""Run: python3 tests/native-glass-frost-check.py PATCHED_SOURCE_DIR. Mock GL only; no rendering/context."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

source = Path(sys.argv[1])/'src'
renderer = (source/'GlassRenderer.cpp').read_text()
blur = renderer[renderer.index('void blurBackground('):renderer.index('\nvoid applyGlassEffect(')]
layer = (source/'GlassLayerSurface.cpp').read_text()
reuse = re.search(r'if \((affected && m_frostMapping[\s\S]*?)\) \{', layer)[1]
assert 'GL_DRAW_FRAMEBUFFER, dynamic_cast<Render::GL::CGLFramebuffer*>(m_frostInputFramebuffer.get())' in layer
assert '&clip, 64, m_frostInputFramebuffer)' in layer
selection = re.search(r'                const int factor = .*?;', layer)[0]
code = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <map>
#include <memory>
#include <optional>
#include <vector>
#include <string_view>
#include <hyprutils/math/Box.hpp>
using Hyprutils::Math::CBox;
template<class T> using SP = std::shared_ptr<T>;
using GLuint = unsigned int;
constexpr int GL_TEXTURE0=0, GL_FRAMEBUFFER=0, GL_TRIANGLE_STRIP=0;
constexpr int SHADER_PROJ=0, SHADER_TEX=0, SHADER_SHADER_VAO=0;
struct Vector2D { int x=0,y=0; bool operator==(const Vector2D&) const = default; };
struct Texture { std::vector<float> pixels; void bind(); };
Texture* input = nullptr;
void Texture::bind() { input=this; }
namespace Render { struct IFramebuffer {
    Vector2D m_size; int m_drmFormat=1; Texture texture;
    void alloc(int w,int h,int format) { m_size={w,h};m_drmFormat=format;texture.pixels.resize(w*h); }
    Texture* getTexture() {return &texture;}
}; }
std::map<GLuint, Render::IFramebuffer*> buffers;
GLuint fbId(SP<Render::IFramebuffer> fb) {
    for(auto [id,p]:buffers) if(p==fb.get()) return id;
    auto id=buffers.size()+1;buffers[id]=fb.get();return id;
}
GLuint output=0; bool horizontal=true; std::optional<CBox> scissor;
struct Shader { void setUniformMatrix3fv(int,int,int,const auto&) {} void setUniformInt(int,int) {} int getUniformLocation(int) {return 0;} } shader;
struct OpenGL {
    Shader* useShader(int) {return &shader;}
    void setViewport(int,int,int,int) {}
    void scissor(const CBox& b,bool) {::scissor=b;}
    void scissor(std::nullptr_t) {::scissor.reset();}
} opengl;
auto g_pHyprOpenGL=&opengl;
struct Renderer { SP<Render::IFramebuffer> createFB(const char*) {return std::make_shared<Render::IFramebuffer>();} } factory;
auto g_pHyprRenderer=&factory;
struct Globals { struct {
    bool isInitialized() {return true;}
    int blurShader=0;
    struct {int taps=0,tapCount=0,totalWeight=0,direction=0;} blurUniforms;
} shaderManager; } globals;
auto g_pGlobalState=&globals;
constexpr int GL_FALSE=0;
void glUniform2fv(int,int,const float*) {} void glUniform1i(int,int) {} void glUniform1f(int,float) {}
void glBindVertexArray(int) {} void glActiveTexture(int) {}
void glBindFramebuffer(int,GLuint id) {output=id;}
void glUniform2f(int,float x,float) {horizontal=x!=0;}
void glDrawArrays(int,int,int) {
    auto* fb=buffers.at(output); const int w=fb->m_size.x,h=fb->m_size.y;
    auto values=input->pixels;
    for(int y=0;y<h;++y) for(int x=0;x<w;++x) {
        if(scissor && (x<scissor->x||y<scissor->y||x>=scissor->x+scissor->w||y>=scissor->y+scissor->h)) continue;
        // A three-tap filter exposes missing input halos and accidental re-filtering.
        float sum=0;
        for(int k=-1;k<=1;++k) sum+=values[std::clamp(y+(horizontal?0:k),0,h-1)*w+std::clamp(x+(horizontal?k:0),0,w-1)];
        fb->texture.pixels[y*w+x]=sum/3;
    }
}
'''+blur+r'''
int frostFactor(float support, std::string_view name) {
    struct { std::string_view m_namespace; } layer{name};
    auto layerSurface = &layer;
    SELECTION
    return factor;
}

int main() {
    assert(frostFactor(0,"quickshell:overview")==1);
    assert(frostFactor(5.99,"quickshell:overview")==1);
    assert(frostFactor(6,"quickshell:overview")==2);
    assert(frostFactor(7.5,"quickshell:overview")==2); // User blur sigma 2.5: previously full resolution.
    for(float support : {6.f,7.5f,11.99f}) {
        for(auto name : {"quickshell:settings","quickshell:bar","quickshell:dock"})
            assert(frostFactor(support,name)==1);
    }
    for(auto name : {"quickshell:overview","quickshell:settings","quickshell:dock"})
        assert(frostFactor(12,name)==2);
    auto raw=std::make_shared<Render::IFramebuffer>();raw->alloc(12,12,1);
    for(int y=0;y<12;++y) for(int x=0;x<12;++x) raw->texture.pixels[y*12+x]=(x<6?.1f:.9f)+(y%3)*.01f;
    auto output=std::make_shared<Render::IFramebuffer>();output->alloc(12,12,1);
    SP<Render::IFramebuffer> scratch;
    CBox full{0,0,12,12};
    blurBackground(output,scratch,1,1,0,12,12,&full,64,raw);
    const auto old=output->texture.pixels;
    raw->texture.pixels[6*12+6]=0;
    auto expected=std::make_shared<Render::IFramebuffer>();expected->alloc(12,12,1);
    blurBackground(expected,scratch,1,1,0,12,12,&full,64,raw);
    CBox clip{5,5,3,3};
    blurBackground(output,scratch,1,1,0,12,12,&clip,64,raw);
    for(int y=0;y<12;++y) for(int x=0;x<12;++x) {
        float wanted=(x>=5&&x<8&&y>=5&&y<8)?expected->texture.pixels[y*12+x]:old[y*12+x];
        assert(std::abs(output->texture.pixels[y*12+x]-wanted)<1e-6);
    }
    raw->texture.pixels[6*12+6]=.9f;
    blurBackground(output,scratch,1,2,0,12,12,&full,64,raw);
    raw->texture.pixels[6*12+6]=0;
    blurBackground(expected,scratch,1,2,0,12,12,&full,64,raw);
    blurBackground(output,scratch,1,2,0,12,12,&clip,64,raw);
    for(int y=0;y<12;++y) for(int x=0;x<12;++x) {
        assert(std::abs(output->texture.pixels[y*12+x]-expected->texture.pixels[y*12+x])<1e-6);
    }
    std::optional<CBox> affected=clip;
    std::array<double,15> mapping{};
    std::optional<std::array<double,15>> m_frostMapping=mapping;
    auto m_frostFramebuffer=output, m_sampleFramebuffer=raw;
    int w=12,h=12;
    auto reusable=[&] {return REUSE;};
    assert(reusable());
    for(auto& value:mapping) {value=1;assert(!reusable());value=0;}
    w=6;assert(!reusable());w=12;
    raw->m_drmFormat=2;assert(!reusable());raw->m_drmFormat=1;
    m_frostMapping.reset();assert(!reusable());
}
'''
code = code.replace('REUSE', reuse).replace('SELECTION', selection)
with tempfile.TemporaryDirectory(prefix='native-frost-check-') as directory:
    cpp=Path(directory)/'check.cpp';cpp.write_text(code)
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','hyprutils'],text=True).split()
    binary=Path(directory)/'check'
    subprocess.run(['g++','-std=c++23','-O0',str(cpp),'-o',str(binary),*flags],check=True)
    subprocess.run([str(binary)],check=True)
print('PASS: actual blur dispatch with mock GL preserves untouched pixels, matches full filtering inside damage, invalidates frost mappings and bounds Overview downsampling to wide blur.')
