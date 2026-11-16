"""Offline inspection of our JSONL metadata or native, sanitised Owly PCAPs.

Reports advertised topology, not the master actually selected by the daemon.
No packets are transmitted; no payload or hostname is included in the report.
"""
import argparse
from collections import Counter
import importlib.util
import io
import json
import math
from pathlib import Path
import struct


spec = importlib.util.spec_from_file_location('awdl_channels', Path(__file__).with_name('bench-channels.py'))
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)


def pcap_records(stream):
    # ponytail: only Owly's LE/microsecond PCAP and channel/RSSI radiotap.
    # For arbitrary monitor captures use tshark, rather than grow a dissector here.
    header = stream.read(24)
    if len(header) != 24:
        raise ValueError('Truncated PCAP header')
    magic, major, minor, zone, sig, snaplen, linktype = struct.unpack('<IHHIIII', header)
    if (magic, major, minor, linktype) != (0xa1b2c3d4, 2, 4, 127) or not 1 <= snaplen <= 65535:
        raise ValueError('Expected native Owly PCAP (LE, microseconds, radiotap)')
    previous = -1
    while record := stream.read(16):
        if len(record) != 16:
            raise ValueError('Truncated PCAP record header')
        seconds, micros, size, original = struct.unpack('<IIII', record)
        timestamp = seconds + micros / 1e6
        if micros >= 1000000 or timestamp < previous or not 8 <= size <= snaplen or original != size:
            raise ValueError('Invalid, unordered or truncated PCAP record')
        previous = timestamp
        data = stream.read(size)
        if len(data) != size:
            raise ValueError('Truncated PCAP packet')
        version, pad, length, present = struct.unpack_from('<BBHI', data)
        expected = 8 + 4 * bool(present & 8) + bool(present & 32)
        if version or present & ~0x28 or length != expected or length > size:
            raise ValueError('Expected sanitised Owly radiotap (channel/RSSI only)')
        item = decoder.announcement(data[length:])
        if item is None:
            continue
        if present & 8:
            item['rx_frequency_mhz'] = struct.unpack_from('<H', data, 8)[0]
        if present & 32:
            item['rssi_dbm'] = struct.unpack_from('<b', data, length - 1)[0]
        yield {'source': 'pcap', 'observed_at': timestamp, **item}


def inspect(records):
    peers = {}
    sources = Counter()
    previous = None
    for item in records:
        timestamp = item['observed_at']
        mac = item['mac']
        if not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp):
            raise ValueError('Invalid observation timestamp')
        if not isinstance(mac, str) or len(mac.split(':')) != 6 or any(len(x) != 2 for x in mac.split(':')):
            raise ValueError('Invalid source MAC')
        bytes.fromhex(mac.replace(':', ''))
        if previous is not None and timestamp < previous:
            raise ValueError('Observations are not ordered; do not mix capture clocks')
        previous = timestamp
        sources[item.get('source', 'legacy-jsonl')] += 1
        peer = peers.setdefault(mac, dict(frames=0, first_at=timestamp, last_at=timestamp,
            election_v2_seen=False, election_frames=0, sync_frames=0,
            retry_flag_frames=0, retry_flag_observed_frames=0,
            channel_sequences=Counter(), advertised_sync_masters=Counter(), advertised_topology=[]))
        peer['frames'] += 1
        peer['last_at'] = timestamp
        peer['retry_flag_observed_frames'] += 'retry' in item
        peer['retry_flag_frames'] += bool(item.get('retry', False))
        peer['sync_frames'] += all(k in item for k in ('next_tu', 'aw_counter', 'sync_master'))
        if 'sync_master' in item:
            peer['advertised_sync_masters'][item['sync_master']] += 1
        if 'channels' in item:
            peer['channel_sequences'][','.join(map(str, item['channels']))] += 1
        election = None
        if 'election_v2' in item:
            peer['election_v2_seen'] = True
            election = dict(item['election_v2'], version=2)
        elif 'election_v1' in item and not peer['election_v2_seen']:
            election = dict(item['election_v1'], version=1, sync=mac)
        if election is not None:
            peer['election_frames'] += 1
            topology = {k: election[k] for k in ('version', 'master', 'sync', 'height', 'master_metric')}
            history = peer['advertised_topology']
            if not history or topology != history[-1]['state']:
                history.append(dict(at=timestamp, state=topology))
            peer['last_election'] = election
    return dict(sources=dict(sources), peers=peers, limitations=[
        'Topology is advertised by each source; actual daemon election/clock are unavailable here.',
        'Observation timestamps are capture/userspace times, not precise RF arrival times.',
        'Counts and retry flags do not measure radio loss, airtime or physical device count.',
        'Legacy JSONL lacks election fields; absent measurements are not evidence of stability.',
    ])


def self_test():
    frame = bytes.fromhex('d0000000ffffffffffff020000000002002500ff94730000')
    frame += b'\x7f\x00\x17\xf2\x08\x10\x03\x00' + bytes(8)
    v2 = bytes.fromhex('020000000009020000000008') + struct.pack('<IIII', 3214, 1, 522, 61) + bytes(8) + struct.pack('<I', 7)
    frame += struct.pack('<BH', 24, len(v2)) + v2
    packet = struct.pack('<BBHIHHb', 0, 0, 13, 0x28, 5220, 0x140, -26) + frame
    header = struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 127)
    data = header + struct.pack('<IIII', 0, 1000, len(packet), len(packet)) + packet
    records = list(pcap_records(io.BytesIO(data)))
    record, = records
    assert record['election_v2']['master_metric'] == 522
    assert (record['rssi_dbm'], record['rx_frequency_mhz'], record['observed_at']) == (-26, 5220, .001)
    mac = record['mac']
    v1 = dict(record, observed_at=.002, election_v1=dict(master=mac, height=0, master_metric=60))
    del v1['election_v2']
    report = inspect(records + [v1])
    assert len(report['peers'][mac]['advertised_topology']) == 1, 'v1 overwrote v2'
    assert report['peers'][mac]['last_election']['master_counter'] == 3214
    legacy = inspect([dict(mac=mac, observed_at=1, channels=[6] * 16)])['peers'][mac]
    assert legacy['advertised_topology'] == [] and legacy['retry_flag_observed_frames'] == 0
    assert inspect([json.loads(json.dumps(record))]) == inspect(records)
    bad_radiotap = bytearray(data)
    struct.pack_into('<I', bad_radiotap, 44, 1)
    for bad in (data[:20], data[:-1], data + b'x', bytes(bad_radiotap)):
        try:
            list(pcap_records(io.BytesIO(bad)))
        except ValueError:
            pass
        else:
            raise AssertionError('Malformed/unsupported PCAP accepted')
    for bad in ([dict(record, observed_at=float('nan'))], [v1, record]):
        try:
            inspect(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Bad capture timestamps accepted')
    print('PCAP/JSONL, election v2 precedence, missing metadata and malformed-input checks passed; offline only')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        elif args.capture:
            if args.capture.suffix == '.pcap':
                with args.capture.open('rb') as stream:
                    report = inspect(pcap_records(stream))
            else:
                with args.capture.open() as stream:
                    report = inspect(json.loads(line) for line in stream if line.strip())
            print(json.dumps(report, indent=2))
        else:
            parser.error('Provide a capture or --self-test')
    except (OSError, ValueError, KeyError, TypeError, struct.error) as error:
        parser.exit(1, f'Capture rejected: {error}\n')
