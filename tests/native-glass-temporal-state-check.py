#!/usr/bin/env python3
"""Compile the actual temporal GL path against mocks. No GL library/context.
Run: python tests/native-glass-temporal-state-check.py PATCHED_NATIVE_SOURCE
"""
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

src = Path(sys.argv[1]).resolve() / 'src'
header = (src / 'GlassRenderer.hpp').read_text()
renderer = (src / 'GlassRenderer.cpp').read_text()
start = header.index('struct SAdaptiveDarkening {')
state = header[start:header.index('\n};', start) + 3]
helpers = renderer[renderer.index('SAdaptiveDarkening::~'):renderer.index('static GLuint fbId(')]
start = renderer.index('    glUniform1i(uniforms.temporalMode, 0);')
work = renderer[start:renderer.rindex('    drawGlass();')]
code = r'''
#include "DarkeningWindow.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <utility>
#include <vector>
using GLuint=unsigned;using GLint=int;using GLenum=unsigned;using GLboolean=bool;
enum {GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_TEXTURE_MAG_FILTER,GL_NEAREST,GL_TEXTURE_WRAP_S,GL_TEXTURE_WRAP_T,
 GL_CLAMP_TO_EDGE,GL_RGBA32F,GL_RGBA,GL_HALF_FLOAT,GL_FLOAT,GL_DRAW_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_FRAMEBUFFER_COMPLETE,
 GL_ACTIVE_TEXTURE,GL_TEXTURE0=32,GL_TEXTURE3=35,GL_TEXTURE_BINDING_2D,GL_SAMPLER_BINDING,GL_SCISSOR_BOX,
 GL_COLOR_WRITEMASK,GL_STENCIL_TEST,GL_DEPTH_TEST,GL_CULL_FACE,GL_DRAW_FRAMEBUFFER_BINDING,GL_VIEWPORT,
 GL_BLEND,GL_SCISSOR_TEST,GL_TRIANGLE_STRIP};
struct GLState {
 int active=GL_TEXTURE0,draw=91;
 std::array<int,4> textures{101,102,103,104},samplers{201,202,203,204};
 std::array<int,4> viewport{1,2,1920,1080},scissor{4,5,400,500};
 std::array<bool,4> colors{true,false,true,false};
 std::array<bool,64> caps{};
 bool operator==(const GLState&)const=default;
} gl;
int generated=0,releasedTextures=0,releasedFBs=0,captures=0,composites=0,mode=0;
std::array<int,64> attachments{};int lastCapturedTexture=0;float bootstrapPolicy=2;
bool fail=false;std::array<int,33> slots{},capturedSlots{};
void glGenTextures(int n,GLuint* ids){for(int i=0;i<n;++i)ids[i]=++generated;}
void glGenFramebuffers(int n,GLuint* ids){for(int i=0;i<n;++i)ids[i]=++generated;}
void glDeleteTextures(int n,const GLuint* ids){for(int i=0;i<n;++i)releasedTextures+=ids[i]!=0;}
void glDeleteFramebuffers(int n,const GLuint* ids){for(int i=0;i<n;++i)releasedFBs+=ids[i]!=0;}
void glActiveTexture(int unit){gl.active=unit;}
void glBindTexture(int,GLuint id){gl.textures[gl.active-GL_TEXTURE0]=int(id);}
void glBindSampler(int unit,GLuint id){gl.samplers[unit]=int(id);}
void glBindFramebuffer(int,GLuint id){gl.draw=int(id);}
void glTexParameteri(int,int,int){}
void glTexImage2D(int,int,int internal,int width,int height,int,int format,int type,const void*){
 assert(width==33&&height==1);
 // OpenGL ES sized-format table: RGBA32F accepts FLOAT, not HALF_FLOAT.
 assert(internal==GL_RGBA32F&&format==GL_RGBA&&type==GL_FLOAT);
}
void glFramebufferTexture2D(int,int,int,GLuint texture,int){attachments[gl.draw]=texture;}
int glCheckFramebufferStatus(int){return fail?0:GL_FRAMEBUFFER_COMPLETE;}
bool glIsEnabled(int cap){return gl.caps[cap];}
void glColorMask(bool a,bool b,bool c,bool d){gl.colors={a,b,c,d};}
void glViewport(int a,int b,int c,int d){gl.viewport={a,b,c,d};}
void glGetBooleanv(int cap,bool* out){assert(cap==GL_COLOR_WRITEMASK);std::copy(gl.colors.begin(),gl.colors.end(),out);}
void glGetIntegerv(int cap,int* out){
 switch(cap){
 case GL_ACTIVE_TEXTURE:*out=gl.active;break;
 case GL_TEXTURE_BINDING_2D:*out=gl.textures[gl.active-GL_TEXTURE0];break;
 case GL_SAMPLER_BINDING:*out=gl.samplers[gl.active-GL_TEXTURE0];break;
 case GL_DRAW_FRAMEBUFFER_BINDING:*out=gl.draw;break;
 case GL_SCISSOR_BOX:std::copy(gl.scissor.begin(),gl.scissor.end(),out);break;
 case GL_VIEWPORT:std::copy(gl.viewport.begin(),gl.viewport.end(),out);break;
 default:assert(false);
 }
}
struct OpenGL {
 void setCapStatus(int cap,bool value){gl.caps[cap]=value;}
 void scissor(int a,int b,int c,int d,bool){gl.scissor={a,b,c,d};}
} openGL;
auto* g_pHyprOpenGL=&openGL;
namespace Hyprutils::Utils {
 template<class F>struct CScopeGuard {F f;explicit CScopeGuard(F value):f(value){}~CScopeGuard(){f();}};
}
void glUniform1i(int uniform,int value){if(uniform==0)mode=value;}
void glUniform1f(int,float){}
void glUniform2f(int,float,float automatic){assert(automatic==0);}
void glUniform4f(int uniform,float,float,float,float policy){if(uniform==2)bootstrapPolicy=policy;}
void glUniform1iv(int,int n,const int* values){assert(n==33);std::copy(values,values+n,slots.begin());}
void glDrawArrays(int,int,int){
 capturedSlots=slots;
 assert(mode==1&&gl.viewport[2]==33&&gl.viewport[3]==1);
 for(int cap:{GL_BLEND,GL_SCISSOR_TEST,GL_STENCIL_TEST,GL_DEPTH_TEST,GL_CULL_FACE})assert(!gl.caps[cap]);
 assert((gl.colors==std::array{true,true,true,true}));assert(gl.samplers[3]==0);lastCapturedTexture=attachments[gl.draw];++captures;
}
struct SGlassRegion {std::array<float,4> rect{};int id=0,darkeningGroup=0;};
using Region=SGlassRegion;
STATE
HELPERS
struct Mask {SAdaptiveDarkening* temporal=nullptr;std::array<float,2> darkening{};
 std::vector<Region> regions,temporalRegions;bool temporalSample=true,sectionDarkening=false;};
struct Uniforms {int temporalMode=0,temporalHistory=1,temporalStep=2,temporalBlend=3,temporalSlots=4,darkening=5;} uniforms;
void render(Mask* mask){
 const auto expected=gl;
 auto uploadRegions=[](const auto& regions){assert(regions.size()<=32);};
 auto drawGlass=[&]{
  assert(gl.draw==expected.draw&&gl.viewport==expected.viewport&&gl.colors==expected.colors);
  for(int cap:{GL_BLEND,GL_STENCIL_TEST,GL_DEPTH_TEST,GL_CULL_FACE})assert(gl.caps[cap]==expected.caps[cap]);
  if(mode==2){assert(gl.samplers[3]==0);assert(gl.textures[3]==lastCapturedTexture);}++composites;
  gl.caps[GL_SCISSOR_TEST]=false;
 };
 WORK
 drawGlass();
}
int main(){
 for(int cap:{GL_BLEND,GL_SCISSOR_TEST,GL_STENCIL_TEST,GL_DEPTH_TEST,GL_CULL_FACE})gl.caps[cap]=true;
 const auto original=gl;
 {
  SAdaptiveDarkening history;
  Mask mask{&history,{.4f,1},{{{20,0,10,10}}},{{{0,0,10,10}},{{10,0,10,10}},{{20,0,10,10}}},true};
  for(int i=0;i<3;++i)mask.temporalRegions[i].id=10+i;mask.regions[0].id=12;
  render(&mask);assert(gl==original);assert(captures==1&&composites==1&&generated==4);
  assert(history.clock.initialized&&mode==2&&slots[1]==3&&bootstrapPolicy<0);
  mask.temporalSample=false;render(&mask);assert(gl==original&&captures==1&&generated==4);
  mask.darkening[1]=0;render(&mask);assert(!history.clock.initialized&&mode==0);gl=original;
  mask.temporalSample=true;mask.darkening[1]=1;render(&mask);assert(captures==2&&generated==4&&gl==original);
  history.presentedBlend=.25f;history.clock.changed-=.7;
  history.restart(history.clock.last);assert(history.resumeBlend==.25f);render(&mask);assert(bootstrapPolicy==.25f);assert(bootstrapPolicy>=0&&captures==3&&gl==original); // Existing visible scene keeps its tone.
  history.restart(history.clock.last,true);render(&mask);assert(bootstrapPolicy<0&&captures==4&&generated==4&&gl==original); // Appearance uses the fresh GPU sample before composition.
  const auto deadline=history.clock.start;
  std::swap(mask.temporalRegions[0],mask.temporalRegions[2]);
  mask.temporalRegions[0].rect[2]+=2; // Same ID survives resizing and area-based sorting.
  history.lastDraw=-1;render(&mask);
  assert(captures==5&&generated==4&&gl==original&&history.clock.start==deadline);
  assert(capturedSlots[1]==3&&capturedSlots[2]==2&&capturedSlots[3]==1&&slots[1]==1);
  mask.temporalRegions[1].id=99;history.lastDraw=-1;render(&mask);
  assert(captures==6&&capturedSlots[2]==-1&&gl==original&&generated==4&&history.clock.start==deadline);
 }
 assert(releasedTextures==2&&releasedFBs==2);
 {
  fail=true;SAdaptiveDarkening history;
  Mask mask{&history,{.4f,1},{},{},true};render(&mask);
  assert(history.failed&&mode==0&&captures==6);gl.caps[GL_SCISSOR_TEST]=true;assert(gl==original);
  const auto allocationCount=generated;render(&mask);assert(generated==allocationCount);gl.caps[GL_SCISSOR_TEST]=true;assert(gl==original);
 }
 assert(releasedTextures==4&&releasedFBs==4);
 {
  fail=false;SAdaptiveDarkening history;
  Mask mask{&history,{.4f,1},{{{0,0,10,10}},{{10,0,10,10}},{{20,0,10,10}},{{30,0,10,10}}},
      {{{0,0,10,10}},{{10,0,10,10}},{{20,0,10,10}}},true,true};
  for(int i=0;i<3;++i)mask.temporalRegions[i].id=-i-1;
  mask.regions[0].darkeningGroup=2;mask.regions[1].darkeningGroup=1;
  mask.regions[2].darkeningGroup=0;mask.regions[3].darkeningGroup=3;
  render(&mask);assert(slots[1]==2&&slots[2]==1&&slots[3]==0&&slots[4]==3&&gl==original);
  const auto deadline=history.clock.start;
  std::swap(mask.temporalRegions[0],mask.temporalRegions[2]);
  mask.temporalRegions[0].rect[2]+=5;history.lastDraw=-1;render(&mask);
  assert(capturedSlots[1]==3&&capturedSlots[2]==2&&capturedSlots[3]==1);
  assert(slots[1]==2&&slots[2]==3&&slots[3]==0&&slots[4]==1&&history.clock.start==deadline&&gl==original);
  mask.temporalRegions.erase(mask.temporalRegions.begin()+1);history.lastDraw=-1;render(&mask);
  assert(slots[1]==0&&slots[2]==2&&slots[3]==0&&slots[4]==1&&gl==original);
 }

}
'''.replace('STATE', state).replace('HELPERS', helpers).replace('WORK', work)
with tempfile.TemporaryDirectory(prefix='temporal-gl-state-') as directory:
    tmp=Path(directory);(tmp/'check.cpp').write_text(code)
    subprocess.run(['g++','-std=c++23','-O0','-I',str(src),str(tmp/'check.cpp'),'-o',str(tmp/'check')],check=True)
    subprocess.run([str(tmp/'check')],check=True)
print('native temporal state: OK (real GL path mocked; restoration, band slot mapping, manual mode, closing snapshot, bounded allocations, failure and destruction)')
