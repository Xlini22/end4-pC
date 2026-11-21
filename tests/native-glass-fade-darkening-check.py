#!/usr/bin/env python3
"""Exercise the actual fade material branch with no GL or rendering."""
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]) / 'src'
layer = (source / 'GlassLayerSurface.cpp').read_text()
start = layer.index('    if (layerSurface->m_fadingOut) {\n        maskInfo.darkening = m_lastDarkening;')
end = layer.index('    if (const auto* surface = enhancedSurface())', start)
assert 'std::array<float, 2> m_lastDarkening{};' in (source / 'GlassLayerSurface.hpp').read_text()
code = r'''
#include <array>
#include <cassert>
#include <memory>
#include <string>
struct Layer {bool m_fadingOut=false;int pid=42;std::string m_namespace="quickshell:popup";int getPID()const{return pid;}};
struct Optics {std::array<float,2> value;auto darkeningValue()const{return value;}bool darkeningTransition()const{return false;}};
Optics optics{{.6f,0}};bool hasProfile=true;int lookups=0;
const Optics* glassDarkeningOptics(int pid,const std::string& key){++lookups;assert(pid==42&&key=="bar");return hasProfile?&optics:nullptr;}
std::string glassProfileKey(const std::string&){return "bar";}
struct Mask {std::array<float,2> darkening{};};
void damageMaterial(){assert(false);}
std::array<float,2> m_lastDarkening{};
auto layerSurface=std::make_shared<Layer>();
Mask frame(){Mask maskInfo;
''' + layer[start:end] + r'''
return maskInfo;}
int main(){
 assert(frame().darkening[0]==.6f);
 layerSurface->m_fadingOut=true;layerSurface->pid=-1;hasProfile=false;
 const int previous=lookups;
 for(int i=0;i<10;++i)assert(frame().darkening[0]==.6f);
 assert(lookups==previous);
 layerSurface->m_fadingOut=false;layerSurface->pid=42;hasProfile=true;
 optics.value={.2f,1};assert(frame().darkening[1]==1);
 layerSurface->m_fadingOut=true;hasProfile=false;optics.value={0,0};
 assert(frame().darkening[0]==.2f&&frame().darkening[1]==1);
 layerSurface->m_fadingOut=false;
 assert(frame().darkening[0]==0&&frame().darkening[1]==0);
 m_lastDarkening={};layerSurface->m_fadingOut=true;
 assert(frame().darkening[0]==0);
}
'''
with tempfile.TemporaryDirectory() as directory:
    cpp = Path(directory) / 'check.cpp'
    exe = Path(directory) / 'check'
    cpp.write_text(code)
    subprocess.run(['g++', '-std=c++23', '-O0', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('fade darkening: OK; manual/auto retained after owner disappears, live disable unchanged')
