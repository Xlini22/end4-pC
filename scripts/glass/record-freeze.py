#!/usr/bin/env python3
"""Stream kernel messages and 1 Hz memory/GPU samples to an SSH host; never enables Glassy."""
import argparse
import datetime
import json
import os
from pathlib import Path
import select
import subprocess
import threading
import time
import uuid


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def sample():
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    gpu = []
    for device in Path('/sys/class/drm').glob('card*/device'):
        if not (device / 'gpu_busy_percent').exists():
            continue
        gpu.append({name: read(device / name) for name in (
            'gpu_busy_percent', 'mem_info_vram_used', 'mem_info_vram_total', 'mem_info_gtt_used')})
    return {'kind': 'sample', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'uptime_s': float(Path('/proc/uptime').read_text().split()[0]),
            'memory_kib': {name: int(memory[name].split()[0]) for name in
                           ('MemAvailable', 'SwapFree', 'SwapTotal', 'Dirty')},
            'pressure': {name: read('/proc/pressure/' + name) for name in ('cpu', 'memory', 'io')},
            'gpu': gpu}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', help='user@raspberry-IP; requires an already verified SSH host/key')
    parser.add_argument('--seconds', type=int, default=120)
    args = parser.parse_args()
    if args.destination.startswith('-') or args.seconds <= 0:
        parser.error('Specify user@host and a positive --seconds value')

    filename = 'freeze-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8] + '.jsonl'
    # The remote file is new and private; the PC never relies on its own disk to retain the stream.
    command = ('set -eu; umask 077; mkdir -p "$HOME/.local/state/end4-pC"; '
               f'file="$HOME/.local/state/end4-pC/{filename}"; '
               'set -C; exec 3>"$file"; printf "READY %s\\n" "$file"; '
               'cat >&3; exec 3>&-; sync -d "$file"')
    receiver = subprocess.Popen(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                                 '-o', 'ConnectTimeout=5', '-o', 'ServerAliveInterval=5',
                                 '-o', 'ServerAliveCountMax=2', args.destination, command],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                                start_new_session=True)
    journal = None
    worker = None
    failed = threading.Event()
    lock = threading.Lock()

    def emit(value):
        with lock:
            receiver.stdin.write(json.dumps(value, ensure_ascii=True) + '\n')
            receiver.stdin.flush()

    def kernel_messages():
        try:
            for line in journal.stdout:
                emit({'kind': 'kernel', 'line': line.rstrip('\n')})
        except OSError:
            failed.set()

    try:
        if not select.select([receiver.stdout], [], [], 15)[0]:
            raise RuntimeError('No acknowledgement from the remote recorder; collection was not started')
        ready = receiver.stdout.readline().strip()
        if not ready.startswith('READY '):
            raise RuntimeError('SSH recorder did not open its log; collection was not started')
        print('Remote log: ' + ready[6:], flush=True)
        emit({'kind': 'start', 'kernel': os.uname().release, 'boot_id': read('/proc/sys/kernel/random/boot_id'),
              'seconds': args.seconds, 'sample_interval_s': 1})
        journal = subprocess.Popen(['journalctl', '--dmesg', '--follow', '--lines=50', '--output=short-monotonic', '--no-pager'],
                                   stdout=subprocess.PIPE, text=True, errors='replace', bufsize=1,
                                   start_new_session=True)
        worker = threading.Thread(target=kernel_messages, daemon=True)
        worker.start()
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            if receiver.poll() is not None or failed.is_set():
                raise RuntimeError('Remote logging stopped; do not start a graphics test')
            if journal.poll() is not None:
                raise RuntimeError('Kernel log reader stopped; do not start a graphics test')
            emit(sample())
            failed.wait(min(1, max(0, deadline - time.monotonic())))
        emit({'kind': 'end', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    except KeyboardInterrupt:
        print('Collection interrupted; records already sent remain on the receiver.', flush=True)
    finally:
        if journal is not None:
            journal.terminate()
            journal.wait(timeout=5)
        if worker is not None:
            worker.join(timeout=5)
        try:
            receiver.stdin.close()
        except OSError:
            pass
        try:
            result = receiver.wait(timeout=15)
        except subprocess.TimeoutExpired:
            receiver.terminate()
            receiver.wait(timeout=5)
            raise RuntimeError('Receiver did not confirm completion; check the remote log')
        if result:
            raise RuntimeError(f'SSH recorder exited with code {result}; check the remote log')


if __name__ == '__main__':
    main()
