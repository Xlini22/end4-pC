#!/usr/bin/env python3
"""Run the bar's real matching/focus/debounce logic with Node; no Qt or GPU."""
from pathlib import Path
import re
import subprocess

repo = Path(__file__).resolve().parents[1]
qml = (repo / 'modules/ii/bar/Bar.qml').read_text()
match = re.search(r'                function matchesOverlapWindow\(\) \{[\s\S]*?\n                \}', qml)[0]
candidate = re.search(r'readonly property var overlapCandidate: \{([\s\S]*?)\n                \}', qml)[1]
remember = re.search(r'onOverlapCandidateChanged: \{([\s\S]*?)\n                \}', qml)[1]
disable = re.search(r'onAppOverlapEnabledChanged: \{([\s\S]*?)\n                \}', qml)[1]
gate = re.search(r'readonly property bool appOverlapEnabled: ([\s\S]*?)\n                readonly', qml)[1]
zone = re.search(r'\n                exclusiveZone: ([\s\S]*?)\n                WlrLayershell', qml)[1]
assert 'onWantsAppOverlapChanged: appOverlapTimer.restart()' in qml
assert 'interval: 150\n                    onTriggered: barRoot.appOverlapActive = barRoot.wantsAppOverlap' in qml
settings = (repo / 'modules/ii/settings/pages/BarConfig.qml').read_text()
parse = re.search(r'onConfirmClicked: Config.options.bar.appOverlap.classes = (\[\.\.\.new Set\([\s\S]*?\)\])', settings)[1]
subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const Config = {options:{bar:{bottom:true,vertical:false,appOverlap:{enable:true,classes:['firefox']}}}};
const WM = {compositor:'hyprland'};
const ToplevelManager = {activeToplevel:null,toplevels:{values:[]}};
const HyprlandData = {clientForToplevel: win => win.client};
const barRoot = {screen:{name:'eDP-1'},overlapMonitor:{activeWorkspace:{id:1}},
    thisMonitorData:{specialWorkspace:{id:0}},overlapWindow:null};
const enabled = new Function('Config','WM','return '+process.argv[4]);
const zone = new Function('appOverlapEnabled','appOverlapActive','contentExclusiveZone','islandTopInset','return '+process.argv[5]);
let appOverlapActive=false, overlapCandidate=null, now=0, deadline=null;
const appOverlapTimer={restart(){deadline=now+150;},stop(){deadline=null;}};
MATCH
const candidate = new Function('barRoot','ToplevelManager','appOverlapEnabled',process.argv[1]);
const remember = new Function('overlapCandidate','overlapWindow',process.argv[2]+'; return overlapWindow;');
const disable = new Function('appOverlapEnabled','appOverlapTimer','appOverlapActive',process.argv[3]+'; return appOverlapActive;');
let previous=false;
function update(){
    barRoot.appOverlapEnabled=enabled(Config,WM);
    appOverlapActive=disable(barRoot.appOverlapEnabled,appOverlapTimer,appOverlapActive);
    overlapCandidate=candidate(barRoot,ToplevelManager,barRoot.appOverlapEnabled);
    barRoot.overlapWindow=remember(overlapCandidate,barRoot.overlapWindow);
    const next=matchesOverlapWindow();
    barRoot.wantsAppOverlap=next;
    if(next!==previous){appOverlapTimer.restart();previous=next;}
}
function tick(ms){now+=ms;if(deadline!==null&&now>=deadline){deadline=null;appOverlapActive=barRoot.wantsAppOverlap;}}
// The attached object only resolves the handle; its own monitor/workspace are null.
function win(appId,monitor='eDP-1',workspace=1){return {appId,HyprlandToplevel:{monitor:null,workspace:null,
    handle:{monitor:{name:monitor},workspace:{id:workspace}}},client:{}};}
const firefox=win('firefox'),terminal=win('foot'),other=win('foot','HDMI-A-1');
ToplevelManager.toplevels.values=[firefox,terminal,other];
const handle=firefox.HyprlandToplevel.handle;
firefox.HyprlandToplevel.handle=null;
ToplevelManager.activeToplevel=firefox;update();tick(200);assert.equal(appOverlapActive,false);
firefox.HyprlandToplevel.handle=handle;
ToplevelManager.activeToplevel=firefox;update();tick(149);assert.equal(appOverlapActive,false);
tick(1);assert.equal(appOverlapActive,true);
// Layer-shell focus and focus on a different monitor must not restore the gap.
ToplevelManager.activeToplevel=null;update();tick(200);assert.equal(appOverlapActive,true);
ToplevelManager.activeToplevel=other;update();tick(200);assert.equal(appOverlapActive,true);
ToplevelManager.activeToplevel=terminal;update();tick(70);
ToplevelManager.activeToplevel=firefox;update();tick(150);assert.equal(appOverlapActive,true);
ToplevelManager.activeToplevel=terminal;update();tick(150);assert.equal(appOverlapActive,false);
firefox.appId='changed-title-independent-id';firefox.client.initialClass='firefox';
ToplevelManager.activeToplevel=firefox;update();tick(150);assert.equal(appOverlapActive,true);
// Empty workspace, special workspace, pinned windows and closure.
barRoot.overlapMonitor.activeWorkspace.id=2;update();tick(150);assert.equal(appOverlapActive,false);
barRoot.thisMonitorData.specialWorkspace.id=1;update();tick(150);assert.equal(appOverlapActive,true);
barRoot.thisMonitorData.specialWorkspace.id=0;firefox.client.pinned=true;
update();tick(150);assert.equal(appOverlapActive,true);
ToplevelManager.toplevels.values=[terminal,other];update();tick(150);assert.equal(appOverlapActive,false);
ToplevelManager.toplevels.values.push(firefox);update();tick(150);assert.equal(appOverlapActive,true);
firefox.HyprlandToplevel.handle.monitor.name='HDMI-A-1';update();tick(150);assert.equal(appOverlapActive,false);
firefox.HyprlandToplevel.handle.monitor.name='eDP-1';
for(const classes of [[],['Firefox'],['fire*'],['']]){
    Config.options.bar.appOverlap.classes=classes;update();tick(150);assert.equal(appOverlapActive,false);
}
Config.options.bar.appOverlap.classes=['firefox'];update();tick(150);assert.equal(appOverlapActive,true);
for(const [key,value,restore] of [[Config.options.bar,'bottom',true],[Config.options.bar,'vertical',false],
    [Config.options.bar.appOverlap,'enable',true],[WM,'compositor','hyprland']]){
    key[value]=typeof restore==='boolean'?!restore:'niri';update();assert.equal(barRoot.appOverlapEnabled,false);
    assert.equal(appOverlapActive,false);key[value]=restore;update();tick(150);assert.equal(appOverlapActive,true);
}
for(const size of [0,4,36,40])for(const inset of [0,5]){
    assert.equal(zone(true,true,size,inset),0);
    assert.equal(zone(true,false,size,inset),size>0?size+inset:size);
    assert.equal(zone(false,true,size,inset),size>0?size+inset:size);
}
const parse=new Function('value','return '+process.argv[6]);
assert.deepEqual(parse(' firefox\r\n\norg.kde.dolphin\nfirefox\napp,with-comma '),['firefox','org.kde.dolphin','app,with-comma']);
assert.deepEqual(parse(' \n\r\n'),[]);
'''.replace('MATCH', match), candidate, remember, disable, gate, zone, parse], check=True)
print('bar app overlap: OK (focus, monitors, debounce, workspace, closure, exact classes, settings and reserved space)')
