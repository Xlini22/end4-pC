#!/usr/bin/env bash
# Local hardware benchmark; no driver, channel or identity settings are changed.
set -uo pipefail
if (( $# == 0 )); then tcp_only=0
elif (( $# == 1 )) && [[ "$1" == --tcp ]]; then tcp_only=1
else printf 'Uso: %s [--tcp]\n' "$0" >&2; exit 2
fi
rto_min=${OMDROP_BENCH_RTO_MIN:-0}
[[ "$rto_min" == 0 || "$rto_min" == 1000 ]] || { printf '%s\n' 'RTO di prova non valido.' >&2; exit 2; }
# Owly's status files must remain readable by its unprivileged clients.
# mktemp keeps each log directory private without changing the helper's umask.
umask 022
cli=${OMDROP_CLI:-"$HOME/.local/bin/omdrop"}
base=${OMDROP_BENCH_DIR:-/tmp/end4-airdrop-speed}
file="$base/airdrop-speed-8MiB.zip"
[[ -r "$file" && -f "$file" && ! -L "$file" ]] || { printf '%s\n' 'Lo ZIP di prova deve essere un file reale leggibile, non un collegamento.' >&2; exit 1; }
run=$(mktemp -d "$base/run-XXXXXXXX") || exit 1
exec > >(tee -i "$run/session.log") 2>&1
printf 'Log della prova: %s\n' "$run"
printf 'Variante: %s\n' "${OMDROP_BENCH_VARIANT:-baseline}"
printf '%s\n' "${OMDROP_BENCH_VARIANT:-baseline}" > "$run/variant.txt"
"$cli" status --json | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin).get("receiving") is False else 1)' || {
    printf '%s\n' 'Spegni AirDrop nel widget prima di iniziare.' >&2; exit 1;
}
connection=$(nmcli -g GENERAL.CON-UUID device show wlp2s0) || connection=
printf '%s\n' 'PROVA AIRDROP - 8 MiB di dati casuali' \
    'Il canale e la correzione della scheda restano quelli attuali.' \
    'Non avviare altri trasferimenti o cambiare il widget durante la prova.'
saved_recipient=
name_file="$(dirname "$(readlink -f "$0")")/benchmarks/device-name"
if [[ -r "$name_file" ]]; then IFS= read -r saved_recipient < "$name_file" || true; fi
read -r -p "Nome AirDrop iPhone${saved_recipient:+ [$saved_recipient]} (Invio per confermare): " recipient || exit 1
recipient=${recipient:-$saved_recipient}
[[ -n "${recipient//[[:space:]]/}" ]] || exit 1
printf '\n%s\n' \
    '1. Avvicina iPhone al PC (circa un metro), sbloccato.' \
    '2. Spegni Hotspot personale; lascia Wi-Fi e Bluetooth accesi.' \
    '3. Imposta AirDrop su Tutti per 10 minuti.' \
    'Il PC restera senza Internet; non serve collegarsi ad altre reti.' \
    'Alla richiesta accetta lo ZIP e salvalo in File, senza estrarlo.'
read -r -p 'Premi Invio quando sei pronto; la radio parte solo ora: ' || exit 1
if (( rto_min )); then sudo -v || exit 1; fi
"$cli" status --json | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin).get("receiving") is False else 1)' || exit 1
started=$(date --iso-8601=seconds)
tcp_pid=
link_pid=
route_added=0
cleanup() {
    trap - EXIT INT TERM HUP
    if [[ -n "$tcp_pid" ]]; then
        kill "$tcp_pid" 2>/dev/null || true
        wait "$tcp_pid" 2>/dev/null || true
        tcp_pid=
    fi
    if [[ -n "$link_pid" ]]; then
        kill "$link_pid" 2>/dev/null || true
        wait "$link_pid" 2>/dev/null || true
        link_pid=
    fi
    if (( route_added )); then
        sudo -n /usr/bin/ip -6 route delete fe80::/64 dev awdl0 metric 1 > "$run/rto-cleanup.log" 2>&1 \
            || printf '%s\n' 'Rimozione route di prova non completata: viene rimossa anche alla chiusura di awdl0.'
        ip -j -6 route show dev awdl0 > "$run/rto-restored.json" 2>/dev/null || true
        route_added=0
    fi
    cp /run/omdrop-owl/announce.log "$run/announce.log" 2>/dev/null || true
    "$cli" off --force || true
    journalctl --user -u airdrop-receiver.service --since "$started" --no-pager -o json > "$run/receiver.jsonl" 2> "$run/receiver-errors.log" || true
    journalctl -u owlyd.service --since "$started" --no-pager -o short-iso-precise > "$run/radio.log" 2>&1 || true
    printf '\nLog salvati in %s. AirDrop fermato.\n' "$run"
}
trap cleanup EXIT
trap 'exit 130' INT TERM HUP
ip -details link show > "$run/links-before.log" 2>&1 || true
ip -ts monitor link > "$run/links-events.log" 2>&1 &
link_pid=$!
ready=0
send_result=1
if "$cli" on -e 10m; then
    printf '%s\n' 'Attendo che radio e ricevitore siano pronti (massimo 30 secondi)...'
    deadline=$((SECONDS + 30))
    while (( SECONDS < deadline )); do
        if timeout 5 "$cli" status --json > "$run/status.json" \
            && python3 -c 'import json,sys; s=json.load(sys.stdin); sys.exit(0 if s.get("receiving") is True and s.get("visible") is True else 1)' < "$run/status.json" \
            && [[ -n "$(ss -H -ltn 'sport = :8771')" ]]; then
            ready=1
            break
        fi
        sleep 1
    done
fi
if (( ready && rto_min )); then
    if ip -j -6 route show dev awdl0 > "$run/rto-before.json" \
        && sudo -n /usr/bin/ip -6 route add fe80::/64 dev awdl0 metric 1 rto_min 1000ms; then
        route_added=1
        if ! ip -j -6 route show dev awdl0 > "$run/rto-applied.json" \
            || ! python3 -c 'import json,sys; routes=json.load(sys.stdin); sys.exit(0 if any(r.get("dst")=="fe80::/64" and r.get("metric")==1 and any(m.get("rto_min")==1000 for m in r.get("metrics",[])) for r in routes) else 1)' < "$run/rto-applied.json"; then
            ready=0
        else
            printf '%s\n' 'Prova TCP: RTO minimo di 1000 ms solo su awdl0, senza modificare la route originale.'
        fi
    else
        ready=0
    fi
fi
if (( ready )); then
    (
        trap - EXIT INT TERM
        trap 'exit' TERM
        # ponytail: 500 ms samples observe TCP counters, not individual packets.
        # Use a packet capture if per-packet timing is needed.
        for ((sample=0; sample<1200; sample++)); do
            printf '\nSAMPLE %s\n' "$(date --iso-8601=ns)"
            ss -tin '( dport = :8770 or sport = :8770 or dport = :8771 or sport = :8771 )' || break
            sleep 0.5
        done
    ) > "$run/tcp.log" 2>&1 &
    tcp_pid=$!
    printf '\n%s\n' 'INVIO PC -> IPHONE: ricerca e attesa di accettazione sono registrate separatamente.'
    printf '%s\n' 'Registro anche le statistiche TCP ogni mezzo secondo.'
    printf 'Limite complessivo invio: %s secondi.\n' "${OMDROP_BENCH_SEND_TIMEOUT:-240}"
    { TIMEFORMAT='TOTAL_SEND_SECONDS=%3R'; time timeout --kill-after=5s "${OMDROP_BENCH_SEND_TIMEOUT:-240}s" "$cli" send --verbose --wait 60 --to "$recipient" -- "$file"; } 2>&1 | tee -i "$run/send.log"
    send_result=${PIPESTATUS[0]}
    if (( send_result == 124 )); then printf '%s\n' 'Tempo massimo raggiunto: invio interrotto, avvio il ripristino.'; fi
else
    printf '%s\n' 'Radio, ricevitore o profilo di prova non pronti: nessun invio tentato. Conservo i log e ripristino il Wi-Fi.'
fi
printf 'Esito invio: %s (0 = completato).\n' "$send_result"
if (( send_result == 0 && !tcp_only )); then
    printf '\n%s\n' \
        'Ora su iPhone apri File e seleziona lo stesso airdrop-speed-8MiB.zip.' \
        'Condividi > AirDrop > scegli il PC. Non estrarre o modificare lo ZIP.' \
        'Aspetta che il telefono dica che il trasferimento e completato.'
    read -r -p 'Premi Invio quando lo ZIP e tornato al PC, o per terminare la prova: ' || true
fi
cleanup
if [[ ${OMDROP_BENCH_FIXED_WIFI:-0} == 1 ]]; then
    printf '\n%s\n' 'Riconnetto il PC alla rete Wi-Fi usata prima della prova.'
else
    printf '\n%s\n' 'Ora puoi riattivare Hotspot personale sull iPhone.'
fi
if [[ ${OMDROP_BENCH_FIXED_WIFI:-0} == 1 ]] || read -r -p 'Premi Invio dopo averlo riattivato per riconnettere il PC: '; then
    if [[ "$connection" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
        nmcli -w 30 connection up uuid "$connection" ifname wlp2s0 || printf '%s\n' 'Seleziona la tua rete dal pannello Wi-Fi.'
    fi
fi
printf '\n%s\n' 'Prova finita: torna alla chat. Non chiudere il terminale se ci sono errori.'
if [[ ${OMDROP_BENCH_NO_PAUSE:-0} != 1 ]]; then read -r -p 'Premi Invio per chiudere: ' || true; fi
exit "$send_result"
