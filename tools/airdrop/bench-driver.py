"""One guided transfer with a temporary, metadata-only ath10k trace instance."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile


# Fixed supervisor only: repository programs execute after dropping privileges.
# stderr is a log opened by the caller, never a root-opened user-supplied path.
SUPERVISOR = '''from pathlib import Path
import json,os,signal,subprocess,sys,time

EVENTS = ('ath10k_htt_tx', 'ath10k_txrx_tx_unref')
COMPLETION_FILTER = 'level == 8 && msg ~ "htt tx completion msdu_id * status *"'

def capture(root, environment, command, uid, gid, completion_status=False):
    events = EVENTS + (('ath10k_log_dbg',) if completion_status else ())
    global_paths = [root / name for name in ('tracing_on', 'current_tracer', 'trace_clock')]
    global_paths += [root / 'events/ath10k' / name / 'enable' for name in events]
    global_paths.append(Path('/sys/module/ath10k_core/parameters/debug_mask'))
    if completion_status:
        global_paths.append(root / 'events/ath10k/ath10k_log_dbg/filter')
    before = {str(p): p.read_text() for p in global_paths}
    instance = root / 'instances' / ('odbench-' + str(os.getpid()))
    instance.mkdir()  # Never reuse or remove someone else's instance.
    child = None
    journal_start = time.time()
    report = {'type': 'complete', 'instance': str(instance), 'global_before': before,
              'completion_status': completion_status}
    def drop():
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)
    try:
        (instance / 'tracing_on').write_text('0')
        (instance / 'buffer_size_kb').write_text('4096')
        (instance / 'trace_clock').write_text('mono')
        if completion_status:
            path = instance / 'events/ath10k/ath10k_log_dbg/filter'
            path.write_text(COMPLETION_FILTER)
            report['completion_filter'] = path.read_text().strip()
            if report['completion_filter'] != COMPLETION_FILTER:
                raise RuntimeError('Completion filter readback failed')
        for event in events:
            (instance / 'events/ath10k' / event / 'enable').write_text('1')
        report['clock_start'] = {'wall': time.time(), 'mono': time.monotonic()}
        (instance / 'tracing_on').write_text('1')
        print('Cattura driver pronta: solo metadati, istanza temporanea.', flush=True)
        print(json.dumps({'type': 'ready', 'instance': str(instance)}), file=sys.stderr, flush=True)
        child = subprocess.Popen(command, env=environment, preexec_fn=drop, stderr=sys.stdout)
        # ponytail: bounded whole guided session; rerun if preparation takes >15 min.
        # A streaming collector is only needed for longer captures.
        return child.wait(timeout=900)
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        try:
            (instance / 'tracing_on').write_text('0')
            report['clock_end'] = {'wall': time.time(), 'mono': time.monotonic()}
            report['cpu_stats'] = {str(p.relative_to(instance)): p.read_text()
                                   for p in sorted((instance / 'per_cpu').glob('cpu*/stats'))}
            report['trace'] = (instance / 'trace').read_text()
        finally:
            try:
                (instance / 'events/enable').write_text('0')
            finally:
                instance.rmdir()
        report['instance_removed'] = not instance.exists()
        report['global_after'] = {str(p): p.read_text() for p in global_paths}
        report['journal'] = {}
        for name, selection in (('services', ['-u', 'owlyd.service', '-u', 'NetworkManager.service', '-u', 'wpa_supplicant.service']),
                                ('kernel', ['-k'])):
            try:
                log = subprocess.run(['/usr/bin/journalctl', '--since', '@' + str(journal_start),
                                      '--until', '@' + str(time.time()), '--no-pager', '-o', 'short-precise',
                                      *selection], capture_output=True, text=True, timeout=10)
                report['journal'][name] = {'returncode': log.returncode, 'stdout': log.stdout, 'stderr': log.stderr}
            except (OSError, subprocess.TimeoutExpired) as error:
                report['journal'][name] = {'error': str(error)}
        print(json.dumps(report), file=sys.stderr, flush=True)

if __name__ == '__main__':
    uid,gid = int(os.environ['SUDO_UID']),int(os.environ['SUDO_GID'])
    assert os.geteuid() == 0 and uid > 0
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    try:
        assert sys.argv[1] in ('timing', 'status')
        result = capture(Path('/sys/kernel/tracing'), json.loads(sys.argv[2]), sys.argv[3:], uid, gid,
                         completion_status=sys.argv[1] == 'status')
    except KeyboardInterrupt:
        result = 130
    raise SystemExit(result)
'''


def main(completion_status=False):
    cli = str(Path.home() / '.local/bin/omdrop')
    status = json.loads(subprocess.check_output([cli, 'status', '--json'], text=True))
    if status.get('receiving') is not False or status.get('visible') is not False:
        raise RuntimeError('Spegni AirDrop dal widget prima della prova.')
    base = Path(tempfile.mkdtemp(prefix='driver-status-' if completion_status else 'driver-',
                                dir=os.environ.get('OMDROP_BENCH_DIR', '/tmp/end4-airdrop-speed')))
    source = Path('/tmp/end4-airdrop-speed/airdrop-speed-8MiB.zip')
    if source.is_symlink() or not source.is_file():
        raise RuntimeError('Serve lo ZIP reale, non un collegamento.')
    target = base / source.name
    shutil.copyfile(source, target)
    target.chmod(0o600)
    check = Path(__file__).with_name('bench-archive-check.py')
    with (base / 'archive-preflight.log').open('w') as log:
        subprocess.run([sys.executable, str(check), str(target)], check=True, stdout=log, stderr=log)
    print('PROVA DRIVER AIRDROP — stesso ZIP da 8 MiB, profilo normale.', flush=True)
    if completion_status:
        print('Registro anche esiti TX firmware con filtro mirato; debug_mask resta invariato.', flush=True)
    print('Appoggia iPhone a circa un metro; accetta lo ZIP senza spostarlo.', flush=True)
    print('La radio aspettera un altro Invio. Il Wi-Fi viene ripristinato alla fine.', flush=True)
    print(f'Log privati: {base}', flush=True)
    input('Premi Invio per preparare la misura driver (serve sudo): ')
    subprocess.run(['sudo', '-v'], check=True)
    # Pass only session essentials, never the full environment or credentials.
    names = ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'LC_ALL', 'XDG_RUNTIME_DIR',
             'DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'WAYLAND_DISPLAY')
    environment = {name: os.environ[name] for name in names if name in os.environ}
    environment.update(OMDROP_BENCH_DIR=str(base), OMDROP_BENCH_NO_PAUSE='1')
    mode = 'status' if completion_status else 'timing'
    probe = ['/usr/bin/python3', '-I', '-c', 'import os; assert os.geteuid()>0; print("Controllo privilegi utente superato.",flush=True)']
    with (base / 'driver-preflight.jsonl').open('w') as log:
        subprocess.run(['sudo', '-n', '/usr/bin/python3', '-I', '-c', SUPERVISOR,
                        mode, json.dumps(environment), *probe], stderr=log, check=True)
    probe_report = json.loads((base / 'driver-preflight.jsonl').read_text().splitlines()[-1])
    if not probe_report['instance_removed'] or probe_report['global_before'] != probe_report['global_after']:
        raise RuntimeError('Preflight tracing non superato: nessuna radio avviata.')
    print('Preflight reale superato: privilegi, tracefs e cleanup verificati.', flush=True)
    command = [sys.executable, str(Path(__file__).with_name('bench-channels.py').resolve())]
    with (base / 'driver.jsonl').open('w') as log:
        child = subprocess.Popen(['sudo', '-n', '/usr/bin/python3', '-I', '-c', SUPERVISOR,
                                  mode, json.dumps(environment), *command], stderr=log)
        try:
            returncode = child.wait()
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
    for run in base.glob('run-*'):
        (run / 'driver-capture.path').write_text(str(base) + '\n')
    reports = []
    for line in (base / 'driver.jsonl').read_text().splitlines():
        if line.startswith('{'):
            reports.append(json.loads(line))
    complete = next((item for item in reports if item.get('type') == 'complete'), None)
    if complete is None or not complete['instance_removed']:
        raise RuntimeError(f'Cleanup driver da verificare: {base / "driver.jsonl"}')
    if complete['global_before'] != complete['global_after']:
        raise RuntimeError('Stato tracing globale variato durante la prova; verificare il log.')
    (base / 'trace.txt').write_text(complete.pop('trace'))
    (base / 'driver-summary.json').write_text(json.dumps(complete, indent=2) + '\n')
    print(f'Prova conclusa, esito {returncode}. Cattura rimossa, tracing globale invariato.', flush=True)
    print(f'Log: {base}. Torna alla chat per l’analisi.', flush=True)
    if os.environ.get('OMDROP_BENCH_NO_PAUSE') != '1':
        input('Premi Invio per chiudere: ')
    return returncode


def self_test():
    import io
    from unittest.mock import patch
    from contextlib import redirect_stderr, redirect_stdout
    namespace = {'__name__': 'driver_check'}
    exec(SUPERVISOR, namespace)
    with tempfile.TemporaryDirectory(prefix='driver check with spaces ') as temporary:
        root = Path(temporary)
        (root / 'instances').mkdir()
        for name in ('tracing_on', 'current_tracer', 'trace_clock'):
            (root / name).write_text('original\n')
        for name in namespace['EVENTS'] + ('ath10k_log_dbg',):
            path = root / 'events/ath10k' / name / 'enable'
            path.parent.mkdir(parents=True)
            path.write_text('0\n')
            (path.parent / 'filter').write_text('none\n')
        original_mkdir, original_rmdir, original_write = Path.mkdir, Path.rmdir, Path.write_text
        def write(path, data, *args, **kwargs):
            if case == 'filter-rejected' and data == namespace['COMPLETION_FILTER']:
                raise OSError('synthetic kernel filter rejection')
            return original_write(path, data, *args, **kwargs)
        def mkdir(path, *args, **kwargs):
            existed = path.exists()
            original_mkdir(path, *args, **kwargs)
            if not existed and path.parent == root / 'instances':
                for name in ('tracing_on', 'buffer_size_kb', 'trace_clock', 'trace', 'events/enable', 'per_cpu/cpu0/stats'):
                    item = path / name
                    item.parent.mkdir(parents=True, exist_ok=True)
                    item.write_text('overrun: 0\n' if name.endswith('/stats') else '')
                for event in namespace['EVENTS'] + ('ath10k_log_dbg',):
                    item = path / 'events/ath10k' / event / 'enable'
                    item.parent.mkdir(parents=True, exist_ok=True)
                    item.write_text('0')
                    (item.parent / 'filter').write_text('none\n')
        def rmdir(path):
            if path.parent == root / 'instances':
                assert (path / 'tracing_on').read_text() == '0'
                assert (path / 'events/enable').read_text() == '0'
                assert (path / 'trace_clock').read_text() == 'mono'
                assert (path / 'buffer_size_kb').read_text() == '4096'
                if with_status and case != 'filter-rejected':
                    assert (path / 'events/ath10k/ath10k_log_dbg/filter').read_text() == namespace['COMPLETION_FILTER']
                shutil.rmtree(path)
            else:
                original_rmdir(path)
        cases = [(mode, case) for mode in (False, True) for case in ('ok', 'failed', 'start-failed', 'timeout', 'journal-timeout')]
        for with_status, case in cases + [(True, 'filter-rejected')]:
            output = io.StringIO()
            with patch.object(Path, 'mkdir', mkdir), patch.object(Path, 'rmdir', rmdir), \
                 patch.object(Path, 'write_text', write), \
                 patch('subprocess.run') as journal, \
                 patch('subprocess.Popen') as process, redirect_stderr(output), redirect_stdout(io.StringIO()):
                journal.return_value = subprocess.CompletedProcess([], 0, 'synthetic log', '')
                if case == 'journal-timeout': journal.side_effect = subprocess.TimeoutExpired('journalctl', 10)
                child = process.return_value
                child.poll.return_value = None if case == 'timeout' else 0
                child.wait.side_effect = [subprocess.TimeoutExpired('test', 900), 130] if case == 'timeout' else None
                child.wait.return_value = 4 if case == 'failed' else 0
                if case == 'start-failed': process.side_effect = OSError('synthetic startup failure')
                try:
                    result = namespace['capture'](root, {}, ['user-command'], os.getuid(), os.getgid(), with_status)
                    assert result == (4 if case == 'failed' else 0)
                except (OSError, subprocess.TimeoutExpired):
                    assert case in ('start-failed', 'timeout', 'filter-rejected')
                assert not list((root / 'instances').iterdir())
                complete = json.loads(output.getvalue().splitlines()[-1])
                assert complete['instance_removed']
                assert complete['completion_status'] == with_status
                assert complete['global_before'] == complete['global_after']
                assert set(complete['journal']) == {'services', 'kernel'}
                assert journal.call_count == 2
                for call in journal.call_args_list:
                    assert call.args[0][0] == '/usr/bin/journalctl' and '--since' in call.args[0]
                    assert call.kwargs['timeout'] == 10
                if case == 'journal-timeout':
                    assert all('error' in log for log in complete['journal'].values())
                else:
                    assert all(log['stdout'] == 'synthetic log' for log in complete['journal'].values())
                if case == 'timeout': child.terminate.assert_called_once()
                if case == 'filter-rejected': process.assert_not_called()
                if case not in ('start-failed', 'filter-rejected'):
                    with patch('os.setgroups') as groups, patch('os.setgid') as gid, patch('os.setuid') as uid:
                        process.call_args.kwargs['preexec_fn']()
                        groups.assert_called_once_with([])
                        gid.assert_called_once_with(os.getgid())
                        uid.assert_called_once_with(os.getuid())
    print('OK: privilege drop, isolated events/status filter, rejection before child start, cleanup on success/failure/timeout, paths with spaces')


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        self_test()
    elif sys.argv[1:] not in ([], ['--completion-status']):
        raise SystemExit('Usage: bench-driver.py [--self-test | --completion-status]')
    else:
        def interrupted(signum, frame):
            raise KeyboardInterrupt
        import signal
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGHUP, interrupted)
        try:
            raise SystemExit(main(completion_status=sys.argv[1:] == ['--completion-status']))
        except KeyboardInterrupt:
            raise SystemExit(130)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            print(f'ERRORE: {error}', file=sys.stderr)
            if os.environ.get('OMDROP_BENCH_NO_PAUSE') != '1':
                input('Premi Invio per chiudere: ')
            raise SystemExit(1)
