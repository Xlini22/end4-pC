#!/usr/bin/env python3
"""From a TTY: recover-session.py [--restart-qs | --status]. Never kills Hyprland."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]


def command(args, env=None):
    return subprocess.check_output(args, env=env, text=True, timeout=8).strip()


def hyprland_pids():
    pids = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid == os.getuid() and (proc / 'comm').read_text().strip() == 'Hyprland':
                pids.append(int(proc.name))
        except FileNotFoundError:
            pass
    return pids


def recover(status=False, restart=False):
    if not status and (not sys.stdin.isatty() or not os.ttyname(0).startswith('/dev/tty')):
        raise RuntimeError('Esegui questo comando da una TTY (Ctrl+Alt+F3).')
    env = dict(os.environ)
    env['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
    pids = hyprland_pids()
    instances = json.loads(command(['hyprctl', 'instances', '-j'], env))
    instances = [i for i in instances if i['pid'] in pids]
    if len(instances) > 1:
        raise RuntimeError('Più sessioni Hyprland: non scelgo automaticamente quale recuperare.')
    if not instances:
        if pids:
            raise RuntimeError('Hyprland è presente ma non ha una sessione IPC rilevabile. Nessun secondo compositor avviato.')
        print('Nessuna sessione Hyprland. Avvio da zero con start-hyprland.', flush=True)
        if not status:
            for key in ('WAYLAND_DISPLAY', 'DISPLAY', 'HYPRLAND_INSTANCE_SIGNATURE', 'HYPRLAND_CONFIG', 'NOTIFY_SOCKET', 'WATCHDOG_PID', 'WATCHDOG_USEC'):
                env.pop(key, None)
            # ponytail: the installed desktop entry uses start-hyprland; its normal
            # autostart already launches Quickshell and the other session services.
            os.execvpe('start-hyprland', ['start-hyprland'], env)
        return
    instance = instances[0]
    inherited = dict(x.split('=', 1) for x in Path(f"/proc/{instance['pid']}/environ").read_text().split('\0') if '=' in x)
    for key in ('DBUS_SESSION_BUS_ADDRESS', 'XDG_SESSION_ID', 'XDG_VTNR', 'XDG_CURRENT_DESKTOP', 'XDG_SESSION_DESKTOP'):
        if key in inherited:
            env[key] = inherited[key]
    env.update(HYPRLAND_INSTANCE_SIGNATURE=instance['instance'], WAYLAND_DISPLAY=instance['wl_socket'], XDG_SESSION_TYPE='wayland')
    env.pop('DISPLAY', None)
    # A responsive IPC endpoint is required before any change to the session.
    assert json.loads(command(['hyprctl', '-j', 'monitors'], env)), 'Hyprland non espone monitor attivi.'
    shells = json.loads(command(['qs', 'list', '-p', str(REPO / 'shell.qml'), '--json'], env))
    print(f"Hyprland attivo (PID {instance['pid']}); Quickshell: {len(shells)} istanze.", flush=True)
    if status:
        return
    if restart:
        for shell in shells:
            command(['qs', 'kill', '--pid', str(shell['pid'])], env)
        deadline = time.monotonic() + 8
        while json.loads(command(['qs', 'list', '-p', str(REPO / 'shell.qml'), '--json'], env)):
            if time.monotonic() >= deadline:
                raise RuntimeError('Quickshell non si è chiuso: non avvio una seconda istanza.')
            time.sleep(.1)
    if not shells or restart:
        subprocess.run(['qs', '-p', str(REPO / 'shell.qml'), '--no-duplicate', '--daemonize'], env=env, check=True, timeout=20)
        if not json.loads(command(['qs', 'list', '-p', str(REPO / 'shell.qml'), '--json'], env)):
            raise RuntimeError('Quickshell non risulta avviato: controllare i suoi log.')
        print('Quickshell avviato.', flush=True)
    session = inherited.get('XDG_SESSION_ID')
    if not session:
        raise RuntimeError('Sessione recuperata; ID login assente. Torna al desktop con Ctrl+Alt+F1.')
    subprocess.run(['loginctl', 'activate', session], check=True, timeout=8)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--status', action='store_true', help='Leggi lo stato senza avviare o cambiare sessione.')
    group.add_argument('--restart-qs', action='store_true', help='Riavvia solo Quickshell nella sessione esistente.')
    args = parser.parse_args()
    try:
        recover(args.status, args.restart_qs)
    except (OSError, ValueError, KeyError, AssertionError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(f'Recupero interrotto: {error}\nNessun riavvio forzato di Hyprland. Un blocco GPU/kernel non è recuperabile con questo script.')
