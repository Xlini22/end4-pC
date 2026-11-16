"""Read-only ath10k preflight; no radio, tracing or driver settings changed."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile


# Only this fixed, read-only program runs under sudo; no repo imports as root.
READ_ONLY = '''from pathlib import Path
import json

def collect(debug, trace):
    result = {'files': {}, 'errors': {}, 'debug_entries': {}}
    def read(path):
        try:
            result['files'][str(path)] = path.read_text()
        except OSError as error:
            result['errors'][str(path)] = str(error)
    try:
        devices = sorted(debug.glob('phy*/ath10k'))
        for device in devices:
            result['debug_entries'][str(device)] = sorted(p.name for p in device.iterdir())
            read(device / 'fw_stats')
    except OSError as error:
        result['errors'][str(debug)] = str(error)
    read(trace / 'available_events')
    read(trace / 'tracing_on')
    read(trace / 'current_tracer')
    try:
        formats = sorted((trace / 'events/ath10k').glob('*/format'))
        formats += sorted((trace / 'events/mac80211').glob('*tx*/format'))
        for path in formats:
            read(path)
    except OSError as error:
        result['errors'][str(trace / 'events')] = str(error)
    return result
'''


def self_test():
    namespace = {}
    exec(READ_ONLY, namespace)
    with tempfile.TemporaryDirectory(prefix='ath10k check with spaces ') as temporary:
        base = Path(temporary)
        device = base / 'debug/phy0/ath10k'
        event = base / 'trace/events/ath10k/ath10k_htt_tx'
        device.mkdir(parents=True)
        event.mkdir(parents=True)
        (device / 'fw_stats').write_text('tx rate 12000\n')
        (event / 'format').write_text('field:unsigned short msdu_id;\n')
        (base / 'trace/available_events').write_text('ath10k:ath10k_htt_tx\n')
        (base / 'trace/tracing_on').write_text('0\n')
        before = {p: p.read_bytes() for p in base.rglob('*') if p.is_file()}
        result = namespace['collect'](base / 'debug', base / 'trace')
        assert result['files'][str(device / 'fw_stats')] == 'tx rate 12000\n'
        assert result['files'][str(event / 'format')].startswith('field:')
        assert str(base / 'trace/current_tracer') in result['errors']
        assert before == {p: p.read_bytes() for p in base.rglob('*') if p.is_file()}
    print('OK: inventory, missing files, paths with spaces, no file changes')


def main():
    base = Path('/tmp/end4-airdrop-speed')
    base.mkdir(mode=0o700, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='driver-inventory-', dir=base))
    print('PRECONTROLLO ATH10K: Wi-Fi collegato, nessun trasferimento.', flush=True)
    print('Legge contatori firmware e formati tracepoint. Non attiva tracing né AirDrop.', flush=True)
    print(f'Log privati: {output}', flush=True)
    input('Premi Invio per il precontrollo (serve la password sudo): ')
    subprocess.run(['sudo', '-v'], check=True)
    program = READ_ONLY + "\nprint(json.dumps(collect(Path('/sys/kernel/debug/ieee80211'), Path('/sys/kernel/tracing'))))\n"
    result = subprocess.run(['sudo', '-n', '/usr/bin/python3', '-I', '-c', program],
                            capture_output=True, text=True, timeout=20, check=True)
    inventory = json.loads(result.stdout)
    (output / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    (output / 'stderr.log').write_text(result.stderr)
    formats = [name for name in inventory['files'] if name.endswith('/format')]
    print(f'Precontrollo concluso: {len(inventory["debug_entries"])} dispositivo/i, {len(formats)} formati.', flush=True)
    if inventory['errors']:
        print(f'Voci non disponibili: {len(inventory["errors"])}; dettagli nel log.', flush=True)
    print(f'Risultato: {output / "inventory.json"}', flush=True)
    input('Torna alla chat per l’analisi. Premi Invio per chiudere: ')


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        self_test()
    elif sys.argv[1:]:
        raise SystemExit('Usage: bench-driver-inventory.py [--self-test]')
    else:
        try:
            main()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print(f'Precontrollo fallito: {error}', file=sys.stderr)
            input('Premi Invio per chiudere: ')
            raise SystemExit(1)
