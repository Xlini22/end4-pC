#!/usr/bin/env bash
# Install only after the two-way hardware test. Does not acquire the radio.
set -euo pipefail
[[ $# == 1 && -f "$1" ]] || { echo 'Uso: install.sh PACCHETTO.pkg.tar.zst' >&2; exit 2; }
[[ $(id -u) != 0 ]] || { echo 'Esegui come utente della sessione, non con sudo.' >&2; exit 2; }
[[ $(cat /sys/class/net/wlp2s0/device/vendor) == 0x168c && $(cat /sys/class/net/wlp2s0/device/device) == 0x0042 ]] || {
    echo 'Questa configurazione è stata collaudata solo sulla QCA9377 168c:0042.' >&2; exit 1;
}
project=$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")
state_dir=${XDG_STATE_HOME:-$HOME/.local/state}/omdrop
mkdir -p "$state_dir"
exec > >(tee -a "$state_dir/install.log") 2>&1
sudo -v
if systemctl is-active --quiet owlyd.service; then
    state=$(busctl --system get-property io.github.t4t5.Owly /io/github/t4t5/Owly io.github.t4t5.Owly.Radio1 State)
    [[ "$state" == 's "idle"' ]] || { echo 'Spegni AirDrop prima di installare il backend.' >&2; exit 1; }
    sudo systemctl stop owlyd.service
fi
sudo pacman -U --needed --noconfirm -- "$1"
for config in radio drivers; do
    if [[ -e /etc/owly/$config.toml && ! -e /etc/owly/$config.toml.before-quickshell ]]; then
        sudo cp -a "/etc/owly/$config.toml" "/etc/owly/$config.toml.before-quickshell"
    fi
done
sudo tee /etc/owly/radio.toml >/dev/null <<'CONFIG'
# QCA9377: trasferimenti iPhone <-> PC collaudati sul canale 6.
station = "wlp2s0"
allow_untested = true
country = "IT"
channels = [6]
CONFIG
sudo tee /etc/owly/drivers.toml >/dev/null <<'CONFIG'
[drivers.ath10k_pci]
status = "untested"
mode = "exclusive"
channels = [6]
reconnect_after_monitor = true
notes = "QCA9377 168c:0042: collaudo locale nei due versi con patch nl80211; Wi-Fi sospeso durante AirDrop."
CONFIG
sudo systemctl daemon-reload
"$project/omdrop-plugin/bin/omdrop" setup
"$project/omdrop-plugin/bin/omdrop" dir "$HOME/Downloads/AirDrop"
"$project/omdrop-plugin/bin/omdrop" doctor --json
python3 - "${XDG_CONFIG_HOME:-$HOME/.config}/illogical-impulse/config.json" <<'BAR_LAYOUT'
import json, os, stat, sys, tempfile
from pathlib import Path
path = Path(sys.argv[1]).resolve()
if not path.exists():
    print('Aggiungi AirDrop dalle impostazioni della barra di Quickshell.')
    raise SystemExit(0)
before = path.read_text()
settings = json.loads(before)
bar = settings.setdefault('bar', {})
layouts = bar.setdefault('layouts', {})
right = layouts.setdefault('rightLayout', ['sysTray', 'utilButtons', 'systemIcons', 'powerButton'])
assert isinstance(right, list) and all(isinstance(item, str) for item in right), 'Layout barra non valido'
island = bar.get('dynamicIsland', {})
used = [layouts.get(key, []) for key in ('leftLayout', 'middleLayout', 'rightLayout')]
used += [island.get(key, []) for key in ('leftWidgets', 'rightWidgets')]
if any('omdrop' in group for group in used) or island.get('centerWidget') == 'omdrop':
    print('AirDrop è già nel layout della barra.')
    raise SystemExit(0)
right.insert(right.index('systemIcons') if 'systemIcons' in right else len(right), 'omdrop')
with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as out:
    temp = Path(out.name)
    json.dump(settings, out, indent=4, ensure_ascii=False)
    out.write('\n')
try:
    temp.chmod(stat.S_IMODE(path.stat().st_mode))
    if path.read_text() != before:
        raise RuntimeError('La configurazione è cambiata durante il setup: aggiungi AirDrop dalle impostazioni della barra.')
    os.replace(temp, path)
finally:
    temp.unlink(missing_ok=True)
print('AirDrop aggiunto alla barra di Quickshell.')
BAR_LAYOUT
printf '%s\n' 'Backend installato. La radio resta spenta fino all attivazione di AirDrop.'
