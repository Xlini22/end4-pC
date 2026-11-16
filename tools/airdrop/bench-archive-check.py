"""Check actual installed sender archive output offline; never open a radio/socket."""
from pathlib import Path
import ast
import hashlib
import io
import logging
import os
import shutil
import sys
import tempfile
import uuid
import zlib

import libarchive

# Compile only the installed encoder and upload method. A fake post receives the
# body in memory; none of the sender's discovery, identity or network code runs.
source = ast.parse(Path('/usr/lib/omdrop/airdrop-send.py').read_text())
encoder = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'dvzip_encode')
client = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'AirDropClient')
upload = next(n for n in client.body if isinstance(n, ast.FunctionDef) and n.name == 'send_upload')
namespace = {'io': io, 'os': os, 'uuid': uuid, 'log': logging.getLogger('archive-check'), 't': lambda: ''}
exec(compile(ast.Module(body=[encoder, upload], type_ignores=[]), '<installed sender archive methods>', 'exec'), namespace)


def check(path):
    class Offline:
        transfer_id = 'offline-check'
        def post(self, endpoint, body, headers):
            assert endpoint == '/Upload'
            self.payload = body.read()
            return True, b''
    offline = Offline()
    assert namespace['send_upload'](offline, [str(path)])
    payload = offline.payload
    cpio = bytearray()
    at = 0
    while at < len(payload):
        assert len(payload) - at >= 4
        header = int.from_bytes(payload[at:at + 4], 'big')
        size = header & 0x7fffffff
        at += 4
        assert size <= len(payload) - at
        block = payload[at:at + size]
        cpio.extend(block if header & 0x80000000 else zlib.decompress(block))
        at += size
    members = []
    with libarchive.memory_reader(bytes(cpio)) as archive:
        for entry in archive:
            assert entry.isreg and not entry.issym, 'Sender archived a link instead of file contents'
            members.append(b''.join(entry.get_blocks()))
    expected = path.read_bytes()
    assert members == [expected], 'Archived data differs from the source'
    assert len(payload) >= len(expected), 'Benchmark data unexpectedly compressible'
    print(f'{path}: regular file, {len(expected)} data bytes, {len(cpio)} CPIO bytes, {len(payload)} wire-body bytes, SHA-256 {hashlib.sha256(expected).hexdigest()}')


if sys.argv[1:]:
    for filename in sys.argv[1:]:
        check(Path(filename))
else:
    with tempfile.TemporaryDirectory(prefix='AirDrop archive check with spaces ') as directory:
        path = Path(directory) / 'airdrop-speed-8MiB.zip'
        shutil.copyfile('/tmp/end4-airdrop-speed/airdrop-speed-8MiB.zip', path)
        check(path)
        link = path.with_name('linked.zip')
        link.symlink_to(path)
        try:
            check(link)
        except AssertionError as error:
            assert 'archived a link' in str(error)
        else:
            raise AssertionError('The symlink regression was not detected')
    print('Real sender payload and symlink regression checks passed; no radio used')
