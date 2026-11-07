#!/usr/bin/env bash
set -euo pipefail
task_script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
task_output=${1:?Usage: bash build.sh STAGING_DIRECTORY}
test "$(pkg-config --modversion hyprland)" = 0.55.4 || { echo 'This patch targets Hyprland 0.55.4.' >&2; exit 1; }
task_build=$(mktemp -d /tmp/hyprglass-build-XXXXXXXX)
trap 'rm -rf -- "$task_build"' EXIT
git clone --depth 1 --branch v0.6.4 https://github.com/hyprnux/hyprglass.git "$task_build/source"
test "$(git -C "$task_build/source" rev-parse HEAD)" = 22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5
git -C "$task_build/source" apply "$task_script_dir/live-background.patch"
python3 "$task_script_dir/../../../tests/native-glass-buffer-check.py" "$task_build/source"
make -C "$task_build/source" -j1
mkdir -p -- "$task_output"
strip --strip-unneeded -o "$task_output/hyprglass.so" "$task_build/source/hyprglass.so"
python3 - "$task_output" <<'PY'
import hashlib, json, pathlib, subprocess, sys
directory = pathlib.Path(sys.argv[1])
running = json.loads(subprocess.check_output(['hyprctl', 'version', '-j'], text=True))
headers = json.loads(subprocess.check_output(['Hyprland', '--version-json'], text=True))
assert running['abiHash'] == headers['abiHash'], 'Running compositor and installed headers differ'
metadata = {'abiHash': running['abiHash'], 'source': '22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5',
            'sha256': hashlib.sha256((directory / 'hyprglass.so').read_bytes()).hexdigest()}
(directory / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
print('Staged build:', directory)
PY
