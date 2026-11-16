"""Run python3 tests/wallpaper-scheduling-check.py; no real wallpaper, D-Bus or theme changes."""
from pathlib import Path
import json
import os
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('services/Wallpapers.qml', 'utf8');
const detached = [], selections = [];
let changes = 0;
const context = vm.createContext({
    Quickshell: {execDetached: command => detached.push(Array.from(command))},
    Directories: {wallpaperSwitchScriptPath:'/scripts/switchwall.sh'},
    Appearance: {m3colors:{darkmode:true}},
    applyProc: {running:false}, selectProc: {select:(...args)=>selections.push(args)},
    root: {changed:()=>changes++}
});
for (const name of ['apply', 'select']) {
    const fn = source.match(new RegExp('^    function '+name+'\\([^]*?^    \\}', 'm'));
    assert.ok(fn, name);
    vm.runInContext(fn[0], context);
    context.root[name] = context[name];
}
context.apply('/wall one.jpg', false);
assert.deepEqual(detached, [['/scripts/switchwall.sh','--mode','light','--image','/wall one.jpg']]);
context.apply('/wall two.jpg', true, true);
assert.equal(context.applyProc.running, true);
assert.deepEqual(Array.from(context.applyProc.command), ['nice','-n','10','ionice','-c','3','/scripts/switchwall.sh','--mode','dark','--image','/wall two.jpg']);
context.apply('/skip.jpg', true, true);
context.apply('', true, true);
assert.equal(changes, 2, 'Automatic jobs must not overlap or queue');
assert.equal(context.root.confirmedPath, '/wall two.jpg');
context.select('/folder', true, null, true);
assert.deepEqual(selections, [['/folder',true,null,true]], 'Keep directory validation and propagate background priority');
assert.match(source, /root\.apply\(selectProc\.filePath, selectProc\.darkMode, selectProc\.background\)/);
assert.match(source, /root\.select\(filePath, darkMode, null, background\)/);
assert.match(source, /running: root\.automaticConsumers > 0 && Config\.ready && Config\.options\.wallpaperSelector\.changeInterval > 0/);
assert.equal((source.match(/root\.randomFromCurrentFolder\(Appearance\.m3colors\.darkmode, true\)/g)||[]).length, 1);
const background = fs.readFileSync('modules/ii/background/Background.qml','utf8');
assert.match(background, /Component\.onCompleted: Wallpapers\.automaticConsumers\+\+/);
assert.match(background, /Component\.onDestruction: Wallpapers\.automaticConsumers--/);
assert.ok(!background.includes('wallpaperChangeTimer'), 'Do not run one automatic job per monitor');
console.log('PASS: one wallpaper scheduler, manual priority unchanged, automatic CPU/IO priority and no overlapping jobs.');
'''], cwd=repo, check=True)

with tempfile.TemporaryDirectory(prefix='wallpaper-theme-check-') as directory:
    base = Path(directory)
    calls, theme = base/'calls.jsonl', base/'theme'
    theme.write_text('A')
    mock = base/'mock'
    mock.write_text('''#!/usr/bin/python3
import json,os,sys
from pathlib import Path
name=Path(sys.argv[0]).name
state=Path(os.environ['TEST_THEME'])
if name=='kreadconfig6': print(state.read_text());sys.exit(0)
with open(os.environ['TEST_CALLS'],'a') as out: out.write(json.dumps([name,*sys.argv[1:]])+'\\n')
if name=='kwriteconfig6':
 if os.environ.get('FAIL_QT_WRITE'): sys.exit(7)
 state.write_text(sys.argv[-1])
''')
    mock.chmod(0o755)
    for name in ('kreadconfig6','kwriteconfig6','gsettings','dbus-send'):
        (base/name).symlink_to(mock)
    env = {**os.environ,'PATH':str(base)+':'+os.environ['PATH'], 'TEST_CALLS':str(calls), 'TEST_THEME':str(theme)}
    def apply(value, fail=False):
        calls.write_text('')
        result = subprocess.run(['bash',str(repo/'scripts/system-appearance.sh'),'--set-icons',value], env={**env,**({'FAIL_QT_WRITE':'1'} if fail else {})})
        return result.returncode, [json.loads(line)[0] for line in calls.read_text().splitlines()]
    assert apply('A') == (0,['gsettings']), 'Unchanged Qt icons must not trigger an application-wide reload'
    assert apply('B') == (0,['kwriteconfig6','dbus-send','gsettings'])
    assert apply('B') == (0,['gsettings'])
    assert apply('C',fail=True) == (7,['kwriteconfig6']), 'Failed writes must not emit a success notification'
print('PASS: unchanged icon theme avoids Qt reload, real changes still notify, failed writes propagate.')

# Reapplying an identical editor accent must not rewrite JSONC or wake editor watchers.
with tempfile.TemporaryDirectory(prefix='wallpaper-editor-check-') as directory:
    base = Path(directory)
    state, config = base/'state', base/'config'
    color = state/'quickshell/user/generated/color.txt'
    color.parent.mkdir(parents=True)
    settings = config/'Code/User/settings.json'
    settings.parent.mkdir(parents=True)
    settings.write_text('{\n  // Keep user comments\n  "material-code.primaryColor": "#112233"\n}\n')
    env = {**os.environ,'XDG_STATE_HOME':str(state),'XDG_CONFIG_HOME':str(config)}
    def update_editor(value):
        color.write_text(value)
        return subprocess.run(['bash',str(repo/'scripts/colors/code/material-code-set-color.sh')],env=env,check=False).returncode
    def stamp():
        data=settings.stat()
        return data.st_ino,data.st_mtime_ns,settings.read_text()
    before=stamp()
    assert update_editor('#112233') == 0 and stamp() == before
    assert update_editor('#445566') == 0
    assert '"material-code.primaryColor": "#445566"' in settings.read_text()
    assert '// Keep user comments' in settings.read_text()
    before=stamp()
    assert update_editor('#445566') == 0 and stamp() == before
    assert update_editor('invalid') != 0 and stamp() == before
    settings.write_text('{\n "other": true\n}\n')
    assert update_editor('#abcdef') == 0
    assert json.loads(settings.read_text())['material-code.primaryColor'] == '#abcdef'
print('PASS: identical editor colours leave JSONC/inode/mtime unchanged; changed colours update, invalid input is rejected.')
