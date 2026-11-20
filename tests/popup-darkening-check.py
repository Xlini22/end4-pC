#!/usr/bin/env python3
"""CPU-only regression: hover popups inherit darkening, not bar optics."""
from pathlib import Path
import subprocess

root = Path(__file__).parents[1]
widget = (root / 'modules/common/widgets/WindowGlass.qml').read_text()
start = widget.index('readonly property var darkeningProfile: GlassProfiles.profile(')
end = widget.index('\n    readonly property', start + 1)
expression = widget[start:end].split('GlassProfiles.profile(', 1)[1].strip()[:-1]
assert 'opticalProfile: root.opticalProfile' in widget
assert 'darkening: root.darkeningProfile?.enable' in widget
assert 'automaticDarkening: root.darkeningProfile?.enable' in widget
subprocess.run(['node', '-e', '''
const assert = require('node:assert/strict');
const key = new Function('win', 'profileKey', 'return ' + process.argv[1]);
for (const ns of ['quickshell:popup', 'quickshell:popupMorph'])
    assert.equal(key({WlrLayershell: {namespace: ns}}, ''), 'bar');
for (const name of ['bar','dock','settings','sidebar','lockscreen',''])
    assert.equal(key({WlrLayershell: {namespace: 'other'}}, name), name);
assert.equal(key(null, ''), '');
''', expression], check=True)
patch = (root / 'patches/native-glass-popup-darkening.patch').read_text()
added = [line for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++')]
assert len(added) == 1
assert 'glassDarkeningOptics' in added[0] and 'glassProfileKey' in added[0]
for namespace in ['quickshell:popup', 'quickshell:popupMorph']:
    assert namespace in added[0]
# The native shader already broadcasts one luminance when a shared reference is set.
bands = (root / 'patches/native-glass-popup-bands.patch').read_text()
assert 'maskInfo.darkeningReference = {0, 0, 1, 1};' in bands
for namespace in ['quickshell:popup', 'quickshell:popupMorph']:
    assert bands.count('"' + namespace + '"') == 2
print('popup darkening: OK (manual/automatic routing, shared luminance, optics preserved)')
