# AirDrop in end4-pC

Stato: trasferimenti Owly nei due versi riusciti con la QCA9377 sul canale 6.
Correzione confezionata in un pacchetto locale e widget Quickshell implementato.
Installazione persistente in attesa della password sudo nel terminale;
collaudo della CLI Omdrop e del pannello reale ancora da eseguire.


## Prossimi upgrade — priorità concordate al 4 novembre 2026

La doppia connessione è registrata come upgrade futuro; non avviare ora
nuovi test condivisi né sostituire la modalità autonoma funzionante.

1. **Spegnimento affidabile:** riprodurre e correggere l’errore del
   supervisore NMmanaged durante off; verificare anche scadenza, crash e
   cambio rete. Il ripristino nell’ultima prova è riuscito nonostante failed.
2. **Chiusura ricezione:** evitare quando possibile i circa3s aggiuntivi
   per il closing chunk mancante, preservando validazione completa archivio,
   limiti e deadline. Non è un guadagno di velocità radio e non si presenta
   in ogni trasferimento; niente semplice riduzione di STEP senza verifica.
3. **Velocità iPhone->PC:** approfondire ritmo invio, consegna ACK e
   comportamento firmware con misure controllate. Dati attuali circa12s per
   8MiB, contro uploadPC circa6–7s; nessun collo di lettura/windowzero
   osservato. Aggregazione/BlockAck e altre impostazioni restano ipotesi
   sperimentali, da valutare una alla volta con ZIP e SHA.
4. **Internet + AirDrop:** modalità condivisa station+IBSS su44/20, con
   gestione P2P dinamica, test HT7, Internet simultaneo e ripristino; usare
   modalità autonoma se rete incompatibile. Driver attuale: station+IBSS
   limitati a un canale. Reti diverse richiedono altra strada verificata
   (seconda radio o Internet cablato); non promettere multicanale IBSS.
5. **Aggiornamenti kernel/installazione:** procedura riproducibile di
   ricompilazione e verifica moduli per nuovo kernel, diagnostica chiara e
   arresto sicuro se incompatibile. Bundle attuale vincolato a6.18.36-1-lts.
6. **Collaudo prima di distribuzione:** repliche bidirezionali, file più
   grandi e multipli, annullamenti e gestione errori/ripristino verificati.
   Valutare messaggi del widget solo per problemi concreti emersi dai test.

80MHz, nuovi rate, LDPC/SGI e aggregazione sono studi successivi, senza
promesse di guadagno: mantenere come riferimento44/20 HT7 funzionante.
Widget veloce già integrato e confermato dall’utente; non ripetere come
attività aperta l’integrazione già conclusa. Nessun branch/commit/PR/push.

## Obiettivo e scelte

Integrare invio e ricezione AirDrop nella barra Quickshell, riutilizzando il
motore di Omdrop e i componenti grafici di end4-pC. Non serve installare Omarchy.
La compatibilità radio va dimostrata prima di costruire il pannello.

Prima versione: pulsante configurabile nella barra, ricezione temporanea,
dispositivi vicini, invio di file, nome del computer, cartella di destinazione,
stato ed errori. Radar, suoni e gestione grafica dei contatti vengono dopo.
L'identità Apple non è un prerequisito per il primo collaudo: sul dispositivo
Apple useremo «Tutti per 10 minuti».

## 0. Punto di partenza

- [x] Esaminare il plugin locale: versione 0.16.1, CLI Bash e ricevitore Python.
- [x] Identificare la radio: QCA9377, PCI 168c:0042, driver ath10k_pci,
  interfaccia wlp2s0; kernel osservato 6.18.36-1-lts.
- [x] Verificare la separazione fra backend radio, ricevitore e pannello QML.
- [x] Identificare le dipendenze UI di Omarchy: qs.Commons, qs.Ui e Panel.
- [x] Rilevare che Owly e i suoi helper non sono installati; LocalSend è presente.
- [x] Eseguire il doctor locale: segnala il backend per PC mancante.
- [x] Completare le letture radio nella sessione host: il driver dichiara monitor
  e IBSS, con monitor aggiungibile come interfaccia software. L'injection e il
  trasferimento effettivo restano da verificare sul campo.

La QCA9377 non compare nella tabella hardware verificata di Owly. Questo
significa compatibilità sconosciuta, non incompatibilità dimostrata.
Ci sono già modifiche locali alla barra e ai test: conservarle e limitare
gli interventi ai punti necessari, senza reset o ripristini globali.

## 1. Preparare e verificare il backend

- [x] Leggere capacità radio e stato corrente di NetworkManager/Bluetooth,
  annotando canale Wi-Fi, firmware e connessione da ripristinare a fine prova.
- [x] Esaminare le ricette e le dipendenze dei pacchetti disponibili: `owly`
  per CLI e servizio radio, `omdrop-owl` per la compatibilità con Omdrop.
  Verificare cosa il secondo pacchetto installa già, evitando duplicazioni.
- [x] Fissare le versioni scelte e verificare il contratto del backend rispetto
  al plugin locale (minimo 0.7.0 nel codice attualmente presente).
- [x] Installare i soli pacchetti necessari tramite il gestore pacchetti;
  eseguire `owly doctor` e il probe degli helper di Omdrop.
- [x] Se il doctor richiede di abilitare hardware non collaudato, verificare
  le capacità reali prima di impostare `allow_untested`; annotare ogni modifica.
- [x] Concordare il momento del test se occorre interrompere il Wi-Fi.
  Non cambiare il canale del router e non sostituire firmware alla cieca.

Uscita: sappiamo quale modalità può usare la scheda e quali problemi restano.
Se mancano capacità indispensabili, fermare la fase radio e documentare
l'esito; valutare un adattatore supportato o LocalSend prima della UI.

## 2. Collaudo radio e trasferimenti da terminale

Richiede un dispositivo Apple vicino e la partecipazione dell'utente per
aprire AirDrop, accettare l'invio e condividere un file verso il PC.

- [x] Avviare la radio con Owly e verificare awdl0 e il suo IPv6 link-local.
- [x] Verificare il firewall effettivamente in uso; aggiungere solo se serve
  una regola per TCP 8771 su awdl0, limitata agli indirizzi IPv6 link-local.
  Non disabilitare il firewall per far passare il collaudo.
- [x] Prima ricezione Apple → PC con la CLI Owly sperimentale.
- [x] Primo invio PC → Apple riuscito; conferma di ricezione sul telefono.
- [x] Ricezione: verificare integrità, destinazione ed errori.
- [x] Registrare esito del mittente e conferma umana della prova inversa.
  Nessun confronto hash disponibile sul telefono.
- [ ] Ripetere entrambi i versi attraverso Omdrop e il pannello finale.
  Lo stop/avvio della radio fra le due prove Owly è già stato verificato.
- [x] Verificare che il Wi-Fi resti utilizzabile o venga ripristinato dopo lo
  stop, secondo la modalità scelta; conservare l'esito e i log essenziali.

Uscita: trasferimenti ripetibili nei due versi e recupero della connessione.
Se funziona un solo verso, registrare il limite e risolverlo prima di
considerare il backend pronto per l'integrazione completa.

## 3. Rendere Omdrop utilizzabile fuori da Omarchy

- [ ] Provare il setup del plugin con i percorsi reali della configurazione;
  verificare quoting dei percorsi con spazi e unità systemd generata.
- [ ] Installare solo le dipendenze mancanti del ricevitore e del selettore
  file; usare gli strumenti e il portale desktop già presenti.
- [x] Adattare i richiami necessari a notifiche, browser e terminale di
  Omarchy usando le funzionalità esistenti della sessione.
- [x] Conservare la CLI come fonte dello stato, delle preferenze e delle
  operazioni: non duplicare in QML timer, identità o impostazioni persistenti.
- [ ] Verificare `omdrop doctor --json`, `status --json`, `on 1m`, `off`,
  selezione file, invio, ricezione, notifica e apertura del file ricevuto.
- [ ] Verificare che scadenza e stop manuale chiudano davvero la visibilità.
- [ ] Lasciare un controllo eseguibile minimo per ogni logica non banale
  aggiunta, estendendo dove possibile i test già presenti nel plugin.

Uscita: CLI e ricevitore funzionano nella sessione end4-pC senza Omarchy.
Se l'evoluzione upstream rende il plugin locale incompatibile, rivalutare
l'aggiornamento prima di accumulare adattamenti alla versione vecchia.

## 4. Integrare il widget nella barra

- [x] Creare `modules/ii/bar/Omdrop.qml` e `OmdropPopup.qml`, riutilizzando
  pulsanti, popup, icone, colori e tipografia della shell.
- [x] Registrare il widget come `omdrop` nel selettore di BarConfig e nei
  percorsi di caricamento della barra orizzontale e verticale necessari.
- [ ] Rendere il popup apribile con click e utilizzabile da tastiera;
  supportare Escape, focus, tooltip e contrasto degli stati.
- [x] Mostrare distintamente: spento, avvio, ricezione attiva, visibilità
  confermata, backend mancante, operazione fallita e invio in corso.
- [x] Offrire ricezione per 10 minuti, fino a un file e stop manuale;
  mostrare il tempo residuo riportato dalla CLI.
- [ ] Mostrare dispositivi vicini e consentire selezione e invio di file;
  mostrare progresso/cancellazione dove supportati dal motore.
- [x] Esporre modifica del nome e della cartella usando la CLI esistente.
- [x] Interrogare lo stato solo quando serve, con un limite di frequenza;
  serializzare le azioni e gestire output non valido e processi falliti.
- [x] Passare percorsi e nomi come argomenti dei processi, senza interpolarli
  in comandi shell. Non mostrare come riuscita un'azione ancora in corso.
- [x] Aggiungere un singleton di servizio solo se più componenti devono
  condividere il medesimo stato/processo; mantenere pochi file.

Uscita: widget aggiungibile dalle impostazioni della barra e operazioni
equivalenti alla CLI, con errori leggibili e senza bloccare Quickshell.

## 5. Verifica finale e consegna

- [ ] Eseguire i controlli mirati sul codice modificato e i test pertinenti
  del plugin; lasciare un piccolo check ripetibile per la nuova logica.
- [ ] Provare il widget nella sessione reale: entrambi i versi, scadenza,
  cancellazione, nessun dispositivo, selettore annullato e backend assente.
- [ ] Verificare reload della shell durante ricezione/invio: nessun avvio
  duplicato, stato ricostruito dal motore e processi UI chiusi correttamente.
- [ ] Verificare barra orizzontale/verticale, stili disponibili e più monitor;
  rispettare il comportamento dei gruppi della barra e del menu di stile.
- [ ] Documentare installazione, uso, limiti osservati e rimozione; aggiornare
  questo file con versioni effettive, risultati e problemi ancora aperti.
- [ ] Rivedere il diff finale preservando tutte le modifiche preesistenti.

Completato quando il trasferimento funziona dalla barra nei due versi,
la ricezione scade correttamente e la rete torna nello stato previsto.

## Ripristino

Annotare e salvare le configurazioni prima di modificarle. Per annullare:
spegnere ricezione e radio, rimuovere il widget dal layout, rimuovere soltanto
le unità/regole/configurazioni introdotte da questa integrazione, e disinstallare
i pacchetti aggiunti se non servono più. Non eliminare file ricevuti, chiavi
o configurazioni personali come parte della pulizia automatica.

## Riferimenti

- Plugin locale: `omdrop-plugin/README.md` e `omdrop-plugin/docs/radio-backend.md`.
- Owly: https://github.com/t4t5/owly#supported-hardware
- Configurazione radio: https://github.com/t4t5/owly#configuration
- Pacchetti/helper: https://github.com/t4t5/owly/blob/main/packaging/install.sh
- AirDrop e hotspot: https://support.apple.com/en-gb/119857

## Registro operativo — 29 ottobre 2026

- Firmware: `WLAN.TF.2.1-00021-QCARMSWP-1`; nessuna modifica al firmware.
- NetworkManager attivo; Bluetooth presente ma spento.
- Unica connessione: hotspot dell'iPhone, 2462 MHz / canale 11. L'utente
  conferma di non avere una seconda connessione. Non interromperla durante
  preparazione e download. Per AirDrop Apple richiede di disconnettere
  l'hotspot: il collaudo dovrà essere coordinato e potrà svolgersi offline.
- La modalità shared di Owly richiede canale 6, 44 o 149: l'attuale canale 11
  non è adatto. Valutare con doctor la modalità exclusive prima di provarla.
- Servizi ufw/firewalld/nftables inattivi; controllato anche il ruleset nft
  effettivo con privilegi amministrativi: nessuna catena input. Sono presenti
  regole Docker per forwarding/NAT. Nessuna modifica al firewall necessaria
  per il collaudo nella configurazione osservata.
- Scelto `omdrop-owl-bin 0.4.1-1`: fornisce insieme `owly` e `omdrop-owl`,
  con gli helper per il plugin Bash/Python locale. Contratto helper 0.10.0,
  superiore al minimo 0.7.0 richiesto dal plugin.
- Ricette AUR e script di installazione esaminati. Release ufficiale GitHub
  verificata con SHA256
  `1df4ea4a208f0fa1ddf35bc61383e779de20fdcaaa2957a2777cff9b09efe91c`.
- Pacchetto preparato con makepkg in `/tmp/end4-airdrop-review/build/`;
  controllati metadati, contenuto, percorsi e proprietà root dei 53 elementi.
  Il binario `owly --help` funziona sul sistema attuale.
- Installati tramite pacman `omdrop-owl-bin 0.4.1-1`, `python-ifaddr 0.2.0-7`,
  `python-libarchive-c 5.3-1` e `python-zeroconf 0.149.16-1`. Autenticazione
  sudo effettuata dall'utente nel terminale locale.
- Doctor e probe riconoscono il backend, ma inizialmente rifiutano di usare
  la scheda non collaudata. Creato `/etc/owly/radio.toml` (prima assente),
  root:root 0644, con `station = "wlp2s0"` e `allow_untested = true`.
  Nessun avvio automatico della radio aggiunto.
- Il servizio 0.4.1 già avviato non ha recepito subito radio.toml; verificato
  che la sessione è `idle` e richiesto il solo riavvio di owlyd per ricaricarlo.
- Il doctor successivo riconosce `168c:0042` e `ath10k_pci`: monitor e IBSS
  affiancabili alla station; canali 6 e 44 trasmissibili, 149 no-ir. Il solo
  blocco della modalità shared è il canale 11 dell'hotspot.
- L'utente autorizza il collaudo offline adesso. Creato il file prima assente
  `/etc/owly/drivers.toml` con profilo `drivers.ath10k_pci`: `status=untested`,
  `mode=exclusive`, `channels=[6]`, `reconnect_after_monitor=true`.
  Riavviato solo owlyd mentre idle. Doctor: `hardware=true`, `missing=[]`,
  modalità exclusive sul canale 6. Questo non dimostra ancora un trasferimento.
- Aperto il terminale «AirDrop - collaudo offline». Attende un Invio prima
  di accendere Bluetooth e avviare il comando ufficiale
  `owly test-card --watch 0 --out /tmp/end4-airdrop-review/results`.
  Il wrapper limita la prova a 12 minuti, indica come disattivare/riattivare
  l'hotspot e riconnette la connessione salvata. Ripristina Bluetooth spento,
  come osservato all'inizio. Dopo la riconnessione esegue 10 ping al gateway.
- Il collaudo ufficiale accetta automaticamente i file in `/tmp/owly-test-*`;
  usare una foto di prova. In questa prima prova offline il controllo Wi-Fi
  di 5 minuti upstream è disabilitato perché l'hotspot viene spento a mano:
  resta da verificare separatamente la stabilità dopo la riconnessione.
- Primo tentativo: probe e configurazione NetworkManager passano; radio
  exclusive sul canale 6 avviata con successo, awdl0 dotata di IPv6 link-local.
  Nessun peer AWDL rilevato in circa 138 secondi, poi interruzione del test.
  Nessun trasferimento effettuato e nessun report JSON conclusivo generato.
- Nei log radio `rx_action` resta 0, mentre `rx_data` cresce fino a 222;
  la trasmissione di action frame è contabilizzata ma non dimostra che
  l'iPhone li abbia ricevuti. Non attribuire ancora l'esito a un'incompatibilità
  hardware: verificare la preparazione del telefono e la scoperta AWDL.
- Dopo l'interruzione il servizio registra `owner-gone`, la sessione torna
  `idle`, Bluetooth torna spento e il PC si riconnette all'hotspot. Il nuovo
  collegamento è sul canale 6 (prima era 11). Nessun reload del driver eseguito.
- Controllo dopo il recupero: 60 ping su 60 ricevuti dal gateway dell'hotspot,
  nessuna perdita nel minuto osservato. Non equivale al collaudo di 5 minuti.
- L'utente conferma che durante il tentativo l'hotspot era spento e la
  schermata Foto → Condividi → AirDrop era aperta; il PC non compariva.
- La documentazione Linux Wireless di ath10k elenca packet injection fra
  i limiti del driver. È un possibile ostacolo distinto dal supporto monitor:
  https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath10k.html
- Preparata un'ultima prova sul canale 44, dichiarato trasmissibile dal
  doctor: terminale «AirDrop - ultima prova canale 44». Autentica la modifica
  del profilo e il riavvio idle di owlyd, quindi aspetta l'Invio per il test.
  Comando di collaudo invariato, limite complessivo 8 minuti. Attendere la
  ricerca fino a 180 secondi e rispondere alle domande per salvare il report.
  Se non si scopre alcun peer anche qui, fermare le prove sulla scheda attuale.
- Esito del tentativo sul canale 44: il probe preliminare passa, ma l'avvio
  effettivo fallisce dopo 6290 ms con «Couldn't start AWDL's ad-hoc cell on
  any of AirDrop's channels.». Rapporto generato:
  `/tmp/end4-airdrop-review/results/owly-test-ath10k_pci-1793273171.json`.
  Il risultato distingue capacità dichiarate dal driver e comportamento reale:
  `missing=[]` nel doctor non significa che l'hardware funzioni in un test.
- Il rapporto upstream etichetta baseline «pass» anche con 0 risposte su 9:
  non considerare quella voce una verifica riuscita della connettività.
  Dopo il ripristino, il wrapper misura invece 10 risposte su 10 dal gateway.
- L'utente conferma assenza di scoperta nei due versi con AirDrop aperto
  a tutti e foto in condivisione. Segnala circa 140 secondi di attesa:
  il log del primo tentativo mostra circa 138 secondi; quello sul canale 44
  mostra invece il fallimento di avvio. Nessun trasferimento verificato.
- Verifica finale host: `wlp2s0` collegata all'hotspot dell'iPhone; Owly `idle`.
  Le interfacce `br-*` sono di tipo bridge locale, non connessioni Wi-Fi.
  L'iPhone si è collegato a una rete pubblica secondo quanto riferito
  dall'utente; lo stato del telefono non è verificabile dal PC. L'accesso
  automatico a quella rete è gestito dal telefono e non è richiesto dal test.
- Completata pulizia del collaudo: impostato `allow_untested=false` e fermato
  owlyd dopo aver verificato che fosse idle. Il profilo di canale 44 resta
  documentato ma non abilita
  la scheda senza opt-in. Nessuna disinstallazione automatica dei pacchetti.
- Log e risultati: `/tmp/end4-airdrop-review/install.log`, `doctor.json`,
  `probe.json`. Sono file temporanei: riportare qui gli esiti essenziali.
  Il report dopo il riavvio è in `doctor-exclusive.json`; il collaudo scrive
  `offline-test.log` e i rapporti `results/owly-test-*.json`.
  Per la variante sul canale 44: `doctor-44.json`, `offline-test-44.log`.

## Diagnosi approfondita richiesta dall'utente

- L'utente vuole continuare con la propria QCA9377 e capire il rifiuto sul 44
  e l'assenza di scoperta sul 6. Conferma posizione Italia e iOS 26.6.
- Log completo del 44: `no ad-hoc cell on 5220 MHz: Invalid argument
  (os error 22)`. Il kernel rifiuta il join; non è un timeout AirDrop.
- NetworkManager aveva avviato una connessione alternativa prima del join,
  ma l'audit mostra poi `managed=no` riuscito prima della richiesta ad-hoc:
  la riconnessione precedente non dimostra da sola la causa del rifiuto.
- Trovata un'omissione reale del sistema: pacchetto `wireless-regdb` assente
  e log kernel `failed to load regulatory.db`. Installato dal repository
  ufficiale `wireless-regdb 2026.09.03-1`; eseguiti `iw reg reload` e
  `iw reg set IT` dopo conferma del Paese. Il dominio globale ora è IT;
  il dominio hardware resta 99. Nessuna modifica ai limiti EEPROM.
- Sorgenti Owly v0.4.1: il dato `rx_data` filtra il BSSID AWDL e i frame
  estranei vengono ignorati, quindi i 222 pacchetti del primo test meritano
  approfondimento. `rx_action` conta invece action frame parsati, da sorgente
  diversa da quella locale, dopo i controlli del contenuto. Lo zero non
  distingue automaticamente silenzio radio, filtri firmware e parsing.
- Primo controllo diretto con iw invalidato: l'interfaccia temporanea
  `qsdiagibss0` non era esclusa dalle regole NetworkManager, che l'ha cambiata
  in client. Il risultato EOPNOTSUPP su tutti i join non dimostra un limite
  del chipset. Interfaccia rimossa e connessione hotspot ripristinata.
- Corretto il controllo con `owlyibss0`, già esclusa dal pacchetto Owly;
  aggiunti assert sullo stato unmanaged e sul tipo IBSS. Il ripristino ora
  attende che il dispositivo sia disponibile e preserva il flag autoconnect.
  Quattro varianti: 44 HT20 con beacon 10000/100 TU, 44 NOHT 100 TU,
  6 HT20 10000 TU. Il telefono può mantenere l'hotspot attivo per questa fase.
- Script e log sotto `/tmp/end4-airdrop-review/diagnosis/`:
  `regdb-install.log`, `check-ibss-root.sh`, `check-ibss.sh`,
  `ibss-matrix.log` (prima prova invalidata), `ibss-matrix-isolated.log`.
- Esito del confronto isolato: tipo IBSS e unmanaged verificati; 44 rifiutato
  con EINVAL in tutte e tre le varianti, 6 HT20 accettato e rete creata.
  Il dump dopo la disconnessione mostra `5220 MHz [44] ... (no IR)`, mentre
  il dump da associata non aveva quel flag. Nel kernel nl80211_join_ibss
  rifiuta con EINVAL un canale sul quale cfg80211_reg_can_beacon è falso.
  La causa osservata del 44 è quindi il vincolo di iniziativa radio che
  compare quando la station viene disassociata, anche con regdb e dominio IT.
  Non provare a rimuovere i vincoli EEPROM; il 6 resta disponibile.
- Corretto il ripristino della prova isolata: connessione hotspot attivata
  con successo. La prima prova invalidata aveva richiesto un secondo
  tentativo perché il dispositivo non era ancora disponibile.
- Preparata una cattura sul 6 con il comando nativo `owly capture discovery
  --ios 26.6 --seconds 60`. Usa il ricevitore standalone e registra errori
  di injection con log debug limitato al modulo native. Configurazioni di
  Owly, Bluetooth e autoconnect vengono ripristinati; log debug solo runtime.
  Script `diagnosis/capture-six.sh`, con flock per impedire doppi avvii.
- Auto-review aveva segnalato una possibile cattura duplicata; verifiche
  host hanno escluso processi/terminali di cattura attivi e mostrato owlyd
  inactive, configurazione ancora disabilitata e log assenti. Dopo l'aggiunta
  del lock l'apertura del terminale è stata autorizzata ed eseguita.
- Il terminale della cattura è aperto ma il log è ancora fermo alla
  preparazione prima di sudo: attende autenticazione locale. Nessuna cattura
  o nuova sessione radio risulta avviata da questa prova al momento del check.
- L'utente era lontano dal PC e richiede di ripetere la cattura: verificata
  assenza di vecchi processi e servizio inactive, riaperto lo stesso script
  con lock. La cattura è poi stata eseguita sul canale 6 per 60 secondi.
- Artefatto: `diagnosis/capture-six/discovery-ios26.6-ath10k_pci-ch6-1.pcap`
  e relativo TOML con indirizzi anonimizzati. 4958 frame totali:
  2896 action frame con sorgente locale, 1937 data frame locali e 125 data
  frame da sorgenti remote. Nessun action frame remoto nella cattura.
- Una sorgente remota invia 69 TCP SYN alla porta 8771 del PC (62 con flag
  0x02, 7 con ECN 0xc2) e 50 pacchetti mDNS UDP/5353; una seconda sorgente
  invia altri 6 mDNS. La cattura non consente di attribuire con certezza
  gli indirizzi a uno specifico telefono, ma dimostra tentativi remoti di
  contattare il ricevitore, non una radio interamente priva di traffico.
- Il motore registra `rx_action=0`, `rx_data=125`, `syn_held=69`,
  `syn_released=0`, `delivered=0`, nessun peer valido. Il codice di Node
  trattiene i SYN dei peer non confermati dagli annunci; è il blocco
  osservato prima della connessione al ricevitore. Nessun errore di injection
  nei log native debug. La conferma di connessione TCP non è riuscita.
- Configurazione e Bluetooth ripristinati; owlyd fermato. La riconnessione
  al solo hotspot non lo trova ancora; chiesta conferma all'utente che sia
  stato riacceso prima di ulteriori tentativi. Non cambiare rete alla cieca.
- Analisi ripetibile: `diagnosis/summarize-capture.py`, con
  `--self-test` eseguito (controlli su action, TCP SYN e file troncati);
  riepilogo in `diagnosis/capture-six-summary.json`.
- Preparata, ma non avviata, la variante `diagnosis/capture-six-mgmt.sh`:
  registra esplicitamente gli action frame vendor Apple tramite
  `iw dev owlyibss0 mgmt dump frame d0 7f:00:17:f2:08` durante una nuova
  cattura. Serve a confrontare il percorso nl80211 con il monitor; nessuna
  sostituzione di firmware e nessuna modifica del motore ancora eseguita.
- Pista firmware da verificare dopo la cattura: la mailing list ath10k
  contiene una segnalazione del 2020 su regressione monitor della QCA9377
  fra le versioni firmware (non dimostra da sola il comportamento attuale):
  https://lists.infradead.org/pipermail/ath10k/2020-November/012053.html
  Nessun firmware sostituito. La versione in uso è API 6,
  WLAN.TF.2.1-00021-QCARMSWP-1, senza feature raw-mode annunciata.
  Il sorgente del driver richiede quella feature per frame_mode=raw o
  cryptmode software: non impostarli alla cieca come tentativo di correzione.

- Aggiornamento dell'utente: ora il PC usa una rete Wi-Fi separata dall'iPhone,
  non più il suo hotspot. Verificata connessione `ScapeWiFi STAR 5GHz`,
  canale 100/5500 MHz, UUID `51bc989c-c09f-4b24-9cb8-e9224c72584c`.
  Il canale attuale non è tra quelli condivisibili da Owly (6/44/149):
  la prossima prova resta esclusiva sul 6, con una breve disconnessione.
- Corretto `diagnosis/capture-six-mgmt.sh`: memorizza e valida l'UUID della
  connessione effettiva, la ripristina anche in cleanup e non tenta più
  l'hotspot precedente. Rimossi gli Invio legati alla riaccensione hotspot.
  `bash -n` e `diagnosis/check-reconnect.py` passano; quest'ultimo esegue il
  cleanup reale con comandi host simulati e verifica riconnessione e caso
  di rete già ripristinata.
- Verificati servizio inactive e assenza di vecchie catture. Aperto il
  terminale «AirDrop - prova annunci canale 6»: attende password sudo e
  successivamente Invio dell'utente prima di attivare la radio.

## Esito ricezione management e correzione sperimentale

- Prova nl80211 completata: ripristinata automaticamente la rete corrente
  sul canale 100; verificati owlyd inactive e opt-in disabilitato.
- `mgmt-register-six.log` contiene 371 action frame AWDL da due sorgenti
  remote. La cattura monitor parallela `discovery-mgmt-ios26.6-ath10k_pci-ch6-1.pcap`
  contiene 2946 frame, inclusi 2897 action frame locali e 21 mDNS remoti,
  ma nessun action frame remoto. Il driver riceve gli annunci sul percorso
  nl80211: il monitor usato dal backend non li espone in questa prova.
- Scaricato sorgente ufficiale Owly v0.4.1 in `/tmp/end4-airdrop-review/owly-0.4.1`.
  Correzione conservata in `tools/airdrop/owly-qca9377-management.patch`:
  aggiunge al monitor una ricezione asincrona nl80211 solo con ambiente
  `OWLY_RX_MGMT=1`, registrata sull'interfaccia IBSS esistente. Nessuna
  modifica ai controlli di validità dei peer o ai limiti radio.
- Test parser degli eventi: passa, inclusi messaggi troncati, più frame,
  indice interfaccia errato, RSSI negativo e vendor estraneo. Replay della
  cattura reale nel motore: 371 frame, 370 action accettati, 1 malformato,
  2 peer validi. Il replay usa tempi sintetici: dimostra parsing e conferma
  dei peer, non sincronizzazione o trasferimento reale.
- Comandi ripetibili dalla copia sorgente, con cache Cargo locale:
  `CARGO_HOME=/tmp/end4-airdrop-review/cargo-home cargo test --locked -p owly-radio --lib management_tests`;
  replay opzionale con `OWLY_MGMT_CAPTURE=/tmp/end4-airdrop-review/diagnosis/mgmt-register-six.log`
  e filtro `captured_management_frames -- --ignored --nocapture`.
- Compilato con successo il solo owlyd ottimizzato; i binari installati restano
  originali. Preparato `diagnosis/capture-six-bridge.sh`: usa una copia
  sotto `/run/owly`, override systemd solo runtime, avvio dopo Invio,
  raccolta log e ripristino completo al termine. La seconda prova non
  avvia iw mgmt dump, perché la registrazione è ora del demone.

- Individuata anche una corsa nello script di prova: `awdl0` può esistere
  prima che la lease D-Bus sia up. Il ricevitore partiva troppo presto e
  rinunciava alla cadenza di annunci richiesta dalla radio (messaggio
  `not announcing as the radio asks: the radio isn't up`). Lo script del
  prossimo test attende ora `owly radio peers` con esito zero, oltre
  all'esistenza dell'interfaccia, prima di avviare il ricevitore.

- Aperto il terminale «AirDrop - prova correzione QCA9377» con lo script
  bridge. Attende password sudo, se richiesta, e Invio prima della radio.
  La patch è salvata nel progetto; nessun binario installato sostituito.

## Prima ricezione riuscita — canale 6

- Prova reale `capture-six-bridge.sh` completata: 2 peer validi; `rx_action`
  sale a 374, `rx_data` a 5378, `delivered` a 5350. Nessun SYN trattenuto.
  Annunci del ricevitore confermati: 64 copie distanziate 16 ms, ogni 3 s.
- L'iPhone identificato nella richiesta AirDrop ha inviato `IMG_0910.PNG`:
  7.167.177 byte ricevuti, uguali alla dimensione annunciata dal mittente.
  Verificati firma PNG, tutti i 445 CRC dei chunk e IEND completo senza
  dati residui. Non è stato confrontato l'hash con quello sul telefono.
- SHA-256 del file ricevuto:
  `000d253c6183a3812793715a48164275d15850012af920ee0e6bbd900790f869`.
- Copia conservata senza sovrascritture in
  `/home/xlini/Downloads/AirDrop/IMG_0910.PNG`; hash verificato dopo copia.
- Log: `diagnosis/receiver-six-bridge.log`, `daemon-six-bridge.log`,
  `radio-six-bridge.log`; PCAP anonimizzato
  `capture-six/discovery-bridge-ios26.6-ath10k_pci-ch6-1.pcap` (17170 frame).
  Il PCAP monitor continua a non contenere gli annunci remoti, che ora
  il motore riceve correttamente dal socket nl80211.
- Dopo la prova: Wi-Fi `ScapeWiFi STAR 5GHz` ripristinato, owlyd inactive,
  opt-in disabilitato, override runtime e binario sperimentale rimossi.
- Preparato e aperto `diagnosis/send-six-bridge.sh`, titolo terminale
  «AirDrop - invio PC verso iPhone». Attende Invio; invia solo un piccolo
  `prova-airdrop.txt` all'indirizzo AWDL del telefono identificato nella
  ricezione, senza scegliere automaticamente altri destinatari. Ripristina
  la rete e rimuove l'override come la prova precedente. `bash -n` e check
  del cleanup superati.

## Consolidamento e pannello preparati

- Invio Owly completato: `accepted`, 177/177 byte del trasferimento e
  `delivered`; l'utente conferma il `.txt` ricevuto sull'iPhone. Rete e
  Bluetooth ripristinati anche dopo questa seconda sessione radio.
- `tools/airdrop/PKGBUILD` contiene la ricetta del pacchetto aggiuntivo
  `owly-qca9377-fix 0.4.1-1`, vincolato al backend 0.4.1, con archivio
  sorgente e patch verificati SHA-256. Non sovrascrive i binari upstream:
  installa `/usr/lib/owly-qca9377/owlyd` e un drop-in systemd dedicato.
- Pacchetto locale assemblato con `makepkg --repackage` dal binario già
  compilato e collaudato; l'identità byte per byte è stata verificata:
  SHA-256 `47fa6c73dc4bcc3191c15594e76b6bffa9fd6629a16265ce37e5d12fb7db09f6`.
  La nuova compilazione makepkg aveva esaurito la quota degli intermedi;
  rimossi solo gli intermedi generati, conservando binario, sorgenti e log.
  La ricetta mantiene build e test da sorgente per le ricostruzioni future.
- Il pacchetto è conservato localmente in `tools/airdrop/` e ignorato da git.
  `tools/airdrop/install.sh` verifica il dispositivo, chiede sudo, ferma
  soltanto un demone idle, installa il pacchetto, salva le vecchie TOML in
  `*.before-quickshell`, fissa il canale 6/Italia e prepara CLI e ricevitore.
  Non acquisisce la radio. Log in `~/.local/state/omdrop/install.log`.
- Il primo tentativo si era fermato perché owlyd risultava attivo ma idle;
  corretto il controllo per distinguere il servizio dalla sessione radio.
  La richiesta `sudo -v` è poi scaduta senza password: nessuna installazione
  persistente riuscita. A codice definitivo, riaperto il terminale
  «AirDrop - installazione pronta».
- Adattato il plugin: notifiche native `notify-send`, apertura con `xdg-open`,
  terminale Kitty quando i launcher Omarchy sono assenti. Le notifiche con
  azione vivono in un'unità utente separata dalla finestra di ricezione.
  I percorsi del servizio sono quotati; il selettore file aveva già il
  fallback al portale desktop e non richiede modifiche o dipendenze nuove.
- Creati `modules/ii/bar/Omdrop.qml` e `OmdropPopup.qml`; registrato AirDrop
  in BarConfig. Ricezione 10 minuti/una volta, stato dalla CLI, scelta file,
  nome e cartella, peer con nomi risolti, avanzamento testuale e annullamento
  invio. Nessun timer di scadenza duplicato nel QML. La ricerca nomi termina
  alla chiusura del pannello. Segnalata nell'interfaccia la pausa del Wi-Fi.
- L'installer aggiunge il widget prima di System Icons solo se non è già
  presente nei layout della barra o dell'isola. Aggiornamento JSON atomico,
  preservando impostazioni, permessi e modifiche concorrenti rilevate.
- Controlli: suite plugin 216 casi, 1 saltato. Due upload inizialmente
  rifiutati con 413 perché `/tmp` aveva meno della riserva di 1 GiB;
  rieseguiti sul disco con spazio sufficiente, entrambi passano. Nessun
  limite del ricevitore è stato disattivato per ottenere il risultato.
- `python3 tests/omdrop-ui-check.py` verifica parsing rigoroso, argomenti
  letterali, serializzazione comandi, cancellazione e modifica del layout
  senza duplicati o perdita di impostazioni. Test nativi desktop aggiunti
  in `omdrop-plugin/tests/test_desktop_portability.py` e superati.
- Caricamento reale QML su Wayland con finestra nascosta e CLI finta:
  widget e popup creati e chiusi correttamente, inclusi due peer e un comando
  fallito senza stderr che viene segnalato come errore. Ripetibile con
  `python3 tests/omdrop-ui-check.py --smoke` nella sessione Wayland.
  Corretto l'import Translation
  trovato da questa prova. `qmlformat` Qt 6 e `bash -n` passano. Il test
  offscreen puro non è usabile perché la shell richiede il backend PanelWindow
  Wayland; la prova nascosta usa configurazioni XDG isolate.
- Modifiche preesistenti a isola, risorse, altri widget e test conservate.

Prossimo passo: completare sudo nel terminale «AirDrop - installazione pronta», verificare pacchetto,
`omdrop doctor/status`, unità utente e pulsante effettivo. Poi ricezione e invio
dal pannello, scadenza, annullamento e ripristino della connessione.

## Ricostruzione e rimozione della correzione locale

Per ricostruire: `cd tools/airdrop && makepkg` (Rust già presente; serve spazio
per gli intermedi), poi `./install.sh ./owly-qca9377-fix-0.4.1-1-x86_64.pkg.tar.zst`.
Il pacchetto include solo demone aggiuntivo, drop-in e licenza; non accende la radio.
Per rimuovere, prima `omdrop off`, quindi `sudo pacman -R owly-qca9377-fix`,
ripristino delle due TOML da `*.before-quickshell` e `sudo systemctl daemon-reload`.
Rimuovere `omdrop` dal layout della barra se desiderato. Conservare foto,
chiavi, preferenze e altri pacchetti finché non se ne richiede la rimozione.

## Ripristino Quickshell e verifica del widget

- Alla richiesta dell'utente Quickshell non era più in esecuzione. Il core
  della vecchia istanza principale (PID 1633) riporta SIGABRT nel blocco
  schermo `WlSessionLock::updateSurfaces`, durante una scorciatoia globale.
  Il widget AirDrop non era ancora presente nel layout utente; il pacchetto
  persistente non risulta installato (autenticazioni sudo scadute).
- Riavviata la configurazione `end4-pC`, verificando istanza viva e superfici
  `quickshell:bar` e background presenti in Hyprland.
- Corretto il widget per il contenitore BarGroup: radice Item con pulsante
  interno, senza esporre la proprietà Qt `mirrored` di sola lettura al loader.
  I callback dei processi ignorano gli eventi durante la distruzione.
- Il popup viene creato alla prima apertura, con barra già mappata, e resta
  istanziato quando viene nascosto. Nessuna distruzione dal callback del
  focus e nessuna finestra nativa creata prima che il parent sia pronto.
  La prova nascosta da sola non copriva il comportamento di mapping Wayland.
- Test aggiornato: `python3 tests/omdrop-ui-check.py --smoke --visible`
  con PanelWindow e BarGroup reali, configurazione isolata, CLI finta,
  riaperture ripetute, verifica del popup mantenuto vivo e degli errori.
  Superato con il renderer nativo; test parser/comandi e sintassi superati.
- Il blocco schermo non è stato modificato. Installazione persistente
  AirDrop e prove dei trasferimenti dal pannello restano nella fase successiva.

Verifica finale del ripristino: configurazione caricata e barra su eDP-1
1920×68. Per riavviare, attendere l'uscita dopo `qs kill -c end4-pC` prima
di `qs -c end4-pC --no-duplicate --daemonize`: il kill è asincrono.

## Installazione persistente completata

- Completata l'autenticazione nel terminale «AirDrop - configurazione definitiva».
  Installato `owly-qca9377-fix 0.4.1-1`; SHA-256 del demone uguale al binario
  dei trasferimenti riusciti. Il servizio attivo usa `/usr/lib/owly-qca9377/owlyd`
  con `OWLY_RX_MGMT=1`.
- `/etc/owly/radio.toml`: `allow_untested = true`, Italia e canale 6.
  Profilo ath10k_pci esclusivo su 6, riconnessione abilitata. `untested`
  resta la classificazione del backend; il collaudo locale è annotato nel profilo.
- `omdrop doctor --json`: `ready: true`, nessun requisito mancante.
  Ricezione spenta, destinazione `~/Downloads/AirDrop`, Quickshell attivo.
  Riaprire il popup aggiorna la verifica dei requisiti e abilita il pulsante.
- Restano da eseguire le prove di ricezione e invio attraverso il widget.

## Correzione dell'avvio del ricevitore

- Primo avvio dal widget fallito: systemd rifiutava `WorkingDirectory`
  perché le virgolette aggiunte al template diventavano parte del percorso.
  Rimossa la quotatura solo da questa direttiva; mantenuta per l'argomento
  di `ExecStart`, che segue una sintassi diversa.
- Aggiunto controllo ripetibile con il parser reale di systemd e un percorso
  con spazi in `tests/test_desktop_portability.py`; due controlli superati.
- Riapplicato `omdrop setup`: unità `loaded`, percorso riconosciuto.
  Avvio `omdrop on -e 10m` riuscito: ricevitore attivo, `receiving: true`,
  `visible: true`, nome `archlinux`. Il journal conferma il bind effettivo
  su IPv6 AWDL, porta 8771, e la chiusura regolare dopo dieci minuti.
  Nessun trasferimento dal widget confermato in questa finestra. AirDrop
  torna spento alla scadenza; il Wi-Fi riprende alla chiusura.

## Preparazione della proposta upstream

- L'utente conferma ricezione e invio dall'interfaccia. Restano da misurare
  le prestazioni; finestra una tantum e cancellazione reale richiedono prove
  dedicate. Il backend su canale 6 resta una configurazione locale.
- Creato `feat/airdrop` nel worktree separato `../end4-pC-airdrop`, dalla base
  ufficiale `upstream/main` aggiornata a `157a46fb`. Checkout in uso e modifiche
  preesistenti conservati; la proposta non eredita i commit personali di `latest`.
- Due commit: `e0844044` (patch desktop Omdrop MIT e controlli), `1362a0f1`
  (widget opzionale, icona, impostazioni, documentazione e controlli UI).
- CLI e ricevitore Omdrop restano dipendenze esterne, con versione e patch
  documentate. Nessun file di `tools/airdrop/` e nessuna configurazione hardware
  sono inclusi nel branch generico. L'installazione locale resta funzionante.
- Superati cinque scenari QML su Wayland con CLI finta, parser e argomenti,
  verifica systemd con spazi e azioni native. Nessuna radio acquisita durante
  questa preparazione. Dettagli e bozza in `PR-AIRDROP.md`, fuori dai commit.

## Allineamento grafico ai pulsanti utilità

- Il pulsante AirDrop riusa `UtilButton` negli stili Material e
  `CircleUtilButton` negli altri stili, mantenendo il controller radice Item.
  Dimensioni e spaziatura come Util Buttons; espansione Material in hover,
  focus tastiera, popup aperto o ricezione attiva. Icona trasparente e colori
  dal tema, con attivazione accessibile da tastiera.
- Aggiornata la configurazione attiva e il branch `feat/airdrop`, preservando
  la rispettiva risoluzione della CLI. Superati controlli delle tre geometrie
  (Material orizzontale, Material verticale e classica), popup e stati backend.
- Quickshell riavviato, barra visibile e risultato a riposo verificato con
  cattura locale. AirDrop era spento; nessuna radio attivata per questi test.
- Terzo commit locale `302a12d3`, bozza della PR aggiornata. Nessun push.

## Controllo della copia Omdrop aggiornata

- Copia aggiunta dall'utente: `omdrop-plugin-aggiornato`, manifest **0.18.7**;
  la copia attiva resta **0.16.1**. La cartella nuova è un'estrazione senza
  `.git`: non va attribuito ad essa l'HEAD del repository padre. La licenza
  MIT è identica. Nessun aggiornamento dell'installazione effettuato.
- Aggiunto `core/`, workspace Rust **0.1.11**. L'entry point resta `bin/omdrop`;
  passa a un core installato solo se abbastanza recente e con gli hook del
  backend. Gli hook Owly esistono dalla 0.4.0, ma `core_supported()` non propone
  ancora l'installazione su Owly: il collaudo su questo backend è dichiarato
  incompleto. Il fallback Python è ancora disponibile. Core non compilato,
  installato o attivato durante questo controllo.
- Correzioni da adottare con priorità: parser `safeplist` con limiti a dimensione,
  profondità e riferimenti; controlli più rigorosi su firme e identità Apple;
  nomi, log e record degli arrivi normalizzati; conteggio e budget per i link;
  nessun file estraneo o symlink interpretato come un nuovo arrivo.
- CA Apple inclusa rinnovata: la vecchia `apple-aai-ca.pem` termina il
  21 ottobre 2026, la nuova il 4 ottobre 2028 (date lette con OpenSSL).
  Rilevante soprattutto per l'identificazione Apple e Contacts Only.
- Ricevitore: gestisce disconnessioni e riavvii più puliti. Verifica in modo
  limitato se un archivio è completo quando manca il chunk HTTP finale;
  controlla la presenza della fine CPIO prima di accettarlo. Chiude la
  connessione al termine e gestisce i byte ancora in transito per evitare reset.
  Questo può risolvere attese a trasferimento concluso, non dimostra maggiore
  banda radio.
- Notifiche e clipboard: gestione HEIC/HEIF/AVIF con conversioni opzionali,
  anteprime limitate e decodifiche serializzate; fallback al file manager se
  manca un'applicazione adatta. Il watcher scrive/legge un record per file,
  compresi nomi con virgole e trasferimenti con molti file.
- Interfaccia da adattare al nostro widget: retry dei nomi limitati a due
  ricerche infruttuose e successivo ricontrollo ogni minuto; nomi limitati ai
  peer effettivamente presenti; rollback dei nomi appresi se la CLI termina
  con codice 65 per elenco sospetto. Il nostro widget non ha ancora questi
  accorgimenti. La grafica Omarchy non serve per adottare la logica.
- `status --json` della nuova CLI supera il parser effettivo del widget.
  `doctor --json` mantiene `ready` e `missing`; il nuovo campo `offers` è
  aggiuntivo e non rompe il contratto. Verifiche eseguite in sola lettura,
  forzando il fallback Python, senza acquisire la radio.
- **Patch desktop vecchia non riutilizzabile così com'è**: su copia temporanea
  della 0.18.7 `patch` fallisce un hunk; gli inserimenti senza contesto finiscono
  anche in posizioni sbagliate e `bash -n` fallisce su `notify-native)`.
  Ricostruire la patch per una nuova revisione fissata, con contesto sufficiente,
  mantenendo i fallback notify-send/xdg-open/Kitty e le virgolette di ExecStart.
  Servizio e dipendenze desktop non risultano risolti dall'upstream nuovo.
- Nessuna modifica QCA9377/ath10k, `OWLY_RX_MGMT` o soluzione dei vincoli sul
  canale 44 trovata nella copia nuova. La correzione Owly locale resta necessaria.
- Passo successivo proposto: verificare il tag/revisione sorgente della 0.18.7,
  aggiornare patch e pin nel branch isolato, integrare gli accorgimenti dei peer,
  quindi collaudare in fallback Python con il demone Owly già funzionante.
  CLI, symlink e unità del ricevitore vanno aggiornati insieme: la sola copia
  della cartella nuova non cambia i riferimenti dell'installazione attiva.
- Suite Python nuova: **413 test eseguiti, 409 superati, 4 saltati, nessun
  errore**, in 293,584 secondi, con `OMDROP_IMPLEMENTATION=python`. Directory
  temporanea isolata sul disco home, evitando la riserva di spazio insufficiente
  del tmpfs `/tmp`. Log locale `/tmp/end4-omdrop-0187-tests.log`.
- Anche il core Rust conserva chiamate alle utility Omarchy per notifiche,
  browser e terminale: adottarlo non elimina automaticamente il lavoro di
  portabilità desktop. La suite Rust non è stata eseguita in questo audit.

## Aggiornamento a Omdrop 0.18.7 applicato

- Recuperato il tag ufficiale `v0.18.7`, commit
  `c73e8a696bee6ade33c3aad920bba9240de2481a`: tutti i 203 file del tag
  corrispondono alla copia fornita dall'utente. Copia fornita e vecchia
  installazione 0.16.1 preservate.
- Rifatta la patch desktop con contesto completo. Preservati i fallback
  notify-send/xdg-open/Kitty e la corretta quotatura di ExecStart; le notifiche
  native mantengono le nuove anteprime HEIC e l'apertura nel file manager.
  Aggiunta validazione degli argomenti dell'azione di notifica.
- Widget: nomi solo per peer presenti, caratteri di controllo rimossi e limite
  senza spezzare coppie surrogate; rollback dei nomi dopo stream falliti,
  incluso exit 65; due tentativi infruttuosi portano a ricontrollo dopo un minuto.
  Il limite è globale per popup, con ritardo di dieci secondi sul primo errore.
- Verifiche: sette scenari QML, geometrie Util Buttons, parser e argomenti;
  patch applicata al tag, servizio systemd con spazi, azioni native, anteprime
  e fallback al file manager. I test dei nomi sono indipendenti dal focus del
  popup; l'XDG isolato espone solo il socket Hyprland necessario al collaudo.
- Suite della 0.18.7 adattata: **413 casi, 409 superati, 4 saltati**, nessun
  errore, in 215,139 secondi. Log locale
  `/tmp/end4-omdrop-0187-patched-tests.log`. Nessuna radio acquisita dai test.
- Installata copia Git indipendente e fissata in `~/.local/share/omdrop`;
  `~/.local/bin/omdrop` punta a questa copia e il servizio utente esegue il
  relativo ricevitore Python. omdrop-core non installato. Nome e cartella
  `~/Downloads/AirDrop` preservati. Configurazioni TOML radio e demone QCA9377
  collaudato invariati, SHA-256 del demone verificato.
- Configurazione in uso allineata ai tre file del branch (widget, popup e test).
  Nuovo commit locale `242edbeb`; PR bozza aggiornata. Il worktree di revisione
  è pulito; le modifiche preesistenti ai file tracciati sono identiche allo
  snapshot iniziale. Nessun push.
- `omdrop --version`: **omdrop 0.18.7**; `doctor`: **ready**; ricevitore
  inattivo, unità loaded, Quickshell riavviato e barra 1920×68 presente.
  Da confermare sull'iPhone i trasferimenti reali della nuova versione e le
  prove dedicate di una finestra singola e annullamento invio.
- Backup per rollback in `/tmp/end4-omdrop-0187-upgrade/rollback`; il vecchio
  plugin rimane disponibile nella cartella originale. Il backup temporaneo
  non sostituisce il checkout originale conservato.

## Diagnosi dopo la prima prova della 0.18.7

- Segnalato dall’utente: PC vede iPhone, iPhone non vede PC, nessun trasferimento.
- Log del 30 ottobre 10:46–10:48: ricevitore avviato e in ascolto su 8771;
  nessuna richiesta HTTP registrata. Owly riceve action e dati remoti, senza
  frame malformati; gli annunci mDNS risultano inviati senza errori locali.
  Questo non dimostra che gli annunci siano arrivati all’iPhone.
- Demone ancora quello corretto QCA9377, con OWLY_RX_MGMT=1. Doctor ready;
  ricevitore spento al momento della diagnosi. Nessuna modifica al sistema.
- La rete corrente è tornata a essere l’hotspot dello stesso iPhone, confermato
  dall’utente. La precedente prova riuscita usava invece un Wi-Fi normale.
  Apple richiede di scollegare Hotspot personale per AirDrop:
  https://support.apple.com/en-gb/119857 . Non è ancora provato che l’hotspot
  fosse acceso anche durante il tentativo fallito.
- Prossima verifica necessaria: disattivare esplicitamente Hotspot personale
  sull’iPhone prima di riaprire AirDrop nel widget e riprovare offline nei due
  versi, poi riattivare l’hotspot. Non serve Internet per il trasferimento.
  Se fallisce anche così, confrontare lo stesso scenario con la 0.16.1
  conservata; non dichiarare risolta o confermata una regressione prima della prova.

### Esito della riprova senza hotspot

- L’utente conferma: «okay si adesso funziona» dopo le istruzioni di
  disattivare Hotspot personale prima di attivare AirDrop nel widget.
- La 0.18.7 funziona nella riprova: il problema segnalato non richiede al
  momento un rollback. Il risultato è coerente con l’incompatibilità con
  l’hotspot attivo dello stesso iPhone; non è stata necessaria una modifica
  al codice o alla configurazione radio.
- La conferma non specifica separatamente ricezione e invio; non attribuire
  due nuovi collaudi distinti o prove di annullamento/finestra singola.

## Popup AirDrop: modifica nome, focus e stile

- Il campo del nome conservava un binding allo stato aggiornato periodicamente;
  ora la bozza viene sincronizzata solo quando non modificata o confermata dal
  backend. Conservata anche dopo perdita di focus, chiusura/riapertura o errore
  di salvataggio. Salva e Invio passano lo stesso argomento letterale alla CLI;
  limite allineato ai 63 caratteri del backend.
- Finestra PanelWindow overlay con WlrKeyboardFocus.OnDemand, indipendente dal
  focus della barra; HyprlandFocusGrab chiude al clic esterno. La finestra resta
  caricata per evitare distruzione della superficie nei callback del focus.
- Aspetto ripreso da StyledPopup/Bluetooth/Battery: ombra condivisa, margine
  esterno elevationMargin, raggio normal+4, contenuto a 8 px e sezioni con
  colSurfaceContainerLow. Badge AirDrop e intestazioni coerenti; menu durata
  con spazio sufficiente per la freccia, nessuna nuova dipendenza.
- Test ripetibile aggiornato: python3 tests/omdrop-ui-check.py --smoke --visible;
  otto scenari superati, incluso editing con polling, perdita di focus,
  riapertura, salvataggio, rifiuto e nome vuoto. CLI simulata, nessuna radio.
- Verifica separata con input Wayland reali sulla finestra dimostrativa: clic
  nel campo, selezione/digitazione via wtype, conservazione durante polling,
  clic Salva, scelta One file nel menu, clic esterno con chiusura confermata.
  Log locale /tmp/end4-airdrop-popup-fix/native.log; screenshot limitato al
  popup /tmp/end4-airdrop-popup-fix/popup.png. Nessuna preferenza AirDrop reale
  modificata dai test. Adattata soltanto la scala del mouse virtuale locale.
- Tutti i file tracciati preesistenti estranei al lavoro hanno ancora gli hash
  dello snapshot precedente. Fixture temporanea e bytecode del test rimossi.

- Commit locale sul branch feat/airdrop: 8114e99, limitato a popup, test e
  docs/airdrop.md. Bozza PR locale aggiornata; nessun push.
- Quickshell riavviato con successo: istanza qa8v1kztpnt, barra 1920×68
  presente. Ricevitore off prima e dopo il riavvio; nessuna attivazione radio.
  Popup e test della configurazione in uso identici ai file del branch.

## Avvio misura delle prestazioni

- Preparato ZIP non compresso con 8 MiB di dati casuali, dimensione effettiva
  8.388.736 byte, SHA-256 ac2dbab130dd40c255993de77b844273f6871693fa18b8a051afe5a49be85b67,
  in /tmp/end4-airdrop-speed/airdrop-speed-8MiB.zip.
- Script locale tools/airdrop/bench-speed.sh: riceve nome iPhone come argomento
  letterale, attende Invio prima della radio, verifica finestra inizialmente off,
  apre una finestra di dieci minuti, registra invio verbose e durata totale,
  aspetta il ritorno dello stesso ZIP e salva journal ricevitore/statistiche Owly.
  Spegne la propria finestra anche in errore e propone riconnessione al profilo
  iniziale dopo che l’utente ha riattivato hotspot. Nessun canale/driver cambiato.
- Self-check tools/airdrop/bench-speed-check.py superato: nome/percorso con spazi
  e metacaratteri, guardia finestra già attiva, cleanup dopo avvio fallito.
  Solo stub, nessuna radio. Usato time integrato Bash, senza nuove dipendenze.
- Utente disponibile alla prova; aperto terminale «AirDrop - prova velocità».
  Non eseguite misure automaticamente: il flusso richiede interazione iPhone.
  File di benchmark e log restano locali; nessun lavoro PR o commit aggiunto.

### Benchmark: primo tentativo non valido e correzione

- Run /tmp/end4-airdrop-speed/run-4dBO93SO: nessun dato di prova trasferito.
  Il comando termina in 0,995 s prima della ricerca/invio; questo valore non
  misura la velocità AirDrop. Ricevitore fermato prima del log serving.
- Causa precisa nello script di collaudo: umask 077 globale ereditata dal
  root helper Owly, che crea i file di stato con mode 0644 soggetta alla umask.
  I file diventavano 0600; la CLI non privilegiata non poteva leggere
  supervisor/lease e riportava erroneamente radio off. Dopo cleanup,
  reason e announce.log sono ancora 0600 e cat reason dà Permission denied.
  La sorgente RunDir::write usa sostituzione atomica: il prossimo start
  con umask corretta ricrea lo stato con i permessi previsti.
- Script corretto con umask 022; i log restano protetti dalla directory
  mktemp 0700. Nessuna modifica ai permessi di identità/chiavi o driver.
- Aggiunta attesa esplicita fino a 30 s di receiving=true, visible=true e
  listener TCP 8771, prima di inviare. In caso di avvio incompleto conserva
  i log, pulisce la propria finestra e propone comunque la riconnessione.
- Self-check aggiornato: parte ereditando umask 077 e verifica quella corretta
  nei comandi, privacy delle directory, attesa con visibilità ritardata,
  argomenti letterali, finestra già attiva e cleanup su avvio fallito.
  Tutte le prove superate con stub, senza radio. Stato reale dopo il primo
  tentativo: ricevitore off e hotspot riconnesso.

### Prima misura valida: invio molto più lento della ricezione

- Run /tmp/end4-airdrop-speed/run-DLSHNoUE. ZIP di 8.388.736 byte inviato
  PC→iPhone con risposta /Upload 200: 188,74 s, 44,45 kB/s (0,0424 MiB/s).
  Comando complessivo 196,194 s; Discover diretto 0,22 s; Ask 3,14 s.
  La fase Upload include preparazione archivio e risposta HTTP finale;
  non misura la velocità PHY. DVZip appena 627 byte oltre lo ZIP originale.
- Due Upload iPhone→PC: 26,291 s e 26,522 s dall’inizio lettura fino a stored,
  rispettivamente circa 319,1 e 316,3 kB/s. Lettura corpo 26,228 e 26,470 s;
  decodifica/salvataggio successivi soltanto 0,063 e 0,052 s.
- Entrambe le copie ricevute hanno dimensione e SHA-256 identici al file
  originale. Il PC invia circa 7,15 volte più lentamente di quanto riceva.
  Non attribuire i secondi di attesa tra due azioni dell’utente alla rete.
- Statistiche Owly: zero radio full/gave up, malformed, no_peer, queue,
  expired e no_overlap nelle righe registrate. Questi contatori non escludono
  perdite over-the-air o ritrasmissioni TCP: il pcap/TCP non è stato acquisito.
- Config corrente e sorgenti indicano canale 6 fisso, tx_rate non impostato
  (richiesta predefinita 12 Mbit/s), no_ack=true per Presence::Fixed,
  tx_amsdu=false. Sono impostazioni richieste dal backend, non misure della
  velocità fisica realmente usata dalla scheda. Nessun parametro modificato.
- Ipotesi da verificare: trasmissione PC/radio/TCP (perdite/ritrasmissioni,
  finestre TCP e disponibilità AWDL). I log attuali non isolano la causa.
  Prossima misura utile: campionamento ss -tin durante lo stesso invio,
  prima di cambiare rate, ACK o aggregazione uno alla volta.
- Ricevitore off e hotspot riconnesso dopo il test. Risultati numerici
  salvati in results.json nella directory del run. Chiesto all’utente se
  i due invii di ritorno fossero manuali o una ripetizione del telefono.

- L’utente conferma di aver avviato manualmente entrambi gli invii iPhone→PC: le due copie non dimostrano un retry automatico.

## Seconda misura: statistiche TCP durante l’invio

- Aggiunto campionamento ss -tin ogni 500 ms nel benchmark, limitato alle porte
  AirDrop 8770/8771, con timestamp e log privato tcp.log nella directory del run.
  Legge solo statistiche socket; niente payload, nuove dipendenze o parametri
  radio modificati. Il monitor viene terminato e atteso nel cleanup prima
  di fermare la finestra; una durata massima di 1200 campioni copre dieci minuti.
- Modalità --tcp: stesso ZIP 8 MiB e stesso invio, senza richiedere il ritorno
  dall’iPhone. L’utente accetta lo ZIP e segue il ripristino dell’hotspot.
- Self-check superato: stato ritardato, umask, argomenti letterali, guardia
  finestra attiva, start fallito, presenza dei campioni, terminazione del
  monitor e assenza del prompt di ritorno in modalità --tcp. Solo stub.
- Verificata la sintassi reale del filtro ss in sola lettura e lo stato
  ricevitore off/Wi-Fi collegato. Nuova prova preparata per attivazione solo
  dopo Invio nel terminale guidato. Nessuna misura TCP ancora disponibile.

### Seconda misura: evidenza TCP e candidato per prova ACK

- Run /tmp/end4-airdrop-speed/run-nfdVRxei: Upload 8 MiB riuscito in 159,33 s,
  52,65 kB/s; comando totale 180,997 s, Discover diretto 0,96 s e Ask 2,07 s.
- Connessione principale, ultimo campione: almeno 659 segmenti ritrasmessi,
  905.581 byte ritrasmessi su 9.329.576 inviati (9,71%, non packet loss fisico).
  78 DSACK duplicati: possibili anche ritrasmissioni spurie/riordinamento.
- 308 campioni oltre 10 kB inviati: cwnd mediana 5 segmenti (min 1, max 23),
  RTT stimato mediano 56,47 ms (max campionato 975,71 ms), RTO mediano
  663,33 ms (max 4173,33 ms), Send-Q mediana 91.169 byte.
- Dati in attesa lato mittente mentre TCP mantiene spesso pochi segmenti
  in volo: pista radio/ACK/ritrasmissioni confermata come area di indagine,
  senza prova che la singola causa sia no-ACK o una perdita fisica specifica.
- Il backend su canale fisso usa no_ack=true se non sovrascritto. Preparato
  soltanto candidato drivers-ack-candidate.toml nel run: differisce dal profilo
  corrente unicamente per tx_noack=false, verificato con tomllib/assert.
  Non installato. Per provarlo servirà riavviare owlyd, che legge configurazione
  e quirks alla costruzione del backend, poi ripristinare il profilo originale.
- Report analysis.md e tcp-summary.json nella directory del run, senza nomi
  personali o endpoint nel report. Nessun driver/canale/config modificato;
  ricevitore off e hotspot collegato dopo la prova. Nessuna PR o commit.

## Prova temporanea con ACK radio

- Script locale tools/airdrop/bench-ack.py prepara il solo tx_noack=false
  sotto drivers.ath10k_pci. Verifica con tomllib che nessun altro parametro
  cambi. CLI e stato D-Bus devono essere off/idle prima delle modifiche.
- Il backup originale e il candidato sono salvati in directory privata
  persistente tools/airdrop/benchmarks/ack-* insieme a restore.sh e phase.
  Non usa solo /tmp per il ripristino. Ogni applicazione usa install su file
  di staging nella stessa /etc/owly e mv atomico, poi restart di owlyd.
- Attende Invio e sudo prima di applicare; avvia poi il benchmark --tcp
  esistente che attende di nuovo l’utente prima della radio. Variante del run
  marcata tx_noack=false. Nessun cambiamento a canale 6, rate o aggregazione.
- Alla fine arresta il proprio benchmark, ferma la finestra, ripristina il
  profilo originale e riavvia il demone; controlla profilo e radio.toml.
  Se trova modifiche esterne al profilo le conserva e segnala il backup.
  SIGINT/TERM/HUP normali entrano nel cleanup; restore.sh resta disponibile
  per interruzioni che non consentono l’esecuzione del cleanup.
- Check isolato tools/airdrop/bench-ack-check.py: candidato, applicazione atomica,
  successo/fallimento benchmark, interruzione, restart fallito, profilo
  modificato esternamente e radio già attiva. Tutti passati con mock.
  Anche self-check del benchmark con statistiche TCP e sintassi Bash passati.
- Stato iniziale reale: radio idle, ricevitore off, hotspot collegato;
  demone QCA9377 corretto con OWLY_RX_MGMT=1. Serve password sudo nel terminale.
  Il solo preparare/aprire il collaudo non modifica ancora /etc/owly.

### Esito ACK e nome del dispositivo per i prossimi collaudi

- Run /tmp/end4-airdrop-speed/run-zPMTwzVO, variante tx_noack=false:
  Upload riuscito dello stesso ZIP di 8.388.736 byte in 173,01 s, 48,49 kB/s.
  Ultimo campione TCP: 774 segmenti ritrasmessi, 1.064.676 byte ritrasmessi
  su 9.488.671 inviati (11,22%, non perdita fisica misurata); 83 DSACK.
  cwnd mediana 5, RTT mediano 52,28 ms e Send-Q mediana 159.572 byte.
- Confronto con il run precedente: 159,33 s, 52,65 kB/s, 659 ritrasmissioni
  e 9,71% dei byte inviati ritrasmessi. Nessun miglioramento osservato con ACK.
  Una sola coppia di prove non dimostra una regressione causale: la prima
  baseline era durata 188,74 s. Non mantenere la modifica in modo permanente.
- Ripristino completato: backup locale benchmarks/ack-ie6159wz, phase=restored,
  result=0; /etc/owly/drivers.toml identico al backup originale, owlyd attivo
  con il binario QCA9377 e OWLY_RX_MGMT=1. Ricevitore off, Wi-Fi riconnesso.
  comparison-summary.json conservato nelle directory dei due run confrontati.
- Nome iPhone salvato su richiesta in tools/airdrop/benchmarks/device-name,
  file locale con permessi 0600. Il benchmark lo propone come destinatario:
  Invio conferma, un nome digitato lo sostituisce per quella prova.
  Il self-check verifica sia il default salvato sia l'override letterale.
  Il dato personale e i risultati grezzi restano fuori dalla proposta di PR.
- Prossima pista: verificare rate di trasmissione richiesto e aggregazione,
  prima di preparare un altro esperimento con un solo parametro e rollback.
  Nessuna nuova impostazione radio applicata dopo il ripristino.

## Prossima prova: A-MSDU in trasmissione

- Dalla lettura del backend 0.4.1: aggregation/rx_ampdu riguarda l'accettazione
  della sessione Block Ack del telefono; tx_amsdu abilita invece il batching
  dell'unicast PC→iPhone quando il peer annuncia capacità HT. La dimensione
  dei gruppi resta limitata dalle capacità del peer e dalla MTU del monitor.
  Il contatore STATS tx_amsdu permette di distinguere l'opzione abilitata
  dall'effettivo utilizzo. Un esito nullo non dimostra da solo un limite RF.
- Il rate richiesto dal backend è 12 Mbit/s per default, senza adattamento
  al risultato dei singoli invii. ath10k dichiara HAS_RATE_CONTROL; il rate
  richiesto tramite radiotap non va scambiato per una misura over-the-air.
  La documentazione del driver segnala anche limiti nei rate riportati:
  https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath10k.html
  Sorgente consultato per la famiglia di kernel 6.18:
  https://github.com/torvalds/linux/blob/v6.18/drivers/net/wireless/ath/ath10k/mac.c
- Riutilizzato bench-ack.py con --amsdu, senza un secondo orchestratore:
  modifica soltanto tx_amsdu=true in /etc/owly/radio.toml, lasciando intatti
  drivers.toml, canale 6, no-ACK predefinito e rate. Backup privato persistente
  benchmarks/amsdu-*, installazione atomica, riavvio su radio idle e ripristino
  automatico del file originale; restore.sh per il recupero manuale.
- Self-check dell'orchestratore passato per entrambe le varianti: candidato,
  override già presente, installazione atomica, successo/fallimento benchmark,
  interruzione, restart fallito, modifiche esterne e radio occupata.
  Passato anche il check benchmark (nome salvato/override, spazi, umask,
  attesa radio, statistiche TCP e cleanup). Nessuna radio usata nei check.
- Stato prima dell'apertura: ricevitore off, Owly idle con patch QCA9377,
  Wi-Fi collegato. La nuova prova aspetta Invio e autenticazione nel terminale;
  segue lo stesso ZIP 8 MiB e richiede hotspot spento. Confronto ancora da fare.
  Config iniziale SHA-256 radio.toml:
  dc35804f22de653140b1c2563b5bc81a69008f24c2f0039d8f3124299e9dfb22;
  drivers.toml: b9278a9a3d426d601e1bbfc4044296eba871604625143d6a367430eb4de5f18f.

### Esito A-MSDU: trasferimento incompleto e timeout

- Run /tmp/end4-airdrop-speed/run-AUZjmAXH, variante tx_amsdu=true.
  Discover/Ask riusciti; Upload iniziato alle 13:11:12,976 e fallito alle
  13:19:46,257 con TimeoutError('The write operation timed out'), esito 4.
  Tentativo Upload 513,281 s; comando complessivo 525,791 s. Nessun Upload 200:
  non classificare il trasferimento come riuscito né calcolare throughput
  sul file completo. L'utente conferma l'attesa eccessiva osservata sull'iPhone.
- Il batching era effettivo: STATS tx_amsdu arriva a 214. Nessun errore MTU
  nei log, né incrementi nei contatori radio full/gave up e drop del backend.
  Questo non prova che ogni aggregato sia stato trasmesso o ricevuto via radio.
- Ultimo campione TCP: 4.899.891 byte confermati, valore fermo per circa
  89,7 s finali; 846 segmenti ritrasmessi, 1.161.669 byte ritrasmessi su
  6.067.071 inviati (19,15%, non misura di packet loss RF); cwnd mediana 2.
  Evidenza di rallentamento e stallo con questa variante; non identifica
  da sola il difetto in driver/firmware, costruzione frame o ricevitore.
  analysis-summary.json conserva il riepilogo numerico nella directory del run.
- Ripristino verificato: benchmarks/amsdu-9wy57hsk phase=restored, result=4;
  radio.toml identico al backup originale e tx_amsdu nuovamente assente.
  owlyd attivo dal 30 ottobre 2026 alle 13:22:46 CET con binario QCA9377
  e OWLY_RX_MGMT=1; radio idle, ricevitore off, Wi-Fi collegato, benchmark finito.
  A-MSDU rimane disabilitato nella configurazione locale.
- Limitato l'invio del solo benchmark con timeout di GNU coreutils: 240 s
  complessivi (inclusa ricerca/accettazione), TERM seguito da KILL dopo 5 s
  se necessario. OMDROP_BENCH_SEND_TIMEOUT consente una durata diversa.
  Esito 124 segnalato esplicitamente; segue lo stesso cleanup/ripristino.
  Check passato con invio simulato oltre la scadenza, verifica del codice 124,
  arresto campionatore e CLI off, più i precedenti casi del benchmark e i
  check ACK/A-MSDU. Nessun limite aggiunto al normale invio del widget.
- Per proseguire serve misurare il comportamento effettivo della trasmissione
  ath10k, mantenendo la configurazione base: il solo rate chiesto in radiotap
  non basta a dimostrare il rate fisico. Nessun altro collaudo radio avviato.

## Sequenza canali iPhone: osservazione passiva durante l'invio

- L'utente ora dispone di Wi-Fi fisso. PC collegato sul canale 100, Owly
  idle; configurazione AirDrop ancora exclusive sul 6, senza ACK sperimentali
  o A-MSDU. La rete fissa consente la riconnessione senza riaccendere hotspot;
  il Wi-Fi del PC viene comunque sospeso durante la sessione AirDrop.
- Riletto il vecchio diagnosis/mgmt-register-six.log: l'indirizzo dell'iPhone
  coincide con quello degli invii riusciti. 296 annunci riportano un solo
  slot sul canale 6 su 16; altri 34 ne riportano due e 21 tre. Sono annunci
  della prova precedente, non una misura corrente né la percentuale reale
  del tempo radio. Non mediare i conteggi di frame come se fossero tempo:
  una cattura sul solo 6 campiona la sequenza in modo condizionato.
- Aggiunto tools/airdrop/bench-channels.py: crea un monitor software nlmon
  temporaneo con ip, osserva i messaggi FRAME che il kernel consegna già
  a Owly e conserva solo metadati degli annunci AWDL (sequenza completa,
  slot sul 6, timestamp di osservazione, canale ricevuto, RSSI quando presente).
  Niente seconda registrazione dei frame che interferisca con Owly, nessuna
  ricompilazione o modifica del backend, niente contenuti dei file salvati.
- Il bootstrap Python isolato apre il socket e abbandona gruppi/GID/UID
  prima di caricare il decoder dal repository. Il decoder verifica lunghezze
  Netlink/TLV, OUI/versione/subtype e le tre codifiche della sequenza;
  log sotto mkdtemp privato, durata massima osservazione 15 minuti per coprire
  i prompt e l'invio. Il programma rimuove il monitor dopo il benchmark,
  anche in caso di errore/interruzione; un benchmark interrotto viene fermato
  e chiusa la propria sessione AirDrop. Non modifica radio.toml/drivers.toml.
- Riutilizzato bench-speed.sh --tcp con destinatario salvato, stesso ZIP
  8 MiB e limite invio 240 s. Modalità Wi-Fi fisso riconnette automaticamente
  l'UUID della rete iniziale; il terminale si ferma soltanto dopo la pulizia
  dell'osservatore. channel-capture.path collega i log TCP alla cattura.
- Check offline passato: tutte le codifiche, slot/frazione annunciata,
  messaggi concatenati, troncamenti, traffico estraneo, directory private,
  avvio fallito, cattura fallita, benchmark fallito, radio occupata e
  interruzione con rimozione monitor/arresto benchmark. Decoder verificato
  anche sui vecchi frame reali. Check benchmark passato, incluso Wi-Fi fisso.
- Il collaudo reale nlmon attende autenticazione sudo nel terminale: il
  ticket precedente è scaduto. La sequenza corrente durante il trasferimento
  non è ancora acquisita; nessuna nuova conclusione sullo stallo.

### Correzione del terminale del collaudo canali

- Il primo tentativo channels-g5u27676/run-uQx30cZk si è fermato al prompt
  del nome: testo a scaletta e Invio inefficace. Ricevitore rimasto off,
  nessun trasferimento né annuncio raccolto. All'ispezione i processi erano
  terminati e restava soltanto l'interfaccia software odcap3399206.
- Il collector sudo in background ereditava stdin e la sessione del terminale:
  ciò permetteva al processo sudo di interferire con la disciplina del TTY
  mentre il benchmark attendeva input. Corretto lo spawn con stdin=DEVNULL
  e start_new_session=True; il benchmark mantiene il normale terminale.
- Self-check eseguito anche in un vero PTY tramite script(1): un processo
  reale avviato con le opzioni usate dal collector conferma sia stdin non TTY
  sia assenza di terminale controllante (/dev/tty non accessibile).
  Passati anche i check precedenti di parser, cleanup e benchmark.
- Predisposto riavvio guidato con stty sane e rimozione del solo monitor
  residuo identificato, dopo autenticazione sudo nel nuovo terminale.
  Config radio e driver invariati; nessuna misura di canali ancora ottenuta
  durante il nuovo trasferimento.

### Autenticazione del collector e precontrollo prima della radio

- Il tentativo successivo channels-hvzacwzb è fallito prima del benchmark:
  capture.log contiene "sudo: a password is required". start_new_session
  applicato a sudo lo separava anche dal terminale autenticato. Nessun invio
  tentato, nessuna nuova directory run, zero annunci. Verificati radio idle,
  ricevitore off, rete fissa collegata e assenza di monitor nlmon residui.
- Avvio corretto: sudo rimane nella sessione originale per il solo bootstrap
  sincrono. Dopo apertura del socket e abbandono di gruppi/GID/UID, il bootstrap
  avvia un lettore separato passando esplicitamente il descrittore del socket.
  Il lettore ha stdin=/dev/null, una sessione propria e file di log aperti
  autonomamente come utente. sudo termina prima di mostrare i prompt del test.
- Prima del trasferimento, iw dev genera una richiesta Netlink di sola lettura;
  la prova deve osservarne un messaggio valido entro tre secondi. In caso
  contrario pulisce e termina prima di attivare AirDrop. Il PID pronto e i
  marker seen/done consentono arresto e verifica del lettore separato.
- Self-check ampliato: passaggio effettivo di un socket Unix tra processi,
  bootstrap terminato mentre il lettore riceve, decodifica di un annuncio
  sintetico e arresto reale. Passato sia normalmente sia dentro un PTY,
  fuori dalla sandbox che blocca la ricostruzione del socket da descrittore.
  Passati anche parser, fallimenti simulati, cleanup e benchmark.
- La prova con autenticazione sudo e monitor kernel reali richiede ancora
  l'avvio dal terminale; i check locali non sostituiscono questa verifica.
  radio.toml e drivers.toml rimangono identici alle copie funzionanti.

### Risultato acquisizione canali riuscita

- Cattura /tmp/end4-airdrop-speed/channels-t00sqqx6, collegata al benchmark
  run-FvByHWHn. Precontrollo reale superato; 6313 datagrammi osservati,
  276 annunci AWDL tutti del destinatario identificato nel send.log.
  12 messaggi Netlink scartati/troncati: non sono una misura di packet loss.
- Upload dello ZIP da 8.388.736 byte completato con risposta 200: 111,08 s,
  75,52 kB/s; comando totale 117,809 s. Migliore delle precedenti baseline
  da 159,33/188,74 s, ma ambiente Wi-Fi cambiato e nessuna ottimizzazione
  applicata: una singola prova non consente attribuzioni causali.
- Prima dell'Upload osservati annunci con 1, 2, 3 e 5 slot sul canale 6.
  Durante l'Upload (15:06:55,254–15:08:45,706 CET): 172 annunci, di cui
  168 con sequenza [44,44,44,44,44,44,44,44,6,6,44,6,6,6,44,44];
  gli altri quattro con due slot sul 6. Il PC resta fisso sul 6.
- La sequenza prevalente dichiara 5/16 sul 6 (31,25%) e 11/16 sul 44
  (68,75%); non trasmissione simultanea. Periodo annunciato 16 TU per AW,
  quattro AW per slot: slot nominale 65,536 ms, ciclo 1048,576 ms.
  Dieci slot consecutivi sul 44 attraverso il confine del ciclo formano
  un intervallo nominale di 655,36 ms fuori dal 6. master_channel resta 6:
  quel campo non rappresenta il canale che occupa più slot.
- Le percentuali derivano dal contenuto della sequenza, non dai conteggi
  degli annunci. La cattura sul solo 6 non misura l'effettivo airtime RF
  sugli altri canali. L'alternanza limita le opportunità sul 6, senza
  isolare la causa delle ritrasmissioni o dello stallo della prova A-MSDU.
- RSSI annunci durante Upload: mediana -26 dBm, estremi -34/-23 dBm.
  213 campioni TCP: cwnd mediana 8; ultimo campione 416 segmenti ritrasmessi,
  570.901 byte ritrasmessi su 8.994.896 inviati (6,35%, non perdita fisica),
  46 DSACK duplicati. Report channel-analysis.md e channel-analysis.json
  conservati nel run, con controlli di coerenza sui dati e sulle durate nominali.
- Cleanup verificato: ready.done presente, nessun nlmon residuo né benchmark
  attivo, radio idle, ricevitore off, owlyd attivo con OWLY_RX_MGMT=1,
  Wi-Fi fisso riconnesso. Entrambi gli hash dei profili coincidono con
  quelli iniziali. Nessuna modifica alla configurazione hardware.
- Verifica normativa in sola lettura: dominio globale IT ma phy#0 ancora
  99 con PASSIVE-SCAN e canale 44 marcato no IR; anche 149 no IR. La rete
  attuale è sul 100. Non basta impostare channels=[44] per superare il
  vincolo del driver/firmware. Valutare il 44 in condizioni consentite,
  eventualmente con associazione a un AP su quel canale; nessun nuovo
  cambio di canale o collaudo attivato automaticamente.

## Rete Starlink e prossima verifica TCP

- L'utente conferma router Starlink di terza generazione. 5 GHz è la banda;
  PC sul canale 100, mentre gli annunci AirDrop dell'iPhone usano soprattutto
  il 44 e in parte il 6. La documentazione delle impostazioni Starlink non
  elenca la selezione manuale del canale: non richiedere modifiche al router
  né considerare la separazione 2,4/5 GHz equivalente alla scelta del 44.
  https://starlink.com/au/support/article/f9a1d602-9204-e70c-a780-f2619d99f9c7
- Le reti già note sul PC sono sul 100 e sul 36, nessuna sul 44. Il backend
  shared accetta solo AP sul 6/44/149, quindi non basta cambiare mode sul
  Wi-Fi attuale. Inoltre la patch QCA9377 apre il management socket su
  owlyibss0: un futuro shared richiede prima di adattare e verificare quel
  percorso, perché shared non crea tale interfaccia. Nessun cambio applicato.
- Analisi run-FvByHWHn: RTO TCP mediano 886,666 ms, minimo 210 ms, massimo
  3223,33 ms; 72/213 campioni hanno RTO sotto il gap annunciato di 655,36 ms,
  26 mostrano backoff, osservati 44 incrementi del contatore DSACK. Nella
  precedente baseline run-nfdVRxei: RTO mediano 663,333 ms e 153/308 sotto
  quel gap. Sono indizi per provare il timer, non prova che ogni ritrasmissione
  sia spuria o che il gap effettivo via radio sia identico a quello annunciato.
- Preparata variante tools/airdrop/bench-channels.py --rto-min: stesso
  benchmark e cattura, canale 6/profilo radio invariati, RTO minimo 1000 ms
  limitato al traffico link-local su awdl0. Aggiunge una route fe80::/64
  sulla stessa interfaccia con metric 1, lasciando la route kernel originale
  metric 256 intatta. La rimuove nel cleanup; anche la chiusura di awdl0
  elimina le route della sessione. Nessuna modifica a sysctl globali o file
  /etc/owly. Prima, applicazione e ripristino salvati in rto-*.json.
- Applicazione verificata leggendo il valore dal kernel prima dell'invio:
  se non vale 1000 o il comando fallisce, nessun send; pulizia e riconnessione.
  Benchmark e collector restano protetti dal limite invio 240 s e dal
  precontrollo Netlink già collaudato. Il valore RTO effettivo nei socket va
  ancora confrontato nel nuovo tcp.log, insieme alla sequenza del telefono.
- Check kernel reale superato con unshare --user --map-root-user --net,
  interfaccia dummy awdl0 e indirizzo fe80::1/64: route originale metric256,
  aggiunta metric1 con metrics.rto_min=1000, eliminazione e ritorno alla sola
  originale. Nessuna radio/rete reale usata. Check benchmark passato con
  applicazione, readback, rimozione, add fallito e readback errato; passati
  anche controlli collector/socket e passaggio della nuova variante.
- Questa è una prova diagnostica: un timer più lungo può rallentare il
  recupero di perdite reali. Valutare il risultato, non renderlo permanente
  sulla base dell'ipotesi. Nessuna PR, commit o cambio router richiesto.

### Esito RTO e necessità di un confronto con posizione fissa

- Run run-Q5jFov6E, cattura channels-_f_31tvh: Upload 200 dello stesso ZIP
  in 156,19 s (53,71 kB/s), contro 111,08 s (75,52 kB/s) del run-FvByHWHn.
  Route applicata con rto_min=1000; RTO minimo nei socket 1013,33 ms,
  mediano 1070 ms: parametro effettivamente utilizzato.
- Ultimo campione: 579 segmenti ritrasmessi, 793.984 byte su 9.217.979 inviati
  (8,61%), cwnd mediana 5; contro 416 segmenti, 6,35% e cwnd mediana 8.
  Campioni con backoff 1/302 contro 26/213; DSACK duplicati finali 3 contro 46.
  Non equiparare questi contatori a una misura completa di perdite o
  ritrasmissioni spurie. Nessun vantaggio di velocità misurato nella coppia.
- Sequenza prevalente identica: 5/16 sul 6 e 11/16 sul 44, presente in
  292/301 annunci durante Upload; gli altri nove annunci hanno due slot sul 6.
  RSSI mediano passato da -26 a -42 dBm. L'utente conferma di aver spostato
  o tenuto diversamente il telefono: il confronto non isola l'effetto RTO.
  Il solo RSSI diverso non dimostra la causa del rallentamento.
- Cleanup verificato: rto-before.json e rto-restored.json identici; nessuna
  awdl0 né nlmon residua, radio idle, ricevitore off, Owly attivo con
  OWLY_RX_MGMT=1 e rete fissa riconnessa. Hash radio/driver originali invariati.
  rto-analysis.md e rto-comparison-summary.json conservati nelle directory run.
- Preparato confronto locale /tmp/end4-airdrop-speed/compare-iedgbowi:
  due invii consecutivi baseline e RTO, con cattura in entrambi e iPhone
  appoggiato nello stesso punto/orientamento, accettando senza sollevarlo.
  Le sottocartelle baseline/rto puntano allo stesso ZIP originale, SHA-256
  verificato; limite quattro minuti per invio. Si ferma se la prima prova
  fallisce; nessuna modifica permanente. Riconnessione del Wi-Fi tra le prove.
- Launcher locale /tmp/end4-airdrop-compare.sh, sintassi Bash verificata;
  collector riutilizzato con OMDROP_BENCH_NO_PAUSE=1 per passare alla seconda
  prova dopo il cleanup, senza il prompt intermedio di chiusura. Nessuna
  modifica alla logica radio/TCP rispetto al collaudo appena completato.

- Su richiesta dell'utente, confronto compare-iedgbowi escluso (excluded.json):
  prima fase run-XXf25fZR terminata con timeout Ask, nessun Upload; seconda
  fase non partita. Cleanup completato, radio off e Wi-Fi riconnesso.
  Ripartenza predisposta in compare-979eyr7q con log nuovi, stesso ZIP verificato
  e stesso ordine baseline/RTO. Launcher /tmp/end4-airdrop-compare-retry.sh,
  sintassi controllata; nessun cambiamento ai parametri del confronto.

### Correzione dei file del confronto: collegamenti non validi per il benchmark

- compare-979eyr7q escluso (excluded.json): entrambe le chiamate Upload hanno
  restituito 200 in circa un secondo, ma il mittente ha inviato soltanto
  116 byte DVZip / 232 byte CPIO. I file nelle cartelle di fase erano symlink:
  libarchive.add_files li archivia come collegamenti, mentre il log nominale
  usa os.path.getsize e mostra la dimensione del target. Nessun risultato
  di velocità valido da questi invii; errore nella preparazione del collaudo.
- Corretto bench-speed.sh: accetta soltanto un file reale leggibile,
  rifiutando symlink prima di chiamare la CLI. Aggiunta verifica nel self-check
  che un collegamento non provochi neppure una chiamata alla radio.
- Aggiunto bench-archive-check.py: esegue in isolamento solo encoder e metodo
  send_upload del mittente installato, con post sostituito da ricezione locale
  in memoria. Decodifica DVZip/CPIO e verifica membro regolare e contenuto
  identico; prova negativa sul symlink. Nessuna scoperta o socket radio.
- Nuovo confronto compare-c9z31ro4: due copie regolari con shutil.copyfile,
  permessi 0600 e SHA-256 identico all'originale. Preflight effettivo di
  entrambe: 8.388.736 byte di dati, 8.388.922 CPIO, 8.389.363 DVZip; contenuto
  e hash verificati. Risultati in archive-preflight.log nella cartella gruppo.
- Passati self-check archivio e benchmark, incluso rifiuto dei link;
  launcher /tmp/end4-airdrop-compare-real-files.sh con sintassi controllata.
  Il confronto continua a richiedere posizione fissa dell'iPhone, normale
  seguito da RTO 1000 ms. Nessun cambiamento a radio, router o timer permanenti.
- Dopo il confronto escluso: ricevitore off, radio idle, nessuna awdl0/nlmon
  residua, Wi-Fi collegato e hash dei due profili originali invariati.

### Confronto valido a posizione fissa: RTO senza guadagno di velocità

- Gruppo compare-c9z31ro4: baseline run-KFQpRjw0 e RTO run-IY5G169S.
  Entrambi Upload 200 con i file reali: 8.388.736 byte, CPIO 8.388.922,
  DVZip 8.389.363 identici ai preflight. Le copie hanno lo stesso SHA-256.
  Tempi Upload 163,57 s / 164,58 s; velocità 51,29 / 50,97 kB/s.
  Differenza +0,62% nel tempo: nessun guadagno misurato per RTO 1000 ms.
- Condizioni osservate comparabili: RSSI mediano -42 dBm in entrambi,
  estremi -50/-37 e -49/-37. Sequenza prevalente uguale, 5/16 sul 6 e
  11/16 sul 44, presente in 305/314 e 304/317 annunci durante Upload.
  RSSI e sequenza annunciata non escludono variazioni RF/interferenze;
  una coppia sequenziale non è una stima statistica della velocità.
- TCP: 750 / 671 segmenti ritrasmessi; byte retrans/sent 10,90% / 9,88%;
  cwnd mediana 5 in entrambi. DSACK duplicati 98 / 1; campioni con backoff
  54/316 / 5/318. RTO minimo effettivo 233,333 / 1016,67 ms e mediano
  573,333 / 1066,67 ms: la variante era realmente applicata, ma ridurre
  questi indicatori non ha aumentato il throughput osservato.
- Decisione: mantenere il profilo normale, nessun timer permanente.
  Route originale ripristinata (JSON prima/dopo identici); monitor conclusi,
  nessuna awdl0/nlmon o processo del test residuo, Owly idle, ricevitore off,
  Wi-Fi riconnesso e hash dei profili originali invariati.
- results.json e analysis.md nel gruppo conservano confronto, controlli di
  coerenza e limiti. Prossima pista: misurare rate effettivo e ritardo nel
  percorso driver/firmware rispetto alle finestre del telefono, evitando
  di assumere che il rate richiesto da radiotap sia quello realmente usato.

### Precontrollo driver prima della prossima misura

- Kernel 6.18.36-1-lts: ATH10K_DEBUGFS e ATH10K_TRACING già abilitati.
  Non sono installati trace-cmd/perf/bpftrace/tcpdump; nessuna dipendenza
  aggiunta. debugfs e tracefs disponibili sul sistema, accessibili a root.
- La FAQ ufficiale ath10k avverte che il rate TX esposto al sistema può
  essere errato: non considerarlo una misura PHY. Gli eventuali tempi
  di completamento driver non equivalgono al timestamp di uscita in radio.
  Fonte: https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath10k/faq.html
- Aggiunto bench-driver-inventory.py: precontrollo in sola lettura,
  raccoglie una volta fw_stats, elenco delle voci debugfs e formati dei
  tracepoint ath10k/TX mac80211. Non abilita eventi, non cambia debug_mask,
  non avvia AirDrop, non sospende il Wi-Fi. Solo il programma letterale
  di lettura viene eseguito con sudo, senza importare codice dal checkout.
- Log sotto /tmp/end4-airdrop-speed/driver-inventory-* in directory 0700;
  nessun dato dei file trasferiti. Password solo nel terminale locale.
  Self-check passato: inventario sintetico, voci mancanti, percorso con
  spazi e verifica che i file letti restino identici. Risultati hardware
  ancora da acquisire; scegliere gli eventi solo dopo questa verifica.

- Precontrollo reale driver-inventory-s1s1da51 completato: un dispositivo,
  38 formati tracepoint, nessun errore, stderr vuoto, directory 0700.
  Presenti ath10k_htt_tx e ath10k_txrx_tx_unref, entrambi con msdu_id:
  consentono di indagare il tempo tra preparazione HTT e completamento
  gestito dal driver. Non sono timestamp RF né prova di consegna iPhone.
- fw_stats disponibile; contatori cumulativi e peer del Wi-Fi normale
  non attribuibili ai precedenti test AirDrop. Rate history VDEV tutte zero.
  Nessuna diagnosi di guasto/perdite ricavabile da questa sola istantanea.
  Tracing globale già su 1 con tracer nop: non è stato modificato.
- Prossima misura definita in analysis.md nella directory inventario:
  solo i due eventi in istanza tracefs dedicata, controllando overflow,
  riuso/ambiguità degli ID e clock. Profilo normale e ZIP reale invariati;
  associare a TCP/annunci AWDL senza confondere completion con airtime.
  Nessuna nuova cattura attivata durante l'analisi del precontrollo.
- Controllo host dopo l'analisi: AirDrop off, Owly attivo con patch RX_MGMT,
  rete fissa connessa, nessuna awdl0/nlmon residua. Salvato analysis.md.

### Prova tempi driver predisposta

- Aggiunto bench-driver.py: copia regolare 0600 dello ZIP in directory
  driver-* privata, con preflight dell'archivio effettivo; poi riutilizza
  bench-channels.py e bench-speed.sh con profilo normale e limite invio 240 s.
- Supervisore sudo letterale, senza importare codice dal repository come
  root: crea un'istanza tracefs nuova, abilita solo ath10k_htt_tx e
  ath10k_txrx_tx_unref, clock mono, buffer 4096 KiB per CPU. Nessun payload.
  Il programma di benchmark parte dopo setgroups/setgid/setuid. Riceve solo
  variabili essenziali della sessione; nessuna copia completa dell'ambiente.
- Prima del benchmark esegue una cattura breve con verifica UID non root;
  verifica rimozione istanza e stato tracing globale invariato. Se fallisce,
  nessuna radio avviata. Una seconda cattura accompagna la sessione guidata;
  cleanup anche su errore, timeout o interruzione ordinaria. Limite intera
  sessione 15 minuti, quindi rerun se si resta lontani dal terminale.
- Trace e statistiche buffer per CPU salvati a fine prova: controllare
  overflow e associazioni ID prima di calcolare latenze. Non misura il
  timestamp RF o la conferma iPhone. Nessun contatore firmware cumulativo
  usato come delta del trasferimento attraverso i cambi di modalità radio.
- Collector AWDL esteso con osservazione monotonic, next_tu, aw_counter e
  campi phy_tx/target_tx, senza cambiare radio o backend. L'istante osservato
  via Netlink include il ritardo di consegna; non è ricezione RF esatta.
- Passati self-check supervisore (privilegi, eventi isolati, cleanup su
  successo/errore avvio/errore invio/timeout, percorsi con spazi) e collector
  con campi temporali sintetici e handoff socket reale non privilegiato.
  Prova hardware da eseguire nel terminale «AirDrop - prova tempi driver».

### Esito prova tempi driver: trasferimento valido e coda lunga di completamenti

- driver-0upbjuk8/run-JRI4nC1C, channels-aix5t892: Upload 200, ZIP reale
  8.388.736 byte in 118,49 s, 70,80 kB/s. Archivio effettivo e SHA originali
  verificati. Il POST/Upload dura 118,18 s; tempo dichiarato include packing.
- Traccia: 24.430 eventi / 12.215 coppie, zero overflow/dropped events su
  tutte le CPU, zero orfani/ID ambigui/TX senza completion o inversioni.
  Durante Upload 11.311 coppie, di cui 6.607 con lunghezza >=1000 byte.
  Pacchetti grandi: mediana 12,059 ms, p95 361,182 ms, p99 726,221 ms,
  massimo 1160,756 ms; 1.323/6.607 oltre uno slot 65,536 ms, 172 oltre
  655,36 ms. Picco osservato 28 ID pendenti nel dispositivo.
- TID 16: 8.459 coppie, mediana 10,954 / p95 249,677 ms; TID 17 management:
  2.852, mediana 2,757 / p95 7,207 ms, max 29,083 ms. La coda lunga riguarda
  soprattutto il percorso dati. Completion host non equivale a airtime
  né a conferma iPhone; mancano esito ACK/discard e rate fisico effettivo.
- TCP: 500 segmenti retrans, 686.069/9.110.064 byte (7,53%); ACKed 8.423.996.
  iPhone: 201 annunci durante Upload, RSSI mediano -42 dBm; 193 con 5/16
  slot sul 6 e 11/16 sul 44, otto con 2/16 sul 6. Netlink 12 datagrammi
  rifiutati/troncati su 6.546: lo zero eventi persi riguarda solo tracefs.
- Più veloce della precedente baseline 163,57 s, ma nessuna ottimizzazione
  applicata: singola osservazione con tracing, non guadagno attribuibile a
  una modifica. Indizio concreto di attese/accodamento/retry nel TX; non
  prova della specifica causa né di trasmissioni RF fuori finestra AWDL.
  Prossima pista: politica ACK effettiva per frame iniettati e gestione code;
  evitare di ripetere il semplice tx_noack toggle già privo di benefici.
- Entrambe le istanze tracefs rimosse, stato globale identico, AirDrop off,
  Owly attivo con RX_MGMT, Wi-Fi fisso riconnesso; niente awdl0/nlmon/processi
  residui. Hash profili radio/driver originali invariati. Nessuna PR/commit.
- Salvati results.json, analysis.md e analyze.py nella directory prova;
  self-check del parser passato (riuso ID valido, rifiuto ambiguità/orfani/
  incompletezza/disordine). Tutti i risultati sintetici riproducibili.

### Verifica ACK: percorso sorgente e acquisizione esiti predisposta

- Sorgenti Linux di riferimento v6.18 conservati in /tmp/end4-airdrop-speed/
  ack-source. Owly scrive F_TX_NOACK (radiotap TX_FLAGS 0x0008) quando no_ack
  è attivo; mac80211/tx.c lo converte in IEEE80211_TX_CTL_NO_ACK.
  Questo prova la richiesta sul lato host, non l'esecuzione nel firmware.
- ath10k marca il normale controllo NOACK per TID configurati su frame QoS;
  i dati Owly ordinari sono non-QoS/TID HTT 16. Non dedurre dal solo TID
  che ACK sia attivo o disattivo. Il completamento ACK può indicare successo
  anche nel percorso no-ACK, come mostra txrx.c: non è prova di ACK RF.
- ath10k_txrx_tx_unref contiene il log HTT «htt tx completion msdu_id N
  status S»: enum interno 0 NONE, 1 ACK, 2 NOACK, 3 DISCARD (htt.h).
  debug.h consente il log quando il tracepoint è attivo anche con debug_mask
  zero; debug.c invia al kernel log soltanto se debug_mask abilita il livello.
- bench-driver.py --completion-status riutilizza il collaudo esistente e
  aggiunge ath10k_log_dbg solo nell'istanza temporanea. Filtro prima di enable:
  level == 8 && msg ~ "htt tx completion msdu_id * status *".
  Nessun dump/header/payload, nessuna modifica a debug_mask. Verificati
  readback filtro, debug_mask e stato/filtri globali prima/dopo.
- Self-check passato in entrambe le modalità: privilegi abbassati prima
  del codice checkout, filtro isolato, cleanup normale/errore/timeout;
  filtro rifiutato impedisce anche l'avvio del processo di benchmark.
  Preflight tracefs reale ripetuto nel terminale prima di attivare radio.
- La prova raccoglie stato firmware per ID e tempi, non conteggio dei retry
  RF né rate PHY effettivo. Il tracepoint debug comporta ulteriore lavoro
  di formattazione nel driver: non attribuire differenze di throughput a
  ottimizzazioni, nessuna ancora applicata. Profilo/rate/timer invariati.
  Nuova acquisizione attende l'utente in «AirDrop - esiti TX firmware».
- Fonti: Linux v6.18 net/mac80211/tx.c e ath10k/{debug.h,debug.c,txrx.c,htt.h};
  filtri nativi documentati in https://docs.kernel.org/trace/events.html.

### Esito acquisizione firmware: NOACK correlati a completamenti lenti

- driver-status-wgc84y81/run-EyqUxCHO, channels-xjmfz1bh: Upload 200,
  ZIP reale e archivio/hash originali verificati, 173,01 s, 48,49 kB/s.
  Traccia 48.039 eventi / 16.013 triplette complete; nessun overflow,
  stato mancante, ID ambiguo/orfano, inversione temporale o pending residuo.
- Durante Upload 13.690 TX: 13.022 successo e 668 NOACK, nessun NONE/DISCARD.
  Tutti i NOACK sono TID16 (dati); 4.162 management TID17 tutti successo.
  Dei 6.860 pacchetti >=1000 byte, 659 (9,61%) con NOACK: mediana 200,903 ms,
  p95 551,501 ms; successo 6.201, mediana 8,828 ms, p95 98,297 ms.
  615/659 NOACK grandi oltre uno slot65,536 ms; anche 510 successi oltre
  uno slot, quindi l'esito NOACK non spiega ogni completamento lento.
- Mediana grandi complessiva 10,044 ms, p95 214,079 ms, max 1004,458 ms;
  picco20 ID pendenti. Tra messaggio stato e unref max146 microsecondi:
  la sola porzione host dopo il messaggio non spiega i ritardi centinaia ms.
  Non misurati numero retry RF, esatto airtime o istante consegna iPhone.
- I NOACK firmware sono un indizio concreto; non dimostrano da soli che
  radiotap NO_ACK venga ignorato. Stato ACK/successo non prova un ACK RF
  nel percorso no-ACK. Richiesta di configurazione e politica effettiva
  restano distinte: verificare quest'ultima insieme ad accodamento/timing,
  senza ripetere il semplice toggle già provato o fissare una patch subito.
- TCP752 segmenti retrans, 1.033.151/9.457.146 byte (10,92%); non equivalgono
  ai 668 NOACK driver. iPhone312 annunci durante Upload, RSSI mediano-24
  (-29/-22), sequenza5/16 sul6 in303, due slot in9. Netlink25 rifiutati/
  troncati su12.035; zero perdite è riferito soltanto alla traccia driver.
- Confronto velocità con118,49 s non controllato: prima RSSI-42 e senza
  tracepoint debug, ora-24 e ulteriore overhead. Nessuna ottimizzazione
  applicata né peggioramento causale attribuito a una modifica radio.
- Istanze entrambe rimosse, stato/filtri globali identici, debug_mask0,
  hash profili invariati, AirDrop off, Owly RX_MGMT attivo e Wi-Fi fisso
  riconnesso; nessuna interfaccia/processo test residuo. Nessuna PR/commit.
  results.json, analysis.md, analyze.py con self-check del parser passati
  conservati nella directory prova; log privati e temporanei.

### Confronto unicast distanziato di 2 ms predisposto

- Il limite BURST=64 / pausa500us esistente è per input e non impedisce
  nuovi burst su nuovi pacchetti. La variante usa next_unicast persistente:
  al massimo un frame unicast ogni2000us lato scheduler, con verifica delle
  finestre e guardie AWDL a ogni invio. Management, multicast, ACK, rate,
  aggregazione e profili restano quelli precedenti. Non garantisce spacing RF.
- Patch locale tools/airdrop/owly-qca9377-pacing.patch, applicata dopo la
  correzione management. Config.unicast_gap_us predefinito0 conserva i vecchi
  test/comportamento; soltanto la build sperimentale radio lo imposta2000.
  Limite globale per questa prova con un iPhone; eventuale uso multi-peer
  richiederebbe stato per peer, esplicitato nel commento ponytail.
- Build in /tmp/end4-airdrop-speed/pacing-build-6uhe8dat, pacchetto separato
  owly-qca9377-pacing-bench-0.4.1-1-x86_64.pkg.tar.zst sotto package/.
  Binario previsto /usr/lib/owly-qca9377-pacing-bench/owlyd, installato tramite
  pacman con ownership root; nessun servizio punta al checkout utente.
  Il pacchetto non contiene unit, hook o script installazione.
- 124 test Rust passati, 1 test hardware ignorato. Check nuovo verifica
  pausa non aggirabile dai nuovi input, deadline timer e nessun invio nel
  canale non condiviso/guardia. Formattazione Rust e sintassi Python/Bash OK.
  Manifest build conserva hash sorgente/pacchetto/binari e risultati.
- Quota /tmp incontrata durante build: rimossi soltanto gli artefatti debug
  nuovi, poi completata build su disco in target temporaneo della workspace.
  Target da422MiB rimosso dopo packaging; nessun binario build nella proposta
  di config e nessun cambiamento a backend installato durante preparazione.
- bench-pacing.py esegue baseline e variante con la stessa diagnostica esiti
  firmware e copie ZIP regolari. Durante fase2 soltanto override root in
  /run/systemd/system/owlyd.service.d/90-pacing-bench.conf; al termine rimuove
  override, riavvia originale e rimuove pacchetto sperimentale. Hash originale
  e profili verificati prima/dopo. Recovery restore.sh nella directory gruppo.
- Verifica systemd dopo installazione del binario e prima di riavvio;
  controllo hash e proprietà root del binario/directory. Self-check rollback
  passati su successo, errore trasferimento/installazione/riavvio/verifica,
  hash errato, timeout off e interruzione. Controllata terminazione child.
- bench-driver.py accetta directory gruppo e assenza pausa intermedia;
  inoltra interruzioni al supervisore con pulizia della cattura. Nessuna
  modifica alla radio prima degli Invio guidati. La seconda fase richiede
  rinnovo Tutti10min senza spostare iPhone. Confronto solo sequenziale,
  non prova statistica; analizzare anche RSSI, sequenze, NOACK, coda e gap TX.
  Terminale predisposto «AirDrop - confronto pacing 2 ms»; nessuna PR/commit.

### Esito confronto pacing: miglioramento nella coppia, prova ripristinata

- Gruppo compare-pacing-y0p3rkdn: baseline driver-status-j9u_ek92/
  run-sPrwomBs, variante driver-status-m0_c08qx/run-Dxmr5Gwr. Entrambi
  Upload200, ZIP reale/archivi/hash identici.205,45->174,06s,40,83->48,19kB/s:
  tempo-15,28%, throughput+18,03% in questa singola coppia sequenziale.
- NOACK totali781->646; tra frame>=1000byte768/6976(11,01%)->643/6848(9,39%).
  Mediana grandi TX->messaggio stato10,020->6,725ms, p95247,306->191,959ms.
  TCP868->738segmenti retrans, byte_retrans/sent12,42%->10,76%.
- Pacing realmente visibile nelle submission dei grandi: gap minimo
  0,016->1,847ms, gap<1ms2383/6975->0/6847; nessuno<1,8ms nella variante.
  Non è misura spacing RF. Outstanding grandi al loro invio mediano3->2,
  picco16->19 (tutti18->21): non riduzione uniforme della coda.
- RSSI mediano-37dBm in entrambi e sequenza prevalente5/16sul6,11/16sul44;
  baseline35/390annunci con soli2slot sul6, variante12/336. Mediane uguali
  non garantiscono stessa RF; non dedurre airtime dai conteggi degli annunci.
  Risultato promettente da confermare con ordine inverso prima di mantenerlo.
- Trace49476eventi/16492TX e47871/15957, nessun overflow/dropped event,
  stati e unref completi. Un ID baseline riusato dopo stato e prima di unref,
  consentito dal driver: parser prudente ha rifiutato l'associazione vecchia.
  Endpoint corretto in entrambe le fasi TX->messaggio stato (prima del rilascio
  ID); unref controllati a bilancio senza associazioni ambigue. Self-check
  dell'interleaving reale e dei casi invalidi passato. Nessun dato alterato.
- Pacman: installazione del solo owly-qca9377-pacing-bench alle20:35:13,
  rimozione alle20:39:46; nessun altro pacchetto rimosso nella transazione.
  Originali owly-qca9377-fix e omdrop-owl-bin0.4.1-1 presenti. Eseguibile
  originale attivo, hash invariati, runtime override/binario sperimentale
  assenti, RX_MGMT=1, debug_mask0. AirDrop off e Wi-Fi fisso riconnesso;
  nessuna awdl0/nlmon residua. phase=restored, result=0.
- Netlink12/9517 e26/10940datagrammi rifiutati/troncati; non estendere zero
  perdite tracefs alla radio. Nessuna nuova prova attivata durante l'analisi.
  results.json, analysis.md, pacman-events.log nel gruppo; analyze.py delle
  fasi riproduce numeri, gap e outstanding. Nessuna PR/commit.

### Ripetizione predisposta con ordine inverso

- bench-pacing.py --pacing-first: prima variante2ms, poi normale. Stesso
  pacchetto sperimentale, SHA256 c8c890ab5b5a54b14a24826f1b1fb5c34bc099c733468b1a8a074b53a33b3242
  verificato; nessuna ricompilazione o variazione a intervallo/ACK/rate/canale.
- La fase pacing viene completamente ripristinata (servizio originale e
  rimozione pacchetto/override) prima della baseline. Primo errore interrompe
  il confronto, dopo cleanup; nessun secondo invio su fase precedente fallita.
  Manifest con ordine esplicito e codici esito separati per fase.
- Self-check superato per entrambi gli ordini e arresto sul primo errore,
  oltre ai precedenti casi rollback. ZIP e diagnostica restano quelli già
  verificati; iPhone fermo e rinnovo Tutti10min prima della seconda fase.
- Terminale «AirDrop - confronto inverso pacing 2 ms» predisposto; prima
  dell'installazione temporanea richiede Invio/sudo. La radio parte soltanto
  dopo gli ulteriori Invio del benchmark. Nessuna PR/commit.

### Ordine inverso: arresto all'avvio, nessuna misura di velocità

- Gruppo compare-pacing-xd9ylu03, prima fase pacing:
  driver-status-xvh5t5k8/run-JYaRWrmf. Owly restituisce
  «Couldn't bring owlyibss0 up: Device or resource busy (os error 16)».
  Nessun invio tentato, nessun send.log/tcp.log; baseline non eseguita.
  Non utilizzare questa sessione per confrontare le velocità.
- phase=restored, result=1: eseguibile originale e hash dei due profili
  invariati; override e pacchetto sperimentali rimossi, AirDrop spento,
  Wi-Fi fisso riconnesso. Trace temporanea rimossa, stato tracing globale
  invariato. Il pacing dei dati non era ancora entrato in funzione;
  causa dell'EBUSY da determinare prima di cambiare i parametri radio.
- Log di sistema non accessibili all'utente e ticket sudo scaduto:
  predisposto terminale di sola lettura collect-startup.sh nella directory
  gruppo, con password inserita localmente. Raccoglie journal Owly,
  NetworkManager e kernel nella finestra21:30–21:33 del30/10/2026;
  non riavvia servizi e non modifica connessione o radio.
- Raccolta completata: startup-system.log e startup-kernel.log conservati
  nel gruppo. Unmanage wlp2s0 alle21:31:19, nuova IBSS creata, poi immediato
  ritorno a managed durante rollback; avviso Owly dopo la riconnessione.
  La cronologia non prova che NetworkManager abbia sottratto la radio:
  evitare di confondere il ripristino conseguente con la causa dell'errore.
  Nessun crash firmware riportato nella finestra raccolta.
- Ripetizione invariata predisposta con diagnostica aggiuntiva:
  bench-speed.sh registra snapshot e monitor degli eventi link, terminato
  nel cleanup; bench-driver.py raccoglie dal supervisore privilegiato i
  journal servizi/kernel nella finestra prova, solo dopo pulizia tracing.
  Output nel campo journal di driver-summary.json; errori/timeout journal
  registrati senza compromettere il ripristino. Nessun codice del checkout
  eseguito come root. Profili/pacchetto/ordine/2ms identici al tentativo fallito.
- Self-check driver (incluso timeout journal), speed (nessun monitor residuo),
  pacing (ordine e rollback) e sintassi Bash superati senza usare la radio.

### Secondo tentativo inverso: radio avviata, connessione Ask rifiutata

- Gruppo compare-pacing-9wlxrdxj, pacing/driver-status-vju9r7uk/
  run-szUCZtqS. Radio esclusiva sul6 correttamente attiva e peer rilevato;
  Discover200 in0,16s. Nuova connessione TCP/TLS per Ask rifiutata con
  ConnectionRefusedError, prima di send_ask e prima dell'upload.
  Durata comando4,397s: non è durata trasferimento né misura di velocità.
- Nessuna seconda fase eseguita. phase=restored, result=1; backend originale
  attivo, pacchetto/override sperimentali assenti, Wi-Fi fisso collegato.
  Stato tracing globale invariato e istanza rimossa; nessuna interfaccia
  AirDrop residua. Journal servizi/kernel leggibili nella nuova diagnostica.
- L'utente conferma schermo bloccato o impostazioni AirDrop cambiate durante
  la prova, senza specificare quale dei due. Evento compatibile con listener
  non più disponibile; non prova della causa unica o di regressione pacing.
  Il sender Python lascia uscire il rifiuto pre-Ask come traceback; eventuale
  gestione più chiara/retry resta separata, nessuna modifica distribuita ora.
- Ripetizione invariata predisposta: PC invia a iPhone, schermo acceso,
  Tutti10min mantenuto/rinnovato fra fasi e nessuna condivisione foto richiesta.
  Nessuna modifica a codice, pacchetto, radio o parametri del confronto.
  results.json nella directory privata del gruppo riporta stadio e limiti.

### Confronto inverso icpegeev: pacing completato, baseline interrotta

- Pacing driver-status-2i9axu89/run-6dZSALAp: Upload200, 8.388.736byte
  in178,21s (47,07kB/s), hash ZIP di riferimento verificato. TCP748segmenti
  retrans,10,88%byte; grandi659/6856NOACK (9,61%). Gap submission minimo
  1,925ms, nessuno<1,8ms. Trace48423eventi/16141triple complete, zero overflow.
- Baseline driver-status-y3kwywkq/run-24QVbTlC: Ask accettato, BrokenPipe
  durante upload a+72,11s; prima osservazione TCP CLOSE-WAIT a+70,45s,
  bytes_acked massimo3163565 (contatore TCP, non file salvato). L'utente
  conferma interruzione autonoma senza toccare il telefono.
- Radio PC attiva fino al cleanup dopo l'errore, iPhone ancora annuncia
  quattro volte dopo CLOSE-WAIT; RSSI mediano-24dBm entrambe le fasi,
  sequenza dominante5/16sul6 identica. Suggerisce chiusura connessione lato
  ricevente, senza spiegare perché. Nessun crash firmware nel journal;
  non attribuire a blocco schermo o stabilità pacing senza altre prove.
- Trace baseline23420eventi:7808TX/7806stati/7806unref, zero overflow.
  Parser rigoroso rifiuta associazione incompleta: escluse latenze firmware
  baseline, nessun dato inventato. analyze-partial.py riproduce diagnostica
  TCP/annunci e verifica i self-check parser, conservando il limite esplicito.
- Confronto di velocità non valido: fase normale non completata. Variante
  precedente174,06s e attuale178,21s, condizioni tra gruppi diverse;
  risultato promettente ma non basta a confermare vantaggio quantitativo.
  Nessuna promozione a backend permanente o nuova prova radio automatica.
- phase=restored,result=4; profili/hash originale invariati, AirDrop off,
  Wi-Fi fisso collegato; pacchetto/override e interfacce sperimentali assenti.
  Tracing globale invariato e istanze rimosse. results.json,analysis.md,
  analyze-partial.py e analyzer pacing nella directory privata del gruppo.
  Prossima verifica: causa chiusura anticipata TCP/HTTPS della baseline.

### Ripetizione inversa wck35bep: successo in entrambe, velocità identica

- Pacing driver-status-norcspj4/run-xpsePSK4 Upload200 in181,41s;
  originale driver-status-i34fzhwt/run-Apag0HIB Upload200 in181,42s.
  Stesso ZIP reale8.388.736byte/hash verificato,46,24kB/s entrambi.
  Differenza0,01s (0,0055%): vantaggio iniziale del18% non riprodotto.
  Manteniamo originale; nessuna promozione della variante o nuova prova radio.
- Variante realmente attiva: gap submission minimo grandi1,875ms contro
  0,018ms, nessun gap<1ms contro2405; non garanzia spacing RF.
  TCP759->735segmenti retrans,11,03%->10,72%byte; NOACK grandi
  676/6867(9,84%)->643/6843(9,40%). Mediana grandi9,870->8,625ms,
  ma p95214,404->250,021ms e picco outstanding grandi9->28, mediana3->2.
  Nessuna riduzione uniforme della coda e nessun guadagno upload misurato.
- RSSI mediano-22dBm originale/-24variante; sequenza dominante5slot6/11slot44
  identica, osservata324/332annunci originale e319/338variante; restanti
  annunci2slot6. Conteggi annunci non equivalgono ad airtime disponibile.
- Trace49110eventi/16370triple originale e51039/17013variante, zerooverflow,
  associazioni complete; analyzer/self-check passati. results.json,analysis.md
  eanalyze.py per fase nella directory privata del gruppo riproducono i dati.
- phase=restored,result=0; AirDrop spento, Wi-Fi fisso collegato, backend
  originale attivo, hash binario/profili invariati; solo dropin originale,
  pacchetto e interfacce sperimentali assenti, tracing globale ripristinato.
  Prossimo ambito: finestre AWDL condivise e smaltimento coda firmware,
  prima analisi delle catture disponibili. Nessuna PR/commit.

### Analisi111s contro181s e rivalutazione canale44

- Analisi offline riproducibile inanalysis-windows-xtmkcovo/analyze.py,
  results.json eanalysis.md: parser TCP con fixture e assert stream completato.
 111,08s/75,52kB/s erano reali con backend normale e canale6; ritrasmissioni
  byte6,35%, cwnd mediana8, RSSI-26. Originale recente181,42s/46,24kB/s,
  retrans11,03%, cwnd4, RSSI-22. Pacing181,41s,10,72%,cwnd5,RSSI-24.
  Segnale più forte da solo non spiega throughput; nessuna causa unica isolata.
- Sequenza dominante5/16sul6 uguale. Stato dell'ultimo annuncio5slot6:
 105,87/110,45s veloce,179,48/181,10s originale,176,79/181,11s pacing.
  Queste durate sono dello stato osservato, non airtime RF. Nessuna evidenza
  di più finestre6 nel run111; mancavano i campi di timing necessari a un
  confronto dettagliato retroattivo della sincronizzazione e la trace TX.
- Grandi TX->messaggio stato>196,608ms:393/6867originale,435/6843pacing.
  Superano la massima finestra6 contigua nominale; non sono timestamp RF.
- Confondente esplicito:111s conTCP+nlmon,181s anche trace firmware dettagliata.
  Macro ath10k_dbg attiva lavoro di debug quando log_dbg tracepoint è attivo
  anche con mask0; filtro limita eventi salvati. Possibile costo non misurato,
  non attribuire automaticamente tutto a RF né tutto a tracing.
- Prossimo confronto proposto A/A originale leggero/dettagliato/leggero,
  nessuna installazione/override, stessa posizione/file, per quantificare costo
  strumentazione prima di altre patch. Non avviato durante questa analisi.
- Canale44 riletto: globalIT/phy99PASSIVE-SCAN e5220MHznoIR ancora presenti.
  Client sul100larghezza80MHz; cache reti100/36, nessuna44(nessunrescan).
 5GHz client non equivale a IBSS autonoma. Eventuale AP44 e mantenimento
  associazione richiedono verifica vincoli e adattamento backend (shared non
  creaowlyibss0). Non basta cambiare TOML e non si promette beneficio11/5.
  Riferimento ufficiale Linux processing_rules.html#beacon-hints.
  Solo letture diiw/nmcli, nessun servizio/configurazione modificato.

### Priorità utente: indagare canale44 con la QCA9377

- L'utente sceglie di concentrarsi sul44. Nessuna ulteriore prova pacing
  predisposta; configurazione funzionante6 preservata e AirDrop spento.
- Rilettura cache(norescan): Starlink100/36, nessunAP44. L'utente dispone
  anche di TP-Link conSIM di5–6anni; richiesti modello e versione hardware
  per verificare5GHz e selezione manuale44 prima di istruzioni specifiche.
  Non servono dati SIM per lo scopo del collegamento Wi-Fi locale.
- Prima porta da verificare: AP reale su44, scansione passiva e lettura
  flag kernel, anche dopo il rilascio della station. Beacon hints kernel
  sono condizionali; non dichiarare che la presenza AP risolve noIR.
  Provare prima join IBSS nativo solo se il canale è consentito. Se il
  permesso sopravvive e il join funziona, mantenere backend esclusivo;
  evitare sviluppo shared non ancora necessario.
- Se la disassociazione ripristina noIR, verificare mantenimento associazione
  prima di adattamenti backend. Hardware dichiara managed+IBSS sul medesimo
  canale; ciò non sostituisce collaudo reale. Shared attuale crea solo monitor,
  correzione management locale apre IBSS fisso: passaggio shared richiede
  progettazione e verifica dati/ACK oltre ai management, non semplice TOML.
- Sorgenti ufficiali kernelv6.18 reg.c,ath/regd.c,mac80211/iface.c echan.c
  consultati. Macro/regole dinamiche country user non abilitate nella config
  kernel letta; globalIT non equivale a consenso iniziativa radio del wiphy.
  Riferimenti:
  https://wireless.docs.kernel.org/en/latest/en/developers/regulatory/processing_rules.html#beacon-hints
  https://raw.githubusercontent.com/torvalds/linux/v6.18/drivers/net/wireless/ath/regd.c
- Nessuna modifica kernel/EEPROM, servizio, profilo, router o nuova radio
  avviata; nessuna compilazione, dipendenza aggiunta, PR o commit.
- TP-Link identificato comeTL-MR150(versione ignota). Specifiche ufficiali
  V1,V2eV3 dichiarano solo2,4GHz: non utilizzabile come AP44, nessuna
  modifica o aggiornamento firmware proposto per abilitarvi5GHz.
  https://www.tp-link.com/it/home-networking/3g-4g-router/tl-mr150/v1/
  Prossimo controllo indipendente: scansione passiva mirata5220MHz per
  verificare eventuale AP44 fuori dalla cache senza associarsi ad altre reti.
- Predisposto controllo channel44-passive-jinjxswh/scan.sh, sintassi Bash
  verificata: guard AirDropoff, attesaInvio/sudo locale, iwscanpassive solo
 5220MHz con timeout25s. Snapshotreg/phy e connessione prima/dopo; nessun
  cambio rete, associazione a terzi o parametro AirDrop. Log privati0700.
  Terminale «AirDrop - ascolto canale44»; iPhone non necessario.

### Ascolto44 completato: nessunAP44 e vincolo invariato

- channel44-passive-jinjxswh: scansione passiva5220MHz completata, exit0.
  Risultato iw restituisce una sola BSS a5500MHz (rete associata/cache),
  nessuna a5220MHz. Non interpretare la BSS cached100 come ricezione sul44;
  una singola scansione non dimostra assenza permanente di AP44 nell'area.
- phy-before/after:5220MHz[44]23dBm(noIR), invariato. GlobalIT,phy99
  PASSIVE-SCAN invariati. Nessun beacon hint utile osservato sul44.
- UUID e stato connessione identici prima/dopo; verifica reale rete fissa
  collegata sul100, AirDropoff e backend originale attivo. results.json
  conserva conteggi per frequenza e limiti della lettura, log privati.
- Ostacolo attuale alla prova AP/beacon: nessun AP44 controllabile noto;
  TP-LinkMR150 solo2,4GHz. Serve accesso temporaneo a un AP5GHz impostabile
  su44 per verificare questa strada; la sua presenza non garantisce che
  kernel/driver consentano IBSS o che il permesso sopravviva al distacco.
  Non preparare altre prove file identiche sul6 per questo obiettivo.

### Ripetizione richiesta della prova111s, diagnostica leggera

- L'utente richiede esplicitamente di ripetere il run veloce sul6 mentre
  attende disponibilità router44. Gruppo replay111-eugy_jx9, una sola fase,
  backend originale, nessun pacing o RTO modificato. Stesso ZIP8.388.736byte
  copiato come file regolare0600; SHAac2dbab130dd40c255993de77b844273f6871693fa18b8a051afe5a49be85b67
  e payload DVZip/CPIO verificati offline, preflight archiviato nel gruppo.
- Riutilizzato bench-channels.py conTCP+nlmon, senza bench-driver e senza
  registrazione TX/status/unref. Precontrollo sudo di sola lettura verifica
  eventi driver/debug_mask spenti anche nelle eventuali altre trace instances;
  abortisce prima della radio se non sono0, senza disabilitare trace altrui.
- Stato reale preliminare: AirDropoff/Owlyidle, originale47fa6c73... attivo,
  profili hash invariati, Wi-Fi fisso collegato, nessun benchmark concorrente.
  launch.sh sintassi verificata; terminale «AirDrop - ripetizione prova111s
  originale» predisposto. Password locale e Invio prima di cattura/radio.
- Telefono fermo e sbloccato, Tutti10min; accettare un solo ZIP PC->iPhone.
  Misurare tempo upload, distinto dalla ricerca e dal consenso. Collector
  rimuove nlmon, benchmark ferma AirDrop e riconnette rete fissa.
  Nessun pacchetto o override installato; nessuna configurazione modificata.

### Ripetizione leggera179,31s: nuovo indizio altri peer AWDL

- replay111-eugy_jx9/run-NzM9SnCt,channels-q67nzwiq: Upload200/exit0,
 8.388.736byte in179,31s/46,78kB/s. Trace TX/status/unref e debugmask0
  nelpreflight. Rimuovere diagnostica dettagliata non riproduce111s;
  non attribuirle da sola la condizione lenta attuale né quantificarne
  l'eventuale piccolo costo senza confronto A/A.
- RSSI mediano-26 uguale a111s; retrans byte6,35%->11,06%,cwnd mediana8->4.
  Dominante5slot6 invariata. Stato ultimoannuncio2slot per8,319s dell'upload
 178,989s fra POST/risposta; non è airtime misurato.
- Stallo campionato5,689s alle22:43:46,883–52,572CET,171927byteacked fermi
  eSendQ169032; RTO1823->3647ms/backoff. Nel tratto23annunci iPhone,
 22con2slot6,1con5slot6 eRSSI-25/-24. Correlazione, non causa provata;
  singolo stallo non basta a spiegare differenza68s.
- Seconda sorgente AWDL ora presente(anche entrambe fasiwck35bep), assente
  nella cattura111. L'utente conferma altri dispositivi Apple vicini.
  Owly elegge sync/master fra peer validi; le catture non salvano tutti i
  campi elezione per dimostrare quale peer fosse seguito. Non identificare
  dispositivi da soliMAC né equiparare dueMAC a due dispositivi certi.
- Prossima verifica proposta: stessa prova/posizione isolando altri Apple,
  con conferma dalla cattura che la seconda sorgente scompaia. Nessuna
  nuova radio/test predisposto durante analisi, nessun parametro cambiato.
- AirDropoff/Owlyidle, originale attivo e hashbinario/profili invariati,
  retefissa collegata, nessuna interfaccia/procedura residua. Analyzer,
  results.json,summary.json,stalls.json eanalysis.md nel gruppo privato.

### Revisione del metodo richiesta: protocol reverse engineering

- Applicata skill protocol-reverse-engineering alla ricostruzione del metodo
  upstream. Versione iniziale plugin(commit a78ab08efd7f15a3cb32d7a2a9d926e8b1ee3322)
  usa AWDL già nel firmware Broadcom AppleSilicon, più driver vendor/helper:
  non reimplementa tutto dazero. Backend software Owly arriva successivamente.
- Owly0.4.1 documenta fonti SEEMOO/OWL e pubblicazioni, catture reali Apple,
  SPEC, domande aperte e corpusPCAP+TOML rigiocato inNode. Replay verifica
  parsing/peer/master e sincronizzazione, con tolleranza3TU sullo schedule.
  Corpus attuale locale: tre sessioni discovery/receive/send mt7925e sul44;
  non è collaudo QCA9377 né una cattura di riferimento iPhone->Mac.
- Lacuna delle nostre catture: metadati TCP/canale/driver utili, ma campi
  elezione/master e timeline interna Owly insufficienti per provare chi
  sincronizza con chi. Altri Apple restano ipotesi correlata, non causa provata.
- Verificato owly capture --help senza radio: disponibile installato.
  Codice capture.rs legge AF_PACKET dal monitor; non integra il percorso
  management nl80211 della patch QCA. Per questa scheda usarlo da solo
  può omettere proprio i management necessari. Unire/arricchire raccolta
  management e dati prima di considerarla una cattura completa.
- Direzione proposta: prima validazione offline contro corpus/spec, poi
  cattura breve mirata(elezione,clock,finestre,sequenze/retry eTCP) compatibile
  conQCA; una ipotesi per confronto, riproduzione offline/test regressione
  prima di una modifica permanente. Canale44 resta filone parallelo in attesa
  AP adatto; nessun nuovo test8MiB o cambiamento radio avviato ora.
- Skill binary-analysis-patterns valutata per disassembly di componenti
  chiusi; non applicata a binari in questa revisione, dato codice Owly aperto.
  Nessuna installazione di tool/deps o ricompilazione, nessuna PR/commit.
  Riferimenti verificati tramite GitHub:
  https://github.com/t4t5/owly/blob/v0.4.1/tests/captures/README.md
  https://github.com/t4t5/owly/blob/v0.4.1/docs/open-questions.md

### Prima fase protocollo: decoder e diagnostica verificati offline

- `bench-channels.py` ora conserva elezione v1/v2 separatamente, metriche,
  contatori, master dichiarato nel Sync TLV, versione/classe, sequenza802.11,
  fragment/retry e tempo monotonic dell'osservazione. Mantiene anche annunci
  PSF/MIF privi del TLV lista canali: prima venivano scartati, perdendo eventuali
  dati di sincronizzazione. `channels` e statistiche derivate sono quindi
  opzionali nei nuovi record; gli analyzer devono verificarne la presenza.
- Nessun frame grezzo, hostname o contenuto file aggiunto ai log: solo metadati.
  I MAC reali restano dati privati; i rapporti delle prove locali non vanno
  distribuiti. Sequenza/retry non equivalgono a misura delle perdite radio.
- Nuovo `awdl-inspect.py`, solo stdlib: legge JSONL e PCAP nativi Owly
  anonimizzati (LE/microsecondi, radiotap limitato a canale/RSSI), rifiuta
  formati diversi e catture troncate/disordinate. Non è un dissector PCAP
  generico; per altri formati usare strumenti esistenti come tshark.
  Riporta per sorgente storia della topologia dichiarata, metriche/contatori
  finali, master Sync dichiarati e sequenze canali. Una volta visto v2, v1
  non sovrascrive quello stato, come nel Peer di Owly. Campi mancanti nelle
  catture vecchie restano sconosciuti, non diventano prova di stabilità.
- Verificato sui tre PCAP upstream: discovery1219, receive1499 e send2175
  annunci (4893 totali). Nel send il peer Linux anonimizzato cambia master
  dichiarato a53,469044s e torna a quello precedente a54,482386s. Questo è
  un evento del corpus mt7925e/44, non una prova del problema QCA9377.
  Rapporti privati: `/tmp/end4-airdrop-speed/protocol-offline-v_e5yoj4/`,
  inclusi fast111/repeat179: entrambi senza campi elezione utilizzabili.
- Nuova patch locale `owly-awdl-diagnostics.patch` per Owly0.4.1, solo
  driver. Inattiva per default, richiede `OWLY_AWDL_DIAG=1` all'avvio del
  daemon compilato con la patch. Non modifica Config/Node, elezione,
  scheduling, canali, ACK o pacing. Non è inclusa nel PKGBUILD/install.sh
  e non è stata installata né attivata sul sistema.
- `AWDL_DIAG_ELECTION`: stato effettivo dopo Node::handle (master,sync,
  height,metric,counter), emesso quando cambiano master/sync/height/metric.
  `AWDL_DIAG_SYNC`: solo annunci accettati dal Node con Sync TLV; error_before_tu
  confrontato PRIMA di Node::handle, selezione master/sync precedente,
  applied=true quando quell'annuncio aggiorna l'orologio, AW/nextTU dopo.
  Eventi scritti dopo l'esecuzione delle azioni per non mettere il log davanti
  all'iniezione dei frame. Nessuna nuova dipendenza. I log hanno comunque
  un costo da considerare nelle comparazioni di velocità.
- `t_us` è il tempo Input relativo alla singola istanza del driver, non
  un timestamp RF. Per correlazione TCP usare anche i timestamp del journal;
  errore prima dell'update include ritardi del percorso di ricezione e non
  dimostra da solo deriva fisica dell'orologio. Il report Python descrive
  gli annunci, mentre questi eventi descrivono la scelta reale del daemon.
- Controlli: self-test Python decoder/socket/cleanup passato (socket locali,
  nessuna radio); self-test inspector su PCAP/JSONL, v2 persistente, input
  malformato e metadata mancanti passato. 62 test owly-awdl con feature driver
  e diagnostica abilitata, incluso nuovo test offset positivo/negativo,
  frame troncato e orologio immutato. Sei test replay owly-radio passati
  prima e dopo la patch. Applicabilità patch verificata con dry-run.
  Eseguiti anche i test lib radio: 32 passati, uno ignorato che richiede
  cattura hardware; il solo test scoperta nl80211 bloccato dalla sandbox
  (EPERM) è passato ripetendolo senza sandbox, da utente e in sola lettura.
- Cargo ha usato dipendenze già in cache, offline/locked, due job. Output
  compilati temporanei rimossi dal progetto dopo i controlli. Nessun package,
  drop-in systemd, backend installato o profilo radio modificato; nessuna PR.
- Verifica finale: hash binario originale47fa6c73..., radio.toml dc35804f...
  e drivers.toml b9278a9a... invariati; AirDrop off/receiving=false/visible=false.
  Inspector verificato anche tramite CLI con percorso contenente spazi;
  `git diff --check` passato. Modifiche preesistenti conservate.

Comandi ripetibili dalla radice del progetto (nessun sudo/radio):

```bash
python3 tools/airdrop/bench-channels.py --self-test
python3 tools/airdrop/awdl-inspect.py --self-test
python3 tools/airdrop/awdl-inspect.py '/percorso con spazi/channels.jsonl'
python3 tools/airdrop/awdl-inspect.py '/sorgenti Owly/tests/captures/send-ios26.x-mt7925e-ch44-1.pcap'
```

Per verificare la patch, applicarla con `patch -p1` in una copia dei sorgenti
Owly0.4.1, quindi da quella copia eseguire:

```bash
OWLY_AWDL_DIAG=1 cargo test --offline --locked --release -p owly-awdl --features driver -j 2
cargo test --offline --locked --release -p owly-radio --test replay -j 2
```

Prossima fase ancora da fare: compilare/confezionare una variante diagnostica
temporanea preservando la patch management QCA, predisporre ripristino automatico
del binario originale e cattura breve guidata di discovery. Confrontare presenza
degli altri Apple, scelta effettiva del sync peer e offset; solo dopo scegliere
un esperimento sul trasferimento. Non assumere colpevole il secondo MAC e non
avviare ancora un altro benchmark8MiB identico. Per il44 serve ancora un AP
adatto e la verifica reale del vincolo noIR, non una modifica software del paese.

### Prova discovery master/clock predisposta, variante temporanea

- Utente disponibile ora per circa2min con iPhone vicino, sbloccato e
  Tutti10min. Nessun file da inviare; raccogliere prima discovery stabile,
  lasciando gli altri Apple nelle condizioni attuali. Radio solo dopo Invio.
- Build offline/locked da tarball0.4.1 verificato, con sole patch management
  QCA e diagnostica. Pacchetto separato owly-qca9377-diag-bench0.4.1-1:
  `/tmp/end4-airdrop-speed/diag-build-jdjez_6g/package/`.
  SHA256pacchetto65fe65827cc660442d31c49415c8f54b8dff085759232cd3fe871a80fc9d32b2;
  binarioe6484b0d2a6e38ee0d5b19fc1308db8f8d5ed841c8b701deceac226247995181.
  Manifest sorgente/patch/hash e build.log nella directory padre.
- 62 test owly-awdl con diagnostica, 6replay e test management parser passati;
  test management da cattura hardware ignorato come previsto. Nessun test radio
  eseguito durante la compilazione. Artifact Cargo temporanei rimossi dal repo.
- `bench-discovery.py` riutilizza switch/rollback di bench-pacing (soltanto
  gestione pacchetto/servizio, nessuna patch pacing). Descrizione della variante
  ora selezionabile via environment nel helper, default pacing invariato.
  Pacchetto ed ELF confrontati con manifest, nomi/percorsi archivio verificati,
  marker diagnostici presenti. Esegue solo binario installato e protetto root
  in `/usr/lib/owly-qca9377-diag-bench/owlyd`, mai codice checkout come root.
- Drop-in temporaneo `/run/systemd/system/owlyd.service.d/90-diag-bench.conf`
  con ExecStart variante ed Environment=OWLY_AWDL_DIAG=1; viene validato con
  systemd-analyze verify dopo installazione e prima del riavvio. Rimozione
  override, riavvio originale, verifica eseguibile e rimozione solo pacchetto
  diagnostico nel finally, anche per annullamento/errori. Originale resta
  installato. restore.sh manuale preserva override eventualmente modificati
  da terzi. Non è una garanzia contro SIGKILL, spegnimento o guasto del sistema.
- `bench-channels.py --discovery` riutilizza nlmon/preflight/cleanup e avvia
  observer90s invece del benchmark file. L'osservatore aspetta un secondo
  Invio prima della radio, verifica receiving/visible, poi campiona stato e
  peers ogni5s. Nessun comando send. Raccoglie JSONL management arricchito e
  journal backend con timestamp; assenza AWDL_DIAG_SYNC segnala prova non
  conclusiva. Timeout raccolta journal non impedisce il tentativo di
  riconnessione; profili e binario originali verificati dopo il ripristino.
- Self-test observer successo/fallimento readiness, pacchetto alterato,
  percorsi con spazi; suite rollback riutilizzata con parametri diagnostici;
  self-test collector esteso a ramo discovery e passato con socket locali.
  git diff --check passato, launcher Bash validato.
- Preflight reale sola lettura: AirDropoff/Owlyidle, originale47fa6c73...,
  hash profili invariati, rete fissa UUID51bc989c-c09f-4b24-9cb8-e9224c72584c,
  nessuna variante già installata/override precedente. Manifest preflight
  nella directory build. Launcher aperto nel terminale «AirDrop — master e
  sincronizzazione», log interattivo terminal.log. Non interpretare apertura
  del terminale come prova svolta: esito, ripristino e dati da verificare
  quando l'utente completa la procedura.

### Discovery: ripetizione richiesta dall'utente

- L'utente segnala di aver sbagliato e chiede riprova. La prima procedura
  discovery-xph8egvb è terminata tecnicamente con result0/phase restored;
  non usarla come confronto controllato senza chiarire l'errore operativo.
  Tutti i log originali, incluso terminal.log, vengono preservati.
- Prima di ripetere verificati realmente: AirDropoff/Owlyidle, eseguibile
  originale e hash profili invariati, nessun override/binario/pacchetto
  diagnostico residuo, Wi-Fi fisso UUID atteso collegato.
- Riutilizzato lo stesso pacchetto verificando hash e contenuto dal manifest;
  nessuna ricompilazione o modifica parametri. Nuovo launcher/log separati
  nella directory indicata da `/tmp/end4-airdrop-speed/discovery-retry.path`.
  Terminale distinto «AirDrop — RIPROVA master e sincronizzazione», conferma
  locale per preparazione e seconda conferma prima della radio. Attendere
  completamento utente e verificare ripristino prima di analizzare la riprova.

### Seconda discovery con foto inviata: nuova riprova solo ricerca

- L'utente conferma di aver inviato una foto durante discovery-l15u8gya.
  Procedura terminata result0/restored, ma condizioni diverse dalla ricerca
  senza trasferimenti: preservare i log senza usarli come baseline controllata.
- Ripristino verificato in sola lettura: off/idle, originale attivo e hash
  binario/profili invariati, nessun pacchetto/binario/override diagnostico,
  rete Wi-Fi fissa attesa collegata.
- Aggiunta istruzione esplicita nel terminale: quando compare il PC tra i
  destinatari NON selezionarlo, lasciare soltanto aperta la ricerca AirDrop.
  Stesso pacchetto diagnostico, hash ricontrollato, nessun nuovo parametro.
  Nuovo launcher/log distinti, indicati da discovery-retry.path; finestra
  «AirDrop — SOLO RICERCA, nessun invio», sempre due conferme prima della radio.

### Discovery corretta: master stabile anche con altre sorgenti

- discovery-t8a5nbrg,channels-5zl26ot0,run-discovery-m38ycyg8:
  l'utente conferma completamento corretto senza invii. Result0/restored;
  verificati realmente originale47fa6c73..., hash radio/profili invariati,
  off/idle, assenza pacchetto/binario/override diagnostici e Wi-Fi fisso UUID
  atteso collegato. Nessuna ulteriore radio avviata durante l'analisi.
- 1170annunci registrati,1094campioni sync accettati dal Node,17osservazioni
  receiving/visible sempre true. Un solo evento elezione: a2,001718s il PC
  segue2a:53:2a:21:e5:90 (sorgente associata all'iPhone nelle prove precedenti),
  metric539/height1. Nessun cambio successivo, pur con altre sorgenti7e... e8e...
  accettate. Nessun loro campione applicato all'orologio del PC. In questa
  discovery non si osserva il sospettato salto continuo verso altri master;
  non conclude assenza di effetti radio da altri dispositivi, né spiega da
  sola la differenza111/179s sotto trasferimento.
- 699sync applicati: esclusa acquisizione iniziale (236069TU, contatori
  inizialmente indipendenti),698successivi. Errore pre-update firmato mediana0,
  range-5..+6TU; assoluto mediana1TU,p953TU=3,072ms,max6,144ms.
 32/698=4,58% oltre3TU, pari alla guardia unicast. Include latenza RX/software,
  non è misura isolata della deriva né prova di TX fuori finestra. Non cambiare
  la guardia senza riscontro sotto carico. Max timer lateness nei blocchi STATS
 2096us; nessun dato TCP di trasferimento disponibile in questa discovery.
- Telefono706annunci,RSSI mediano-37; lista con2slot6 in671,1slot in26,
 5slot in9. Scheduling di discovery, non confronto valido con5slot prevalenti
  sotto upload. Altra sorgente8e...323annunci;7e...141, tutti SENZA lista canali.
  Il decoder precedente avrebbe scartato7e...: correggere interpretazione
  retrospettiva «nessun altro peer nella111» in «nessun altro peer trattenuto
  dal filtro di allora». Non si possono recuperare i campi mancanti dal JSONL.
 35datagrammi collector rifiutati/troncati non sono un conteggio perdite radio.
- Analyzer offline con self-check su acquisizione/segno/percentili/epoche,
  analysis.json,advertised.json eanalysis.md nel gruppo privato. Riproduzione:
  `python3 /tmp/end4-airdrop-speed/discovery-t8a5nbrg/analyze.py`.
  Prossimo confronto utile: un solo ZIP identico, stessa variante diagnostica
  e scheduler/canale6 originali, TCP leggero; correlare scarti/stalli/retrans.
  Non è ancora predisposto/avviato qui. Il44 resta filone AP/noIR separato.

### Invio diagnostico singolo predisposto dopo discovery valida

- L'utente autorizza di proseguire con invio sotto carico. Aggiunta modalità
  `bench-discovery.py MANIFEST --transfer`, riusando lo stesso pacchetto
  diagnostico65fe6582.../binarioe6484b0d... già compilato e collaudato.
  Nessuna ricompilazione, patch/pacing/ACK/canale/guardia o RTO nuovi.
- Modalità transfer riutilizza bench-channels standard e bench-speed.sh--tcp:
  un solo ZIP PC->iPhone, TCP ogni500ms più metadata nlmon e journal interno
  clock/elezione. Nessuna trace TX/unref/log_dbg, nessun ritorno file richiesto.
  Timeout invio240s invariato. Stesso switch root-owned da pacchetto separato,
  systemd-analyze verify prima del riavvio e rollback automatico già verificati.
- Copia regolare privata dello ZIP8.388.736byte, SHAac2dbab130dd40c255993de77b844273f6871693fa18b8a051afe5a49be85b67
  verificato anche DOPO la copia. Sorgente symlink o contenuto cambiato rifiutati
  prima di installazione/radio; manifest annota dimensione/hash e modalità.
  Launcher aggiunge confronto discovery-t8a5nbrg; dispositivo predefinito
  resta quello nel file privato device-name, confermabile nel terminale.
- Payload reale sender verificato offline: CPIO8.388.922byte,
  wire-body8.389.363byte, contenuto identico allo ZIP. Self-test wrapper esteso
  a scelta discovery/transfer, terminazione child in entrambi i modi, copia
  reale/hash alterato/symlink e percorsi con spazi; suite rollback passata.
  Self-test collector e bench-speed-check passati; nessuna radio nei test.
  Label variante diagnostic-master-clock conservata dal collector. git diff
  --check e sintassi launcher Bash passati.
- Preflight reale: off/idle, originale47fa6c73..., hash profili invariati,
  nessuna variante residua e Wi-Fi fisso UUID atteso collegato. Nuovo launcher
  `/tmp/end4-airdrop-speed/transfer-launch-oqw1ny2c/`, indicato anche da
  transfer-launch.path; manifest/log interattivo privati. Terminale
  «AirDrop — INVIO ZIP e diagnostica clock/TCP» aperto; resta in attesa di
  Invio/sudo per preparazione, conferma nome e conferma finale prima radio.
  Questa volta utente deve ACCETTARE un solo ZIP e salvarlo in File sull'iPhone,
  tenerlo fermo/sbloccato e non inviare foto al PC. La prova non è ancora
  certificata completata: verificare esito/ripristino e correlazione clock/TCP
  al ritorno dell'utente. Confronto discovery serve per comportamento temporale,
  non è un benchmark throughput A/B controllato né una spiegazione già provata
  dei111/179s storici. Nessuna PR/commit/pubblicazione.

### Invio154,17s: elezioni mobili e reset clock riprodotti offline

- transfer-diag-w6w8xo67/run-sN9DFHPT,channels-mmjckky5: Upload200/exit0,
  ZIP8.388.736byte in154,17s (54,41kB/s); sendtotale192,639s. Ripristino
  verificato realmente: off/idle, originale47fa6c73..., hash profili invariati,
  variante/override assenti, Wi-Fi fisso UUID atteso. Nessuna nuova radio qui.
- Nel POST->HTTP200:23eventi elezione,20cambi indirizzo master e16sync.
  PC segue telefono102,860s,8e...47,000s,7e...4,000s. Discovery stabile non
  esclude questa dinamica, ma metrica telefono539->513 fra sessioni e peer
  fino541: non attribuire al solo carico la diversa scelta. Non è A/B throughput.
- TCP298campioni, mediana cwnd5,982437byte retrans su9406432sent=10,44%;
  telefonoRSSI-30 mediano,310annunci5slot6/21a2slot6. Timer max2086us.
  Alcuni cambi sono legittimi per la classifica; non vietare altri peer.
- Tre PSF del peer8e..., già selezionato, abbassano metrica a65 e ripartono
  daAW6/14/16 a upload+5,945/+40,068/+80,208s. Vecchio Node aggiorna subito
  peer.election ma usa ancora self.election.sync precedente per clock.update,
  prima del prossimo tick1s. Log applied e corrispondente frame nlmon univoci
  entro2ms provano l'adozione del contatore. Successivi frame tornano alla
  sequenza del telefono. Non è stato dedotto soltanto dal numero di elezioni.
- Primo episodio dentro stallo TCP campionato2,569s (upload+5,601..8,170),
  ACK203621fermo/coda positiva/RTO fino3940ms. Annuncio telefono nel tratto
  mostra scarto di fase ciclica367TU=375,8ms. Correlazione, non quantificazione
  causale dello stallo né spiegazione completa della lentezza. Offset interi
  AW71021/104207/143369TU non sono ritardi RF di decine/centinaia di secondi:
  valutare anche fase modulo16*64=1024TU. Analyzer con self-check e report
  JSON/Markdown salvati nel gruppo privato. Capture26datagrammi rifiutati non
  implica26perdite radio; tutte le consuete cautele nlmon/TCP restano valide.
- Utente chiede di continuare durante l'analisi: completata riproduzione
  offline del difetto con frame sintetici513/541->65 eAW6. Nessun driver,
  rete o radio. Regresso identico fallisce con comportamento originale
  (strumentato solo con contatore update), passa sul candidato; verifica
  clock non contaminato dal peer declassato e update dal peer scelto.
- Nuova candidata `tools/airdrop/owly-awdl-sync-freshness.patch`, da applicare
  dopo management+diagnostica0.4.1. Se cambia l'elezione dichiarata dal peer
  selezionato, riesegue classifica/adotta sequenza PRIMA di applicarne il clock.
  Non modifica la classifica, non forza telefono/MAC, non cambia canali,
  pacing, ACK o guardia. Nuovi/non selezionati restano al tick1s. La tabella
  peer esistente limita il costo; nessuna nuova dipendenza o astrazione.
- La candidata aggiunge Stats.sync_updates e usa la sua variazione per
  applied nella diagnostica, così un cambiamento di scelta durante handle
  non rende il log ambiguo. Pacchetto diagnostico precedente e vecchi dati
  restano immutati; applied precedente è valido per il vecchio ordinamento.
- 63test core/driver/simulazioni/regressione più6replay corpus passati,
  diagnostica attiva nei test in memoria, dry-run patch passato. Nessun
  test hardware nuovo. Artifact Cargo temporanei rimossi dal repo; librerie,
  riproduttori e log privati in candidate/ e repro/ del gruppo della prova.
  Riproduzione `python3 .../transfer-diag-w6w8xo67/analyze.py` e
  `python3 .../transfer-diag-w6w8xo67/repro/check.py`.
- La candidata NON è installata né inclusa in PKGBUILD/install.sh; non è
  ancora compilato un daemon/pacchetto con la correzione e il beneficio
  reale resta da misurare. Il test sintetico non ricostruisce integralmente
  tutti i peer/traffico RF della cattura. Prossimo passo utile: confezionare
  variante temporanea con rollback e verificare sotto stesso ZIP se reset
  e retrans calano, senza dichiarare risolta la lentezza da soli69test offline.
  Nessuna PR/commit/pubblicazione e nessuna modifica alla configurazione locale.

### Collaudo correzione sync predisposto: pacchetto temporaneo revisione2

- L'utente autorizza prova reale della candidata. Build offline/locked di
  owlyd0.4.1 con management QCA, diagnostica e sync-freshness f108a514...
  completato in `/tmp/end4-airdrop-speed/sync-build-sq3m0b7h/`.
  Pacchetto separato owly-qca9377-diag-bench0.4.1-2, stesso nome temporaneo
  del precedente esperimento ma nuova revisione, nessuna sostituzione del
  pacchetto originale owly-qca9377-fix. Revisione1 e relativi log preservati.
- SHA256pacchetto8171facac917cb7afc910db04499f79db17b5874ed394a45792053a2528af55b;
  binario0abec8281a258615d19517d7eb8cadbf1ea6463cb3a8ee41c17038ae3df80e9d.
  Manifest include variante sync-freshness, sorgenti/patch, baseline
  transfer-diag-w6w8xo67 e semantica applied da vero contatore sync_updates.
  ELF archivio uguale a quello compilato, diverso dai due binari precedenti;
  nome/versione/percorsi archivio verificati e validazione helper passata.
- Sorgenti Node,driver,test regressione confezionati identici alla candidata
  già collaudata. Nel build passati63test core/driver/simulazioni/regressione,
 6replay e parser management; test da cattura hardware ignorato come previsto.
  Nessuna radio nei controlli. Build.log e wrapper-check.log conservati;
  target Cargo temporaneo rimosso dal progetto dopo confezionamento.
- Wrapper riconosce variante dal manifest, usa label sync-freshness, messaggi
  specifici e directory transfer-sync-*; rifiuta varianti sconosciute prima
  di subprocess. Self-test aggiornato/passato con guard, rollback, selezione
  modo, file regolare/hash/symlink e percorsi con spazi. Nessun cambiamento
  al benchmark file/TCP/nlmon, timeout240s, ACK, pacing, canale6 o guardia.
  ZIP originale SHAac2dbab... invariato, ricontrollato e copiato con hash.
- Preflight reale off/idle, originale47fa6c73... e profili hash invariati,
  nessuna variante residua, Wi-Fi fisso UUID atteso. Come prima, programma
  root eseguito solo da percorso root-owned installato con pacman, mai dal
  checkout. Drop-in runtime esistente e rollback riutilizzati, con verifica
  systemd dopo installazione e prima del riavvio. Nessun profilo riscritto.
- Launcher in directory build, puntatore `/tmp/end4-airdrop-speed/sync-launch.path`;
  sintassi Bash/git diff --check passati. Aperto terminale
  «AirDrop — PROVA CORREZIONE SYNC», attesa conferme locali prima della radio.
  Utente deve mantenere posizione iPhone/altri Apple come nella154s, rinnovare
  Tutti10min e ACCETTARE un solo ZIP PC->iPhone senza mandare foto al PC.
  Attendere ritorno utente prima di certificare esito e ripristino.
- Criterio analisi prossimo: cercare frame del peer seguito che ne abbassano
  priorità e se applied=false evita il reset; distinguere assenza del caso
  scatenante da sua correzione. Confrontare fase, stall/retrans e tempo, tenendo
  conto di metriche/peer/RSSI variabili: un solo tempo migliore non prova
  guadagno causale. Se nulla scatta, prova inconclusiva sul difetto reale.
  Nessuna PR/commit; installazione resta solo temporanea per collaudo.

### Esito candidata sync:144,81s e replay degli stessi annunci

- Completato transfer-sync-_m1rp0jz/run-bKZ2VIv4, channels-i_9lphn5:
  ZIP8.388.736byte, Upload200/exit0,144,81s(57,93kB/s), totale183,852s.
  Controllato ripristino reale: off/idle, servizio originale47fa6c73...,
  hash profili invariati, pacchetto/binario/override temporanei assenti,
  Wi-Fi fisso UUID atteso riconnesso. Nessuna nuova radio per l'analisi.
- Contro154,17s:−6,07%tempo; TCP883445/9307440byte ritrasmessi=9,49%
  contro10,44%, mediana cwnd ancora5. RSSI telefono−29 contro−30dBm.
  Stallo ACK campionato più lungo0,522s contro2,569s, non misura RF esatta.
  Elezioni7contro23, cambi indirizzo master/sync7/7contro20/16;
  durate sync telefono111,642s,peer8e...30,860s,peer7e...2,000s.
  Priorità telefono521 anziché513 e storia peer diverse: non è un A/B
  controllato e non prova beneficio throughput causale della patch.
- Due grandi salti applicati a upload+17,959/+81,212s sono prime acquisizioni
  da8e... dopo cambio sorgente, priorità523/527 superiore al telefono521.
  Non sono il vecchio aggiornamento da peer seguito appena declassato a65.
  Scarti interi−41301/−59138TU, fase ciclica−341/+254TU modulo1024;
  gli scarti interi non sono attese fisiche di quella durata. Nel live62frame
  SYNC abbinati di8e...own-master65, nessuno con quel peer seguito prima
  dell'ingresso e nessuno applicato: l'innesco preciso qui non è avvenuto.
- Per verificare il difetto senza un'altra prova radio: ricostruiti i campi
  management di1206ingressi accettati della prova154s, abbinamento nlmon/
  diagnostica uno-a-uno per sorgente, tempo e compatibilità contatore;
  scarto massimo5,896ms. Replay negli stessi core reali originale/candidato.
  Ai3istanti53311884/87435030/127574980us, originale riproduce esattamente
  gli errori registrati−71021/−104207/−143369TU e aggiorna il clock;
  candidata, con identici ingressi e sorgente prima selezionata, riseleziona
  telefono e non applica il clock del peer declassato. Tutti4gli ingressi
  candidata con peer prima seguito ora65 esclusi. Check assert passato.
- Replay ricostruisce solo management, non PCAP RF completo né dati/driver/
  perdite/feedback; timer ideali e gate RSSI disabilitato su ingressi già
  accettati. Prova la correzione delle decisioni, non la velocità. Report e
  check ripetibili nel gruppo privato: analysis.md/json, analyze.py,
  replay/prepare.py,replay.rs,check.py,analysis.json. Nessun payload personale.
- Prossimo punto mirato: fase all'acquisizione di un nuovo master e validità
  temporale dei peer scelti. Non forzare telefono/MAC o cambiare parametri
  TCP/guardia/canale alla cieca. Candidata ancora solo sperimentale, nessuna
  installazione permanente, commit o PR. Modifiche preesistenti conservate.

### Router reale sul44: collegamento confermato e probe nativo predisposto

- L'utente ha collegato il PC al router configurato sul44. Lettura reale:
  station wlp2s0 su5220MHz/44, larghezza80MHz, segnale−50dBm al primo
  controllo. GlobalIT e dominio hardware99PASSIVE-SCAN restano, ma il
  canale44 non mostra noIR mentre associata. Questo non prova ancora che
  il permesso sopravviva al distacco necessario al backend esclusivo.
- AirDropoff, originale attivo, profili ancora6 invariati. Nuovo UUID del
  router salvato privatamente: non riconnettere il precedente Starlink.
  Preflight e hash in channel44-router-amnvum_t/preflight.json sotto/tmp.
- Preparato probe.py privato: attesaInvio e sudo locale, verifica rete44,
  AirDropoff/interfacce assenti, distacco station e lettura vincoli. Se
  noIR riappare, salta join; altrimenti singolo join IBSS nativo5220HT20,
  BSSID AWDL/beacon10000TU come backend, verifica canale/tipo e rimozione.
  Non trasferisce file e non richiede iPhone. Nessun TOML/servizio/pacchetto
  modificato; IPv6 disabilitato soltanto sull'interfaccia effimera eliminata.
- Solo programma letterale Bash passato a sudo, nessun file del checkout
  eseguito/importato da root. Log scritti da tee non privilegiato. Trap
  errore/segnali ripristina managed/autoconnect originari e UUID router;
  controlla connessione reale, flag e interfaccia rimossa, segnala errore70
  se ripristino incompleto. Lock impedisce doppio avvio di questo probe.
- Check senza radio passato per noIR, join riuscito/rifiutato, errore con
  rollback e percorsi con spazi; Bashsyntax e gitdiff--check passati.
  Launcher predisposto in stessa directory: il risultato radio resta da
  raccogliere dopo il consenso locale conInvio. Nessuna PR/commit.
- Aperto terminale «AirDrop — verifica canale44», log conferma attesaInvio
  prima di sudo/radio. Nessun distacco avviato durante la preparazione.

### Esito router44: noIR ricompare al distacco; prova coesistenza preparata

- channel44-router-amnvum_t concluso exit0: prima5220MHz consentita;
  dopo station unmanaged/down compare noIR su44. PROBE=blocked_after_disconnect,
  join correttamente saltato, RESTORE_OK=1. Non è un join fallito né un
  trasferimento provato: conferma che il permesso osservato da associata
  non sopravvive al distacco in questa configurazione.
- Postflight reale: stesso UUID del router attivo su5220MHz, managed=yes,
  autoconnect=yes, AirDropoff, nessuna awdl0/owlyibss0; servizio originale
  ancora attivo, hash originale e due TOML identici al preflight. Analyzer
  assert passato; analysis.json/postflight.json salvati nel gruppo privato.
- Preparato controllo nativo successivo channel44-concurrent-rn4lbhtv:
  station mantenuta associata, nuova IBSS con MAC locale distinto sullo
  stesso44, un solo joinHT20/beacon10000/BSSIDAWDL come nel backend.
  Verifica station ancora collegata44 e IBSSjoined44 nello stesso intervallo;
  rimuove l'interfaccia effimera e riconnette UUID iniziale se necessario.
  Nessuna modifica alla station prevista, nessun cambio TOML/servizio,
  nessuna installazione o trasferimento. IPv6 solo su interfaccia effimera.
- La combinazione managed1+IBSS1 su un canale è dichiarata dal wiphy;
  la prova serve a verificarla realmente. L'eventuale successo non prova
  dati/ACK, injection, ricezione management o compatibilità backend shared:
  l'adattamento di Owly resta successivo alla prova nativa, se giustificato.
- Privilegi come prima: solo Bash letterale via sudo, niente codice da
  checkout importato/eseguito da root; log non privilegiati. Sei casi mock
  passati (noIR, interfaccia rifiutata/up rifiutato, join rifiutato, coesistenza,
  perdita station e riconnessione), percorsi con spazi e sintassiBash passati.
  Terminale guidato predisposto, attesaInvio/sudo locale prima della radio;
  iPhone non necessario. Nessuna PR/commit o modifica permanente.
- Aperto «AirDrop — coesistenza sul canale44»; log conferma attesaInvio.
  Preflight privato conferma stesso router44/off e nessuna interfaccia prova.

### Coesistenza44 breve: EBUSY prima del join; confronto P2P predisposto

- channel44-concurrent-rn4lbhtv concluso exit0, PROBE=interface_up_rejected:
  creazione IBSS, MAC distinto e preparazione riusciti; `ip link set
  owlyibss0 up` restituisce «Device or resource busy». Nessun join5220 né
  trasferimento eseguito. Per questo la prova dura pochi secondi: non è
  un timeout AirDrop né un rifiuto HT20/80MHz durante il join.
- RESTORE_OK=1, RECONNECT_NEEDED=0. Verifica reale: station ancora collegata
  allo stesso router44, flag managed/autoconnect originali, interfaccia
  temporanea assente, off, daemon originale attivo, tre hash invariati.
  Postflight e analyzer assert salvati nel gruppo privato; check passato.
- Osservata anche interfaccia P2P-device non-netdev. La combinazione wiphy
  managed1+IBSS1 totale2 non include P2P-device; le altre combinazioni
  includono P2P ma non IBSS. Il solo oggetto presente non dimostra running
  né causa EBUSY: lettura stato debugfs richiede sudo, non disponibile dalla
  sessione non interattiva; D-Bus wpa_supplicant rifiuta lettura non root.
- Consultati sorgenti ufficiali dello stesso kernel6.18.36:
  mac80211/iface.c check_concurrent_iface -> check_combinations,
  mac80211/util.c fill_ifcomb_params conta solo interfacce running;
  cfg80211 controlla che tutti i tipi rientrino nella stessa combinazione.
  mac80211/debugfs_netdev.c espone state; header installato conferma bit0
  SDATA_STATE_RUNNING. nl80211 start/stop_p2p_device confermati nei sorgenti.
  Copie in kernel/ del gruppo privato. Riferimenti ufficiali:
  https://raw.githubusercontent.com/gregkh/linux/v6.18.36/net/mac80211/util.c
  https://raw.githubusercontent.com/gregkh/linux/v6.18.36/net/mac80211/iface.c
  https://raw.githubusercontent.com/gregkh/linux/v6.18.36/net/mac80211/debugfs_netdev.c
  https://raw.githubusercontent.com/gregkh/linux/v6.18.36/net/wireless/nl80211.c
- Nuovo probe privato channel44-p2p-7is57hi7 riusa la prova nativa con
  confronto controllato: legge running P2P da debugfs e verifica identità
  wdev0x91/MAC/tipo. Stato mancante, non interpretabile o identità cambiata
  fanno saltare prima di modifiche. Primo up nello stato originale; solo
  se EBUSY e P2Pprima attivo, stop nativo P2P e secondo up sulla medesima
  IBSS. Verifica running0 e registra lo stato alla riuscita/errore del retry.
  Se up riesce prova il singolo join44 e la station ancora collegata.
- Cleanup rimuove IBSS PRIMA di riavviare P2P se inizialmente attivo;
  verifica running ripristinato e segnala errore70 se non lo è. Riutilizza
  ripristino rete/flag e log non privilegiati. Nessun file/profilo/servizio
  modificato, niente dati/trasferimenti; solo letterale Bash sotto sudo.
- Dieci casi mock passati, inclusi P2Pnon attivo, baseline già riuscita,
  stop rifiutato/autoriavvio, busy persistente, join rifiutato, annullamento,
  ripristino fallito segnalato e perdita station recuperata; paths con spazi,
  sintassi Bash e gitdiff--check passati. Prova reale ancora da eseguire con
  Invio/sudo nel terminale guidato. Nessuna PR/commit o modifica permanente.
- Aperto «AirDrop — confronto P2P canale44»; log conferma attesaInvio.
  Preflight verifica rete44, wdevP2P atteso e AirDropoff. Nessun nuovo
  comando radio eseguito durante la preparazione.

### Canale44: confronto P2P riuscito, IBSS e station simultanee

- channel44-p2p-7is57hi7 exit0, PROBE=concurrent_joined_44. Il confronto
  nello stesso setup mostra P2Prunning1/upIBSSEBUSY -> stopP2P/running0 ->
  up stessaIBSS riuscito con P2Pancora0. Poi joinAWDL5220HT20 accettato.
  Durante osservazione5s: station collegata44/80MHz e IBSSjoined44/20MHz,
  MACIBSS locale distinto12:63...; nessuna modifica dominio/EEPROM.
- La durata breve è prevista: sleep5 dopo il singolo join, nessun file
  trasferito né discoveryiPhone. Non è il fallimento immediato precedente.
  Due ostacoli separati ora osservati: distacco station ripristina noIR;
  station associata con P2Pattivo impedisce upIBSS. Qui preservare
  associazione e fermare P2P ha consentito il setup nativo sul44.
- Cleanup: IBSSrimossa prima di P2Pstart, P2Prunning1 verificato e registrato,
  RECONNECT_NEEDED=0/RESTORE_OK=1. Postflight reale conferma stesso router44,
  managed/autoconnect originali, P2Ppresente, off, originale attivo, hash
  daemon e due TOML identici. Postflight non-root non rilegge runningP2P:
  quel bit è verificato dal log privilegiato al termine del probe.
- Analyzer assert passato su ordine degli eventi, entrambe le interfacce,
  canali/larghezze e ripristino; analysis.md/json e postflight.json nel
  gruppo privato. Nessuna radio aggiuntiva durante analisi.
- Audit Owly0.4.1: shared() crea solo monitor/MACstation, exclusive() crea
  IBSS ma stacca station; OWLY_RX_MGMT apre socket suIBSS. Un semplice
  mode=shared nel TOML non riproduce la prova riuscita. Occorre variante
  sperimentale associata+IBSS con MACAWDL distinto e ripristino P2P tramite
  journal esistente (StepP2P e Ops start/stop ancora assenti). Riutilizzare
  setup/rollback e managementpatch, mantenere invariato profilo6.
- Limiti: ancora nessun monitor accanto alla coppia STA+IBSS, injection,
  management reale, ACK/dati o velocità provati sul44. Prossimo controllo
  minimo è completare setup con monitor, poi discovery e ZIP tramite backend
  sperimentale; non dichiarare risolta lentezza né compatibilità AirDrop.
  Nessuna nuova variante installata, commit/PR o cambi permanenti.

### Canale44: primi trasferimenti riusciti con router a20MHz (31ottobre2026)

- Autorizzazione utente: completare i controlli necessari prima di perdere
  accesso al router con canale selezionabile. Nessun commit/PR richiesto.
  Gruppo privato `channel44-live-ve0jg64e`, sotto il laboratorio locale.
- Completato il controllo station+IBSS+monitor. Primo tentativo fermato da
  NetworkManager: il monitor non compare fra i suoi device; non era un
  fallimento dell'up radio. Corretta la sonda ignorando solo quel controllo
  NM, verificando invece presenza e up del monitor. Un altro tentativo è
  stato annullato prima delle modifiche perché la station era passata alla
  rete2.4GHz. Ultimo controllo MONITOR_READY=1, ripristino P2P verificato.
- Variante locale Owly0.4.1, opt-in `OWLY_QCA_SHARED_IBSS=1`: mantiene station
  associata5220, aggiunge IBSS HT20 con MAC locale distinto e monitor con lo
  stesso MAC AWDL; riusa journal e rollback delle interfacce esistenti.
  Controlla QCA9377/ath10k, frequenza, gateway e permesso TX sul primario44.
  Non modifica dominio radio, EEPROM o profilo6 della produzione.
- P2P fermato prima del daemon tramite unit temporanea; ExecStopPost rimuove
  prima monitor/IBSS e ripristina P2P anche dopo crash. Marker protetto in
  /run, verifiche running prima/dopo e ulteriore cleanup finale. Nessun
  file del checkout viene eseguito da root: il daemon proviene da pacchetto
  temporaneo installato in /usr/lib; i helper privilegiati sono letterali.
- Build release offline riuscita; 18 test ordinari injection passati.
  Nuovo check opt-in copre successo, errore monitor, IBSS rifiutata e canale
  sbagliato, compreso rollback; passato con Fixed attivo e disattivo.
  Check helper systemd su errori, marker/retry, ordine cleanup e percorsi con
  spazi passato; systemd-analyze verify passato sul servizio candidato.
- v3 usa Presence::Share; v4 aggiunge opt-in `OWLY_QCA_FIXED44=1`, presenza
  Fixed e richiesta no-ACK come nel profilo6 funzionante, sul44. Include la
  correzione sync-freshness precedente. Nessuna nuova dipendenza o API.
- Con station44/80MHz e IBSS44/20MHz: due tentativi ZIP Share senza nome
  del peer, nessun trasferimento iniziato. Prima prova esclusa perché utente
  non pronto; seconda confermata corretta, PC assente dalla schermata iPhone.
  Due sonde35s Share/Fixed sentono annunci iPhone ma rx_data resta0.
  Il cambio della sola presenza non ha risolto la scoperta a80MHz.
- Attenzione alla cattura monitor: le copie PACKET_OUTGOING dimostrano solo
  consegna locale al socket, non trasmissione o ACK via etere. Corretto il
  decoder affinché tx_failed sia null sulle copie outgoing, test passato;
  vecchi log conservati e interpretati con questa limitazione.
- Traccia ath10k80MHz:1215TX, solo vdev_id0. Traccia20MHz:1130TX vdev0 e
  6975TX vdev1. La mappatura dei vdev non è stata provata separatamente;
  il comparire del secondo vdev è coerente col traffico della nuova IBSS.
  Nessun overrun/drop nei buffer CPU; istanza rimossa e stato trace/debug
  globale identico prima/dopo. Le tracce registrano metadati, non payload.
- Ipotesi dal sorgente del kernel6.18.36: monitor_start_xmit usa il chandef
  del contesto canale, che può essere più largo dell'IBSS, e verifica
  cfg80211_reg_can_beacon. Se i secondari rimangono noIR, può scartare prima
  del driver restituendo comunque NETDEV_TX_OK. Questa specifica decisione
  non è ancora tracciata: è una spiegazione da verificare, non causa provata.
  Riferimento: https://raw.githubusercontent.com/gregkh/linux/v6.18.36/net/mac80211/tx.c
- Su richiesta l'utente ha impostato router44/20MHz; verificato anche sul
  PC prima del test. Stesso pacchetto v4, nessuna ricompilazione tra prova
  Fixed80 e Fixed20. Risultati del medesimo ZIP con hash verificato:

  | Gruppo | Caricamento PC→iPhone | Invio totale | Ritrasmissioni TCP campionate |
  | --- | ---: | ---: | ---: |
  | transfer-qca44-ok3dswvp | 8,65s | 17,080s | 0,206% |
  | transfer-qca44-niabxdjf | 9,18s | 14,494s | 0,249% |
  | transfer-qca44-7jp50e2t | 9,44s | 15,987s | 0,283% |

- Entrambi HTTP200, circa0,87–0,92MiB/s di file. Primo con traccia driver,
  secondo senza; RSSI mediano −40/−41dBm, cwnd mediana33,5/40. Le percentuali
  TCP derivano dall'ultimo campione disponibile, non da contatori finali.
  Tempi di consenso/scoperta distinti dal caricamento. Un miglioramento
  ripetuto rispetto ai111–154s storici, ma non un confronto isolato del solo
  canale: cambiano anche associazione, larghezza e modalità radio.
- Il secondo test non include ricezione: utente conferma di NON avere
  rimandato lo ZIP. Nessun file ricevuto e nessun errore di ricezione
  dimostrato. Preparata ripetizione guidata per verificare il ritorno.
- Analyzer offline con assert su risultato, ripristino, SHA ZIP, HTTP200,
  flusso TCP e annunci5220 passato su entrambi; conservato come
  `channel44-live-ve0jg64e/analyze-transfer.py`, analysis.json nei gruppi.
- Postflight di entrambi: originale attivo, tre hash originali invariati,
  pacchetto/override sperimentali rimossi, radio off, interfacce temporanee
  assenti, router44/20MHz ripristinato. La funzione non è ancora attiva nel
  widget né installata permanentemente; TOML originali ancora sul6.
- Artifatti privati, sorgenti e log sono stati spostati senza eliminarli
  in `.airdrop-local-lab` per esaurimento quota /tmp; vecchio percorso
  `/tmp/end4-airdrop-speed` conservato come symlink. Directory0700 con
  .gitignore `*`, esclusa da Git. Target Cargo separato generato localmente.
  Patch v4 privata `owly-qca-shared44-fixed.patch`, SHA256
  `608d85dc1777f5dccf30d2c14ac9ec2f17d1f425f33e7bca00a37a858f366512`.
  Manifest e pacchetto verificati conservati nello stesso gruppo; nessun
  binario/log/dato personale aggiunto alla modifica distribuibile.
- Limiti prima di rendere permanente il44: verificare iPhone→PC, proteggere
  esplicitamente avvio con larghezza diversa da20MHz, gestione portabile del
  P2P (wdev sperimentale locale), perdita/cambio AP durante l'uso e rollback.
  Dipendenza attuale da AP associato sul44; non promettere stesso risultato
  su hotspot/Starlink o con radio scollegata. Nessuna modifica permanente
  del backend o della configurazione del widget durante questi controlli.
- Terza prova `transfer-qca44-7jp50e2t`: invio ZIP riuscito9,44s, totale15,987s.
  Ricezione funzionale confermata: foto770860B salvata, risposta HTTP200;
  poi arrivato anche lo ZIP8388736B. Ricezione→salvataggio12,233s, HTTP200
  e SHA256 identico all'originale. Analyzer con percorso del file contenente
  spazi passato: `python3 channel44-live-ve0jg64e/analyze-transfer.py
  transfer-qca44-7jp50e2t '/home/xlini/Downloads/AirDrop/airdrop-speed-8MiB 20.zip'`
  dalla radice del laboratorio. analysis.json contiene anche il ritorno.
  Foto e ZIP rimangono nella directory utente, senza copie nel repository.
- Cleanup terzo test concluso e postflight reale con assert passato: daemon
  originale attivo e hash/TOML invariati, off, pacchetto/override/marker
  assenti, nessuna interfaccia effimera, medesimo router44/20MHz collegato.
  Bit running P2P verificato dal helper privilegiato finale, non riletto
  dal postflight non-root. postflight.json conservato nel gruppo privato.
- Annunci iPhone durante i primi due upload: soprattutto15slot su16 sul44,
  contro soprattutto5slot su16 sul6 nelle prove144,81/154,17s. Sono finestre
  annunciate, non misura di airtime o prova della sola causa del guadagno.
  Il segnale sul44 è anche meno forte rispetto alle prove6 (−40/−41 contro
  −29/−30dBm): il guadagno non coincide con RSSI migliore.
- Esito funzionale:44/20MHz ora verificato in entrambi i sensi. Rimangono
  da implementare i controlli della larghezza e il ripristino portabile già
  elencati prima dell'uso permanente. Esperimenti e misure salvati localmente;
  widget e installazione ordinaria restano sul backend originale.

### Ripresa del31ottobre: candidata protetta, solo test offline e preflight

- L'utente ha chiesto di consolidare44/20 e continuare prove/test, senza
  branch/commit/PR/push. Ha confermato che il router44/20 non è più disponibile.
  Rete reale attuale `ScapeWiFi STAR 5GHz`,100/80MHz, center5530;44noIR.
  Il precedente risultato bidirezionale veloce resta acquisito e non viene
  sostituito con nuovi tentativi sul6.
- Nuova copia nel gruppo privato `channel44-guarded-20261031`: vecchi sorgenti,
  patch e pacchetto v4 restano intatti. Nessuna installazione o modifica radio.
- Guard candidata su frequenza5220, larghezza20MHz nota, center5220, BSSID,
  QCA9377/ath10k, permesso TX, combinazione STA+IBSS+monitor e gateway.
  P2P individuato via dump nl80211 sul phy corretto, senza wdev fissato;
  reale0xa6/166 confermato dalla query nativa e da iw, invece del vecchio0x91.
  Running richiede debugfs mac80211 con voce unica, fail-safe se ambiguo.
- Stop P2P e identità originale registrati nel journal prima delle modifiche;
  riavvio soltanto se inizialmente attivo e ancora stesso wdev+MAC, dopo
  eliminazione monitor/IBSS. Stato inizialmente spento e oggetti sostitutivi
  lasciati invariati. Errori delete/start conservano il journal per retry.
- Supervisore esistente1s controlla AP/profilo NM/canale/larghezza/permesso
  TX/P2P/IBSS e segnala Lost; il servizio chiude la lease ed esegue down.
  Cleanup non richiama la vecchia rete se scelta utente cambiata/disconnessa.
  Poll non atomico con roaming, nessuna promessa di stop istantaneo.
- Corretto un errore osservato nel servizio: prima ignorava down fallito
  nella risposta Release. Ora errore NoRadio al chiamante e recovery pending
  nel motivo LastEnd/idle. Stato idle significa nessuna lease; integrazione
  widget dovrà mostrare il motivo di recovery, non garantire ripristino.
- Passati35 test libreria,18 ordinari injection,12 servizio su bus privato;
  matrice fake35 scenari con PresenceFixed e Share, inclusi rifiuto iniziale
  senza mutazioni, errori setup/rollback, crash/retry, sostituzione P2P e
  cambi AP/rete/width. Preflight reale di sola lettura rifiuta correttamente
  l'attuale100/80. Nessuno stop P2P/setup IBSS/trasferimento reale nuovo.
- Build release offline e patch dry-run passati; Cargo.lock invariato.
  Patch incrementale su v4, binario, manifest/hash, README, checks.json,
  postflight.json e log conservati nel nuovo gruppo privato. Niente nuovi
  rate, BlockAck o prove sulla causa80; l'ipotesi resta non verificata.
- Postflight: AirDropoff, daemon originale attivo, tre hash originali
  invariati, marker/override/pacchetto diagnostici e interfacce prova assenti.
  Widget invariato e candidata NON installata. Non eseguire launcher v4
  col vecchio wdev, né combinarne helper P2P con il nuovo journal. Serve un
  nuovo launcher/pacchetto che recuperi il journal con la candidata prima
  del ritorno all'originale; nessuno preparato in questa sessione.
- Pendenti hardware quando disponibile AP44/20: P2P nativo privilegiato,
  setup/teardown/crash/cambio AP reali e ZIP nei due sensi con SHA256;
  soltanto dopo integrare nel widget. Modifiche preesistenti conservate.

### Nuova priorità: canale44 senza router, diagnosi regolamentare e ACPI

- L'utente chiede esplicitamente di concentrare il lavoro sull'autonomia
  dal router per usare il44. La variante shared associata non soddisfa
  questo obiettivo; integrazione widget non è il passo prioritario attuale.
- Gruppo privato `channel44-autonomous-20261031`: ANALISI.md conserva la
  valutazione, sette sorgenti ufficiali6.18.36 verificate contro hash Git
  blob (sources.json), due fonti kernel della precedente raccolta, snapshot
  reale e messaggi di inizializzazione/Paese filtrati. Nessuna nuova radio.
- Boot reale: EEPROM regdomain0x6c, Country alpha2 00, profilo world roaming.
  In seguito si vedono aggiornamenti da Country IE IT; quei messaggi non
  attestano scrittura EEPROM. GlobalIT attuale non elimina il profilo
  custom99passivo, né44NO_IR, con questi driver/configurazione.
- Sorgenti: IBSS e monitor TX verificano entrambi il permesso beaconing;
  il solo monitor o rimozione del guard applicativo non superano il blocco.
  Beacon hint normale richiede BSS ESS, non i messaggi action AWDL. Eventuale
  AP esterno senza associazione lascerebbe comunque una dipendenza dall'AP.
- Il relaxNO_IR generico non copre IBSS/monitor ed è disabilitato. Nessun
  parametro modulo ath permette il percorso cercato. Database e firma
  installati integri (pacmanQkk25/0); errore DB al boot non basta a dedurre
  il problema attuale. Nessun aggiornamento/initramfs cambiato alla cieca.
- Verificata sorgente alternativa Paese ath10k: metodo ACPI WRDD prima del
  fallback a hw_eeprom_rd. Sudo non autenticato: aperto terminale guidato
  di sole letture; l'utente ha completato il controllo, result0. Tutte le
  8tabelle DSDT/SSDT hanno lunghezza/checksum validi e zero nomi WRDD.
  Nessuna valutazione AML o tabella grezza salvata. Bootstrap letterale
  legge da sysfs e abbandona gruppi/GID/UID prima di caricare il decoder.
- check-platform.py --self-test passato su6tabelle valide, firme/lunghezze/
  checksum/troncamenti errati, dato assente vs sconosciuto, esclusione
  tabelle estranee, percorsi con spazi e ordine drop privilegi/decoder.
- Individuato ramo nativo CONFIG_ATH_REG_DYNAMIC_USER_REG_HINTS: potrebbe
  recepire il Paese realeIT senza AP, previa valutazione/validazione. Richiede
  CFG80211_CERTIFICATION_ONUS/EXPERT, non abilitati nel kernel corrente.
  Kconfig ne limita l'impiego a sistemi/Paesi/schede verificati. Non attivato
  e non dichiarato funzionante sulla QCA9377; poi compilato separatamente
  dopo il chiarimento, senza caricarlo (seguito sotto).
- Chiesto chiarimento sul vincolo preesistente in CONTESTO-AIRDROP.md che
  vieta cambi dominio/EEPROM/aggiramenti: includere lo studio separato di un
  driver che recepiscaIT, conservando database firmato, potenza e DFS, non
  equivale ad autorizzarne installazione o caricamento. Risposta acquisita:
  «Sì, valutiamo la variante del driver per IT», solo studio/build separati.
- Originale attivo/AirDropoff, rete100/80, modifiche preesistenti preservate.
  Nessun modulo/dominio/servizio/rete/configurazione modificati, nessuna
  nuova prova sul6, branch/commit/PR/push. Obiettivo autonomo non raggiunto;
  motivo specifico del blocco80 ancora ipotetico e distinto.

### Seguito autorizzato: build separata ath originale e QCA9377/IT

L'utente ha autorizzato la valutazione del driver per IT reale, senza
installazione/caricamento. In channel44-autonomous-20261031/driver sono
conservati README, due moduli ath.ko, patch, configurazioni/delta, log, check
C e manifest con hash.17 sorgenti ufficiali del tag6.18.36 verificate;9
Kconfig mancanti degli header distribuiti recuperati dallo stesso tag.

La patch regd.c limita l'helper del percorso nativo a PCI168c:0042/IT su
tutti i quattro richiami, mantiene Country IE ordinari e controlli nativi.
Non modifica EEPROM, freq_reg_info, potenza/DFS, profilo CUSTOM/STRICT o DB.
Nella copia privata EXPERT/CERTIFICATION_ONUS/ATH_REG_DYNAMIC_USER_REG_HINTS
ON, DB firmato/chiavi kernel ON, CERT_TESTING/RELAX_NO_IR/CELLULAR_HINTS OFF.

Prima compilato stock con gli header preparati originali; olddefconfig per
IT non aggiorna da solo autoconf per build esterna. Controllo finale ha
scartato quel primo risultato e imposto syncconfig, pulizia dei soli oggetti
IT e ricompilazione completa: CC/MODPOST/link/BTF passati. Macro native
verificate anche negli header generati. Check C compila la funzione reale
e verifica filtro hardware/Paese, CONFIG spento e Paese nativo bloccato,
più presenza dei quattro richiami; passato. Self-test ACPI ripassato.

Stessi18 export e vermagic6.18.36-1-lts, nessuna prova ABI durante esecuzione
(MODVERSIONS spento).16 differenze di valori attivi nella configurazione,
comprese indisponibilità bindgen/Rust e default EXPERT: review pendente prima
di hardware. Moduli non firmati e non load-ready. Nessun modulo caricato,
nessun pacchetto o launcher di installazione. Patch SHA256
7756cfea70f5345356a09613b2f807947d2cb62122c5f537995d8c2486a7d6af;
modulo IT SHA2560657cd83bad9337afa908dd66f8b0c420a07a7c8dd0ad07e1d6713f128b32bad.

Postflight: rete100/80,44NO_IR, P2P0xa6, AirDropoff/originale attivo; cinque
hash header/config sistema e tre hash Owly identici, tainted0. Nessun cambio
Paese/rete/radio/servizio, test6/44 o modifica widget. Nessun branch/commit/PR/push.

Passo successivo tecnico: review config/ABI/firme e piano di ripristino
locale senza rete prima di richiedere un test temporaneo hardware, perché
scaricare ath/ath10k interrompe Wi-Fi. Studio/build non ne autorizzano il
caricamento. Poi verificare notifier IT con station senza AP (globalIT già
presente non basta),44/20, IBSS/monitor, ZIP bidirezionale/hash, cambi rete
e ripristino. Autonomia44 ancora non verificata; ipotesi80 ancora distinta.

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
