"""Exercise ACK/A-MSDU changes and rollback using temporary files and mocks."""
from pathlib import Path
from unittest.mock import patch
import importlib.util
import itertools
import json
import shutil
import subprocess
import tempfile
import tomllib

spec = importlib.util.spec_from_file_location('bench_ack', Path(__file__).with_name('bench-ack.py'))
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
original = b'[drivers.ath10k_pci]\nstatus="untested"\nmode="exclusive"\nchannels=[6]\nnotes="keep this note"\n\n[drivers.other]\nstatus="tested"\n'
proposed = bench.candidate(original)
parsed = tomllib.loads(proposed.decode())
assert parsed['drivers']['ath10k_pci'].pop('tx_noack') is False
assert parsed == tomllib.loads(original.decode())
try:
    bench.candidate(proposed)
except ValueError:
    pass
else:
    raise AssertionError('Existing override must be reviewed, not overwritten')
radio_original = b'channels=[6]\ncountry="IT"\n# preserve this\n'
radio_proposed = bench.candidate(radio_original, amsdu=True)
parsed = tomllib.loads(radio_proposed.decode())
assert parsed.pop('tx_amsdu') is True and parsed == tomllib.loads(radio_original.decode())
try:
    bench.candidate(radio_proposed, amsdu=True)
except ValueError:
    pass
else:
    raise AssertionError('Existing A-MSDU override must not be overwritten')

with tempfile.TemporaryDirectory(prefix='ACK check with spaces ') as directory:
    root = Path(directory)
    bench.PROFILE = root / 'drivers.toml'
    bench.RADIO = root / 'radio.toml'
    bench.BACKUPS = root / 'backups'
    for amsdu, case in itertools.product((False, True), ('success', 'failed-benchmark', 'interrupted', 'failed-restart', 'external-edit', 'busy')):
        bench.PROFILE.write_bytes(original)
        bench.RADIO.write_bytes(radio_original)
        target = bench.RADIO if amsdu else bench.PROFILE
        target_before, target_after = (radio_original, radio_proposed) if amsdu else (original, proposed)
        events = []
        def output(command, **kwargs):
            if command[0] == bench.CLI:
                return json.dumps({'receiving':case=='busy','visible':False})
            assert command[0] == 'busctl'
            return 's "idle"\n'
        def run(command, **kwargs):
            events.append(command)
            if command[:2] == ['sudo', 'install']:
                shutil.copyfile(command[-2], command[-1])
            elif command[:2] == ['sudo', 'mv']:
                Path(command[-2]).replace(command[-1])
            elif command == ['sudo','systemctl','restart','owlyd.service'] and case=='failed-restart':
                if events.count(command)==1:
                    raise subprocess.CalledProcessError(1,command)
            return subprocess.CompletedProcess(command,0)
        class Child:
            def __init__(self, command, env):
                assert command == ['bash',str(bench.BENCH),'--tcp']
                assert env['OMDROP_BENCH_VARIANT'] == ('tx_amsdu=true' if amsdu else 'tx_noack=false')
                assert target.read_bytes() == target_after
            def poll(self): return 0
            def wait(self):
                if case=='interrupted': raise KeyboardInterrupt
                if case=='external-edit': target.write_bytes(target_before+b'# external edit\n')
                return 4 if case=='failed-benchmark' else 0
        with patch.object(bench.subprocess,'check_output',output), patch.object(bench.subprocess,'run',run), patch.object(bench.subprocess,'Popen',Child), patch('builtins.input',return_value=''):
            try:
                result=bench.main(amsdu=amsdu)
                assert case in ('success','failed-benchmark')
                assert result == (4 if case=='failed-benchmark' else 0)
            except (KeyboardInterrupt,subprocess.CalledProcessError,RuntimeError):
                assert case not in ('success','failed-benchmark')
        assert target.read_bytes() == (target_before+b'# external edit\n' if case=='external-edit' else target_before)
        assert (bench.PROFILE if amsdu else bench.RADIO).read_bytes() == (original if amsdu else radio_original)
        if case=='busy': assert not events
        if case in ('success','failed-benchmark','interrupted','failed-restart'):
            assert events.count(['sudo','systemctl','restart','owlyd.service']) == 2
    assert all(p.stat().st_mode & 0o077 == 0 for p in bench.BACKUPS.iterdir())
print('ACK and A-MSDU candidates, atomic install, rollback, failure, interruption and external edit checks passed; no system changes')
