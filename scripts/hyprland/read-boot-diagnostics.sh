#!/usr/bin/env bash
# Read existing boot files only; never open DRM devices or change the session.
set -euo pipefail
if (( EUID != 0 )); then
    echo 'Esegui questo script con sudo nel terminale attuale.' >&2
    exit 1
fi

echo '=== Voci GRUB (solo kernel e initrd) ==='
if [[ -r /boot/grub/grub.cfg ]]; then
    awk '/^[[:space:]]*(menuentry|linux|linuxefi|initrd|initrdefi)[[:space:]]/' /boot/grub/grub.cfg
else
    echo 'grub.cfg non leggibile'
fi

for image in /boot/initramfs-linux-lts.img /boot/initramfs-linux.img; do
    echo "=== Microcode iniziale: $image ==="
    # ponytail: read the early archive listing; do not extract the full initramfs.
    if ! lsinitcpio --early --list "$image" | awk 'BEGIN { IGNORECASE=1 } /microcode|authenticamd/ { found=1; print } END { if (!found) print "Nessuna voce microcode trovata nell’elenco" }'; then
        echo 'Elenco initramfs non disponibile'
    fi
done

for directory in /sys/fs/pstore /var/lib/systemd/pstore; do
    echo "=== $directory ==="
    if [[ -d "$directory" && -r "$directory" ]]; then
        ls -la -- "$directory"
        for record in "$directory"/*; do
            [[ -f "$record" ]] || continue
            echo "=== Record: $record (massimo 64 KiB) ==="
            head -c 65536 -- "$record"
            echo
        done
    else
        echo 'Directory assente o non leggibile'
    fi
done
