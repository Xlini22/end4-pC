"""Run: python3 tests/recover-session-check.py. No desktop processes are started."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'scripts/hyprland/recover-session.py'
spec = importlib.util.spec_from_file_location('recover_session', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
instance = {'pid': 123, 'instance': 'test-instance', 'wl_socket': 'wayland-9'}


def scenario(instances, pids, shells, *, status=False, restart=False, failure=None):
    calls = []
    def command(args, env):
        calls.append(args)
        if args[:2] == ['hyprctl', 'instances']:
            return json.dumps(instances)
        assert env['HYPRLAND_INSTANCE_SIGNATURE'] == 'test-instance'
        assert env['WAYLAND_DISPLAY'] == 'wayland-9'
        if args[0] == 'hyprctl':
            if failure:
                raise failure
            return '[{"name":"eDP-1"}]'
        if args[:2] == ['qs', 'kill']:
            return ''
        assert args[:2] == ['qs', 'list']
        return json.dumps(shells.pop(0))
    with patch.object(m, 'hyprland_pids', return_value=pids), patch.object(m, 'command', side_effect=command), \
         patch.object(m.sys.stdin, 'isatty', return_value=True), patch.object(m.os, 'ttyname', return_value='/dev/tty3'), \
         patch.object(m.Path, 'read_text', return_value='XDG_SESSION_ID=2\0'), \
         patch.object(m.os, 'execvpe') as start, patch.object(m.subprocess, 'run') as run:
        try:
            m.recover(status, restart)
        except (RuntimeError, m.subprocess.TimeoutExpired):
            assert failure or (pids and not instances) or len(instances) > 1
            assert not start.called and not run.called
        return calls, start.call_args, run.call_args_list


calls, start, runs = scenario([], [], [])
assert start.args[:2] == ('start-hyprland', ['start-hyprland']) and not runs
assert 'WAYLAND_DISPLAY' not in start.args[2]
calls, start, runs = scenario([], [123], [])  # unresponsive compositor: no duplicate
assert start is None and not runs
calls, start, runs = scenario([instance, instance], [123], [])  # ambiguous: no arbitrary choice
assert start is None and not runs
calls, start, runs = scenario([instance], [123], [[{'pid': 456}]])
assert start is None and [r.args[0] for r in runs] == [['loginctl', 'activate', '2']]
calls, start, runs = scenario([instance], [123], [[], [{'pid': 789}]])
assert runs[0].args[0][0] == 'qs' and '--no-duplicate' in runs[0].args[0]
assert runs[-1].args[0] == ['loginctl', 'activate', '2']
calls, start, runs = scenario([instance], [123], [[{'pid': 456}], [], [{'pid': 789}]], restart=True)
assert ['qs', 'kill', '--pid', '456'] in calls and len(runs) == 2
calls, start, runs = scenario([instance], [123], [[{'pid': 456}]], status=True)
assert not runs and start is None
calls, start, runs = scenario([instance], [123], [], failure=m.subprocess.TimeoutExpired('hyprctl', 8))
assert not runs and start is None
print('Recovery checks passed: new session, reuse, missing QS, restart QS, status, ambiguous/stuck compositor.')
