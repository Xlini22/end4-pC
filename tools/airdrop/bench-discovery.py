"""Guided AWDL discovery or one ZIP transfer, with a temporary diagnostic daemon."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time


spec = importlib.util.spec_from_file_location('discovery_backend', Path(__file__).with_name('bench-pacing.py'))
backend = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backend
spec.loader.exec_module(backend)
# Reuse the already checked package switch/rollback; no pacing code is used.
backend.PACKAGE = 'owly-qca9377-diag-bench'
backend.EXPERIMENT = Path('/usr/lib/owly-qca9377-diag-bench/owlyd')
backend.OVERRIDE = Path('/run/systemd/system/owlyd.service.d/90-diag-bench.conf')
backend.BODY = f'[Service]\nExecStart=\nExecStart={backend.EXPERIMENT}\nEnvironment=OWLY_AWDL_DIAG=1\n'
CLI = backend.CLI
BENCH_ZIP = Path('/tmp/end4-airdrop-speed/airdrop-speed-8MiB.zip')
BENCH_SHA = 'ac2dbab130dd40c255993de77b844273f6871693fa18b8a051afe5a49be85b67'


def copy_benchmark(base):
    if BENCH_ZIP.is_symlink() or not BENCH_ZIP.is_file():
        raise RuntimeError('Lo ZIP di riferimento deve essere un file regolare.')
    destination = base / 'airdrop-speed-8MiB.zip'
    shutil.copyfile(BENCH_ZIP, destination)
    if hashlib.sha256(destination.read_bytes()).hexdigest() != BENCH_SHA:
        destination.unlink()
        raise RuntimeError('Lo ZIP è diverso da quello delle prove precedenti.')
    return destination


def observe():
    base = Path(os.environ.get('OMDROP_BENCH_DIR', '/tmp/end4-airdrop-speed'))
    run = Path(tempfile.mkdtemp(prefix='run-discovery-', dir=base))
    backend.idle()
    print('CATTURA AWDL - 90 secondi, nessun file da inviare.', flush=True)
    print('Tieni iPhone fermo e sbloccato, hotspot spento, Wi-Fi e Bluetooth accesi.', flush=True)
    print('Rinnova Tutti per 10 minuti e apri Foto > Condividi > AirDrop.', flush=True)
    print('Quando compare il PC tra i destinatari, NON toccarlo: lascia aperta soltanto la ricerca.', flush=True)
    print('Lascia gli altri Apple come sono; non cambiare widget o reti durante la cattura.', flush=True)
    input('Premi Invio quando sei pronto: solo ora parte AirDrop e si sospende il Wi-Fi del PC: ')
    backend.idle()
    ready = False
    try:
        subprocess.run([CLI, 'on', '-e', '10m'], check=True, timeout=40)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            state = json.loads(subprocess.check_output([CLI, 'status', '--json'], text=True, timeout=5))
            if state.get('receiving') is True and state.get('visible') is True:
                ready = True
                break
            time.sleep(1)
        if not ready:
            raise RuntimeError('Radio/ricevitore non pronti: cattura annullata, avvio ripristino.')
        print('RADIO PRONTA. Non avviare trasferimenti; tieni aperta la schermata AirDrop per 90 secondi.', flush=True)
        deadline = time.monotonic() + 90
        with (run / 'observations.jsonl').open('w') as output:
            while time.monotonic() < deadline:
                state = json.loads(subprocess.check_output([CLI, 'status', '--json'], text=True, timeout=5))
                if not state.get('receiving') or not state.get('visible'):
                    raise RuntimeError('La ricezione si è fermata durante la cattura.')
                result = subprocess.run([CLI, 'peers', '--json'], capture_output=True, text=True, timeout=5)
                row = dict(observed_at=time.time(), observed_mono=time.monotonic(),
                    status=state, peers=json.loads(result.stdout) if result.returncode == 0 else None,
                    peers_exit=result.returncode)
                output.write(json.dumps(row) + '\n')
                output.flush()
                print(f'Cattura in corso: ancora {max(0, int(deadline - time.monotonic()))} secondi.', flush=True)
                time.sleep(min(5, max(0, deadline - time.monotonic())))
        (run / 'result').write_text('0\n')
        return 0
    finally:
        subprocess.run([CLI, 'off', '--force'], check=False, timeout=30)
        print(f'Cattura radio conclusa. Log: {run}', flush=True)


def captured_trial(environment):
    command = [sys.executable, str(Path(__file__).with_name('bench-channels.py'))]
    if environment.get('OMDROP_BENCH_TRANSFER') != '1':
        command.append('--discovery')
    child = subprocess.Popen(command, env=environment)
    try:
        return child.wait()
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=45)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


def validate_package(manifest):
    package = Path(manifest['package']).resolve()
    if hashlib.sha256(package.read_bytes()).hexdigest() != manifest['package_sha256']:
        raise RuntimeError('Pacchetto diverso da quello verificato: nessuna installazione.')
    names = subprocess.check_output(['bsdtar', '-tf', str(package)], text=True).splitlines()
    allowed = {'.PKGINFO', '.BUILDINFO', '.MTREE', 'usr/', 'usr/lib/', 'usr/share/', 'usr/share/licenses/'}
    for name in names:
        if '..' in Path(name).parts or (name not in allowed and not name.startswith((
                f'usr/lib/{backend.PACKAGE}/', f'usr/share/licenses/{backend.PACKAGE}/'))):
            raise RuntimeError('Il pacchetto contiene percorsi inattesi.')
    info = subprocess.check_output(['bsdtar', '-xOf', str(package), '.PKGINFO'], text=True)
    if f'pkgname = {backend.PACKAGE}\n' not in info:
        raise RuntimeError('Nome pacchetto inatteso.')
    binary = subprocess.check_output(['bsdtar', '-xOf', str(package), str(backend.EXPERIMENT).lstrip('/')])
    if hashlib.sha256(binary).hexdigest() != manifest['binary_sha256']:
        raise RuntimeError('Binario diverso da quello verificato.')
    return package


def main(manifest_path, transfer=False):
    manifest = json.loads(manifest_path.read_text())
    variant = manifest.get('variant', 'diagnostic-master-clock')
    if variant not in ('diagnostic-master-clock', 'sync-freshness'):
        raise RuntimeError('Variante diagnostica sconosciuta.')
    corrected = variant == 'sync-freshness'
    package = validate_package(manifest)
    backend.idle()
    if (backend.OVERRIDE.exists() or backend.EXPERIMENT.exists()
            or backend.executable() != str(backend.ORIGINAL)
            or subprocess.run(['pacman', '-Q', backend.PACKAGE], capture_output=True).returncode == 0):
        raise RuntimeError('Esperimento precedente o backend diverso: nessuna modifica.')
    if hashlib.sha256(backend.ORIGINAL.read_bytes()).hexdigest() != manifest['original_sha256']:
        raise RuntimeError('Il backend attuale è cambiato: prova annullata.')
    profiles = {str(p): p.read_bytes() for p in (Path('/etc/owly/radio.toml'), Path('/etc/owly/drivers.toml'))}
    connection = subprocess.check_output(['nmcli', '-g', 'GENERAL.CON-UUID', 'device', 'show', 'wlp2s0'], text=True).strip()
    if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', connection):
        raise RuntimeError('Rete Wi-Fi attuale non identificabile: verifica prima della prova.')
    prefix = ('transfer-sync-' if corrected else 'transfer-diag-') if transfer else 'discovery-'
    base = Path(tempfile.mkdtemp(prefix=prefix, dir='/tmp/end4-airdrop-speed'))
    if transfer:
        copied = copy_benchmark(base)
        manifest = dict(manifest, zip_sha256=BENCH_SHA, zip_size=copied.stat().st_size)
    unit = base / '90-diag-bench.conf'
    unit.write_text(backend.BODY)
    (base / 'manifest.json').write_text(json.dumps(dict(manifest, wifi_uuid=connection,
        trial='transfer' if transfer else 'discovery'), indent=2) + '\n')
    recovery = [
        [CLI, 'off', '--force'], ['sudo', 'rm', '-f', '--', str(backend.OVERRIDE)],
        ['sudo', 'systemctl', 'daemon-reload'], ['sudo', 'systemctl', 'restart', 'owlyd.service'],
    ]
    (base / 'restore.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
        + f'if [[ -e {shlex.quote(str(backend.OVERRIDE))} ]]; then cmp -s -- {shlex.quote(str(unit))} {shlex.quote(str(backend.OVERRIDE))}; fi\n'
        + '\n'.join(shlex.join(c) + (' || true' if c[0] == CLI else '') for c in recovery) + '\n'
        + f'if pacman -Q {backend.PACKAGE} >/dev/null 2>&1; then sudo pacman -R --noconfirm -- {backend.PACKAGE}; fi\n'
        + shlex.join(['nmcli', '-w', '30', 'connection', 'up', 'uuid', connection, 'ifname', 'wlp2s0']) + '\n')
    if corrected:
        print('PROVA CORREZIONE SYNC: rivalutazione elezione prima di applicare il clock del peer.', flush=True)
        print('Canale 6, ACK, pacing e guardia invariati. Serve sudo per il pacchetto temporaneo.', flush=True)
    else:
        print('PROVA DIAGNOSTICA: scheduler e canale 6 invariati. Serve sudo per il pacchetto temporaneo.', flush=True)
    print('Alla fine verrà rimosso SOLO il pacchetto diagnostico; quello originale resta installato.', flush=True)
    if transfer:
        print('Questa volta il PC INVIA un solo ZIP da 8 MiB: accettalo e salvalo in File sull’iPhone.', flush=True)
        print('Non inviare foto o altri file al PC. Tieni iPhone fermo e sbloccato fino alla fine.', flush=True)
        if corrected:
            print('Mantieni posizione iPhone e altri dispositivi Apple come nella prova da 154 secondi.', flush=True)
    print(f'Log e ripristino manuale: {base}', flush=True)
    input('Premi Invio per preparare la variante; la radio resterà spenta fino alla conferma finale: ')
    started = time.strftime('%Y-%m-%d %H:%M:%S')
    backend.benchmark = captured_trial
    environment = {**os.environ, 'OMDROP_BENCH_DIR': str(base), 'OMDROP_BENCH_NO_PAUSE': '1',
        'OMDROP_BENCH_TRANSFER': '1' if transfer else '0',
        'OMDROP_BENCH_VARIANT': variant if transfer else 'discovery',
        'OMDROP_BENCH_DESCRIPTION': ('Correzione sync attiva: elezione rivalutata prima del clock.' if corrected else
            'Diagnostica master/clock pronta. Nessuna modifica di velocità o canale.')}
    subprocess.run(['sudo', '-v'], check=True)
    try:
        if any(Path(p).read_bytes() != content for p, content in profiles.items()):
            raise RuntimeError('Profili modificati nel frattempo: prova annullata.')
        result = backend.paced_trial(package, unit, environment, manifest['binary_sha256'])
        (base / 'result').write_text(str(result) + '\n')
        return result
    finally:
        # Journal access here uses the local sudo credential; no repo code runs as root.
        journal_ok = False
        try:
            with (base / 'radio.jsonl').open('w') as output, (base / 'journal-errors.log').open('w') as errors:
                journal = subprocess.run(['sudo', '-n', 'journalctl', '-u', 'owlyd.service', '--since', started,
                    '--no-pager', '-o', 'json'], stdout=output, stderr=errors, timeout=20)
            journal_ok = journal.returncode == 0
        except (OSError, subprocess.TimeoutExpired) as error:
            (base / 'journal-errors.log').write_text(str(error) + '\n')
        restored = (not backend.OVERRIDE.exists() and not backend.EXPERIMENT.exists()
            and backend.executable() == str(backend.ORIGINAL))
        (base / 'phase').write_text('restored\n' if restored else 'restore-needed\n')
        if (not restored or any(Path(p).read_bytes() != content for p, content in profiles.items())
                or hashlib.sha256(backend.ORIGINAL.read_bytes()).hexdigest() != manifest['original_sha256']):
            raise RuntimeError(f'Ripristino da verificare: {base / "restore.sh"}')
        subprocess.run(['nmcli', '-w', '30', 'connection', 'up', 'uuid', connection, 'ifname', 'wlp2s0'],
            check=False, timeout=40)
        if not journal_ok:
            raise RuntimeError(f'Journal non raccolto: {base / "journal-errors.log"}')
        if not any('AWDL_DIAG_SYNC' in json.loads(line).get('MESSAGE', '')
                   for line in (base / 'radio.jsonl').read_text().splitlines() if line.strip()):
            raise RuntimeError('Nessun annuncio AWDL interno registrato: cattura non conclusiva, originale ripristinato.')
        print(f'Originale ripristinato e rete Wi-Fi richiamata. Torna alla chat. Log: {base}', flush=True)


def self_test():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory(prefix='discovery check with spaces ') as directory:
        base = Path(directory)
        unknown = base / 'unknown variant.json'
        unknown.write_text(json.dumps({'variant': 'unknown'}))
        with patch('subprocess.run') as commands:
            try:
                main(unknown, transfer=True)
            except RuntimeError as error:
                assert 'Variante diagnostica sconosciuta' in str(error)
            else:
                raise AssertionError('Unknown variant accepted')
            commands.assert_not_called()
        calls = []
        def command(argv, **kwargs):
            calls.append(argv)
            if argv[1:3] == ['status', '--json']:
                return json.dumps(dict(receiving=True, visible=True))
            return subprocess.CompletedProcess(argv, 0, '[]', '')
        for failure in (False, True):
            calls.clear()
            with patch.object(backend, 'idle'), patch('builtins.input', return_value=''), \
                    patch.dict(os.environ, {'OMDROP_BENCH_DIR': str(base)}), \
                    patch('subprocess.run', side_effect=command), \
                    patch('subprocess.check_output', side_effect=RuntimeError('failed readiness') if failure else command), \
                    patch('time.sleep'), \
                    patch('time.monotonic', side_effect=[0, 1, 2, 3, 4, 5, 6, 93] if not failure else [0, 1]):
                try:
                    assert observe() == 0
                except RuntimeError:
                    assert failure
            assert [CLI, 'off', '--force'] in calls
            assert all('send' not in c for c in calls)
        observations = list(base.glob('run-discovery-*/observations.jsonl'))
        assert len(observations) == 1
        assert json.loads(observations[0].read_text())['peers'] == []
        manifest = dict(package=str(base / 'test.pkg'), package_sha256='wrong')
        Path(manifest['package']).write_bytes(b'test')
        try:
            validate_package(manifest)
        except RuntimeError:
            pass
        else:
            raise AssertionError('Modified package accepted')
        # Exercise real file copying and reject changed content and symlinks.
        source = base / 'reference with spaces.zip'
        source.write_bytes(b'offline benchmark check')
        with patch.dict(globals(), BENCH_ZIP=source, BENCH_SHA=hashlib.sha256(source.read_bytes()).hexdigest()):
            copied = copy_benchmark(base)
            assert not copied.is_symlink() and copied.read_bytes() == source.read_bytes()
            copied.unlink()
            source.write_bytes(b'changed')
            try:
                copy_benchmark(base)
            except RuntimeError:
                pass
            else:
                raise AssertionError('Changed benchmark payload accepted')
            assert not copied.exists()
            source.unlink()
            source.symlink_to(base / 'missing')
            try:
                copy_benchmark(base)
            except RuntimeError:
                pass
            else:
                raise AssertionError('Benchmark symlink accepted')
        for transfer in (False, True):
            for interrupted in (False, True):
                env = {'OMDROP_BENCH_TRANSFER': '1' if transfer else '0'}
                with patch('subprocess.Popen') as spawn:
                    child = spawn.return_value
                    child.poll.return_value = None if interrupted else 0
                    child.wait.side_effect = [KeyboardInterrupt(), 130] if interrupted else [0]
                    try:
                        assert captured_trial(env) == 0
                    except KeyboardInterrupt:
                        assert interrupted
                    expected = [sys.executable, str(Path(__file__).with_name('bench-channels.py'))]
                    if not transfer:
                        expected.append('--discovery')
                    spawn.assert_called_once_with(expected, env=env)
                    assert child.terminate.call_count == int(interrupted)
    print('OK: discovery success/readiness failure, receiver cleanup, package hash and paths with spaces; no radio')
    override, experiment = backend.OVERRIDE, backend.EXPERIMENT
    try:
        backend.self_test()
    finally:
        backend.OVERRIDE, backend.EXPERIMENT = override, experiment


if __name__ == '__main__':
    os.umask(0o022)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path, nargs='?')
    parser.add_argument('--observe', action='store_true')
    parser.add_argument('--transfer', action='store_true', help='One PC-to-iPhone ZIP with clock/TCP diagnostics')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    try:
        if args.self_test:
            self_test()
            raise SystemExit(0)
        if args.observe:
            raise SystemExit(observe())
        if args.manifest is None:
            parser.error('Provide the package manifest')
        result = main(args.manifest, transfer=args.transfer)
    except KeyboardInterrupt:
        result = 130
    except Exception as error:
        print(f'ERRORE: {error}. Conserva il terminale e il percorso restore.sh.', file=sys.stderr, flush=True)
        result = 1
    if not args.observe:
        try:
            input('Premi Invio per chiudere: ')
        except (EOFError, KeyboardInterrupt):
            pass
    raise SystemExit(result)
