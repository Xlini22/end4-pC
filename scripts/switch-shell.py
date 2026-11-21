#!/usr/bin/env python3
"""Select the next login's shell; never load/unload a compositor plugin."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile


def write(path, data):
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def select(home, target, instance, plugin=None):
    config = home / '.config/hypr/custom/variables.lua'
    native = home / '.local/share/end4-pC/native-glass'
    binary = native / 'hyprglass.so'
    parked = native / 'hyprglass.so.disabled-by-shell-switch'
    manifest = native / 'manifest.json'
    if target is not None and not (home / f'.config/quickshell/{target}/shell.qml').is_file():
        raise ValueError('Configurazione Quickshell non trovata')
    enabled = target == 'end4-pC' if plugin is None else plugin
    original = config.read_bytes()
    updated, count = re.subn(rb'hl\.env\("qsConfig", "(?:ii|end4-pC|end4-pC-main)"\)',
                             f'hl.env("qsConfig", "{target}")'.encode(), original)
    if count != 1:
        raise ValueError('Selettore qsConfig inatteso; nessuna modifica')
    if target is None:
        updated = original
    settings = home / '.config/illogical-impulse/config.json'
    old_settings = settings.read_bytes()
    options = json.loads(old_settings)
    glass = options.setdefault('background', {}).setdefault('widgets', {}).setdefault('glass', {})
    glass['nativePlugin'] = enabled
    if enabled:
        glass.update(enable=True, source='windows')
    elif target == 'ii':
        glass['source'] = 'wallpaper'
    with (native / 'loader.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (native / 'test-once.json').exists():
            raise ValueError('Test one-shot pendente: annullarlo prima del cambio')
        old_manifest = manifest.read_bytes()
        metadata = json.loads(old_manifest)
        source = None
        if enabled:
            if not instance:
                raise ValueError('Eseguire dalla sessione Hyprland: identificativo assente')
            candidates = [binary, parked, *sorted(native.glob('hyprglass.so.disabled-for-ii-*'))]
            source = next((p for p in candidates if p.is_file() and
                           hashlib.sha256(p.read_bytes()).hexdigest() == metadata['sha256']), None)
            if source is None:
                raise ValueError('Nessun binario HyprGlass corrisponde al manifest')
            metadata['deferInstance'] = instance
        elif binary.exists() and parked.exists():
            raise ValueError('Binario parcheggiato già presente: conservare entrambe le copie')
        backups = home / '.local/state/end4-pC/shell-switches'
        backups.mkdir(parents=True, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix='switch-', dir=backups))
        (backup / 'variables.lua').write_bytes(original)
        (backup / 'manifest.json').write_bytes(old_manifest)
        (backup / 'config.json').write_bytes(old_settings)
        created = moved = False
        try:
            if enabled:
                write(manifest, (json.dumps(metadata, indent=2) + '\n').encode())
                if source != binary:
                    if source == parked:
                        source.rename(binary)
                    else:
                        shutil.copy2(source, binary)
                    created = True
                    with binary.open('rb') as stream:
                        os.fsync(stream.fileno())
            elif binary.exists():
                binary.rename(parked)
                moved = True
            write(config, updated)
            write(settings, (json.dumps(options, ensure_ascii=False, indent=2) + '\n').encode())
        except Exception:
            if created:
                if source == parked:
                    binary.rename(parked)
                else:
                    binary.unlink()
            if moved:
                parked.rename(binary)
            write(manifest, old_manifest)
            write(config, original)
            write(settings, old_settings)
            raise
    return backup


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('shell', nargs='?', choices=['ii', 'end4', 'end4-pC'])
    parser.add_argument('--plugin', choices=['on', 'off'], help='Solo HyprGlass; non cambia la shell')
    args = parser.parse_args()
    if bool(args.shell) == bool(args.plugin):
        parser.error('Specificare una shell oppure --plugin on/off')
    try:
        target = ('ii' if args.shell == 'ii' else 'end4-pC') if args.shell else None
        enabled = args.plugin == 'on' if args.plugin else target == 'end4-pC'
        backup = select(Path.home(), target, os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'), enabled)
        print(f'Prossimo accesso: {target or "shell invariata"}; HyprGlass {"abilitato" if enabled else "disabilitato"}.')
        print('Salva il lavoro, esci dalla sessione e rientra. Nessun plugin viene caricato o scaricato a caldo.')
        print(f'Backup: {backup}')
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Errore: {error}\n')
