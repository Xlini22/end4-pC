#!/usr/bin/env python3
"""Exercise the actual namespace cache across reload; CPU mocks, no GL."""
import argparse
from pathlib import Path
import resource
import subprocess
import tempfile

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--expect-bug', action='store_true')
args = parser.parse_args()
source = (args.source / 'src/main.cpp').read_text()
functions = source[source.index('static void parseCommaSeparated('):source.index('using renderLayerFn')]
code = r'''
#include <array>
#include <cassert>
#include <cmath>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
using StringConfigPtr=const std::string*;
std::string_view readStringConfig(StringConfigPtr value){return value?*value:std::string_view{};}
struct Layer {std::string m_namespace;};
using PHLLS=std::shared_ptr<Layer>;
struct Global {
 struct {StringConfigPtr layersNamespaces, layersExcludeNamespaces,
         layersNamespacePresets, layersNamespaceMaskThresholds;} config;
 std::unordered_set<std::string> layerNamespaceFilter,layerNamespaceExclude;
 std::unordered_map<std::string,std::string> layerNamespacePresets;
 std::unordered_map<std::string,float> layerNamespaceMaskThresholds;
} global;
auto* g_pGlobalState=&global;
''' + functions + r'''
int main(){
 std::string names="quickshell:bar,quickshell:dock",exclude="never",
  presets="quickshell:bar:clear",thresholds="quickshell:bar=0.03";
 global.config={&names,&exclude,&presets,&thresholds};
 const auto bar=std::make_shared<Layer>("quickshell:bar");
 const auto background=std::make_shared<Layer>("quickshell:background");
 assert(shouldGlassLayer(bar)&&!shouldGlassLayer(background));
 assert(!shouldGlassLayer(nullptr));
 const std::array saved={names,exclude,presets,thresholds};
 for(int reload=0;reload<3;++reload){
  // Hyprland resets plugin options; the native reload callback parses them.
  names.clear();exclude.clear();presets.clear();thresholds.clear();
  parseLayerNamespaceFilters();
  assert(global.layerNamespaceFilter.empty());
  // Layers are disabled during this gap, so shouldGlassLayer is not called.
  names=saved[0];exclude=saved[1];presets=saved[2];thresholds=saved[3];
#ifdef EXPECT_BUG
  assert(shouldGlassLayer(background));
  std::cout<<"Confirmed: unchanged restored settings leave an empty whitelist matching the background\n";
  return 0;
#else
  assert(!shouldGlassLayer(background));
  assert(shouldGlassLayer(bar));
  assert(global.layerNamespaceExclude.contains("never"));
  assert(global.layerNamespacePresets.at("quickshell:bar")=="clear");
  assert(std::abs(global.layerNamespaceMaskThresholds.at("quickshell:bar")-.03f)<.00001f);
#endif
 }
 // Intentional wildcard and exclusion semantics must survive the correction.
 names.clear();exclude="quickshell:background";presets.clear();thresholds.clear();
 parseLayerNamespaceFilters();
 assert(shouldGlassLayer(bar)&&!shouldGlassLayer(background));
 // Lua layer entries merged after parsing must not be erased by an unchanged read.
 names="quickshell:bar";exclude.clear();parseLayerNamespaceFilters();
 global.layerNamespaceFilter.insert("custom-layer");
 assert(shouldGlassLayer(std::make_shared<Layer>("custom-layer")));
 std::cout<<"PASS: repeated reload, filters, exclusions, presets, thresholds and Lua overrides\n";
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / 'check.cpp').write_text(code)
    command = ['g++', '-std=c++23', '-O0', str(path / 'check.cpp'), '-o', str(path / 'check')]
    if args.expect_bug:
        command.insert(1, '-DEXPECT_BUG')
    subprocess.run(command, check=True, timeout=30)
    subprocess.run([str(path / 'check')], check=True, timeout=5)
