"""Run: python3 tests/freeze-recorder-check.py. No network, compositor or kernel changes."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import signal
import time
import tempfile
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / 'scripts/glass/record-freeze.py'
spec = importlib.util.spec_from_file_location('recorder', source)
recorder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recorder)
own = recorder.process_sample(Path('/proc') / str(os.getpid()))
assert own['pid'] == os.getpid() and own['cpu_ticks'] >= 0 and own['start_ticks'] > 0
assert own['rss_bytes'] > 0 and own['threads'] >= 1 and own['state'] in 'RSDZTtWXxKPI'
assert recorder.process_sample(Path('/proc/0')) is None
with tempfile.TemporaryDirectory(prefix='freeze-record-check-', dir='/tmp') as directory:
    base = Path(directory)
    runtime = base / 'runtime'
    instance = runtime / 'hypr/test-instance'
    instance.mkdir(parents=True)
    hyprlog = instance / 'hyprland.log'
    hyprlog.write_bytes(b'initial\n')
    previous_runtime = os.environ.get('XDG_RUNTIME_DIR')
    previous_roots = {key: os.environ.get(key) for key in ('XDG_STATE_HOME','XDG_DATA_HOME')}
    os.environ['XDG_RUNTIME_DIR'] = str(runtime)
    os.environ['XDG_STATE_HOME'] = str(base/'state')
    os.environ['XDG_DATA_HOME'] = str(base/'data')
    try:
        positions = {}
        first = recorder.hyprland_log_updates(positions)
        assert len(first) == 1 and first[0]['text'] == 'initial\n' and first[0]['offset'] == 0
        assert recorder.hyprland_log_updates(positions) == []
        with hyprlog.open('ab') as stream:
            stream.write(b'crash\xff\n')
        update = recorder.hyprland_log_updates(positions)[0]
        assert update['offset'] == 8 and update['text'] == 'crash\ufffd\n'
        hyprlog.write_bytes(b'new\n')
        assert recorder.hyprland_log_updates(positions)[0]['text'] == 'new\n'
        replacement = instance / 'replacement'
        replacement.write_bytes(b'x' * 70000)
        replacement.replace(hyprlog)
        update = recorder.hyprland_log_updates(positions)[0]
        assert update['offset'] == 70000 - 65536 and len(update['text']) == 65536
        hyprlog.unlink()
        assert recorder.hyprland_log_updates(positions) == [] and positions == {}
        hyprlog.write_text('CRASH CHECK\n')
        sddm = base/'data/sddm/wayland-session.log'
        sddm.parent.mkdir(parents=True)
        sddm.write_text('SESSION STDERR\n')
        fixture = base/'state/end4-pC/diagnostics/20261114-frame-pipeline/stage-profile/runs/123/0-fixture.log'
        fixture.parent.mkdir(parents=True)
        fixture.write_text('TEST FIXTURE\n')
        updates=recorder.hyprland_log_updates(positions)
        assert any(r['kind']=='session-log' and r['text']=='SESSION STDERR\n' for r in updates)
        assert any(r['kind']=='session-log' and r['text']=='TEST FIXTURE\n' for r in updates)
    finally:
        for key,value in previous_roots.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
        if previous_runtime is None:
            del os.environ['XDG_RUNTIME_DIR']
        else:
            os.environ['XDG_RUNTIME_DIR'] = previous_runtime
    (base / 'bin').mkdir()
    # Local endpoints exercise the real stream and receiver shell without connecting to a host.
    ssh = base / 'bin/ssh'
    ssh.write_text('#!/usr/bin/python3\nimport os,sys\ncommand=sys.argv[-1].replace(\'$HOME/.local/state/end4-pC\',os.environ[\'END4_RECORDER_CHECK_DIR\'])\nos.execv(\'/bin/sh\',[\'sh\',\'-c\',command])\n')
    ssh.chmod(0o700)
    journal = base / 'bin/journalctl'
    journal.write_text('#!/usr/bin/python3\nimport time,sys,json\nprint(json.dumps({"MESSAGE":"session test message","_COMM":"Hyprland","_PID":"123"}) if "--output=json" in sys.argv else "[1.000] recorder test message",flush=True)\nif "--follow" in sys.argv:time.sleep(20)\n')
    journal.chmod(0o700)
    loginctl = base / 'bin/loginctl'
    loginctl.write_text('#!/usr/bin/python3\nimport json,os,sys\nprint(json.dumps([{"session":"2","uid":os.getuid(),"tty":"tty1"}]) if "list-sessions" in sys.argv else "Id=2\\nType=wayland\\nVTNr=1\\nActive=yes")\n')
    loginctl.chmod(0o700)
    env = {**os.environ, 'PATH': str(base / 'bin') + os.pathsep + os.environ['PATH'],
           'END4_RECORDER_CHECK_DIR': str(base / 'logs'), 'XDG_RUNTIME_DIR': str(runtime),
           'XDG_STATE_HOME': str(base/'state'),'XDG_DATA_HOME':str(base/'data')}
    result = subprocess.run(['python3', str(source), 'xlini@example.invalid', '--seconds', '2'],
                            env=env, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, (result.stdout, result.stderr)
    log = next((base / 'logs').glob('freeze-*.jsonl'))
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert log.stat().st_mode & 0o777 == 0o600
    assert records[0]['kind'] == 'receiver-start' and any(r['kind'] == 'end' for r in records)
    start = next(r for r in records if r['kind'] == 'start')
    assert start['clock_ticks_per_second'] == os.sysconf('SC_CLK_TCK')
    assert start['version'] == 2 and start['performance']
    assert any(r['kind'] == 'receiver-heartbeat' for r in records)
    assert records[-1]['kind'] == 'receiver-end' and records[-1]['sender_end_seen']
    sender = [r for r in records if 'seq' in r]
    assert [r['seq'] for r in sender] == list(range(1,len(sender)+1))
    assert all('received_utc' in r and r['receiver_monotonic_s'] > 0 for r in sender)
    samples = [r for r in records if r['kind'] == 'sample']
    assert len(samples) == 2 and all(r['memory_kib']['MemAvailable'] >= 0 and r['uptime_s'] > 0 for r in samples)
    assert all(r['memory_kib']['SwapFree'] <= r['memory_kib']['SwapTotal'] for r in samples)
    assert all(isinstance(r['processes'], list) for r in samples)
    assert any(r['kind'] == 'kernel' and 'recorder test message' in r['line'] for r in records)
    assert any(r['kind'] == 'hyprland-log' and r['text'] == 'CRASH CHECK\n' for r in records)
    assert any(r['kind'] == 'session-journal' and r['MESSAGE'] == 'session test message' for r in records)
    assert any(r['kind'] == 'sessions' and r['details'][0]['VTNr'] == '1' for r in records)
    assert any(r['kind']=='previous-boot-kernel' and 'session test message' in r['journal_jsonl'] for r in records)
    # Receiver heartbeats must continue even when the PC stops sending samples.
    receiver_log = base/'receiver-alone.jsonl'
    receiver = subprocess.Popen(['python3','-u','-c',recorder.RECEIVER,str(receiver_log)],
                                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert receiver.stdout.readline().startswith('READY ')
        receiver.stdin.write('{"kind":"sample","seq":1}\n');receiver.stdin.flush()
        for _ in range(100):
            rows = [json.loads(line) for line in receiver_log.read_text().splitlines()]
            if any(r['kind']=='receiver-heartbeat' and (r['last_sample_age_s'] or 0) >= 1 for r in rows):break
            time.sleep(.03)
        else:raise AssertionError('Receiver heartbeat stopped when the sender went silent')
        receiver.stdin.write('partial');receiver.stdin.close();receiver.stdin=None
        stdout,stderr=receiver.communicate(timeout=3)
        assert receiver.returncode==0,(stdout,stderr)
        rows=[json.loads(line) for line in receiver_log.read_text().splitlines()]
        assert rows[-1]['kind']=='receiver-end' and not rows[-1]['sender_end_seen'] and rows[-1]['partial_bytes']==7
    finally:
        if receiver.poll() is None:receiver.kill();receiver.wait()
    before=receiver_log.read_bytes()
    duplicate=subprocess.run(['python3','-u','-c',recorder.RECEIVER,str(receiver_log)],input='',text=True,capture_output=True)
    assert duplicate.returncode!=0 and receiver_log.read_bytes()==before
    with patch.object(recorder.subprocess,'check_output',side_effect=subprocess.TimeoutExpired('loginctl',1)):
        assert 'error' in recorder.session_snapshot(), 'Unresponsive logind must not stop collection'
    # One DRM client may have multiple descriptors; different devices may reuse client IDs.
    drm = base / 'drm/fdinfo'
    drm.mkdir(parents=True)
    (drm.parent/'fd').mkdir()
    for name, device, client, count in [('1','A','2',100),('2','A','2',100),('3','A','3',200),('4','B','2',300)]:
        (drm.parent/'fd'/name).symlink_to('/dev/dri/renderD128')
        (drm/name).write_text(f'drm-pdev: {device}\ndrm-client-id: {client}\ndrm-engine-gfx: {count} ns\n')
    assert recorder.gpu_engines(drm.parent) == {'gfx': 600}
    assert recorder.gpu_engines(base/'missing') == {}
    real_sample = recorder.process_sample
    fake = {**own, 'cpu_ticks': 200, 'start_ticks': 50, 'name': 'qs'}
    try:
        recorder.process_sample = lambda path, **kwargs: dict(fake) if path.name == str(os.getpid()) else None
        previous = {'time': time.monotonic()-1, 'processes': {os.getpid():(50,180)}}
        _, top = recorder.process_samples(previous)
        assert len(top) == 1 and abs(top[0]['cpu_percent'] - 20/os.sysconf('SC_CLK_TCK')*100) < 1
        previous = {'time': time.monotonic()-1, 'processes': {os.getpid():(49,1)}}
        _, top = recorder.process_samples(previous)
        assert top[0]['cpu_percent'] == 0, 'PID reuse must not create a false CPU spike'
        previous = {'time':time.monotonic()-1, 'processes':{os.getpid():(50,180,time.monotonic()-5)}}
        _, top = recorder.process_samples(previous)
        assert abs(top[0]['cpu_percent'] - 4/os.sysconf('SC_CLK_TCK')*100) < 1, 'A discovery scan must use the per-process interval'
        assert top[0]['cpu_interval_s'] >= 4.9
    finally:
        recorder.process_sample = real_sample
    config = base / 'config/illogical-impulse/config.json'
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({'background': {'wallpaperPath':'/test/light.jpg','widgets':{'glass':{'enable':True}}}}))
    local_env = {**env, 'XDG_CONFIG_HOME': str(base/'config')}
    local_log = base / 'local.jsonl'
    local = subprocess.run(['python3',str(source),'--local',str(local_log),'--seconds','2'],
                           env=local_env,text=True,capture_output=True,timeout=10)
    assert local.returncode == 0, (local.stdout,local.stderr)
    rows = [json.loads(line) for line in local_log.read_text().splitlines()]
    assert local_log.stat().st_mode & 0o777 == 0o600
    assert rows[0]['performance'] and any(row['kind']=='end' for row in rows)
    assert any(row['kind']=='context' and row['wallpaper']=='/test/light.jpg' for row in rows)
    samples = [row for row in rows if row['kind']=='sample']
    assert len(samples)==2 and all(row['sampling_ms']>=0 and isinstance(row['top_processes'],list) for row in samples)
    before = local_log.read_bytes()
    repeated = subprocess.run(['python3',str(source),'--local',str(local_log),'--seconds','1'],
                              env=local_env,text=True,capture_output=True,timeout=10)
    assert repeated.returncode != 0 and local_log.read_bytes()==before, 'Never overwrite an existing recording'
    interrupted_log = base/'interrupted.jsonl'
    process = subprocess.Popen(['python3',str(source),'--local',str(interrupted_log),'--seconds','30'],
                               env=local_env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        for _ in range(100):
            if interrupted_log.exists() and '"kind": "sample"' in interrupted_log.read_text(): break
            time.sleep(.03)
        else: raise AssertionError('Local recorder did not start')
        process.send_signal(signal.SIGINT)
        stdout,stderr=process.communicate(timeout=8)
        assert process.returncode==0,(stdout,stderr)
        assert any(json.loads(line).get('reason')=='interrupted' for line in interrupted_log.read_text().splitlines())
    finally:
        if process.poll() is None: process.kill();process.wait()
    ssh.write_text('#!/bin/sh\nexit 255\n')
    failed = subprocess.run(['python3', str(source), 'xlini@example.invalid', '--seconds', '1'],
                            env=env, text=True, capture_output=True, timeout=10)
    assert failed.returncode != 0 and 'did not open its log' in failed.stderr
print('Recorder: SSH/local streams, independent receiver heartbeat, receive timestamps, sequence, partial EOF, no overwrite, session/kernel logs, session timeout, DRM counters, PID reuse and clean interrupt passed.')
