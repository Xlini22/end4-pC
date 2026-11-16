#!/usr/bin/env bash
set -euo pipefail
umask 022
/home/xlini/.local/bin/omdrop off --force || true
sudo install -m 0644 -- /home/xlini/.config/quickshell/end4-pC/tools/airdrop/benchmarks/ack-ie6159wz/drivers.before.toml /etc/owly/.ack-ie6159wz.toml
sudo mv -T -- /etc/owly/.ack-ie6159wz.toml /etc/owly/drivers.toml
sudo systemctl restart owlyd.service
