#!/usr/bin/env bash
set -euo pipefail
umask 022
/home/xlini/.local/bin/omdrop off --force || true
sudo install -m 0644 -- /home/xlini/.config/quickshell/end4-pC/tools/airdrop/benchmarks/amsdu-9wy57hsk/radio.before.toml /etc/owly/.amsdu-9wy57hsk.toml
sudo mv -T -- /etc/owly/.amsdu-9wy57hsk.toml /etc/owly/radio.toml
sudo systemctl restart owlyd.service
