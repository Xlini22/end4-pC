#!/usr/bin/env python3
"""Check the actual dock branches with Node, without Qt/rendering."""
from pathlib import Path
import re
import subprocess

repo = Path(__file__).resolve().parents[1]
qml = (repo / 'modules/ii/dock/Dock.qml').read_text()
reveal = re.search(r'property bool reveal: \{([\s\S]*?)\n            \}', qml)[1]
zone = re.search(r'exclusiveZone: ([\s\S]*?)\n\n            anchors', qml)[1]
layer = re.search(r'WlrLayershell.layer: (.*)', qml)[1]
gate = re.search(r'appOverlapEnabled: ([\s\S]*?)\n            \}', qml)[1]
subprocess.run(['node', '-e', r'''
const assert=require('node:assert/strict');
const reveal=new Function('s','with(s){'+process.argv[1]+'}');
const zone=new Function('s','with(s){return '+process.argv[2]+'}');
const layer=new Function('s','with(s){return '+process.argv[3]+'}');
const gate=new Function('s','with(s){return '+process.argv[4]+'}');
const s={appOverlapActive:false,dockContextMenu:{isOpen:false},DockMagnify:{entries:[]},
 dockRoot:{position:'bottom'},fullscreenOnThisMonitor:false,Config:{options:{dock:{hoverToReveal:false,appOverlap:{enable:true}}}},
 dockMouseArea:{containsMouse:false},riseArea:{containsMouse:false},root:{pinned:false},
 activeApps:{requestDockShow:false},dragSlots:{requestDockShow:false},ToplevelManager:{activeToplevel:{activated:true}},
 GlobalStates:{isFrameHovered:()=>false},DockStyle:{zone:80},WlrLayer:{Top:2,Overlay:3},WM:{compositor:'hyprland'}};
for(const pinned of [false,true])for(const fullscreen of [false,true])for(const hover of [false,true])
for(const requested of [false,true])for(const active of [false,true])for(const menu of [false,true]){
 s.root.pinned=pinned;s.fullscreenOnThisMonitor=fullscreen;s.Config.options.dock.hoverToReveal=hover;
 s.dockMouseArea.containsMouse=hover;s.activeApps.requestDockShow=requested;
 s.ToplevelManager.activeToplevel.activated=active;s.dockContextMenu.isOpen=menu;
 s.appOverlapActive=false;
 assert.equal(reveal(s),menu||(fullscreen?hover:(pinned||hover||requested||!active)));
 assert.equal(zone(s),pinned&&!fullscreen?80:0);assert.equal(layer(s),2);
 s.appOverlapActive=true;
 assert.equal(reveal(s),true);assert.equal(zone(s),0);assert.equal(layer(s),3);
}
assert.equal(gate(s),true);
s.dockRoot.position='left';assert.equal(gate(s),false);
s.dockRoot.position='right';assert.equal(gate(s),false);
s.dockRoot.position='bottom';s.WM.compositor='niri';assert.equal(gate(s),false);
s.WM.compositor='hyprland';s.Config.options.dock.appOverlap.enable=false;assert.equal(gate(s),false);
''', reveal, zone, layer, gate], check=True)
assert 'classes: Config.options.dock.appOverlap.classes' in qml
assert 'appOverlapEnabled: barRoot.appOverlapEnabled' in (repo / 'modules/ii/bar/Bar.qml').read_text()
print('dock overlap: OK (64 visibility combinations, fullscreen, pin, menu, layers, reserved space and enable gates)')
