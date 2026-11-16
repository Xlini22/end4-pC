# Passaggio di contesto AirDrop / Quickshell — 31 ottobre 2026

**STATO ATTUALE — 2 novembre2026:** integrazione LOCALE nel widget completata.
La CLI del widget ora passa da `/usr/lib/end4-airdrop-fast/omdrop` al backend
44/20 autonomo con MCS7/STBCoff/LDPCoff; driver candidati solo durante AirDrop,
originali ripristinati allo spegnimento. Ciclo reale on/off e postflight passati,
AirDrop attualmente off e rete104/80 ripristinata. Prova ZIP dalla UI ancora
da eseguire; A/B CLI precedente: media8,34s legacy contro6,33s HT7 (-24% upload).
I riferimenti sottostanti a «widget NON integrato» sono storici. Bundle/report:
`.airdrop-local-lab/widget-fast-20261101`. Kernel supportato6.18.36-1-lts;
nessun candidato installato come driver Wi-Fi ordinario/di boot.

**ULTIMO RISULTATO — 1 novembre2026:** AirDrop realmente riuscito SENZA
associazione al router sul44/20, driver ITv2 + backend esclusivo esistente.
ZIP8MiB PC→iPhone8,65s upload (13,224s CLI totale), iPhone→PC12,699s,
SHA256 identico. Sessione `channel44-backend-20261101/live-py0dklbo`.
Originali/radio/config ripristinati, test package rimosso; widget NON ancora
integrato. Restano crash/cambio rete/ripetibilità e confezionamento sicuro.
I precedenti «nessun trasferimento senza AP» descrivono fasi storiche.

**Aggiornamento hardware — 1 novembre2026:** collaudo radio autonomo
`driver-live-pss7ksxh` concluso exit0 e ripristino verificato. Con driver IT
v2, station NON associata:44 senzaNO_IR, IBSS44/20 a23dBm e monitor up sullo
stesso phy. RX monitor non provato: cattura passiva senza frequenze utili.
NESSUN trasferimento AirDrop senza AP ancora eseguito. Driver/backend
originali ripristinati, rete100/80 e AirDropoff; ora phy9/P2P0x900000002,
mai fissarli nel codice. Taint12288 fino al riavvio. Dettagli finali in fondo.

**Priorità più recente dell'utente:** ottenere il canale44 senza dipendere
dal router. Indagine in `channel44-autonomous-20261031/ANALISI.md`, riepilogo
in fondo. Non continuare automaticamente l'integrazione della variante
associata: prima va risolta l'autonomia radio.

**Chiarimento acquisito:** l'utente autorizza lo studio separato del driver
per il Paese reale IT, senza installarlo o caricarlo. Compilati stock e
variante QCA9377/IT in `channel44-autonomous-20261031/driver`. La successiva
autorizzazione ai test e gli esiti hardware sono nell'aggiornamento sopra e
in fondo; non fermarsi al precedente stato «nessun modulo attivato».

**Aggiornamento della ripresa:** l'utente non ha più il router44/20. Rete
attuale verificata: `ScapeWiFi STAR 5GHz`, canale100/80MHz, center5530;
44 è di nuovo noIR. Preparata e verificata solo in laboratorio la nuova
candidata `channel44-guarded-20261031` (dettagli in fondo). NON installata.
Il backend originale resta attivo e AirDrop spento. I vecchi helper v4
fissano wdev0x91, mentre ora P2P è0xa6: non rilanciarli invariati.

## Da leggere prima di agire

Utente: xlini, parla italiano. Workspace:
`/home/xlini/.config/quickshell/end4-pC`.

Lavoro attivo: rendere veloce e affidabile AirDrop sulla scheda Wi-Fi già
presente, integrato nel widget Quickshell. **Non creare PR, commit, branch o
push**: l'utente ha esplicitamente rimandato la PR. Il branch corrente,
verificato durante questo passaggio, è `latest`.

**Risultato principale: abbiamo finalmente completato trasferimenti veloci
in entrambi i sensi sul canale44, con router e station a20MHz. La variante
veloce è ancora sperimentale: NON è il backend attivo del widget.**

L'ultima richiesta operativa era eseguire tutte le prove necessarie prima
di perdere l'accesso al router con canale44 selezionabile. L'utente aveva
confermato iPhone disponibile e pronto ad accettare lo ZIP; poi ha cambiato
il router da80 a20MHz su nostra richiesta. Non presumere che quel router
sia ancora disponibile nella nuova chat: verificarlo prima di altre prove.

Ultima domanda prima del passaggio: confronto con tempi pubblicati nelle
repo, PR e issue. Risposta e riferimenti sono riepilogati in fondo.

## Regole di lavoro

- Seguire AGENTS.md: poche modifiche, niente dipendenze superflue,
  calibrazione sul vero hardware, un piccolo check eseguibile per logica
  non banale. Preservare tutte le modifiche estranee.
- Nessun subagent salvo richiesta esplicita o istruzione applicabile.
- Nessun avvio automatico di AirDrop nel widget: solo su richiesta utente.
- Non cambiare dominio radio, EEPROM o aggirare vincoli regolamentari.
  Chiarimento successivo esplicito: ammesso studio/build separato di una
  variante per IT reale con DB firmato/potenza/DFS/EEPROM preservati;
  NON ammessi installazione o caricamento in questa fase.
- Italia è il Paese fisico dichiarato dall'utente.
- Comandi host/GUI richiedono spesso esecuzione fuori sandbox. Questa non
  equivale a sudo/root: password sudo inserita dall'utente nel terminale.
- Non eseguire script/file del checkout come root. I test usano solo
  comandi letterali privilegiati e un daemon installato da pacchetto in
  /usr/lib. I decoder da file vengono caricati DOPO drop gruppi/GID/UID.
- Skill protocol-reverse-engineering usata per catture/analisi. Prima di
  nuova analisi protocollo leggere la skill disponibile nella sessione.
- Non eliminare log, sorgenti o file ricevuti dell'utente per fare spazio.

## Installazione e componenti

- Quickshell end4-pC, integrazione derivata da OmDrop:
  `https://github.com/netmojo-systems/omdrop-plugin`.
- Backend radio Owly: `https://github.com/t4t5/owly`.
- Due copie upstream locali: `omdrop-plugin/` e
  `omdrop-plugin-aggiornato/`. La licenza è stata verificata MIT in precedenza.
- Widget: `modules/ii/bar/Omdrop.qml` e `OmdropPopup.qml`.
- Icona trasparente: `assets/icons/airdrop-symbolic.svg`.
- Registrazione/impostazioni barra già parte delle modifiche locali.
- CLI attuale: `/home/xlini/.local/bin/omdrop`.
- Ricevitore: servizio utente `airdrop-receiver.service`.
- Daemon radio: servizio di sistema `owlyd.service`.
- Nome visibile PC: `archlinux`.
- Download: `/home/xlini/Downloads/AirDrop`.
- Documenti preesistenti: `PIANO-AIRDROP.md` (cronologia molto dettagliata),
  `PR-AIRDROP.md` (bozza storica, NON autorizza a creare una PR ora).
- Hardware locale, binari, log, identità e dati personali NON sono parte
  della modifica distribuibile del widget.

## Hardware e rete

- Qualcomm Atheros **QCA9377**, PCI **168c:0042**, driver **ath10k_pci**.
- Kernel del test: **6.18.36-1-lts**, phy0, station `wlp2s0`.
- MAC station: `10:63:c8:44:37:d5`.
- MAC AWDL sperimentale distinto: `12:63:c8:44:37:d5`.
- iPhone: nome esatto **fuckingProShit_iPhone**, richiesto dall'utente come
  destinatario da ricordare. Versione dichiarata iOS26.6, non verificata.
- Nome salvato privatamente in `tools/airdrop/benchmarks/device-name`.
- MAC AWDL iPhone osservato: `2a:53:2a:21:e5:90`.
- Router controllabile del test: SSID `TIM-28613063`,
  BSSID `52:59:43:6b:d8:d5`, UUID
  `fb352e05-d032-4995-8aec-46e31bc77dda`.
- Prima:44/80MHz, center5210; dopo cambio utente: **44/20MHz, center5220**.
- Altra rete TIM osservata: `TIM-28613021`, canale10, UUID
  `fd8e9a21-bd48-42f6-b495-fc0f5720190d`. Una prova è stata annullata perché
  la station era passata lì: controllare sempre la rete reale.
- Normalmente l'utente ha Starlink gen3; in passato usava hotspot dello
  stesso iPhone. Non assumere che quei collegamenti possano riprodurre44/20.
- TP-Link TL-MR150 e scheda Wi-Fi originale Flipper Zero non hanno risolto
  il requisito di un AP5GHz con canale44 selezionabile.
- P2P-device non-netdev locale: wdev `0x91`. Il suo bit running si legge
  sotto sudo in
  `/sys/kernel/debug/ieee80211/phy0/netdev:p2p-dev-wlp2s0/state` (bit0).
  Questo identificatore è locale e non va fissato in un'integrazione portabile.

## Stato ordinario ripristinato dopo i test

Ultimo postflight reale: originale attivo, AirDrop off, router44/20 collegato,
nessuna interfaccia temporanea o pacchetto diagnostico residuo.
Controllare nuovamente prima di modificare: l'utente può aver cambiato rete.

- Pacchetto originale: `owly-qca9377-fix 0.4.1-1`;
  frontend backend `omdrop-owl-bin 0.4.1-1`.
- Eseguibile originale `/usr/lib/owly-qca9377/owlyd`, SHA256:
  `47fa6c73dc4bcc3191c15594e76b6bffa9fd6629a16265ce37e5d12fb7db09f6`.
- `/etc/owly/radio.toml`, SHA256:
  `dc35804f22de653140b1c2563b5bc81a69008f24c2f0039d8f3124299e9dfb22`.
  Profilo originale: stationwlp2s0, allow_untested=true, countryIT, channels[6].
- `/etc/owly/drivers.toml`, SHA256:
  `b9278a9a3d426d601e1bbfc4044296eba871604625143d6a367430eb4de5f18f`.
  ath10k exclusive6, reconnect_after_monitor=true.
- Drop-in originale:
  `/usr/lib/systemd/system/owlyd.service.d/50-qca9377.conf`,
  ExecStart originale, `Environment=OWLY_RX_MGMT=1`.
- Variante veloce non installata permanentemente; il widget usa ancora il
  vecchio profilo6. Non dire che il widget ha già acquisito i tempi nuovi.

## Dove sono sorgenti, patch e prove

Il laboratorio è stato spostato per quota esaurita in /tmp:

```
/home/xlini/.config/quickshell/end4-pC/.airdrop-local-lab
/tmp/end4-airdrop-speed -> il percorso sopra
```

Directory privata0700 con `.gitignore` contenente `*`. Il symlink conserva
i vecchi percorsi degli script; non cancellarlo arbitrariamente. Se /tmp
è pulito dopo reboot, usare il percorso persistente e controllare i path
assoluti nei manifest prima di rilanciare.

Gruppo principale recente: **`channel44-live-ve0jg64e`**.

- `source/`: sorgente completo Owly0.4.1 candidato.
- `source/crates/owly-radio/src/injection/setup.rs`: setup sperimentale.
- `source/crates/owly-radio/tests/injection.rs`: check dedicato.
- `owly-qca-shared44.patch`: v3 PresenceShare.
- **`owly-qca-shared44-fixed.patch`**: v4 PresenceFixed, SHA256
  `608d85dc1777f5dccf30d2c14ac9ec2f17d1f425f33e7bca00a37a858f366512`.
- **`manifest-v4.json`**: provenienza, hash e path verificati.
- Pacchetto v4:
  `package-v4/owly-qca9377-diag-bench-0.4.1-4-x86_64.pkg.tar.zst`.
  SHA256 `c62569427988a5d6809778b3ef8ab93814f20adfb308853c64db03ff5a2c0056`.
- SHA256 binario candidato:
  `f9819c4ac07ce68af662ba94b348a565919870191457f5d419336a17f46ce95a`.
- `bench44-fixed-debug.py`: installazione temporanea, discovery/ZIP e rollback.
- `bench-channels-fixed-debug.py`: raccolta annunci AWDL metadata-only via
  nlmon; importazione decoder dopo abbandono privilegi.
- `bench-speed.sh`: test ZIP, TCP ogni500ms, guida operatore.
- `repeat-fixed44-bidirectional.sh`, `repeat-fixed44-receive.sh`: launcher.
- `trace-fixed44.py`, `trace-fixed44-transfer.py`: supervisor ftrace
  metadata-only riusato da `tools/airdrop/bench-driver.py`.
- `driver-fixed44-trace.txt`: discovery44/80, nessun traffico dati AWDL.
- `driver-fixed44-transfer-trace.txt` e relativo summary: primo ZIP44/20.
- `monitor-headers.py`: solo header802.11, niente payload salvati.
- **`analyze-transfer.py`**: analyzer offline con assert, nessuna radio.
- `p2p-pre.sh`, `p2p-post.sh`, `unit-check.py`: helper e verifiche rollback.
- `kernel/`: sorgenti kernel ufficiali consultati, non moduli modificati.

Target Cargo locale `.airdrop-channel44-target` nella root workspace,
ignorato con `.gitignore *`; può occupare circa400MB. Conservato per build
incrementali, non distribuibile. Cache Cargo:
`/tmp/end4-airdrop-review/cargo-home`.

## Come funziona la variante riuscita

Opt-in **OWLY_QCA_SHARED_IBSS=1**, ramo nuovo prima dei modi standard:

1. Verifica QCA9377/ath10k, station su5220, gateway raggiungibile,44 TX ammesso.
2. Mantiene station collegata al router; nessuna conversione della station.
3. Crea `owlyibss0`, MAC AWDL distinto, unmanaged, disabilita IPv6 soltanto
   su quella interfaccia effimera, up e join5220 HT20 sul BSSIDAWDL.
4. Aggiunge monitor passivo `owlymon0` con lo stesso MAC dell'IBSS.
5. OWLY_RX_MGMT riceve management da IBSS via nl80211; dati su monitor/awdl0.
6. Opt-in **OWLY_QCA_FIXED44=1**: PresenceFixed, AnnounceFIXED e richiesta
   no-ACK come nel profilo6 funzionante. Senza flag resta PresenceShare.
7. Riusa journal e rollback esistenti per interfacce/reconnect; nessuna API
   o Mode aggiuntiva. Include correzione sync-freshness descritta sotto.

Il P2P va fermato temporaneamente: altrimenti STA+IBSS dà EBUSY. Il test lo
gestisce con ExecStartPre/ExecStopPost nel drop-in temporaneo
`/run/systemd/system/owlyd.service.d/90-diag-bench.conf`.
Marker protetto `/run/owly/qca44-p2p-before`; cleanup rimuove monitor/IBSS
PRIMA di P2Pstart e verifica running1, anche dopo crash del daemon.

Pacchetto diagnostico separato `owly-qca9377-diag-bench`, installazione
originale conservata. Alla fine si rimuovono solo override/pacchetto
diagnostici e si riavvia il daemon originale. Le rimozioni pacman osservate
dall'utente durante i test riguardavano questo pacchetto temporaneo.

**Limiti del prototipo:** wdevP2P locale fissato, nessun controllo esplicito
larghezza20MHz nel Rust candidato, gestione perdita/cambio AP da completare.
Non installare questa variante come generica soluzione pronta senza tali
controlli. Con Shared80 o Fixed80 il setup era possibile ma AirDrop non
completava discovery/trasferimenti.

## Prove e risultati sul44

Prove native precedenti, tutte nel laboratorio:

- `channel44-router-amnvum_t`: dopo distacco station44 torna noIR, join
  correttamente saltato. Non un trasferimento fallito.
- `channel44-concurrent-rn4lbhtv`: STA associata + nuovaIBSS, upIBSS EBUSY.
- `channel44-p2p-7is57hi7`: confronto nello stesso setup:
  P2Prunning1 -> upEBUSY; stopP2P -> running0 -> up e join44 riusciti.
  Station44/80 e IBSS44/20 contemporanee per5s; cleanup verificato.
- Poi completato setup anche col monitor. Errore iniziale NM sul monitor
  corretto verificando direttamente interfaccia/up, non pretendendo che
  NM esponga un device monitor. Un tentativo annullato su rete2.4GHz.

Con AP/station44/80MHz:

- `transfer-qca44-9d23a3pk`: Share, utente non pronto, esclusa da confronto.
- `transfer-qca44-yqh5zu7p`: Share, ripetizione corretta, PC non compare
  sull'iPhone, nome peer non risolto. Timeout discovery, nessun file inviato.
- `discovery44debug-vmnl1qxt`: Share35s, annunci iPhone ricevuti, rx_data0.
- `discovery44fixed-u6n_n0u7`: Fixed35s, stesso esito. Il solo cambio
  PresenceShare→Fixed NON ha risolto il problema a80MHz.

Stesso pacchetto v4, dopo cambio router/station a **44/20MHz**:

| Gruppo | PC→iPhone, caricamento ZIP | Invio totale | Ritrasmissioni campionate |
| --- | ---: | ---: | ---: |
| transfer-qca44-ok3dswvp | 8,65s | 17,080s | 0,206% |
| transfer-qca44-niabxdjf | 9,18s | 14,494s | 0,249% |
| transfer-qca44-7jp50e2t | 9,44s | 15,987s | 0,283% |

ZIP: **8388736B**, SHA256
`ac2dbab130dd40c255993de77b844273f6871693fa18b8a051afe5a49be85b67`.
Tutti HTTP200; circa0,85–0,92MiB/s di file. Ricerca/consenso distinti dal
caricamento. Primo con trace driver, altri senza. RSSI−40/−41dBm.

Seconda prova: nessun ritorno richiesto eseguito dall'utente, NON un guasto.
Terza prova: ricevuti foto770860B e poi stesso ZIP dall'iPhone:

- File `/home/xlini/Downloads/AirDrop/airdrop-speed-8MiB 20.zip`.
- Ricezione→salvataggio **12,233s**, HTTP200.
- **SHA256 identico al file originale**, percorso con spazi gestito.
- Ultimo postflight con assert passato in
  `transfer-qca44-7jp50e2t/postflight.json`.

Ogni gruppo ha `manifest.json`, `analysis.json`, `phase` restored, `result`0,
radio.jsonl, directory run con send/session/TCP/receiver log, directory
channels con annunci decodificati. Non pubblicare i log grezzi: possono
contenere nomi personali e header identità; estrarre misure sanificate.

## Evidenze tecniche: non confondere fatti e ipotesi

- Prima del cambio20MHz, rx_action funzionava ma rx_data rimaneva0.
- Traccia Fixed80:1215TX ath10k, solo vdev0. Traccia primoZIP20:
  1130TX vdev0 +6975TX vdev1. Mappatura vdev non verificata separatamente.
- Nessun overrun/drop dei buffer CPU; istanza ftrace rimossa, parametri
  globali/debug_mask identici prima/dopo. Non è stata abilitata debug globale.
- Tutte le copie monitor precedenti erano PACKET_OUTGOING: provano
  consegna locale, NON successo RF/ACK. Decoder corretto: tx_failed null
  sulle copie outgoing. Non reinterpretare vecchi TXflags come completion.
- Kernel6.18.36 `ieee80211_monitor_start_xmit` usa chandef del contesto
  canale, verifica cfg80211_reg_can_beacon, può liberare frame restituendo
  NETDEV_TX_OK. Ipotesi: contesto80 include secondari ancora noIR, causando
  scarto prima di ath10k; a20 il problema sparisce. **Non ancora provato da
  tracing della decisione regolamentare**. Non dichiararlo causa certa.
- Sorgente ufficiale:
  https://raw.githubusercontent.com/gregkh/linux/v6.18.36/net/mac80211/tx.c
- Se serve verificarlo, simbolo `cfg80211_reg_check_beaconing` esiste;
  cfg80211_reg_can_beacon è wrapper inline. Nessun kprobe è stato aggiunto.
- Durante upload44 iPhone annuncia soprattutto15slot/16 sul44, rispetto a
 5slot/16 sul6 nelle recenti prove lente. Sono slot annunciati, non airtime.
- Il guadagno sul44 è ripetuto ma NON un A/B isolato del solo canale:
  rispetto al6 cambiano anche associazione, setupIBSS e larghezza.

## Contesto delle precedenti prove lente sul6

- Funzionavano già invio e ricezione, ma il medesimo ZIP talvolta impiegava
 111s e in altre prove molto di più. La variabilità coinvolgeva anche
 posizione del telefono e presenza di altri dispositivi Apple.
- Ultime prove controllate6: baseline154,17s e candidata sync144,81s;
 ritrasmissioni rispettivamente10,44% e9,49%, cwnd mediana5.
- Bug distinto verificato offline: dopo demozione del peer selezionato
 (master metric65/resetAW), il clock poteva essere applicato prima della
 rielezione periodica. Patch sync-freshness rivaluta l'elezione prima di
 applicare il clock quando cambiano i dati di elezione del peer selezionato.
- Patch repo `tools/airdrop/owly-awdl-sync-freshness.patch`; incorporata
 nella candidata44. Replay1206annunci mostra tre reset errati del baseline
 eliminati dalla patch;69test AWDL/sync/PCAP passati. Questo prova la
 correzione logica, non un beneficio di velocità generalizzabile.
- Artefatti: `transfer-diag-w6w8xo67`, `transfer-sync-_m1rp0jz`,
 `sync-build-sq3m0b7h`. Vecchi test pacing/RTO non risolvevano la lentezza;
 non reinstallare alla cieca varianti precedenti o ritestare6 da zero.

## Verifiche già eseguite e comandi utili

- Build release offline v3/v4 riuscite.
-18test ordinari injection, più check opt-in4casi (successo, monitorfail,
 IBSSrefused, wrongchannel); passato sia con Fixed che con Share.
- Helper P2P: errori/ripristino/marker/retry/ordine cleanup e paths con
 spazi verificati; systemd-analyze verify passato sul servizio candidato.
- Parser/capture self-check passato fuori sandbox (socket locali vietati
 nella sandbox, non è un errore del parser). Nessuna radio nel self-check.
- Analyzer offline passato per3upload e hash del ritorno; git diff --check
 passato. Nessuna PR/commit creata.

Analisi offline dalla root workspace:

```bash
python3 .airdrop-local-lab/channel44-live-ve0jg64e/analyze-transfer.py \
  .airdrop-local-lab/transfer-qca44-7jp50e2t \
  '/home/xlini/Downloads/AirDrop/airdrop-speed-8MiB 20.zip'
```

Per ricompilare solo se necessario, nella directory source candidata:

```bash
CARGO_HOME=/tmp/end4-airdrop-review/cargo-home \
CARGO_TARGET_DIR=/home/xlini/.config/quickshell/end4-pC/.airdrop-channel44-target \
cargo build --offline --locked --release -p owlyd -j2
```

Per il check radio opt-in usare lo stesso CARGO_HOME/TARGET e
`OWLY_QCA_SHARED_IBSS=1 OWLY_QCA_FIXED44=1 cargo test --offline --locked
-p owly-radio --test injection qca44_opt_in_setup_and_rollback -- --ignored`.
Non avviare test hardware senza controllare prima rete/radio/off/stato
P2P e disponibilità dell'utente; i launcher chiedono sudo e Invio locale.

## Stato Git da preservare

Branch `latest`. Già modificati, non ripulire o includere indiscriminatamente:

- modules/common/widgets/BarWidgetSwitcher.qml, BarWidgetSwitcherArea.qml
- modules/ii/bar/ClockWidget.qml, DiMedia.qml, DynamicIsland.qml,
  Resource.qml, Resources.qml, Visualizer.qml
- modules/ii/settings/pages/BarConfig.qml
- tests/activity-exit-check.py

Untracked preesistenti comprendono PIANO-AIRDROP.md, PR-AIRDROP.md,
widget/icon AirDrop, due cartelle OmDrop, tools/, testomdrop/island.
Il laboratorio e target sono ignorati localmente. Questo documento è
un'aggiunta di contesto locale, non un file da proporre automaticamente upstream.

## Confronto pubblico consultato il31ottobre2026

Fonti lette mediante connettore GitHub, inclusi commenti del maintainer.
Sono misure riferite da altri, con dispositivi/file/tempi diversi; non una
classifica controllata né risultati trasferibili direttamente allaQCA9377.

- Owly README: AX201, canale6, foto2,4MB in10–17s; il maintainer attribuisce
  parte della lentezza ai pochi slot AWDL disponibili sul6.
  https://github.com/t4t5/owly#known-issues
- PR85: RTL8188FTV sul6, ricezione foto2,57MB in75–80s (~32–35kB/s).
  https://github.com/t4t5/owly/pull/85
- PR58 **merged**: MT7612U sul149/HT40, video30MB da iPhone in47s senza
  accettare Block Ack,14s accettandolo; confronto dichiarato con altre
  impostazioni identiche. Richiede capacità hardware Block Ack, non basta
  annunciarla. Contesto vecchio OWL in C, non patch da applicare al Rust.
  https://github.com/t4t5/owly/pull/58
- PR62: MT7921 con driver modificato,2stream/VHT80 e aggregazione sul44:
  iPad→PC30,4MB in3–3,4s; PC→iPad10,2–11,6s; PDF71,3MB in4,96–6,49s.
  **Chiusa senza merge** perché superata dal rewriteRust, non per prova
  di prestazioni smentita. Non è il nostro hardware né backend stock.
  https://github.com/t4t5/owly/pull/62
  https://github.com/t4t5/owly/pull/62#issuecomment-6540779325
- Issue82: AX211 con mac80211 modificato e switchmode, canale149/BlockAck:
  video43MB in~17s,7,5MB in~4s. Nel commento il maintainer conferma anche
  sulla sua AX20144noIR senza station associata; una cella149 può avviarsi
  ma non garantisce che il suo iPhone la usi. Non assumere che149 risolva
  tutto. Il numero di slot cambia per scenario.
  https://github.com/t4t5/owly/issues/82
  https://github.com/t4t5/owly/issues/82#issuecomment-6369364514
- Issue38: MT7921 localmente modificata sul44, video30,4MB in17,339s
  fino agli ultimi dati,21,788s fino a stored/HTTP200; caso precedente alle
  ottimizzazioni dellaPR62.
  https://github.com/t4t5/owly/issues/38
- OmDropPR69: MT7922, driver ratefix locale/shared44,43,17MB in30,181s;
  PDF2,90MB in9,760s. Distingue upload/HTTP200 da scoperta/UI.
  https://github.com/netmojo-systems/omdrop-plugin/pull/69
- OmDropissue110: RTL8852AE,149, ricezione1MB in2,8s; sul6~60s per2MB.
  Hardware e Paese diversi, non copiare impostazioni regolamentari.
  https://github.com/netmojo-systems/omdrop-plugin/issues/110
- Nessun risultato QCA9377 emerso dalla ricerca mirata nelle issue Owly.

## Prossimi passi proposti, non ancora eseguiti

1. Consolidare44/20 come opzione hardware locale, con guard reale sulla
   larghezza/frequenza e messaggi comprensibili quando i prerequisiti mancano.
2. Gestire P2P senza wdev fissato, proprietà dello stato, crash/riavvio e
   perdita/cambio rete/AP. Preservare il profilo6 funzionante come fallback
   esplicito e non mentire sullo stato reale del ricevitore.
3. Integrare nel widget solo dopo questi controlli; evitare che basta il
   toggle ad attivare una variante fragile o interrompere la rete a sorpresa.
4. Se serve capire il blocco80, verificare direttamente il controllo
   regolamentare del chandef; non attribuirlo alla radio senza evidenza.
5. Ulteriore velocità: misurare rate effettivo e aggregazione/BlockAck sulla
   QCA9377. Verificare capacità reali prima di modificare annunci: le patch
   MediaTek2stream/VHT80 non sono portabili automaticamente alla nostra scheda.
6. Nessuna PR o pubblicazione finché l'utente non la richiede nuovamente.

Storia pregressa non prioritaria: interesse per foto personalizzata e
ContactsOnly; l'utente ha un Mac non a portata di mano. Non implementare
autenticazione Apple o considerare che salvare PC in rubrica risolva da
solo fiducia/visibilità: non è il lavoro attivo attuale.

## Ripresa: candidata protetta, router44/20 non più disponibile

- Letto integralmente questo documento; consultata la cronologia recente.
  L'utente chiede di continuare prove/test, senza branch/commit/PR/push.
- Nuovo gruppo privato `.airdrop-local-lab/channel44-guarded-20261031`:
  copia sorgenti v4 preservata separatamente, patch incrementale
  `owly-qca-shared44-guarded.patch`, binario release `owlyd`, README con
  comandi/limiti, manifest/hash, log test, checks.json e postflight.json.
  I sorgenti, la patch e il pacchetto v4 riusciti sono rimasti intatti.
- Implementati nella candidata: guard reale5220/20MHz/center5220/BSSID,
  controllo permesso TX e combinazione interfacce, P2P dinamico via dump
  nl80211 con identità wdev+MAC, stop/ripristino nel journal, ownership dello
  stato iniziale e ordine monitor/IBSS prima del riavvio P2P. Niente nuovo
  Mode, dipendenze o modifiche rate/BlockAck/dominio radio.
- Running P2P ancora da debugfs mac80211: richiede una sola voce p2p-dev
  sul phy; stato assente/illeggibile/ambiguo fa fallire in sicurezza. Non è
  supporto universale per tutti i driver. Bit reale non riletto in questa
  sessione e nessuno stop/start P2P reale eseguito.
- Supervisore1s rileva cambio AP/BSSID/profilo NM, frequenza/larghezza,
  permesso TX, P2P e perdita IBSS; emette Lost, poi owlyd chiude e ripristina.
  Non forza la vecchia rete se l'utente ne ha scelta un'altra/disconnessa.
  Poll non atomico col roaming, query potenzialmente più lente di1s:
  eventuale upgrade a eventi nl80211 prima di promettere arresto immediato.
- Errori delete/ripristino conservano il journal per retry. Corretto anche
  il servizio candidato: Release restituisce NoRadio se down fallisce;
  LastEnd e segnale idle includono recovery pending. Idle indica lease
  assente, non ripristino garantito; il widget dovrà esporre quel motivo.
- Verifiche finali passate:35 test libreria,18 ordinari injection,12 servizio
  D-Bus privato; matrice fake35 scenari sia Fixed sia Share. Preflight reale
  di sola lettura rifiuta100/80 e rileva P2P166/0xa6 coerente con iw. Build
  release offline e patch dry-run passati, Cargo.lock invariato.
- Nuova patch SHA256:
  `44e1d5fcade6b505ac0a686768d56fe93afdbeaa25ee0c870543c2289fb69182`.
  Nuovo binario SHA256:
  `e4ee2a3fa7e00191f8bf8e8376fb69990d37ae4df9ccb768d0804b39d4a190fb`.
- Nessun nuovo trasferimento, setup IBSS o cambio rete durante questa
  ripresa. Originale attivo, AirDropoff, tre hash originali invariati,
  pacchetto/override/marker diagnostici assenti, nessuna interfaccia residua.
- NON usare i vecchi launcher/helper v4 con questa candidata: doppia
  ownership P2P e vecchio daemon incompatibile coi nuovi step del journal.
  Nessun nuovo pacchetto/launcher hardware preparato. Il prossimo dovrà
  completare recovery con la candidata prima di ripristinare l'originale;
  continuano a valere niente codice checkout eseguito da root.
- Restano: collaudo privilegiato P2P/setup/teardown/crash/cambio AP reali
  su44/20, ZIP bidirezionale con hash, poi integrazione widget. Senza router
  adatto questi controlli hardware restano pendenti; non sostituirli con
  prove sul6. Motivo del blocco80 ancora non verificato.

## Priorità successiva: canale44 autonomo, indagine del driver

- L'utente vuole concentrarsi sull'indipendenza dal router «per forza».
  Nessuna promessa che sia ottenibile col driver/kernel attuale. Non
  confondere la candidata shared44 protetta con una variante già autonoma.
- Laboratorio privato `channel44-autonomous-20261031`, con ANALISI.md,
  sorgenti ufficiali del kernel6.18.36 e provenienza/hash in sources.json,
  snapshot.json, boot-country.jsonl e check-platform.py con self-test.
- Nuova evidenza reale dal boot: EEPROM regdomain0x6c, Country alpha2 00.
  È un profilo Atheros world roaming; regd.c applica CUSTOM_REG/STRICT_REG
  e NO_IR sul5GHz. Messaggi successivi0x817c/IT sono aggiornamenti della
  struttura del driver da Country IE, NON prova di scritture della EEPROM.
- Confermato nel sorgente: sia join IBSS sia monitor injection richiedono
  cfg80211_reg_can_beacon. Cambiare solo il widget, togliere il guard o
  eliminare IBSS non risolve il controllo monitor. NO_IR-relax generico
  non è una soluzione per IBSS/monitor e non è abilitato in questo kernel.
- GlobalIT già impostato, phy99passivo e44NO_IR. Database radio/firma
  presenti e pacman Qkk wireless-regdb:25file/0alterati. Il boot registra
  anche DB mancante all'avvio, ma non prova che manchi ora o sia la sola causa.
- Controllo guidato ACPI eseguito dall'utente:8tabelle DSDT/SSDT valide,
  nessun nome WRDD. Dati protetti letti da bootstrap letterale, decoder
  caricato soltanto dopo drop gruppi/GID/UID. Nessuna valutazione AML,
  nessuna tabella grezza salvata. Limite: ricerca nomi, non valutazione
  del namespace a runtime. Riepilogo in platform-*/acpi-summary.json/result0.
- Percorso nativo individuato per ulteriore valutazione:
  CONFIG_ATH_REG_DYNAMIC_USER_REG_HINTS, dipendente da
  CONFIG_CFG80211_CERTIFICATION_ONUS e CONFIG_EXPERT. Nel kernel corrente
  non abilitati. Il ramo esistente accetta il Paese indicato dall'utente
  e consulta le regole nazionali prima di adattare i flag; non è una
  normale opzione Owly, né una soluzione già verificata su questa scheda.
  Kconfig riserva l'uso a sistemi/Paesi/schede validati; non assumere
  automaticamente conformità o successo. Inizialmente nessuna variante;
  dopo il chiarimento compilata separatamente, mai attivata (vedi sotto).
- Chiarimento acquisito: «Sì, valutiamo la variante del driver per IT».
  Ammessi studio e compilazione separati con DB firmato/potenza/DFS/EEPROM
  preservati, senza installare/caricare. Nessuna autorizzazione a cambiare
  EEPROM, rimuovere arbitrariamente NO_IR o usare altri Paesi.
- Self-test diagnostico passato (tabelle valide/errate, assente vs ignoto,
  bootstrap e drop privilegi, percorsi con spazi). Sette sorgenti confrontate
  con hash Git blob ufficiali, più due dalla precedente raccolta; verificato
  anche il ramo corrispondente nell'upstream attuale, senza dedurne che un
  aggiornamento generico risolva. Nessuna issue QCA9377 trovata nella ricerca
  mirata Owly; non prova assenza assoluta di patch pubbliche.
- Stato finale di questa indagine: ancora originale/AirDropoff e rete100/80,
  nessun cambio rete/dominio/modulo/configurazione, nessuna nuova prova6 o44.
  Nessun branch/commit/PR/push. Ipotesi del blocco80 resta distinta e non provata.

### Variante IT compilata, non caricata

- `channel44-autonomous-20261031/driver/README.md` documenta ambito,
  riproduzione e limiti; manifest.json conserva hash, metadati e differenze.
- Modulo comune Atheros `ath.ko`, stock ufficiale6.18.36 e variante. Unica
  patch C in regd.c: helper user-hint limitato a QCA9377 PCI168c:0042 e IT
  su tutti e quattro i richiami, inclusi quelli sui flag. Normali Country IE
  e controlli nativi di Paese/CONFIG conservati. Nessuna scrittura EEPROM o
  modifica del database/regole EIRP/DFS. Il ramo nativo può applicare le
  frequenze consentite IT, non soltanto44; nessuna certificazione dedotta.
- Native EXPERT/CERTIFICATION_ONUS/ATH_REG_DYNAMIC_USER_REG_HINTS abilitate
  nella copia privata degli header, con olddefconfig e syncconfig. DB firmato
  e chiavi kernel ON; CERT_TESTING/RELAX_NO_IR/CELLULAR_HINTS OFF. La prima
  build esterna usava ancora autoconf originale: scartata come prova, poi
  syncconfig, clean solo candidata e ricompilazione completa passata.
- Check della funzione C effettiva e quattro richiami passato: QCA/IT sì,
  NULL/nonPCI/altri ID e sette Paesi no, CONFIG spento e Paese nativo
  bloccato no. Self-test ACPI ripassato.17 sorgenti comuni verificate via
  Git blob;9 Kconfig ufficiali mancanti aggiunti solo agli header privati.
- Build stock e IT riuscite, stessi18 export/vermagic6.18.36-1-lts; moduli
  esterni non firmati, MODVERSIONS OFF. Non basta a garantire ABI runtime.
  olddefconfig ha16 differenze di valori attivi, incluse Rust/bindgen assente
  e default EXPERT: review prima di qualsiasi caricamento. Non load-ready.
- Patch SHA256 `7756cfea70f5345356a09613b2f807947d2cb62122c5f537995d8c2486a7d6af`.
  ath.ko IT SHA256 `0657cd83bad9337afa908dd66f8b0c420a07a7c8dd0ad07e1d6713f128b32bad`.
- Postflight.json: rete100/80,44NO_IR, P2P0xa6, AirDropoff, originale attivo.
  Cinque hash header/config sistema e tre hash Owly invariati, tainted0.
  Nessun modulo/servizio/rete/Paese modificato, nessun test6/44, widget invariato.
- Prima di hardware: review config/ABI/firma e ripristino locale senza rete;
  scaricare ath/ath10k interrompe il Wi-Fi. Caricamento/installazione non
  autorizzati in questa fase; nessun launcher preparato. Prova decisiva
  successiva: station senza AP, notifier IT realmente eseguito,44/20 e
  permessi/limiti corretti, IBSS/monitor e ZIP bidirezionale con hash.
  GlobalIT già presente non dimostra che un nuovo hint venga elaborato.
  Autonomia44 e ipotesi sul blocco80 restano non provate. Nessun git write.

Revisione statica successiva: comandi C dei sei oggetti identici;
14/16 differenze di configurazione non compaiono nelle dipendenze Kbuild.
Le due rilevanti sono native: hint in regd.o e CERTIFICATION_ONUS nel
DFS pattern detector comune, la cui init diventa disponibile (prima NULL).
ATH9K_DFS_CERTIFIED resta OFF; nessun vincolo radar/DFS rimosso. Effetto
aggiuntivo documentato: ath è condiviso anche da altre schede. Non è prova
ABI runtime o conformità; modulo sempre non load-ready e mai caricato.

## Test temporaneo autorizzato successivamente

L'utente ha poi scritto «okay quindi testiamo»: autorizzato il collaudo
hardware temporaneo del driver e il ripristino, senza installazione permanente.
Launcher test-driver.py eseguito come xlini; sotto sudo solo codice letterale
stdlib e comandi nativi. Moduli verificati con SHA256 e staged root-owned in
/run, nessuno script Python del checkout caricato come root.

Prima stock e poi IT con NetworkManager temporaneamente escluso dalle sole
interfacce della prova tramite configurazione /run. Un timer systemd locale
indipendente a180s e deadline della prova a100s proteggono il ripristino.
Nessun modulo forzato e nessun cambio di Paese diverso da IT reale. Il test
si ferma se44 restaNO_IR, potenza/DFS non corrispondono o compare P2P inatteso.
Ripristino dell'ath originale installato e backend precedente; preserva
un'eventuale altra connessione Wi-Fi attivata dall'utente. Moduli non firmati
possono lasciare i flag diagnostici di taint fino al riavvio.

Self-test passato: recovery senza modifiche e dopo modifiche simulate,
idempotenza, errore busy mantenuto per retry, ordine unload e arresto al
primo errore, sintassi dei due programmi letterali, watchdog/deadline.
Prima verifica di sola radio: nessun iPhone o ZIP richiesto. Non assumere
successo finché non acquisiti log, risultato e verifica del ripristino.

## Primo collaudo e correzione v2

Prima sessione driver-live-rj4xfng5: caricati stock e candidata, entrambi
ancora44NO_IR, station non associata durante il confronto; nessun IBSS o
monitor creato e nessuna trasmissione di prova. Ripristino automatico passato:
ath originale srcversionEE75841D3B45284B3402DCF, rete100/80, backend originale
attivo e AirDropoff. Runtime NM e timer rimossi/spenti; tre hash Owly invariati.
Kernel taint12288 (modulo esterno/non firmato), resta fino al riavvio.

Trovato un errore aggiunto da noi: wiphy_dev() negli header6.18.36 restituisce
GIÀ wiphy->dev.parent, il dispositivo PCI. Il filtro faceva ->parent un'altra
volta, quindi controllava il bridge. Il primo harness aveva riprodotto male
l'accessor. Ora usa il corpo reale copiato dagli header, include parent bridge
e NULL: fallisce sul vecchio codice e passa sulla correzione di una riga.
Non dedurre ancora che sia l'unico ostacolo hardware.

Sorgente, modulo, patch, check e manifest v1 conservati in driver/v1-failed;
launcher esatto della prima prova copiato nella sua sessione. Versione2
ricompilata, MODPOST/link/BTF passati, check C e recovery ripassati.
Nuovo ath SHA2567ae63c7737940d8620704233b317ec04355f38de2bdb77f242f0040ad5a990ad;
patch SHA256ab8d6016e7e6c2d7f191d95794d103fa9c658800652b4ccd18c0f5daa81fdf46.
Seconda sessione avviata; esito da acquisire, non presumere44 funzionante.

## Secondo collaudo:44 autonomo/IBSS riusciti, controllo monitor da completare

Sessione driver-live-qwiytg08, stesso confronto senza AP. Stock44NO_IR;
modulo IT v2 caricato con srcversion54CCBB3EDCF13BEA9CF4B67,44 senzaNO_IR,
potenza23dBm, vincoli radar/DFS presenti. Log kernel: «dynamically updated by
user», quindi la richiesta IT è realmente arrivata al ramo nativo.

Station Not connected, nessun P2P; IBSS HT20 fixed5220 creato con successo,
BSSID locale02:25:00:ff:94:73 e MAC distinta12:63:c8:44:37:d5. Info IBSS:
44/20, center5220,23dBm. Monitor creato e up sullo stesso phy5. Il launcher
si è fermato perché pretendeva la frequenza anche nella risposta GET_INTERFACE
del monitor; questa risposta la ometteva. Non confondere quell'assert con
un rifiuto IBSS/firmware: tutti i comandi setup erano exit0.

Ripristino passato, originaleEE75841D3B45284B3402DCF e rete100/80 tornati,
AirDropoff. Dopo questa sessione phy6/P2P0x600000002: gli identificatori
cambiano a ogni ricaricamento, non fissarli. Taint12288 già noto.

Il launcher finale richiede44/20 all'IBSS e tipo monitor/stesso phy, poi
legge passivamente per8s con socket stdlib. Conserva solo frequenze/count,
mai payload/identità dei vicini. Decoder radiotap limitato al campo canale,
testato per allineamento TSFT/flags/rate, bitmap estesa, campo assente e
input troncati. Se non riceve frame, monitor RX resta esplicitamente ignoto;
nessuna trasmissione monitor o trasferimento ZIP viene dedotto. Terza prova
aperta in driver-live-g97ei2tf, esito da acquisire.

## 1 novembre2026 — collaudo radio autonomo concluso

Sessione driver-live-pss7ksxh, launcher esatto/session.log/kernel.log,
summary.json e postflight.json conservati. La precedente g97ei2tf non era
partita: nessun log/result e nessun processo ancora aperto alla ripresa.

Test finale exit0, test_passed=true, restored=true. Stock:44NO_IR. V2 IT:
44 senzaNO_IR,23dBm e vincoli radar/DFS presenti; log «dynamically updated by
user». Station Not connected prima/durante/dopo il setup, nessun P2P durante
la prova. IBSS HT20/5220 avviato e Joined IBSS, monitor up sullo stesso phy.
Questa è verifica reale del setup radio senza associazione a un AP.

La cattura passiva di8s non ha prodotto frequenze radiotap decodificate
(lista vuota): monitor RX sul5220 resta NON provato. Non dedurre zero frame
ricevuti, perché il launcher registra solo le frequenze decodificate, non
il conteggio di tutti i frame. Nessuna injection AWDL o ZIP eseguiti.
Il risultato radio non dimostra ancora AirDrop autonomo bidirezionale.

Postflight verificato separatamente: ath originaleEE75841D3B45284B3402DCF,
backend originale attivo, stessa rete100/80, managedyes e UUID iniziale,
AirDropoff. Nessuna interfaccia di prova o configurazione NM temporanea,
timer di recovery spento. Tre hash Owly e cinque hash header sistema
invariati. Ora phy9, P2P wdev0x900000002: sempre individuarli dinamicamente.
Taint12288 dai moduli esterni resta fino al riavvio; nessun riavvio eseguito.

Prossimo lavoro: adattare/validare il backend veloce alla modalità autonoma
44/20 e provare TX/RX con iPhone, ZIP bidirezionale con SHA256, cambi rete e
ripristino. Variante driver e backend NON installati permanentemente; widget
ancora originale. Nessun branch/commit/PR/push o esperimento sul6. L'ipotesi
specifica sul blocco80 resta distinta e non verificata.

## Esito live: trasferimento ZIP autonomo nei due versi riuscito

Sessione live-py0dklbo,1novembre2026. result0 e controller-result0.
Stage root/run/end4-airdrop-driver-ck2sesjh, recovery senza errori. Profilo
esclusivo esistente, IT/[44], PresenceFixed/no-ACK, gestioneRX1 e P2P assente
perché station esclusa da NM prima della ricarica driver. Station NON
associata durante il backend; IBSS44 HT20, center5220,23dBm e awdl0 attivi.
MAC IBSS=station (qui station inattiva), diversamente dal precedente shared44
con due MAC attivi. Nessuna nuova implementazione del backend necessaria.

Stesso ZIP8388736byte, SHA256
ac2dbab130dd40c255993de77b844273f6871693fa18b8a051afe5a49be85b67:
- PC→iPhone: sender UPLOAD ok8,65s; comando CLI completo13,224s con
  ricerca/Ask/accettazione. Non confondere queste due misure.
- iPhone→PC: POST/Upload13:32:55,826→HTTP20013:33:08,525,12,699s.
  File restituito in Downloads/AirDrop/airdrop-speed-8MiB21.zip (il nome
  reale contiene uno spazio prima di21), dimensione e SHA ricontrollati.

TX/RX e file integri verificati end-to-end su44 senza associazione al router;
la precedente cattura passiva vuota non era prova di impossibilità RX.
Una sessione riuscita non valida ancora crash/cambi rete/ripetibilità.

Ripristino verificato separatamente: ath originaleEE75841D3B45284B3402DCF,
backend originale47fa6c...attivo, OWLY_RX_MGMT1, rete100/80, AirDropoff.
Pacchetto separato, override temporaneo, configurazione NM e interfacce prova
rimossi, timer spento. Tre hash Owly/config e cinque header sistema invariati.
Profili test applicati con BindReadOnlyPaths al solo servizio: nessuna
riscrittura /etc/owly. Ora phy11/P2P0xb00000002, da trovare dinamicamente.
Taint12288 resta fino al riavvio, nessun riavvio eseguito.

Artefatti: manifest, profili, pacchetto, launcher/self-test nel gruppo
channel44-backend-20261101; nella sessione send.log, receiver.log privato,
transfer.json, summary.json, supervisor.log, owlyd.log, kernel.log e
postflight.json. Log contengono identità/metadati privati, non pubblicarli.
Un controllo read-only postflight ha avuto timeout della revisione automatica
permessi; retry con comandi più piccoli riuscito, nessuna verifica rimasta
bloccata. Nessun branch/commit/PR/push, prodotto/widget invariati.

Restano consolidamento: supervisione perdita44/width/nuova rete, crash e
journal recovery reali, ripetibilità e confezionamento del driver/backend
per uso ordinario. Solo dopo integrazione widget; rate/BlockAck e causa80
ancora rimandati, nessuna nuova conclusione sulla causa80.


## 1 novembre2026 — ricerca upstream e confronto rate24

Richiesta utente: consultare PR/issue Owly e continuare a migliorare la velocità.
Ricerca read-only salvata in channel44-rate24-20261101/research.json.
PR58: BA su MT7612U,30MB47→14s, hardware specifico. PR59: riordino TCP,
nessuna riduzione significativa del totale nel run pubblicato. PR62: HT/VHT
su MT7921 con varie modifiche insieme; codice C storico, maintainer segnala
riscrittura Rust. PR81 corrente: tx_rate54/mcs7 già supportati; non copiare
annunci2SS sulla QCA9377 a1SS. Issue82 e PR102 riguardano Intel, non prova
applicabilità QCA. Rate radiotap richiesto può essere ignorato da firmware.

Test channel44-rate24-20261101/live-nreiqg3v concluso result0/controller0:
44/20 autonomo, stessa variante v2 e backend; sola richiesta tx_rate24.
PC→iPhone upload8,58s vs8,65s baseline: differenza<1%, nessun miglioramento
conclusivo. CLI11,953s. iPhone→PC12,572s (POST13:52:02,784→20013:52:15,356).
Stesso ZIP, hash ritorno identico; transfer.json aggiornato. Rate hardware
NON verificato. Originale ripristinato: athEE75841D3B45284B3402DCF, backend
attivo, AirDropoff, rete100/80, pacchetto test assente. Profili originali
mai riscritti. Widget invariato.

Preparato confronto channel44-rate54-20261101: stesso pacchetto/binario,
solo tx_rate54; aggiunta lettura nativa fw_stats dopo trasferimento prima
del ripristino. Il contatore potrebbe non esporre il rate injection effettivo.
Self-test recovery passato. Terminale guidato aperto: esito DA ACQUISIRE,
non dedurre successo né rate effettivo. Manifest/hash e launcher conservati.


## Esito rate54 e successivo controllo nativo ath10k

channel44-rate54-20261101/live-qbvtu7wi concluso result0/controller0:
PC→iPhone upload8,80s, CLI13,046s; iPhone→PC14,807s (13:58:18,767→13:58:33,574).
ZIP identico, SHA ricontrollato indipendentemente. Nessun guadagno rispetto
al default8,65s o rate24a8,58s. fw_stats salvato: rate peer/history tutti0,
non utilizzabili per confermare la velocità RF. Postflight indipendente:
ath originaleEE75841D3B45284B3402DCF, rete100/80, AirDropoff, overrideassente;
hashoriginali in postflight.json. Primo comando postflight multiplo ha avuto
timeout revisione automatica; controlli più piccoli poi riusciti.

Sorgente ath10k-mac.c6.18.36: set_bitrate_mask→set_fixed_rate_params invia
WMI fixed_rate per vdev. Preparata channel44-native54-20261101, stesso
pacchetto/profilo54 e rollback, aggiunta sola richiesta nativa iw alla IBSS
44/20 già verificata (sudo iw dev owlyibss0 set bitrates legacy-5 54).
Errore comando interrompe test e ripristina; accettazione non prova rateRF.
Interfaccia effimera rimossa dal recovery: nessun bitrate station modificato.
Esito hardware DA ACQUISIRE. Non installato permanentemente; widget invariato.


## Native54 interrotto prima della scoperta; nuova prova native24

Sessione channel44-native54-20261101/live-na4oe651: nessun trasferimento;
comando iw legacy-5 54 rifiutato EINVAL(-22). La visibilità iPhone non è
stata la causa di questo arresto. result1/controller0 e restoretrue.
Controllo indipendente: driver originale, daemon originale, AirDropoff,
override assente. Launcher esatto conservato nella sessione.

Sorgente ufficiale mac80211/cfg.c6.18.36 ieee80211_set_bitrate_mask rifiuta
maschera che non interseca basic_rates dell'interfaccia attiva; non verificato
quale controllo abbia materialmente prodotto EINVAL in questa sessione.
Inoltre nl80211.c mantiene HT/VHT abilitati se omessi dalla richiesta.
Preparata native24: tx_rate24 come precedente confronto, comando nativo
legacy-5 24 ht-mcs-5 vht-mcs-5 (HT/VHT vuoti). Nessun cambiamento driver
aggiuntivo o dei parametri regolamentari; medesimo rollback. Da collaudare:
non dedurre accettazione, velocità RF o risultato prima dei log.


## Esito native24 riuscito — 1 novembre2026

Sessione channel44-native24-20261101/live-2k4psgjn result0/controller0.
Comando nativo iw dev owlyibss0 set bitrates legacy-5 24 ht-mcs-5 vht-mcs-5
accettato (exit0), dopo verifica IBSS44/20 e station non associata. Owly
richiede anch'esso tx_rate24, pacchetto/driver sperimentali invariati.
PC→iPhone upload7,86s (CLI12,5405s), contro baseline8,65s e sola richiesta
Owly24a8,58s: circa9% in meno, UNA prova, non guadagno causale dimostrato.
iPhone→PC12,687s, sostanzialmente uguale al baseline12,699s. ZIP8MiB
restituito con SHA identico, ricontrollato indipendentemente. Comando
accettato NON prova bitrate RF effettivo; fw_stats precedenti inutilizzabili.

Postflight indipendente salvato: driverEE75841D3B45284B3402DCF, backend
originale attivo, AirDropoff, rete100/80, overrideassente e tre hashoriginali
identici. Trasferimenti, logreceiver privato, esattolauncher e postflight
conservati nella sessione. Widget e installazione permanente invariati.
Il tentativo live-i_iajdgt precedente era stato interrotto prima dei log.
Launcher ora attende Invio locale prima di sudo/setup; self-test passato.
Prossimo confronto utile: ripetere/alternare baseline e native24 prima di
attribuire il guadagno al controllo firmware o introdurre altre variabili.


## Confronto A/B rate24 preparato

Richiesta utente «okay procedi»: channel44-ab24-20261101, sequenzaA1/B1/A2/B2.
Tutti richiedono Owly24; soloB applica maschera nativa24 HT/VHTvuoti.
Quattro invii, un solo ritorno ZIP finale con SHA. Ogni user_trial chiude
AirDrop, richiede exit0 e verifica rimozioneIBSS prima del round successivo:
no maschera nativa residua fra A/B. Stesso driver/pacchetto/profili44/20,
nessuna nuova patch prodotto; supervisor e watchdog originali invariati.
Launcher aspetta Invio prima di sudo. Salva confronto incrementale e log
per-round; parser rifiuta metriche mancanti/invalide. Self-check ordine,
ritorno finale, propagazione errori e rollback passati; parser sui tre log
reali precedenti verificato. Preflight originale/off/nooverride verificato.
Terminale aperto; esito hardware DA ACQUISIRE. Non dedurre quattro successi.


## A/B interrotto sul secondo avvio: non errore operatore

Sessione channel44-ab24-20261101/live-fqt0qqv1: A1 inviato9,02s,
CLI13,5708s, richiestaOwly24 soltanto. B1 interrotto PRIMA dell'invio:
iw legacy-5 24 ht-mcs-5 vht-mcs-5 restituisceEINVAL(-22), mentre identico
comando era accettato nella prova singola live-2k4psgjn. Nessun A2/B2.
result1/controller0, restoredtrue. Hash ritorno A1false atteso: il protocollo
richiedeva ritorno solo suB2, mai raggiunto; non prova corruzione o erroreutente.

Kernel nella seconda creazione IBSS: «Selected IBSS BSSID ... based on
configured SSID», poi «bitrate not supported 3». Questa stringa proviene
da ath10k_recalculate_mgmt_rate, non da set_fixed_rate_params: non dedurre
che il3 sia il bitrate richiesto dall'utente. MAC della secondaIBSS diversa
daA1: ulteriore variabile non controllata dopooff/on. La causa esatta del
rifiuto non è ancora isolata. Non aggiungere retry ciechi o spacciare A/B
incompleto per conferma del9% guadagnato nella singola prova.

Verifica indipendente: athoriginaleEE75841D3B45284B3402DCF, daemonoriginale
attivo, AirDropoff e overrideassente. Nessun nuovo test avviato. Prima di
ripetere il confronto bisogna diagnosticare/controllare statoIBSS/basicrates,
identità e riavvio; alternativa per isolamento: ciclo completo radio/driver
fra round, riusando il recovery già verificato. Nessuna patchprodotto o
integrazionewidget. Log e launcher esatto conservati.


## A/B con isolamento completo preparato dopo il rifiuto B1

Utente richiede controlli e nuova prova. Nuovo gruppo
channel44-ab24-cold-20261101. Non modifica prodotto/widget, driver o package:
ROOT eWATCHDOG sono byte-identici al precedente; hashpacchetto verificato.
Ogni round A1/B1/A2/B2 esegue una sessione completa separata: preflight
originale→driver temporaneo→invio→off→recovery/pacchetto rimosso→driver
originale/rete ripristinati prima del round dopo. SoloB richiede maschera
nativa24 HT/VHTvuoti; tutti Owly24/44/20. Controlla MAC cell=station=pre-on;
se cambia o recovery fallisce interrompe, senza continuare altre prove.
Quattro invii, ritorno soloB2 con SHA; log e launcher esatto per sessione,
comparison.json incrementale in comparison-latest.path. live-latest.path
indica invece l'ULTIMA sessione, non l'intero confronto. Esito DA ACQUISIRE.

Self-test ordine sessioni/ritorno finale/fallimento stop/salvataggio
incrementale/parser passati; parser verificato anche su logreali9,02/7,86.
Recovery precedenti ripassati. Preflight host salvato: athoriginale,
daemonoriginale attivo, trehashoriginali identici, off e nessuna interfaccia
temporanea/override; rete100/80. Terminale aperto e attende Invio locale.

La causa del rifiuto resta non isolata: cambioMAC e messaggio kernel
«bitrate not supported3» sono osservazioni, non prova di specifico bugrate.
Nuova procedura serve a eliminare il carryover fraoff/on; non dichiararla
soluzione verificata finché completato l'hardware. Nessun git write.


## Confronto cold completo: nessun vantaggio utile del rate nativo24

comparison-r2jcxfp1 result0; tutti i quattro round result0/controller0 con
restoretrue. A1=9,63s; B1=9,65s; A2=9,22s; B2=9,10s. MediaA9,425s,
mediaB9,375s, differenza0,53%: nessun beneficio utile dimostrato. Il precedente
9% della singola prova NON confermato. Due campioni/condizione, non prova
statistica di equivalenza né conferma rateRF. Ultimo ritornoZIP SHA identico,
ricontrollato indipendentemente; analysis.json conserva sintesi.

Utente chiede di fermare prove e riflettere su avvicinamento AirDrop nativo.
Nessun nuovo test/radio/driver avviato. Priorità proposta: misurare rateRF e
percorso dati realmente usato (non copie outgoing); valutare HT1SS/20MHz
prima di80; aggregazioneA-MSDU TX e BlockAck RX soltanto se hardware/percorso
li supportano; correlare rate/cwnd/ritrasmissioni/code e finestreAWDL prima
di patchsync. Configurazione sorgente corrente accept_addbafalse/amsdufalse,
rateHT20 supportato ma rateRF richiesto non verificato. PR58 MediaTek non
prova applicabilità QCA. Obiettivo8MiB/3s richiede22,4Mbit/s di file: non
impone80MHz e non garantisce3s totali incl.discovery/consenso. Nessuna nuova
conclusione sulla causa80 o promessa di uguagliareApple con chipsetattuale.


## Punto1 avviato: osservabilità rate e diagnostica RX preparata

Utente autorizza punto1 poi2. Gruppo channel44-rate-observe-20261101:
profilo Owly24/44/20 invariato, stesso driver/binario/package, un ZIP con
ritorno SHA. RX monitor: istogrammi legacy/HT/VHT reali ricevuti da iPhone,
retry/AMSDUbit/campoAMPDU e referenceconsecutive; contatoridrop AF_PACKET.
TX PC outgoing etichettato SOLO richiesto; own nonoutgoing feedbacklocale,
non provaRF. Filtra dati BSSIDAWDL/endpoint e conserva soltanto conteggi,
mai payload/indirizzi nei risultati. Decoder parte DOPOdrop gruppi/GID/UID
nel bootstrap letterale root che apre solo socket suowlymon0. Stopprima
diCLIoff e rootrecovery; deadline300s. JSONdiagnostico valido distinto da
successotrasferimento; RX0 o rateunknown restano limitazioni osservabilità.

Sorgenti ufficialihtt_tx.c/txrx.c/trace.h/debug.c/htt_rx.c6.18.36 salvati con
SHA eURL: normalesubmitHTT senza rate radiotap per-frame; completamento
status.rates[0].idx=-1. HW HAS_RATE_CONTROL. Non affermare rateRF misurato
tramite trace/commandaccepted. Firmwarepktlog/TXstats esistono come opzioni,
ma utilitàQCA/peer e formato da verificare; nessuna attivazione ora.
Legge wmi_services/pktlog_filter/htt_stats_mask soltanto per inventario.

Self-test bounds/allineamento/bitmapestesa/legacyHTVHT/unknown/AMPDUAMSDU/
filtro e TXRX passato; literalbootstrap sintassi/droporder e recovery passati.
Preflight driveroriginale e off verificato. Terminale aperto, attendeInvio;
esito DA ACQUISIRE. Non passare al2 fingendo punto1 TX concluso. Widget e
installazioneoriginale invariati, nessun branch/commit/PR/push.


## Diagnostica rate riuscita: RX iPhone prevalentemente MCS1

channel44-rate-observe-20261101/live-gijsjo2e result0/controller0, captureexit0.
PC→iPhone9,79s (CLI14,375s); iPhone→PC12,306s. ZIP SHA identico e
ricontrollato indipendentemente. RXRF iPhone9832 frame dati:8885HTMCS1/20LGI
(90,37%),944MCS0/20LGI,3legacy12. MCS1 nominale13Mbit/s, MCS0a6,5;
1556frameconretrybit (15,83% dei ricevuti), NON percentuale perdita file.
Socketpacketdrop0. CampoAMPDU su9832 ma massima referenceconsecutiva1:
non prova né aggregazioneefficiente né incapacità hardware. AMSDUbit0.
PCoutgoing10659legacy24 richiesti; feedbacklocale10659rateunknown:
TXRF PC ancoraNON verificato. WMIpeerstats-serviceoff; pktlog0/httmask0.
Tutto inanalysis/radio-summary/transfer/receiverlogprivato, wmi-services.txt.
DriveroriginaleEE75841D3B45284B3402DCF e AirDropoff verificati, restoretrue.

Punto2 successivo autorizzato: channel44-amsdu-20261101, sola opzione
radio tx_amsdu=true, rate24/noACK/BAdefault/44/20 e binario/driver invariati.
Native::start già richiede monitorMTU8192 e adegua max_frame alla MTU reale;
non cambiare il default node2304 credendolo capruntime senza leggere questo.
Raggruppamento giàimplementato e limitato da HTpeer/capframe. Cattura
verificherà A-MSDUbit e dimensionemassimaframe; RSSI e azioniADDBA/DELBA
aggiunti come SOLA osservazione. Zeroazioni non provaassenza suRF, dato
hooknl80211 riceve soloAWDLvendor; monitor può avere limiti management.
Non attivatoBlockAck: supporto risposta hardware da verificare. Nuovo
parser testRSSI/BA/troncamenti passati, recoveryripassato. Terminaleaperto
attendeInvio, esito DAACQUISIRE. Nessuna nuova patchRust/build/pacchetto;
installazioneoriginale/widget invariati. TXRF rimanequesitoaperto delpunto1.


## A-MSDU TX: funzione usata pochissimo, pista Native-Wifi/QoS

channel44-amsdu-20261101/live-jomel1rm result0/controller0, captureexit0,
SHA ritorno identico e ricontrollato. PC→iPhone9,07s (CLI14,149s), ritorno
11,712s contro diagnostica precedente9,79/12,306s: singoli run, guadagno
modesto non attribuibile con certezza adA-MSDU. iPhone questa volta usa
soprattuttoMCS1SGI (8829frame) inveceLGI; altra variabilità da considerare.
RXretry1347/9736, RSSI-42..-31dBm, socketdrop0. Nessuna azioneBA osservata:
NON prova assenzaRF perché il management sul monitor può essere incompleto.

PCrequested10194frame, solo11A-MSDU (0,108%); maxframe2986B. Feedbacklocale
10194frame, AMSDUbit0 e max2984B, totale22B meno dei requested: COMPATIBILE
con rimozione2B QoS per11frame; non abbiamo salvato coppieper-sequenza né
misurato il bit sulRF. Non affermare perditaRF provata. Sorgente ath10k
ath10k_tx_h_nwifi rimuove QoSctl e bitQoS nel percorsoNative-Wifi; fwpuò
ricostruire header, ma preservazione AMSDU non dimostrata. Analisi.json.

frame_mode attuale letto=1 (NativeWi-Fi); kerneltestlog raw0 hwcrypto1,
firmware WLAN.TF.2.1-00021-QCARMSWP-1 api6 featureswowlan,ignore-otp:
raw-mode NON pubblicizzato. core.c ufficiale6.18.36 controllafeatureRAW:
frame_mode0 senzafeature fallisce; inoltre RAW disabilita aggregazioneFW
AMSDU per workaround. Non forzare bitFW o parametro come se fosse supportato.
Referencecore salvato conSHA/URL nelmanifest. Nessun parametro modulo,
firmware o driver modificato per questa indagine.

Ripristinoauto riuscito, driveroriginaleEE75841D3B45284B3402DCF e off
verificati indipendentemente. Nessun nuovo test aperto. Priorità ora:
chiarire percorsoTX NativeWi-Fi/QoS/ACK e perché il batch produce cosìpochi
aggregati; eventualeA-MPDU/BA richiede supportohardware e visibilità richieste,
non attivare semplicemente aggregationtrue. TXRFancora ignoto; non promettere
rate alti o3s. Widget/installazioneoriginale invariati.


## Analisi offline completata: batching e classificazione QoS

channel44-tx-analysis-20261101/ANALISI.md e manifest; copia source dal
backend già collaudato, un solo testnode aggiunto, prodotto immutato.
Replay44:64 pacchettiIPv6 da1450B, arrivoindividuale con finestraaperta→
64frame/0AMSDU; giàaccodati e poi finestraaperta con cap8176→32frameAMSDU;
cap2304→64frame. Payloadidentici. Testdedicato e interasuiteNode17passati.
Dimostrato meccanismo: Node::handle service dopo ogniOutbound; driverTAP
un pacchetto perhandle. Non dimostrato quantitativamente backlog live.
Native::start adeguamax_frame allaMTUmonitor: non alteraredefault2304alla cieca.

check-kernel-qos.py estrae duehelper reali, harnessC constubskb/header:
nonQoS→TID16/no rimozione; QoSnormale→TID0/-2B; QoSAMSDU→TID0/-2B.
Ultimidue buffer/header uguali con bodyuguale, nessun bitAMSDU in questi
helperoutputs. ClassificazioneQOS conservata. Il nomeTID16NON_QOS_MCAST_BCAST
NON prova trasmissionemulticast, ratebasso o assenzaACK. PreservazioneQoS/
AMSDUnelRF rimane ignota. Non chiamare provatobugfirmware.

Nessuna rete/radio/driver/firmware/configurazionehost modificata. Nessun
terminale nuovo aperto. Prossima prova proposta: QoSordinario SENZA AMSDU,
un pacchetto perframe e stesso44/20/rate; isolaTID/header prima di
coalescenzabatch. Da preparare/validare, NON già disponibile néinstallata.
RAWmodenonpubblicizzato dalFW attuale, non forzare feature. Nessun gitwrite.


## Prova QoS ordinario preparata e terminale aperto

Utente «okay facciamo la prossima prova»: channel44-qos-20261101.
Copia sorgente base; unica modificaprodotto Node::send_unicast ramo
batchlen1: data_frame normale→bitQoSData e QoSctl[0,0] inserito aoffset24.
Nessun batch/delay/rate/noACK nuovo; multicast/management invariati.
Nessun optin aggiunto inproduzione: variante SOLO del laboratorio/pacchetto
separato temporaneo, mai installata come backend permanente/widget.

Profilo Owly24/44/20, tx_amsdufalse e aggregationfalse espliciti. DriverITv2
identico. Pacchetto temporaneoowly-qca9377-standalone-test0.4.1-2 con solo
daemon/licenza/PKGINFO, senza hook; SHAdaemon
85cf45072adb569b0bf84068b4a11ae11923284ff7f1e80340189f8cc10c1ccd.
PackageSHA/radioprofileSHA e launcher/decoder hash nelmanifest aggiornato.
ROOT conserva stesse protezioni/hashing/dropin/watchdog/recovery, filename
pacchetto aggiornato e nuovi hash applicati dalmanifest. Originale preservato.

34unitAWDL+17Node passati, incluso nuovo test su44: frameQoS0x88, ctl0,
A-MSDUfalse, singoloIPv6da1450B integro, rate/noACK invariati. Releaseoffline
riuscita. Decoder aggiunge qoscounter e selftest; launcher richiede anche
QoSrequested>0 e AMSDUrequested0 oltre ZIP/hash e JSONcattura valido.
Captureoutgoing/feedback NON prova rate/headerRF, TID0 atteso per logica
driver ma non ancora misurato in live. Nessun cambiofirmware/kernelparam.

Preflight driveroriginaleEE75841D3B45284B3402DCF e off verificati. Terminale
aperto attendeInvio. Un solo ZIP e ritorno; esito hardware DAACQUISIRE,
non presumere velocità/compatibilità. Artefatti patch/README/source conservati.
Nessun branch/commit/PR/push.


## QoS ordinario live riuscito: invio7,68s, causalità da confermare

channel44-qos-20261101/live-71_9g6hg result0/controller0, catturavalida,
qos_experiment_observedtrue. PC→iPhone7,68s upload, CLI12,1846s; ritorno
12,574s con ZIP SHA identico e ricontrollato. Confrontobaseline diagnostica
nonQoS/Owly24/AMSDUoff9,79s:21,55% meno tempo, UNAprova, non conferma
causale. Storicamente anche native24nonQoS aveva7,86s non replicati: serve
A/Bintercalato a cicli completi prima di chiamarlo guadagnoripetibile.

10409PCrequested,9829QoS e0A-MSDU. Feedback10409frame/nonQoS,19658Bmeno,
esattamente2*9829: compatibile con trasformazioneNativeWifi, non misuraRF.
9535frameiPhone:8725MCS1LGI20,810MCS0LGI20,1370retrybit (14,37%);
nessun dropAFPACKET, AMPDUfieldpresent ma referenceconsecutivamax1,
nessunaazioneBAosservata (limiti visibilità restano). RateTXRF PC ignoto.
Ricezione sostanzialmente invariata, nessun nuovo bitrateRXalto dimostrato.

Restoretrue, athoriginaleEE75841D3B45284B3402DCF e off verificati fuori
cattura. Analisi/transfer/receiverlogprivato salvati. Nessun nuovo terminale
aperto inquestaturnata; prossimaazione utile confrontoQoSoff/on ripetuto,
con stessaprofilo/binarybase e isolamento completo giàcollaudato. Nessuna
integrazionepermanente o widget, nessun gitwrite.


## QoS A/B preparato e avviato in attesa operatore

Utente «okay procediamo»: channel44-qos-ab-20261101. A1/B1/A2/B2 con
setup/restorecompleto perround. A usa packagebaseline0.4.1-1/e4ee...,
B QoS0.4.1-2/85cf..., entrambi giàcollaudati. Manifestvariants conservaSHA
completi; root_for cambia solo filename e SHApackage/binary nella stringa
letteraleROOT, con count==1 echeckcompile perogni variante. Profilocomune
Owly24/44/20, tx_amsdufalse aggregationfalse, stesso noACK/driverITv2.

Metadata identica perentrambi: A richiedeQosframes0, B>0, AMSDU0. MACcell=
station=primaon richiesto. Quattroinvii, ritornoSHAfinaleB2. Ogni sessione
finisce restoredriver/NM/backendprima di successiva; errori fermano sequenza.
Comparisonincrementale in comparison-latest.path, live-latest.path=ultimoround.
Selftest hashpackage/binary, ROOTA/B, ABAB/failstop/partialsave/ritornofinale/
parser/decoder/recovery passati. Parser9,79/7,68logreali verificato. Nessuna
nuova modificaRust/build; pacchetti verificati giàesistenti ricopiati.

Preflight originaleEE75841D3B45284B3402DCF/off verificato. Terminale aperto
attendeInvio perTutti10min. Esito hardware DAACQUISIRE, non inferire guadagno.
Nessun gitwrite o installazionepermanente/widget.


## QoS A/B completato: medie identiche, nessun guadagno dimostrato

channel44-qos-ab-20261101/comparison-045fwooe result0; tutti4sessioni
result0/controller0/restoredtrue. A1=8,63s, B1=9,00s, A2=9,68s, B2=9,31s.
MediaA=mediaB=9,155s (0,0% differenza). QoSconditionverified inogni round:
Aqosframes0; B1=6157/B2=9369, AMSDU0ovunque. CaptureAFPACKETdrop0.
Il precedente7,68s QoS singolo NON si conferma come vantaggioripetibile.
Duecampioni/condizione non sono provauniversaleequivalenza, ma non supportano
QoSordinario come ottimizzazione da integrare. Pacchettibase/candidata
restano nel laboratorio; non portare questeprototipazioni nelwidget.

FinaleB2 ritornoZIP hashidentico e ricontrollato, ricezione12,607s dajournal
letto SENZA escalation (questocomando funziona nella sandbox: preferirlo).
IPhoneframeRFrimane soprattuttoMCS1/20LGI inentrambicasi; sporadici5frameMCS7
soloA, non guadagnosostenuto. TXRF PCancora non verificato. Analysis.json,
comparison.json, logreceiverprivato e metadataper-round conservati.

DriveroriginaleEE75841D3B45284B3402DCF verificato. Primo controlloCLIoffhost
ha timeoutrevisioneprimaesecuzione; retrybreve unavolta consentito. Ripristini
controller tutti riusciti; retry riuscito: AirDropoff verificato indipendentemente.
Nessun nuovotestaperto; priorità successiva misurareACK/rate/percorsofirmware,
non altri toggleQoS. A-MSDUcoalescenza software spiegataoffline ma sua
preservazione/efficaciaRFnon dimostrata; BlockAckhardware restada verificare.
Nessun gitwrite/installazionepermanente o modificawidget.


## Diagnostica ACK/completion preparata e terminale aperto

Utente autorizza ACK/rateeffettivo/firmware. Nuovo gruppo
channel44-ack-trace-20261101: riprende baselinee4ee/0.4.1-1 e profilo
Owly24/noACK/44/20, AMSDUfalse aggregationfalse, QoSoff. Nessun cambio
backend/kernel/firmware. Solo monitorcontrolflag e tracefs peristanza.

ROOT dopo loadcandidate e prima CLIon: istanzatracefs univoca rootstage-tx,
ath10k_htt_tx/unref e ath10k_log_dbg filtratolivello8+completionmsg.
Buffer4096KiB/CPU, clockmono con anchorwall/mono. Snapshotglobaltrace/
debug_mask/eventenable/filter confrontati aifinali; nessunascritturaglobale.
Tracecleanup integrato PRIMA stopdaemon/unload inrestore_backend_pre e
ancheWATCHDOG. State markerpersistito prima mkdir; erroripreservati perretry.
Cattura kernel metadataonlyviaJSONstdoututente, perCPUoverrunconservati.

Usertrial richiede sudo iw owlymon0 set monitor control (soloRX), errore
interrompe e ripristina. Decoder contatoriACK/CTS/RTS/BAR/BA perRApc/iphone,
checkminheader e peerfilter percontrolconTA; nienteindirizzi/payloadsalvati.
ACKsoloRA non identifica mittente. Zerocontrolosservati NON provaassenzaRF.
Normali rateRX/TXrequested e RSSI/AMPDU/AMSDU metadatariutilizzati.

analyze-tx.py correla ID/submit/completiondebug, distingueriuso/unmatched/
pending e grandiframe>=1000B, p50/p95/p99code; anchorperPCsendwindow.
Enum interno ufficialehtt.h: NONE0,ACK1,NOACK2,DISCARD3 (NON wireenum).
NoACKrichiesto: statusACKnominale nonprovaACKfisico. Tempi includonocode,
non soloairtime. RateTXRF sempre NON verificato con questicompletion.

LinuxWireless debugdoc conferma HTT_TX_RATE_INFOmask0x10 e statsattraverso
tracebinario; perf/trace-cmd/libtraceevent noninstallati. Nessunadepnuova,
HTTstats/pktlog nonattivati finchéformat/toolingQCAverificati; non fingere
rateRFmisurato. Fonti FAQ/debug ufficiali consultate, htt.hsalvatoSHAURL.

Selftest decodercontrol/headerbounds/RA/outgoing, statusenum/IDriuso/
finestretemporali/analyzer, trace stop-read-disable-remove/idempotenza/
foreignpath/debugglobal e recovery/watchdog passati. Preflight originale
EE75841D3B45284B3402DCF/off verificato. Terminaleaperto attendeInvio,
un ZIP+ritornoSHA; esito DAACQUISIRE. Nessun gitwrite/installazionepermanente.


## Diagnostica ACK/firmware completata: live-0cwxzzmf

channel44-ack-trace-20261101/live-0cwxzzmf: result e controller-result 0,
RESTORE_OK true. Baseline originale sperimentale e4ee, Owly24/noACK,
44/20 MHz autonomo, QoS e AMSDU disabilitati. PC -> iPhone 7,392 s
(POST Upload -> 200); processo CLI completo 11,691 s include discovery e
conferma. iPhone -> PC 12,924 s; SHA-256 ZIP ricontrollato identico.
Singolo campione con diagnostica: NON dimostra una nuova ottimizzazione.

Traccia kernel integra: 11.117 submit correlati ad altrettanti completamenti,
zero ID riusati prima del completamento, zero completamenti senza submit,
zero pending finali. Status interni: 11.108 success ACK-named, 9 NOACK,
zero DISCARD. Finestra processo invio: 6.633 completamenti, 6.626 success,
7 NOACK. Success nominale con noACK richiesto NON verifica ACK fisici.
Contatori NOACK NON sono una misura della perdita RF.

Pacchetti >=1000 B nella finestra invio: 6.122, submit -> completion
mediana 34,570 ms, p95 50,517 ms, p99 96,802 ms, massimo 99,787 ms.
Picco pending dell'intera sessione 57. Intervalli includono code software/
firmware e consegna delle notifiche; non sono misura dell'airtime né prova
che una singola trasmissione richieda 35 ms. Il kernel htt_rx.c:2980-3023
accetta completion con num_msdus multipli: batching delle notifiche è
possibile. Questa cattura filtra i messaggi per singolo MSDU, non registra
num_msdus: non consente di separare attesa RF e raggruppamento dei report.

Flag monitor control accettato, nessun ACK/CTS/RTS/BAR/BA osservato:
limite di visibilità, NON prova assenza sul mezzo. RX iPhone 9.898 frame:
8.990 MCS1/20/LGI, 907 MCS0/20/LGI, un MCS7 di soli94 B. Retry bit su
1.422 frame (~14,37%), NON perdita percentuale. Zero drop AF_PACKET e
zero overrun/dropped trace su tutte le CPU. TX RF PC ancora ignoto;
la richiesta24 Mbps non verifica il bitrate effettivo del firmware.

Istanza trace rimossa, configurazione trace globale e debug_mask invariati.
Driver originale EE75841D3B45284B3402DCF e AirDrop off verificati fuori
cattura. Primo controllo CLI timeout revisione automatica; unico retry
riuscito. Nessuna integrazione nel widget o modifica permanente.
Transfer.json aggiornato, receiver.log privato, tx-trace.txt e
analysis tx-analysis.json conservati; self-test analyzer passato.

Prossimo approfondimento utile: verificare formato e accesso alle statistiche
HTT TX_RATE_INFO specifiche di questo firmware prima di un altro test;
per distinguere code da reporting acquisire anche num_msdus nelle completion.
Nessuna evidenza attuale giustifica nuovi toggle di ACK/QoS/80 MHz.


## HTT TX_RATE_INFO verificato su QCA9377, nuova prova preparata

Utente «okay vai». channel44-htt-rate-20261101/probe-9sddsord:
sonda6s sulla station attuale senza cambio rete/driver/backend, mask0x10
ripristinata a0. Sei risposte firmware PRESENT, tipoTLV4,172B, zero lost
perf. Solo stdin sudo nel terminale locale, codice privilegiato letterale
stdlib, gruppi/GID/UID abbassati prima decoding. Watchdog indipendente20s
su parent death/deadline; nessun trace globale/debug_mask o resetcontatori.

Trovata definizione primaria Qualcomm/TLF wlan_defs.h nel kernel AOSP,
commit8158d57467c4332c1b144c5dc4cc21d5ade64ce6, archivio+SHA nelmanifest.
Layout non-AR900B172B: mcs10,sgi10,nss3,stbc10,bw3,pream4,ldpc/rts/ack_rssi.
Plugin ufficiale Qualcomm qca-swiss-army-knife commit6df4dae3 usa invece
180B/nss4/bw4: NON applicarlo direttamente alla QCA9377. Decoder seleziona
layout per lunghezza esatta, altri non interpretati; PARTIAL non decodificato
come struttura completa. Limiti perf/data_loc/TLV e contatori con reset
coperti da self-test; nessuna nuova dipendenza.

Delta primo/ultimo campione station:92 MCS (81MCS8+11MCS9),92NSS1,
92BW80,92preamVHT,81SGIMCS8. Coerente con station80; NON misura TXAirDrop
né dimostra AWDL80 funzionante. Marginali firmware globali non sono una
misura per-pacchetto e non vanno combinati arbitrariamente. ACK RSSI
istantaneo può essere stantio con noACK, non prova ACK fisici del transfer.

channel44-htt-live-20261101 pronto: riusa precedente prova ACK baseline
44/20 autonoma e ripristino completo. Aggiunge perf FDs/buffer perCPU
CLOCK_MONOTONIC e mask16, restore prima stopdaemon/unload anche watchdog;
zero atteso iniziale, valori esterni preservati. Errori cattura chiudonoFD
senza bloccare ripristino radio. Traccia include anche num_msdus completion.
Analyzer HTT separato unprivileged, delta finestraCLI via anchorwall/mono,
nessuna inferenza TXRF se eventi persi/reset o campioni insufficienti.

Self-test decoder, integrazione, errore overflow, mask restore/foreign,
watchdog, recovery preesistente passati. Package/profili hash verificati;
originaleEE75841D3B45284B3402DCF e CLIoff verificati prima nuovo terminale.
Nuova prova guidata richiedeInvio e iPhoneTutti10min, esito DAACQUISIRE.
Nessuna modifica widget/permanente, nessun branch/commit/PR/push.


## HTT AirDrop completato: legacy OFDM e contatore RTS elevato

channel44-htt-live-20261101/live-xac66s73, result0/controller0/RESTORE_OKtrue.
Il sospetto errore sudo non ha impedito il test. PC -> iPhone8,342s
(Upload->200), CLI14,386s; iPhone -> PC12,687s. ZIP SHA ricontrollato identico.
Profilo invariato baselinee4ee/Owly24/noACK/44/20, QoSoff/AMSDUoff/BAoff.

54campioni HTT PRESENT/type4/172B, lost0, nessun capture_error, maskrestored.
Nella finestraCLI15campioni (delta14,187s): preamOFDM+7295, HT/VHT0,
MCS/NSS/BW/SGI tutti0, RTS+6717. Nella finestra effettiva Upload8campioni,
delta interno7,093s: OFDM+6615, RTS+6311, nessun incrementoHT/VHT/MCS.
Questo sostiene TXlegacy nel percorso attuale. Configtx_rate24 richiede
esplicitamente legacy: risultato coerente, NON dimostra hardware incapaceHT.
Istogramma non distingue bitrateOFDM6/12/24/54; bitrate PC per-pacchetto
ancora NON verificato. RTS è contatore firmware, non captureRTS radio;
non attribuire automaticamente ogni incremento a un singolo pacchetto o
asserire che sia la causa del limite. Monitor non vede controlframes.

Ultimo campione dopo off ha azzerato i contatori. Primo/ultimo campione
entrambi0 avrebbero nascosto la transizione: analyzer corretto per verificare
OGNI coppia consecutiva, non solo endpoint. Self-test sequenza0/1/0 aggiunto
passato. Delta intera sessione ora dichiarato non valido per reset;
finestre invio/Upload precedenti al reset restano valide. Dati raw conservati.

11.900submit/completion correlati: 11.892successACK-named,8NOACK,0DISCARD;
pendingfinali0,picco51,zeroIDreuse/unmatched. 10.630messaggi HTT di completion
dati osservati, TUTTI num_msdus1: non emergono completion multi-MSDU;
restano possibili raggruppamento interrupt/notifiche e code firmware.
Grandi frame in finestraCLI6121: mediana33,848ms,p9546,240ms,
p99105,271ms,max112,992ms. Intervalli non sono airtime né provaACKfisici.

Trace drop/overrun0, istanza rimossa, debug/trace globali invariati.
OriginaleEE75841D3B45284B3402DCF e AirDropoff verificati indipendentemente;
un timeout revisioneCLI, unico retry riuscito. Nessuna nuova prova avviata.
Log privati, transfer/HTT/TX analysis e completion-bundles.json salvati.
Nessuna integrazionewidget/permanente o gitwrite.

Prossima prova motivata: richiestaHTMCS su20MHz (supportata già daTxRate e
limitata alle capacitàHT annunciate dall'iPhone), verificando che firmware
conti davveroHT; non limitarsi a cambiare numero legacy24->54. In parallelo
capire policyRTS nel percorso driver/firmware e limite visibilità. MCS7 è
1SS/20, non richiede80MHz; successo della sola richiesta non garantisce
adozione firmware. Nessuna promessa di guadagno prima misura ripetuta.


## Prova HT MCS7 preparata, in attesa trasferimento

Utente «procedi»: channel44-htt-mcs7-20261101. Unica variazione profilo
rispetto live-xac66s73: tx_rate24 -> mcs7,1SS/20MHz/LGI. Package/binarye4ee
identici, noACK/QoSoff/AMSDUoff/BAoff, ITv2 autonomo44/20. Nessuna build
né modifica Rust/kernel/firmware. Configbindtemporaneo nuovoSHA verificato;
originali radio.toml/drivers.toml non scritti. Nessun nuovo maskiwbitrate.

Software già esistente TxRate::for_peer limita MCS alle HTcap annunciate;
seMCS7non supportato tornaBASIC12. Metadatarequest PC separata daRXiPhone,
nuovi campi transfer pc_requested_rates/ht_requested_frames/
ht_mcs7_requested_frames/ht_request_observed; fallback resta diagnosticabile.
RichiestaHT osservata NON prova usoHT firmware. Stessa acquisizioneHTT,
tracecompletionnum_msdus e ripristino completo/mainwatchdog collaudati.

Self-test invarianti profilo/package/hash, richiestaHT vsRX/fallback,
decoder/analyzer bounds/reset e recovery preesistenti passati. Originale
EE75841D3B45284B3402DCF e CLIoff verificati prima terminale. Prova guidata
attendeInvio/iPhoneTutti10min, invioZIP8MiB+ritornoSHA; esitoDAACQUISIRE.
Nessuna integrazionewidget/permanente o branch/commit/PR/push.


## MCS7 richiesto osservato, firmware ancora OFDM: live-k1p6wgcq

channel44-htt-mcs7-20261101/live-k1p6wgcq: result0/controller0/RESTORE_OKtrue.
Upload PC -> iPhone8,441s, CLI14,240s; ritorno12,217s, SHA256 ricontrollato
identico. Precedente legacy24 con medesima diagnostica8,342s/12,687s:
nessun vantaggio upload dimostrato (singoli campioni, no conclusioni sul
miglioramento del ritorno). Profilo solo tx_rate mcs7/1SS/20/LGI cambiato.

Metadata uscita: 10.002 frame richiedono HT_MCS7_20MHz_GIlong;581legacy12
per traffico base. Nessun fallback totale software per capacità peer;
ht_request_observedtrue. Non confondere i 10.002 request con trasmissioniRF.

HTT41campioni, lost0, capture_errornull, mask ripristinata. FinestraCLI:
15campioni, delta14,187s, OFDM+7423, RTS+6835, HT/VHT/MCS/NSS/BW/SGI0.
FinestraUpload:8campioni, delta interno7,097s, OFDM+6388, RTS+6106,
HT/VHT/MCS0. Il cambiamento della richiesta non emerge come usoHT nei
contatoriTX firmware. Supporta richiesta non applicata lungo driver/firmware;
non isola ancora la causa né rivela bitrateOFDM effettivo6/12/24/54.
ContatoriRTS non sono captureRTS né prova che RTS causi il limite.
Ultimo campione off resetta contatori; analyzer scarta correttamente delta
intera sessione e conserva finestre precedenti al reset.

FinestraCLI6722submit/completion (6379tid16,343tid17),6702successACK-named,
20NOACK,0DISCARD; pendingfinali0, picco sessione40,0reuse/unmatched.
Grandi frame6135: mediana26,520ms,p9537,564ms,p99102,767ms,max345,765ms.
Tempi includono code/notifiche, nonairtime. 10.664completionHTT dati,
tutti num_msdus1. RXiPhone9828 soprattuttoMCS1/20SGI8381frame; dueMCS7
ricevuti non sono evidenza di TXPC HT. CaptureAFPACKETdrop0, no control.

Trace drop/overrun0, istanza rimossa, globaltrace/debug invariati, driver
originaleEE75841D3B45284B3402DCF e CLIoff verificati indipendentemente.
AnalisiHTT/TX, transfer con Uploadwall/timezone, receiverlogprivato e
completion-bundles.json salvati. Nessuna altra prova aperta né integrazione
widget/config permanente o branch/commit/PR/push.

Prossimo approfondimento: percorso injection ath10k NativeWiFi, selezione
vdev/peer e rate/protezioneRTS firmware. Sorgente htt_tx.c seleziona vdev da
scan/vif/monitor/default0; tutti i TX di questo test vdev0. NON attribuire
vdev0 a una interfaccia specifica senza verificarne mapping effettivo.
Evitare altri numeriMCS/80MHz finché non si capisce dove si applica il rate.


## Lettura percorso TX: richiesta radiotap e controllo WMI distinti

Utente «come lo capiamo?»: ispezione sola lettura delle copie sorgenti kernel
6.18.36 già archiviate. htt_tx.c ath10k_htt_tx_32 costruisce cmd_tx con
flags/vdev/TID/len/id/frags/peer/freq; non copia MCS o control.rates del singolo
frame nel descrittore esaminato. Questo fornisce una spiegazione candidata
alla richiesta radiotapHT senza incrementoHT firmware; non basta a isolare
tutti gli stadi intermedi o il rateRF preciso.

mac.c:8312 ath10k_mac_set_fixed_rate_params usa invece WMI vdev_set_param
fixed_rate/nss/sgi/ldpc, vdev scelto dall'arvif. Quindi precedente iw accettato
non garantisce controllo dello stesso vdev usato dall'injection. htt_tx.c:1150
sceglie scan/vif/monitor/default0; mapping effettivo vdev0 va ancora misurato.
mac.c:1365 ath10k_recalc_rtscts_prot imposta WMIenable_rtscts con profilo
che dipende da num_legacy_stations; contatoreRTS non isola policy o causa.

Prossimo ordine diagnostico: tracciare mapping vdev/interfacce e parametriWMI
in setup; verificare se rate nativo raggiunge vdevTX; solo dopo provare
HT nativo suquelvdev con contatori, separando RTS come variabile successiva.
Non cambiare contemporaneamente width/ACK/RTS/rate; nessuna prova hardware
avviata in questa lettura, nessuna modifica driver/installazione/widget/git.


## Mappatura vdev/WMI preparata, senza iPhone né trasferimenti

Utente autorizza controlli e test. channel44-vdev-map-20261101: riusa
baselinee4ee/radio24/noACK/QoSoff/AMSDUoff/BAoff, ITv2 autonomo44/20 e
ripristino completo/mainwatchdog660s esistente. Nessuna build/installazione
permanente o modifica prodotto. Utente lancia test-map.py da kitty, sudo
locale. Non serve iPhone; nessunZIPtrasferito, nessun sent/hash fittizio.

Traceprivata esistente estesa: MAClevel16 msgmac*, WMIlevel2 wmi tlv vdev*,
STAlevel4194304 mac vdev *peer*. Prima CLIon, conserva eventi creazionevdev,
rateparams eRTS. Globaltrace/debug_mask invariati. HTTmask16 eperfmetadata
esistenti restano attivi con identico cleanup. Fonti ufficiali v6.18.36
wmi-tlv.c/wmi.h/wmi-tlv.h lette viaGitHub; estratti numerati eURLmanifest.
Vdevtype2STA/3IBSS/4MONITOR. Param IDs ricavati dall'enum TLV archiviato.

Prova: CLIon, checkstationnonassociata/44/20 e snapshotiwdev; baseline4s;
iwIBSS legacy24, HT7only, HT7+legacy24, resetallrates,2spercomando; CLIoff
poi restore driver/backend/NM. Rifiuti registrati come dati diagnostici,
nessun bypass basicrates/kernel. Analyze-map.py correla wall/mono comandi,
creazionevdevtype, TXvdev/TID eparametriWMI senza stampareMACpeer.
WMIgenerazione/submission NON prova adozione firmware o bitrateRF.

Selftest mapping/finestre/eventi eprobe simulata conHTrejected, reset,
off anche dopo onfallito passati; recovery esistente passata. Originale
EE75841D3B45284B3402DCF e CLIoff verificati prima terminale. Terminale
aperto attendeInvio; esitohardwareDAACQUISIRE. Nessun nuovo testZIP o
modificawidget/permanente, nessun branch/commit/PR/push.


## Mappatura completata: vdev corretto, HT misto non imposta rate fisso

channel44-vdev-map-20261101/live-vbeli2kz result0/controller0,
mapping_completedtrue/RESTORE_OKtrue. NessunZIP o iPhone necessario.
Durante CLIon creazioneIBSS WMItype3/vdev0 e monitorvdev1. Snapshot iw e
comando nativeowlyibss0 corrispondono aMACfixedratevdev0; TX244tid16+
320tid17 entrambi vdev0. Il rate nativo non sta colpendo il vdev sbagliato.
IDvdev riciclati dopoCLIoff (station/P2P): non interpretare lista totale
creazioni come interfacce contemporanee o mapping permanente.

legacy24 accettato, MACfixedratevdev0 code0x01/nss1/sgi0;
WMI TLVvdev0param27FIXED_RATE=0x01,34NSS=1,28SGI=0,29LDPC=1.
HT7only: exit234/kernel-EINVAL22, nessun MACfixedrate o WMIsetparam nella
finestra comando. HT7+legacy24 accettato, maMACfixedrate0xff eWMIparam27
0xff: automatico, NON HT7 fisso. Resetallrates invia anch'esso0xff.
Conferma hardware la distinzione tra comando iw riuscito e rateHTimpostato.

SetupIBSS WMIrts_thresholdparam1=0xffffffff, enable_rtsctsparam44=0x11
(profilo driver). Soglia apparentemente disabilitata non esclude protezione
RTS automatica/seconda rate series nel firmware. Non provata causalità
RTS rispetto alla velocità; nessuna modificaRTS inquestaprova.

15campioniHTT lost0/capture_errornull, maskrestoredtrue. Traceoverrun/drop0,
istanza rimossa eglobaltrace/debug invariati. Originaleath
EE75841D3B45284B3402DCF eCLIoff verificati fuori cattura. Findings.json,
mapping-analysis.json/tx-trace.txt e log privati conservati.

Ricerca controlloWMIalternativo: /proc/config.gz dice
CONFIG_NL80211_TESTMODE non impostato; testmode.c ufficiale v6.18.36 inoltre
limita ATH10K_TM_CMD_WMI aATH10K_STATE_UTF, nonnormale firmwareoperativo.
Non usareUTF/firmwaretest perAirDrop o fingere controlloWMI disponibile.

Risultato restringe il passo successivo: capire rifiutoHTonly/basicrates e
se serve un controllo diagnostico separato e minimo del rateWMI, conservando
ratelegacy di management. Non serve ripetere radiotapMCS7 né cambiare80MHz.
Nessuna variante ath10k nuova compilata/caricata, nessuna modifica permanente,
widget, branch/commit/PR/push. Testmodefonte primaria consultata soltanto.


## VincoloHT identificato, variante ath10k_core compilata, smoke pronto

Utente «procedi». Fonti ufficiali v6.18.36 mac80211cfg.c:3715-3742:
maschera suinterfaccia attiva deve conservare almeno un legacybasicrate;
HTonly viene rifiutato prima drv_set_bitrate_mask. ath10k conta tutti i
rate e legacy24+HT7 nonè singolorate; ramo singleNSS invia0xff. Coerente
con provaWMI acquisita. Firmware nonannuncia PEER_TID_CONFIGS néEXT;
TIDsettings salvate perpeerQoS nonrisolvono injectiontid16. Nessun UTF.

channel44-ht-driver-20261101:64fileath10k ufficiali scaricati viaGitHub,
GitblobSHA1 verificati, athheadercomuni giàarchiviati; buildstock evariante
con headersinstallati originali6.18.36-1-lts, GCC16.1.1. Nessuna modifica
sistemaheaders/firmware. Solo mac.cpatchato: boolairdrop_ht_test0400 defaultoff;
helper richiedePCI168c:0042,QCA9377,IBSS,5220/HT20, mascheraexactlegacy24+
MCS7senzaaltreHT/VHT,GIdefault. Soloinquelcaso sceglieWMIHT0x87/NSS1,
altrimentiperconstock. Conserva basicratecheck kernel egestionerate management,
multicast/regolatorio/potenza/DFS/EEPROM/noACK/RTS/aggregazione/frame_mode.

ActualCguard compilato e testato perdefaultoff/card/bus/freq/width/GI/mask,
tuttiHT/VHTextrabits rifiutati. Buildstock/variante passate. Vermagicidentico;
stocksrcversion7526A2B02E94546E1923A35 NON ugualedistribuitoA082...;
non usarlo comeprovaABI. DiecistruttureBTF loaded/stock/variante identiche,
60exportnames identici aModule.symversinstallato eambeduebuild. Nonè
certificazioneruntimeABIcompleta. CandidatasrcversionDB033CA7B1181FF5A9BBF65,
SHA2560732813b450b70b320466c01042f430e1d8e9231294ae7fc7f80b2312c9d04db.

channel44-ht-driver-smoke-20261101 pronto, test-map.py. Riusa probe senza
telefono/ZIP: corehashpinned copiato0600 in /run, insmodcoreconparametro1
primaPCI, assertcandidateversion/parametroY. StessoITv2 ebaselineOwly24,
tracceMAC/WMI/HTT, legacy24/HTonly/HTmixed/reset. Watchdog/recoveryesistenti
scaricanoPCI/core/ath ecaricanooriginali; mainassertoriginalcoreA082... dopo
restore. Selfteststaging/hash/loadorder/watchdog/parametronopersist passato.

Preflight originalecoreA082DD95309E1D00A1EED1F/athEE75841D3B45284B3402DCF e
CLIoff verificati. NUOVOmodulocore soltanto compilato, NONancoracaricato;
terminale guidato attendeavvio, esitohardwareDAACQUISIRE. Nessun guadagnoHT
presunto. Nessuna installazionepermanente o modificawidget/gitwrite.


## Smoke nuovo core concluso: WMIHT7 reale, originali ripristinati

channel44-ht-driver-smoke-20261101/live-o0w85mzk eseguito durante la turnata:
result0/controller0/mapping_completedtrue/RESTORE_OKtrue. Candidata caricata
con parametroY e srcversionDB033... verificati dal supervisor; CLIon44/20,
nessuntelefono/ZIP. Legacy24 ->WMIparam27code0x01, HTonly ancoraEINVAL,
HT7+legacy24 ->MACfixedrate0x87/NSS1/sgi0 eWMIvdev0param27=0x87;
reset ->0xff. Confermafunzione del controllo separato lasciando intatto
il basicratecheck di mac80211. NON prova ancora TXRF HT o guadagnovelocità.

Trace/HTT senzaerrori, overrun/drop0, maskripristinata, istanza rimossa e
globaltrace/debug invariati. Moduloath10k_coreoriginaleA082DD95309E1D00A1EED1F
eathEE75841D3B45284B3402DCF verificati fuori cattura, CLIoff verificato.
Nessun modulo installato sufilesystem di sistema; main/watchdogrestore
esistente ha completato anche il nuovo core. Risultati in findings.json,
mapping-analysis.json e logprivati. Prossimo passoZIP con controlloWMIHT
attivo e conteggioHT firmware; esitoRF ancora ignoto. No gitwrite/widget.


## Prova ZIP con controlloHTWMI pronta

channel44-ht-driver-transfer-20261101: stesso coreSHA0732813b... dello smoke
riuscito, stessa varianteITv2 ebaselineOwlye4ee; profiloradioMCS7 byteidentico
al precedente live-k1p6wgcq (8,441s/12,217s). Nessun cambioACK/RTS/QoS/
AMSDU/BA/width. Unico controllonuovo: nativeiw legacy24+HT7 dopo check44/20
prima discovery/capture/invio, oraWMI0x87 conmodulo diagnosticocollaudato.

Riuso flussotestZIP+ritornoSHA, traceMAC/WMI/TX eHTTstatsmask16. Wrapper
unprivileged derivauser_trial giàcollaudato tramiteinspect e sostituzione
unicaancoraassertata; nessuna importazioneprivilegiata dalrepo. Native
failure alzaerrore e passa dafinallyoff+restoremainsupervisor. Core/profile/
packagehash verificati, rootstaging/hash/loadorder eoriginalcoreassert
riusati da smoke. Selftestprofilo/package/modulo/ordinecommand eparserpassati.

Nuovo terminale attendeInvio/iPhoneTutti10min; esitoRFHT/speedDAACQUISIRE.
WMI0x87 nonèancoraprovaTXHT. Originalicore/ath eCLIoff verificati dopo
smoke prima diquestanuovaprova. Nessun permanente/widget/gitwrite.


## ZIP HT fisso fallito prima HTTP: HT presente, connessione8770 assente

Utente «test fatto ma non mi è attivata la richiesta sull'iphone».
channel44-ht-driver-transfer-20261101/live-l98g44bo result1, controller0,
RESTORE_OKtrue. NativeHTmaskexit0; senderexit3 dopo63,883s, messaggio
«never opened8770». NessunPOSTDiscover/Ask/Upload: nessunZIPiniziato o
ritornoSHAatteso. Non interpretare come rifiuto utente o filecorrotto.

HTT69campioni lost0/capture_errornull, sendwindow63campioni62,830s:
MCS7+945,NSS1+945,BW20+945,HTpreamble+945,OFDM+2489,
STBCMCS7+945,LDPC+945,SGI0,RTS0. Perprima volta contatori firmware
registranoHT7 con controlloWMI, ma questo non prova ricezioneiPhone.
AFout1029frame:64richiesteHT7/20LGI e965legacy12. RXiPhonesolo5frame
legacy12, nessunRXHT. Firmwaresendwindow:2571completion,2508success,
63NOACK (tid16),0DISCARD,nessun grandeframe.945=63*15 è compatibile con
ripetuti tentativiHT; NON prova conteggioRF preciso o15retryperframe.
StatusNOACK non è perdita percentuale. STBCcounterelevato è dato da
verificare, non diagnosi né autorizzazione a togglearlo.

TuttiIDcorrelati, pendingfinali0/picco4. Trace/AFdrop0, istanzarimossa,
globaltrace/debug invariati, HTTmaskripristinata. OriginalicoreA082... e
athEE758... ricontrollati; CLIoffverificato dopo unico retry pertimeout
revisione automatica. Nessun permanentewidget/gitwrite.

Il messaggio CLI «receiver notopen» non distingue telefono noninricezione
da linkHTnonfunzionante. Nuova prova channel44-ht-connect-ab-20261101:
stesso coreSHA0732813b... eprofiloMCS7, TCP8770legacy24 -> HT7 -> legacy24;
primaA deveaprire altrimentiB saltata. Socketstdlib con2stimeout distingue
open/refused/timeout/networkerror; helperwakeBLE giàinstallato riusato come
utente, costante suABC, cleanupcontextmanager. NessunHTTP/ZIPrichiesto.

Selftestsocketerrori, sequenzaABA ebaselineunavailable->skipHT, reset/off,
modulehash/profile ecompilazioneROOTwatchdog passati. Terminale guidato
richiede iPhoneTutti10min/sbloccato/pannelloCondividiAirDrop aperto. Esito
DAACQUISIRE. ProfiliFW/regolatorio/ACK/QoS/STBC/RTS non modificati oltre
al rateWMI della prova. Nessun nuovo modulo o rebuild; stesso corecollaudato.


## A/B/A valido: connessione legacy funziona, HT7 timeout, legacy riprende

Utente «potrei aver sbagliato il test». Log mostrano sequenza completata
coerentemente, nessun errore che richieda ripetizione peresecuzione:
channel44-ht-connect-ab-20261101/live-z37agize result0/controller0,
mapping_completedtrue, wake_registeredtrue, RESTORE_OKtrue.
AlegacyprimaTCP8770open1/1; BHT7timeout3/3; Alegacydopoopen3/3.
Stesso coreSHA0732813b..., profiloMCS7,44/20 e BLEwake continuo;
comandiWMIvdev0param27 rispettivamente0x01 ->0x87 ->0x01 verificati.

Confronto sostiene problema di connettività introdotto dalla modalitàHT7
in questa configurazione, senza imputarlo al pannelloiPhone o alla
mancanza di ascolto: servizio raggiungibile prima e dopo il solo cambio
rate. Unasequenza non isola causaPHY né prova guasto genericoHW/firmware.
NessunHTTP/ZIP richiesto, nessunpopup accettazione atteso.

FaseHT8campioniHTT, delta interno7,097s: MCS7/NSS1/BW20/HTpream/STBC7
+180,OFDM+303,RTS0; completionnell'interafase347successACK-named/15NOACK.
Legacydopo3campioni, delta2,023s: OFDM+122,HT/MCS/STBC0,RTS0;
158success/0NOACK. Legacyprima rapidoopen:0campioniHTT interni alla breve
fase, noninventaredelta;14success/0NOACK. Metriche HTT ecompletion hanno
finestre differenti: non calcolare retry-ratio accoppiando180e15.

HTTlost0, traceoverrun/drop0; istanzarimossa/globaltrace-debug invariati,
originalicoreA082DD95309E1D00A1EED1F eathEE75841D3B45284B3402DCF
verificati, CLIoffverificato. connection-analysis.json, WMIeprivate log
salvati. WarnGLFWNoReplynel terminal.log non ha impedito la sequenza e
noncorrelato ai timeoutTCP; nessuna nuova provaaperta.

Prossimo passo: verificare formato/semantica STBCcounter eparametriHT
(preservando controllolegacy), percorsopeer/nonQoS/NativeWiFi, prima di
nuove variazioni o ZIP. Non dichiarare STBC causa provata. Nessun cambio
ulteriore a sorgenti driver/config/widget o installazione permanente/git.


## Ripetizione A/B/A richiesta: pannello iPhone aperto prima dell'avvio

Utente precisa di aver aperto Condividi/AirDrop dopo l'inizio del precedente
live-z37agize. La sequenza registrata resta corretta, ma la disponibilità
ricevitore può essere cambiata durante la prova: conclusione causale sul
rateHT da mantenere provvisoria finché confronto ripetuto con pannello
aperto per l'intera sequenza. Non attribuire errore certo all'operatore o
al firmware dai soli dati precedenti.

Utente «si ci sono»: rilancio identico channel44-ht-connect-ab-20261101,
nessuna modifica a core/profile/ACK/STBC/RTS/QoS. iPhone sbloccato,
Tutti10min e Condividi->AirDrop già aperto prima Invio e mantenuto aperto
per tutte le fasi. Ancora TCP soltanto, nessunZIP o richiesta accettazione.
Preflight coreA082DD95309E1D00A1EED1F/athEE75841D3B45284B3402DCF,
CLIoff verificati; self-test controlli/cleanup passato. Nuovo terminale
con log separato, esito della ripetizione DAACQUISIRE. Nessun gitwrite.


## Ripetizione con iPhone pronto conferma timeout specifico della faseHT7

Utente conferma «okay ora fatto bene», pannelloCondividi/AirDrop giàaperto
prima e mantenuto nella sequenza. channel44-ht-connect-ab-20261101/
live-d9kpl7j3: result0/controller0/mapping_completedtrue/RESTORE_OKtrue,
wake_registeredtrue. Legacyprimaopen1/1, HT7timeout3/3, legacydopoopen3/3.
WMIvdev0param27 osservato0x01 ->0x87 ->0x01. Ripete esattamente precedente
risultato, ora con disponibilità telefono confermata dall'utente dall'inizio.
Conferma problema riproducibile della configurazioneHT7, nonnecessità di
ripetere ancora la stessa prova per attivazione tardiva. Non identifica
ancora causa specifica o guasto generale dell'hardware/firmware.

FaseHT:8campioniHTT, delta interno7,093s, MCS7/NSS1/BW20/HTpream/STBC7
+315,OFDM+242,RTS0. Completionnella fase384success/25NOACK. Legacydopo:
3campioni, delta2,027s OFDM+58,HT/MCS/STBC0,RTS0;139success/0NOACK.
Legacyprima connessione rapida:0campioni interni,15success/0NOACK;
nessun deltaHTT inventato. Finestrestats/completion differenti, non dedurre
numero retry preciso. ContatoreSTBC rimane dato da verificare.

HTTlost0 e traceoverrun/drop0, maskripristinata, istanzarimossa,
globaltrace/debug invariati. OriginalicoreA082DD95309E1D00A1EED1F e
athEE75841D3B45284B3402DCF, CLIoff verificati fuori cattura.
connection-analysis.json/WMI/trace/logprivati conservati. Nessun nuovo
terminale aperto inquesta lettura; nessuna modifica codice/kernel/widget/git.

Prossimo controllo utile da preparare: HTMCS0/1SS/20/LGI a rate basso,
con stesso confronto legacy/HT/legacy, per distinguere MCS7 alto da problema
HT piùgenerale. Il modulo attuale accetta ESATTAMENTE MCS7: non inviare
MCS0 con quelmodulo fingendo ratefisicoHT0. Eventuale estensione va prima
compilata/verificata/hashpinned comevariante separata e testata con contatori.
Nessuna estensione già implementata o installata inquestaturnata.


## MCS0 separato preparato per confronto TCP

Utente «okay proviamo». channel44-ht-driver-mcs0-20261101: nuova variante
separata dalmodulo MCS7 conservato. Due differenze funzionali rispetto a7:
helper accetta solo legacy24+MCS0, WMIrate0x80; etichette aggiornate.
Stesse guardie defaultoff0400/PCI168c:0042/QCA9377/IBSS44/HT20/LGI/1SS;
nessuna modificaACK/RTS/STBC/LDPC/aggregazione/frame-mode/regolatorio oFW.
ActualCguard passa e rifiuta esplicitamente7 ealtri bit HT/VHT. Buildpassata
contro headersinstallati6.18.36-1-lts, no modificheheaderssistema.

Candidata4627E241815236B4522D6D0,
SHA175a71eb31f04dd7b56cc4ecaf585d64db9d0ca7ed04ec04c265507e7539dfea.
Vermagic,60exportnames e10layoutBTF corrispondono aireferimenti installati;
noncertificazioneruntimecompleta. Sorgenti upstream64file condividono
provenienza giàverificata; solo mac.c differisce dallo stock.

channel44-ht0-connect-ab-20261101: stesso probeTCP8770 A/B/A, maschera
nativeMCS0 eprofiloOwlymcs0. Wrapperasserta una sola sostituzione diognuno
hashcore/srcversion/radioprofile nellaROOT giàcollaudata. LabelB ht0;
legacyprima deveopen, poitreHT0 e trelegacydopo. BLEwake costante,
noZIP/popup, iPhonepannello aperto da primaInvio per tutta la prova.
Unitguard/profilo/maskmodulo, ABA/skipHT/quandoAbaseassente, reset/off,
compileROOT/watchdog passati. AttesiWMI0x80 econtatoriHTT MCS0, non
presumere adozioneFW. Niente nuovodriver sulsistema finchéterminaleavviato;
nessuna installazionepermanente/widget/gitwrite. EsitohardwareDAACQUISIRE.


## Ripetizione MCS0 richiesta dall’utente

Utente «ho sbagliato rifacciamolo». La precedente sessione
channel44-ht0-connect-ab-20261101/live-zvtx_m7z ha completato il ripristino
(result0/controller0/RESTORE_OKtrue): legacyprimaopen1/1, HT0timeout3/3,
legacydopoopen3/3. Per la segnalazione dell’utente, mantenerla provvisoria
senza dedurne una nuova conclusione causale. OriginalicoreA082.../athEE758...
e CLIoff già verificati dopo la sessione.
Riaperto lo stesso test senza modifiche, con log terminale separato e
precondizione iPhone sbloccato/Tutti10min/Condividi->AirDrop aperto PRIMA
Invio e per l’intera sequenza. Nessun ZIP o popup atteso; nuovo esito pendente.
Nessuna modifica permanente/widget/branch/commit/PR/push.


## Ripetizione MCS0 conclusa: anche HT basso interrompe TCP

Utente «okay fatto». channel44-ht0-connect-ab-20261101/live-5eka9evv:
result0/controller0/mapping_completedtrue/RESTORE_OKtrue, BLEwake registrato.
Legacyprima TCP8770open1/1; HT0timeout3/3; legacydopoopen3/3.
WMIvdev0param27 0x01 ->0x80 ->0x01 verificato dalla trace. Test autonomo
44/20 senza station associata; nessun ZIP o HTTP/popup richiesto.
FaseHT0:9campioniHTT, delta interno8,103s MCS0/NSS1/BW20/HT/STBC0/LDPC
+270, OFDM+309, SGI0, RTS0. Legacydopo4campioni, delta3,043s OFDM+93,
HT/MCS/STBC0, RTS+3. PrimaA troppo breve: nessun deltaHTT disponibile.
Contatori marginali firmware non provano bitrate RF per singolo pacchetto,
ricezione iPhone, retry-ratio o causa STBC/LDPC.
HTTlost0/maskrestoredtrue; traceoverrun/drop0, istanza rimossa eglobaltrace/
debug invariati. Analisi mapping e connection-analysis.json conservate.
Postflight indipendente: coreA082DD95309E1D00A1EED1F,
athEE75841D3B45284B3402DCF, CLIoff, station canale100/80 center5530.
La sola riduzione daHT7 aHT0 non risolve: indagare configurazione/percorsoHT
comune (peer/NativeWiFi e codifiche STBC/LDPC), senza attribuire già la causa
al segnale o al firmware. Nessuna nuova variazione radio o integrazione
widget avviata, nessuna modifica permanente/branch/commit/PR/push.


## Prova HT0 con solo LDPC disabilitato preparata

Utente «okay proviamo». Lettura sorgente kernel archiviato: bitrate_mask
inizializza ldpc dal capability hardware e invia WMIvdevparam29=1; il ramo
HT0 precedente non lo cambia. STBC ha parametri separati e resta invariato.
Nuova channel44-ht0-no-ldpc-driver-20261101: stessi sorgenti della candidata
MCS0, unica aggiunta funzionale ldpc=0 dentro la guardia HT0 esistente;
legacy/reset/default-off e ogni altra maschera restano stock. Nessuna
modifica STBC/RTS/ACK/QoS/width/firmware/regolatorio/EEPROM.
GuardiaC reale compilata e testata, diff esatto contro candidata precedente
assertato, altri63file uguali allo stock. Build kernel6.18.36-1-lts passata;
vermagic,60exportnames e10layout tipi corrispondono alla precedente candidata.
SHA39d9e90f51bdb4607b74c60af9577f04b2af62b92e4c939070fbd496cc691ae3,
srcversion6EA8C3B7711CE6316CC876F. Modulo non installato permanentemente.

channel44-ht0-no-ldpc-connect-20261101: stesso A/B/A TCP8770, radio.toml e
backend byteidentici al testHT0 precedente, BLEwake costante. Rootletterale
riusata con sostituzione assertata solo hash/srcversion modulo; staging0600,
parametroY, main/watchdog/ripristino originali invariati. Selftest ABA,
baselineunavailable->skipHT, reset/off, compilazioneROOT/watchdog e hash
package/modulo/config/decoder passati. OriginalicoreA082.../athEE758... letti.
Termine apertura GUI: primo tentativo revisione automatica scaduto senza
esecuzione; unico retry riuscito, kittyPID2044747. Terminale attende operatore;
iPhone sbloccato/Tutti10min/pannelloCondividiAirDrop PRIMA Invio e per tutte
le fasi. NoZIP/HTTP/popup. Attesi WMIHT0x80 conLDPC0 econtatoriHTT;
esito hardware DAACQUISIRE, nessun miglioramento ancora dimostrato.
Nessuna modifica widget/permanente/branch/commit/PR/push.


## HT0 senza LDPC concluso: nessun recupero TCP, disabilitazione verificata

Utente «controllo finito». channel44-ht0-no-ldpc-connect-20261101/live-vxhh0nmo:
result0/controller0/mapping_completedtrue/RESTORE_OKtrue, BLEwake registrato.
TCP8770 legacyprimaopen1/1, HT0timeout3/3, legacydopoopen3/3. NessunZIP.
WMIvdev0param27 0x01->0x80->0x01 eparam29LDPC 1->0->1 verificati.
HTT nella faseHT0:9campioni, delta8,110s MCS0/NSS1/BW20/HT/STBC0 +300,
OFDM+326, LDPC0, SGI0, RTS0. Dunque comando LDPCoff accompagnato da
contatoreLDPC senza incrementi; attivitàHT resta, connessione non recupera.
Questo esclude LDPCoff come soluzione sufficiente nella configurazione
provata, senza attribuire già causa a STBC o dedurre formatoRF perpacket.
Legacydopo3campioni delta2,027s OFDM+71, HT/MCS/STBC/LDPC0, RTS+3.
PrimaA troppo breve: nessun deltaHTT. HTTlost0 e maskripristinata;
traceoverrun/drop0, istanzarimossa/globaltrace-debug invariati.
Analisi mapping/connection e logprivati conservati. Postflight indipendente:
originalicoreA082DD95309E1D00A1EED1F/athEE75841D3B45284B3402DCF,
CLIoff; rete adesso104/80 center5530 (in precedenza100/80, non assumere44).
Prossimo parametro da verificare: STBC separato mantenendo LDPC costante;
prima stabilire comando/supporto e cleanup, non dichiarare causa provata.
Nessuna nuova prova avviata o modifica permanente/widget/branch/commit/PR/push.


## Prova TX_STBCoff preparata, LDPCoff invariato

Utente «okay procediamo». Sorgenti ufficiali archiviati v6.18.36:
wmi-tlv.c mappa tx_stbc al VDEV_PARAM_TX_STBC; enum reale inwmi-tlv.h
compilato/assertato TX_STBC30/LDPC29. mac.c stock non invia esplicitamente
TX_STBC durante il percorso fixedrate esaminato. Nessun default firmware
inventato o dedotto dal solo contatore.

channel44-ht0-no-stbc-driver-20261101: identico alla candidata HT0/LDPCoff
precedente più solo comando WMI TX_STBC=0, sotto conf_mutex, dietro stessa
guardia exactMCS0/PCI168c0042/QCA9377/IBSS44/HT20/defaultoff0400, prima
setfixedrate. Fallimento hostWMI interrompe setup. LDPCoff resta invariato;
nessun cambio ACK/RTS/QoS/width/FW/regolatorio/EEPROM. STBC0 resta sul vdev
temporaneo anche nel legacydopo (OFDM): resetbitrates NON ripristina STBC.
Ripristino tramite CLIoff->distruzionevdev e main/watchdog->reloadoriginali;
nessun valore predefinito indovinato/reimpostato. Documentato inREADME.

ActualCguard ebloccoWMI testati perdefaultoff/maskerrata/noinvio,
successocontinua/errorabort. Diff esatto precedente +blocco assertato,
altri63file uguali stock. Buildpassata kernel6.18.36-1-lts; vermagic,
60exports e10layouttipi uguali alla precedente candidata. SHA
 a004a7a2f53912b392458f65b1151ae49528fc779b403b635cf3e48747f85e45,
srcversion34230BE6B2988C2BF20A808. Nessuna installazionepermanente.

channel44-ht0-no-stbc-connect-20261101: stesso A/B/A TCP8770 eprofiloMCS0,
BLEwake ebaselinelegacyopen obbligatoria, package/core/config/decoderhash
verificati. LiteralROOT riusata sostituendo soltanto corehash/srcversion;
staging0600,parametroY,watchdog/mainrestoreoriginali invariati. Selftest
ABA/skipHT/resetoff/ROOTwatchdog passato. WMIhostsend non prova adozioneFW:
verificare contatoreSTBC faseHT e LDPC prima di interpretare esitoTCP.
Preflight hostoriginalicoreA082.../athEE758... eCLIoff verificati.
KittyPID2052628 aperto eattendeInvio/sudo locale, iPhoneTutti10min/sbloccato/
pannelloCondividiAirDrop aperto PRIMA e per tutte le fasi. NoZIP/popup.
EsitohardwareDAACQUISIRE; nessun miglioramento presunto. Nessun widget/
configpermanente/branch/commit/PR/push modificato.


## Prima connessione HT riuscita: TX_STBCoff con LDPCoff

Utente «test fatto». channel44-ht0-no-stbc-connect-20261101/live-nn03dbk5:
result0/controller0/mapping_completedtrue/RESTORE_OKtrue, BLEwake registrato.
Legacyprima: primo tentativo refused, secondo open (baseline requisito
soddisfatto); HT0open3/3 con connect6,250/4,912/3,067ms; legacydopoopen3/3.
Nessun ZIP/HTTP, non una misura di throughput o prova velocità AirDrop.

WMIvdev0 nella faseHT: TX_STBCparam30=0, FIXED_RATEparam27=0x80,
LDPCparam29=0. Legacyprima/dopo rate0x01/LDPC1; STBC0 resta sulvdev
attraverso legacydopo e ripristinato dalla distruzionevdev/reloadoriginali.
HTTfaseHT3campioni, delta interno2,027s MCS0/NSS1/BW20/HT +6,
STBC0/LDPC0/SGI0/RTS0, OFDM+63. Legacydopo3campioni delta2,027s OFDM+69,
HT/MCS/STBC/LDPC0, RTS+3. PrimaA uncampione: nessun delta inventato.
Il nuovo comando è accompagnato da assenza incrementiSTBC econnessioneHT
riuscita, mentre HT0/LDPCoff precedente timeout3/3 eSTBC+300. Forte indizio
sulla configurazioneTX_STBC, NON ancora isolamento RF o causa firmware
universale né prova ripetuta nella stessa sessione con HTSTBC on/off.
Non affermare che LDPCoff sia necessario: non testato STBCoff/LDPCon.

HTTlost0/maskrestoredtrue; traceoverrun/drop0, istanzarimossa eglobaltrace/
debug invariati. Connection/mappinganalysis eprivatelog conservati.
Postflight indipendente coreA082DD95309E1D00A1EED1F,
athEE75841D3B45284B3402DCF, CLIoff, station104/80 center5530.
Prossimo passo utile: HT7 conSTBCoff/LDPCoff mantenuti, primaconnettività,
poi ZIP se connessione valida per misurare il guadagno reale. HT0 è stato
scelto perrobustezza diagnostica, non pervelocizzare il trasferimento.
Nessuna nuova prova avviata inquesta lettura, nessuna modifica permanente/
widget/branch/commit/PR/push. Le varianti precedenti restano conservate.


## MCS7 con STBCoff/LDPCoff preparato dopo successo HT0

Utente «okay proviamo». channel44-ht7-no-stbc-driver-20261101 conserva
variante HT0/STBCoff/LDPCoff riuscita, con sole differenze funzionali
maschera esatta legacy24+MCS7 e codiceWMI0x87 inveceMCS0/0x80. Etichette
aggiornate. Stesse guardie defaultoff0400/PCI168c0042/QCA9377/IBSS44/HT20,
1SS/LGI eLDPC0/TX_STBC0; ACK/RTS/QoS/AMSDU/BA/FW/regolatorio invariati.
ActualCguard ebloccoWMI testati (MCS0 rifiutato, success/failure), delta
esatto contro precedente assertato, altri63file uguali stock. Buildpassata
con headers6.18.36-1-lts, vermagic/60exports/10layouttipi coincidono.
SHAae93c7db32a5958fb3ec288580d4a6a5a0829eec00423f652e9ffda6b22235f6,
srcversion5292E77612270AB8D81C465. Nessuna installazionepermanente.

channel44-ht7-no-stbc-connect-20261101 riusa stessaROOT/watchdog con sole
sostituzioni assertate corehash/srcversion/radioprofilehash. ProfiloMCS7,
stesso backendpackage. ProbeHT7 originale estratto viaAST e riusato come
utente, nessuna nuova logica connessione. SelftestA/B/A/baselineunavailable
skipHT/resetoff/ROOTwatchdog passed; pinpackage/core/config/decoderverificati.
Attesi WMIHT0x87/TX_STBC0/LDPC0 econtatoriHTT corrispondenti; nessunRF
presunto. STBC0 permane sulvdev attraverso legacydopo: ripristino mediante
CLIoff/distruzionevdev e main/watchdog reloadoriginali, non resetbitrates.
Preflight originale coreA082.../athEE758... eCLIoff hostverificati. Kitty
PID2060756 aperto, attendeInvio/sudo con iPhoneTutti10min/sbloccato/pannello
CondividiAirDrop giàaperto e mantenuto. TCPsoltanto/noZIP/popup, hardware
DAACQUISIRE. PoiZIPsolo se connessione valida, nessun guadagno giàprovato.
Nessuna modifica widget/permanente/branch/commit/PR/push.


## MCS7/STBCoff/LDPCoff connessione riuscita; ZIP pronto

Utente «test fatto». channel44-ht7-no-stbc-connect-20261101/live-crpof8x1:
result0/controller0/mapping_completedtrue/RESTORE_OKtrue, wake registrato.
Legacyprimaopen1/1, HT7open3/3 (11,718/30,808/3,821ms), legacydopoopen3/3.
WMIvdev0 HTparam27=0x87, TX_STBCparam30=0, LDPCparam29=0 verificati.
HTTfaseHT3campioni delta interno2,027s MCS7/NSS1/BW20/HT +20, OFDM+114,
STBC/LDPC/SGI0, RTS+3. Legacydopo3campioni delta2,027s OFDM+121, HT0;
primaA uncampione, nessun delta. Non prova throughput o bitrateRF perpacket.
HTTlost0/maskrestoredtrue; traceoverrun/drop0, istanzarimossa/globalinvariati.
Postflight indipendente originalicoreA082.../athEE758..., CLIoff e104/80
center5530. Connection/mappinganalysis e logprivati conservati.

Connettività valida: proseguita preparazione ZIP prevista. Nuova
channel44-ht7-no-stbc-transfer-20261101 riusa testZIP precedente senza
nuova logica: solo sostituzione hash/srcversioncore nellaROOTletterale;
core e radio.toml byteidentici al confrontoTCPriuscito, stesso backend.
Selftestpin/modulo/profilo/package/config/decoder, ordine44check->nativeHT
->capture->send eoff/finally/ROOTwatchdog passato. Nessun rebuildaggiuntivo.
KittyPID2072272 aperto, attendeavvio locale. iPhoneTutti10min/CondividiAirDrop;
accettareZIP8MiB poi rimandare lo stesso ZIP alPC perSHA. Stavolta popup
atteso pertrasferimento, non semplice connessione. Misurare Upload distinto
daCLI/discovery/consenso; HTT/STBC/LDPC da verificare sottocarico.
EsitoZIPDAACQUISIRE, nessun miglioramento velocità giàprovato. Main/watchdog
ripristino originali e vdev teardownSTBC invariati. Nessun permanente/widget/
branch/commit/PR/push. Variante veloce ancora NON integrata nelwidget.


## Primo ZIP MCS7/STBCoff/LDPCoff riuscito: upload6,358s

Utente «test fatto». channel44-ht7-no-stbc-transfer-20261101/live-h6cvk00u:
result0/controller0/RESTORE_OKtrue. ZIP8388736B inviato conHTTP200 e
ritornato alPC: SHA256ac2dbab130dd40c255993de77b844273f6871693fa18b8a051afe5a49be85b67
indipendentemente ricalcolato sulfile ricevuto eidentico alloriginale.
Upload POST->200 6,358s (21:22:11,613->21:22:17,971 Europe/Rome);
CLI11,129s distinto daupload/ricerca/consenso. Primo dato promettente contro
storici8–9s, NON ancora confrontoA/B ripetuto o miglioramento generalizzato.
Ritorno POSTUpload->stored16,511s, più lento di precedenti12–13s; include
warning ricevitore «no closing chunk after3s, archive complete; storing».
Non sottrarre ciecamente3s per chiamare restante tempo puroRF. Archivio integro.
Receiverlog salvato privato0600; non pubblicare header/identità/pushtoken.

WMIvdev0TX_STBC30=0,FIXED_RATE27=0x87,LDPC29=0 osservati. HTT50campioni,
lost0/maskrestoredtrue; finestraCLI11campioni delta10,133s MCS7/NSS1/BW20/HT
+6552,OFDM435,STBC/LDPC/SGI0,RTS6517. Finestra internaUpload6campioni
delta5,066s MCS7/NSS1/BW20/HT+6401,OFDM237,STBC/LDPC/SGI0,RTS6398.
I contatori marginali provano attivitàHT sottocarico, nonRFperpacket o
ricezioneperframe. RTS frequente resta dato, noncausa prestazionale provata.
Ultimo off resetta contatori: analyzer rifiuta delta interasessione e
conserva finestre precedenti valide.

AFcapture drop0, richiesteHT7/20LGI10313, legacy12642; RXiPhone9260frame,
MCS1/20LGI8286,MCS0/20LGI974, retrybit1696 (non percentualeperdita).
QoS/AMSDU richiesti0, no control/BAosservati (non provaassenza).
CLI6615submit/completion,6611successACK-named/4NOACK/0discard;
6118grandiframe p5053,770ms,p95108,271ms,p99148,616ms. Include code e
notifiche, nonairtime; pendingfinal0,piccosessione130,0reuse/unmatched.
Non confondere successnoACK conACKfisico o confrontare finestre incompatibili.
Traceoverrun/drop0, istanzarimossa/globaltrace-debug invariati.

Postflight hostoriginalicoreA082DD95309E1D00A1EED1F,
athEE75841D3B45284B3402DCF,CLIoff,station104/80 center5530.
transfer.json con Uploadwall/timezone e ritorno, htt/txanalysis/findings,
tracemetadati eprivatelog conservati. Nessuna prova nuova aperta.
Prossimo confronto utile: legacy vsHT7 a parità di core/STBCoff eassetto,
con ripetizioni e Upload separato daCLI; indagare separatamente chiusura
chunk nelritorno. Nessun widget/permanente/branch/commit/PR/push modificato.


## A/B upload preparato: quattro ZIP nella stessa sessione radio

Utente «okay facciamo prove a b». channel44-rate-ab-20261101: A1legacy24,
B1HT7,A2legacy24,B2HT7, stessoZIP8388736B/hash giàverificato, uploadsoltanto.
Quattro accettazioni iPhone, nessunritorno alPC richiesto inquestoconfronto;
non inventare sent/hash-return dalla prova upload-only. main riusata con
successoab_completed anziché mapping_completed; report ab.json/phasefiles.
Tempi Upload POST->200 separati daCLI/discovery/consenso; interrompe su
sendfallito oUploadmancante/ambiguo/non200/intervallo nonpositivo. Prima
ogniinvio Inviooperatore; controller540s/watchdog660s esistenti, non lasciare
attese indefinite. Activecheck impedisce invio colbackendoriginale se
controllerterminato. On44/20/stationnonassociata verificati; finallyreset/off,
main/watchdog restoreoriginali. Nessuna catturaAF aggiuntiva necessaria:
tracceMAC/WMI/HTT private giàattive misurano entrambiimodi efinestreupload.
Bufferprivato ftrace8192KiB/CPU invece4096 perquattroupload, filtriidentici,
globalinvariati ecleanup esistente. Nessun resetstats nuovo.

Per vero controllo dei codingparameter anche inA, nuova variante separata
channel44-rate-ab-driver-20261101 accetta guardiaexactlegacy24 conHTmask0
oppureBIT7, nessun altrobitHT/VHT; ramo sceglie0x01(OFDM24) o0x87(HT7).
EntrambiNSS1/SGI0/LDPC0 eWMI_TX_STBC0. Defaultoff0400/PCI168c0042/QCA9377/
IBSS44/HT20 invariati, solomac.c deltaassertato rispettoHT7STBCoff; altri63
fileuguali stock. NessunFW/regolatorio/EEPROM/ACK/RTS/QoS/width diverso.
ActualCguard, legacyemptyaccepted/MCS0rejected/bitextra, WMIerrorabort e
selezionerate passati. Buildkernel6.18.36-1-lts, vermagic/60exports/10layout
tipi uguali alla precedente candidata. SHA
c7f676cc061f27a7037052713a15a3e49cda8de3320fb891a0182a5709001207,
srcversion0B6607F256A42B44F7F657A. Modulo noninstallatopermanentemente.

Stesso core caricato UNA volta; alternanza soltanto maschera nativeiw.
Profiloradiotapmcs7 ebackend byteidentici inA/B: requestedmcs7 NONprovaRF;
verificareWMI eHTT OFDMvsHT nelle finestre, STBC/LDPC0 perentrambi.
STBC0 persiste sulvdevtemporaneo finoCLIoff/distruzionevdev, poi reload
originali, non tentare ripristinovaloredefault indovinato conresetbitrates.
ROOTletterale riusata concorehash/srcversionpinned nuovi ebuffersizeprivato;
watchdoginvariato. Selftest parserbounds/success/ambiguity, sequenzaABAB e
maschere, failureB1stops, finallyreset/off dopo faseinterrotta, compilazione
ROOT/watchdog/pin passati. README/patch/manifest archiviati.
Preflight hostoriginalicoreA082.../athEE758... eCLIoff verificati.
KittyPID2118420 aperto eattendeutente, esitoA/BDAACQUISIRE. Telefono fermo,
sbloccatoTutti10min, riaprireCondividiAirDrop aognifase eaccettareZIP.
Nessuna integrazionewidget/permanente/branch/commit/PR/push.


## A/B alternato conferma guadagno upload MCS7: -24,06% tempo medio

Utente «test fatto sembra che i miglioramenti sono concreti».
channel44-rate-ab-20261101/live-ie7dra0u: result0/controller0/ab_completedtrue/
RESTORE_OKtrue. Quattroinvii ZIP8MiB HTTP200 nella stessa sessioneradio,
stessocore/backend/radio44/20/1SS/LGI/STBCoff/LDPCoff eposizione richiesta.
A1legacy24 Upload8,510s; B1HT7 5,807s; A2legacy24 8,167s; B2HT7 6,857s.
MediaA8,3385s, mediaB6,3320s: riduzione tempo24,063%, guadagno throughput
31,688%. EntrambeB piùrapide dientrambeA. Evidenza concreta/ripetuta in
questasessione ma solo2misure/modo, non generalizzare precisionepercentuale
ad ambienti diversi. Questa serieconfronta il rate con STBC/LDPCoff comuni,
nonisola separatamente necessitàLDPCoff o causa universaleSTBC.

CLI: A12,454/12,522s, B13,383/12,918s: tempo totalenondiminuito nella serie,
perché comprende ricerca/consenso; non spacciare24% per miglioramento
end-to-end. Upload misurato daPOST/Upload a200, escluso attesaoperatore.
NessunritornoZIP previsto/richiesto qui: non attribuire a questaserie hash
ritorno; integritàbi-direzionale verificata nella prova live-h6cvk00u.

WMIogniA TX_STBC30=0,FIXED_RATE27=0x01,LDPC29=0; ogniB STBC30=0,
FIXED_RATE27=0x87,LDPC29=0. HTT finestre interne Upload:
A1 9campioni/8,107s OFDM6745, HT/MCS/STBC/LDPC0,RTS4729;
B1 5campioni/4,053s HT7/NSS1/BW20 +5774,OFDM153,STBC/LDPC/SGI0,RTS3463;
A2 8campioni/7,090s OFDM6467,HT/MCS/STBC/LDPC0,RTS2584;
B2 7campioni/6,080s HT7/NSS1/BW20 +6636,OFDM276,STBC/LDPC/SGI0,RTS4712.
I contatori marginali firmware supportanoadozione modiA/B, non provanoRF
perpacket né numeroRTSperpacchetto/perdita. Le finestreHTT non coincidono
con gliinteriUpload: evitare rapporti misti o causalitàRTS nonmisurata.
HTTlost0/maskrestoredtrue, traceoverrun/drop0, istanzarimossa eglobaltrace/
debug invariati. ab-analysis.json include TX perfinestre, mapping-analysis,
ab.json/logsend/tracemetadati conservati privati.

Postflight indipendente hostoriginalicoreA082DD95309E1D00A1EED1F,
athEE75841D3B45284B3402DCF,CLIoff/receivingfalse/visiblefalse verificati.
Prima lettura finalehostrevisioneautomatica scaduta senzaesecuzione; unico
retry breve riuscito. Rete ripristinata secondo supervisorRESTORE_OK,
nessuna seconda letturacanalehost completata inquesta turnata.
Nessun nuovo test aperto, nessuna integrazione widget/configpermanente/
branch/commit/PR/push. CandidataHT7/STBCoff/LDPCoff conservata conrisultati;
widget continua usare backendoriginale finché integrazione autorizzata.


## Integrazione widget autorizzata: preparazione e installazione locale pronta

Utente autorizza applicazione del guadagno alwidget e chiede prossimoobiettivo/
asimmetria. Successivo «continua il lavoro». Nessun branch/commit/PR/push.
Il2novembre ripresa: hostkernel6.18.36-1-lts, originalicoreA082.../athEE758...,
CLIoriginale eAirDropoff verificati. QuickshellusaOMDROP_CLIdefault, processo
in app.scope VSCode, quindi il link ~/.local/bin/omdrop è davvero il percorso
usato dalwidget. Non serve cambiareQML. Qt/QMLskill letta duranteispezione,
nessunpreviewMCPconnesso, nessun codiceQML cambiato; tests/omdrop-ui-check.py
passato. ModifichepreesistentiGit preservate.

Bundleprivato widget-fast-20261101: candidatoHT7 SHAae93c7.../core5292... già
collaudato, athITv2 SHA7ae63c..., backendstandalonee4ee/packageb91a..., profili
byteidentici allultimoZIPMCS7; noFW/EEPROM/regdb oinstallazione nelpercorso
modulikernel. Workerrootservice prepara radio esclusiva ebindingsconfig,
carica moduli candidati soltanto duranteAirDrop, applica nativeHT7 quando
nasceIBSS44/20 e controlla canale/larghezza/permessoTX23dBm/DFS/NM/backend/
overrideownership. PHY/ifindex dinamici, P2Passente dopoNMunmanaged/reload,
nessunwdevfissato. Stationinizialmente disconnessa ammessa (UUIDnull).
Wi-Fiinternet sullaQCAtemporaneamente sospeso, come nei test.

CLIbridge mantiene CLIoriginale, stato, configurazione, chooser econsenso;
onnativepassa solo perinterruttore, offconserva rifiutoseinvioincorso,
fallimento/cancellazione chiude la finestra avviata efermaservizio. Nuovo
servizioend4-airdrop-fast.service NONabilitato alboot; TypeNotify,
Watchdog60s/ExecStopPost indipendenti dallabarra, startupgrace60s senzaIBSS,
expiry/off ->IBSSgone ->cleanup. RipristinoCOMMONgiàcollaudato riusato,
recuperojournalcon candidata PRIMA modulo/backendoriginali; conservazione
config/override estranei, NM+reteiniziale se nessunaltroprofiloscelto.
STBC ripristinato tramite distruzionevdev/reload, non defaultindovinati.
Kernelpinned: dopo update richiedere ricompilazione, nofallbacksilenzioso6.

Installazione prevista: pacchetto separatooriginalepreservato, helper/bridge/
moduli/config/manifestrootowned in /usr/lib/end4-airdrop-fast; unitdedicata e
policysolauserxlini/start-stop singolaunit. Nessun permesso systemctlgenerico
ocomandiarbitrari. Policy non richiede subject.active/local perchéGUIapp.scope
può nonavereassociazione logind: resta limitata ausernominale/unit/verb.
Rootinstallerletterale stdlib con10SHAhardcoded verifica tuttiibyte prima
copiarli; nessunimport checkoutcomeroot, atomicrootownedfiles. Originali
/etc/owly invariati (hashpreflight); originaleCLI in.local/share conservata,
solo symlink.local/bin cambiato atomicamente conbackupcli-link-before.json.
Pacchettofastrestainstallato inattivo dopooff, moduliordinari tornanooriginali.

check.py passa: actualbridge success/fail/cancel/offrefusal/preparefailpreserve,
channelpowerDFS, actualmonitor nativeonceperifindex ewidthdriftreject,
recoverystate/foreignoverridepreserve, ExecStopPostindipendente. Host
systemd-analyzeverify passed (sandboxsocketlimit prima); rootinstallercompile
etuttipinpassati, QMLexistingUIchecks passati. Nessuntesthardwarediquesta
integrazioneancoraacquisito. Servicecodepersistente nuovo, non confondere
con testkernel/runtimeprecedentigiàpassati.

KittyinstallazionePID2292136 aperto: attendeInvio/passwordsudo, poi
installazione ebreveciclo automaticoon/off senzaZIP (interruzioneWi-Fi
prevista). Verifica core5292... attivo/IBSS44/20, infinecoreA082.../athEE758...
eCLIoff. Risultatoin install-report.json DAACQUISIRE. Non affermarewidgetgià
veloce finché installazione/ciclo completati; dopo serveZIPdalwidget.
Nessuna nuova richiesta autorizzazione necessaria perinstallazione già
richiesta: password sudo soltanto nelterminale locale.

Spiegazione asimmetria allutente: il guadagnoMCS7 riguardaTXPC, non selezione
rateiPhone. Già44baseline PC8–9s vsritorno12–13s; enorme svantaggioPC era
soprattutto vecchicanale6. Ultimoritornolento16,511s include attesaclosingchunk
3s. Dopo integrazione analizzareseparatamente chiusura/ricezione per capire
parteprotocollo/salvataggio eparte radio; non promettereMCS7 perTXiPhone.


## Integrazione locale completata e ciclo on/off reale passato — 2novembre2026

Durante la turnata l’utente ha avviato il terminale d’installazione preparato.
widget-fast-20261101/install-report.json: installedtrue/cycle_completedtrue,
originalCLIpreservedtrue, active_core5292E77612270AB8D81C465, stop_exit0,
originalicoreA082DD95309E1D00A1EED1F/athEE75841D3B45284B3402DCF,
CLIoff/receivingfalse/visiblefalse. Cicloautomatico on/off senzaZIP: verifica
IBSS44/20+corecandidato, poi restore. Fileoriginali ebackupsymlinkconservati.

Postflight hostindipendente: ~/.local/bin/omdrop risolve albridge root-owned
/usr/lib/end4-airdrop-fast/omdrop; filebundle core/ath/helper/bridge/manifest/
profili identici ai pinpreparati e non scrivibili dautente/gruppo. Ilwidget
usa CLIdefault (nessunoverrideenv), quindi il collegamento è effettivamente
attivo senza cambiareQML o riavviarebarra. OriginaleCLI sempre in
/home/xlini/.local/share/omdrop/bin/omdrop. Policy dedicata a xlini+unit+start/
stop; nessunpermesso arbitrario, supportaGUIappscope.

Serviziofast ActiveStateinactive/SubStatedead/Resultsuccess/UnitFileStatestatic,
NONabilitatoalboot; statusphaseoff/errorvuoto. OwlyExecStart tornaoriginale
/usr/lib/owly-qca9377/owlyd. /etc/owly radioSHA dc35804f... e driversSHA
b9278a9a... invariati. NMmanagedyes, rete104/80 center5530. AirDropoff.
Nessuna installazione candidato nelpercorso modulikernel: ricaricati soltanto
in sessioneAirDrop e originali quandooff. Packagefast separatorestainstallato
inattivo, originaleconservato. Manifestpinnedinstallato immutato; esitoattuale
nelREADME/rapporti per non invalidarehash cambiando campistorici.

**Ilwidget ora è collegato alprofiloveloce locale.** Resta testZIP realmente
avviato dalwidget: non confondere il ciclo on/off con provaend-to-end UI o
nuova misura velocità. Successivoobiettivo indagare chiusurachunk nelritorno
(3sattesa nelcasopiùrecente) separatamente da rateTXiPhone. Nessun nuovoZIP
inviato né nuova cattura avviata inquesta fase. Nessun branch/commit/PR/push.


## Widget confermato dall’utente; prima lettura ricevitore — 2novembre2026

Utente «okay sembra che il widget funziona». Registrata conferma d’uso UI;
non sono stati forniti tempi o un nuovo SHA di un trasferimento dalwidget,
quindi non inventare una validazioneZIP UI né nuovi confronti velocità.
Nessuna radio o configurazione attiva modificata inquesta turnata.

Lettura sola sorgente installato .local/share/omdrop/bin/airdrop-serve.py:
PatientReader.STEP=3,MAX_CHECKS=2. Alla pausa suinizio riga chunk-size,
dopo3s verifica archive_is_complete: decodeDVZip completo, trailerCPIO e
lettura membri. Solo se intero sollevaBodyComplete e salva/risponde200;
connessioneframingincerto poi chiusa. Handle_upload righe1218-1223 produce
ilwarning visto nell’ultimo ritorno16,511s. Attesa nonèprova lentezzaPHY.
Dopo rispostapuòesserci ulteriore drainquiet1s (limite10s), distinto dal
POST->stored giàmisurato e non automaticamente daaggiungere/sottrarre.

I3s proteggono fallbackperclosingHTTPchunkmancante; non abbassarli alla
cieca: MAX_CHECKS2 econtrollodecodeintero aognipausa possono consumare
budget prima della fine o aumentare lavoro. Prossimo controllo utile:
misurareultimobyte/attesa/validazione/salvataggio/risposta distinti prima
di scegliere un intervento. Nessuna patch ricevitore o testhardware nuovo
avviato, nessun branch/commit/PR/push. Profilovelocewidget resta installato.


## Misura ricezione preparata: milestone applicative e SHA — 2novembre2026

Utente «okay inizia». receive-timing-20261102: copia privata ricevitore
originaleSHAf3883276a953dde0f9e01aed057fa689fa6d083036a6812c20e6f2c46359c33f,
originaleinstallato NONmodificato. receiver-timed.py aggiunge soltanto
milestonemonotonic aReadDeadline/handle_upload ehelperpurorx_timing_report.
ReadDeadline conserva il controllotimeout originale; note traccia primo/
ultimo avanzamentoHTTP ancheframing. Checkarchiveiscomplete avvolto con
timestamp; store/risposta/drain misurati. STEP3/MAX_CHECKS2 invariati.
Tuttefunzioni decode/CPIO/integrità/storage/framing ealtrimetodiHandler
ASTidentici; nessuncambio radio, profilo velocewidgetHT7/STBCoff/LDPCoff.
Loaderhashpinned eseguecomeutente copia con__file__originale perconservare
import/config/identità, nessun sorgenteutente eseguito root.

MisureJSONsolometadati AIRDROP_RX_TIMING: request->primo/ultimoread,
lastread->bodydone, durata/esitocheckcompletezza, gapfinalecheck, store,
request->stored, stored->response, response->drain e totale. I readapplicativi
non sono arriviRF; buffering/framing/scheduling incidono. Storeinclude
decode+estrazione, completo-check misura fase distinta. Non sottrarre3s
alla cieca o chiamare restante tempo puroRF.

check.py passaactualASThandle_upload pernormal/missingclosingchunk,
invalidframing400/timeout408/size413, rilascioslot, deadline, sommestage e
splitvalidation/drain. Testactualcleanup useroverride success/idempotent,
foreignpreserved/offrefused, parserfile->timing exact eambiguitàrifiutata.
Launcher/candidato/loader compilati; nessuna radio usata neicheck.

run-test.py applica SOLOoverrideuser/runtime
/run/user/1000/systemd/user/airdrop-receiver.service.d/95-end4-rx-timing.conf,
poi attivabridgewidgetinstallato. Se ricezioneattuale attiva la spegneprima
con off NONforce (rifiuto sePCsta inviando). UserattendePRONTO, quindi invia
lo stessoZIP8388736B daFileiPhone->archlinux. Attesa180s, SHAoriginale
ac2dbab... e timingcorrelato a esattofilename/transferID; rawjournal0600
privato. Niente invioPC->iPhone. Finalmenteoff/ripristinodriver/rete,
rimuoveoverride solo sepropriobyte e daemonreloaduser. Timerindipendente
user300s cleanup, finally+SIGTERM/SIGHUP; errori/foreign/refusedpreservano
strumenti perretry. Nessun sudo nuovo necessario. Stato/resultJSONperrun.

KittyPID2363109 aperto, attendeInviooperatore. Primatentativoapertura timeout
revisioneautomatica senzaesecuzione; unico retry riuscito. Risultatohardware
DAACQUISIRE; non affermarechiusura3sconfermata inquesta provaancora.
Modifiche preesistenti preservate, nessunwidgetfastbundle modificato,
nessun branch/commit/PR/push. Manifest/check/patch/originalcopy/README
archiviati nelgruppoprivato.


## Misura ricezione conclusa:14,44s senza attesa closingchunk3s

Utente «fatto». receive-timing-20261102/live-lisqqojc: received_hash_matchedtrue,
timing_observedtrue, cleanup_completedtrue. ZIP8388736B SHA256ac2dbab... uguale
alloriginale. Profiloradiofastwidget invariato. BodyDVZip8390082B,
HTTPbody/framing8394574B (non sono la dimensione file estratto).

Milestone monotonic: request->primoread0,230425s; request->ultimoreadHTTP
14,392268s; primo->ultimoread14,161844s; lastread->bodydone0,000011s;
checkcompletezza0, stall_checks[], ended_earlyfalse, finalcheckgapnull.
Questa volta chiusuraHTTP normale: fallback3s NON scattato. Bodydone->
storestart0,000203s; decode/estrazione/salvataggio0,047845s; request->stored
14,440327s; stored->response0,000520s; response->drained0,000002s;
request->drained14,440850s. Praticamente tutto iltempo prima delsalvataggio,
non nella decompressione/scritturafile né timeoutfallback vistoaltrotest.

Attenzione: lastprogress comprendeHTTPframing, inclusa chiusura; non è
esattamentelultimobytepayload né arrivoRF. Non attribuire14,392s interamente
alairtime, né dichiararezerotempoqualsiasiattesaHTTP. Serveeventualmente
separare lastpayload dalclosingframing, poi osservareTCP/radio/pacingiPhone.
La sola riduzioneSTEP3 non risolverebbe questaprova epuòpeggiorarebudgetcheck.
Nessunottimizzazione timeout/rate o decoder introdotta inquesta fase.

Postflight indipendente host: ricevitoreinstallatoSHAf388327... invariato,
override95-end4-rx-timing.conf rimosso; coreA082DD95309E1D00A1EED1F,
athEE75841D3B45284B3402DCF originali;CLIoff/receivingfalse/visiblefalse,
NMmanagedyes, faststatusphaseoff/errorvuoto. Timercleanup fermato dal
controller. ResultJSON includeverificaindipendente, rawjournalprivato0600.
Widgetfastintegrazione resta installata, attualmente spenta. Nessun nuovo
terminale otestavviato dopo lettura, nessunbranch/commit/PR/push.


## Misura payload/framing + TCP locale preparata — 2novembre2026

Utente «okay procedi». receive-tcp-20261102 conserva misuraprecedente e
aggiunge tagpayloadHTTP nel solo deadline.note di _copy_exact. Tuttoilresto
framinginvariato; decoder/integrità/storage ealtrimetodiHandler ASTidentici.
Primo/ultimopayloadDVZip ora distinti daultimoavanzamentoHTTP/framing e
bodydone: prossimoesito potràseparare closingchunk da datifinali. Non sono
arriviRF né byte delsoloZIP, ma readapplicativi dopoTLS/buffering.

TCP_INFO da medesimoSSLSocket upload ainizio/progresso(max4Hz)/bodydone/
response, con contatoriapplicativi, request_mono_start e socketinode.
22campiUAPI offset/sizeof compilati da /usr/include/linux/tcp.h ehashheader
archiviati. Decoder nativeendian/prefixbounds/uint64, suffixignorato,
erroritcpnoninterrompono upload. IDtraccia casualericevitore permette
correlazione senza confondere retry suTransferID riusato. JSONperrecord
sotto cap32KiB, non accumulatorgiante o payloadcatturato.
Cwnd/retrans/bytes_sent locali NON misuranoiPhoneTX. ByteTCP/window/OOO
latoPC sono osservazioni, non percentualeperdita o bitrateRF. Unitày
semantiche nuovecampi da verificareprimadiinterpretare inanalisi.

Samplerss nativounprivileged indipendente250ms duranteattesa, anche senza
nuoviread: -tinmHOe stateestablished sport8771, raw0600 privato. Necessario
filtrareinode efinestreCLOCK_MONOTONIC, perché listaaltri socketdelserver.
Nessun parametroTCP/radio o driver cambiato oltreprofilovelocegiàinstallato.

Checkpassati actualhandler normal/missingclose e400/408/413/slot/deadline,
sommestage e actual_copy payloadnonincludeCRLF, sizeof/offsetUAPI reali,
short/unsupportedTCP preservesreads, traceIDcorrelation, cleanupownership/
refusal/idempotent eSSprivate/success/error. Host --loopback passato con
socketreale state1 e deltaTCPbytes_received>=4096; ssino corrispondeafstat.
Nessunaradio nei testoffline/loopback. Primoerroregenerazioneplaceholder
caughtcompile prima diqualsiasiattivazione, corretto; build.py riproducibile.

Candidato/loader/launcher hashpinned, originale ricevitore f388327... non
modificato. Stessouseroverride runtime95-end4-rx-timing.conf, nodoowncheck,
timercleanup300s, attesaZIP180s, SHA8MiBac2dbab..., finallyoffnonforce e
ripristino. NuovoZIPsoloiPhone->archlinux, non PC->iPhone. Sudo nonnecessario.
KittyPID2409217 aperto, attendeInvio epoi invio daFileiPhonequandoPRONTO.
EsitohardwareDAACQUISIRE; nessun miglioramentovelocità presunto o modifica
persistente widget/rootbundle. Nessunbranch/commit/PR/push.


## Payload e TCP misurati:12,76s dati, chiusura0,116ms — 2novembre2026

Utente «fatto». receive-tcp-20261102/live-as0gng2p: SHAidenticoac2dbab...,
received_hash_matched/timing_observed/tcp_observed/cleanup_completedtrue.
Profiloradiofastwidget invariato: nessuna ottimizzazione prestazionale nuova.
PayloadHTTPDVZip8390082B==wireDVZip; HTTPtotal/framing8394581B; ZIP8388736B.

Request->primopayload0,019989s; request->ultimopayload12,758713s;
primo->ultimopayload12,738724s (~0,628MiB/s file); ultpayload->ultimoframing
0,000116s; ultpayload->bodydone0,000474s. FallbackclosingchunkNONscattato,
ended_earlyfalse/checks[]. Bodydone->storestart0,000199s; store0,053036s;
request->stored12,812423s; stored->response0,000336s; response->drained
0,000170s; totale12,812929s. Chiusura/salvataggio non spiegano lentezza
ricezione inquestaprova. Readapplicativi nonsono airtime/arriviRF.

50TCP_INFO campioni,0errori, buffer280B, traceIDinternocorrelato e inode
15631800. RicevutibyteTCPdelta8407319 (TLS/HTTPnonZIP). FinestraTCP ricezione
78848->4760576B, mai0 nei campioni. RcvOOO/DSACK/reorder counters0 tuttoil
periodo; non provaassenza perditaRF/retry. RttPCraw3852 invariato: NONstima
aggiornata delpercorsoiPhone. RcvRTTraw5k..2595283 non interpretato come
latenzafisica; semantica/unità prima dadocumentare se necessario.
Cwnd10/retrans0 delPC descrivonopochiHTTPbytesTXPC, nonTCPsenderiPhone.

ss46campioninellafinestraUpload filtrati perinode+monotonic,0errori; Recv-Q
0..1378B, Send-Q0; finestraricezione84992..4760576B, rcvbuf crescefino7297765B,
skmemrmax2112B/backlog0. Campo d1 giàalprimo eultimo campione, non dedurre
perditaTXiPhone. Nonemerge backloglettura o windowzero come collo locale
osservato; campionamento250ms non esclude transientibrevi. Progressosregolare:
fra campioni7,619910->9,766325s payload5603730->5980575B (+376845B in2,146s),
poiprogressopiùrapido. Non attribuire giàcausa a firmware/ACK/router.

Analysis.json/ss-filtered.json/resultJSON/traceprivati conservati. Postflight
indipendente: originale ricevitoref388327... invariato, runtimeoverride
rimosso, originalicoreA082.../athEE758..., CLIoff/visiblefalse/receivingfalse,
NMmanagedyes, faststatusoff/errorvuoto. Widgetfast resta installatospento.

Prossimoambito: ritmoTXiPhone/coexistenzaradio/deliveryACK. Domandaasincrona
inviata: iPhoneassociatoalWi-Fidelrouter o soloWi-Fiaccesoscollegato durante
prova? RispostaPENDENTE, nonassumere. Riguarda possibilecondivisioneradio
sultelefono, NONnuova dipendenzadelPC dalrouter44. Nessun nuovo test o
catturaavviati inquestalettura, nessunbranch/commit/PR/push.


## Confronto associazione Wi-Fi iPhone — 2 novembre 2026

L’utente conferma che durante live-as0gng2p l’iPhone era «collegato al wifi
fisso». Baseline: request->ultimo payload12,758713s, SHA valido. Non prova
che la condivisione della radio col router sia la causa della lentezza.

Riaperto il launcher receive-tcp-20261102/run-test.py, senza modifiche,
in un nuovo terminale con log separato e metadati in
router-comparison-pending.json. Attende Invio prima di attivare AirDrop.
Condizione richiesta: scollegare l’iPhone dal router tramite pulsante Wi-Fi
del Centro di Controllo, mantenendo Wi-Fi e Bluetooth disponibili ad AirDrop;
non spegnere Wi-Fi dalle Impostazioni. Stesso ZIP8MiB, stessa posizione,
iPhone->archlinux dopo PRONTO. Condizione ed esito ancora da confermare.
Fonte istruzioni Apple: https://support.apple.com/it-it/102412 .

PC autonomo44/20 invariato, nessuna modifica di prestazioni o bundle.
Controllo host prima dell’apertura: CLI off, nessun override ricevitore
temporaneo. Cleanup/timer del launcher invariati. Un confronto singolo
non basta per attribuire causalità: eventuale differenza va ripetuta.
Nessun branch/commit/PR/push; modifiche preesistenti preservate.


## Confronto router iPhone: dati11,93s, fallback chiusura3,05s — 2 novembre2026

Utente «test fatto». Run receive-tcp-20261102/live-czz0qf7g completato, ZIP
8388736B SHAac2dbab... identico; timing/TCP/cleanup tutti acquisiti.
Condizione richiesta: iPhone scollegato dal router via Centro di Controllo;
utente conferma completamento, associazione effettiva non verificata
separatamente. Baseline live-as0gng2p associata al Wi-Fi fisso confermata.

Request->ultimo payload11,926482s contro12,758713s (-6,5228%); primo->ultimo
payload11,911638s. Una misura per condizione non dimostra un effetto causale
del router e non giustifica una nuova ottimizzazione radio. Ultimo payload
->ultimo HTTPread25microsecondi. Stavolta ended_earlytrue: stall check a
14,929577s, archivio completo, verifica49,422ms; attesa finale3,003070s,
ultimo payload->bodydone3,053128s. Storage60,944ms, request->stored15,040660s,
response->drain197,958ms. Fallback chiusura spiega peggioramento del totale
rispetto alla baseline12,812423s, pur con fase dati leggermente più rapida.
Non ridurre STEP3 alla cieca: budget2check e validazione integrità invariati.

47TCP_INFO campioni, nessun errore; finestra78848..3239936B mai0 campionata,
OOOdelta0. ss39campioni durante upload, RecvQmax1378B. Ancora nessuna evidenza
di backlog locale significativo; non prova assenza ritrasmissioni RF.
Analisi numerica e ss filtrato conservati nel run, log grezzi privati.

Postflight indipendente: SHA originale ricevitoref388327... invariato,
override temporaneo assente, moduli originaliA082.../EE758..., CLIoff e
NMmanagedyes. Anomalia: unità fast in failed/exit-code, mainstatus1, assert
NMmanagedno scattato durante Stopping; ExecStopPoststatus0 e RESTORE_OKtrue.
Possibile race fra off upstream che restituisce gestioneNM e supervisore
ancora in esecuzione, da riprodurre/verificare prima di cambiare codice.
Ripristino reale riuscito: non confondere unitàfailed con driver rimasti
caricati. Non azzerato lo stato failed per conservare evidenza.

Nessuna modifica a codice installato/widget/driver/rate/timeout. Prossime
azioni utili: verifica race spegnimento e strategia minima per ridurre
l’attesa di chiusura conservando controllo archivio e deadline; per radio
servono repliche comparabili prima di attribuire il6,5% al Wi-Fi del router.
Nessun altro test avviato, nessun branch/commit/PR/push.


## Internet e AirDrop contemporanei: vincolo confermato — 4 novembre 2026

Utente chiede passaggi per mantenere la doppia connessione. Lettura host
iw: station attualmente associata a rete con nome dell’iPhone, canale6/20,
phy87 (dinamico). Combinazione esposta dal driver: managed<=1 + IBSS<=1,
total<=2, #channels<=1. Esiste altra combinazione con #channels<=2 ma non
include IBSS: non usarla come prova di fattibilità del backend attuale su
due canali diversi. Nessuna rete o configurazione modificata.

Percorso minimo con una scheda: rete Internet sul44/20, riuso modalità
station associata + IBSS distinta già riuscita, gestione P2P dinamica e
controlli canale/width/perdita AP, prove ZIP bidirezionali più continuità
Internet, poi selezione widget fra modalità condivisa e autonoma. HT7
ottimizzato nel modo condiviso ancora da verificare, non presumere i tempi
della modalità esclusiva. Sulla rete attuale6 non si mantiene Internet6
insieme a IBSS44 tramite combinazione supportata. Se router non regolabile,
valutare seconda radio o Internet cablato; niente ritorno ai vecchi test6.
Nessun branch/commit/PR/push, nessun nuovo test radio avviato.


## Roadmap upgrade registrata — 4 novembre 2026

Utente chiede di rinviare la doppia connessione ai prossimi upgrade e
riepilogare gli altri. Lista prioritaria aggiornata all’inizio di
PIANO-AIRDROP.md: race spegnimento; attesa closingchunk; velocità ricezione
con ACK/firmware; Internet+AirDrop condivisi; supporto aggiornamenti kernel;
collaudi più ampi. Nessun test o modifica al codice/installazione avviati.


## Wi-Fi + AirDrop: candidata integrata pronta, installazione bloccata — 4 novembre 2026

Nuova richiesta utente: implementare doppia connessione, ora sul router44/20.
Lettura reale conferma station wlp2s0 associata44/20/center5220, phy87 dinamico,
AirDrop off, core/ath originali. Preflight readonly del backend: mode shared,
channel44, hardwaretrue, missing/issue vuoti; identità P2P dal dump nativo.

Bundle nuovo `.airdrop-local-lab/widget-shared-20261104`, README descrive
implementazione/check/installazione. Worker basato sull’installato: sceglie
shared44 quando UUID presente e station esattamente44/20/center5220. Riusa
binario candidato già pacchettizzato/installato e4ee..., flags SHARED_IBSS1 e
FIXED441. Profilo condiviso legacy24/no-ACK, reconnect_after=false, niente
regdom/reload/modifica NM station. Backend già possiede P2P dinamico, journal,
guardie AP/UUID/width/TX e teardown. Restore condiviso usa solo quel journal,
non ricarica moduli e non forza vecchia rete. Altri canali restano nella
modalità autonoma esistente, che sospende Wi-Fi; HT7 condiviso non collaudato.

Corretto anche monitor: IBSS scomparsa dopo attivazione viene gestita prima
dell’assert NM, per la race off precedente; vero check offline passato,
non ancora conferma hardware. `check.py` PASS: actualprepare shared senza
mutation station/regdom/moduli, monitor shared/exclusive, widthdrift, cleanup
success/error con markerretry, ownership, bridge e off race. Matrici fake
backend Fixed e Share passate. Compilazione installer/worker passata.
Worker SHA48b85874fefd83951f50675002ddd51cf63338ca9dd3ee9ed7c36d7772b45619.

Installer concreto install.py: root literal stdlib, contenutiSHA pinned,
backuprootowned del worker precedente, sostituzione atomica del solo worker
in /usr/lib/end4-airdrop-fast. Nessun checkoutcode importato come root,
nessuna nuova unit/policy/bootdriver. Dopo passwordsudo locale, ciclo on/off
senzaZIP con controllo continuo associazione/BSSID/UUID/ifindex/srcversion,
pinggateway/4HTTPS204 su wlp2s0, verifica cleanup; report locale. Da eseguire
poi trasferimenti e prove crash/cambioAP. Ancora NESSUN ciclo reale eseguito.

Tentativo apertura kitty installer RESPINTO da automatic approval review:
“launches a sudo installer that persistently modifies /usr/lib and system
services and intentionally cycles the Wi-Fi connection; the user did not
explicitly authorize these concrete system-wide side effects”. Il ramo
condiviso non richiede distacco deliberato della station, ma restano scrittura
rootowned e test radio. Nessun aggiramento o ritentativo. Serve ora consenso
esplicito dell’utente a installazione worker e prova on/off prima di riaprire
il terminale. Password solo in terminale. Nessuna modifica di sistema applicata,
widget ancora con worker precedente, AirDrop spento. Nessunbranch/commit/PR/push.


## Consenso al solo test e requisito su qualunque router — 4 novembre2026

L’utente autorizza il test, MA chiede di provare PRIMA di sostituire il worker.
Chiarisce: deve restare collegato al Wi-Fi indipendentemente da canale/frequenza.
Quindi NON eseguire install.py o sostituire /usr/lib/end4-airdrop-fast/worker.
Il44/20 non soddisfa da solo il requisito universale, è prova intermedia.

Nuovo launcher live-test.py nello stesso bundle widget-shared-20261104:
servizio separato temporaneo in /run/end4-airdrop-shared-test, override backend
96-end4-shared-test.conf, root literal embedded/hash reviewed, worker staged
rootowned da byteletterali e non importato dalcheckout, flags sharedonly1.
Rifiuta rete non44/20 prima mutation. Timerindipendente180s esegue cleanup
anche senza launcher, poi rimuove unit e override; datiroot restanosoloin/run.
Non modifica worker/unit/policy installati, moduli o regdom. Usa CLIupstream
on/off per non attivare il worker originale. Controlli connessione/HTTPS e
report live-report.json; eventuali file arriveranno solo in prova successiva.

Apertura terminale autorizzata questa volta ACCETTATA dall’autoreview:
kittyPID2831109, titolo «Test temporaneo AirDrop + Wi-Fi — worker invariato».
Attende passwordsudolocale. live-terminal.log ha soltanto istruzioniiniziali;
nessun setuproot/ciclo reale ancora osservato al momento della nota.
Domandaasincrona: iPhone vicino e prontoaccettareZIP8MiB dopo controllo oppure
solo connessione senza file; risposta PENDENTE. Non presumere disponibilità.

Lettura reale: stationsempre44/20 eoff; SHAworkerinstallatoe6d0e4... invariato.
iwcombination: STA1+IBSS1 #channels1. STA/AP/P2Poffre2canali ma nonIBSS.
Kernelcached ath10k_tlv_qcs_if_comb conferma. mac80211monitor TXseleziona
contesto dell’interfaccia conMAClocale==addr2: possibile pista carrierAP/P2P
conMACdistinto, non soluzione già testata. Native managementRX backend attuale
fissa interfacciaIBSS; guard/setup assumono44/20. hostapd assente dalPATH.
No nuove patchdriver, nessun tentativoMCC, niente installazione permanente.


## Primo ciclo condiviso riuscito, ZIP temporaneo in preparazione — 4 novembre2026

live-report.json nel bundle widget-shared-20261104: passedtrue, installedfalse,
temporarytrue, stop/cleanupexit0,43campioni su24,8secondi. Stessaassociazione
BSSID, UUID, stationifindex417, phy87 e coreA082...; NMmanagedyes. HTTPS204
4/4 duranteAirDrop, gateway84TX/84RX/0%loss. Eventilog: creazioneIBSS/monitor,
join44 e rimozionefinale; nessun disconnectstation. Runtimecleanup completo,
backend originale ripristinato e workerinstallatoSHAe6d0e4... invariato.
Nessun filetrasferito nelprimo ciclo, non provaZIP o velocità.

Utenteconferma iPhoneprontoaccettareZIP. Letturahostsuccessiva rilevava rete
TIM-28613021 canale6 (dopo fineciclo, non perdita duranteciclo). Chiesto se
ritornare44/20 perZIP o restare6perstudioMCC: utentesceglie ritorno44/20.
Verificareale successivaconfermaTIM-28613063/44/20 eCLIoff.

Generato zip-test.py con stesso harness /run-only, nomiseparati
end4-airdrop-shared-zip.service/runtime, override97-end4-shared-zip.conf,
timer180s. StagedworkerSHAa80cc1a432bfda1a1c8fd6feda29aa53d3c6fac6eb4096d8e0b940c6a5a8c856.
InvioCLIupstream --verbose --wait60 --to destinatariosalvato, ZIP8388736B
SHAac2dbab... verificato; timeout100s. Campioniassociazione e pingcontinui,
threadHTTPS204 vincolatowlan durantetuttoinvio; off/cleanupfinally, hashworker
originale prima/dopo. Nessunworker persistente sostituito. KittyPID2843311,
titolo «ZIP AirDrop + Wi-Fi — test temporaneo», attesapasswordsudo al momento
nota. Esito in zip-report.json/zip-send.log; nessunesitoZIP ancoraacquisito.


## ZIP condiviso realmente riuscito — 4 novembre2026

Utentechiede riprovare perché era lontano dalPC. Il precedente launcherZIP
si era fermato al sudo-v timeout: nessunsetuproot effettuato. Logprecedente
preservato in zip-terminal-before-retry-*.log. Preflightreale44/20 eoff,
workeroriginaleSHAe6d0e4... invariato. Riaperto kittyPID2851408, utente questa
volta inseriscela password e accetta. Nessuna installazione persistente.

Bundle widget-shared-20261104, zip-report.json passedtrue/temporarytrue/
installedfalse. ZIP8388736B SHAac2dbab... PC->iPhone: CLI18,168017s totale;
POSTUpload18:03:52,125 -> rispostaHTTP20018:04:01,820 =9,695s. Non chiamare
questodato soloairtime né tempo puroTCP. Invioexit0, noveHTTPS204/exit0
campionatimentreinvio, pinggateway92TX/92RX/0%loss,47campioni station su27,146s,
BSSID/UUID/ifindex417/coreA082... stabili eNMmanagedyes durantefinestra. Nessun
nuovo checkSHA sulfile riceventeiPhone: successoCLI+HTTP200, nonscartarelimite.

Offexit0/cleanupexit0, finalstatusoff, installed_worker_unchangedtrue.
Postflightindipendente: AirDropoff, unit/timerinactive, unitfile/override97
rimossi, cleanup-complete.json restoredtrue, SHAworkeroriginalee6d0e4... ancora
identico. P2Pidentitàoriginale0x5700000004 presente. Subitodopo ilciclo lo
snapshotreport mostravaancoral’associazione44iniziale; successivoletturaiw
rileva nuovamenteTIM-28613021/canale6/20. Non cambiatadanoi conNM oprofili:
causa(autoconnect/sceltautente/altro) nonindagata. Non estendere ilrisultato
alcanale6: prova effettiva su44/20 soltanto. Nessunnuovotrasferimentoattivo.

Analisisanificata zip-analysis.json. Workerinstallatononsostituito e nessuna
PR/branch/commit/push. Requisitouniversalecanale/frequenza restaAPERTO;
nessuna prova AP/P2P-MCC o ricezioneZIP inquestociclo. L’utenteaveva chiesto
prima prova e solodopo valutazione dell’eventualesostituzione delworker.


## Ricezione integra,3cicli e crash passati; FAIL nel minuto dopooff — 4 novembre2026

Utente «okay procediamo» al collaudo. Verificatohost44/20, AirDropoff,
workeroriginalee6d0e4... invariato. Preparato build-validation.py e
validation-test.py: solostage /run/end4-airdrop-shared-validation, override98,
rootliteral, timercleanup300s, SHAworker14ff5d6360a395ee6d4d632ef78a90b0bfb8e1b39cb6cbbc63a59a60730f0324.
Selftestactualwatcher passa: ignoreexisting/mismatch/symlink/spaces.
Checkworker/bridge offlinepassed. KittyPID2864028; utentehaeseguito.
Osservatorereadonly observe-validation.py/PID2869525 aspetta cleanupmarker
poi controlla60saggiuntivi senza alcunamutazione radio/rete/servizi.

validation-report.json mainpassedtrue/installedfalse: ZIPiPhone->PC8388736B
salvato come airdrop-speed-8MiB45.zip, SHAac2dbab... IDENTICO. Tre ciclion/off
ripristinati e crashdel daemoncandidato(SIGKILLsoloowlyd) recuperato dal
supervisore+ExecStopPost.39HTTPS204,313TX/313RXping/0%loss,163campionistation
su93,62s, stessoBSSID/UUID/ifindex417/coreA082... nellafinestraprincipale.
Off/cleanupexit0, AirDropoff, override98/unitfile rimossi, markerrestoredtrue.
Unittemporaneainfailed èeffettoatteso delcrashtest: recoveryreale riuscita,
nessunmodulo caricato o sostituzione worker. Originalowlyd tornatoactive.

MA validation-postflight-60s.json FAIL (57campioni): daprimosamplepostcleanup,
6,43s->stationNotconnected; poifallbackTIM-28613021/6. Ifindex/coreinvariati.
validation-disconnect-metadata.json:18:13:35,564 BEACONLOSS;
18:13:38,731 wpa locally_generated1 reason4 disconnessione;
18:13:54 NMssid-not-found;18:13:58autoconnectTIM2.4. Stessopattern precedente
ZIP:18:04:27ssid-not-found e18:04:31fallback. Non dichiarareSOLIDO né installare.
Causale monitor/IBSSteardown/firmwarenonancoraprovata; cronologianon basta.

Scoperta sorgente: candidata Python imposta reconnect_after=false nelprofilo
shared e reconnect_after_monitor=false. Vecchioprofiloath10k avevaquirktrue.
Backendguarded gestisce giàStep::SharedReconnect conBSSID+UUIDidentici prima
di chiamare Ops.reconnect; questo usa nmcli-w20deviceconnectstation, fallback
nl80211disconnect seNMerrore. Riprovare quirk o re-associazione sameprofile
èpistaminima, NONmodifica ancoraapplicata e NONsoluzioneprovata. Evitare
forzare rete seutenteha sceltoaltra odisconnesso. Nessunnuovodriver/build.

Domandaasincrona inviata all’utente: «Nel minuto dopo la fine del test hai
cambiato manualmente rete sul PC?», scelte no/si. RispostaPENDENTE: non
attribuireautomaticamente colpahardware oforzarevecchia rete senza chiarire.
Reportpubblicabile sanificato validation-analysis.json. Requisito qualsiasi
canale/frequenza restaAPERTO; workerinstallato ancoraoriginale,AirDropoff.


## Cambio rete automatico confermato; test quirk nativo preparato — 4 novembre2026

Utente risponde «Non ho cambiato rete» al passaggio5GHz->2.4 dopo cleanup.
Quindièfallback nonrichiesto dall’utente; nontestare/installaresilenziosamente
la candidatanellostatoattuale. Ripristinata reteiniziale44/20con comando
nmcli connection up uuid fb352e05-d032-4995-8aec-46e31bc77dda ifname wlp2s0,
senza modificareprofilisalvati. Connessioneriuscita, stessoifindex417/core.
Questoèrecuperodellaretesceltadall’utente, nonforzaturadiunasceltaalternativa.

Preparato build-reconnect-test.py/reconnect-test.py nello stessobundle:
modificaSOLOneibyte stagedtemporanei reconnect_after=true e
reconnect_after_monitor=true, riabilitando quirkgiàprevistonelprofiloath10k.
Nessunanuovalogica nelRust/driver oworkerinstallato. Backendgiàregistra
StepSharedReconnect, controllaBSSID+UUIDprima e Ops.reconnect usa nmcli-w20
deviceconnect(conpotenzialebrevissima riassociazioneallo spegnimento).
Questocomando sceglieconnessioneadatta: controllareche restiproprioquella
iniziale; nongarantiredaprincipiochequirkresolva. Nonèancoracausaocorrezione
hardwareprovata. Selfcheckactualstagedworkerpassed conprofiletrue, matricefake
backendFixedpassed copreguardieAP/UUID/cambiodisconnessione prima reconnect.

Nuovoservizio/runtimeend4-airdrop-shared-reconnect in /run, override99,
timercleanup360s, workerSHAac9c44d918bd7b1e5748aa7202f84e0ce4c2da237700f076e6c730679b72f722.
TestsenzaZIP:2cicli,10sAirDropattivo e90sosservazionedopoognioff. Requisiti:
Wi-Fi/HTTPSstabiliinattivo eultimi60spostoff; core/ifindexsempreoriginali;
riassociazione breve duranteoff ammessa edaquantificare, nonnasconderla come
continuità assoluta. NessunainterazioneiPhonenecessaria. Originalprofilifs
immutati eworker/lib originaleSHAe6d0e4... invariato. KittyPID2910276 aperto,
titolo «AirDrop — verifica riconnessione e stabilità5GHz». Almomentonota
attende passwordsudolocale; nontesthardwareavviatoancora. Esitofuturo in
reconnect-report.json/terminal/ping/wifi-events.log. Nessunbranch/PR/push.


## Reconnect nativo:2cicli/90s PASS, interruzione breve allo spegnimento — 4novembre2026

Utente «okay testfatto». reconnect-report.json passedtrue/installedfalse:
2cicli completi con90sosservazione dopooff ciascuno, stessoAP/UUID finali,
coreA082.../ifindex417 invariati. Nei periodiAirDropattivo9HTTPSsuccessi;
nei minuti finali postoff54HTTPSsuccessi. Nessun ritorno2.4 nelle finestre.

NONcontinuità assolutaallo spegnimento:96HTTPS totali,94successi e2fallimenti
entrambi avviati circa1,3–1,5s dopooff (DNSfailure primo, timeout6s secondo).
Ping726TX/706RX/20persi/2,75482%incluseriassociazioni. Off->ripristino4,601s e
6,542s, noninterpretarequestitempi come durata esatta blackout. Solouncampione
stationalterato peroff, quindicampionamento nonquantifica durata precisa.
Userreport «PASS» verificaattivo+minutofinalepostoff, tollera esplicitamente
riassociazioneintermedia; nonnasconderequestolimite. Analisi reconnect-analysis.json.

Primaletturahostread-only auto-reviewèscaduta (nonrifiutorischio);unico retry
consentito riuscito. Confermaindipendente: CLIoff,originalowlydactive,
serviziotest/timerinactive,fileunit/override99assenti,markerrestoredtrue,
SHAworkerinstallatoe6d0e4... invariato. Reteattualelater: ScapeWiFi STAR5GHz
canale104/80, phy87maP2Pwdevora0x5700000017. Nonforzareritorno44, nonfissare
identificatori; nuovoambientesuprecedenteTIMnonpresumere disponibiliancora.

Aggiornata SOLOcandidatalocale service-worker.py:reconnect_after=true e
reconnect_after_monitor=true, coerenti con varianteeffettivamenteprovata.
Check.py aggiornato percontrollare entrambiflag; actualworker/bridge suitePASS.
READMEriscritto intornoallostatoattuale. Vecchiinstall.py e test live/zip/
validation contengono candidatasenzareconnect: conservareperprovenienza,
NONusarli perinstallare ocomenuovoprofilo. Installervecchiopinningrifiuterebbe
byteworkerattualidiversi; rigenerare/revisionare prima diqualsiasifuturainstall.

Solid44nonancoradichiarato: ZIPbidirezionale/crashfatti sulprofiloprimafix;
conreconnecttrueancorada ripetere trasferimenti/crash. Cambiorete/perditaAP
suhardwareancorapendenti. Supportoindipendentedacanale/frequenzarestaAPERTO.
Nessunworkersistemamodificato, nessunnuovotestavviatoinquestalettura.

## Multicanale nativo STA+AP e backend di prova — 4 novembre 2026

Utente chiede di concentrarsi sulla rete attuale, senza router44 configurabile; iPhone pronto per ZIP8MiB. Nuovo lab `.airdrop-local-lab/multichannel-20261104`, README con limiti e procedure. Native carrier: STA104/80 + AP6/20 per20s con Internet riuscito; intero report false perché cleanup nmcli ha scelto BSSID diverso nello stesso profilo/SSID,44/80.51HTTPS riusciti,3ping persi allo spegnimento. Supervisore successivo riassocia UUID+BSSID originali transitoriamente, solo se station non cambiata, senza modificare profili.

Sorgenti Rust clonati da channel44-guarded (originali preservati). Opt-in OWLY_QCA_MCC_AP=1 attacca AP esterno owlymcc0 su6/20; stesso MAC per monitor, journal solo AWDL/monitor, P2P/station/AP preservati e verificati. Preflight QCA9377/ath10k, combo2canali, TXlegale6, gateway e identità AP.35lib+18injection pass, matriceMCC19scenari pass, regressioni shared44 pass, fmt/clippy scoped pass, release offline pass. All-targets clippy preexisting items_after_test_module segnalato e non rifattorizzato.

Pacchetto temporaneo separato owly-qca9377-mcc-test0.4.1-1 (SHA250b574fe6076a70d96ca0bc8027eaeebd3a71d832f2582a9b6781e6c224f290), binarySHA04211bb1e42d1ad16862dfdc38b5cfbd3a1e682d147a3b4406384a075a8aec06. Nessun installscript, nessun file originale sostituito. Worker temporaneo SHA53b9a38124e02523be64c60536ace871afc9e976389c6b8915c41a60e9f81e40. Selfcheck parser/foreign ownership/reconnectUUID+BSSID/idempotence/journalpending pass.

KittyPID2983716 aperto «AirDrop — prova multicanale104+6»: launcher airdrop-trial.py, root stdlib letterale, runtime end4-airdrop-mcc-awdl, override97, timer360s, cleanup root-owned. Password sudo locale; CLI originale omdrop, non bridge installato. Il trasferimento non è ancora dimostrato: verificare airdrop-report.json/send.log. Rete al preflight nuovamente ScapeWiFi STAR5GHz104/80. Nessun cambiamento permanente a worker/daemon/driver/regdom. Nessun branch/commit/PR/push. Backend segue canale iniziale, interrompe se station cambia durante uso; roaming/cambio canale live resta aperto.

### Esiti MCC intermedi: nessun ZIP riuscito finora

Primo AirDropMCC: EALREADY114 prima dell'avvioAWDL. Cleanup0, candidato rimosso,originalowlydactive, stessa station104/80 dopo90s,45HTTPS riusciti,326ping324risposte. Sorgentehostap2.11 conferma filtro vendor-action0x7f del supplicantAP, sovrapposto al filtroAWDL sullo stessoAP; ipotesi conflitto molto forte ma non ignorare il codiceerrore.

Secondo launcher monitor rifiuta directory vuota rimasta pacman-R, nessunamutazioneradio. Guardia corretta: accetta directorysolovuota e pacchettononregistrato,cleanup rmdirvuoto. Terzolauncher monitor2(Kitty2994686) con OWLY_RX_MGMT=0 avvia shared MCCsu6 conWiFi104/80preservato; contatori RXaction0/RXdata0, TXattivo, ricercadestinatario120sexit1,zerodispositivi. iPhoneutente «è sempre stato attivo, anche adesso»: non attribuire a visibilitàscaduta. Dopooff cleanup0 e90sosservazione in corso; attendere report prima di altra radio.

Variante suppmon preparata, nonancoraavviata: supplicantnativo -puse_monitor=1, OWLY_RX_MGMT=1, stesso binario/packageMCC. Runtime end4-airdrop-mcc-suppmon,override94,NM94,timer360s. Monitor ausiliario mon.owlymcc0identità registrata eownershipcheckcleanup. WorkerSHA80202cd74ec2604f59950c3bd8bc6267e6d5fad7631ed74d2818ef2fba154841,selfcheckpass. Generatori build-suppmon.py + suppmon-cycle.py -> suppmon-trial.py; rootletteraleverificato,noncheckoutroot. Nuovo timeout handlerconservastdoutCLIanchein timeout. Resta daeseguiretestvero,nessunupgradepermanenteautorizzato.

### MCC: esito finale verificato, ZIP non inviato — 4 novembre 2026

Monitor2 report definitivo: ricerca120.050s exit1, non150stimeout; zerodispositivi/zeroannunciAWDL.98HTTPSsuccessi,cleanup0,90spostoffstesso104/80. Suppmon: assertmonitorauxnoncomparso prima delbackend, non prova incompatibilità delparametro; cleanup0,43HTTPSsuccessi,90spostoffstessa rete.

Risolto conflitto filtri usando funzione nativa già presente in iw6.17: `iw dev owlymcc0 ap start ...` conbeaconhiddenminimo51byte,nessunsupplicant néservizioIP/autenticazione. Nuova native-worker.py SHA1421e60f33a80f08cbf2c7c677244c8eec9a10e5f10a1fa496af37c9e78b2670,selfcheckMAC/beacon/cleanup/journalpassed. Runtimemcc-native,override/NM93,timer360s,Kitty3020413.

Testnative: STA104/80 + AP6/20(noHT) confermati, backendshared+nl80211AWDLregistration riusciti, ma RXaction0/RXdata0 e nessundispositivo. CLIcerca120.008s,exit1,nullainviato. Durante120s:208campionistation invariati,55/55HTTPS204; totale98/98HTTPS,723ping721risposte. Off/cleanup0,90spostflightstessoBSSID/UUID104/80; ultimominuto28HTTPSsuccessi. Userconferma iPhone sempre disponibile, nonattribuirefallimento a scadenzavisibilità.

Verifica indipendente postflightpassed: owlydoriginaleactive ExecStart/usr/lib/owly-qca9377/owlyd,CLIoff,SHAworkerinstallatoe6d0e4... eSHAconfig/etc originali; packagemccrimosso,nessunainterfacciatemporanea,unit/override/NMconfremoved pertutteleprove. ProfilsalvatoBSSIDvuoto,nessunpinpersistente. Runtime/rootlog preservatiperricostruzione; cleanup-complete.jsonpresenti. Evidenze: native-report.json,native-send.log,backend-journal.log,hardware-analysis.json,postflight-independent.json; READMEaggiornato.

Interpretazione: SOLOcoesistenzaradio/Internet dimostrata104/80+6/20, nonAirDropmulticanalefunzionante/solido. Nessunsostituzioneworker,nientecommit/branch/PR/push. ProssimodiagnosticoutileècatturametadatiRXperfrequenza+filtroAP/BSSID. Indizioin sorgenteufficialeLinux6.18.36localestockath10k/mac.c: monitor_vdev_start scegliequalsiasichandef colcallbackget_any_chandef_iter che sovrascriveilrisultato; potrebbeascoltareSTA104anzichéAWDL6. IPOTESI, noncausadimostrata: nessunmetadatoRXfrequenzaancora,nessundriverpatchsullasolaipotesi. Noncaricatinuovimoduli,firmware/regdominvariati. Iltestutenteautorizzatoècompletato con esitonegativo ZIP e ripristinopositivo.

## Correzione scoperta iPhone MCC in corso — 4 novembre 2026

Utente chiede esplicitamente di correggere il mancato rilevamento. Nuovo lab `.airdrop-local-lab/mcc-rx-fix-20261104`, README leggibile con artefatti e verifiche. Nessun worker installato modificato, nessun commit/branch/PR/push.

Prima misura RX stock (trial.py, runtime mcc-rxfix/override92, Kitty3114630): dati radiotap frequenza5520 sia prima sia dopo riassociazione controllata UUID+BSSID; ricerca120s exit1. Contatore awdl_rx455 nella prima misura include eco TX None/d0: NON ricezione iPhone. Parser corretto dopo per escludere TX_FLAGS (runnable selfcheck). Cleanup0, core/SSID originali.

Preparata e compilata patch driver default-off airdrop_mcc_monitor (0400), QCA9377/PCI168c:0042, carrier AP6/20 legale già presente. Riporta monitor sul carrier e riavvia monitor background all'arrivo esplicito. Modifica solo mac.c; C harness vero selettore pass,10BTF/60exported symbols, vermagic6.18.36-1-lts pass; ABI runtime resta da calibrare. Modulo SHA988418a8157d379228e512ab8ac1f1659a3c4d6113068f002f0ff6118f9df145, srcversion5CB12092961C6C27397697A. Driver test caricato SOLO IN RAM da file root-staged /run, nessun file modulo originale o boot modificato. Stock diskSHA in driver-session.py.

Primo driver test(mcc-mon6, workerb90fb72...,Kitty3149688): errore inizializzazione NM dopo reload (`not compatible`), cleanup marker pending ma coreA082... e WiFi104/80 già tornati. Readiness corretta con retry limitato agli errori transitori e riconoscimento connessione già ripristinata; check-ready.py pass (anche autenticazione non ritentata). Secondo launcher ready-trial.py(mcc-mon6b,worker486d1b...,Kitty3156106) recupera prima il precedente worker root-owned SHAverificato e rimuove vecchi artefatti, poi prova. Stage root/unit/timer480s come prima. Guardie journal-recovery prima unload, original file hashes, foreign-driver/NM preservation, onecard, ABIcheck; no forced unload.

ready-trial: log kernel conferma monitor2437 mentreSTA104/80, ma zeropeer/RXaction, ricercadestinatario120s exit1. Cleanup0, modulo originale ripristinato. ROOT CAUSE CONCRETA aggiuntiva: AP nativo precedente avviato con iw manca di PROBE_RESP; driver ath10k beacon-offload `ath10k_mac_vif_fix_hidden_ssid` fa vdev_down, poi fallisce template probe, ritorna prima restart/up. In kernel: failed get probe resp/failed update presp/failed fix hidden ssid expect trouble. Quindi dichiarare AP6 con iw non dimostrava effettivo airtime radio: limitare precedenti conclusioni coesistenza a configurazione+Internet. Ricezione frequency può inoltre essere fallback driver, non prova RF autonoma.

Fixnative-ap.py: START_AP via stdlib netlink include NL80211_ATTR_PROBE_RESP fullSSID insiemebeaconhidden eattrsSSID/channel6/NOHT/DTIM. Costanti headerLinux verificate conminiC; check-ap.py pass byte-template/SSID/index/truncation. fullap-worker.py torna su driverORIGINALE; niente reloadmoduli inquesta variante. WorkerSHA3ac0966ce8be1d59757420da8befbcdc2959098ad35a99dc03d3fa6e18020e4f. build-fullap.py/cycle ->fullap-trial.py. Runtime end4-airdrop-mcc-fullap,NM/override87,timer360s; Kitty3179804 «AirDrop — avvio AP completo, driver originale», sudo locale. Al momento ancora in corso, NONsuccessoZIPpresunto: leggere fullap-report/send/kernel e verificarepostflight. BackendMCCpackage/hash invariati250b.../04211...,sempretesttemporanei; workerprod SHAe6d0e4... intatto. Prossimo se stockfullAP nonbasta: combinare APcorretto con driverselector testato, senza assumere giàcausaunica.

### Ripresa verificata — 5 novembre 2026

Fullap concluso: errore GETFAMILY EINVAL prima di START_AP, causato da CTRL_ATTR_FAMILY_NAME3 invece di2. Cleanup0, off, postflight90s. Corretto native-ap.py e aggiunto controllo dei messaggi reali GETFAMILY/START_AP e ACK al check-ap.py; tutti passano. Nuovo fullap2-trial.py incorpora fullap2-worker.py SHA d74ee91d1d6f6a0cb14376c0a2f7471cb4ee974235f2d7f9c0c2686c502b4b0c (corrispondenza verificata via AST), driver stock, runtime mcc-fullap2, conf/override86, timer360s. Non ancora lanciato:4novembre approvazione automatica non completabile per limite d'uso, azione non eseguita.

Il5novembre le verifiche host autorizzate funzionano nuovamente: kernel6.18.36-1-lts, coreA082DD95309E1D00A1EED1F, worker e configurazioni originali con hash invariati, pacchetto candidato assente, cleanup-complete e off per fullap e mon6b. GETFAMILY corretto verificato in sola lettura sul kernel: nl80211ID40. Selfcheck AP e fullap2-worker passano.

Rete ATTUALE diversa: fuckingProShit_iPhone, UUID edfd4558-720c-43a2-b331-294ebcf4b1fd, BSSID aa:17:55:12:7d:eb, canale11/20, ifindex466. Nome identico al destinatario: chiesto se hotspot del medesimo iPhone. Apple richiede Hotspot personale disattivato prima di AirDrop (support.apple.com/it-it/119857, fonte verificata online). Richiesta chiarificazione pendente; nessuna disconnessione né prova radio avviata. Se stesso iPhone, serve altra rete per il PC per testare Wi-Fi+AirDrop simultanei senza hotspot sul destinatario. Non attribuire questo nuovo vincolo ai fallimenti di ieri su ScapeWiFi104/80. Worker installato non sostituito; correzione multicanale non ancora validata con scoperta o ZIP.

L'utente ha poi confermato iPhone pronto e intenzione di spostare il PC a un'altra rete, spegnendo l'hotspot. Il controllo in sola lettura del passaggio rete è stato interrotto senza risultato acquisito; nessun launcher fullap2 avviato. Successiva istruzione esplicita: «adesso non possiamo testare, ci penseremo dopo». TEST RIMANDATI: non avviare nuove prove radio finché non vengono ripresi dall'utente. Richiesto invece recap, schema AirDrop e distinzione fra conoscenze pubbliche e risultati locali. Per riprendere, rileggere la rete effettiva: hotspot11 e precedente ScapeWiFi104 non sono uno stato corrente garantito.
