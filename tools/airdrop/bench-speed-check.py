"""Check benchmark command arguments and cleanup without touching the radio."""
from pathlib import Path
import json, os, subprocess, tempfile

script = Path(__file__).with_name('bench-speed.sh')
with tempfile.TemporaryDirectory(prefix='airdrop speed check ') as directory:
    base = Path(directory)
    script_copy = base / script.name
    script_copy.write_bytes(script.read_bytes())
    (base / 'benchmarks').mkdir()
    (base / 'benchmarks' / 'device-name').write_text('Saved iPhone\n')
    (base / 'airdrop-speed-8MiB.zip').write_bytes(b'test')
    stub = base / 'omdrop'
    stub.write_text('''#!/usr/bin/python3
import os,sys,json
from pathlib import Path
base=Path(os.environ['OMDROP_BENCH_DIR'])
with (base/'calls.jsonl').open('a') as log: log.write(json.dumps(sys.argv[1:])+'\\n')
cmd=sys.argv[1]
mask=os.umask(0)
os.umask(mask)
assert mask & 0o044 == 0, 'Owly status files would be unreadable by the desktop'
if cmd=='status':
    started=(base/'started').exists()
    counter=base/'polls'
    count=int(counter.read_text())+1 if counter.exists() else 1
    if started: counter.write_text(str(count))
    print(json.dumps({'receiving':started or os.environ['BENCH_CASE']=='busy',
                      'visible':started and (os.environ['BENCH_CASE']!='delayed' or count>1)}))
if cmd=='on':
    if os.environ['BENCH_CASE']=='failed-start': sys.exit(2)
    (base/'started').touch()
if cmd=='off': (base/'route-added').unlink(missing_ok=True)
if cmd=='send':
    assert (base/'started').exists()
    if os.environ['BENCH_CASE']=='delayed': assert int((base/'polls').read_text())>1
    import time
    time.sleep(2 if os.environ['BENCH_CASE']=='deadline' else 0.2)
''')
    stub.chmod(0o755)
    for name, text in {
        'nmcli': '#!/bin/sh\nif [ "$1" = -g ]; then echo 12345678-1234-1234-1234-123456789abc; fi\n',
        'journalctl': '#!/bin/sh\nexit 0\n',
        'sudo': '''#!/usr/bin/python3
import os,sys,json
from pathlib import Path
base=Path(os.environ['OMDROP_BENCH_DIR'])
with (base/'route-calls.jsonl').open('a') as log: log.write(json.dumps(sys.argv[1:])+'\\n')
if sys.argv[1:]==['-v']: sys.exit(0)
assert sys.argv[1:5]==['-n','/usr/bin/ip','-6','route']
action=sys.argv[5]
assert sys.argv[6:]==(['fe80::/64','dev','awdl0','metric','1','rto_min','1000ms'] if action=='add' else ['fe80::/64','dev','awdl0','metric','1'])
if action=='add':
    if os.environ['BENCH_CASE']=='rto-add-failed': sys.exit(2)
    (base/'route-added').touch()
elif action=='delete': (base/'route-added').unlink()
else: raise AssertionError(action)
''',
        'ip': '''#!/usr/bin/python3
import os,sys,json
from pathlib import Path
if sys.argv[1:]==['-details','link','show']:
    print('synthetic links'); sys.exit(0)
if sys.argv[1:]==['-ts','monitor','link']:
    import time
    (Path(os.environ['OMDROP_BENCH_DIR'])/'link-monitor-pid').write_text(str(os.getpid()))
    print('synthetic link event', flush=True)
    time.sleep(60); sys.exit(0)
assert sys.argv[1:]==['-j','-6','route','show','dev','awdl0']
base=Path(os.environ['OMDROP_BENCH_DIR'])
routes=[{'dst':'fe80::/64','protocol':'kernel','metric':256}]
if (base/'route-added').exists() and os.environ['BENCH_CASE']!='rto-readback-failed':
    routes.insert(0,{'dst':'fe80::/64','metric':1,'metrics':[{'rto_min':1000}]})
print(json.dumps(routes))
''',
        'ss': '''#!/usr/bin/python3
import os,sys
from pathlib import Path
if '-tin' in sys.argv:
    (Path(os.environ['OMDROP_BENCH_DIR'])/'sampler-pid').write_text(str(os.getppid()))
    print('ESTAB 0 0 [fe80::1]:12345 [fe80::2]:8770')
    print(' cubic rto:250 rtt:12/2 mss:1440 cwnd:3 retrans:0/2 bytes_acked:1024')
else: print('LISTEN')
''',
    }.items():
        p = base / name
        p.write_text(text)
        p.chmod(0o755)
    recipient = 'iPhone "test" $(false); literal'
    for case in ('success', 'saved', 'fixed-wifi', 'tcp', 'delayed', 'deadline', 'failed-start', 'busy', 'rto', 'rto-add-failed', 'rto-readback-failed'):
        log = base / 'calls.jsonl'
        log.unlink(missing_ok=True)
        (base / 'started').unlink(missing_ok=True)
        (base / 'polls').unlink(missing_ok=True)
        (base / 'sampler-pid').unlink(missing_ok=True)
        (base / 'link-monitor-pid').unlink(missing_ok=True)
        (base / 'route-calls.jsonl').unlink(missing_ok=True)
        (base / 'route-added').unlink(missing_ok=True)
        old_runs = set(base.glob('run-*'))
        env = {**os.environ, 'PATH': str(base) + os.pathsep + os.environ['PATH'],
               'OMDROP_CLI': str(stub), 'OMDROP_BENCH_DIR': str(base), 'BENCH_CASE': case,
               'OMDROP_BENCH_SEND_TIMEOUT': '0.5' if case == 'deadline' else '240',
               'OMDROP_BENCH_FIXED_WIFI': '1' if case == 'fixed-wifi' else '0',
               'OMDROP_BENCH_NO_PAUSE': '1' if case == 'fixed-wifi' else '0',
               'OMDROP_BENCH_RTO_MIN': '1000' if case.startswith('rto') else '0'}
        command = ['bash', '-c', 'umask 077; exec bash "$@"', 'bench-check', str(script_copy)]
        if case == 'tcp': command.append('--tcp')
        result = subprocess.run(command, env=env, input=('' if case == 'saved' else recipient)+'\n\n\n\n\n',
                                capture_output=True, text=True, timeout=10)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        expected_result = 124 if case == 'deadline' else (1 if case in ('failed-start', 'busy', 'rto-add-failed', 'rto-readback-failed') else 0)
        assert result.returncode == expected_result, result.stdout + result.stderr
        if case == 'deadline': assert 'Tempo massimo raggiunto' in result.stdout
        if case == 'fixed-wifi':
            assert 'Riconnetto il PC alla rete Wi-Fi' in result.stdout
            assert 'Ora puoi riattivare Hotspot' not in result.stdout
        assert [c for c in calls if c[0]=='off'] == ([] if case=='busy' else [['off','--force']]), calls
        if (base / 'link-monitor-pid').exists():
            try: os.kill(int((base / 'link-monitor-pid').read_text()), 0)
            except ProcessLookupError: pass
            else: raise AssertionError('Link monitor was left running')
        if case in ('success', 'saved', 'fixed-wifi', 'tcp', 'delayed', 'deadline', 'rto'):
            expected_recipient = 'Saved iPhone' if case == 'saved' else recipient
            assert [c for c in calls if c[0]=='send'] == [['send','--verbose','--wait','60','--to',expected_recipient,'--',str(base/'airdrop-speed-8MiB.zip')]], calls
            run, = set(base.glob('run-*')) - old_runs
            assert 'SAMPLE ' in (run/'tcp.log').read_text()
            assert 'retrans:0/2' in (run/'tcp.log').read_text()
            pid = int((base/'sampler-pid').read_text())
            try: os.kill(pid, 0)
            except ProcessLookupError: pass
            else: raise AssertionError('TCP sampler was left running')
            assert ('Ora su iPhone apri File' in result.stdout) == (case not in ('tcp', 'deadline'))
        else:
            assert not any(c[0]=='send' for c in calls), calls
        if case.startswith('rto'):
            root_calls=[json.loads(x) for x in (base/'route-calls.jsonl').read_text().splitlines()]
            assert sum('delete' in c for c in root_calls) == (0 if case=='rto-add-failed' else 1)
            assert not (base/'route-added').exists()
            if case=='rto':
                assert json.loads((run/'rto-restored.json').read_text()) == json.loads((run/'rto-before.json').read_text())
    assert all(p.stat().st_mode & 0o077 == 0 for p in base.glob('run-*'))
    log.unlink(missing_ok=True)
    test_file = base / 'airdrop-speed-8MiB.zip'
    real_file = base / 'original.zip'
    test_file.rename(real_file)
    test_file.symlink_to(real_file)
    result = subprocess.run(command, env=env, input='\n', capture_output=True, text=True, timeout=5)
    assert result.returncode == 1 and 'file reale' in result.stderr
    assert not log.exists(), 'A symlink must be rejected before calling the radio CLI'
print('Benchmark readiness, TCP sampling, RTO route apply/readback/cleanup, deadline, literal arguments and busy guard passed; no live radio used')
