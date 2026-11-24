#!/usr/bin/env python3
"""CPU only: python3 tests/glassy-input-check.py [SOURCE_ROOT]."""
from pathlib import Path
import json
import re
import subprocess
import sys

repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
page = (repo / 'modules/ii/settings/pages/GlassyConfig.qml').read_text()
tabs = (repo / 'modules/common/widgets/SecondaryTabBar.qml').read_text()
group = Path(__file__).resolve().parents[1] / 'modules/common/widgets/GroupedList.qml'
assert 'visible: !collapsed' in group.read_text()
assert 'wheelNavigationEnabled: false' in page
assert 'property bool wheelNavigationEnabled: true' in tabs
assert 'WheelHandler {\n            enabled: root.wheelNavigationEnabled' in tabs
assert 'wheelEnabled: false' in page
assert 'MouseArea {' not in page and 'MouseArea {' not in tabs
assert 'onWheel:' not in page
assert 'onClicked: root.toggleProfile(modelData)' in page
assert 'onCurrentIndexChanged: root.selectedTab = currentIndex' in page
collapsed = re.findall(r'readonly property bool groupedListCollapsed: ([^\n]+)\n\s*visible: !groupedListCollapsed', page)
assert len(collapsed) == 4
script = r'''
const assert = require('assert/strict');
for (const value of [true, false, null]) {
    const root = {commonValue: () => value, automaticMode: value};
    const collapsed = EXPRESSIONS.map(expression => eval(expression));
    // Exactly one actual row per group: switch for uniform values, selector for mixed.
    assert.deepEqual(collapsed, value === null ? [true, false, true, false] : [false, true, false, true]);
    assert.equal(root.automaticMode, value);
}
const colors = Object.fromEntries(['colLayer2','colLayer1Hover','colPrimary','colPrimaryHover',
    'colSecondaryContainer','colSurfaceContainer','colSecondaryContainerHover','colOnSurface']
    .map((name,index) => [name,{r:index/10,g:0.2,b:0.3,a:0.25}]));
const Appearance = {colors};
const Qt = {color: value=>value === "transparent" ? {r:0,g:0,b:0,a:0} : value, rgba:(r,g,b,a)=>({r,g,b,a})};
const ColorUtils = {transparentize: TRANSPARENTIZE};
const root = {satinProfileTabs:true};
let checked = false;
const expressions = COLORS;
for (const selected of [false,true]) {
    checked = selected;
    for (const expression of expressions) assert.ok(Qt.color(eval(expression)).a < 1);
}
// Selected, unselected and hover styles use distinct palette entries.
checked = false; const plain = eval(expressions[4]), hover = eval(expressions[5]);
checked = true; const selected = eval(expressions[4]), selectedHover = eval(expressions[5]);
assert.notDeepEqual(plain,hover);assert.notDeepEqual(plain,selected);assert.notDeepEqual(selected,selectedHover);
root.satinProfileTabs = false;
assert.equal(eval(expressions[0]).a,0.25);assert.equal(eval(expressions[4]).a,0);
for (const global of [false,true]) for (const settings of [false,true])
for (const enhanced of [false,true]) for (const frosted of [false,true]) {
    const GlassCompositor={enhancedActive:enhanced,frostedAvailable:frosted};
    const Config={options:{background:{widgets:{glass:{enable:global,elements:{settings:{enable:settings}}}}}}};
    assert.equal(eval(GATE),global && settings && enhanced && frosted);
}
'''.replace('EXPRESSIONS', json.dumps(collapsed))
color_expressions = re.findall(r'^\s*colBackground\w*: (root\.satinProfileTabs[^\n]*(?:\n\s+[?:][^\n]+)*)',page,re.M)
assert len(color_expressions) == 6
assert 'ColorUtils.applyAlpha' not in page
assert page.count('property WindowGlass tabGlass: WindowGlass {') == 2
for marker in ['parent: profileButton.background','parent: profileTab.background']:
    assert marker in page
for marker in ['glassEnabled: root.satinProfileTabs','trackGeometry: false','nativeClip: root',
               'frost: root.satinProfileTabs ? Math.max(8, Config.options.background.widgets.glass.haze) : 0']:
    assert page.count(marker) == 2
utility = (Path(__file__).resolve().parents[1] / 'modules/common/functions/ColorUtils.qml').read_text()
transparentize = re.search(r'function transparentize\(color, percentage = 1\) \{[^}]+\}', utility)[0]
gate = re.search(r'readonly property bool satinProfileTabs: ([^\n]+)\n\s*([^\n]+)\n\s*([^\n]+)',page)
script = script.replace('COLORS',json.dumps(color_expressions)).replace('TRANSPARENTIZE',transparentize).replace('GATE',json.dumps(gate[1]+' '+gate[2]+' '+gate[3]))
subprocess.run(['node', '-e', script], check=True)
print('Glassy input: OK (page scroll routing, click wiring, native satin profile materials, uniform/mixed row collapse; no rendering)')
