"""Observe AWDL channel announcements via nlmon, alongside the existing benchmark."""
from pathlib import Path
import json
import os
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time


def sequence(value):
    if len(value) < 6 or value[0] != 15 or value[2:6] != b'\x00\x03\xff\xff':
        raise ValueError('Unsupported channel sequence header')
    encoding = value[1]
    if encoding not in (0, 1, 3):
        raise ValueError('Unsupported channel encoding')
    size = 1 if encoding == 0 else 2
    if len(value) < 6 + 16 * size:
        raise ValueError('Truncated channel sequence')
    return list(value[6 + (encoding == 1):6 + 16 * size:size])


def announcement(frame):
    if len(frame) < 40 or struct.unpack_from('<H', frame)[0] & 0xfc != 0xd0:
        return None
    if frame[24:30] != b'\x7f\x00\x17\xf2\x08\x10' or frame[30] not in (0, 3):
        return None
    control, sequence_control = struct.unpack_from('<H', frame)[0], struct.unpack_from('<H', frame, 22)[0]
    result = {'mac': frame[10:16].hex(':'), 'subtype': frame[30],
              'sequence_number': sequence_control >> 4, 'fragment_number': sequence_control & 15,
              'retry': bool(control & 0x0800),
              'phy_tx': struct.unpack_from('<I', frame, 32)[0],
              'target_tx': struct.unpack_from('<I', frame, 36)[0]}
    at = 40
    while len(frame) - at >= 3:
        kind, length = struct.unpack_from('<BH', frame, at)
        at += 3
        if length > len(frame) - at:
            raise ValueError('Truncated AWDL TLV')
        value = frame[at:at + length]
        at += length
        if kind == 18:
            result['channels'] = sequence(value)
        elif kind == 4:
            if len(value) < 31:
                raise ValueError('Truncated sync parameters')
            result.update(next_channel=value[0], master_channel=value[3],
                          sync_master=value[21:27].hex(':'),
                          next_tu=struct.unpack_from('<H', value, 1)[0],
                          aw_period_tu=struct.unpack_from('<H', value, 5)[0],
                          af_period_tu=struct.unpack_from('<H', value, 7)[0],
                          aws_per_slot=value[27], aw_counter=struct.unpack_from('<H', value, 29)[0])
        elif kind == 5:
            if len(value) < 19:
                raise ValueError('Truncated election v1')
            result['election_v1'] = dict(master=value[5:11].hex(':'), height=value[3],
                master_metric=struct.unpack_from('<I', value, 11)[0],
                self_metric=struct.unpack_from('<I', value, 15)[0])
        elif kind == 24:
            if len(value) < 40:
                raise ValueError('Truncated election v2')
            result['election_v2'] = dict(master=value[:6].hex(':'), sync=value[6:12].hex(':'),
                **dict(zip(('master_counter', 'height', 'master_metric', 'self_metric'),
                           struct.unpack_from('<IIII', value, 12))),
                self_counter=struct.unpack_from('<I', value, 36)[0])
        elif kind == 21:
            if len(value) < 2:
                raise ValueError('Truncated version')
            result.update(version=value[0], devclass=value[1])
    if any(frame[at:]):
        raise ValueError('Nonzero truncated TLV tail')
    if 'channels' in result:
        result['slots_on_6'] = result['channels'].count(6)
        result['announced_fraction_on_6'] = result['slots_on_6'] / 16
    return result


def announcements(data):
    """Decode only generic-netlink FRAME events; unrelated traffic is discarded."""
    at = 0
    while len(data) - at >= 16:
        length, family = struct.unpack_from('=IH', data, at)
        if length < 16 or length > len(data) - at:
            raise ValueError('Truncated netlink message')
        message = data[at:at + length]
        at += (length + 3) & ~3
        if family < 16 or len(message) < 20 or message[16] != 59:
            continue
        attrs = {}
        pos = 20
        while len(message) - pos >= 4:
            size, kind = struct.unpack_from('=HH', message, pos)
            if size < 4 or size > len(message) - pos:
                raise ValueError('Invalid netlink attribute')
            attrs[kind & 0x3fff] = message[pos + 4:pos + size]
            pos += (size + 3) & ~3
        result = announcement(attrs.get(51, b''))
        if result is not None:
            for key, attr, fmt in (('ifindex', 3, '=I'), ('rx_frequency_mhz', 38, '=I'), ('rssi_dbm', 151, '=i')):
                if attr in attrs and len(attrs[attr]) == 4:
                    result[key] = struct.unpack(fmt, attrs[attr])[0]
            yield result


def listen(sock, ready):
    if os.geteuid() == 0:
        raise RuntimeError('The decoder must run unprivileged')
    ready_path = Path(ready)
    temporary = ready_path.with_suffix('.tmp')
    temporary.write_text(str(os.getpid()))
    temporary.replace(ready_path)
    # ponytail: allow 15 minutes for the guided prompts and four-minute send.
    # If the user returns later, rerun the capture rather than leaving it open.
    deadline = time.monotonic() + 900
    stop = False
    def stopped(signum, frame):
        nonlocal stop
        stop = True
    signal.signal(signal.SIGTERM, stopped)
    signal.signal(signal.SIGINT, stopped)
    invalid = seen = kept = 0
    with sock:
        while not stop and time.monotonic() < deadline:
            try:
                data, ancillary, flags, address = sock.recvmsg(262144)
                seen += 1
                if flags & socket.MSG_TRUNC:
                    invalid += 1
                    continue
                for item in announcements(data):
                    kept += 1
                    print(json.dumps({'source': 'nl80211', 'observed_at': time.time(),
                                      'observed_mono': time.monotonic(), **item}), flush=True)
                ready_path.with_suffix('.seen').touch(exist_ok=True)
            except socket.timeout:
                continue
            except ValueError:
                invalid += 1
    print(f'Capture finished; datagrams: {seen}; AWDL announcements: {kept}; rejected/truncated: {invalid}', file=sys.stderr)
    ready_path.with_suffix('.done').touch()


# Only this constant bootstrap runs as root. The repo decoder loads AFTER dropping
# groups, GID and UID; no repository code is imported with elevated privileges.
LISTENER = '''import runpy,socket,sys
s=socket.socket(fileno=int(sys.argv[3]));s.settimeout(0.5)
sys.argv=[sys.argv[1],'--listen',sys.argv[2]]
runpy.run_path(sys.argv[0],run_name='__main__',init_globals={'capture_socket':s})
'''
BOOTSTRAP = '''import os,socket,subprocess,sys
uid,gid=int(os.environ['SUDO_UID']),int(os.environ['SUDO_GID'])
assert uid>0
s=socket.socket(socket.AF_PACKET,socket.SOCK_DGRAM,socket.htons(3))
s.bind((sys.argv[2],0));s.settimeout(0.5)
os.setgroups([]);os.setgid(gid);os.setuid(uid)
base=os.path.dirname(sys.argv[3])
with open(os.path.join(base,'channels.jsonl'),'a') as output,open(os.path.join(base,'capture.log'),'a') as errors:
    subprocess.Popen([sys.executable,'-I','-c',LISTENER,sys.argv[1],sys.argv[3],str(s.fileno())],
                     pass_fds=(s.fileno(),),stdin=subprocess.DEVNULL,stdout=output,stderr=errors,start_new_session=True)
'''.replace('LISTENER', repr(LISTENER))


def main(tcp_rto=False, discovery=False):
    cli = os.environ.get('OMDROP_CLI', str(Path.home() / '.local/bin/omdrop'))
    status = json.loads(subprocess.check_output([cli, 'status', '--json'], text=True))
    if status.get('receiving') is not False or status.get('visible') is not False:
        raise RuntimeError('Spegni AirDrop dal widget prima della prova.')
    base = Path(os.environ.get('OMDROP_BENCH_DIR', '/tmp/end4-airdrop-speed'))
    capture = Path(tempfile.mkdtemp(prefix='channels-', dir=base))
    ready = capture / 'ready'
    iface = f'odcap{os.getpid()}'
    created = False
    benchmark = None
    print('PROVA SEQUENZA CANALI: nessuna configurazione radio modificata.', flush=True)
    if tcp_rto:
        print('Variante TCP: RTO minimo 1000 ms solo su awdl0; rimosso alla chiusura della prova.', flush=True)
    print('Registra solo annunci AWDL, senza contenuto dei file. Serve sudo per il monitor Netlink.', flush=True)
    print(f'Log privati: {capture}', flush=True)
    if not discovery:
        input('Premi Invio per preparare la cattura; poi il benchmark aspettera ancora prima della radio: ')
    subprocess.run(['sudo', '-v'], check=True)
    try:
        subprocess.run(['sudo', '-n', '/usr/bin/ip', 'link', 'add', iface, 'type', 'nlmon'], check=True)
        created = True
        subprocess.run(['sudo', '-n', '/usr/bin/ip', 'link', 'set', iface, 'up'], check=True)
        with (capture / 'channels.jsonl').open('w') as output, (capture / 'capture.log').open('w') as errors:
            # Authenticate in this terminal; detach only AFTER dropping privileges.
            try:
                subprocess.run(['sudo', '-n', '/usr/bin/python3', '-I', '-c', BOOTSTRAP,
                                str(Path(__file__).resolve()), iface, str(ready)], check=True,
                               stdin=subprocess.DEVNULL, stdout=output, stderr=errors, timeout=10)
            except subprocess.CalledProcessError as error:
                raise RuntimeError(f'Avvio cattura fallito: leggi {capture / "capture.log"}') from error
        deadline = time.monotonic() + 10
        while not ready.exists():
            if time.monotonic() >= deadline:
                raise RuntimeError(f'Cattura non pronta: leggi {capture / "capture.log"}')
            time.sleep(0.1)
        subprocess.run(['/usr/bin/iw', 'dev'], check=True, stdout=subprocess.DEVNULL)
        deadline = time.monotonic() + 3
        while not ready.with_suffix('.seen').exists():
            if time.monotonic() >= deadline:
                raise RuntimeError(f'Nessun messaggio Netlink valido osservato: leggi {capture / "capture.log"}')
            time.sleep(0.1)
        print('Precontrollo superato: cattura attiva e messaggi Netlink ricevuti.', flush=True)
        before = set(base.glob('run-*'))
        command = [sys.executable, str(Path(__file__).with_name('bench-discovery.py')), '--observe'] if discovery else [
            'bash', str(Path(__file__).with_name('bench-speed.sh')), '--tcp']
        benchmark = subprocess.Popen(command,
            env={**os.environ, 'OMDROP_BENCH_FIXED_WIFI': '1', 'OMDROP_BENCH_NO_PAUSE': '1',
                 'OMDROP_BENCH_RTO_MIN': '1000' if tcp_rto else '0',
                 'OMDROP_BENCH_VARIANT': 'discovery' if discovery else 'rto-min=1000ms' if tcp_rto else os.environ.get('OMDROP_BENCH_VARIANT', 'channel-sequence')})
        result = benchmark.wait()
        for run in set(base.glob('run-*')) - before:
            (run / 'channel-capture.path').write_text(str(capture.resolve()) + '\n')
        if ready.with_suffix('.done').exists():
            raise RuntimeError(f'Cattura terminata prima del benchmark: leggi {capture / "capture.log"}')
        return result
    finally:
        if benchmark is not None and benchmark.poll() is None:
            benchmark.terminate()
            try:
                benchmark.wait(timeout=10)
            except subprocess.TimeoutExpired:
                benchmark.kill()
                benchmark.wait()
            try:
                subprocess.run([cli, 'off', '--force'], timeout=30, check=False)
            except (OSError, subprocess.TimeoutExpired) as error:
                print(f'Arresto AirDrop da verificare: {error}', file=sys.stderr)
        if ready.exists() and not ready.with_suffix('.done').exists():
            try:
                os.kill(int(ready.read_text()), signal.SIGTERM)
                deadline = time.monotonic() + 3
                while not ready.with_suffix('.done').exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                if not ready.with_suffix('.done').exists():
                    os.kill(int(ready.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass
        if created:
            subprocess.run(['sudo', '/usr/bin/ip', 'link', 'delete', iface], check=True)
        print(f'Cattura conclusa. Log: {capture}', flush=True)


def self_test():
    channels = [149] * 8 + [0] * 7 + [6]
    for encoding in (0, 1, 3):
        slots = bytes(channels) if encoding == 0 else b''.join(bytes((0, c) if encoding == 1 else (c, 81)) for c in channels)
        value = bytes((15, encoding, 0, 3, 255, 255)) + slots
        assert sequence(value) == channels
        frame = bytes.fromhex('d0000000ffffffffffff020000000002002500ff94730000') + b'\x7f\x00\x17\xf2\x08\x10\x03\x00' + bytes(8)
        frame += struct.pack('<BH', 18, len(value)) + value
        parsed = announcement(frame + b'\x00\x00')
        assert parsed['slots_on_6'] == 1 and parsed['announced_fraction_on_6'] == 1 / 16
        assert parsed['channels'] == channels
        sync = bytearray(31)
        sync[21:27] = bytes.fromhex('020000000009')
        struct.pack_into('<H', sync, 1, 20)
        struct.pack_into('<H', sync, 29, 401)
        timed = announcement(frame + struct.pack('<BH', 4, len(sync)) + sync)
        assert (timed['next_tu'], timed['aw_counter'], timed['phy_tx'], timed['target_tx']) == (20, 401, 0, 0)
        assert timed['sync_master'] == '02:00:00:00:00:09'
        sync_only = announcement(frame[:40] + struct.pack('<BH', 4, len(sync)) + sync)
        assert sync_only['next_tu'] == 20 and 'channels' not in sync_only
        v1 = bytearray(19)
        v1[3] = 2; v1[5:11] = bytes.fromhex('020000000009')
        struct.pack_into('<II', v1, 11, 510, 60)
        v2 = bytes.fromhex('020000000009020000000008') + struct.pack('<IIII', 3214, 1, 522, 61) + bytes(8) + struct.pack('<I', 7)
        tlv = lambda kind, data: struct.pack('<BH', kind, len(data)) + data
        elected = announcement(frame + tlv(24, v2) + tlv(5, v1) + tlv(21, bytes((16, 4))))
        assert elected['election_v1'] == dict(master='02:00:00:00:00:09', height=2, master_metric=510, self_metric=60)
        assert elected['election_v2'] == dict(master='02:00:00:00:00:09', sync='02:00:00:00:00:08',
            master_counter=3214, height=1, master_metric=522, self_metric=61, self_counter=7)
        assert (elected['version'], elected['devclass']) == (16, 4)
        repeated = bytearray(frame)
        struct.pack_into('<H', repeated, 0, 0x08d0)
        struct.pack_into('<H', repeated, 22, 0xfff3)
        parsed = announcement(repeated)
        assert (parsed['sequence_number'], parsed['fragment_number'], parsed['retry']) == (4095, 3, True)
        for kind, data in ((4, sync), (5, v1), (24, v2), (21, bytes((16, 4)))):
            try: announcement(frame + tlv(kind, data[:-1]))
            except ValueError: pass
            else: raise AssertionError('Truncated timing/election/version accepted')
        def attr(kind, data):
            item = struct.pack('=HH', 4 + len(data), kind) + data
            return item + bytes(-len(item) % 4)
        attrs = attr(3, struct.pack('=I', 9)) + attr(38, struct.pack('=I', 2437)) + attr(51, frame)
        message = struct.pack('=IHHII', 20 + len(attrs), 42, 0, 0, 0) + bytes((59, 0, 0, 0)) + attrs
        event, = announcements(message)
        assert event['ifindex'] == 9 and event['rx_frequency_mhz'] == 2437
        assert len(list(announcements(message + message))) == 2
        for bad in (value[:5], value[:-1], b'\x0e' + value[1:]):
            try: sequence(bad)
            except ValueError: pass
            else: raise AssertionError('Invalid sequence accepted')
        for bad in (frame[:-1], frame + b'\x01', message[:-1]):
            try:
                if bad == message[:-1]: list(announcements(bad))
                else: announcement(bad)
            except ValueError: pass
            else: raise AssertionError('Truncation accepted')
        assert announcement(b'not AWDL') is None
        assert not list(announcements(message[:16] + b'\x01' + message[17:]))
    from unittest.mock import patch
    from contextlib import redirect_stdout
    import io
    real_popen = subprocess.Popen
    with tempfile.TemporaryDirectory(prefix='channel check with spaces ') as directory:
        # Exercise the actual handoff after privilege drop, using a local socket
        # instead of a privileged radio socket. The bootstrap exits before input.
        probe_dir = Path(directory) / 'handoff'
        probe_dir.mkdir()
        ready = probe_dir / 'ready'
        receiver, sender = socket.socketpair(type=socket.SOCK_DGRAM)
        try:
            probe = 'import os,socket,subprocess,sys\ns=socket.socket(fileno=int(sys.argv[4]))\n' + BOOTSTRAP.split('os.setuid(uid)\n', 1)[1]
            process = real_popen([sys.executable, '-I', '-c', probe, str(Path(__file__).resolve()),
                                  'unused', str(ready), str(receiver.fileno())], pass_fds=(receiver.fileno(),))
            assert process.wait(timeout=5) == 0
            sender.send(message)
            deadline = time.monotonic() + 5
            while not ready.with_suffix('.seen').exists():
                assert time.monotonic() < deadline, 'Detached listener did not receive the socket'
                time.sleep(0.05)
            assert json.loads((probe_dir / 'channels.jsonl').read_text().splitlines()[0])['channels'] == channels
        finally:
            receiver.close()
            sender.close()
            if ready.exists():
                os.kill(int(ready.read_text()), signal.SIGTERM)
                deadline = time.monotonic() + 3
                while not ready.with_suffix('.done').exists():
                    assert time.monotonic() < deadline, 'Listener did not shut down'
                    time.sleep(0.05)
        for case in ('success', 'rto', 'discovery', 'busy', 'failed-start', 'failed-capture', 'failed-benchmark', 'interrupted'):
            base = Path(directory) / case
            base.mkdir()
            events = []
            def run(command, **kwargs):
                events.append(command)
                if command[:5] == ['sudo', '-n', '/usr/bin/ip', 'link', 'set'] and case == 'failed-start':
                    raise subprocess.CalledProcessError(1, command)
                if command[:6] == ['sudo', '-n', '/usr/bin/python3', '-I', '-c', BOOTSTRAP]:
                    assert not kwargs.get('start_new_session'), 'sudo must retain the authenticated session'
                    assert kwargs['stdin'] == subprocess.DEVNULL
                    if case == 'failed-capture': raise subprocess.CalledProcessError(1, command)
                    Path(command[-1]).write_text('999999')
                    Path(command[-1]).with_suffix('.seen').touch()
                return subprocess.CompletedProcess(command, 0)
            class Child:
                pid = 999999
                def __init__(self, command, **kwargs):
                    if case == 'discovery':
                        assert command == [sys.executable, str(Path(__file__).with_name('bench-discovery.py')), '--observe']
                    else:
                        assert command[0] == 'bash'
                    self.benchmark = True
                    self.done = False
                    if self.benchmark:
                        assert kwargs['env']['OMDROP_BENCH_FIXED_WIFI'] == '1'
                        assert kwargs['env']['OMDROP_BENCH_RTO_MIN'] == ('1000' if case == 'rto' else '0')
                        (base / 'run-test').mkdir()
                def poll(self):
                    return 0 if self.done else (1 if case == 'failed-capture' else None)
                def wait(self, **kwargs):
                    if self.benchmark and case == 'interrupted' and not self.done: raise KeyboardInterrupt
                    self.done = True
                    return 124 if self.benchmark and case == 'failed-benchmark' else 0
                def terminate(self):
                    self.done = True
                    events.append(['terminated-benchmark'])
            def stopped(pid, sig):
                for ready in base.glob('channels-*/ready'):
                    ready.with_suffix('.done').touch()
            with patch.dict(os.environ, {'OMDROP_BENCH_DIR': str(base)}), patch('builtins.input', return_value=''), \
                 patch.object(subprocess, 'check_output', return_value=json.dumps({'receiving':case == 'busy', 'visible':False})), \
                 patch.object(subprocess, 'run', side_effect=run), patch.object(subprocess, 'Popen', Child), \
                 patch.object(os, 'kill', side_effect=stopped) as kill, redirect_stdout(io.StringIO()):
                try:
                    result = main(tcp_rto=case == 'rto', discovery=case == 'discovery')
                    assert case in ('success', 'rto', 'discovery', 'failed-benchmark')
                    assert result == (124 if case == 'failed-benchmark' else 0)
                    assert (base / 'run-test' / 'channel-capture.path').exists()
                except (RuntimeError, KeyboardInterrupt, subprocess.CalledProcessError):
                    assert case not in ('success', 'rto', 'discovery', 'failed-benchmark')
                if case != 'busy':
                    assert any(c[:4] == ['sudo', '/usr/bin/ip', 'link', 'delete'] for c in events)
                if case in ('success', 'rto', 'discovery', 'failed-benchmark', 'interrupted'):
                    kill.assert_called_once_with(999999, signal.SIGTERM)
                if case == 'interrupted':
                    assert ['terminated-benchmark'] in events
                    assert any(c[-2:] == ['off', '--force'] for c in events)
                assert all(p.stat().st_mode & 0o077 == 0 for p in base.glob('channels-*'))
    print('AWDL parser, Netlink framing, private logs, monitor cleanup and failure checks passed; no radio used')


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        self_test()
    elif len(sys.argv) == 3 and sys.argv[1] == '--listen':
        listen(globals()['capture_socket'], sys.argv[2])
    elif sys.argv[1:] in ([], ['--rto-min'], ['--discovery']):
        def interrupted(signum, frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGHUP, interrupted)
        try:
            result = main(tcp_rto=sys.argv[1:] == ['--rto-min'], discovery=sys.argv[1:] == ['--discovery'])
        except KeyboardInterrupt:
            result = 130
        except Exception as error:
            print(f'ERRORE: {error}', file=sys.stderr)
            result = 1
        try:
            if os.environ.get('OMDROP_BENCH_NO_PAUSE') != '1': input('Premi Invio per chiudere: ')
        except (EOFError, KeyboardInterrupt): pass
        raise SystemExit(result)
    else:
        raise SystemExit('Usage: bench-channels.py [--self-test | --rto-min | --discovery]')
