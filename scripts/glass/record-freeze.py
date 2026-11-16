#!/usr/bin/env python3
"""Record kernel/Hyprland logs and 1 Hz resources to SSH or a private local file; never enables Glassy."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import select
import shlex
import signal
import subprocess
import threading
import time
import traceback
import uuid


# ponytail: a single SSH receiver, fsync at most once/second; this bounds the
# unsynced tail, not storage-controller power-loss behavior. No remote dependency.
RECEIVER = r'''
import datetime,json,os,select,sys,time
path=os.path.expanduser(sys.argv[1])
os.makedirs(os.path.dirname(path),mode=0o700,exist_ok=True)
stream=os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w',buffering=1)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def emit(row):stream.write(json.dumps(row,ensure_ascii=True)+'\n');stream.flush()
started=time.monotonic();last_data=None;last_sample=None;last_seq=None;sender_end=False
last_sync=started;buffer=b'';records=0
emit({'kind':'receiver-start','received_utc':utc(),'receiver_monotonic_s':started,'fsync_interval_s':1})
os.fsync(stream.fileno())
print('READY '+path,flush=True)
try:
    while True:
        if select.select([0],[],[],.5)[0]:
            data=os.read(0,65536)
            if not data:break
            buffer+=data
            if len(buffer)>4194304:raise ValueError('Sender record exceeds 4 MiB')
            while b'\n' in buffer:
                line,buffer=buffer.split(b'\n',1)
                if not line:continue
                row=json.loads(line)
                now=time.monotonic();last_data=now;records+=1
                row['received_utc']=utc();row['receiver_monotonic_s']=now
                last_seq=row.get('seq',last_seq)
                if row.get('kind')=='sample':last_sample=now
                if row.get('kind')=='end':sender_end=True
                emit(row)
        now=time.monotonic()
        if now-last_sync>=1:
            emit({'kind':'receiver-heartbeat','received_utc':utc(),'receiver_monotonic_s':now,
                  'last_data_age_s':None if last_data is None else round(now-last_data,3),
                  'last_sample_age_s':None if last_sample is None else round(now-last_sample,3),
                  'last_sender_seq':last_seq,'sender_records':records})
            os.fsync(stream.fileno());last_sync=now
finally:
    emit({'kind':'receiver-end','received_utc':utc(),'sender_end_seen':sender_end,
          'partial_bytes':len(buffer),'sender_records':records})
    os.fsync(stream.fileno());stream.close()
'''


def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def process_sample(path, with_wait=True):
    raw = read(path / 'stat')
    if not raw:
        return None
    fields = raw[raw.rfind(')') + 2:].split()
    if len(fields) < 22:
        return None
    return {'pid': int(path.name), 'name': raw[raw.find('(') + 1:raw.rfind(')')],
            'state': fields[0], 'ppid': int(fields[1]), 'cpu_ticks': int(fields[11]) + int(fields[12]),
            'start_ticks': int(fields[19]), 'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE'),
            'threads': int(fields[17]), 'wait': read(path / 'wchan') if with_wait else None,
            'minor_faults': int(fields[7]), 'major_faults': int(fields[9])}


def gpu_engines(path):
    clients = {}
    try:
        for fd in (path / 'fd').iterdir():
            try:
                if not os.readlink(fd).startswith('/dev/dri/'):
                    continue
            except OSError:
                continue
            data = read(path / 'fdinfo' / fd.name)
            if not data:
                continue
            fields = dict(line.split(':', 1) for line in data.splitlines() if ':' in line)
            client = fields.get('drm-client-id')
            if client is not None:
                clients[(fields.get('drm-pdev'), client)] = {
                    key.removeprefix('drm-engine-'): int(value.split()[0])
                    for key, value in fields.items() if key.startswith('drm-engine-') and value.strip().endswith(' ns')}
    except OSError:
        pass  # The process may exit while descriptors are being read.
    return {engine: sum(values.get(engine, 0) for values in clients.values())
            for engine in {key for values in clients.values() for key in values}}


def process_samples(previous=None):
    result, top, current = [], [], {}
    now = time.monotonic()
    full_scan = previous is None or now - previous.get('full_scan', 0) >= 5
    # ponytail: discover processes every 5 s, track graphics/top consumers at 1 Hz; short-lived jobs need event tracing.
    paths = Path('/proc').iterdir() if full_scan else (Path('/proc') / str(pid) for pid in previous.get('watched', []))
    for path in paths:
        if not path.name.isdigit():
            continue
        if previous is None and read(path / 'comm') not in ('Hyprland', 'qs', 'quickshell'):
            continue
        info = process_sample(path, with_wait=previous is None)
        if info is None:
            continue
        graphic = info['name'] in ('Hyprland', 'qs', 'quickshell')
        if graphic and previous is not None:
            info['wait'] = read(path / 'wchan')
        if previous is not None:
            current[info['pid']] = (info['start_ticks'], info['cpu_ticks'], now)
            old = previous.get('processes', {}).get(info['pid'])
            elapsed = now - (old[2] if old and len(old) > 2 else previous.get('time', now))
            percent = max(0, info['cpu_ticks'] - old[1]) / os.sysconf('SC_CLK_TCK') / elapsed * 100 if old and old[0] == info['start_ticks'] and elapsed > 0 else 0
            info['cpu_percent'] = round(percent, 2)
            info['cpu_interval_s'] = round(elapsed, 3)
            top.append({key: info[key] for key in ('pid', 'ppid', 'name', 'cpu_percent', 'cpu_interval_s', 'rss_bytes', 'major_faults')})
        if not graphic:
            continue
        render_threads = []
        try:
            threads = (path / 'task').iterdir() if full_scan else (path / 'task' / str(tid) for tid in previous.get('render_threads', {}).get(info['pid'], []))
            for thread in threads:
                if read(thread / 'comm') == 'QSGRenderThread':
                    value = process_sample(thread)
                    if value is not None:
                        render_threads.append(value)
        except OSError:
            pass
        info['render_threads'] = render_threads
        if full_scan:
            # Only session identifiers: never dump the complete environment or argv.
            raw = read(path / 'environ') or ''
            info['session_env'] = {key: value for entry in raw.split('\0') if '=' in entry
                                   for key, value in [entry.split('=', 1)] if key in
                                   ('XDG_SESSION_ID', 'XDG_VTNR', 'XDG_RUNTIME_DIR', 'WAYLAND_DISPLAY', 'HYPRLAND_INSTANCE_SIGNATURE')}
            try:
                # ponytail: snapshot at most 32 graphics threads every 5 s;
                # scheduler tracing is needed for shorter stalls or larger thread pools.
                info['thread_states'] = [item for thread in sorted((path / 'task').iterdir())[:32]
                                         if (item := process_sample(thread)) is not None]
            except OSError:
                info['thread_states'] = None
        if previous is not None:
            info['gpu_engine_ns'] = gpu_engines(path)
        result.append(info)
    top = sorted(top, key=lambda item: item['cpu_percent'], reverse=True)[:8]
    if previous is not None:
        if full_scan:
            previous.update(full_scan=now, processes=current)
        else:
            previous['processes'].update(current)
        previous.update(time=now, watched=list({item['pid'] for item in result + top}),
                        render_threads={item['pid']:[t['pid'] for t in item['render_threads']] for item in result})
    for item in top:
        if item['name'] in ('python', 'python3', 'bash', 'sh'):
            try:
                args = (Path('/proc') / str(item['pid']) / 'cmdline').read_bytes().split(b'\0')
                if len(args) > 1 and args[1] and not args[1].startswith(b'-'):
                    item['script'] = Path(os.fsdecode(args[1])).name
            except OSError:
                pass
    return result, top


def hyprland_log_updates(positions):
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
    updates = []
    current = {}
    logs = list((runtime / 'hypr').glob('*/hyprland.log'))
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
    data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    logs.append(data / 'sddm/wayland-session.log')
    runs = state / 'end4-pC/diagnostics/20261114-frame-pipeline/stage-profile/runs'
    # The two latest runs include a current attempt and its immediately previous one.
    for run in sorted(runs.glob('*'), reverse=True)[:2]:
        logs.extend(run.glob('*-hyprland.log'))
        logs.extend(run.glob('*-fixture.log'))
    for path in logs:
        try:
            with path.open('rb') as stream:
                info = os.fstat(stream.fileno())
                identity = (info.st_dev, info.st_ino)
                previous = positions.get(str(path))
                # ponytail: cap initial/per-tick reads at 64 KiB/file; use a dedicated reader if sustained logging exceeds this rate.
                offset = previous[2] if previous and previous[:2] == identity and previous[2] <= info.st_size else max(0, info.st_size - 65536)
                stream.seek(offset)
                data = stream.read(65536)
                current[str(path)] = (*identity, stream.tell())
                if data:
                    updates.append({'kind': 'hyprland-log' if path.name == 'hyprland.log' else 'session-log',
                                    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                    'file': str(path), 'offset': offset, 'remaining_bytes': max(0,info.st_size-stream.tell()),
                                    'text': data.decode('utf-8', errors='replace')})
        except OSError:
            pass  # A compositor may exit or replace its log while we read it.
    positions.clear()
    positions.update(current)
    return updates


def session_snapshot():
    try:
        sessions = json.loads(subprocess.check_output(['loginctl', 'list-sessions', '--json=short', '--no-pager'],
                              text=True, stderr=subprocess.PIPE, timeout=1))
        details = []
        for session in sessions[:8]:
            if session.get('uid') != os.getuid():
                continue
            raw = subprocess.check_output(['loginctl', 'show-session', str(session['session']),
                    '-p', 'Id', '-p', 'User', '-p', 'Type', '-p', 'State', '-p', 'Active', '-p', 'VTNr',
                    '-p', 'Leader', '-p', 'Service', '-p', 'Desktop'], text=True, stderr=subprocess.PIPE, timeout=1)
            details.append(dict(line.split('=', 1) for line in raw.splitlines() if '=' in line))
        return {'kind': 'sessions', 'sessions': sessions, 'details': details,
                'active_vt': read('/sys/class/tty/tty0/active')}
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return {'kind': 'sessions', 'error': str(error)}


def sample(previous=None):
    started = time.monotonic()
    processes, top = process_samples(previous)
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    gpu = []
    for device in Path('/sys/class/drm').glob('card*/device'):
        if not (device / 'gpu_busy_percent').exists():
            continue
        gpu.append({name: read(device / name) for name in (
            'gpu_busy_percent', 'mem_info_vram_used', 'mem_info_vram_total', 'mem_info_gtt_used',
            'power_dpm_force_performance_level', 'pp_dpm_sclk', 'pp_dpm_mclk',
            'gpu_reset_counter', 'power/runtime_status', 'current_link_speed', 'current_link_width')})
        gpu[-1]['device'] = str(device)
        gpu[-1]['temperature_millidegrees'] = [read(path) for path in device.glob('hwmon/hwmon*/temp1_input')]
    return {'kind': 'sample', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'uptime_s': float(Path('/proc/uptime').read_text().split()[0]),
            'memory_kib': {name: int(memory[name].split()[0]) for name in
                           ('MemAvailable', 'SwapFree', 'SwapTotal', 'Dirty')},
            'cpu_stat': {line.split()[0]: list(map(int, line.split()[1:])) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('cpu')},
            'pressure': {name: read('/proc/pressure/' + name) for name in ('cpu', 'memory', 'io')},
            'gpu': gpu, 'processes': processes, 'top_processes': top,
            'monotonic_s': started, 'sampling_ms': round((time.monotonic() - started) * 1000, 2),
            'power': [{key: read(device / key) for key in ('type', 'online', 'status', 'capacity', 'power_now')}
                      for device in Path('/sys/class/power_supply').iterdir()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', help='user@raspberry-IP; requires an already verified SSH host/key')
    parser.add_argument('--seconds', type=int, default=120)
    parser.add_argument('--local', type=Path, help='New private local JSONL file; includes performance counters')
    args = parser.parse_args()
    if bool(args.destination) == bool(args.local):
        parser.error('Specify an SSH destination or --local FILE')
    if (args.destination and args.destination.startswith('-')) or args.seconds <= 0:
        parser.error('Specify user@host and a positive --seconds value')

    filename = 'freeze-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8] + '.jsonl'
    # The remote file is new and private; the PC never relies on its own disk to retain the stream.
    command = 'exec python3 -u -c ' + shlex.quote(RECEIVER) + f' "$HOME/.local/state/end4-pC/{filename}"'
    receiver = None
    if args.local:
        args.local.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        output = os.fdopen(os.open(args.local, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', buffering=1)
    else:
        receiver = subprocess.Popen(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                                     '-o', 'ConnectTimeout=5', '-o', 'ServerAliveInterval=5',
                                     '-o', 'ServerAliveCountMax=2', args.destination, command],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                                    start_new_session=True)
        output = receiver.stdin
    journal = None
    worker = None
    events = None
    event_worker = None
    failed = threading.Event()
    lock = threading.Lock()
    log_positions = {}
    sequence = 0
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)

    def emit(value):
        nonlocal sequence
        with lock:
            sequence += 1
            value = {'seq': sequence, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'monotonic_s': time.monotonic(), **value}
            output.write(json.dumps(value, ensure_ascii=True) + '\n')
            output.flush()

    def kernel_messages():
        try:
            for line in journal.stdout:
                emit({'kind': 'kernel', 'line': line.rstrip('\n')})
        except OSError:
            failed.set()

    def session_messages():
        try:
            for line in events.stdout:
                try:
                    row = json.loads(line)
                except ValueError:
                    emit({'kind': 'reader-warning', 'reader': 'session-journal', 'error': 'Invalid journal JSON'})
                    continue
                emit({'kind': 'session-journal', **{key: row[key] for key in
                     ('__REALTIME_TIMESTAMP', '__MONOTONIC_TIMESTAMP', '_BOOT_ID', '_PID', '_UID', '_COMM',
                      '_SYSTEMD_UNIT', '_SYSTEMD_USER_UNIT', 'SYSLOG_IDENTIFIER', 'PRIORITY', 'MESSAGE') if key in row}})
        except OSError:
            failed.set()

    try:
        if receiver is not None:
            if not select.select([receiver.stdout], [], [], 15)[0]:
                raise RuntimeError('No acknowledgement from the remote recorder; collection was not started')
            ready = receiver.stdout.readline().strip()
            if not ready.startswith('READY '):
                raise RuntimeError('SSH recorder did not open its log; collection was not started')
            print('Remote log: ' + ready[6:], flush=True)
        else:
            print('Local log: ' + str(args.local), flush=True)
        emit({'kind': 'start', 'version': 2,
              'recorder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'kernel': os.uname().release, 'boot_id': read('/proc/sys/kernel/random/boot_id'),
              'seconds': args.seconds, 'sample_interval_s': 1,
              'clock_ticks_per_second': os.sysconf('SC_CLK_TCK'), 'performance': True,
              'clocksource': read('/sys/devices/system/clocksource/clocksource0/current_clocksource'),
              'watchdog': read('/proc/sys/kernel/watchdog'), 'nmi_watchdog': read('/proc/sys/kernel/nmi_watchdog'),
              'sysrq': read('/proc/sys/kernel/sysrq'),
              'firmware': {name: read('/sys/class/dmi/id/' + name) for name in
                           ('sys_vendor', 'product_name', 'bios_vendor', 'bios_version', 'bios_date')}})
        # A user service starts after login: retain evidence from the preceding boot too.
        try:
            tail = subprocess.check_output(['journalctl', '--boot=-1', '--dmesg', '--lines=120',
                       '--output=json', '--no-pager'], text=True, stderr=subprocess.PIPE, timeout=2)
            emit({'kind': 'previous-boot-kernel', 'journal_jsonl': tail[-131072:], 'truncated': len(tail) > 131072})
        except (OSError, subprocess.SubprocessError) as error:
            emit({'kind': 'previous-boot-kernel', 'error': str(error)})
        journal = subprocess.Popen(['journalctl', '--dmesg', '--follow', '--lines=50', '--output=short-monotonic', '--no-pager'],
                                   stdout=subprocess.PIPE, text=True, errors='replace', bufsize=1,
                                   start_new_session=True)
        worker = threading.Thread(target=kernel_messages, daemon=True)
        worker.start()
        events = subprocess.Popen(['journalctl', '--boot', '--follow', '--lines=100', '--output=json', '--no-pager',
                 '_COMM=Hyprland', '+', '_COMM=qs', '+', '_COMM=quickshell', '+', '_COMM=start-hyprland',
                 '+', '_COMM=systemd', '+', '_COMM=systemd-shutdow', '+', '_SYSTEMD_UNIT=sddm.service',
                 '+', '_SYSTEMD_UNIT=systemd-logind.service', '+', '_SYSTEMD_UNIT=systemd-oomd.service'],
                 stdout=subprocess.PIPE, text=True, errors='replace', bufsize=1, start_new_session=True)
        event_worker = threading.Thread(target=session_messages, daemon=True)
        event_worker.start()
        deadline = time.monotonic() + args.seconds
        previous = {}
        context = None
        next_sessions = 0
        while time.monotonic() < deadline:
            if (receiver is not None and receiver.poll() is not None) or failed.is_set():
                raise RuntimeError('Remote logging stopped; do not start a graphics test')
            if journal.poll() is not None:
                raise RuntimeError('Kernel log reader stopped; do not start a graphics test')
            if events.poll() is not None:
                raise RuntimeError('Session log reader stopped; do not start a graphics test')
            if time.monotonic() >= next_sessions:
                emit(session_snapshot())
                next_sessions = time.monotonic() + 5
            for update in hyprland_log_updates(log_positions):
                emit(update)
            try:
                config = json.loads((Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'illogical-impulse/config.json').read_text())
                background = config.get('background', {})
                state = {'wallpaper': background.get('wallpaperPath'), 'animation': background.get('wallpaperAnimation'),
                         'glass': background.get('widgets', {}).get('glass'), 'settings_style': config.get('settings', {}).get('style')}
                if state != context:
                    emit({'kind': 'context', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), **state})
                    context = state
            except (OSError, ValueError):
                pass
            emit(sample(previous))
            failed.wait(min(1, max(0, deadline - time.monotonic())))
        emit({'kind': 'end', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    except KeyboardInterrupt:
        emit({'kind': 'end', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reason': 'interrupted'})
        print('Collection interrupted; written records are retained.', flush=True)
    except Exception:
        try:
            emit({'kind': 'collector-error', 'traceback': traceback.format_exc(limit=8)})
        except OSError:
            pass  # Preserve the original failure if the SSH stream is already gone.
        raise
    finally:
        if journal is not None:
            journal.terminate()
            journal.wait(timeout=5)
        if worker is not None:
            worker.join(timeout=5)
        if events is not None:
            events.terminate()
            events.wait(timeout=5)
        if event_worker is not None:
            event_worker.join(timeout=5)
        try:
            if receiver is None:
                output.flush()
                os.fsync(output.fileno())
            output.close()
        except OSError:
            if receiver is None:
                raise
        if receiver is not None:
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
