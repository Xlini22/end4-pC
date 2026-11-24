"""Run: python3 tests/native-glass-safety-check.py PATCHED_SOURCE. Mock GL only; no rendering."""
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
source = Path(sys.argv[1]).resolve() / 'src'
layer = (source / 'GlassLayerSurface.cpp').read_text()
renderer = (source / 'GlassRenderer.cpp').read_text()
main = (source / 'main.cpp').read_text()
contrast_end = '\nvoid CGlassLayerSurface::damageMaterial()' if '\nvoid CGlassLayerSurface::damageMaterial()' in layer else '\nbool CGlassLayerSurface::enhanced()'
if '\nvoid CGlassLayerSurface::updateDarkeningVisibility()' in layer:
    contrast_end = '\nvoid CGlassLayerSurface::updateDarkeningVisibility()'
contrast = layer[layer.index('std::string CGlassLayerSurface::contrastSample()'):layer.index(contrast_end)]
acquire = renderer[renderer.index('void blurBackground('):].split('    // Fullscreen quad projection:', 1)[0] + '}\n'
sample_acquire = renderer[renderer.index('void sampleBackground('):].split('    int srcX0', 1)[0].replace('SAMPLE_PADDING_PX', '60') + '}\n'
release_frost = ''
if '        if (!frostRendered) {' in layer:
    start_release = layer.index('        if (!frostRendered) {')
    release_frost = layer[start_release:layer.index('        m_hasCachedSample', start_release)]
clear = layer[layer.index('    CBox clearBox = transformBox;'):layer.index('\n}\n\nvoid CGlassLayerSurface::compositeAndRestore')]
start = main.index('                    if (auto monitor = layer->m_monitor.lock(); monitor && glassSurfaceChanged(')
end = main.index('\n                }\n            }\n            for (const auto& decoration', start)
damage = main[start:end]

code = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <memory>
#include <sstream>
#include <vector>
#include <hyprutils/math/Box.hpp>
#include <hyprutils/math/Region.hpp>
#include <hyprutils/utils/ScopeGuard.hpp>
#include "GlassRegions.hpp"
using Hyprutils::Math::CBox;
using Hyprutils::Math::CRegion;
using Hyprutils::Math::Vector2D;
template<class T> using SP=std::shared_ptr<T>;
using GLint=int; using GLuint=unsigned; using GLsync=void*;
enum {GL_READ_FRAMEBUFFER_BINDING,GL_DRAW_FRAMEBUFFER_BINDING,GL_PIXEL_PACK_BUFFER_BINDING,
 GL_PACK_ALIGNMENT,GL_PACK_ROW_LENGTH,GL_PACK_SKIP_ROWS,GL_PACK_SKIP_PIXELS,
 GL_SCISSOR_BOX,GL_TEXTURE_BINDING_2D,GL_READ_FRAMEBUFFER,GL_DRAW_FRAMEBUFFER,
 GL_PIXEL_PACK_BUFFER,GL_SCISSOR_TEST,GL_TEXTURE_2D,GL_TIMEOUT_EXPIRED,GL_WAIT_FAILED,
 GL_ALREADY_SIGNALED,GL_MAP_READ_BIT,GL_STREAM_READ,GL_COLOR_BUFFER_BIT,GL_LINEAR,
 GL_RGBA,GL_UNSIGNED_BYTE,GL_SYNC_GPU_COMMANDS_COMPLETE,DRM_FORMAT_ABGR8888,GL_FRAMEBUFFER};
std::array<int,9> state{11,12,13,8,15,2,3,0,19};
std::array<int,4> scissorBox{7,8,90,100}; bool scissorEnabled=true;
int waitState=GL_ALREADY_SIGNALED, allocations=0, maps=0, reads=0, fences=0, damageCalls=0;
bool failAlloc=false,failMap=false,failUnmap=false,failFence=false;
std::array<unsigned char,32*24*4> pixels{};
std::vector<CBox> cleared, damaged;
void glGetIntegerv(int key,int* value){
 if(key==GL_SCISSOR_BOX) std::copy(scissorBox.begin(),scissorBox.end(),value);
 else *value=state.at(key);
}
bool glIsEnabled(int){return scissorEnabled;}
void glBindFramebuffer(int key,int value){if(key==GL_FRAMEBUFFER)state[0]=state[1]=value;else state[key==GL_READ_FRAMEBUFFER?0:1]=value;}
void glBindBuffer(int,int value){state[2]=value;}
void glPixelStorei(int key,int value){state.at(key)=value;}
void glBindTexture(int,int value){state[8]=value;}
int glClientWaitSync(GLsync,int flags,int timeout){assert(flags==0&&timeout==0);return waitState;}
void* glMapBufferRange(int,int,int,int){++maps;return failMap?nullptr:pixels.data();}
bool glUnmapBuffer(int){return !failUnmap;}
void glDeleteSync(GLsync){--fences;}
void glGenBuffers(int,GLuint* id){*id=42;}
void glBufferData(int,int,const void*,int){}
void glBlitFramebuffer(int,int,int,int,int,int,int,int,int,int){}
void glReadPixels(int,int,int,int,int,int,void*){
 assert(state[2]==42 && state[3]==1 && state[4]==0 && state[5]==0 && state[6]==0);
 ++reads;pixels.fill(255);
}
GLsync glFenceSync(int,int){if(failFence)return nullptr;++fences;return reinterpret_cast<void*>(1);}
void glFlush(){}
void glClearColor(float,float,float,float){}
void glClear(int){assert(scissorEnabled);cleared.emplace_back(scissorBox[0],scissorBox[1],scissorBox[2],scissorBox[3]);}
namespace Render {
struct IFramebuffer {
 virtual ~IFramebuffer()=default;
 Vector2D m_size; int m_drmFormat=0;
 bool alloc(int w,int h,int format){
  ++allocations;state[0]=state[1]=state[8]=0;
  if(failAlloc)return false;m_size={double(w),double(h)};m_drmFormat=format;return true;
 }
};
namespace GL {struct CGLFramebuffer:IFramebuffer {int getFBID(){return 66;}};}
}
struct Renderer {
 struct {CRegion damage;} m_renderData;
 SP<Render::IFramebuffer> createFB(const char*){return std::make_shared<Render::GL::CGLFramebuffer>();}
 void damageBox(CBox b){damaged.push_back(b);}
} factory;
auto g_pHyprRenderer=&factory;
struct Globals{struct {bool isInitialized(){return true;}} shaderManager;} globals;
auto g_pGlobalState=&globals;
struct OpenGL {
 void setCapStatus(int,bool enabled){scissorEnabled=enabled;}
 void scissor(int x,int y,int w,int h,bool){scissorBox={x,y,w,h};scissorEnabled=true;}
 void scissor(CBox b,bool){scissor(b.x,b.y,b.w,b.h,false);}
 void scissor(std::nullptr_t){scissorEnabled=false;}
} opengl;
auto g_pHyprOpenGL=&opengl;
constexpr int WL_OUTPUT_TRANSFORM_NORMAL=0;
struct Monitor{std::string m_name="eDP-1";int m_transform=0;double m_scale=1;};
template<class T>struct Ref{SP<T> ptr;auto lock()const{return ptr;}T* operator->()const{return ptr.get();}explicit operator bool()const{return !!ptr;}};
struct Animated{Vector2D v;Vector2D value(){return v;}Vector2D goal(){return v;}};
struct Layer {
 std::string m_namespace="quickshell:settings";bool m_fadingOut=false;
 Ref<Monitor> m_monitor{std::make_shared<Monitor>()};
 SP<Animated> m_realPosition=std::make_shared<Animated>(Animated{{0,0}});
 SP<Animated> m_realSize=std::make_shared<Animated>(Animated{{1920,1080}});
};
struct CGlassLayerSurface {
 Ref<Layer> m_layerSurface{std::make_shared<Layer>()};
 bool m_contrastFailed=false;GLsync m_contrastFence=nullptr;GLuint m_contrastBuffer=0;
 SP<Render::IFramebuffer> m_contrastFramebuffer;
 std::chrono::steady_clock::time_point m_contrastRequested{},m_contrastStarted{},m_contrastReady{};
 std::array<float,4> m_contrastBox{},m_contrastPendingBox{};
 std::array<unsigned char,32*24> m_contrastLuma{};
 bool enhanced(){return true;}void damageMaterial(){++damageCalls;}
 std::string contrastSample();
 void sampleContrast(const SP<Render::IFramebuffer>&,CBox,const SGlassSurface&);
};
'''+contrast+acquire+sample_acquire+r'''
void updateDamage(SP<Layer> layer,const SGlassClient& previous,const SGlassClient& current){
'''+damage+r'''
}
void clearMask(bool partial,bool maskReallocated,const std::string& ns="quickshell:settings"){
 CBox transformBox{0,0,1920,1080};int monitorWidth=1920,monitorHeight=1080;
 auto layerSurface=std::make_shared<Layer>();
 layerSurface->m_namespace=ns;
'''+clear.replace('GlassRenderer::SAMPLE_PADDING_PX','60')+r'''
}
int main(){
 using namespace std::chrono;
 auto input=std::make_shared<Render::GL::CGLFramebuffer>();input->m_size={1920,1080};
 SGlassSurface surface{"quickshell:settings","eDP-1",1920,1080};
 SGlassRegion card;card.rect={200,200,500,400};card.frost=8;surface.regions={card};
 auto original=state;auto originalScissor=scissorBox;
 CGlassLayerSurface sample;sample.m_contrastRequested=steady_clock::now();
 sample.sampleContrast(input,{0,0,1920,1080},surface);
 assert(state==original&&scissorEnabled&&scissorBox==originalScissor);
 assert(reads==1&&fences==1&&maps==0&&damageCalls==1);
 waitState=GL_TIMEOUT_EXPIRED;
 for(int frame=0;frame<120;++frame)sample.sampleContrast(input,{0,0,1920,1080},surface);
 assert(reads==1&&maps==0&&fences==1); // One PBO/fence, no queue growth or blocking wait.
 waitState=GL_ALREADY_SIGNALED;
 sample.sampleContrast(input,{0,0,1920,1080},surface);
 assert(fences==0&&maps==1&&sample.m_contrastLuma[0]==255);
 assert(state==original&&scissorEnabled&&scissorBox==originalScissor);
 auto pending=[&]{
  CGlassLayerSurface s;s.m_contrastRequested=steady_clock::now();
  s.sampleContrast(input,{0,0,1920,1080},surface);return s;
 };
 auto timed=pending();timed.m_contrastStarted=steady_clock::now()-seconds(3);
 waitState=GL_TIMEOUT_EXPIRED;int calls=damageCalls;
 timed.sampleContrast(input,{0,0,1920,1080},surface);
 assert(timed.m_contrastFailed&&timed.contrastSample()=="null"&&damageCalls==calls);
 glDeleteSync(timed.m_contrastFence);timed.m_contrastFence=nullptr;
 for(int failure=0;failure<4;++failure){
  auto s=pending();waitState=failure==0?GL_WAIT_FAILED:GL_ALREADY_SIGNALED;
  failMap=failure==1;failUnmap=failure==2;
  if(failure==3)s.m_layerSurface.ptr->m_monitor.ptr.reset();
  if(failure==3)assert(s.contrastSample()=="null");
  else {s.sampleContrast(input,{0,0,1920,1080},surface);assert(s.m_contrastFailed);}
  failMap=failUnmap=false;
  if(s.m_contrastFence)glDeleteSync(s.m_contrastFence);
  assert(state==original&&scissorEnabled&&scissorBox==originalScissor);
 }
 failAlloc=true;auto failed=pending();assert(failed.m_contrastFailed);failAlloc=false;
 failFence=true;auto noFence=pending();assert(noFence.m_contrastFailed);failFence=false;
 assert(state==original&&scissorEnabled&&scissorBox==originalScissor&&fences==0);
 SP<Render::IFramebuffer> scratch;int before=allocations;
 for(int frame=0;frame<120;++frame)blurBackground(input,scratch,8,1,0,1920,1080,nullptr,64,{});
 assert(allocations==before+1);
 input->m_drmFormat=7;blurBackground(input,scratch,8,1,0,1920,1080,nullptr,64,{});
 assert(allocations==before+2&&scratch->m_drmFormat==7); // Same size, changed format must reallocate.
 SP<Render::IFramebuffer> sampleBuffer;Vector2D padding;
 sampleBackground(sampleBuffer,input,{0,0,980,720},padding,1,nullptr);
 before=allocations;
 sampleBackground(sampleBuffer,input,{0,0,980,720},padding,1,nullptr);
 assert(allocations==before);
 input->m_drmFormat=8;sampleBackground(sampleBuffer,input,{0,0,980,720},padding,1,nullptr);
 assert(allocations==before+1&&sampleBuffer->m_drmFormat==8);
 {
  bool frostRendered=false;
  std::optional<std::array<double,15>> m_frostMapping=std::array<double,15>{};
  auto m_frostFramebuffer=std::make_shared<Render::GL::CGLFramebuffer>();
  auto m_frostInputFramebuffer=std::make_shared<Render::GL::CGLFramebuffer>();
  auto m_frostTempFramebuffer=std::make_shared<Render::GL::CGLFramebuffer>();
  std::weak_ptr<Render::IFramebuffer> released=m_frostInputFramebuffer;
  auto source=input;
'''+release_frost+r'''
  assert(!m_frostMapping&&!m_frostFramebuffer&&!m_frostInputFramebuffer&&!m_frostTempFramebuffer);
  assert(released.expired()&&state[0]==66&&state[1]==66);
 }
 assert((glassDamageBox(surface,{0,0,1920,1080},1)==std::array<double,4>{118,118,664,564}));
 assert(!glassDamageBox(surface,{0,0,1920,1080},0));
 auto scaled=glassDamageBox(surface,{1920,-100,1920,1080},2);
 assert(scaled&&(*scaled)[0]==2039&&(*scaled)[1]==19);
 SGlassClient previous,current;previous.enhanced=current.enhanced=true;
 previous.surfaces={surface};surface.regions[0].rect[0]+=100;current.surfaces={surface};
 auto layer=std::make_shared<Layer>();updateDamage(layer,previous,current);
 assert(damaged.size()==2&&damaged[0].x==118&&damaged[1].x==218);
 assert(damaged[0].w==664&&damaged[1].w==664);damaged.clear();
 current.surfaces.clear();updateDamage(layer,previous,current);
 assert(damaged.size()==1&&damaged[0].w==1920);damaged.clear(); // Missing geometry uses full fallback.
 current.surfaces={surface,surface};updateDamage(layer,previous,current);
 assert(damaged.size()==1&&damaged[0].w==1920);damaged.clear(); // Ambiguous layers also use full fallback.
 current.enhanced=false;updateDamage(layer,previous,current);
 assert(damaged.size()==1&&damaged[0].w==1920);damaged.clear();
 current.enhanced=true;layer->m_monitor.ptr->m_transform=1;updateDamage(layer,previous,current);
 assert(damaged.size()==1&&damaged[0].w==1920);
 g_pHyprRenderer->m_renderData.damage=CRegion{CBox{100,100,10,20}};
 g_pHyprRenderer->m_renderData.damage.add(CBox{1000,500,30,40});
 clearMask(true,false);
 assert(cleared.size()==2&&cleared[0].w*cleared[0].h+cleared[1].w*cleared[1].h==1400);
 for(const auto* ns : {"quickshell:popup", "quickshell:popupMorph"}) {
  cleared.clear();clearMask(true,false,ns);
  assert(cleared.size()==2&&cleared[0].w*cleared[0].h+cleared[1].w*cleared[1].h==1400);
  cleared.clear();clearMask(true,true,ns);
  assert(cleared.size()==1&&cleared[0].w==1920&&cleared[0].h==1080);
 }
 cleared.clear();clearMask(true,true);
 assert(cleared.size()==1&&cleared[0].w==1920&&cleared[0].h==1080); // Initialize new storage.
}
'''

if '--contrast-only' in sys.argv[2:]:
    begin = code.index('int main(){')
    end = code.index(' SP<Render::IFramebuffer> scratch;', begin)
    code = code[:code.index('void updateDamage(')] + code[begin:end] + '\n}\n'

with tempfile.TemporaryDirectory(prefix='native-glass-safety-', dir='/tmp') as directory:
    cpp = Path(directory) / 'check.cpp'
    binary = Path(directory) / 'check'
    cpp.write_text(code)
    flags = subprocess.check_output(['pkg-config', '--cflags', '--libs', 'hyprutils', 'pixman-1'], text=True).split()
    subprocess.run(['c++', '-std=c++23', '-O0', '-I'+str(source), str(cpp), '-o', str(binary), *flags], check=True)
    subprocess.run([str(binary)], check=True)
print('PASS: real contrast state/error/timeout paths, format reuse, old/new material damage and partial mask clear; mock GL only.')
