"""Run: python3 tests/freeze-recorder-check.py. No network, compositor or kernel changes."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

source = Path(__file__).resolve().parents[1] / 'scripts/glass/record-freeze.py'
with tempfile.TemporaryDirectory(prefix='freeze-record-check-', dir='/tmp') as directory:
    base = Path(directory)
    (base / 'bin').mkdir()
    # Local endpoints exercise the real stream and receiver shell without connecting to a host.
    ssh = base / 'bin/ssh'
    ssh.write_text('#!/usr/bin/python3\nimport os,sys\ncommand=sys.argv[-1].replace(\'$HOME/.local/state/end4-pC\',os.environ[\'END4_RECORDER_CHECK_DIR\'])\nos.execv(\'/bin/sh\',[\'sh\',\'-c\',command])\n')
    ssh.chmod(0o700)
    journal = base / 'bin/journalctl'
    journal.write_text('#!/usr/bin/python3\nimport time\nprint("[1.000] recorder test message",flush=True)\ntime.sleep(20)\n')
    journal.chmod(0o700)
    env = {**os.environ, 'PATH': str(base / 'bin') + os.pathsep + os.environ['PATH'],
           'END4_RECORDER_CHECK_DIR': str(base / 'logs')}
    result = subprocess.run(['python3', str(source), 'xlini@example.invalid', '--seconds', '2'],
                            env=env, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, (result.stdout, result.stderr)
    log = next((base / 'logs').glob('freeze-*.jsonl'))
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert log.stat().st_mode & 0o777 == 0o600
    assert records[0]['kind'] == 'start' and any(r['kind'] == 'end' for r in records)
    samples = [r for r in records if r['kind'] == 'sample']
    assert len(samples) == 2 and all(r['memory_kib']['MemAvailable'] >= 0 and r['uptime_s'] > 0 for r in samples)
    assert all(r['memory_kib']['SwapFree'] <= r['memory_kib']['SwapTotal'] for r in samples)
    assert any(r['kind'] == 'kernel' and 'recorder test message' in r['line'] for r in records)
    ssh.write_text('#!/bin/sh\nexit 255\n')
    failed = subprocess.run(['python3', str(source), 'xlini@example.invalid', '--seconds', '1'],
                            env=env, text=True, capture_output=True, timeout=10)
    assert failed.returncode != 0 and 'did not open its log' in failed.stderr
print('Recorder: private JSON stream, kernel and memory/GPU samples, clean stop and SSH failure passed.')
