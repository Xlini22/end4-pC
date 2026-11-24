"""Run python3 tests/hyprland-live-colors-check.py; Lua and IPC are mocked, no rendering."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import tempfile

repo=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('live_colors',repo/'scripts/colors/hyprland-colors.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source='''hl.config({general={col={active_border="base-a",inactive_border="base-i"}},misc={background_color="dark"}})
hl.window_rule({name="end4-pC-pinned-colours",match={pin=1},border_color="pin"})
-- ]=] ]] quoting test
'''
mock='''local opts={general={col={active_border="custom-a",inactive_border="custom-i"}}}; local rules={}
hl={config=function(t)
 for k,v in pairs(t) do
  if k=="general" then for key,value in pairs(v.col or {}) do opts.general.col[key]=value end
  else opts[k]=v end
 end
end,window_rule=function(r) assert(r.name);rules[r.name]=r end}
'''
with tempfile.TemporaryDirectory(prefix='live-colors-check-') as d:
    root=Path(d)
    for custom in (False,True):
        code=mock+'\n'+m.command(source,custom)+'\n'+m.command(source,custom)
        code+='\nassert(opts.general.col.active_border=='+m.lua_string('custom-a' if custom else 'base-a')+')'
        code+='\nassert(opts.misc.background_color=="dark"); local count=0;for _ in pairs(rules)do count=count+1 end;assert(count==1)'
        subprocess.run(['lua','-'],input=code,text=True,check=True)
    borders=['rgba(11223344)','rgba(aabbccdd)']
    code=mock+'\n'+m.command(source,True,borders)+'\nassert(opts.general.col.active_border=="rgba(11223344)")'
    subprocess.run(['lua','-'],input=code,text=True,check=True)
    for bad in [['rgba(11)'],['rgba(11223344)','bad'],['rgba(11223344);os.exit(0)','rgba(00000000)']]:
        try:m.command(source,True,bad)
        except ValueError:pass
        else:raise AssertionError('Unvalidated border colour')
    state=root/'state';config=root/'config';mock_bin=root/'bin';mock_bin.mkdir()
    (config/'illogical-impulse').mkdir(parents=True)
    (config/'illogical-impulse/config.json').write_text(json.dumps({'hyprland':{'general':{'borderColor':{'enable':True}}}}))
    capture=root/'calls.json'
    executable=mock_bin/'hyprctl';executable.write_text('''#!/usr/bin/python3
import json,os,sys
from pathlib import Path
Path(os.environ['TEST_CAPTURE']).write_text(json.dumps(sys.argv[1:]))
print(os.environ.get('TEST_REPLY','ok'))
''');executable.chmod(0o755)
    env={**os.environ,'XDG_CONFIG_HOME':str(config),'XDG_STATE_HOME':str(state),'TEST_CAPTURE':str(capture),'PATH':str(mock_bin)+':'+os.environ['PATH']}
    script=repo/'scripts/colors/hyprland-colors.py'
    subprocess.run(['python3',str(script)],env=env,check=True)
    assert not capture.exists(),'Uninstalled migration must not call Hyprland'
    cache=state/'quickshell/user/generated/hyprland-colors.lua';cache.parent.mkdir(parents=True);cache.write_text(source)
    subprocess.run(['python3',str(script),'--borders',*borders],env=env,check=True)
    args=json.loads(capture.read_text());assert args[0]=='eval' and len(args)==2
    subprocess.run(['lua','-'],input=mock+'\n'+args[1],text=True,check=True)
    # Disabling the override must work before the delayed QML JSON write finishes.
    subprocess.run(['python3',str(script),'--borders'],env=env,check=True)
    args=json.loads(capture.read_text())
    subprocess.run(['lua','-'],input=mock+'\n'+args[1]+'\nassert(opts.general.col.active_border=="base-a")',text=True,check=True)
    failed=subprocess.run(['python3',str(script)],env={**env,'TEST_REPLY':'error: Lua failed'},capture_output=True,text=True)
    assert failed.returncode!=0 and 'Lua failed' in failed.stderr
    # The candidate startup loader reads the cache without requiring/dofiling it.
    subprocess.run(['lua','-'],input=mock+'\n'+m.STARTUP_LOADER+'\nassert(rules["end4-pC-pinned-colours"])',text=True,env=env,check=True)
print('PASS: Lua colours, custom borders, named rules, safe quoting, startup persistence, no-op before migration and IPC failures; no rendering.')

# Migration checks and rollback operate only on temporary files.
import hashlib
import shutil
with tempfile.TemporaryDirectory(prefix='live-colors-migration-') as d:
    root=Path(d);stage=root/'stage';stage.mkdir()
    installer=repo/'diagnostics/wallpaper-performance-20261124/no-reload-candidate/install.py'
    shutil.copyfile(installer,stage/'install.py')
    target=root/'target';target.write_text('old');target.chmod(0o600)
    (stage/'candidate').write_text('new')
    row={'target':str(target),'candidate':'candidate','beforeSha256':hashlib.sha256(b'old').hexdigest()}
    (stage/'plan.json').write_text(json.dumps([row]))
    subprocess.run(['python3',str(stage/'install.py')],capture_output=True,check=True)
    assert target.read_text()=='old'
    subprocess.run(['python3',str(stage/'install.py'),'--apply'],capture_output=True,check=True)
    assert target.read_text()=='new' and target.stat().st_mode&0o777==0o600
    # Stale plans refuse all writes.
    result=subprocess.run(['python3',str(stage/'install.py'),'--apply'],capture_output=True)
    assert result.returncode!=0 and target.read_text()=='new'
    target.write_text('old')
    invalid=root/'not-a-directory';invalid.write_text('file')
    second={'target':str(invalid/'child'),'candidate':'candidate','beforeSha256':None}
    (stage/'plan.json').write_text(json.dumps([row,second]))
    result=subprocess.run(['python3',str(stage/'install.py'),'--apply'],capture_output=True)
    assert result.returncode!=0 and target.read_text()=='old','Earlier changes must roll back on failure'
print('PASS: migration dry-run, stale-plan protection, permissions and rollback on write failure.')
