"""Native desktop fallbacks keep received paths and URLs as individual arguments."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'bin/omdrop'


class DesktopTests(unittest.TestCase):
    def test_receiver_unit_passes_systemd_validation_with_spaces(self):
        template = (CLI.parents[1] / 'share/airdrop-receiver.service').read_text()
        with tempfile.TemporaryDirectory(prefix='omdrop unit ') as directory:
            unit = Path(directory) / 'airdrop-receiver.service'
            unit.write_text(template.replace('@PLUGIN_DIR@', directory))
            result = subprocess.run(['systemd-analyze', '--user', 'verify', '--man=no', str(unit)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_notification_and_browser_keep_literal_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for command, body in {
                'notify-send': "#!/bin/sh\nprintf 'default\\n'\n",
                'uwsm-app': '#!/usr/bin/python3\nimport json,os,sys\nwith open(os.environ["CALLS"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n',
            }.items():
                file = folder / command
                file.write_text(body)
                file.chmod(0o755)
            calls = folder / 'calls'
            env = {**os.environ, 'PATH': f'{folder}:/usr/bin', 'CALLS': str(calls),
                   'XDG_CONFIG_HOME': str(folder / 'config'),
                   'XDG_RUNTIME_DIR': str(folder / 'runtime')}
            received = folder / 'foto con spazi $(false).png'
            received.write_bytes(b'PNG')
            subprocess.run([str(CLI), 'act', 'notify-native', str(received)],
                           env=env, capture_output=True, check=True, timeout=10)
            self.assertEqual(json.loads(calls.read_text().splitlines()[-1]),
                             ['--', 'xdg-open', str(received)])
            url = 'https://example.org/?q=$(false)&x=a%20b'
            shortcut = folder / 'pagina.url'
            shortcut.write_text('[InternetShortcut]\nURL=' + url + '\n')
            subprocess.run([str(CLI), 'open-link', str(shortcut)],
                           env=env, capture_output=True, check=True, timeout=10)
            self.assertEqual(json.loads(calls.read_text().splitlines()[-1]),
                             ['--', 'xdg-open', url])


if __name__ == '__main__':
    unittest.main()
