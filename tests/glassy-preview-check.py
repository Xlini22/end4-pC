#!/usr/bin/env python3
"""CPU only: python3 tests/glassy-preview-check.py [SOURCE_ROOT]."""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile

repo = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
page = (repo / 'modules/ii/settings/pages/GlassyConfig.qml').read_text()
global_source = (repo / 'GlobalStates.qml').read_text()

def body(text, marker):
    start = text.index('{', text.index(marker)) + 1
    depth = 1
    for end in range(start, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if depth == 0:
            return text[start:end]
    raise AssertionError(marker)

expressions = {}
for kind, path in [('bar', 'modules/ii/bar/Bar.qml'), ('vertical', 'modules/ii/verticalBar/VerticalBar.qml')]:
    text = (repo/path).read_text()
    assert '(GlobalStates.barOpen || GlobalStates.glassyPreviewTargets.includes("bar"))' in text
    assert 'preview && !GlobalStates.barOpen ? 0 :' in text
    assert '(!normalMustShow || !Config?.options.bar.autoHide.pushWindows)' in text
    assert 'property bool mustShow: preview || normalMustShow' in text
for side in ['Left', 'Right']:
    text = (repo/f'modules/ii/sidebar{side}/Sidebar{side}.qml').read_text()
    expression = re.search(r'readonly property bool open: ([^\n]+)', text)[1]
    expressions[side] = expression
    assert expression == f'GlobalStates.sidebar{side}Open || preview'
    assert 'if (visible && !root.preview)' in text and 'if (!root.preview) panelWindow.hide();' in text
    assert 'if (panelWindow.visible && !root.preview) GlobalFocusGrab.addDismissable(panelWindow)' in text
    assert 'item: root.preview ? null :' in text
    assert 'target: root\n' in text and 'function onOpenChanged()' in text
    if side=='Left':
        assert 'onOpenChanged: {\n        if (root.open) root.load();' in text
        assert 'exclusiveZone: root.preview && !GlobalStates.sidebarLeftOpen ? 0 :' in text
        assert 'root.preview ? WlrKeyboardFocus.None : WlrKeyboardFocus.OnDemand' in text
    else:
        assert '!root.preview && GlobalStates.sidebarRightOpen ?' in text

dock = (repo/'modules/ii/dock/Dock.qml').read_text()
expressions['reveal'] = 'function reveal(){' + body(dock, 'property bool reveal:') + '}'
assert 'WlrLayershell.layer: appOverlapActive || preview ? WlrLayer.Overlay : WlrLayer.Top' in dock
assert 'exclusiveZone: (root.pinned && !fullscreenOnThisMonitor && !appOverlapActive)' in dock
match = re.search(r'readonly property var glassyPreviewTargets: ([^\n]+)\n\s*([^\n]+)',global_source)
preview_expression = match[1]+' '+match[2]
assert 'property Item glassyPreviewPage: null' in global_source
assert 'onPreviewChanged: syncPreview()' in page and 'onVisibleChanged: if (!visible) preview = false' in page
assert 'Component.onDestruction: if (GlobalStates.glassyPreviewPage === root) GlobalStates.glassyPreviewPage = null' in page
assert 'function onSettingsOpenChanged() { if (!GlobalStates.settingsOpen) root.preview = false }' in page
assert 'function onScreenLockedChanged() { if (GlobalStates.screenLocked) root.preview = false }' in page
assert page.index('objectName: "glass-multi-edit"') < page.index('objectName: "glass-preview"') < page.index('model: GlassProfiles.keys')
assert 'Config.options' not in body(page, 'function syncPreview(')
script = r'''
const assert=require('assert/strict'),vm=require('vm');
const state={settingsOpen:true,screenLocked:false,glassyPreviewPage:null,barOpen:false,sidebarLeftOpen:false,sidebarRightOpen:true};
const context={GlobalStates:state,preview:false,visible:true,targets:['dock']};context.root=context;
vm.createContext(context);vm.runInContext('function syncPreview(){'+SYNC+'}',context);
vm.createContext(state);Object.defineProperty(state,'glassyPreviewTargets',{get(){return vm.runInContext(EXPRESSION,state)}});
const ordinaryState=()=>JSON.stringify([state.barOpen,state.sidebarLeftOpen,state.sidebarRightOpen]);
const before=ordinaryState();context.preview=true;context.syncPreview();assert.equal(state.glassyPreviewPage,vm.runInContext('root',context));
assert.deepEqual(Array.from(state.glassyPreviewTargets),['dock']);
context.targets=['bar','sidebar'];assert.deepEqual(Array.from(state.glassyPreviewTargets),['bar','sidebar']);
// Both sidebars are effectively visible but their actual open state stays intact.
for(const side of ['Left','Right']){
 const flag=state['sidebar'+side+'Open'];
 assert.equal(vm.runInContext(SIDES[side],vm.createContext({GlobalStates:state,preview:true})),true);
 assert.equal(vm.runInContext(SIDES[side],vm.createContext({GlobalStates:state,preview:false})),flag);
}
context.targets=[];assert.equal(state.glassyPreviewTargets.length,0);assert.equal(ordinaryState(),before);
context.targets=['dock'];context.visible=false;assert.equal(state.glassyPreviewTargets.length,0);context.syncPreview();assert.equal(state.glassyPreviewPage,null);
context.visible=true;context.syncPreview();state.settingsOpen=false;assert.equal(state.glassyPreviewTargets.length,0);
context.preview=false;context.syncPreview();assert.equal(state.glassyPreviewPage,null);
state.settingsOpen=true;context.preview=true;context.syncPreview();state.screenLocked=true;assert.equal(state.glassyPreviewTargets.length,0);
context.preview=false;context.syncPreview();state.screenLocked=false;assert.equal(ordinaryState(),before);
// A hidden or destroyed old page must not clear a newer page's preview ownership.
const other={preview:true,visible:true,targets:['sidebar']};state.glassyPreviewPage=other;context.syncPreview();assert.equal(state.glassyPreviewPage,other);
const dock={preview:false,appOverlapActive:false,dockContextMenu:{isOpen:false},DockMagnify:{entries:[]},
 fullscreenOnThisMonitor:false,root:{pinned:false},Config:{options:{dock:{hoverToReveal:false}}},
 dockMouseArea:{containsMouse:false},riseArea:{containsMouse:false},GlobalStates:{isFrameHovered:()=>false},
 dockRoot:{screen:{name:'eDP-1'},position:'bottom'},activeApps:{requestDockShow:false},dragSlots:{requestDockShow:false},ToplevelManager:{activeToplevel:{activated:true}}};
vm.createContext(dock);vm.runInContext(REVEAL,dock);assert.equal(dock.reveal(),false);
dock.preview=true;assert.equal(dock.reveal(),true);dock.fullscreenOnThisMonitor=true;assert.equal(dock.reveal(),true);
dock.preview=false;assert.equal(dock.reveal(),false);dock.fullscreenOnThisMonitor=false;dock.root.pinned=true;assert.equal(dock.reveal(),true);
'''.replace('SYNC',json.dumps(body(page,'function syncPreview('))).replace('EXPRESSION',json.dumps(preview_expression)).replace('SIDES',json.dumps({side:expressions[side] for side in ['Left','Right']})).replace('REVEAL',json.dumps(expressions['reveal']))
with tempfile.TemporaryDirectory(prefix='glassy-preview-check-') as directory:
    path=Path(directory)/'check.js';path.write_text(script)
    subprocess.run(['node',str(path)],check=True)
print('Glassy preview: OK (live selection, ownership/cleanup, no saved-state writes, sidebar focus/input safety, dock reveal and bar reservation; no rendering)')
