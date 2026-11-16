"""Local ACK or --amsdu benchmark; restore the original configuration afterwards."""
from pathlib import Path
import argparse
import json
import os
import shlex
import signal
import subprocess
import tempfile
import tomllib

PROFILE = Path('/etc/owly/drivers.toml')
RADIO = Path('/etc/owly/radio.toml')
BENCH = Path(__file__).with_name('bench-speed.sh')
BACKUPS = Path(__file__).with_name('benchmarks')
CLI = os.environ.get('OMDROP_CLI', str(Path.home() / '.local/bin/omdrop'))


def candidate(original, amsdu=False):
    if amsdu:
        before = tomllib.loads(original.decode())
        if 'tx_amsdu' in before:
            raise ValueError('tx_amsdu gia configurato: verificare prima della prova.')
        result = b'tx_amsdu = true\n' + original
        after = tomllib.loads(result.decode())
        assert after.pop('tx_amsdu') is True and after == before
        return result
    header = '[drivers.ath10k_pci]\n'
    text = original.decode()
    before = tomllib.loads(text)
    if text.count(header) != 1 or 'tx_noack' in before['drivers']['ath10k_pci']:
        raise ValueError('Il profilo e cambiato: verificare il parametro tx_noack prima della prova.')
    result = text.replace(header, header + 'tx_noack = false\n', 1).encode()
    after = tomllib.loads(result.decode())
    assert after['drivers']['ath10k_pci'].pop('tx_noack') is False and after == before
    return result


def idle():
    status = json.loads(subprocess.check_output([CLI, 'status', '--json'], text=True))
    if status.get('receiving') is not False or status.get('visible') is not False:
        raise RuntimeError('Spegni AirDrop prima della prova.')
    state = subprocess.check_output([
        'busctl', '--system', 'get-property', 'io.github.t4t5.Owly',
        '/io/github/t4t5/Owly', 'io.github.t4t5.Owly.Radio1', 'State'], text=True).strip()
    if state != 's "idle"':
        raise RuntimeError('Owly non e idle: nessuna configurazione modificata.')


def main(amsdu=False):
    os.umask(0o022)
    idle()
    profile, untouched = (RADIO, PROFILE) if amsdu else (PROFILE, RADIO)
    variant = 'tx_amsdu=true' if amsdu else 'tx_noack=false'
    original = profile.read_bytes()
    other_before = untouched.read_bytes()
    proposed = candidate(original, amsdu)
    BACKUPS.mkdir(exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix='amsdu-' if amsdu else 'ack-', dir=BACKUPS))
    before = backup / (profile.stem + '.before.toml')
    after = backup / (profile.stem + '.candidate.toml')
    before.write_bytes(original)
    after.write_bytes(proposed)
    (backup / 'phase').write_text('prepared\n')
    # Atomic replacement keeps a failed copy from truncating the live profile.
    staging = profile.with_name('.' + backup.name + '.toml')
    def install(source):
        subprocess.run(['sudo', 'install', '-m', '0644', '--', str(source), str(staging)], check=True)
        subprocess.run(['sudo', 'mv', '-T', '--', str(staging), str(profile)], check=True)
    recovery = backup / 'restore.sh'
    recovery.write_text('#!/usr/bin/env bash\nset -euo pipefail\numask 022\n'
        + shlex.join([CLI, 'off', '--force']) + ' || true\n' + '\n'.join(
        shlex.join(command) for command in (
            ['sudo', 'install', '-m', '0644', '--', str(before.resolve()), str(staging)],
            ['sudo', 'mv', '-T', '--', str(staging), str(profile)],
            ['sudo', 'systemctl', 'restart', 'owlyd.service'])) + '\n')
    print(f'PROVA AIRDROP: cambia soltanto {variant}, sul canale 6.', flush=True)
    print('Il profilo originale viene ripristinato alla fine, anche se la prova fallisce.', flush=True)
    print('Serve la password sudo. Prima autentichiamo il PC, poi preparerai iPhone.', flush=True)
    print(f'Backup persistente: {backup}\nRipristino manuale, se necessario: bash {shlex.quote(str(recovery))}', flush=True)
    input('Premi Invio per preparare il profilo temporaneo; Ctrl+C annulla: ')
    idle()
    if profile.read_bytes() != original or untouched.read_bytes() != other_before:
        raise RuntimeError('Configurazione modificata nel frattempo: prova annullata.')
    subprocess.run(['sudo', '-v'], check=True)
    modified = False
    child = None
    try:
        # Set before mutation so the finally block also handles an interrupted install.
        modified = True
        install(after)
        subprocess.run(['sudo', 'systemctl', 'restart', 'owlyd.service'], check=True)
        subprocess.run(['systemctl', 'is-active', '--quiet', 'owlyd.service'], check=True)
        (backup / 'phase').write_text('active\n')
        print(f'Profilo {variant} attivo. Segui il benchmark; non cambiare il widget.', flush=True)
        child = subprocess.Popen(['bash', str(BENCH), '--tcp'],
            env={**os.environ, 'OMDROP_BENCH_VARIANT': variant})
        result = child.wait()
        (backup / 'result').write_text(str(result) + '\n')
        return result
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        if modified:
            try:
                subprocess.run([CLI, 'off', '--force'], check=False, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as error:
                print(f'Arresto CLI non completato: {error}. Ripristino comunque il profilo.', flush=True)
            current = profile.read_bytes()
            if current not in (original, proposed):
                raise RuntimeError(f'Il profilo contiene modifiche esterne: preservato. Backup in {backup}')
            install(before)
            subprocess.run(['sudo', 'systemctl', 'restart', 'owlyd.service'], check=True)
            subprocess.run(['systemctl', 'is-active', '--quiet', 'owlyd.service'], check=True)
            if profile.read_bytes() != original or untouched.read_bytes() != other_before:
                raise RuntimeError(f'Ripristino da verificare: backup in {backup}')
            (backup / 'phase').write_text('restored\n')
            print('Profilo originale ripristinato e demone riavviato. Prova sperimentale disattivata.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--amsdu', action='store_true', help='Prova tx_amsdu=true invece degli ACK radio')
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    try:
        result = main(args.amsdu)
    except KeyboardInterrupt:
        print('\nProva annullata.', flush=True)
        result = 130
    except Exception as error:
        print(f'ERRORE: {error}\nConserva questo terminale e il percorso del backup.', flush=True)
        result = 1
    try:
        input('Premi Invio per chiudere questo terminale: ')
    except (EOFError, KeyboardInterrupt):
        pass
    raise SystemExit(result)
