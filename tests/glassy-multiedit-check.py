#!/usr/bin/env python3
"""CPU only: python3 tests/glassy-multiedit-check.py [GlassyConfig.qml]."""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
qml = Path(sys.argv[1]) if len(sys.argv) > 1 else repo / 'modules/ii/settings/pages/GlassyConfig.qml'
source = qml.read_text()

def body(text, marker):
    start = text.index('{', text.index(marker)) + 1
    depth = 1
    for end in range(start, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if not depth:
            return text[start:end]
    raise AssertionError(marker)

functions = []
for name, arguments in [('commonValue', 'name'), ('writeValue', 'name, value, keys = targets'),
                        ('toggleMultiEdit', ''), ('toggleProfile', 'key'),
                        ('sliderPressed', 'control, name'), ('sliderMoved', 'control, name'), ('resetSelected', '')]:
    functions.append('function ' + name + '(' + arguments + '){' + body(source, 'function ' + name + '(') + '}')
expressions = {name: re.search(r'readonly property \w+ ' + name + r': ([^\n]+)', source)[1]
               for name in ['target', 'targets', 'automaticMode', 'blurLimit']}
visibility = {}
for name, identifier in [('automatic', 'automaticStrengthControl'), ('manual', 'darkeningControl')]:
    start = source.rfind('        ColumnLayout {', 0, source.index('id: ' + identifier))
    column = body(source[start:], 'ColumnLayout')
    visibility[name] = re.search(r'visible: ([^\n]+)', column)[1].replace('root.', '')
    assert 'Accessible.description:' in column
assert visibility == {'automatic': 'automaticMode === true', 'manual': 'automaticMode === false'}
assert 'visible: root.targets.length > 0' in source
assert source.count('property bool edited: false') == 3
assert source.count('property real editValue: 0') == 3
assert 'onCheckedChanged: if (checked !== root.profile' not in source
assert 'onSelected: value => root.writeValue("automaticDarkening", value)' in source
assert 'max: root.blurLimit' in source
profile_source = (repo / 'services/GlassProfiles.qml').read_text()
defaults = 'function defaults(key){' + body(profile_source, 'function defaults(') + '}'
script = r'''
const vm=require('vm'),assert=require('assert/strict');
const keys=['bar','dock','sidebar','settings','lockscreen','terminal','overview'];
const writes=[];const profiles={};
for(const key of keys){
 const values={enable:true,rim:7,refraction:135,blur:key==='bar'?7:12,reflections:key==='bar'?25:75,
  darkening:key==='bar'?15:35,automaticDarkening:key!=='bar',automaticDarkeningStrength:key==='bar'?20:80};
 profiles[key]=new Proxy(values,{set(object,name,value){writes.push([key,name,value]);object[name]=value;return true;}});
}
const context={selectedTab:1,multiEdit:false,selectedProfiles:[],Config:{options:{background:{widgets:{glass:{haze:3}}}}},
 GlassProfiles:{keys,profile:key=>profiles[key],reset:key=>Object.assign(profiles[key],context.defaults(key))}};
context.root=context;vm.createContext(context);vm.runInContext(FUNCTIONS+'\n'+DEFAULTS,context);
for(const [name,expression] of Object.entries(EXPRESSIONS))vm.runInContext(`Object.defineProperty(this,${JSON.stringify(name)},{get(){return ${expression}}});`,context);
const snapshot=()=>JSON.stringify(profiles);
const before=snapshot();
assert.equal(context.target,'dock');assert.equal(context.commonValue('darkening'),35);
context.toggleMultiEdit();assert.deepEqual(Array.from(context.targets),['dock']);
context.toggleProfile('bar');assert.equal(context.commonValue('automaticDarkening'),null);assert.equal(context.commonValue('reflections'),null);
assert.equal(context.blurLimit,8);
for(const expression of Object.values(VISIBILITY))assert.equal(vm.runInContext(expression,context),false);
for(const name of ['rim','refraction','blur','reflections','darkening','automaticDarkeningStrength'])context.commonValue(name);
assert.equal(snapshot(),before);assert.equal(writes.length,0); // Selection and neutral slider handles never modify saved values.
const manual=keys.map(key=>profiles[key].darkening),strength=keys.map(key=>profiles[key].automaticDarkeningStrength);
context.writeValue('automaticDarkening',true);
assert(writes.every(record=>record[1]==='automaticDarkening'));assert.equal(context.automaticMode,true);
assert.equal(vm.runInContext(VISIBILITY.automatic,context),true);assert.equal(vm.runInContext(VISIBILITY.manual,context),false);
context.writeValue('automaticDarkening',false);
assert.equal(vm.runInContext(VISIBILITY.automatic,context),false);assert.equal(vm.runInContext(VISIBILITY.manual,context),true);
assert.deepEqual(keys.map(key=>profiles[key].darkening),manual);assert.deepEqual(keys.map(key=>profiles[key].automaticDarkeningStrength),strength);
// Programmatic rebind, initial/released state, or pressing an unchanged mixed handle cannot commit a value.
const control={pressed:false,enabled:true,value:50,editKeys:[],edited:false,editValue:0};
writes.length=0;context.sliderPressed(control,'reflections');control.pressed=true;context.sliderPressed(control,'reflections');
control.pressed=false;context.sliderPressed(control,'reflections');assert.equal(writes.length,0);
// Mouse edits commit once, to the profiles and value at the last user move, even if selection/rebinding changes before release.
control.pressed=true;context.sliderPressed(control,'reflections');control.value=60;context.sliderMoved(control,'reflections');
assert.equal(writes.length,0);context.toggleProfile('bar');context.toggleProfile('sidebar');control.value=99;
control.pressed=false;context.sliderPressed(control,'reflections');
assert.deepEqual(writes,[['dock','reflections',60],['bar','reflections',60]]);assert.equal(profiles.sidebar.reflections,75);
// Keyboard/wheel edits apply only the changed field to the current selection.
writes.length=0;control.value=42;context.sliderMoved(control,'darkening');
assert.deepEqual(writes,[['dock','darkening',42],['sidebar','darkening',42]]);assert.equal(profiles.bar.darkening,15);
assert.deepEqual(keys.map(key=>profiles[key].automaticDarkeningStrength),strength);
// A disabled slider discards pending edits, including those interrupted by mode/visibility changes.
writes.length=0;control.pressed=true;context.sliderPressed(control,'reflections');control.value=10;context.sliderMoved(control,'reflections');
control.enabled=false;control.pressed=false;context.sliderPressed(control,'reflections');context.sliderMoved(control,'reflections');assert.equal(writes.length,0);
// Empty selection is safe; invalid keys are ignored; leaving multi-edit restores the original single tab.
context.toggleProfile('dock');context.toggleProfile('sidebar');assert.equal(context.targets.length,0);assert.equal(context.commonValue('enable'),null);
context.writeValue('darkening',12);context.resetSelected();context.toggleProfile('unknown');assert.equal(context.targets.length,0);assert.equal(writes.length,0);
context.toggleMultiEdit();assert.deepEqual(Array.from(context.targets),['dock']);
context.writeValue('rim',9);assert.deepEqual(writes,[['dock','rim',9]]);
// Blur ceiling depends on every selected profile; reset retains each profile's own defaults.
context.toggleMultiEdit();context.toggleProfile('sidebar');assert.equal(context.blurLimit,16);
context.toggleProfile('terminal');assert.equal(context.blurLimit,8);context.toggleProfile('terminal');context.toggleProfile('bar');
const unselected=JSON.stringify(profiles.settings);context.resetSelected();
assert.equal(profiles.bar.blur,1);assert.equal(profiles.dock.blur,8);assert.equal(profiles.sidebar.blur,8);
assert.equal(profiles.bar.automaticDarkeningStrength,100);assert.equal(JSON.stringify(profiles.settings),unselected);
'''.replace('FUNCTIONS', json.dumps('\n'.join(functions))).replace('DEFAULTS', json.dumps(defaults)).replace('EXPRESSIONS', json.dumps(expressions)).replace('VISIBILITY', json.dumps(visibility))
with tempfile.TemporaryDirectory(prefix='glassy-multiedit-check-') as directory:
    path = Path(directory) / 'check.js'
    path.write_text(script)
    subprocess.run(['node', str(path)], check=True)
print('Glassy multi-edit: OK (mixed states, no selection writes, per-field edits, drag snapshots, keyboard, slider visibility, retained values, blur limits and per-profile reset; no rendering)')
