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
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-safety.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-popup-darkening.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-popup-bands.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-popup-frame.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-close-darkening.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-temporal-darkening.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-frost-reflections.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-initial-darkening.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-sidebar-initial-darkening.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-darker-coherence.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-bar-sections.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-fade-continuity.patch"
git -C "$task_build/source" apply "$task_script_dir/../../../patches/native-glass-reload-filters.patch"
python3 "$task_script_dir/../../../tests/native-glass-reload-filters-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/darker-fade-continuity-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/bar-section-darkening-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/native-glass-buffer-check.py" "$task_build/source" --pending-target
python3 "$task_script_dir/../../../tests/native-glass-safety-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/native-glass-fade-darkening-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/darker-temporal-check.py" "$task_build/source" "$task_script_dir/../../.."
python3 "$task_script_dir/../../../tests/native-glass-temporal-state-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/darker-reappearance-check.py" "$task_build/source" "$task_script_dir/../../.."
python3 "$task_script_dir/../../../tests/glass-reflections-check.py" "$task_build/source" "$task_script_dir/../../.."
python3 "$task_script_dir/../../../tests/native-glass-frost-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/native-glass-visibility-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/topbar-glass-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/glass-profiles-check.py" "$task_build/source"
python3 "$task_script_dir/../../../tests/bar-visibility-check.py" "$task_build/source"
# Rendering tests create a GL context, so run them only when explicitly requested.
if [[ ${HYPRGLASS_RENDER_TESTS:-0} == 1 ]]; then
    python3 "$task_script_dir/../../../tests/native-glass-shader-check.py" "$task_build/source"
    python3 "$task_script_dir/../../../tests/native-glass-bands-check.py" "$task_build/source"
fi
make -C "$task_build/source" -j1
mkdir -p -- "$task_output"
strip --strip-unneeded -o "$task_output/hyprglass.so" "$task_build/source/hyprglass.so"
python3 - "$task_output" "$task_script_dir/../../../patches/native-glass-temporal-darkening.patch" <<'PY'
import hashlib, json, pathlib, subprocess, sys
directory = pathlib.Path(sys.argv[1])
running = json.loads(subprocess.check_output(['hyprctl', 'version', '-j'], text=True))
headers = json.loads(subprocess.check_output(['Hyprland', '--version-json'], text=True))
assert running['abiHash'] == headers['abiHash'], 'Running compositor and installed headers differ'
metadata = {'abiHash': running['abiHash'], 'source': '22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5',
            'sha256': hashlib.sha256((directory / 'hyprglass.so').read_bytes()).hexdigest(),
            'buildRevision': 'reload-filter-cache-r46-2026-11-24', 'namespaceFilterReloadFix': True,
            'namespaceFilterReloadPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('native-glass-reload-filters.patch').read_bytes()).hexdigest(),
            'temporalDarkeningVisibility': True, 'temporalDarkeningWindowMs': 1500,
            'temporalDarkeningPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).hexdigest(),
            'qmlPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('glass-temporal-darkening-qml.patch').read_bytes()).hexdigest(),
            'frostReflectionsPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('native-glass-frost-reflections.patch').read_bytes()).hexdigest(),
            'frostReflectionsQmlPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('glass-frost-reflections-qml.patch').read_bytes()).hexdigest(),
            'initialDarkeningPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('native-glass-initial-darkening.patch').read_bytes()).hexdigest(),
            'fadeContinuity': True, 'fadeDamageTimer': True,
            'fadeContinuityPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('native-glass-fade-continuity.patch').read_bytes()).hexdigest(),
            'fadeContinuityQmlPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('glass-fade-continuity-qml.patch').read_bytes()).hexdigest(),
            'barSectionDarkening': True, 'barSectionSamples': [2, 3, 2], 'barSectionMean': True,
            'barSectionsPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('native-glass-bar-sections.patch').read_bytes()).hexdigest(),
            'darkerCoherencePatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('native-glass-darker-coherence.patch').read_bytes()).hexdigest(),
            'darkerCoherenceQmlPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('glass-darker-coherence-qml.patch').read_bytes()).hexdigest(),
            'sidebarInitialDarkeningPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('native-glass-sidebar-initial-darkening.patch').read_bytes()).hexdigest(),
            'initialDarkeningQmlPatchSha256': hashlib.sha256(pathlib.Path(sys.argv[2]).with_name('glass-initial-darkening-qml.patch').read_bytes()).hexdigest()}
(directory / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
print('Staged build:', directory)
PY
