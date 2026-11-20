#!/usr/bin/env python3
"""Check the actual toggle logic without creating a Wayland/GPU surface."""
from pathlib import Path
import re
import subprocess

source = (Path(__file__).parents[1] / 'services/Idle.qml').read_text()
assert 'inhibit: Persistent.states.idle.inhibit' in source
assert not re.search(r'root\.inhibit\s*=', source), 'Do not break the persistent binding'
toggle = re.search(r'function toggleInhibit\(active = null\)\s*\{([^}]+)\}', source).group(1)
subprocess.run(['node', '-e', '''
const assert = require('node:assert/strict');
let Persistent = {states: {idle: {inhibit: false}}};
const root = {get inhibit() {return Persistent.states.idle.inhibit;}};
const toggle = new Function('Persistent', 'root', 'active', process.argv[1]);
function set(active = null) {toggle(Persistent, root, active);}
// Loaded before or after the Idle singleton: both must restore the saved value.
Persistent.states = JSON.parse('{"idle":{"inhibit":true}}');
assert.equal(root.inhibit, true);
set(); assert.equal(root.inhibit, false);
set(true); assert.equal(root.inhibit, true);
Persistent.states = JSON.parse(JSON.stringify(Persistent.states));
assert.equal(root.inhibit, true);
set(false); assert.equal(root.inhibit, false);
set(false); assert.equal(root.inhibit, false);
set(); assert.equal(root.inhibit, true);
''', toggle], check=True)
print('idle persistence: OK')
