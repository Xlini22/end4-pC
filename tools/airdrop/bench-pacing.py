"""Local baseline/pacing comparison with a separate package and runtime unit."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile

PACKAGE = 'owly-qca9377-pacing-bench'
ORIGINAL = Path('/usr/lib/owly-qca9377/owlyd')
EXPERIMENT = Path('/usr/lib/owly-qca9377-pacing-bench/owlyd')
OVERRIDE = Path('/run/systemd/system/owlyd.service.d/90-pacing-bench.conf')
BODY = f'[Service]\nExecStart=\nExecStart={EXPERIMENT}\n'
CLI = str(Path.home() / '.local/bin/omdrop')
BENCH = Path(__file__).with_name('bench-driver.py').resolve()


def run(command):
    return subprocess.run(command, check=True)


def idle():
    status = json.loads(subprocess.check_output([CLI, 'status', '--json'], text=True))
    state = subprocess.check_output(['busctl', '--system', 'get-property', 'io.github.t4t5.Owly',
        '/io/github/t4t5/Owly', 'io.github.t4t5.Owly.Radio1', 'State'], text=True).strip()
    if status.get('receiving') is not False or status.get('visible') is not False or state != 's "idle"':
        raise RuntimeError('Spegni AirDrop e attendi che Owly sia idle.')


def executable():
    value = subprocess.check_output(['systemctl', 'show', '--value', '-p', 'ExecStart', 'owlyd.service'], text=True)
    return re.search(r'\bpath=([^ ;]+)', value)[1]


def installed_hash():
    for path in (EXPERIMENT, EXPERIMENT.parent):
        stat = path.stat()
        if path.is_symlink() or stat.st_uid != 0 or stat.st_mode & 0o022:
            raise RuntimeError('Backend sperimentale o directory non protetti da root.')
    return hashlib.sha256(EXPERIMENT.read_bytes()).hexdigest()


def benchmark(environment):
    child = subprocess.Popen([sys.executable, str(BENCH), '--completion-status'], env=environment)
    try:
        return child.wait()
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=60)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


def paced_trial(package, unit, environment, binary_hash):
    installed = changed = False
    try:
        idle()
        if OVERRIDE.exists():
            raise RuntimeError('Override gia esistente: nessuna modifica.')
        installed = True
        run(['sudo', 'pacman', '-U', '--noconfirm', '--', str(package)])
        if installed_hash() != binary_hash:
            raise RuntimeError('Hash backend sperimentale non corrispondente.')
        changed = True
        run(['sudo', 'install', '-D', '-m', '0644', '--', str(unit), str(OVERRIDE)])
        run(['systemd-analyze', 'verify', 'owlyd.service'])
        run(['sudo', 'systemctl', 'daemon-reload'])
        run(['sudo', 'systemctl', 'restart', 'owlyd.service'])
        run(['systemctl', 'is-active', '--quiet', 'owlyd.service'])
        if executable() != str(EXPERIMENT):
            raise RuntimeError('Backend sperimentale non attivo.')
        print(environment.get('OMDROP_BENCH_DESCRIPTION',
            'Backend sperimentale pronto: un frame unicast ogni 2 ms. Rinnova Tutti per 10 minuti.'), flush=True)
        return benchmark(environment)
    finally:
        if changed:
            try:
                subprocess.run([CLI, 'off', '--force'], check=False, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as error:
                print(f'Arresto CLI non completato: {error}. Ripristino comunque il backend.', flush=True)
            if OVERRIDE.exists():
                if OVERRIDE.read_text() != BODY:
                    raise RuntimeError(f'Override modificato esternamente: preservato. Leggi {unit.parent / "restore.sh"}')
                run(['sudo', 'rm', '--', str(OVERRIDE)])
            run(['sudo', 'systemctl', 'daemon-reload'])
            run(['sudo', 'systemctl', 'restart', 'owlyd.service'])
            run(['systemctl', 'is-active', '--quiet', 'owlyd.service'])
            if executable() != str(ORIGINAL):
                raise RuntimeError('Ripristino eseguibile originale da verificare; pacchetto preservato.')
        if installed and subprocess.run(['pacman', '-Q', PACKAGE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            run(['sudo', 'pacman', '-R', '--noconfirm', '--', PACKAGE])
        if changed:
            print('Backend originale ripristinato; override e pacchetto sperimentali rimossi.', flush=True)


def compare_phases(package, unit, environment, folders, binary_hash, pacing_first=False):
    order = ('pacing', 'baseline') if pacing_first else ('baseline', 'pacing')
    for index, phase in enumerate(order, 1):
        if index > 1:
            input('Prima fase completata. Lascia iPhone fermo, rinnova Tutti 10min; Invio per continuare: ')
        print(f'FASE {index}/2: {"variante 2 ms" if phase == "pacing" else "backend normale"}.', flush=True)
        (unit.parent / 'phase').write_text(phase+'\n')
        env = {**environment, 'OMDROP_BENCH_DIR': str(folders[phase])}
        if phase == 'pacing':
            if index == 1:
                input('Premi Invio per preparare la variante temporanea (serve sudo): ')
            run(['sudo', '-v'])
            result = paced_trial(package, unit, env, binary_hash)
        else:
            idle()
            if executable() != str(ORIGINAL):
                raise RuntimeError('Backend normale non ripristinato: seconda prova annullata.')
            result = benchmark(env)
        (unit.parent / (phase+'.result')).write_text(str(result)+'\n')
        if result:
            print('Fase non completata: confronto interrotto, nessun altro invio.', flush=True)
            return result
    return 0


def main(package, pacing_first=False):
    package = package.resolve()
    if not package.is_file():
        raise RuntimeError('Pacchetto sperimentale mancante.')
    names = subprocess.check_output(['bsdtar', '-tf', str(package)], text=True).splitlines()
    allowed = {'.PKGINFO', '.BUILDINFO', '.MTREE', 'usr/', 'usr/lib/', 'usr/share/', 'usr/share/licenses/'}
    if any(name not in allowed and not name.startswith(('usr/lib/' + PACKAGE + '/', 'usr/share/licenses/' + PACKAGE + '/')) for name in names):
        raise RuntimeError('Contenuto pacchetto inatteso.')
    info = subprocess.check_output(['bsdtar', '-xOf', str(package), '.PKGINFO'], text=True)
    if f'pkgname = {PACKAGE}\n' not in info:
        raise RuntimeError('Nome pacchetto inatteso.')
    binary = subprocess.check_output(['bsdtar', '-xOf', str(package), str(EXPERIMENT).lstrip('/')])
    binary_hash = hashlib.sha256(binary).hexdigest()
    already_installed = subprocess.run(['pacman', '-Q', PACKAGE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if OVERRIDE.exists() or EXPERIMENT.exists() or already_installed or executable() != str(ORIGINAL):
        raise RuntimeError('Esperimento precedente o backend diverso: nessuna modifica.')
    idle()
    original_hash = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    profiles = {name: Path(name).read_bytes() for name in ('/etc/owly/radio.toml', '/etc/owly/drivers.toml')}
    base = Path(tempfile.mkdtemp(prefix='compare-pacing-', dir='/tmp/end4-airdrop-speed'))
    baseline, pacing = base / 'baseline', base / 'pacing'
    baseline.mkdir(); pacing.mkdir()
    unit = base / '90-pacing-bench.conf'
    unit.write_text(BODY)
    (base / 'manifest.json').write_text(json.dumps(dict(package=str(package), package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
        original_sha256=original_hash, experiment_sha256=binary_hash, gap_us=2000,
        order=['pacing','baseline'] if pacing_first else ['baseline','pacing']), indent=2)+'\n')
    commands = [[CLI, 'off', '--force'], ['sudo', 'rm', '-f', '--', str(OVERRIDE)],
                ['sudo', 'systemctl', 'daemon-reload'], ['sudo', 'systemctl', 'restart', 'owlyd.service']]
    (base / 'restore.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
        + f'if [[ -e {shlex.quote(str(OVERRIDE))} ]]; then cmp -s -- {shlex.quote(str(unit))} {shlex.quote(str(OVERRIDE))}; fi\n'
        + '\n'.join(shlex.join(command) for command in commands)+'\n'
        + f'if pacman -Q {PACKAGE} >/dev/null 2>&1; then sudo pacman -R --noconfirm -- {PACKAGE}; fi\n')
    print('CONFRONTO AIRDROP: '+('variante 2 ms, poi normale.' if pacing_first else 'normale, poi variante 2 ms.'), flush=True)
    print('iPhone fermo nella stessa posizione/orientamento per entrambe le prove.', flush=True)
    print('La fase pacing installa un pacchetto locale separato, poi lo rimuove.', flush=True)
    print('Il backend attuale resta installato. Solo override systemd in /run, nessun profilo radio cambiato.', flush=True)
    print(f'Log e ripristino manuale: {base}', flush=True)
    environment = {**os.environ, 'OMDROP_BENCH_NO_PAUSE': '1'}
    try:
        result = compare_phases(package, unit, environment, {'baseline':baseline, 'pacing':pacing}, binary_hash, pacing_first)
        (base / 'result').write_text(str(result)+'\n')
        return result
    finally:
        if any(Path(name).read_bytes() != data for name, data in profiles.items()) or hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() != original_hash:
            raise RuntimeError('Backend/profili originali modificati esternamente: verifica necessaria.')
        restored = not OVERRIDE.exists() and executable() == str(ORIGINAL)
        (base / 'phase').write_text('restored\n' if restored else 'restore-needed\n')
        print(f'Confronto concluso. Log: {base}', flush=True)


def self_test():
    from unittest.mock import patch
    import shutil
    global OVERRIDE, EXPERIMENT
    with tempfile.TemporaryDirectory(prefix='pacing check with spaces ') as directory:
        base = Path(directory)
        OVERRIDE, EXPERIMENT = base / 'runtime.conf', base / 'binary'
        unit = base / 'candidate.conf'; unit.write_text(BODY)
        for case in ('success', 'failed-transfer', 'failed-restart', 'failed-install', 'off-timeout', 'failed-hash', 'failed-verify', 'cancelled'):
            calls, state = [], {'installed': False}
            def fake(command, **kwargs):
                calls.append(command)
                if command[:3] == ['sudo', 'pacman', '-U']:
                    if case == 'failed-install': raise subprocess.CalledProcessError(1, command)
                    state['installed'] = True; EXPERIMENT.write_bytes(b'test')
                elif command[:2] == ['sudo', 'install']: shutil.copyfile(unit, OVERRIDE)
                elif command[:2] == ['sudo', 'rm']: OVERRIDE.unlink()
                elif command[:3] == ['sudo', 'systemctl', 'restart'] and case == 'failed-restart' and OVERRIDE.exists():
                    raise subprocess.CalledProcessError(1, command)
                elif command[:2] == ['systemd-analyze', 'verify'] and case == 'failed-verify':
                    raise subprocess.CalledProcessError(1, command)
                elif command[:3] == ['sudo', 'pacman', '-R']:
                    state['installed'] = False; EXPERIMENT.unlink()
                elif command[:2] == [CLI, 'off'] and case == 'off-timeout':
                    raise subprocess.TimeoutExpired(command,30)
                code = 0
                if command[:2] == ['pacman', '-Q']: code = 0 if state['installed'] else 1
                if command[:2] == [sys.executable, str(BENCH)] and case == 'failed-transfer': code = 4
                return subprocess.CompletedProcess(command, code)
            with patch('subprocess.run', fake), patch(__name__+'.idle'), \
                 patch(__name__+'.installed_hash', return_value='wrong' if case == 'failed-hash' else hashlib.sha256(b'test').hexdigest()), \
                 patch(__name__+'.benchmark', side_effect=KeyboardInterrupt if case == 'cancelled' else None,
                       return_value=4 if case == 'failed-transfer' else 0), \
                 patch(__name__+'.executable', side_effect=lambda: str(EXPERIMENT if OVERRIDE.exists() else ORIGINAL)):
                try:
                    result = paced_trial(base/'package', unit, {}, hashlib.sha256(b'test').hexdigest())
                    assert result == (4 if case == 'failed-transfer' else 0)
                except subprocess.CalledProcessError:
                    assert case in ('failed-restart', 'failed-install', 'failed-verify')
                except RuntimeError:
                    assert case == 'failed-hash'
                except KeyboardInterrupt:
                    assert case == 'cancelled'
            assert not OVERRIDE.exists() and not state['installed'] and not EXPERIMENT.exists()
            if case not in ('failed-install', 'failed-hash'):
                assert ['sudo', 'rm', '--', str(OVERRIDE)] in calls
                assert ['sudo', 'pacman', '-R', '--noconfirm', '--', PACKAGE] in calls
        for reverse in (False, True):
            for fail_first in (False, True):
                seen = []
                def normal(env):
                    assert env['OMDROP_BENCH_DIR'] == str(base/'baseline')
                    seen.append('baseline')
                    return 4 if fail_first and len(seen)==1 else 0
                def paced(package, unit, env, digest):
                    assert env['OMDROP_BENCH_DIR'] == str(base/'pacing')
                    seen.append('pacing')
                    return 4 if fail_first and len(seen)==1 else 0
                with patch(__name__+'.benchmark', normal), patch(__name__+'.paced_trial', paced), \
                     patch(__name__+'.idle'), patch(__name__+'.executable', return_value=str(ORIGINAL)), \
                     patch(__name__+'.run'), patch('builtins.input', return_value=''):
                    result = compare_phases(base/'package', unit, {},
                        {'baseline':base/'baseline','pacing':base/'pacing'}, 'hash', reverse)
                expected = ['pacing','baseline'] if reverse else ['baseline','pacing']
                assert seen == (expected[:1] if fail_first else expected)
                assert result == (4 if fail_first else 0)
    with patch('subprocess.Popen') as process:
        child = process.return_value
        child.poll.return_value = None
        child.wait.side_effect = [KeyboardInterrupt, 130]
        try: benchmark({})
        except KeyboardInterrupt: pass
        else: raise AssertionError('Interrupt swallowed')
        child.terminate.assert_called_once()
    print('OK: both phase orders, stop on first failure, rollback, child termination and paths with spaces')


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        self_test()
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('package', type=Path)
        parser.add_argument('--pacing-first', action='store_true', help='Variante prima del backend normale')
        args = parser.parse_args()
        def interrupted(signum, frame): raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, interrupted); signal.signal(signal.SIGHUP, interrupted)
        try:
            result = main(args.package, args.pacing_first)
        except KeyboardInterrupt:
            result = 130
        except Exception as error:
            print(f'ERRORE: {error}. Conserva il terminale e il percorso restore.sh.', file=sys.stderr)
            result = 1
        try:
            input('Premi Invio per chiudere: ')
        except (EOFError, KeyboardInterrupt):
            pass
        raise SystemExit(result)
