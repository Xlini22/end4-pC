# Glassy UI: sfondo live in Hyprland

## Correzioni candidate offline (16 novembre 2026)

Su richiesta dell'utente preparata la patch incrementale
`patches/native-glass-safety.patch`: buffer/formati/rilascio, ripristino GL e
timeout del contrasto, invalidazioni e clear limitati al danno delle Impostazioni.
Dettagli e controlli CPU nel [rapporto della candidata](native-glass-safety-candidate-2026-11-16.md).
Solo sorgenti separati e test: nessun nuovo binario o caricamento. R35 resta
in quarantena; la causa delle schermate nere non è dichiarata risolta.

## R35 rimossa su richiesta (16 novembre 2026)

Indagine successiva sui tre nuovi blocchi riferiti, con log dei boot e analisi
CPU del trascinamento: [rapporto r35](native-glass-r35-freeze-investigation-2026-11-16.md).
Confermati costi aggiuntivi nel percorso Impostazioni; causa precisa dei freeze
non accertata. Nessuna nuova installazione o modifica del rendering.

Dopo il nuovo accesso è stata verificata r35 caricata. L'utente ha poi richiesto
«togli subito il plugin»: il binario operativo è stato spostato reversibilmente
in `hyprglass.so.quarantined-1794847246327774723`, con record di hash e motivo
nella directory `~/.local/share/end4-pC/native-glass/`. Il percorso di caricamento
è ora assente. Nessun unload a caldo: la build già mappata resta attiva fino al
logout; al prossimo login il loader userà il percorso Quickshell. Registratore
verificato inactive/disabled prima della rimozione. Nessuna modifica a QML,
effetti, driver o clock.

## R35 installata per il prossimo accesso: satinatura parziale e sfarfallio (16 novembre 2026)

L'utente riferisce sfarfallio assente nel percorso Qt, resa peggiore senza plugin
e prestazioni delle Impostazioni peggiori con r34. Richiede la reintroduzione
del plugin preservando effetti e prestazioni. Non è una misura controllata né
identifica la causa dei blocchi dell'intero sistema.

Individuati due difetti nella pipeline nativa:

- R34 copia lo sfondo grezzo su tutto `m_frostFramebuffer`, poi sfoca solo il
  rettangolo danneggiato. Fuori da quel rettangolo i precedenti pixel filtrati
  sono sostituiti da pixel grezzi. Anche i quattro campioni del darker possono
  leggere valori filtrati o grezzi a seconda del danno del fotogramma.
- Il passaggio orizzontale del blur usa lo stesso scissor del passaggio verticale,
  senza aggiornare le righe di supporto lette dal secondo passaggio.

R35 conserva il risultato satinato in un buffer persistente e usa un buffer
grezzo separato, riutilizzato per layer. La copia del grezzo è limitata al danno
più il supporto del kernel, mantenendo il mapping del blit completo. Il primo
passaggio aggiorna anche le righe richieste dal secondo. Cambiamenti di crop,
posizione, dimensioni, raggio, formato o bounds invalidano il riuso e aggiornano
l'intero materiale richiesto. Un periodo senza materiali satinati invalida la
cache. Il buffer aggiuntivo viene rilasciato con gli altri framebuffer.

Restano crop a capacità di 64 texel, frost a risoluzione ridotta quando previsto,
Gaussiane a tap accoppiati, aggiornamenti parziali e bande da 128 pixel.
L'eccezione è il blur legacy con più iterazioni: per correttezza usa copertura
completa; intermedi parziali richiederebbero un ulteriore buffer persistente.
I profili enhanced attuali usano una sola iterazione.

Gli shader ottici sono byte per byte quelli r34: rifrazione, satinatura,
riflessi e formula del darker non sono stati ridotti. Il debounce Qt non è
stato portato al nativo. La correzione rimuove un difetto concreto dei buffer;
non prova che tutto lo sfarfallio sia eliminato. Il buffer grezzo aggiunge
memoria per layer e l'halo corretto aggiunge lavoro necessario; la copia
parziale riduce il traffico rispetto al blit completo. Nessun guadagno in FPS
o consumi è stato misurato sul portatile.

Compilazione completa `-O2`, senza debug, con `make -j1`, nice 10 e limite di
memoria virtuale del compilatore. Controlli senza GPU passati: frost con GL
simulato (kernel dimostrativo a tre tap, non validazione del GLSL), buffer e
rilascio, visibilità, profili, ottiche della barra, eventi barra, loader e
applicazione della patch a una base upstream pulita e fissata. Il primo test
degli eventi barra ha ereditato un limite virtuale incompatibile con la riserva
di V8; ripetuto senza quel limite, con heap Node di 128 MB e core dump disabilitati,
è passato. Non è un'evidenza di RAM di sistema esaurita. Nessun rendering,
nemmeno llvmpipe, compositor di prova o modifica a clock/driver.

Build separata e backup r34:
`~/.local/state/end4-pC/diagnostics/20261116-native-frost-r35/`.
SHA256 r35: `b4ef0de986d78e7027daa682cba08f06317ebb215d3ad660afb8afe0414142a7`.
ABI verificata contro Hyprland 0.55.4 corrente e intestazioni installate.

**INSTALLATA per il prossimo accesso**, dopo l'autorizzazione esplicita
dell'utente «installa». Il precedente tentativo era stato respinto dalla
revisione automatica per il vincolo di mantenerlo disattivato e i blocchi;
non era stato aggirato. La nuova installazione autorizzata conserva il manifest
precedente nella directory diagnostica e tutti i binari r34 in quarantena.
Manifest e binario r35 sono stati sostituiti atomicamente, scrivendo prima
`deferInstance` con la firma corrente. Hash e ABI verificati. Il controllo reale
`backend.py --ensure` risponde che il plugin è preparato per la prossima
sessione; plugin list `[]`, registratore inactive/disabled. Nessun caricamento
o scaricamento a caldo, riavvio o rendering di prova. Dettagli dell'installazione
in `installation.json` nella directory diagnostica.

La prova minima successiva proposta è un trascinamento di pochi secondi delle
Impostazioni dopo il nuovo login, verificando continuità del darker, clock nello
sfondo e resa degli effetti. Misure prestazionali e stabilità restano da valutare
in una fase concordata; nessun test di rendering separato.

## Nuova disattivazione richiesta dopo il rientro (16 novembre 2026)

L'utente conferma sfarfallio persistente con r34 e richiede di togliere il plugin
lasciando il resto. Confermato `hyprglass`, versione `end4-live-0.6.4-r34`, nella
sessione in esecuzione. Il solo binario installato è stato nuovamente spostato
in `hyprglass.so.quarantined-*`, con record di hash e motivo nella stessa
directory. QML, shader, diagnostica, configurazione e loader restano invariati;
registratore inactive/disabled. Nessun unload a caldo: il plugin già mappato
rimane nella sessione attuale fino a logout. Al nuovo accesso il file di
caricamento è assente e viene usato il percorso Quickshell.

## Reintroduzione preparata su richiesta dell'utente (16 novembre 2026)

L'utente ha richiesto di reintrodurre HyprGlass insieme all'aggiornamento
diagnostico. Ripristinata su disco la build r34 con SHA256
`a48592e2a25730538c618f5d7a0d0e89431181771f4870ca2889ec6a65520103`,
verificata contro manifest e ABI di Hyprland 0.55.4. Conservata la copia
originale in quarantena; nessuna ricompilazione o modifica del codice nativo.

Il manifest contiene `deferInstance` con la firma del compositor attuale.
Il loader rifiuta il caricamento in quell'istanza, anche dopo reload della
shell; resta bloccato anche se la firma non è disponibile. Una nuova sessione
Hyprland con firma diversa può caricare la build dopo i controlli ABI/hash.
Verificato realmente che `backend.py --ensure` riporti il rinvio e plugin list
resti `[]`. Nessun load/unload a caldo, logout o riavvio avviato dall'agente.

Applicata la patch di osservazione del darker: `settings glassStatus` espone
profilo e stato del debounce Qt quando il materiale è caricato. Nello stato
osservato Impostazioni era chiuso e `darker: null`; non è una verifica del
congelamento durante il trascinamento. Il debounce Qt non modifica il darker
nativo di r34. La comparsa dell'orologio nel vetro e lo sfarfallio vanno
verificati separatamente dopo il nuovo accesso; nessun difetto dichiarato risolto.

Registratore ancora inactive/disabled; nessun test separato di rendering,
compositor di prova, modifica di driver o clock. Backup dei QML precedenti,
manifest originale e record dell'operazione in
`~/.local/state/end4-pC/diagnostics/20261116-native-reintroduction/`.
Controlli: loader con IPC simulato e diagnostica su copie temporanee.

## Contenimento dopo ulteriori blocchi (15 novembre 2026)

Dopo ulteriori schermate nere riferite dall'utente, il servizio
`end4-freeze-recorder.service` è stato fermato e disabilitato e il comando
`run` del profiler è nuovamente bloccato prima di qualsiasi operazione.
Il plugin installato è stato rinominato reversibilmente in
`~/.local/share/end4-pC/native-glass/hyprglass.so.quarantined-1794749565745448853`;
un file `quarantine-*.json` nella stessa directory ne conserva hash e percorso.
Il loader non lo caricherà al prossimo accesso. Nessuno scaricamento del
plugin o riavvio del compositor è stato eseguito nella sessione corrente.
La verifica delle mappe ha mostrato r34 dal percorso installato, senza
build del profiler o LD_PRELOAD diagnostico nella sessione principale.
Non è stata identificata la causa dei blocchi; queste misure rimuovono
componenti sospetti e non costituiscono una diagnosi né una garanzia.

## Registratore Raspberry v2 (15 novembre 2026)

Il servizio `end4-freeze-recorder.service` usa `scripts/glass/record-freeze.py`.
La raccolta SSH ora include gli stessi contatori CPU/DRM per processo della
modalità locale, identificatori della sessione dei processi grafici e fino
a 32 stati dei thread ogni cinque secondi. Nessuna interrogazione periodica
di Hyprland via IPC, né modifica dei clock o delle impostazioni GPU.

Un secondo lettore del journal conserva eventi di Hyprland, Quickshell,
SDDM, logind, systemd e oomd. Si raccolgono anche stderr della sessione SDDM
e log dei due tentativi più recenti del profiler, con letture limitate a
64 KiB per file e per giro. Un record `sessions` ogni cinque secondi include
TTY, sessione attiva, leader e desktop tramite loginctl con timeout. Errori
o dati non leggibili restano espliciti. L'avvio registra versione/hash del
recorder, firmware, clocksource e watchdog; include anche la coda kernel
disponibile del boot precedente. Le impostazioni Glassy sono registrate
quando cambiano, senza esportare l'intero ambiente dei processi.

Sul Raspberry il ricevitore Python standard scrive `received_utc`, un clock
monotono locale e heartbeat indipendenti dal flusso del PC, con età dell'ultimo
dato e dell'ultimo campione. I record del PC hanno una sequenza crescente.
`receiver-end` indica se è arrivato un record finale e quanti byte di una
riga incompleta sono rimasti. Il ricevitore chiama fsync circa una volta
al secondo e alla chiusura; ciò non garantisce il comportamento della
cache del supporto in caso di perdita di alimentazione. File nuovi, privati
e mai sovrascritti. Gli orologi monotoni dei due host hanno basi diverse.

Controllo riproducibile senza rete o compositor:
`python3 tests/freeze-recorder-check.py`. Copre anche silenzio del mittente,
heartbeat autonomo, EOF parziale, timeout logind, sequenza e no-overwrite.
Il servizio aggiornato è stato attivato e i record v2 verificati realmente
sul Raspberry in `freeze-20261115T121611Z-e467569a.jsonl`.

Il ricevitore può osservare che il PC non invia più campioni, ma questo
non distingue da solo un hang del kernel da un problema di rete o del
recorder. Non può raccogliere un guasto prima dell'avvio di Linux; durante
un arresto completo del PC può conservare solo i dati già ricevuti. I log
non abilitano automaticamente recovery GPU, SysRq, panic o riavvii.

## Prova TTY fallita e avvii con schermo nero (15 novembre 2026)

Il comando `run` è stato sospeso durante l'indagine e poi corretto su
richiesta dell'utente, senza rilanciare la prova nella sessione grafica.
La prova delle 12:19 CET (`runs/1794741547912141589`) si è fermata con
`IndentationError` durante la compilazione della fixture Python generata,
prima dell'avvio del compositor e del caricamento dei plugin diagnostici.
Il self-test precedente compilava il runner esterno ma non questa fixture
interna: non copriva il percorso effettivamente fallito.

L'utente riferisce schermo nero anche prima del boot visibile, ripristino
dopo rimozione dell'alimentazione e pressione prolungata del tasto di
accensione, poi un blocco al login e un successivo accesso riuscito.
Il journal registra una sequenza regolare di riavvio alle 12:20:54–56;
il boot delle 12:27:57 si interrompe nei log alle 12:28:02. Il boot corrente
inizia alle 12:30:56. Questi dati non identificano la causa dei blocchi.

Il recorder Raspberry della TTY conserva 187 campioni dalle 12:17:26 alle
12:20:51 CET: GPU busy 100% in tutti, nessun processo Hyprland/Quickshell
rilevato, nessun nuovo timeout/reset GPU registrato. Il valore busy da solo
non dimostra lavoro GPU effettivo né identifica un guasto. Gli avvisi TSC
e PSP presenti nei boot successivi compaiono anche nel boot precedente.
Le evidenze sono archiviate sotto
`~/.local/state/end4-pC/diagnostics/20261115-black-screen/`.
Nessuna nuova prova grafica è stata eseguita durante questa indagine.

### Correzione della prova e recupero da TTY

La trasformazione della fixture conserva ora l'indentazione di tutte le
righe aggiunte. Il self-test esegue il vero blocco di generazione del runner
e compila anche la fixture finale, senza eseguirla; il comando `run` ripete
questi controlli prima della misura. Non sono cambiate le build GPU.
Questo corregge l'errore Python, senza risolvere né spiegare i blocchi.

Dopo logout, accesso alla TTY e scollegamento dell'alimentatore:
`bash ~/prova-glass`. Le due acquisizioni e lo scorrimento sono automatici.
Per tornare al desktop, anche se la prova termina con errore:
`bash ~/riprendi-desktop`. L'avviatore richiama
`scripts/hyprland/recover-session.py`: riusa una sola sessione Hyprland
rispondente, avvia Quickshell se assente e attiva la sessione con loginctl.
Se non esiste Hyprland, usa `start-hyprland`, come la voce desktop installata;
la configurazione locale avvia già Quickshell end4-pC.
L'opzione `--restart-qs` riavvia solo le istanze Quickshell di questa
configurazione sul display selezionato. Non termina Hyprland e non avvia
un secondo compositor se ne rileva uno bloccato o più sessioni ambigue.
Un blocco GPU/kernel che impedisce l'accesso alla TTY non è recuperabile
con questo script. Verifica senza modificare la sessione: `--status`.

```sh
python3 tests/recover-session-check.py
python3 tests/native-glass-stage-profile.py self-test
```

## Schermo nero durante il banco annidato (14 novembre 2026, sera)

Durante la preparazione della misura GPU per passaggio, l'utente ha riportato
schermo nero, mancata risposta anche a Ctrl+Alt+F3 e spegnimento forzato.
Il nuovo avvio parte alle 23:34 CET. Il registratore sul Raspberry conserva
campioni del precedente avvio fino alle **23:33:02 CET** nel file
`freeze-20261114T193756Z-1c8eb1b5.jsonl`.

Nell'ultimo campione erano presenti Hyprland principale PID 499174,
Quickshell principale PID 712017, Hyprland annidato PID 752654 e Quickshell
di prova PID 752735. Il Quickshell annidato era attivo sul thread CPU;
restavano circa 920 MiB di memoria disponibile. Nei record ricevuti non
compare un nuovo reset/timeout GPU o un OOM in quella fase. L'assenza di
questi messaggi non esclude un blocco del driver o del sistema: la raccolta
si interrompe senza un evento conclusivo che ne identifichi la causa.

Il compositor annidato separa processi e configurazione, **ma condivide GPU
e driver con il desktop**. Non costituisce isolamento da un blocco hardware.
La misura dei singoli passaggi non è completata; sorgenti e risultati
temporanei sotto `/tmp/end4-pass-profile` sono andati persi al riavvio.
Nessuna build diagnostica è stata installata. Le precedenti tracce kernel e
Wayland valide restano in
`~/.local/state/end4-pC/diagnostics/20261114-frame-pipeline/`.

Dopo il riavvio sono stati verificati r34 nella sessione principale e il
recorder remoto attivo. L'indagine prosegue con letture e revisione statica;
il banco annidato che ha preceduto il blocco non è stato rilanciato.
La ripresa delle misure hardware richiede una sessione di prova dedicata e
registrazione esterna, senza presumere che un processo annidato protegga
il desktop da errori del driver.

### Banco per passaggio ricostruito senza esecuzione GPU

`tests/native-glass-stage-profile.py` prepara una build di riferimento dalla
patch corrente e una seconda build con soli timer GPU asincroni. Non installa
plugin. I timer campionano un passaggio ogni otto, attendono la disponibilità
dei risultati senza bloccare e scartano i risultati invalidati dal driver.
Misurano cattura, blur esterno, copia della satinatura, blur della satinatura,
contrasto e rifrazione/composizione finale (che condividono uno shader).
`redirect-total` contiene le fasi di preparazione: non va sommato ai suoi figli.

Le build sono preparate in
`~/.local/state/end4-pC/diagnostics/20261114-frame-pipeline/stage-profile/`;
`build.json` conserva revisione upstream, hash della patch, ABI e hash dei
binari. Il riferimento è il codice della patch corrente, non una promessa
di identità binaria con il plugin già installato.

Sono passati compilazione delle due build, controlli dei buffer, confronti
software di 336 immagini native e 102 immagini Gaussian, più il controllo
senza GPU del profiler:

```sh
python3 tests/native-glass-stage-profile.py self-test
```

La misura hardware **resta da completare dopo la correzione del 15 novembre**.
Il comando `run` rifiuta un desktop
attivo e richiede una console `/dev/tty*`, recorder esterno attivo e connessione
al Raspberry. Avvia un compositor diretto, senza collegarsi a un compositor
padre. Ogni acquisizione crea una cartella persistente distinta sotto `runs/`;
i log vengono scritti lì durante la prova, non recuperati soltanto all'uscita.
Un'interruzione o un crash rende l'acquisizione non valida. La chiusura della
sessione desktop richiede l'intervento dell'utente.

## Priorità concordate il 16 novembre 2026

- Nuovo blocco completo durante il lavoro sul debounce, senza movimento del
  portatile: vedere `black-screen-investigation-2026-11-16.md`. Test di rendering
  llvmpipe ritirato e sostituito con soli controlli statici. La candidata
  `../patches/settings-darker-debounce.patch` è stata poi applicata alle 12:42
  CET dopo autorizzazione dell'utente alla prova nella sessione esistente;
  reload riuscito, riscontro visivo pendente. Nessun test di rendering separato.
- HyprGlass, inizialmente mantenuto disattivato per richiesta dell'utente, è
  stato poi preparato per il prossimo accesso su sua nuova richiesta, come
  descritto all'inizio del documento. Nessun reload nativo a caldo; confrontare
  stabilità, correttezza visiva e costo con il percorso Qt.
- Raccogliere il riscontro sulla patch del darker durante il trascinamento delle
  Impostazioni, applicata il 16 novembre; controlli senza GPU superati, esito
  visivo ancora non confermato. Dettagli in `../patches/settings-backdrop-stability.md`.
- L'indagine sulle schermate nere resta aperta: non attribuire il problema al
  plugin senza evidenze. Conservare anche l'osservazione dei blocchi muovendo
  soltanto lo schermo, con la base ferma. Nessuna nuova prova TTY o di carico
  nell'ambito di questi lavori; plugin e registratore restano disattivati.
- Riprendere il confronto prestazionale a batteria quando sarà opportuno;
  nessun beneficio del backend nativo va dato per acquisito.
- Completare il riordino dei commit e la verifica autonoma del branch Glassy
  descritti sotto, partendo dai controlli statici e software.

## Prossimi lavori: commit e autonomia del branch Glassy

Richiesta del 12 novembre 2026, da eseguire nella prossima fase:

- Inventariare tutte le modifiche non committate e creare commit coerenti,
  separando Glassy, diagnostica e modifiche delle altre funzionalità.
- Verificare e aggiornare `feat/enhanced-glassy`: deve contenere tutti i
  componenti, comportamenti, impostazioni, risorse, patch native e test
  necessari al Glassy, inclusi i dialoghi della sidebar destra.
- Preparare una base pulita aggiornata dal branch principale **originale di
  upstream**, distinguendola da `latest` e dal branch di integrazione locale.
- In un worktree separato, applicare a quella base **soltanto il branch
  Glassy**. Non usare altri branch locali o file non tracciati del checkout
  corrente. Risolvere eventuali dipendenze portando in Glassy il minimo
  necessario e documentandone la provenienza.
- Eseguire build e test usando solo file e patch di quel worktree: un binario
  nativo già installato o risorse rimaste nella configurazione utente non
  devono nascondere dipendenze mancanti. Verificare configurazione nuova e
  compatibilità con le impostazioni salvate.
- Controllare attivazione/disattivazione, profili e slider di Bar, Dock,
  Sidebar sinistra/destra, Impostazioni standard/Dashboard, Lockscreen e
  Terminale; includere hover, dialoghi, animazioni, rifrazione degli angoli,
  contrasto e comportamento in fullscreen. Eseguire i controlli software e
  poi la verifica visiva e delle prestazioni, anche a batteria.

Il criterio di riuscita è una configurazione riproducibile con la sola base
upstream aggiornata più Glassy. Conservare riferimenti dei commit di base e
feature, risultati dei test ed eventuali dipendenze riscontrate. Il checkout
della sessione desktop resta separato dalla prova; nessun ricaricamento a
caldo del plugin nativo. Ripristinare la raccolta sul Raspberry prima di
eventuali prove manuali relative ai crash.

## Crash del blocco schermo dopo una ricarica (14 novembre 2026)

Il report `~/.cache/quickshell/crashes/gn48ktzgot/report.txt` registra un
SIGABRT di Quickshell alle 03:33:16, durante la richiesta di blocco prima
della sospensione: `Tried to show lockscreen surfaces without active lock`.
Hyprland PID 254998 resta presente fino allo spegnimento ordinato delle
10:15:48, richiesto da TTY3 dopo il risveglio. Il successivo SIGSEGV nel
gestore della schermata di crash è un secondo errore, non la causa iniziale.
Questi dati non indicano un nuovo crash del plugin Glassy.

Il difetto è riprodotto in un **Hyprland separato senza plugin Glassy**, con
Quickshell in rendering software: blocco, ricarica con il lock sotto un
`LazyLoader` condizionato dal caricamento della configurazione, nuovo blocco.
Dopo la ricarica l'oggetto nuovo riporta `locked=false` ma `secure=true`:
la precedente acquisizione Wayland resta attiva senza essere trasferita.
Il blocco successivo fallisce con lo stesso messaggio fatale. Il report
`t1hgqjhot` delle 10:30 riguarda questa riproduzione isolata.

La lockscreen ora appartiene direttamente a `ShellRoot`, fuori dai loader
dipendenti da `Config.ready`. `PersistentProperties` conserva la richiesta
di blocco e i workspace originali durante la ricarica, prima della migrazione
dell'oggetto Wayland. Le mappe usano stringhe JSON: un oggetto JavaScript del
vecchio motore QML non è trasferibile al nuovo motore. La ricarica deve
conservare la sessione bloccata, senza introdurre uno sblocco transitorio.

`python3 tests/session-lock-reload-check.py` esercita i blocchi di produzione
in un compositor separato: tre ricariche da bloccato, tre sblocchi/nuovi blocchi
e conservazione dei workspace. Il caricamento QML e lo scorrimento software
passano anche con la lockscreen nella nuova posizione. Nessuna sospensione o
prova di blocco del desktop principale è stata eseguita. La verifica prolungata
di sospensione/risveglio nella sessione reale resta da fare.

Report e riproduzioni sono conservati privatamente in
`~/.local/state/end4-pC/diagnostics/20261114-lockscreen-crash/`.
Il Raspberry continua a ricevere i log. Una nuova registrazione locale delle
prestazioni, a bassa priorità, dura un'ora di attività dopo questa verifica;
il percorso è in `performance-path.txt` nella cartella diagnostica sopra.

## Carico persistente anche con darker spento: driver Qt (14 novembre 2026)

La sessione usa r32; a batteria la GPU rimane in `auto`, con SCLK 200 MHz e
MCLK 400 MHz. L'oscuramento della barra è zero e automatico spento. Settings
conserva automatico attivo, ma la relativa finestra è chiusa: non confondere
questa configurazione con un test di tutti i profili automatici spenti.

Il precedente intervento aveva forzato `QSG_USE_SIMPLE_ANIMATION_DRIVER=1`
nella prima parte di `shell.qml`. Il sorgente di
[Quickshell, launch.cpp](https://raw.githubusercontent.com/quickshell-mirror/quickshell/master/src/launch/launch.cpp)
segnala esplicitamente il costo di questa modalità con molte finestre:
ridisegni superflui anche sugli altri window, collegati a QTBUG-126099.
La registrazione mostra lavoro regolare in tutti i thread QSG, compresi quelli
dei popup conservati dopo la chiusura. La correlazione non attribuisce al darker
il lavoro CPU né dimostra da sola la causa di tutti i precedenti lag.

Rimossa la forzatura e riavviato **solo Quickshell**, con il driver Qt standard;
Hyprland resta PID 254998 e il plugin caricato resta r32 con lo stesso handle.
Glassy, ottiche, oscuramento e preferenze dell'utente restano attivi/invariati.
Sono rimossi anche il walker QML e i comandi IPC temporanei delle prove.

Con alimentatore collegato e GPU sempre a 200 MHz, prima del riavvio la misura
stabile della stessa scena rileva circa 64–71% di un core per QS e 253–254 ms
GPU/s. Dopo l'avvio, tre finestre di cinque secondi rilevano **14.4–15.6%** e
206–208 ms GPU/s. Hyprland passa da circa 13–17% CPU a 8.8–9%, mentre il suo
tempo GPU resta circa 387–388 ms/s rispetto a 391–392: non attribuire alla
correzione un forte risparmio GPU del compositor. Questi sono contatori di
risorse, non FPS. La misura a batteria precede quella con alimentatore e non
va confrontata senza distinguere le due condizioni. La verifica finale
manuale a batteria è ancora richiesta all'utente; dopo la misura la sessione
è entrata nella schermata di blocco, senza interventi per sbloccarla.

Dopo il riavvio e la correzione del blocco schermo, una nuova misura a batteria
con GPU ancora in `auto` a 200 MHz rileva QS circa 22% CPU e Hyprland 13.3%
(venti campioni). In una finestra di cinque secondi il carico GPU è circa
207 ms/s per QS, 333 ms/s per Hyprland e 9 ms/s per Code. Gli altri client
GPU non risultano dominanti in questa finestra. È una scena di una nuova
sessione: questi numeri non misurano gli FPS e non sostituiscono il confronto
visivo dell'utente a batteria.

Misure e risultati sono conservati privatamente anche in
`~/.local/state/end4-pC/diagnostics/20261114-animation-driver/`.
Dati temporanei: `/tmp/end4-qml-animation-ab.json` (prima, valori riletti dal
processo) e `/tmp/end4-animation-driver-after.json` (dopo). La prima acquisizione
`end4-animation-driver-before.json` è invece inutilizzabile: ha intercettato
la ricarica QML, con GPU a zero e CPU occupata nella ricostruzione dell'interfaccia.
Le prove cambiano le sole opzioni indicate e le ripristinano in `finally`.
Il tentativo di spegnere il visualizzatore desktop non ha mantenuto il valore
`false` nella rilettura QML: non usarlo come prova di assenza di costo.

Ulteriori esclusioni misurate:

- Oscuramento automatico spento: GPU di Hyprland circa 356 ms/s contro 355
  del ritorno alla configurazione iniziale, a batteria; Glassy spento riduce
  invece il costo a circa 232 ms/s. I valori sono di fasi precedenti della
  raccolta e non un confronto diretto con la misura dopo il riavvio.
- Registratori sospesi per sei secondi e poi ripresi: QS circa 262 ms GPU/s,
  Hyprland 352–354 ms/s in entrambi gli stati. La connessione Raspberry è ora
  attiva, con conferma del ricevitore; il registratore esterno resta operativo.
- Build diagnostica senza codice di oscuramento automatico: in compositor
  separati a 200 MHz, r32 2.496/2.501 ms GPU per composizione, diagnostica
  2.472 ms. Non spiega il calo. Nessuna installazione di questa build;
  sorgenti e binario temporanei ripristinati a r32 originale.

`tests/qml-load-check.py` ora usa anch'esso il driver standard e supera i
controlli di caricamento, animazione delle tessere, scorrimento diretto con
piccole inversioni e contrasto IPC, con rendering software. Il gestore touchpad
che aveva corretto il tremolio resta presente. Passa anche il controllo del
recorder e i controlli delle transizioni default/Material della Dynamic Island
con il driver standard. La prima raccolta locale è terminata regolarmente alle 03:14 CET;
alle 03:26 è stata avviata un'altra ora, nello stesso servizio temporaneo,
file `~/.local/state/end4-pC/performance-20261114T022655Z-9d8d0b.jsonl`.
La raccolta locale usa tempo monotono: la sospensione del
portatile ne prolunga l'orario di fine sul calendario; non era un arresto mancato.

## Ridisegno del desktop causato dall'orologio Cookie (14 novembre 2026)

Con Settings aperto e alimentatore collegato, il confronto controllato rileva
Hyprland circa 582–585 ms GPU/s e QS 88–90. Disattivare soltanto l'automatico
di Settings cambia poco (572/99); fermare la rotazione del Cookie porta invece
i due processi a **72/1.7**. Ripristinando la rotazione si torna a 584/88.
Spegnere il visualizzatore non produce un beneficio comparabile. I valori sono
contatori GPU, **non FPS**; non dimostrano la causa di ogni precedente regressione.

La correzione conserva l'animazione originale: `WindowedClock.qml` riutilizza
`ClockWidget` in una superficie Wayland Bottom grande quanto il widget più un
margine di 32 px. Il disegno non è rimpicciolito. La rotazione evita così il
ridisegno del window del wallpaper, grande quanto il monitor. Il namespace
non include `quickshell:` per non attivare la sfocatura generica del compositor.
La cattura del wallpaper nel Cookie è inoltre scollegata quando la sfocatura
del widget è spenta: una cattura tra window differenti non è valida in Qt.

Coordinate e controller del canvas restano quelli originali. Per blocco
schermo, sfocatura dei widget, stili diversi da Cookie, sovrapposizione con
widget superiori, oscuramento desktop e collage si usa il percorso originale.
Questi casi conservano quindi anche il costo del window intero. Il test
`python3 tests/clock-surface-check.py --plugin /percorso/hyprglass.so` verifica
rotazione, dimensioni, parallasse, salvataggio posizione, registrazione al
canvas e ritorno dal percorso originale. Usa Qt software e un compositor
separato; il test non simula un trascinamento reale del puntatore.

La sola rimozione della cattura inutilizzata non basta: il confronto
inline/superficie piccola/inline mantiene il costo più alto nel percorso
inline. Alcune misure includono ricariche lente di QS e frequenze GPU diverse:
sono conservate per diagnosi, non usate come confronto diretto a regime.
Dopo l'assestamento, tre campioni di cinque secondi con GPU a 200 MHz e
alimentatore collegato rilevano Hyprland **352–357 ms GPU/s**, QS **16–20**.
La somma scende da circa 670 a 370 ms/s; il beneficio a batteria richiede ancora
verifica con l'utente. Glassy, oscuramento automatico e profilo GPU non sono
disattivati; il plugin della sessione principale resta r32, senza ricarica nativa.
Passano anche caricamento QML, scorrimento e contrasto nel controllo software.

Misure e risultati sono conservati privatamente in
`~/.local/state/end4-pC/diagnostics/20261114-clock-surface/`.

## R33: sospendere la rotazione completamente coperta (14 novembre 2026)

L'utente conferma un miglioramento con la superficie piccola, ma resta lag a
batteria. Nel confronto con Settings aperto e pronto per ogni campione, GPU
in auto a 200 MHz: Hyprland circa 428 ms GPU/s; blur di Settings a zero 394;
automatico spento 408; rotazione del Cookie ferma **86**. Ripristinando tutte
le opzioni iniziali si torna a 431. Un altro confronto esclude temporaneamente
solo il namespace Settings: 427 → 104 → 426; escludere la barra porta solo a 412.
I valori temporanei sono ripristinati, Glassy e oscuramento automatico restano
attivi. Questi dati non attribuiscono tutti i regressi storici al Cookie.

R33 osserva il piccolo layer dell'orologio durante il render del compositor.
Se una finestra realmente opaca ne copre tutta l'area, Qt mette in pausa la sola
rotazione decorativa. Ora, lancette e data continuano a seguire il tempo; la
rotazione riparte dalla fase conservata quando il quadrante diventa visibile.
La verifica usa l'opacità effettiva e le geometrie di Hyprland, senza un nuovo
timer di campionamento. La funzione nativa
[CWindow::opaque](https://github.com/hyprwm/Hyprland/blob/a0136d8c04687bb36eb8a28eb9d1ff92aea99704/src/desktop/view/Window.cpp#L835)
considera anche le alpha della finestra e del workspace.

Il controllo è conservativo: nessuna pausa dietro finestre trasparenti, in
copertura parziale, con geometrie/offset in animazione o trasformazioni della
finestra. Esclude inoltre il raggio degli angoli e un pixel di antialiasing.
Una sola finestra deve coprire l'intero clock: la copertura combinata di più
finestre non è ottimizzata. Il protocollo riusa il collegamento di visibilità
esistente, con eventi solo sui cambiamenti, PID del proprietario, monitor,
numero di serie e snapshot iniziale. Con r32 il dato è assente e la rotazione
conserva il comportamento precedente. I parametri grafici e i passaggi di
rendering del plugin sono identici a r32.

Passa `tests/clock-surface-check.py --plugin PATH`: formato Wayland opaco reale,
pausa della fase, ripresa dietro una finestra trasparente, copertura parziale,
rivelazione, salvataggio posizione, parallasse e fallback per blur/blocco.
Il Cookie scollega anche la sorgente di blur durante il passaggio tra window,
evitando una cattura Qt tra superfici differenti. Passano validazione degli
eventi/snapshot, controlli IPC, loader, profili, risorse e geometrie native.
La patch applicata a v0.6.4 pulito riproduce tutti i sorgenti/header compilati.

Nella stessa scena isolata, Settings Glassy aperto, a batteria e a 200 MHz,
dopo l'assestamento: pausa automatica **0.0 ms GPU/s**, rotazione forzata
**274.3**, ritorno alla pausa **0.0** per il compositor del test; QS software
passa da circa 0.2% a 27.8% di un core e poi a 0.2%. Zero indica assenza di
nuovo lavoro nel contatore durante quei cinque secondi, non assenza di consumo
del PC. La GPU è condivisa con il desktop. I primi confronti tra processi
separati, prima dell'assestamento, erano incoerenti e non provano il beneficio.
Questa misura controllata non è una misura degli FPS del desktop principale.

R33 e manifest sono installati atomicamente per il prossimo accesso, SHA256
`a8bc170dc6f94153c7ee540f8f7279c5f72aa2313ba9cd0f3af064d7095664e7`.
Dopo il successivo accesso r33 è caricata nella sessione principale: l'utente
conferma Quick fluida a batteria, ma segnala lag nella pagina Interface. Non è
stato effettuato unload/reload del plugin. La verifica prosegue nella sezione r34. Backup r32, misure e riproduzione privata:
`~/.local/state/end4-pC/diagnostics/20261114-clock-occlusion/`.
Il registratore sul Raspberry resta attivo; il comando di arresto resta
`systemctl --user stop end4-freeze-recorder.service`.

## R34: ridurre il costo delle righe di Interface (14 novembre 2026)

Con r33 attiva e alimentazione a batteria, Interface presenta 11 materiali
visibili. Tre campioni a riposo con GPU in auto a 200 MHz rilevano Hyprland
149–169 ms GPU/s, QS circa 1–2. Disabilitare temporaneamente solo il blur o
l'oscuramento automatico non produce un beneficio stabile: le opzioni iniziali
sono ripristinate. La presenza di più materiali pesa anche con oscuramento
manuale a zero; non è una prova che il campionatore causi da solo il rallentamento.

R34 divide la composizione di `quickshell:settings` in fasce disgiunte di
128 pixel e invia allo shader solo le regioni che intersecano ciascuna fascia,
con un pixel di margine. Restano identici shader, coordinate, ordine dei
materiali, sorgente e kernel della sfocatura. Ogni pixel conserva il proprio
insieme di materiali, incluse righe in dissolvenza e bordi antialias. Anche
le ombre fuori dalle card mantengono il percorso originale. I rettangoli di
damage restano disgiunti e non viene modificato il damage globale di Hyprland.
Non sono aggiunti framebuffer. Materiali completamente sovrapposti conservano
il costo della scansione completa; output ruotati mantengono il percorso precedente.

Con la carica insufficiente per un'altra prova a batteria, l'utente attiva
per 180 secondi il profilo AMD `low` mentre il PC è collegato. La GPU è
verificata a 200 MHz; alla fine il profilo torna su `auto`. Nella scena isolata
con la vera pagina Interface: r33 **10.52 ms GPU/fotogramma**, prototipo r34
**6.51**; una successiva conferma della baseline rileva **10.58**. Riduzione
circa **38%** in questa scena, non una misura degli FPS del desktop né una
simulazione completa della batteria. Il prototipo misurato riporta ancora r33
nella stringa di versione; la build finale cambia solo tale stringa e cast C++
equivalenti. L'aumento delle chiamate di disegno porta CPU da circa 2.30 a
2.38 ms/fotogramma. Il primo tentativo di separare selezione e shading nello
shader non migliora il tempo ed è scartato.

Controlli: 108 confronti fra selezione C++ effettiva e GLSL su llvmpipe, entro
1/255, con 3–32 regioni, sovrapposizioni, dissolvenze, oscuramento automatico,
damage parziale e posizioni frazionarie/negative. Passano anche i pixel live
di sfondo e controlli nel test `--settings`, gli aggiornamenti fuori pannello,
la validazione delle risorse, i profili, gli eventi e il loader. Il benchmark
conta una composizione per maschera, anche quando richiede più draw.

```sh
python3 tests/native-glass-bands-check.py SOURCE_DIR
python3 tests/native-glass-damage-check.py --plugin R34.so --settings
python3 tests/native-glass-performance.py R33.so R34.so R33.so --settings-interface
```

Patch verificata su v0.6.4 pulita e build installata atomicamente, SHA256
`a48592e2a25730538c618f5d7a0d0e89431181771f4870ca2889ec6a65520103`.
**La sessione principale mantiene r33**: r34 richiede un nuovo accesso e una
verifica d'uso, anche a batteria appena la carica lo permette. Non è ricaricata
a caldo. Backup r33 e misure private:
`~/.local/state/end4-pC/diagnostics/20261114-interface-bands/`.

## Verifica r34 su batteria reale e hover (14 novembre 2026)

Dopo il nuovo accesso, r34 è caricata. Con alimentatore realmente scollegato,
profilo GPU `auto`, core 200 MHz, memoria 400 MHz e CPU `schedutil`, lo stesso
benchmark della pagina Interface misura r33 **12.438**, r34 **8.176**, ritorno
r33 **12.503 ms GPU/fotogramma**. Output 951×1023, identica copertura per
fotogramma nelle tre fasi: 1,037,541 pixel glass e 712,776 pixel blur. Il
beneficio reale è circa **34%**. Le guardie controllano alimentazione e profilo
prima/dopo ogni campione; non viene modificato il profilo energetico.

Il precedente `low` con alimentatore aveva la stessa frequenza del core, ma
una diversa quantità di pixel ridisegnati: non dimostra equivalenza completa
con la batteria. I valori assoluti 6.51 e 8.18 ms non possono essere attribuiti
alla sola alimentazione. La prova reale diventa il riferimento per le verifiche
successive; questi contatori non misurano direttamente gli FPS percepiti.

L'utente segnala lag al passaggio sulle categorie a sinistra e sui controlli a
destra. Nel desktop, a batteria e 200 MHz, una prova con coordinate verificate
e veri eventi mouse confronta spazi vuoti, movimento dentro una riga, cursore
fermo e passaggi tra righe. Tra categorie Hyprland passa da circa **153 a 282
ms GPU/s**, QS da 1.5 a 20.5. Tra i controlli a destra il confronto ripetuto
è **144 → 435 → 171 → 436 → 145 ms GPU/s**, con QS 0.9 → 37.9 → 2.5 → 36.9
→ 1.0. Le geometrie Glassy restano stabili: zero scritture nelle fasi misurate.
Le prime prove di movimento con posizionamento accelerato o solo warp sono
scartate, perché non garantivano la posizione o gli eventi hover ricevuti da Qt.

In `RippleButton` anche due colori con alpha zero conservavano RGB diversi:
la loro animazione durava 200 ms pur non essendo visibile. Il Behavior ora
usa valore destinazione e alpha corrente per saltare soltanto queste
transizioni invisibili. Restano animati colore visibile, ingresso e uscita.
Il controllo QML fallisce sul codice precedente e passa con la correzione,
insieme a caricamento dei componenti, scorrimento e contrasto IPC. Non è
necessario un nuovo plugin nativo. Il confronto d'uso dopo la correzione va
registrato con la propria alimentazione: nel frattempo l'utente ha ricollegato
l'alimentatore, quindi non costituisce un A/B diretto con le misure a batteria.
Il costo delle animazioni visibili della navigazione resta un tema distinto.

Un successivo A/B con la stessa alimentazione collegata, GPU `auto` a 200 MHz,
r34 invariata e stessa traiettoria mouse confronta soltanto il guard del
Behavior. Prima: riferimento **149**, passaggi tra controlli **417.7**, ritorno
**149.1 ms GPU/s** per Hyprland; QS **1.6 → 37.5 → 1.5**. Dopo: riferimento
**147.7**, passaggi **318.9**, ritorno **168.8**; QS **1.7 → 8.0 → 2.6**.
Il costo Qt durante l'hover cala circa 79%, quello del compositor circa 24%.
La prova non garantisce assenza di lag e il residuo di composizione rimane;
la verifica a batteria di questa correzione QML resta da completare. Il guard
è ripristinato nel `finally` dell'esperimento e lasciato attivo. Nessun
unload/reload nativo; gli effetti visibili continuano a passare il controllo
QML, che include ora un'asserzione sul marcatore del test hover.

Misure e comandi riproducibili sono conservati privatamente in
`~/.local/state/end4-pC/diagnostics/20261114-real-battery-hover/`.

### Hover residuo: colore trasparente delle righe

Con r34 e il guard delle animazioni caricati, una nuova prova realmente a
batteria (`auto`, SCLK 200 MHz, MCLK 400 MHz) conferma il residuo: spazio vuoto
**113.6**, passaggi tra controlli **273.7**, ritorno **122.6**, seconda prova
**271.8**, ritorno **118.8 ms GPU/s** per Hyprland. QS passa da circa 1–2 a
8–9 ms GPU/s. Zero aggiornamenti delle geometrie Glassy durante la misura.

Forzare temporaneamente il cursore a freccia non cambia il risultato
(hover **275.6**). Disabilitare l'hover del controllo invece lo riporta vicino
al riferimento (**112.7 → 122.9 → 130.8**), ma non è la soluzione conservata.
`ConfigSwitch` ereditava un colore trasparente con RGB del tema, mentre
l'hover usava il nero trasparente: il precedente guard evitava l'animazione,
ma il cambio di RGB continuava a sporcare la scena anche ad alpha zero.

La correzione assegna anche allo stato normale `"transparent"`, mantenendo
hover, cursore, ripple, accessibilità e switch. A parità di alimentazione e
traiettoria: **111.4 → 103.9 → 124.3 ms GPU/s**, QS **1.6 → 0.8 → 2.3**.
Il controllo QML verifica che colore normale e hover siano identici e
trasparenti, oltre alla conservazione delle dissolvenze visibili; passa.

Le categorie a sinistra conservano invece animazioni visibili: riferimento
**119.2**, hover **253.4**, ritorno **111.7 ms GPU/s**. Né eliminare il cambio
di peso dell'icona (**245.6**) né una dissolvenza sul render thread
(`OpacityAnimator`, **247.1**) riduce il residuo in modo convincente: entrambe
le prove sono ripristinate. Non attribuire la soluzione delle righe anche
alla navigazione, né interpretare questi contatori come FPS. Tutti i test
temporanei dei sorgenti usano un ripristino `finally`; il plugin principale
non viene scaricato o ricaricato.

Un prototipo isolato con fasce da 64 anziché 128 pixel supera gli stessi 108
confronti dei pixel, ma il benchmark a batteria misura **9.076 → 8.073 →
8.188 ms GPU/fotogramma** (r34, prototipo, ritorno r34). Il vantaggio rispetto
alla baseline di ritorno non è convincente e il costo CPU aumenta: il
prototipo non è installato né conservato nella patch di produzione.

### Scorrimento e aggiornamenti inutili dei materiali

Una successiva acquisizione nella sessione reale distingue i fotogrammi
consegnati da Qt dal tempo GPU del compositor. Durante uno scorrimento
continuo, a batteria e GPU `auto`, la mediana dei segnali `frameSwapped` è
circa **33 ms**; questi segnali non sono una misura della presentazione sul
monitor. Il registro conteneva **452** materiali, comprese pagine nascoste,
contro circa **20** regioni effettivamente visibili.

`WindowGlass` ora registra soltanto i materiali nativi attivi e visibili e li
rimuove alla chiusura o alla disattivazione; riaprire il pannello li ripristina.
Il registro scende a **123** elementi (le righe fuori viewport continuano a
essere escluse da `nativeRegion`). Inoltre la cache della geometria usata dai
testi per il contrasto non dipende più dalla conferma IPC `regionsApplied`:
ogni movimento della lista ne provocava una ricostruzione superflua, mentre
il campionamento del contrasto continua al proprio intervallo.

Nella stessa prova a batteria, prima/dopo queste correzioni, QS passa da
**129.9% a 95.4% di un core**; Hyprland da **496.9 a 489.8 ms GPU/s**. La
mediana resta **33 ms**: il risparmio CPU è misurabile, ma non dimostra la
risoluzione del lag GPU. Nessuna modifica al profilo energetico, all'effetto
o alle animazioni. `node tests/glass-registry-check.js` controlla il ciclo
chiusura/riapertura e i cambi di profilo; `python3 tests/qml-load-check.py`
controlla il binding reale della cache, compreso l'aggiornamento al successivo
campione di contrasto.

Un prototipo separato della satinatura a un quarto di risoluzione, con
prefiltro per le dimensioni dispari, passa 40 confronti software su bordi,
righe sottili, scacchiere e gradienti (massimo 3/255, media entro 1/255).
Sulla GPU reale a batteria, però, misura **8.214 → 8.490 → 8.198 ms per
fotogramma**, con uguale copertura glass e frequenze 200/400 MHz. Il costo
del passaggio aggiuntivo annulla il risparmio: il prototipo è scartato e non
viene installato. Questo confronto non giustifica un'ulteriore riduzione
della qualità della sfocatura.

La prova QML con una finestra più piccola, mantenendo il pannello centrato,
non completa il caricamento ed è interrotta senza usarne i dati. Il runner
ripristina `Settings.qml`; il thread principale di QS rimane occupato e viene
riavviato **solo Quickshell**. Hyprland e r34 rimangono caricati. Nessuna
modifica alla dimensione della finestra è conservata. I controlli QML finali
passano; non rimane strumentazione temporanea nei componenti.

I risultati di questa acquisizione sono in
`~/.local/state/end4-pC/diagnostics/20261114-real-battery-hover/cpu-cache-and-frost-probe/`.

## Registrazione dei lag sporadici con r32 (13 novembre 2026)

R32 è caricato e l'utente conferma un miglioramento, con scatti sporadici.
La connessione SSH a `xlini@192.168.1.199` scade e il servizio del Raspberry
rimane in riavvio automatico: non considerarlo una registrazione funzionante.
È stata avviata una raccolta **locale**, persistente su disco, a priorità bassa
per un'ora. Unità temporanea `end4-performance-recorder.service`, senza avvio
permanente al login né modifiche di Glassy o del profilo GPU.

Log corrente:
`~/.local/state/end4-pC/performance-20261113T142149Z-0ad5da.jsonl`.
File privato 0600, creato in esclusiva e mai sovrascritto. Il percorso corrente
si trova anche nel journal del servizio e in `/tmp/end4-performance-current-path`.
Il file contiene UTC e tempo monotono: per correlare una segnalazione dell'utente
usare il fuso Europe/Rome e una finestra di alcuni secondi attorno al messaggio.
Un eventuale marcatore scritto dall'assistente va in un file laterale; non
appendere dall'esterno al file che il recorder sta scrivendo.

```sh
systemctl --user status end4-performance-recorder.service
# Arrestare questa raccolta locale:
systemctl --user stop end4-performance-recorder.service
# Il comando importante già salvato per il registratore Raspberry rimane:
systemctl --user stop end4-freeze-recorder.service
```

Il recorder esistente supporta ora anche:

```sh
python3 scripts/glass/record-freeze.py --local /percorso/nuovo-log.jsonl --seconds 3600
```

In locale raccoglie ogni secondo CPU e contatori DRM cumulativi di QS/Hyprland,
thread QSG, frequenze/temperatura GPU, alimentazione, pressione CPU/memoria/I/O,
swap, fault maggiori, contatori CPU complessivi e principali consumatori CPU.
Registra inoltre i cambi di wallpaper e dei parametri Glassy, più i flussi di
log kernel/Hyprland già previsti. I contatori misurano risorse, non FPS o ogni
singolo frame perso. Deduplicare i descrittori DRM per dispositivo/client.
Un valore zero nel contatore GPU globale non implica assenza di lavoro: usare
le differenze di `gpu_engine_ns` e del tempo monotono, distinguendo PID/start
nuovi e reset dei contatori.

Per contenere l'overhead i nuovi processi vengono scoperti ogni cinque secondi;
QS/Hyprland e i consumatori principali sono seguiti ogni secondo. Il campo
`cpu_interval_s` indica l'intervallo effettivo di ciascun processo. I lavori
molto brevi fra due scansioni possono sfuggire: la correlazione col wallpaper
può indicare quando serve una traccia mirata. I nomi degli script dei processi
principali sono basename; non vengono salvate le righe di comando complete.

La prima raccolta, `performance-20261113T141529Z-19eb11.jsonl`, è stata fermata
perché il campionatore stesso consumava circa il 10% di un core. La versione
attiva evita di leggere fdinfo dei descrittori non grafici, condivide lo stato
delle scansioni e conserva l'intervallo per PID: prove brevi mostrano circa
12–14 ms CPU per campione ordinario e una scansione completa di circa 39 ms
ogni cinque secondi, variabili col carico. Nice 15, I/O idle, limite memoria
128 MiB, stop automatico dopo un'ora; niente riavvio automatico di questa unità.
Verifica in esecuzione: dopo 96 campioni il servizio è attivo, file di circa
883 KiB con permessi 0600 e contatori DRM presenti; durata media del campione
28.2 ms, massimo 75.27 ms. CPU cumulativa del servizio 3.47 s in circa 105 s,
incluso l’avvio del lettore journal. Due eventi di contesto wallpaper/config
sono già presenti. Queste letture confermano la raccolta, non la causa di un lag.

`tests/freeze-recorder-check.py` verifica anche modalità locale senza SSH,
permessi, assenza di sovrascritture, contesto wallpaper, deduplicazione DRM,
riuso PID, intervalli fra scansioni, SIGINT e chiusura corretta. I controlli SSH
precedenti rimangono. Il prossimo passo è correlare i campioni con una
segnalazione «lag adesso», senza riabilitare/disabilitare effetti durante la
raccolta ordinaria.

## Prestazioni globali e occlusione: r32 (13 novembre 2026)

L'utente segnala cali anche con alimentatore collegato dopo il nuovo accesso.
Verificato che il renderer attivo è r31. Le prove cambiano temporaneamente
singoli campi delle preferenze, rileggendo il JSON corrente a ogni aggiornamento
e ripristinando i valori iniziali in `finally`; wallpaper e altre preferenze
non vengono ripristinati a una vecchia copia. Nessuna modifica del profilo GPU.

Confronto di sei secondi per stato, con ritorni alla configurazione iniziale:
il solo automatico spento lascia sostanzialmente invariato il lavoro GPU di
Hyprland (circa 565 ms GPU/s); Glassy spento lo riduce a circa 229 ms/s. La
rotazione del clock non spiega il lavoro grafico del compositor. I numeri sono
tempi DRM e non FPS; frequenze e altri carichi possono cambiare fra campioni.
I file temporanei sono `/tmp/end4-glassy-ab.json` e
`/tmp/end4-glassy-targets.json`. I dati ottenuti dal primo tentativo via
`hyprctl keyword` **non sono validi**: con questo parser servono comandi Lua.
Il confronto ripetuto usa `hl.config` e verifica ogni valore rileggendolo:
`/tmp/end4-native-targets-lua.json`. Tutti i filtri sono ripristinati al termine.

Individuato un difetto nel collegamento al render pass: i passaggi Glassy
restituivano `disableSimplification() == true`. In
[Hyprland 0.55.4, Pass.cpp](https://raw.githubusercontent.com/hyprwm/Hyprland/v0.55.4/src/render/pass/Pass.cpp)
un solo elemento con questo flag salta la semplificazione per l'intero frame.
Il costo riguarda quindi anche contenuti coperti, oltre ai pixel del vetro.

R32 conserva `needsLiveBlur()` per mantenere fresco lo sfondo nella regione
interessata, ma riabilita la semplificazione per layer e decorazioni delle
finestre. I passaggi di redirect e restore dei layer sono entrambi
`undiscardable()`: devono restare abbinati anche sotto occlusione. Il pre-pass
con damage vuoto non cambia framebuffer. I controlli di ripristino dei buffer
alla chiusura rimangono invariati.

La dock nascosta risultava registrata come materiale y=186..246 dentro una
superficie alta 178: continuava comunque a inserire il passaggio nativo.
Ora una geometria nota completamente fuori superficie non lo inserisce.
Si conserva un margine di un pixel per il bordo antialias; geometrie sconosciute,
rotazioni e snapshot di chiusura conservano il fallback previsto. Il box del
pre-pass si limita al materiale con supporto della rifrazione/Gaussian; il
passaggio del contenuto Qt rimane completo per icone ingrandite e anteprime.
Anche campionamento e damage della dock usano il ritaglio già esistente per
Settings e sidebar sinistra. Nessuna riduzione dei parametri o disattivazione
permanente di Glassy/darker.

Riscontri in compositor separati (plugin principale sempre r31):

- Scena con grande pannello: circa 12.21 → 10.20 chiamate GL per composizione.
- Scena simile al desktop con tre pillole e dock nascosta: **43 → 19 chiamate**
  per composizione (-55.8%); passaggio Glassy 233946 → 64668 pixel/composizione
  (-72.4%). Circa 1.271 → 1.062 ms GPU per composizione in questa scena; frequenze
  medie 660 → 641 MHz. Sono misure della fixture, non una garanzia sugli FPS
  o sull'assenza di tutti i cali della sessione reale.
- Nessuna nuova allocazione di texture durante le finestre di misura.
- Dati: `/tmp/end4-r31-r32-scene-comparison.log` e
  `/tmp/end4-r31-r32-bar-comparison.log`; fixture mirata
  `/tmp/end4-bar-hidden-dock-fixture.qml`.

Correzione alla descrizione iniziale delle prove: erano state impostate
`LIBGL_ALWAYS_SOFTWARE=1` e `GALLIUM_DRIVER=llvmpipe`, ma il compositor separato
ha comunque usato la GPU (contatori DRM non nulli). Non classificare queste
prove come interamente CPU. I confronti dei singoli shader e il controllo
geometrico rimangono invece esplicitamente su CPU. La sessione principale non
ha subito unload/reload del plugin né modifiche delle sue animazioni.

Verifiche completate: compilazione; controllo geometrico nuovo
`tests/native-glass-visibility-check.py` (incluso in build.sh); buffer e
ripristino alla chiusura; loader e compatibilità r31; profili; ottiche e
visibilità barra; 336 confronti shader e 102 Gaussian; prova reale isolata di
movimento/workspace; rifrazione mantenuta in 7 frame di chiusura e 9 di apertura;
12 controlli di pixel su ridisegni parziali, zero composizioni per aggiornamenti
esterni al materiale, variazioni del solo profilo correttamente ridisegnate.
La fixture damage usava ancora `frost` locale, ignorato dal profilo sidebar:
falliva allo stesso modo su r31. Ora cambia il vero profilo sidebar entro il
limite consentito (16/8), conservando le asserzioni sui pixel.

Verificato anche il percorso finestra Settings flottante: il fondo cambia
verde → rosso → verde sotto il satinato, con marker Qt bianco conservato.
Il tracer esistente in `tests/native-glass-performance.py` espone ora anche
chiamate e area GL complessive per composizione. Nei commit includere il nuovo
controllo di visibilità, richiesto anche dalla compilazione del branch.

R32 installato atomicamente per il prossimo accesso, SHA256
`510d2cbe93af91cfd2f0658c1aea9a7024e606034ccf02e888c081aad98d9368`.
Backup `~/.cache/end4-pC/native-glass-backup-before-r32-20261113-144432`.
L'installer verifica che il plugin attivo rimanga r31. Rimane da verificare la
fluidità nella sessione principale dopo il nuovo accesso, anche a batteria;
non dichiarare ancora eliminati tutti i cali intermittenti.

## Oscuramento stabile della barra: r31 (13 novembre 2026)

Segnalati un flash del darker all'espansione della barra e rallentamenti
intermittenti anche dopo la transizione del wallpaper. Il renderer effettivamente
caricato durante la diagnosi è ancora **r29**: r30 era installato su disco,
ma la sessione non era stata riaperta. Nessun hot-unload/reload del plugin.

Il test CPU riproduce il difetto geometrico: una pillola che si allarga sposta
i quattro campioni da una zona scura a una chiara; inoltre i box interni usano
riferimenti diversi dal contenitore. R31 usa per `quickshell:bar` una fascia
comune alla barra: intera larghezza della superficie e intervallo verticale dei
materiali. L'espansione orizzontale e la comparsa di box annidati non spostano
i campioni. Il riferimento viene azzerato esplicitamente per le altre superfici.
Restano quattro prelievi per vertice, sedici per draw dell'intera barra,
indipendenti dal numero di pillole; nessun nuovo passaggio, framebuffer, timer
o readback. L'adattamento locale per singola pillola richiederebbe ID stabili dei
materiali; questa scelta tratta la barra come un unico elemento delle impostazioni.
Il percorso Qt/wallpaper non cambia in r31: la segnalazione misurata usa la
sorgente finestre e il renderer nativo. Transizioni dei parametri, sfocatura,
rifrazione, colore dei contenuti e impostazioni conservati.

Misure passive, non confronti controllati di FPS:

- 30 secondi durante il calo: QS circa 74.2% CPU, Hyprland 24.6%, VS Code 60.4%
  complessivo in media; nessuna pressione memoria significativa in quella finestra.
- Successivi 75 secondi con un cambio wallpaper: QS 40.7% medio / 71.1% massimo,
  Hyprland 11.9% / 22.1%, processi Code 35.8% / 255.7%. Il dato massimo è il totale
  su più core. Registrazione temporanea `/tmp/end4-glassy-wallpaper-cycle.jsonl`.
- Cinque secondi tramite fdinfo DRM: circa 107.6 ms GPU/s per QS e 564.7 ms/s per
  Hyprland. Il contatore globale `gpu_busy_percent` indicava zero: non è una
  misura affidabile di assenza di carico in questa prova.
- Gli script switchwall rimasti vivi per minuti risultano in attesa di
  `notify-send` per la richiesta di upscaling: non sono generatori di tema in
  esecuzione continua. Non terminati né rimossi.
- L'utente conferma che a batteria il calo peggiora. Nella lettura successiva
  l'alimentatore risulta nuovamente collegato: GPU in auto, frequenze osservate
  200–254 MHz, QS 32.8% CPU / 107.0 ms GPU/s, Hyprland 11.0% / 571.3 ms GPU/s.
  Non è quindi una misura controllata a batteria. Il confronto sul renderer r31
  attivo, anche a batteria, resta da effettuare dopo il nuovo accesso.

Lo script del colore di VS Code evita adesso `sed -i` quando l'accento è identico,
per non risvegliare inutilmente editor ed estensioni. Se cambia lo aggiorna come
prima; valida il formato esadecimale prima di inserirlo nella sostituzione.
Questo elimina riscritture evitabili, senza attribuire tutti i picchi di Code
all'estensione del tema o disabilitare le personalizzazioni.

Verifiche completate: compilazione nativa; pixel GLSL su llvmpipe con regressione
che riproduce il flash senza riferimento fisso e lo elimina con riferimento
fisso, compresa la comparsa del box interno; 336 confronti di geometria e 102
confronti Gaussian; buffer/resize/chiusura; loader/ABI/hash e compatibilità r30;
profili indipendenti; ottica della barra e visibilità. Il controllo wallpaper
verifica anche che un colore editor identico conservi inode e mtime, un colore
nuovo si aggiorni mantenendo i commenti JSONC e valori invalidi non scrivano file.
Nessuna prova grafica aggiuntiva sul desktop o modifica del profilo energetico.

R31 installato atomicamente per il prossimo accesso, SHA256
`5696f7d1e19274c04defa2ab0afee95bc1d833e7d53a6b4657257d8b4dc5ade9`.
Backup del precedente installato/staged:
`~/.cache/end4-pC/native-glass-backup-before-r31-20261113-133731`.
L'installer verifica che il plugin caricato resti invariato (r29). R31 include
anche l'ottimizzazione vertex di r30; non dichiarare risolti i cali intermittenti
prima di verificarlo nella sessione e a batteria.

## Ottimizzazioni darker e cambio wallpaper: r30 (13 novembre 2026)

L'utente segnala cali generali e, al cambio wallpaper, rallentamenti di pochi
secondi. Prima delle modifiche il renderer caricato è r29. Una lettura di sei
secondi, con alimentatore collegato e GPU in auto, rileva circa 35.8% CPU per
Quickshell e 10.3% per Hyprland; la lettura GPU al termine è 10%. Non è una
misura controllata del picco durante il cambio wallpaper né una prova della
causa esclusiva del rallentamento.

Il darker r29 ripeteva quattro campioni identici per ogni frammento di ogni
materiale. R30 li valuta nel **vertex shader** e passa la luminanza ai pixel:
quattro vertici per quad, quattro campioni per materiale, più il materiale di
fallback. Il limite nativo resta 32 regioni: al massimo 528 prelievi per draw,
indipendentemente dall'area del pannello, invece di quattro prelievi per pixel.
Il percorso Qt ha un solo valore per box e usa gli stessi punti e lo stesso LOD.
Nessun nuovo framebuffer, passaggio, readback GPU o cattura. In manuale i campioni
sono esclusi. Conservati attenuazione uniforme, colori, rifrazione e animazioni.

Il vertex shader nativo estende quello fornito da Hyprland mantenendone la
trasformazione; nove vec4 flat contengono le luminanze di fallback e regioni.
I nuovi asset Qt `liquidLens.vert` e `liquidLens.vert.qsb` devono essere inclusi
insieme al fragment shader e al suo QSB nei commit e nelle verifiche del branch.
La scelta dell'inchiostro condivide inoltre uno snapshot delle geometrie fra
le scritte, anziché richiamare `nativeRegion()` per ogni box a ogni cambio colore
di ciascun testo. Lo snapshot segue campioni, geometrie applicate e oggetti live.

Il cambio wallpaper conserva tema, intervallo e transizione. Il timer è unico
nel singleton Wallpapers; soltanto le istanze Background lo abilitano tramite
contatore, evitando sia la moltiplicazione per monitor sia i cambi avviati da
processi standalone delle impostazioni. I lavori automatici usano `nice -n 10`
e `ionice -c 3`, senza avviarne un altro se il precedente è ancora in corso.
Le scelte manuali mantengono la priorità precedente e la validazione delle
cartelle. Le richieste di icone identiche non riscrivono più KDE né emettono
la notifica globale Qt; i cambi reali continuano a essere applicati e gli
errori di scrittura sono propagati.

Verifiche: confronto fra la stessa formula nei fragment shader e nei vertex
shader su CPU llvmpipe, incluse regioni sovrapposte, angoli, materiali opachi,
fading, toni chiari e colorati. Differenze entro 1/255. Il test Qt RenderControl
usa il vero ShaderEffect di FrostedGlass con i suoi QSB, controlla i pixel dei
materiali manuali/automatici e termina correttamente. La prima versione della
nuova scena di test aveva un errore di lifetime PySide nel distruggere un secondo
QQmlComponent; il test finale usa un solo componente e un Loader.

Timing informativo su CPU, 128×96 e 40 draw senza readback nel ciclo:
automatico circa 0.923 ms/draw prima e 0.709 dopo; manuale circa 0.832 e 0.607.
Non equivale agli FPS né misura il guadagno sulla GPU del desktop, soprattutto
a batteria. Passano anche il caricamento QML, i controlli framebuffer/profili/
visibilità, il loader, il contrasto, i 32 test del gestore icone e
`tests/wallpaper-scheduling-check.py` (comandi mock: nessun tema reale modificato).

R30 installato su disco con SHA-256
`ba572d6f12d197833c4a75080425bac3c6e7af3e6a8d12709202407cdd98ace8`.
Backup: `~/.cache/end4-pC/native-glass-backup-r29-20261113-132127/`.
La sessione mantiene r29 caricato: il renderer ottimizzato entra in uso al
prossimo accesso. Le modifiche QML e agli script sono già disponibili.
Resta da confrontare la fluidità reale durante cambi automatici e a batteria,
senza confondere il carico della compilazione con quello a regime.

## Toni chiari conservati nell'oscuramento automatico: r29 (13 novembre 2026)

Il confronto dell'utente fra wallpaper e impostazioni ha mostrato la perdita di
una separazione fra due superfici chiare. Causa riprodotta: in r27/r28 il nero
veniva calcolato separatamente per ogni pixel, con una curva che portava tutti
i grigi sopra 0.38 allo stesso grigio. Nel test, fasce 230 e 180 diventavano
entrambe 97/255. Questo non è un effetto inevitabile di uno strato nero trasparente.

R29 calcola una **sola opacità nera per materiale**, stimando la zona più chiara
con quattro punti fissi nei quadranti del box. Quell'opacità moltiplica tutti i
colori del materiale nello stesso modo: conserva i rapporti RGB e la distinzione
fra le fasce, incluse quelle beige/azzurre. La selezione della zona più chiara
privilegia la leggibilità rispetto alla media. L'oscuramento manuale è invariato.
Il prelievo usa lo sfondo già disponibile prima del contenuto Qt, evitando feedback
di testi e pulsanti; funziona anche con box annidati e terminali trasparenti.

L'automatismo richiede quattro texture fetch aggiuntivi **per frammento**, alle
stesse coordinate per tutto il materiale, sfruttando la cache delle texture.
Non introduce catture, readback GPU, nuovi framebuffer o passaggi di rendering.
In manuale quei prelievi sono esclusi. Il limite intenzionale è il campionamento
sparso: piccoli dettagli chiari fra i quattro punti possono sfuggire. Una stima
spaziale completa richiederebbe una riduzione della texture mantenuta in cache.
Le prestazioni reali a batteria restano da confrontare; i test su CPU non le
certificano.

Il percorso Qt usa la stessa regola; lo shader QSB è rigenerato. La scelta
adattiva dell'inchiostro nelle impostazioni tiene conto del materiale che contiene
la scritta, usando la geometria registrata e i campioni di luminanza esistenti.
Il loader negozia `uniformDarkening` solo per r29: fino al prossimo accesso
mantiene il calcolo dell'inchiostro coerente con r27/r28 ancora caricati.
L'interfaccia segnala l'aggiornamento necessario quando l'automatismo è attivo.

Il test pixel delle due fasce fallisce sullo shader precedente e passa sul nuovo,
anche per due fasce colorate; verifica una sola attenuazione su tutti i canali.
Passano inoltre il test dei pallini agli angoli, 336 confronti delle geometrie,
102 confronti Gaussiani, i controlli dei profili e del loader, il test della
pagina QML e i casi di contrasto delle scritte su materiali e sfondi misti.
Nessuna prova GPU hardware o ricarica del plugin nel compositor attivo.
R29 installato atomicamente con SHA-256
`2ffbd10fccbf48abf94e353d74ef2ef678286ca02d926575a0d8dd08a480e35d`.
Backup dei file precedenti:
`~/.cache/end4-pC/native-glass-backup-r28-20261113-124935/`.
Il plugin caricato verificato durante l'installazione è ancora r27; il prossimo
accesso applicherà insieme la correzione degli angoli r28 e quella dei toni r29.

## Pallini scuri fuori dagli angoli della barra: r28 (13 novembre 2026)

Con oscuramento attivo su sfondo bianco erano visibili piccoli punti scuri
vicino agli angoli delle pillole. Riprodotto su CPU llvmpipe: un pixel dell'ombra
Qt con alpha 1/255, fuori da tutte le regioni Glassy, diventava vetro opaco.
Il ramo di fallback dello shader estendeva il vetro alla superficie della barra
anche quando il pixel apparteneva soltanto all'ombra. Senza oscuramento il
risultato quasi bianco nascondeva il difetto.

Nelle superfici layer con regioni Glassy esplicite, i pixel fuori dalle sagome
ora conservano il contenuto Qt originale, inclusa la sua alpha. Il vetro dentro
le sagome, le sovrapposizioni, i bordi antialias e il percorso delle finestre
floating restano gestiti come prima. Nessun nuovo passaggio di rendering.

Il test in `tests/native-glass-shader-check.py` controlla i quattro angoli e un
punto esterno al bordo della pillola su bianco, con oscuramento 0/55/100% e
automatico: fallisce su r27 e passa su r28. Passano inoltre 336 confronti pixel
delle geometrie precedenti, 102 confronti Gaussiani, controlli di ripristino
framebuffer, profili, visibilità della barra e negoziazione del loader.

Il loader conserva tutte le capacità di r27 mentre il nuovo binario attende
il prossimo accesso. Nessuna ricarica del plugin nel compositor attivo.
Binario r28 installato atomicamente, con ABI verificata e SHA-256
`8805b055bc165c44f663afc22eade16d80e05ace07051cf66906fc03fbb0c86c`.
Backup:
`~/.cache/end4-pC/native-glass-backup-r27-20261113-123723/`.
All'installazione il compositor conserva r27 caricato; resta da verificare
visivamente il bordo della barra dopo il prossimo accesso.


## Oscuramento per elemento: r27 (13 novembre 2026)

La pagina Glassy offre **Oscuramento** (0–100%) e **Oscuramento automatico**
per Bar, Dock, Sidebar, Impostazioni, Lockscreen e Terminale. I valori persistenti
sono `background.widgets.glass.elements.<elemento>.darkening` e
`automaticDarkening`. Il valore manuale resta salvato quando l'automatismo
lo disabilita; il reset del singolo elemento ripristina 0% e automatico spento.
I nuovi campi predefiniti conservano l'aspetto delle configurazioni esistenti.

L'effetto agisce sul colore dello sfondo già rifratto/sfocato, prima dei riflessi
e della composizione di testi e controlli. L'automatismo è **locale**, non una
singola media dell'intero monitor: le zone scure restano inalterate, quelle
chiare vengono attenuate con una curva continua. Per luminanza sRGB ponderata
`L`, il nero automatico è `max(0, 1 - 0.38 / max(L, 0.38))`:
bianco → circa 62%, nero → 0%. Non aggiunge texture fetch, catture, framebuffer,
readback GPU o timer di campionamento; segue il contenuto effettivamente
renderizzato, incluse le sue transizioni. Non introduce un ritardo temporale
indipendente ai cambi dello sfondo. Le variazioni dei controlli manuali e
l'attivazione/disattivazione dell'automatismo hanno una transizione di 800 ms.
La transizione nativa richiede ridisegni soltanto finché è in corso.

Il percorso Qt copre wallpaper e lockscreen; il percorso nativo copre le finestre
sottostanti e i terminali trasparenti. I due shader usano la stessa curva.
La scelta adattiva dell'inchiostro nelle impostazioni tiene conto del nero
applicato; i campioni che contengono solo luminanza sono approssimati come grigi,
quindi non costituiscono una misura esatta del contrasto sui colori saturi.

L'IPC `end4profiles` conserva il formato precedente e aggiunge, solo se il motore
lo supporta, una coda `darkening <attivo> <chiave> <nero 0..1> <automatico 0|1> ...`.
Parsing atomico, limiti numerici, unicità delle chiavi e controllo PID restano
obbligatori. Il loader riconosce r27 e conserva tutte le capacità di r26;
non invia la coda a r26. L'interfaccia segnala quando serve il nuovo accesso.

Verifiche effettuate senza caricare il nuovo plugin nel compositor attivo:

```sh
python3 tests/qml-load-check.py
node tests/glass-contrast-check.js
python3 tests/native-glass-loader-check.py
python3 tests/glass-ipc-check.py
python3 tests/glass-profiles-check.py /tmp/end4-darkening-native
python3 tests/native-glass-shader-check.py /tmp/end4-darkening-native
python3 tests/native-glass-buffer-check.py /tmp/end4-darkening-native
python3 tests/topbar-glass-check.py /tmp/end4-darkening-native
python3 tests/bar-visibility-check.py /tmp/end4-darkening-native
```

Il sorgente in `/tmp` è la base v0.6.4 fissata dal progetto più
`scripts/glass/native/live-background.patch`; può essere rigenerato dal build.
I test pixel usano esclusivamente CPU llvmpipe e controllano 0/25/50/100%,
nero/grigio/bianco automatico, materiali trasparenti/opachi, modalità standard/
enhanced e pixel del contenuto invariati. Restano da confermare visivamente
nella sessione reale cambi wallpaper, scorrimento e prestazioni a batteria.

Binario r27 installato atomicamente per il prossimo accesso; nessun unload/load
a caldo. SHA-256:
`19157304a16004c64feb5a46fd3cd9c6b99dd4e6b44cd14c5b814c4e152e44dc`.
Backup di installazione e staging r26:
`~/.cache/end4-pC/native-glass-backup-r26-20261113-120822/`.
La sessione verificata durante l'installazione mantiene r26 caricato.

## Crash dopo l'installazione r27: verifica del 13 novembre 2026

L'utente ha trovato una schermata di crash ed è passato a TTY3 per riavviare.
Il journal colloca il riavvio richiesto da console alle 12:19:46. Dopo il
riavvio il plugin caricato è r27 e il suo hash coincide con il manifest.
Tutti i profili riletti conservano oscuramento 0% e automatico spento.

Il primo report completo trovato è invece di **Quickshell**, PID 309736,
run ID `gmn3taqfot`, alle 12:16 circa:
`~/.cache/quickshell/crashes/gmn3taqfot/report.txt`.
Riporta SIGABRT in `WlSessionLock::updateSurfaces`, con messaggio fatale
`Tried to show lockscreen surfaces without active lock`, lungo il percorso
di una scorciatoia globale. Il sorgente installato di Quickshell contiene
quel controllo in `src/wayland/session_lock.cpp:102`; la sequenza che porta
allo stato incoerente non era ancora stata riprodotta o corretta durante
quella verifica. La riproduzione e la correzione del 14 novembre sono
descritte nella sezione sul blocco schermo all'inizio di questo documento.

Il coredump PID 309740 con stack nullo in Qt/Wayland riguarda il successivo
gestore della schermata di crash (`qsCheckCrash`), non il primo arresto.
C'è inoltre un secondo report alle 12:19, run ID `gmn36ztfot`, con SIGSEGV in
`QQmlConnections::connectSignalsToMethods`; resta da analizzare separatamente.
Non risultano nuovi crash report di Hyprland o errori GPU di timeout/reset
nei dati consultati per questo intervallo. Questo non dimostra da solo
l'assenza di qualsiasi problema del compositor.

Durante la precedente installazione su disco era stato verificato r26 ancora
caricato; r27 è stato preparato per il prossimo accesso senza reload nativo.
Non attribuire automaticamente questi arresti al nuovo shader: occorre
correlare gli eventi e il percorso di blocco automatico. Nessuna patch della
lockscreen o prova di blocco della sessione reale è stata applicata durante
questa verifica.

Il recorder esterno non raccoglieva: il journal riporta SSH verso
`192.168.1.199:22` fallito con `Network is unreachable` e riavvii del servizio.
Ripristinare la connessione prima di usarlo come evidenza nelle prossime prove.

## Dialoghi della sidebar destra (12 novembre 2026)

Wi-Fi, Bluetooth, VPN, audio ingresso/uscita, luce notturna e scelta icone
usano il contenitore `WindowDialog` con il materiale satinato e i parametri
del profilo Sidebar. La sagoma resta il rettangolo originale: stesso raggio,
dimensioni, posizione, contenuto e animazioni; nessun rettangolo interno o
fascia aggiuntiva. Disattivando Glassy torna il riempimento originale.

Il vetro nativo viene composto sotto il contenuto Qt dell'intera superficie:
rendere trasparente un dialogo lasciava quindi leggibili i controlli della
sidebar sottostante. Una maschera Qt sul solo gruppo delle sezioni esclude
ora il rettangolo arrotondato occupato dal dialogo Glassy. All'esterno della
sagoma i controlli rimangono visibili. La maschera segue movimento e chiusura;
è disabilitata senza dialoghi o con Glassy spento. Il materiale del dialogo
ha precedenza sulle geometrie dei box sottostanti, mantenendo invariato il
formato dell'IPC e l'ordinamento degli altri materiali. Il plugin r26 già
caricato non è stato sostituito o ricaricato.

```sh
python3 tests/qml-load-check.py
python3 tests/glass-dialog-check.py
```

Il primo controllo usa finestre nascoste e verifica forma, materiale,
interruttori e chiusura. Il secondo esegue il codice effettivo della maschera
con Qt RenderControl e un framebuffer 320×240 su **CPU llvmpipe**, verificando
il renderer prima di disegnare. Controlla i pixel dentro/fuori la sagoma,
angoli arrotondati, movimento, toggle, riapertura, chiusura e ordinamento
delle richieste native. Non usa la GPU hardware e non misura le prestazioni
del desktop. Questi controlli passano; l'utente ha inoltre confermato nella
sessione reale che la forma è corretta e il vetro satinato non lascia più
leggibili i controlli sottostanti.

L'utente ha riferito una schermata di crash di Hyprland prima del riavvio
delle 12:52, senza dialoghi aperti. Nei dati locali consultati non risultano
nuovi report/coredump di Hyprland né errori GPU pertinenti; i due coredump
alle 12:44 e 12:52 appartengono a `kded6`. Non spiegano il sintomo riferito e
non escludono un errore del compositor. La causa resta non determinata.
Il recorder sul Raspberry falliva la connessione SSH (codice 255), perciò
non è disponibile quella raccolta esterna. Nessuna prova di stress GPU è
stata avviata durante questa verifica.

## Pillola volume e gesture della barra: r26 (12 novembre 2026)

La pillola fullscreen usa lo stesso profilo Glassy della barra e conserva il
proprio indicatore durante un cambio workspace, senza duplicarlo nella barra.
Resta in alto quando la barra è nascosta; quando questa compare scende dello
spazio occupato, seguendone anche lo scorrimento Qt e l'auto-hide. Il timeout
predefinito del volume è 2,5 secondi e riparte a ogni variazione o mute.

Hyprland mostra i layer Top all'inizio della gesture, prima di cambiare il
workspace attivo. La r26 osserva l'alpha reale dei layer durante i frame già
previsti dal compositor e invia `end4barvisibility` solo quando cambia lo stato.
Gli eventi sono separati per PID e monitor, con numero progressivo. QS legge
una fotografia iniziale tramite socket; una risposta vecchia non sovrascrive
eventi più recenti. Non sono aggiunti polling o frame forzati. Gli anchor
laterali distinguono la barra dalla pillola Overlay, pur condividendo il
namespace ottico. Annullare la gesture ripristina la posizione della pillola.

Build nativa completata e controlli CPU/QML software superati:

```sh
python3 tests/bar-visibility-check.py /percorso/sorgenti-patchati
python3 tests/volume-osd-check.py
python3 tests/qml-load-check.py
```

Passano anche buffer, profili, ottiche della barra e compatibilità del loader.
Questi controlli non sostituiscono la verifica visiva della gesture reale.
Il binario r26 è installato atomicamente per il prossimo logout/login, con
ABI e NODELETE verificati. La sessione aperta mantiene r25, senza ricaricamenti
del plugin. SHA-256:
`455f490ae6cb907565c4b1cb6e770605274aba3d85253cffc8f2a66f88513afe`.
Backup r25: `~/.cache/end4-pC/native-glass-backup-r25-20261112-114919/`.

Alla verifica delle 11:49 il recorder è in riavvio automatico: SSH termina con
codice 255. La raccolta esterna non è quindi confermata attiva; controllare il
collegamento al Raspberry prima di altre prove diagnostiche sui blocchi.

## Comando importante: fermare la raccolta dei log sul Raspberry

Da eseguire sul **PC Arch** per interrompere la registrazione:

```sh
systemctl --user stop end4-freeze-recorder.service
```

I log già salvati sul Raspberry restano disponibili. L'avvio automatico al
prossimo login rimane abilitato. Per riprendere subito la raccolta:

```sh
systemctl --user start end4-freeze-recorder.service
```

Il recorder salva anche il log dettagliato di Hyprland da
`$XDG_RUNTIME_DIR/hypr/*/hyprland.log`, che altrimenti scompare al riavvio.
I record `hyprland-log` contengono percorso, offset e testo: includono messaggi
del compositor e dei plugin, che possono riportare nomi di applicazioni o
finestre. Il file originale non viene modificato. La lettura avviene a 1 Hz,
fino a 64 KiB per file e ciclo; all'avvio conserva gli ultimi 64 KiB. Segue
anche nuove istanze, sostituzioni e troncamenti del log. Questo limite può
lasciare indietro il recorder se la produzione di log resta superiore.
`python3 tests/freeze-recorder-check.py` verifica anche questi casi senza GPU
o connessioni esterne.

**Stato attuale della Dashboard (10 novembre 2026, dopo le 16:16):** l'utente
ha visto la schermata di crash di Hyprland, poi ha aperto TTY3 ed eseguito
`reboot`; non ha dovuto spegnere forzatamente il PC. Il Raspberry
ha conservato sia il recorder principale sia la sonda temporanea. Il journal
registra un accesso a TTY3 e un riavvio tramite comando; non ci sono nuovi
coredump o errori AMDGPU pertinenti. I 19 campioni della sonda mostrano sei
tessere ferme, frost esattamente 8 e nessuna variazione delle geometrie: non
confermano le ipotesi su animazioni persistenti o soglie di sfocatura. Il sensore
GPU riporta 100%, ma questo dato da solo non identifica la causa del blocco.
Il precedente log dettagliato in `/run` non era incluso nella raccolta ed è
andato perso al reboot; l'assenza di coredump non smentisce il sintomo riferito.

Glassy resta attivo, `windowFrosted` incluso, e il recorder principale continua.
La Dashboard è stata chiusa e la sola sonda temporanea QML è stata rimossa.
La r23 è ora caricata, senza ricaricamenti del plugin nella sessione; nessuna
nuova prova automatica è stata avviata. Log e analisi privata:
`~/.local/state/end4-pC/diagnostics/20261110-dashboard-1616/`.
La correzione IPC resta applicata: il precedente test manuale riuscito non
dimostra l'assenza di ogni possibile blocco.

**Aggiornamento dopo il ritorno del calo (circa 19:10 CET):** la prima
conferma di fluidità non era sufficiente per considerare il problema risolto
in tutte le condizioni. Riattivare il campionatore non ha eliminato il calo.
A batteria, con profilo GPU `auto`, 200 letture in due secondi hanno rilevato
sempre 200 MHz, temperatura 46 °C e monitor a circa 60 Hz. Una prova manuale
di 20 secondi con il profilo driver `high` ha portato le letture a circa
530–985 MHz e l'utente ha confermato più fluidità. Il ripristino automatico
di `auto` ha riportato il rallentamento. Collegando poi l'alimentatore,
sempre in `auto`, la frequenza è salita intorno a 400–435 MHz e l'utente ha
confermato il recupero. Glassy e le impostazioni ottiche sono rimasti attivi.

Questo identifica una dipendenza dall'alimentazione e dal margine GPU;
non prova un difetto del driver dopo la sospensione né la causa del vecchio
crash. Il costo GPU del Glassy a batteria resta da ridurre. Non è stato
impostato un profilo energetico persistente: è attivo `auto`. Il confronto
temporaneo è concluso, con log privati verificati sul Raspberry. Il recorder
principale resta attivo e usa ora `xlini@192.168.1.199`, evitando le interruzioni
di risoluzione mDNS osservate con `raspberry.local`. Analisi e dati in
`~/.local/state/end4-pC/diagnostics/20261110-dashboard-power/`.

**Ottimizzazione r24 per la prova a batteria:** la passata Gaussian ora
calcola pesi e offset dei campioni una sola volta sulla CPU, poi li invia come
uniformi. Prima lo shader ripeteva `exp`, pesatura e normalizzazione del kernel
per ciascun pixel. Restano invariati raggio, numero di campioni, risoluzione,
passate e ottiche. Il guadagno sulla Radeon a batteria resta da verificare:
non è stato imposto un profilo GPU `high` persistente.

Il controllo software compila il blocco C++ effettivo di generazione dei
coefficienti e confronta il GLSL nuovo con il precedente: 102 immagini Gaussian
entro 1/255 per canale, con raggi frazionari e fino a 96 px, limiti 8/64 e
passate orizzontali/verticali ripetute. Passano anche i 192 confronti del
materiale Glassy e i controlli di buffer, profili, ottiche e loader. Mesa è
forzato su llvmpipe: questi test non misurano le prestazioni GPU reali.

Build r24 compilata con un solo processo, priorità bassa e limiti di memoria
850M + 128M swap; ABI e NODELETE verificati. Installata atomicamente e copiata
nello staging, con SHA-256
`d81a31ccc49b09d78ca9839ad80d7bc146346d343542e5eef8bc551cc7f68df9`.
Backup r23: `~/.cache/end4-pC/native-glass-backup-r23-20261110-193631/`.
La sessione corrente continua a usare r23: r24 si attiva al prossimo accesso
(o riavvio), senza ricaricare il plugin nativo durante la sessione. Il backend
mantiene tutte le capacità r23 e il test verifica che non tenti il ricaricamento.
Dopo il nuovo accesso, confrontare manualmente la stessa pagina Dashboard a
batteria con GPU `auto`; il recorder sul Raspberry resta attivo.

**Prova a batteria con r24 e preparazione r25:** l'utente riferisce un lieve
miglioramento ma ancora lag. R24 risulta effettivamente caricata; nei dodici
campioni dello stato rallentato la GPU resta a 200 MHz, le otto tessere sono
ferme e `regionWrites` non cambia. Negli 11 secondi tra gli estremi Hyprland
accumula circa 5,14 secondi di motore grafico e QS 1,77. Questi contatori non
misurano FPS né attribuiscono il tempo a una passata specifica. Dati privati:
`~/.local/state/end4-pC/diagnostics/20261110-dashboard-r24-battery/`.

R25 evita il percorso ottico nel centro piatto del materiale enhanced: lì
l'offset, il riflesso e l'ombra del bordo sono zero. Campiona direttamente la
stessa texture satinata/trasparente e mantiene opacità e antialiasing. Sui
bordi e negli angoli mantiene il percorso completo. Salta inoltre la correzione
colore che il renderer imposta a identità in enhanced e la norma a potenze
quando entrambe le distanze dell'angolo sono interne (il suo contributo è zero).
Il materiale classico continua a usare le correzioni colore configurate.

Passano 336 confronti del materiale e 102 della Gaussian su llvmpipe, entro
1/255 per canale: includono il confronto con il GLSL r24 reale, angoli asimmetrici,
forme con flares, dissolvenze, bordi sottili, materiali classico/enhanced e
roundingPower 1/2/2,5/4. Sono verificati anche i vincoli C++ sui valori neutri,
buffer, profili, ottiche e loader. Il guadagno a batteria resta da provare dopo
il nuovo accesso; nessuna riduzione di risoluzione o qualità è stata applicata.

R25 compilata con un solo processo, priorità bassa, MemoryMax 850M e swap
massimo 128M; ABI e NODELETE verificati. Binario installato atomicamente e
nello staging, SHA-256
`3dc0943b1869e4417f563c4f61be9ce14be253c7ecec6d18bab39d83bcc57d70`.
Backup r24: `~/.cache/end4-pC/native-glass-backup-r24-20261110-204316/`.
La sessione corrente usa ancora r24: r25 si attiva al prossimo accesso o
riavvio. Il loader conserva le capacità r24 senza tentare di ricaricare il
plugin. GPU `auto` e recorder principale restano attivi.

Per il calo persistente dopo il caricamento di nuove tessere sono ora attivi
due interventi QML/Qt: i Loader delle tessere Settings usano `asynchronous`,
mentre i titoli restano sincroni; QS usava `QSG_USE_SIMPLE_ANIMATION_DRIVER=1`
(rimosso il 14 novembre per il sovraccarico multi-finestra, descritto sopra).
Il primo distribuisce la creazione delle tessere su più cicli. Il secondo usa
il tempo reale anziché la stima adattiva del vsync per avanzare le animazioni,
un'opzione nativa [documentata da Qt](https://doc.qt.io/qt-6/qtquick-visualcanvas-scenegraph.html#driving-animations).
Nel sorgente Qt 6.11.1 il driver predefinito passa tra modalità vsync e timer
dopo frame lenti/veloci: è un meccanismo compatibile con il sintomo, non ancora
una diagnosi confermata. Non sono state cambiate le curve o eliminate le
animazioni, né modificato o ricaricato il plugin r23.

È stato riavviato solo QS; il log dell'istanza reale conferma
`Animation Driver: using QElapsedTimer` sia nel thread GUI sia nei thread di
rendering, mentre il PID Hyprland è rimasto 1716. Il test QML software verifica
che le tessere completino il caricamento anche a riposo e mantiene i controlli
di scorrimento e animazione; i controlli della Dynamic Island passano anche
con il driver temporale e il render loop threaded software. L'utente ha poi
confermato che il calo persistente non si ripresenta e la Dashboard resta
fluida o recupera da sola. La raccolta successiva contiene 570 campioni con
Dashboard e da 2 a 17 regioni; negli ultimi dieci campioni il contatore delle
geometrie resta fermo a 2885. La prova manuale supporta la correzione del
sintomo, senza misurare gli FPS o distinguere il contributo dei due interventi.
La causa esatta del crash precedente e l'assenza di futuri crash non sono
dimostrate. La raccolta temporanea del confronto è stata fermata e conservata;
il recorder principale dei crash resta attivo sul Raspberry.
`qs -c end4-pC ipc call glass geometry` legge le ultime geometrie applicate
senza forzare un ridisegno. La prova precedente non ha acquisito lo stato
rallentato: durante la raccolta la Dashboard risultava chiusa.

La r22 evita copia dello sfondo e blur della Dashboard quando il danno del
frame non interseca la finestra. Gli aggiornamenti delle geometrie confrontano
le superfici prima/dopo per namespace e monitor: cambiare le tessere della
Dashboard non invalida più automaticamente barra e dock, e un aggiornamento
della barra non invalida la Dashboard. Cambiamenti di materiale, rimozione
di superfici e attivazione/disattivazione restano inclusi nel confronto.

La lista Settings aggiorna la fascia di precaricamento una volta per riga,
anziché per ogni frazione di pixel del touchpad; le tessere visibili restano
precaricate e le animazioni di ingresso/uscita restano attive. La modifica
QML è disponibile subito. Shader, parametri ottici e animazioni non cambiano.

Verifiche senza nuovi benchmark GPU: build C++ completa; test delle risorse e
dei confronti tra superfici, ottiche della barra, profili, loader, mittenti IPC
su socket locali e componenti QML con rendering software. Il test QML verifica
anche che 99 piccoli movimenti non spostino la fascia di precaricamento e che
la fascia avanzi alla riga successiva. Il guadagno reale a riposo va misurato
dopo il nuovo accesso: il plugin attivo non è stato ricaricato. Build r22
installata e nello staging, hash SHA-256
`7c150e66d529ab8bec3178b5d02e2e4ea59ba5f9d181970850b4f73c987da77b`;
backup r21: `~/.cache/end4-pC/native-glass-backup-r21-20261110-153637/`.

La r22 ha dato un miglioramento riferito dall'utente, ma il calo resta con più
box. La r23 riduce il lavoro per pixel: calcola direttamente la distanza dei
rettangoli arrotondati senza flares/hangs; evita la normale della finestra che
le tessere sovrascrivono; salta la rifrazione al centro piatto, dove l'offset
è zero; interrompe la ricerca dei materiali sottostanti quando il pixel della
Dashboard è già coperto. Sui layer mantiene il calcolo completo del carrier,
necessario per rimuovere correttamente la maschera nera. Dissolvenze e bordi
parzialmente coperti continuano a comporre i materiali sottostanti.

`python3 tests/native-glass-shader-check.py SOURCE_DIR` confronta le immagini
del GLSL reale ottimizzato con il percorso r22, tramite EGL/GLES su llvmpipe
forzato (`LIBGL_ALWAYS_SOFTWARE=1`, `EGL_PLATFORM=surfaceless`), verificando il
renderer prima di disegnare. Non usa il compositor né la GPU hardware. Il test
richiede le librerie Mesa software già installate e usa due thread CPU. È ora
incluso in `build.sh`. Sono passati 192 confronti con 0/1/8/32 box, disposizioni
separate e annidate, angoli asimmetrici, flares/hangs, layer/finestra, opacità
1/0,6/0,02 e fascia 7%/24%, entro 1/255 per canale. Il riferimento ricostruito
dal test è stato confrontato anche con il sorgente r22 precedente. Questi sono
controlli di equivalenza, non misure di FPS sulla Radeon.

Build r23 compilata con un solo processo, priorità bassa, MemoryMax 850M e
swap massimo 128M; ABI, hash e NODELETE verificati. Installazione atomica per
il prossimo accesso, senza ricaricare il plugin attivo r22. SHA-256:
`1fbe089038695a04a71e47d38105469bdacee07bd82bdf4b31c1d8048df44df7`;
backup r22: `~/.cache/end4-pC/native-glass-backup-r22-20261110-155840/`.

Nella riproduzione precedente, iniziata dopo le 14:58 e prima della correzione
IPC, dopo circa 30 secondi di scorrimento l'interfaccia si è fermata;
Ctrl+Alt+F3 non ha mostrato una console e l'utente ha aspettato oltre due
minuti prima dello spegnimento forzato. Gli altri materiali e il recorder
restano attivi. Il plugin nativo non è stato ricaricato né modificato.

La nuova registrazione contiene 118 campioni consecutivi, dalle **15:01:36
alle 15:03:38 CET**, con il thread principale di Hyprland sempre in stato
`S`, attesa `unix_stream_read_generic` e contatore CPU fermo a 19.789 tick.
Anche i contatori dei thread QSGRenderThread restano fermi; QS conserva
attività CPU e il recorder continua a trasmettere. Il nuovo avvio inizia
alle 15:03:49. Non risultano esaurimento RAM/VRAM, timeout/reset GPU o nuovi
coredump nei dati conservati. Il log locale del kernel termina prima del
blocco: l'assenza di nuovi messaggi non esclude da sola un guasto del driver.

Nel [sorgente della versione installata di Hyprland](https://github.com/hyprwm/Hyprland/blob/a0136d8c04687bb36eb8a28eb9d1ff92aea99704/src/debug/HyprCtl.cpp#L2244)
il lettore IPC esegue letture bloccanti da 1.023 byte e continua se il blocco
è pieno. Un client che invia un multiplo esatto e aspetta la risposta senza
chiudere la scrittura può quindi fermare il ciclo del compositor. È un difetto
riprodotto sul socket locale e compatibile con il punto d'attesa registrato;
mancano però la richiesta esatta e il backtrace del vecchio processo per
attribuirgli con certezza questo blocco.

I mittenti QML di geometrie e profili ora aggiungono uno spazio finale solo
quando la lunghezza UTF-8 della richiesta è un multiplo di 1.023. I parser
nativi accettano spazi finali. `python3 tests/glass-ipc-check.py` riproduce
lo stallo del vecchio mittente su un server finto con timeout e verifica i
Socket QML reali ai limiti, con UTF-8 e richieste grandi, usando Qt offscreen
e rendering software. Questa correzione IPC non dimostra ancora la stabilità
del materiale Dashboard, ora riattivato per la prova richiesta. Copie private e analisi della
nuova prova: `~/.local/state/end4-pC/diagnostics/20261110-dashboard-freeze-1503/`.

Nella prima prova del 10 novembre erano disponibili 822 campioni remoti dalle 14:01:14 alle
14:14:57 CET, fino a circa 20 secondi prima dell'avvio successivo delle
14:15:17. Alla fine risultano circa 1,24 GiB di RAM disponibili e 1.000,5 MiB
di VRAM occupati su 2.048 MiB. Nei log raccolti non risultano OOM, timeout/reset
GPU o nuovi coredump. L'utente riferisce interfaccia e puntatore immobili,
con circa 45 secondi di attesa prima dello spegnimento forzato; Ctrl+Alt+F3
non è stato provato. Confrontando questa durata con i campioni remoti,
la raccolta e la rete risultano ancora operative durante almeno parte del
blocco visibile. Non era quindi fermo tutto il sistema per l'intera attesa.
La causa precisa resta sconosciuta: questi dati non distinguono QS, Hyprland
e le attese nel percorso grafico, né escludono un problema del driver GPU.
Il momento esatto dello spegnimento e il tempo di avvio del firmware non
sono misurati, quindi non si assegna un secondo preciso all'inizio del blocco.

I dati sono conservati sul Raspberry e copiati sul PC in
`~/.local/state/end4-pC/diagnostics/20261110-dashboard-freeze/`, con una
relazione `ANALISI.md`. Il vuoto dalle 13:51 alle 14:01 corrisponde a una
sospensione del PC; al risveglio la raccolta si è riconnessa automaticamente.
Il recorder ora include anche stato, CPU, memoria e punti d'attesa di Hyprland,
QS e QSGRenderThread, senza leggere argomenti o contenuti delle finestre.
La prima riattivazione del 10 novembre non ha quindi risolto il problema.
La nuova riproduzione è richiesta dall'utente e non viene eseguita automaticamente.

**Storico della sospensione:** il 7 novembre 2026 il PC si era bloccato
completamente durante lo scorrimento di Settings nella Dashboard. Puntatore
immobile per oltre 30 secondi e spegnimento forzato. Il journal dell'avvio
precedente terminava alle 19:28:49 CET, prima del riavvio delle 19:30:42,
senza timeout/reset GPU, OOM o crash Hyprland/Quickshell registrati nel tratto
finale e senza nuovi dump corrispondenti. Questo non identificava la causa e
non escludeva un blocco del kernel/driver senza registrazione persistente.

La sospensione sul backend r18 usava `windowFrosted: false`, fondi pieni e
nessuna cattura alternativa; animazioni e correzione dello scroll restavano
attive. La prova del 10 novembre aveva ripristinato il materiale della r21, senza
scaricare o ricaricare il plugin in Hyprland. Prima della riattivazione erano stati
verificati il flusso remoto dei log e i controlli software di capability,
caricamento QML e disattivazione tramite profilo Impostazioni.
Il benchmark GPU storico `tests/native-dashboard-check.py --reproduce-r18`
rimane escluso dall'esecuzione ordinaria e non viene lanciato automaticamente.

## Raccolta su Raspberry prima di una riproduzione

`scripts/glass/record-freeze.py` invia i messaggi del kernel e campioni di
memoria disponibile, swap, pressione CPU/memoria/I/O, carico GPU, memoria
grafica e stato dei processi grafici a un host SSH. Usa solo letture di `/proc` e `/sys`, `journalctl` e SSH;
non apre finestre, non riabilita Glassy e non modifica servizi o parametri del
kernel. I campioni arrivano circa una volta al secondo, non sono un benchmark.

Richiede un host SSH già verificato e autenticazione con chiave funzionante.
Non accetta automaticamente chiavi host nuove e non richiede password nello
script. Dal 10 novembre 2026 è verificato l'accesso senza password a
`xlini@raspberry.local`, raggiungibile anche come `xlini@192.168.1.199`.
Per autorizzare un nuovo PC, eseguire **dal PC sorgente** (non dal Raspberry):

```sh
ssh-copy-id -i ~/.ssh/id_ed25519.pub xlini@192.168.1.199
```

```sh
python3 tests/freeze-recorder-check.py
python3 scripts/glass/record-freeze.py xlini@raspberry.local --seconds 120
```

Il ricevitore crea un file nuovo con permessi 0600 in
`~/.local/state/end4-pC/freeze-*.jsonl` sul Raspberry; il percorso viene mostrato
quando il file è aperto. Il test software controlla JSON, permessi, messaggi
kernel, campioni, arresto e fallimento SSH usando endpoint locali, senza rete
o rendering. La ricezione reale è stata verificata il 10 novembre 2026:
file privato in crescita, campioni JSON con memoria/GPU e messaggi del kernel.

La raccolta continua è installata sul PC come servizio utente in
`~/.config/systemd/user/end4-freeze-recorder.service`, abilitato al login.
Lo stop segnala prima il processo Python (`KillMode=mixed`), permettendo la
chiusura del flusso SSH e il completamento del file remoto.
Esegue il recorder verso `xlini@raspberry.local` per 24 ore, poi riparte con
un file nuovo. Se la connessione fallisce, ritenta dopo 15 secondi.
Il Raspberry non richiede un nuovo servizio: il ricevitore usa la sessione SSH.

```sh
systemctl --user status end4-freeze-recorder.service
journalctl --user -u end4-freeze-recorder.service -n 20 --no-pager
# Sospendere fino al prossimo login oppure riavviare la raccolta:
systemctl --user stop end4-freeze-recorder.service
systemctl --user restart end4-freeze-recorder.service
# Disabilitare anche l'avvio automatico:
systemctl --user disable --now end4-freeze-recorder.service
```

Il percorso esatto del file corrente compare nel journal del servizio.
La verifica iniziale ha ricevuto 35 campioni, 50 messaggi kernel e i dati di
una GPU, senza riavvii del servizio. File iniziale sul Raspberry:
`~/.local/state/end4-pC/freeze-20261110T122122Z-d652301a.jsonl`.

I dati già ricevuti restano sul Raspberry se il PC si blocca, ma gli ultimi
eventi non ancora trasmessi possono mancare. Il lettore dei messaggi kernel è
separato dal campionamento: una lettura di stato della GPU bloccata non ferma
da sola l'invio dei messaggi kernel. Una disconnessione interrompe la raccolta
con errore; prima di una prova controllare la crescita effettiva del file remoto.
SSH sul PC non è necessario per questo invio verso il Raspberry; l'accesso
inverso di emergenza richiede una preparazione separata ed è ancora disattivato.

## Dock: magnification e sfondo satinato

Pin, separatori e pulsante della griglia applicazioni partecipano alla stessa
onda delle icone: ingrandimento dal bordo inferiore e spostamento orizzontale.
Il bordo inferiore delle immagini e dei simboli resta fermo durante l'ingrandimento:
lo spazio sotto l'icona non viene ingrandito verso l'alto insieme al pulsante.
Le icone vengono caricate alla risoluzione richiesta dall'ingrandimento massimo
configurato, usando il tema esistente (SVG inclusi). La dimensione della texture
resta fissa durante il movimento del mouse; pin e griglia usano QtRendering per
mantenere nitidi i simboli. Senza magnification si carica la risoluzione normale.
La distanza segue la curva di Build UI: ingrandimento lineare entro una fascia
finita attorno al puntatore e spinta laterale che raggiunge un limite per le icone
lontane. I valori di riferimento (icone da 40px, fascia 110px, spinta 40px a 2.25x)
sono proporzionati alla dimensione e all'ingrandimento configurati. Il calcolo usa
i centri originali, senza sommare le larghezze ingrandite o ricentrare la fila.
Scala e spostamento seguono direttamente il puntatore, senza molleggio. Lo sfondo
segue separatamente l'espansione dei due lati, anch'esso senza molle. La transizione
di ingresso e uscita dell'ingrandimento mantiene la sua interpolazione morbida. I separatori interni alle app registrano solo la linea, senza duplicare il
pulsante contenitore. In verticale o con magnification spenta tornano scala e
posizione originali.

Con Glassy lo sfondo della dock usa un solo materiale satinato, frost almeno 8,
senza riempimento opaco o contorno disegnati sopra. Il materiale conserva gli
angoli della modalità hug. Spegnendo lo sfondo si ritira anche il vetro; spegnendo
Glassy tornano riempimento e bordo configurati. La quarantena Dashboard resta attiva.

`python3 tests/dock-magnify-check.py` verifica i componenti reali con una finestra
nascosta e rendering software: bordo inferiore delle icone fermo da 1.2x a 2.2x,
registrazione, curva delle distanze ai limiti di influenza, separazione delle icone
del riferimento, movimento diretto senza molle, immagini ad alta risoluzione
senza ricaricamenti al movimento del mouse, elementi nascosti, modalità
verticale/disattivata e configurazione del materiale.
Il test simula solo l'associazione alla finestra per il calcolo e il movimento diretto,
poiché la finestra nascosta non crea un backing QWindow. Non è una prova GPU.

`node tests/dock-hover-check.js` riproduce il passaggio rapido app aperta → chiusa
→ aperta, includendo eventi di uscita ricevuti dopo l'ingresso nella nuova icona.
Solo il pulsante che possiede l'hover corrente può azzerarlo alla propria uscita.

Con `Glassy UI` e `Glass source → Windows underneath` attivi, il backend nativo
campiona il framebuffer del compositor a ogni frame disegnato. Segue quindi
contenuto animato, spostamenti e transizioni tra workspace, senza ricostruire lo
sfondo dalle singole finestre esportate a Quickshell.

Il rendering live è sempre attivo per questa sorgente. L'interruttore provvisorio
`True Glassy` è stato rimosso da entrambe le interfacce delle impostazioni;
un vecchio valore `trueGlassy: false` salvato nel profilo viene ignorato.

Il backend è una build locale di [HyprGlass v0.6.4](https://github.com/hyprnux/hyprglass/releases/tag/v0.6.4),
commit `22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5`, per **Hyprland 0.55.4**.
La patch in `scripts/glass/native/live-background.patch` disabilita la cache dei
layer, applica i filtri dei namespace anche dopo modifiche runtime e lascia
l'effetto sulle normali applicazioni disabilitato per impostazione iniziale.
Le revisioni da `end4-live-0.6.4-r2` possiedono e scollegano esplicitamente i listener
degli eventi. Usa inoltre il flag ELF `NODELETE`: il codice rimane mappato fino
all'uscita del processo, perché Hyprland/Hyprutils possono conservare oggetti e
puntatori a distruttori del plugin dopo lo scaricamento. Questo evita di
eseguire codice già rimosso dalla memoria durante la chiusura delle finestre.

`services/GlassCompositor.qml` limita il vetro ai namespace dell'interfaccia e
alla finestra Dashboard di questo processo Quickshell. Il cursore Glass intensity
controlla la sfocatura; non modifica l'opacità del testo o dell'intera finestra.
Quando il backend è attivo, WindowGlass interrompe le vecchie catture delle
finestre e il tracciamento delle coordinate delle finestre mobili.

La prima variante del materiale satinato sulle righe delle impostazioni è
stata ritirata dopo un blocco completo del PC segnalato il 7 novembre 2026,
con spegnimento forzato. Il benchmark breve aveva mostrato meno carico CPU,
ma non dimostra stabilità.
Il journal dell'avvio precedente termina alle 01:45:27 CET senza errori GPU,
OOM o lockup registrati nei minuti finali; non consente di attribuire il blocco
a un componente preciso.

Il blocco è avvenuto durante lo scorrimento, con puntatore immobile. L'analisi
statica individua un'amplificazione da verificare: `queueRegions()` accorpa gli
aggiornamenti per giro dell'event loop, senza un limite per fotogramma, e ogni
comando `end4glass` invalida tutte le layer del processo, anche quelle con
geometria invariata. Questo può aumentare il lavoro durante lo scorrimento;
non dimostra la causa del blocco. La nuova variante accorpa gli aggiornamenti
di scorrimento una volta per fotogramma; il comportamento dei danni nel backend
nativo rimane invariato.

Lo scorrimento delle impostazioni usa il gestore `TouchpadScrollArea` già
presente nel progetto anche quando l'accelerazione personalizzata è spenta:
in questo caso segue i pixel del gesto con fattore 1, senza inerzia aggiunta
da Qt. Con l'accelerazione attiva resta il gestore esistente e mantiene i
fattori configurati; i due non intercettano contemporaneamente gli eventi.
La rotellina conserva il percorso nativo. La ricerca interrompe la propria
animazione quando parte un gesto diretto. Il tentativo di allineamento forzato
ai pixel è stato rimosso: non risolveva il tremolio segnalato e arrotondava i
piccoli incrementi del fallback angolare. L'utente ha confermato risolto il
tremolio sul touchpad; questo non dimostra la risoluzione del blocco del PC.
La diagnostica temporanea è stata rimossa.

Le righe della finestra Impostazioni classica usano ora lo stesso frost della
barra laterale quando Enhanced e il backend satinato nativo sono attivi.
Il contesto dei delegate è vincolato con `ComponentBehavior: Bound`;
la pagina aggiorna le geometrie una volta per fotogramma e ritaglia le regioni
al viewport, senza osservatori degli antenati per riga. La sfocatura condivide
il buffer del backend già usato dalle altre superfici. Nel controllo software con
backend simulato, 30 righe producono 6 regioni visibili e 80 spostamenti
accorpano un solo aggiornamento. La singola prova nativa isolata autorizzata
dall'utente ha verificato 11 righe visibili su 115, un solo aggiornamento per
la raffica di scorrimento e 24 pixel di controllo dei pulsanti durante gli
spostamenti della finestra. Questa prova breve non dimostra stabilità prolungata.

```sh
node tests/glass-backdrop-check.js
python3 tests/native-settings-check.py --plugin $HOME/.cache/end4-pC/native-glass-staged/hyprglass.so --blur-rules
```

## Compilazione e verifica

### Contrasto adattivo delle impostazioni (r17)

Il contrasto adattivo sceglie testo e icone chiari (`#e7edf2`) o scuri (`#1b2229`)
in base alla luminosità locale dietro le etichette delle impostazioni classiche.
Il colore si aggiorna ogni 1,25 secondi, un secondo in più rispetto alla prima
versione. I testi sui controlli
con sfondo colorato mantengono i colori del tema. La selezione usa il rapporto
di contrasto e conserva il colore precedente vicino alla soglia quando rimane
leggibile, per limitare l'oscillazione. Quando entrambi i toni smorzati restano
sotto il rapporto 4,5:1, conserva l'isteresi invece di alternarli a ogni lettura.
Ogni etichetta conserva un colore unico.

Il compositor campiona soltanto le impostazioni aperte, su richiesta del loro
processo, in una griglia di 32×24 punti, al massimo quattro volte al secondo.
Trasferisce i pixel tramite PBO e legge il risultato soltanto dopo una fence
segnalata, con attesa zero; a QML invia solo la luminanza. Il polling non avvia
nuove catture a pannello fermo. Un campione in ritardo mantiene l'ultimo colore;
un backend assente o non disponibile conserva i colori del tema. Il meccanismo
segue l'uso dei [PBO e delle fence documentato da Khronos](https://wikis.khronos.org/opengl/Pixel_Buffer_Object).

Compilazione, caricamento QML software, selezione del contrasto e rilascio delle
risorse superano i controlli software. La prima prova nativa ha individuato
la cancellazione dei campioni alla normale chiusura del socket IPC: una risposta
valida ora rimane disponibile dopo la disconnessione. La verifica software
esercita il socket reale con un server temporaneo e controlla anche il ritorno
ai colori del tema quando la connessione fallisce.

La seconda prova nativa isolata supera cinque scenari (nero, bianco, divisione
orizzontale, divisione verticale, ritorno al nero), controllando 38 etichette,
24 pixel dei pulsanti durante gli spostamenti, clipping delle righe e accorpamento
degli aggiornamenti di scorrimento. A pannello fermo il polling del contrasto non
riscrive le geometrie. Non è una prova di stabilità prolungata o di sospensione.

La r17 è stata verificata e installata; la sessione successiva ne ha confermato
il caricamento. La copia precedente è in
`~/.cache/end4-pC/native-glass-backup-r16-xl5ta1_8`.
Il crash del 7 novembre alle 16:28 è invece registrato da Quickshell come
`Tried to show lockscreen surfaces without active lock`, durante l'attivazione
del blocco schermo prima della sospensione; il nuovo contrasto era inattivo.
Il percorso di ricarica del blocco schermo è stato poi riprodotto e corretto
il 14 novembre, come descritto all'inizio di questo documento.

```sh
node tests/glass-contrast-check.js
python3 tests/native-settings-check.py --plugin /path/to/r17/hyprglass.so --blur-rules --contrast
```

### Schede satinate della Dashboard (r18)

Il percorso seguente è attualmente disabilitato dopo il blocco descritto all'inizio
di questo documento; le verifiche precedenti restano documentate come riferimento.

Il componente comune `DashboardCard` usa lo stesso materiale satinato dei box
interni della sidebar, con intensità minima 8 e una velatura al 72% che conserva
il colore della scheda. Copre Home e schede delle impostazioni in stile Dashboard;
il percorso Media con copertina sfocata mantiene la sua sorgente. Disattivando
Glassy tornano i colori pieni precedenti.

La Dashboard è una finestra normale, diversa dalle layer delle impostazioni
classiche. La r18 accetta geometrie locali solo per la finestra delle impostazioni
del processo Quickshell che le invia, su output non ruotati. Le schede visibili
condividono un solo buffer di satinatura; quelle fuori dal viewport vengono
escluse. Restano i limiti di 32 regioni e la gestione esistente delle animazioni.
Il canale alfa della finestra viene predisposto prima dell'apertura, anche se
il backend diventa disponibile più tardi, per evitare un fondo nero.

La serializzazione limita i raggi alle dimensioni già arrotondate del rettangolo:
durante lo scorrimento una striscia sottile non può più produrre un raggio appena
oltre la metà dell'altezza e far rifiutare l'intero aggiornamento. Le dimensioni
che arrotondano a zero vengono escluse. Il controllo `glass-backdrop-check.js`
include questi casi. Il rilascio dei buffer della finestra conserva i binding
OpenGL di lettura e scrittura, verificati da `native-glass-buffer-check.py`.

La prova nativa isolata verifica 6 schede della Home, 10 delle impostazioni e
8 dopo lo scorrimento, su 13 schede precaricate. La deviazione della trama di
sfondo scende da 108,93 nel vetro trasparente a 0,80 nel satinato. A finestra
ferma non vengono riscritte le geometrie e tre fotogrammi dopo la chiusura
conservano lo sfondo. Il test applica `no_blur` alla finestra come il desktop
reale: il blur standard di Hyprland sopra quello nativo nasconderebbe la
differenza tra i materiali. È una verifica breve, non di stabilità prolungata.

La r18 verificata è installata, nella directory di staging e caricata nella
sessione principale dopo il logout/login. Backup di binario e manifest precedenti:
`~/.cache/end4-pC/native-glass-backup-r17-75aqdia0`.

Lo scorrimento della tab Settings usa ora il percorso diretto del touchpad
anche quando l'accelerazione personalizzata è disattivata, con fattore e
sensibilità 1. L'animazione di navigazione è separata da `contentY`: l'input
diretto la interrompe e una ricerca o un cambio gruppo annullano la destinazione
precedente. I test software verificano piccoli passi, inversioni e posizione
invariata dopo la fine del gesto.

Le tessere ricreate nel margine di precaricamento mentre si scorre conservano
l'animazione originale di ingresso, come richiesto dall'utente. L'uscita al cambio
pagina ferma prima l'ingresso eventualmente ancora in corso, evitando che due
animazioni scrivano le stesse proprietà. Il test software verifica stato iniziale,
avanzamento dell'ingresso e completamento dell'uscita.

Il viewport accorpa il tracciamento dello scroll per fotogramma; ogni scheda
osserva solo la propria animazione e il suo Loader, evitando di ricostruire la
geometria di tutti gli antenati. La prova nativa controlla anche una raffica di
80 movimenti consecutivi; attende poi la fine delle animazioni prima di verificare
geometrie ferme, satinatura e chiusura.

Il primo confronto breve di quattro secondi, che sopprimeva l'ingresso durante
lo scroll, misurava circa 24,25 contro 12,51 ms di tempo CPU di Quickshell per
fotogramma e costo GPU simile (5,14 contro 5,20 ms/fotogramma). Questi numeri
precedono il ripristino delle animazioni durante lo scroll. Le correzioni sono
solo QML e non richiedono un nuovo logout.

Ripetendo il confronto con gli ingressi ripristinati, il tempo CPU di Quickshell
misurato passa da 23,93 a 13,62 ms/fotogramma (circa −43%); il tempo GPU è
5,09 contro 5,28 ms/fotogramma, senza nuove allocazioni di texture. La misura
breve usa lo stesso plugin r18 e passi sintetici del touchpad in profili isolati;
non dimostra stabilità prolungata né garantisce gli stessi FPS in ogni scena.

```sh
node tests/glass-backdrop-check.js
python3 tests/qml-load-check.py
# NON eseguire come controllo ordinario: riproduzione del percorso in quarantena.
# python3 tests/native-dashboard-check.py --plugin /path/to/r18/hyprglass.so --reproduce-r18
```

### Backend nativo

Richiede gli strumenti di compilazione e gli header della stessa versione del
compositor in esecuzione. Lo script non installa pacchetti, non modifica la
configurazione di Hyprland e non carica il plugin nel desktop.

```sh
bash scripts/glass/native/build.sh $HOME/.cache/end4-pC/native-glass-staged
python3 tests/native-glass-loader-check.py
python3 tests/native-glass-motion-check.py --plugin $HOME/.cache/end4-pC/native-glass-staged/hyprglass.so
python3 tests/native-glass-motion-check.py --plugin $HOME/.cache/end4-pC/native-glass-staged/hyprglass.so --legacy
python3 tests/qml-load-check.py
python3 tests/popup-window-check.py
```

La prova di movimento richiede una sessione Wayland, `grim` e Pillow già
installati. Avvia un Hyprland annidato con profili temporanei e il componente
WindowGlass del progetto. Controlla pixel animati attraverso il vetro e due
workspace, quindi verifica scaricamento, ricaricamento e uscita regolare del
compositor prima di terminare i processi di prova. I workspace del desktop principale
non vengono cambiati. Le altre prove impostano `QS_DISABLE_COMPOSITOR_GLASS=1`
per non configurare il backend del desktop principale.

## Attivazione

Caricare codice nativo dentro Hyprland può terminare l'intera sessione in caso di
incompatibilità o errore. Salvare il lavoro prima della prima attivazione.
Dopo la verifica del binario, copiare **entrambi** i file preparati:

```sh
mkdir -p ~/.local/share/end4-pC/native-glass
install -m755 ~/.cache/end4-pC/native-glass-staged/hyprglass.so ~/.local/share/end4-pC/native-glass/.hyprglass.so.new
mv -f ~/.local/share/end4-pC/native-glass/.hyprglass.so.new ~/.local/share/end4-pC/native-glass/hyprglass.so
install -m644 ~/.cache/end4-pC/native-glass-staged/manifest.json ~/.local/share/end4-pC/native-glass/.manifest.json.new
mv -f ~/.local/share/end4-pC/native-glass/.manifest.json.new ~/.local/share/end4-pC/native-glass/manifest.json
```

Con Glassy UI e Windows underneath selezionati, Quickshell verifica
il backend all’avvio, al cambio di modalità e dopo il ricaricamento di Hyprland. Il loader controlla l'hash del binario e l'ABI del compositor prima
di caricarlo. Un aggiornamento incompatibile di Hyprland richiede una nuova
build supportata: il loader rifiuta quella precedente. Un HyprGlass di versione
diversa già caricato viene lasciato intatto.

Senza un backend compatibile viene usato il precedente metodo a catture, che
rimane una ricostruzione approssimata e può scattare durante le transizioni.

## Disattivazione e limiti

Selezionare `Glass source → Wallpaper` oppure disattivare Glassy UI: il servizio
disabilita l'effetto nativo. Per rimuovere anche il codice dal compositor:

```sh
hyprctl plugin unload ~/.local/share/end4-pC/native-glass/hyprglass.so
```

Il comando rimuove gli effetti e i listener; per liberare anche il codice
mappato occorre terminare la sessione. Non scrivere dentro un binario già caricato:
una sostituzione deve creare un nuovo inode e rinominarlo atomicamente. La nuova
build va caricata soltanto nella sessione successiva.

Questa versione usa la geometria del layer per la rifrazione e la sua maschera
alpha per ritagliare il vetro: il bordo ottico non segue con precisione ogni
singolo widget dentro un layer che occupa tutto lo schermo. Il costo GPU cresce
con l'area del vetro e il movimento sottostante; viene usata una sola iterazione
di blur. Wallpaper e schermata di blocco mantengono il loro percorso dedicato.

## Verifica dopo il riavvio del 5 novembre 2026

Nel journal del boot precedente i cinque SIGSEGV delle 15:16–15:22 riguardano
`Hyprland --config /tmp/hg-*/hyprland.conf`, cioè i compositor di prova. Il servizio
principale risulta arrestato durante il riavvio richiesto alle 15:22:28. Nessun
HyprGlass era installato/caricato nel desktop principale.

La prova completa della revisione r2 ha superato movimento, cambio di workspace,
scaricamento/ricaricamento e uscita con codice 0. Anche compilazione dei componenti
QML, aperture ripetute dei popup e controlli del loader ABI/hash sono passati.
Le prove annidate disabilitano l'integrazione systemd e rimuovono NOTIFY_SOCKET
per non inviare notifiche di sessione al servizio del desktop principale.

## Attivazione nella sessione reale

Il backend r2 è installato in `~/.local/share/end4-pC/native-glass/`.
Il loader rileva il parser tramite una valutazione Lua senza effetti collaterali.
Con il parser Lua i parametri vengono applicati con `hl.config()` e i tag con
`hl.dispatch(hl.dsp.window.tag(...))`; il parser legacy conserva `keyword` e
`dispatch tagwindow`. Il test di movimento usa Lua per impostazione iniziale;
`--legacy` verifica il percorso precedente.

Lo stato del servizio e del pannello si può leggere senza modifiche:

```sh
qs -c end4-pC ipc call glass status
qs -c end4-pC ipc call settings glassStatus
hyprctl getoption plugin:hyprglass:layers:enabled -j
```

Verifica reale: servizio attivo con parser Lua, pannello nativo con colore
`#00000000`, intensità 8.5 mappata a blur_strength 2.125. Durante il passaggio al
workspace con Firefox, il vetro mostra e sfoca i colori della finestra sottostante.
Il workspace originale viene ripristinato al termine della verifica.

## True Glassy e attività periodiche

`Interfaccia → Trasparenza → True Glassy` (anche nella Dashboard):

- Attivo: vetro nativo che segue i pixel disegnati da Hyprland.
- Disattivo: precedente percorso Quickshell a catture; le finestre sottostanti
  rimangono la sorgente, con i limiti della ricostruzione durante le transizioni.

L'opzione mantiene attiva la modalità corrente per impostazione iniziale.
Disattivarla spegne gli effetti del plugin sui layer e rimuove il tag dalla
Dashboard; il codice della libreria resta mappato fino al termine della sessione.

Il servizio non esegue più il controllo del plugin ogni 10 secondi e non applica
nuovamente parametri identici quando cambia l'elenco finestre. Il contatore
`writes` in `glass status` permette di controllare le riconfigurazioni effettive;
`captures` indica i consumatori del vecchio percorso. Le coordinate vengono
aggiornate nei frame già prodotti dalla finestra, senza una FrameAnimation che
forzi continuamente nuovi frame anche sulle superfici ferme.

Il test isolato verifica entrambi i passaggi dell'interruttore e che aggiornamenti
dell'elenco finestre invariati non riscrivano i parametri. Rimuovere questo lavoro
superfluo non misura da solo tutti i possibili blocchi di GPU o compositor.

## Impostazioni: crash Qt dopo la ripresa del 5 novembre, ore 17:51

Il rapporto `~/.cache/quickshell/crashes/7ha2q2c1ot/report.txt` riporta un SIGSEGV
nel thread grafico, dentro `QQuickItemPrivate::addToDirtyList()` durante
`QQuickWindowPrivate::syncSceneGraph()`. Il log immediatamente precedente ripete
`Cannot use same item on different windows at the same time`. La ripresa dalla
sospensione risulta nel kernel alle 17:50:49; il crash alle 17:51:31.

Le impostazioni classiche ora creano il contenuto in modo asincrono soltanto
quando la finestra è aperta e lo distruggono alla chiusura, mantenendo l'indice
della pagina selezionata. Le pagine e il profilo si caricano alla prima visita:
è stato rimosso il precaricamento forzato di tutte le pagine nascoste e
l'azzeramento globale di `Config.readWriteDelay`. WindowGlass rilascia i propri
effetti quando la finestra non è visibile.

```sh
python3 tests/settings-window-check.py
```

La prova usa le impostazioni reali con preferenze isolate e rendering hardware:
12 cicli di apertura/chiusura, modalità senza vetro, wallpaper e catture delle
finestre, navigazione Interfaccia e profilo, assenza di pagine non visitate e di
riferimenti alle pagine dopo la chiusura. Non simula una sospensione hardware:
la riproduzione del crash originale dopo la ripresa resta da verificare.

## Ottimizzazione dei buffer: revisione r3

Ogni layer e decorazione conserva ora il proprio buffer temporaneo del blur.
Il buffer globale precedente veniva riallocato passando tra superfici di
dimensioni diverse, anche se ciascuna superficie rimaneva ferma. Ora viene
riallocato solo al cambio della sua dimensione e rilasciato con la superficie.
Il compromesso è un buffer aggiuntivo per ogni superficie contemporaneamente
presente, anziché un unico buffer condiviso. Campionamento live, risoluzione
del blur, intensità e frequenza del rendering rimangono invariati.

La prova con barra e pannello di dimensioni diverse, stesso compositor annidato
e stessa animazione, ha intercettato le chiamate reali a `glTexImage2D` del solo
compositor: **896 → 2 allocazioni per ciascuna delle due dimensioni del blur**
(535×111 e 535×571). Sono conteggi di allocazioni, non misure di FPS o una prova
che i blocchi periodici siano risolti. Il controllo dei pixel animati, dei
workspace e del ciclo scaricamento/ricaricamento/uscita passa con entrambe le
build. Il test include ora una seconda superficie di dimensione diversa.

Il controllo minimo usa il codice reale di acquisizione del buffer, con
framebuffer simulati, per verificare 120 frame alternati senza riallocazioni,
il ridimensionamento e il rilascio:

```sh
python3 tests/native-glass-buffer-check.py /percorso/sorgenti-hyprglass-patchati
```

`build.sh` esegue il controllo prima della compilazione. Il Makefile patchato
segue anche le dipendenze degli header, per evitare build parziali incompatibili
quando cambia la struttura dello stato del plugin.

Il loader accetta r2 e r3: la sessione corrente può continuare a usare r2 mentre
la nuova build attende una nuova sessione. Non scaricare e ricaricare una build
diversa nello stesso processo Hyprland: il codice precedente rimane mappato.

La build r3 è preparata nella directory di staging e installata con sostituzione
atomica in `~/.local/share/end4-pC/native-glass/`. Alla verifica finale la sessione
reale continua correttamente a usare r2, con zero consumatori del vecchio percorso.
Il backup precedente è in
`~/.cache/end4-pC/native-glass-backup-r2-20261105-184718/`.
Per usare r3 occorre uscire e rientrare nella sessione Hyprland; riavviare soltanto
Quickshell non sostituisce il plugin già mappato nel compositor. Dopo il nuovo
accesso va ripetuta la misura durante l'uso reale per valutare i blocchi periodici.

## Enhanced: revisione r4

`Interfaccia → Trasparenza → Enhanced`, anche nella Dashboard, abilita l'ottica
calibrata con la prova trascinabile: **fascia al 7% del lato corto** e
**rifrazione al 135%**. È disattivata inizialmente; spegnendola torna lo stile
precedente, conservando le ottimizzazioni dei buffer della revisione r3.
La scelta dell'utente è **barra trasparente, pannelli satinati**. Il centro della
barra viene campionato senza blur, tinta o lente centrale. Il cursore Glass
intensity regola la sfocatura dei pannelli. Il backend a wallpaper/catture usa
la stessa taratura nel componente FrostedGlass.

La patch ottica è integrata in `live-background.patch`, insieme al percorso r3
precedente. `backend.py` accetta r2/r3 durante l'aggiornamento e dichiara la
capacità Enhanced soltanto per r4. Una libreria già mappata non viene sostituita
nel processo: l'installazione atomica prepara r4 per il prossimo accesso.
La build r4 è installata e nella directory di staging. La verifica finale del
desktop mostra ancora r3 attivo, `captures: 0` e `regionWrites: 0`, con Enhanced
disattivato. Il backup r3 è in
`~/.cache/end4-pC/native-glass-backup-r3-20261105-232639/`.
Occorre uscire e rientrare nella sessione prima di attivare l'effetto nativo
Enhanced; riavviare soltanto Quickshell non cambia il codice mappato da Hyprland.

### Geometrie delle singole card

WindowGlass registra geometria, quattro raggi, raccordi e opacità delle card nel
servizio GlassCompositor. Le variazioni di geometria e dei trasformatori Scale e
Translate accodano un aggiornamento coalescente. Non c'è un timer periodico né
un'animazione che forzi frame; geometrie identiche non producono messaggi.
Il servizio usa Socket di Quickshell direttamente sul socket IPC di Hyprland:
non avvia un processo hyprctl per aggiornare le card.

Il comando nativo `end4glass` verifica il PID del mittente con le credenziali
raccolte da Hyprland e valida l'intero messaggio prima di sostituire i dati.
La geometria è limitata a 32 superfici per processo e 32 card per superficie,
con dimensioni/raggi finiti e messaggi fino a 32 KiB. Lo shader segue i bordi di
ogni card, inclusi i raccordi; rimuove il marcatore nero semitrasparente usato
da Qt senza aggiungere una velatura. Conta anche i marcatori sovrapposti.

Limiti intenzionali: layer su monitor ruotati mantengono lo stile standard;
la gestione dei trasformatori dell'output richiede un'estensione del protocollo
geometrico. Due finestre dello stesso processo con namespace, monitor e dimensioni
identici non vengono confuse: in quel caso l'ottica usa la geometria del layer.
Identificatori Wayland unici eliminerebbero questa ambiguità. Le finestre floating
Dashboard usano la geometria e l'arrotondamento già noti a Hyprland.

## Raccordo ottico degli angoli: revisione r5

Quando la fascia al 7% supera il raggio dell'angolo, le normali del bordo
arrotondato si incontrano prima della fine della rifrazione. La distanza dalla
forma rimane continua, ma la sua direzione cambia bruscamente sulla diagonale,
producendo uno spigolo visibile nel contenuto rifratto.

Per le card senza raccordi aggiuntivi, la fascia ora si restringe vicino agli
angoli e si spegne prima di quel salto. Il raggio visibile, la rifrazione al
135% e la fascia al 7% sui tratti dritti rimangono gli stessi. La correzione è
applicata allo shader nativo e al percorso wallpaper/catture; non aggiunge
campioni di texture, timer o buffer.

La prova WebGL verifica tutti e quattro gli angoli con raggi 0, 8, 16 e 52 px,
sia per finestre sia per card dentro un layer. Legge lo spostamento effettivo
dallo shader: r4 fallisce con il raggio 16 px, r5 supera il controllo.
Il loader conserva Enhanced anche mentre una sessione r4 attende il nuovo accesso.

La build r5 ha superato anche movimento/workspace e ciclo completo del plugin
nel compositor annidato, oltre alle aperture ripetute dei popup Quickshell.
È installata e nella directory di staging; la sessione reale mantiene r4 fino
al prossimo accesso. Il backup precedente è in
`~/.cache/end4-pC/native-glass-backup-r4-20261105-235550/`.

## Rifrazione interna agli angoli: revisione r6

La r5 eliminava il salto spegnendo la rifrazione sulla diagonale interna agli
angoli stretti. Questo rendeva continua l'immagine, ma non riproduceva la curva
della prova: il contenuto interno non veniva più ripiegato in quella zona.

La r6 mantiene la fascia al 7% e raccorda la direzione della normale verso una
curva interna più larga quando il raggio esterno è minore della fascia. Sul
contorno usa ancora la normale della curva reale. La rifrazione continua a
campionare lo sfondo interno oltre il punto in cui le normali originali si
incontravano. Il centro piatto e i tratti dritti mantengono la taratura precedente.
La stessa correzione è presente nel percorso wallpaper/catture.

La prova WebGL richiede ora uno spostamento verso l'interno su entrambi gli assi
anche sulla diagonale dell'angolo, oltre alla continuità. La r5 fallisce questo
requisito. La prova nativa disegna una cornice blu e un interno verde: un pixel
dei quattro angoli situato sul blu deve mostrare il verde interno rifratto.

Entrambe le prove passano, insieme a movimento/workspace, ciclo del plugin e
aperture ripetute dei popup. La r6 è installata e nella directory di staging;
la sessione principale continua a usare r5 fino al prossimo accesso. Il backup è
`~/.cache/end4-pC/native-glass-backup-r5-20261106-001431/`.

## Eliminazione della piega diagonale: revisione r7

La r6 raccordava la direzione, ma usava ancora la distanza geometrica minima
per l'intensità della rifrazione. All'interno del centro di curvatura questa
distanza passa dal lato orizzontale a quello verticale: è continua, ma la sua
derivata cambia sulla diagonale. Una cifra sullo sfondo rendeva visibile la piega.

La r7 calcola anche la profondità ottica lungo il raggio del raccordo interno,
intersecandolo con il lato oppure con l'arco reale dell'angolo. Il ritaglio resta
quello della card; direzione e intensità seguono ora una geometria curva nella
fascia attiva. Il calcolo aggiuntivo riguarda gli angoli più stretti della fascia;
non aggiunge campioni di texture o buffer.

La prova WebGL legge la profondità dallo shader a precisione di due canali e
misura la variazione ai due lati della diagonale, con raggi 8 e 16 px e tutti
e quattro gli angoli. La r6 mostra una piega di circa 2 px; la r7 passa la
soglia di 0,8 px sulla stessa geometria. La scena nativa include anche quattro
cifre “6” come riferimento visivo.

Il calcolo analitico usa gli archi circolari delle card. Le eventuali finestre
floating con superellissi non circolari conservano la profondità del compositor;
estendere la correzione a quelle forme richiede l'intersezione con la superellisse.

La r7 supera la prova WebGL, la prova nativa completa e le aperture ripetute dei
popup. Il confronto delle cifre usa due acquisizioni della stessa scena con r6
e r7; il test attende che il monitor annidato si stabilizzi dopo il ridimensionamento
del suo contenitore e misura la barra fuori dall'avviso del compositor di prova.
La build è installata e nella directory di staging, con backup in
`~/.cache/end4-pC/native-glass-backup-r6-20261106-003925/`.
La sessione corrente mantiene r6 fino al prossimo accesso.

## Larghezza della fascia sui pannelli grandi: revisione r8

La fascia proporzionale cresceva fino a 50,4 px nelle impostazioni standard
(980×720), contro un raggio di 23 px. La prova originale usava una fascia di
circa 20 px. La r8 mantiene il 7% del lato corto con un massimo di **20 px
logici**; i widget il cui lato corto non supera circa 286 px mantengono la
larghezza precedente. La rifrazione rimane al 135%.

Il percorso nativo converte il limite in pixel del framebuffer usando la scala
del monitor. Il percorso wallpaper/catture applica il limite alle coordinate
logiche dell'elemento. La prova WebGL controlla widget piccoli, pannelli
980×720 e il limite fisico di 40 px per una scala doppia, sia per finestre sia
per card dentro layer. Mantiene inoltre i controlli delle curve senza limite.

La scena nativa include un pannello 800×720 con raggio 23: un campione a 28 px
dal lato deve conservare lo sfondo originale, poiché è oltre la fascia da 20 px.
La vecchia fascia lo rifrangeva. Le cifre “6” restano sui quattro angoli per il
confronto visivo della stessa geometria prima e dopo il limite.

Le prove WebGL, native e di apertura ripetuta dei popup passano. La r8 è
installata e nella directory di staging; la sessione principale mantiene r7
fino al prossimo accesso. Il backup è
`~/.cache/end4-pC/native-glass-backup-r7-20261106-105630/`.

```sh
qs -c end4-pC ipc call glass status
hyprctl end4glass
```

Lo stato Quickshell espone `enhanced`, `enhancedAvailable` e `regionWrites`.
Il comando nativo senza argomenti espone conteggi di superfici, card e aggiornamenti.
Il test nativo verifica il passaggio Enhanced/stile precedente, card distinte
nello stesso layer e card sovrapposte, barra nitida senza tinta, rifrazione dei
bordi delle card, modifiche di posizione/Scale e assenza di messaggi ripetuti
quando la geometria rimane ferma. Conserva le prove di movimento, workspace,
scaricamento/ricaricamento e uscita regolare del compositor.
È verificato anche il rifiuto di messaggi che dichiarano il PID di un altro
processo e il ripristino delle geometrie dopo il ricaricamento del plugin.

### Prova ottica nel browser

`tools/glass-optics-preview.html` conserva la taratura scelta e si può trascinare
sopra la fotografia di MagicForestPass. Il centro del materiale Trasparente è
nitido; Satinato permette di regolare il blur. Si può caricare un'altra immagine
localmente. La foto è incorporata: il file non richiede un servizio esterno.
Le tre immagini IMG_0935–0937 mostrano il vetro in movimento sopra contenuto
fermo, ma non ne forniscono la geometria completa o la scala logica del dispositivo:
7% e 135% sono una taratura visiva approvata dall'utente, non misure fisiche.

La prova incorpora lo stesso fragment shader nativo con Enhanced attivo;
cambia soltanto la mappatura della texture sullo sfondo del browser. La sfocatura
della fotografia viene preparata al cambio del cursore, mentre il plugin usa il
proprio blur GPU. La prova del browser isola una singola forma; la prova Hyprland
copre il protocollo e la composizione di più card.

```sh
python3 scripts/glass/native/preview.py /percorso/sorgenti-patchati tools/glass-optics-preview.html /percorso/foto.webp
python3 tests/native-glass-optics-check.py tools/glass-optics-preview.html
python3 tests/native-glass-buffer-check.py /percorso/sorgenti-patchati
```

Il controllo browser usa un profilo temporaneo e un server su localhost:
verifica compilazione GLSL, centro nitido, direzione normale al bordo, campioni
spostati, sfondo fisso e movimento, rifrazione zero e materiale satinato.
Il controllo C++ verifica anche il rifiuto di geometrie malformate senza
sovrascrivere i dati validi, oltre al riuso/rilascio dei buffer.


## Impostazioni: buffer ritagliati nella revisione r9

Con Enhanced, il layer delle impostazioni occupa tutto il monitor per consentire
trascinamento e gestione dei clic esterni. La r8 campionava e sfocava quindi
l'intero layer, anche se il pannello visibile era molto più piccolo.
La r9 ritaglia i buffer di campionamento e blur all'unione delle card registrate,
con un margine per rifrazione e supporto di tutti i passaggi del blur. Conserva
la stessa griglia e densità di campionamento; cambiano dimensioni e coordinate
dei buffer, non intensità, risoluzione o frequenza dell'effetto.
Le dimensioni vengono arrotondate a blocchi di 64 texel per evitare riallocazioni
continue durante piccoli spostamenti e animazioni. La composizione della superficie
rimane completa: i contenuti opachi esterni al vetro continuano a essere disegnati.
Gli altri namespace e il vetro senza Enhanced conservano il percorso precedente.

Lo shader evita inoltre quattro valutazioni della distanza della card nei pixel
del centro piatto, dove la rifrazione è già nulla. La fascia di 20 px e la
correzione degli angoli restano quelle della r8.

Confronto isolato sullo stesso hardware, pannello 800×720, output annidato
951×1023, sfondo animato e piccoli spostamenti del pannello, circa cinque secondi
per build dopo il riscaldamento:

| Misura | r8 | r9 |
| --- | ---: | ---: |
| Pixel per passaggio di blur | 305.485 | 229.376 |
| Tempo GPU del compositor per frame | 5,225 ms | 4,963 ms |
| Tempo CPU del compositor per frame | 1,792 ms | 1,755 ms |
| Clock GPU medio | 403,1 MHz | 366,0 MHz |
| Allocazioni di texture durante la misura | 0 | 0 |

Il carico del blur scende del 24,9%; il tempo GPU complessivo misurato del 5,0%.
Il clock varia automaticamente e la prova include il resto del rendering del
compositor: questi numeri non sono un aumento equivalente degli FPS e non provano
che ogni rallentamento sia risolto. Sul monitor 1920×1080, un pannello standard
980×720 centrato richiede buffer di blur 576×448 invece di 1020×600, alle impostazioni
usate nella prova: questa è una riduzione geometrica, non una misura prestazionale.

Il confronto dei pixel centrato e spostato rispetto alla r8 ha uno scarto massimo
di 1/255 nei canali, escluso l'avviso del compositor di prova. La prova nativa
controlla anche i contenuti opachi fuori dal campione e lo sfondo fisso sotto
una card spostata. Restano i controlli di movimento live, workspace, angoli,
caricamento/scaricamento e uscita regolare.

```sh
python3 tests/native-glass-performance.py /percorso/r8/hyprglass.so /percorso/r9/hyprglass.so
```

Il confronto usa solo compositor annidati, conta i passaggi GL effettivi e legge
i tempi CPU/GPU del loro processo; non sostituisce il plugin del desktop.
La r9 richiede una nuova sessione Hyprland per essere attivata. Riavviare soltanto
Quickshell non sostituisce il codice nativo già mappato. Dopo il nuovo accesso
va verificata la fluidità delle impostazioni nella sessione reale.

La build verificata è installata e nella directory di staging; la sessione reale
mantiene r8. Il backup precedente è in
`~/.cache/end4-pC/native-glass-backup-r8-20261106-115125/`.


## Sidebar satinata: revisione r10

La sidebar delle impostazioni usa un materiale distinto: sfocatura minima di
8 px logici, che segue Glass intensity quando il valore globale supera 8.
Il pannello esterno e gli altri widget conservano il valore globale; testo,
avatar e pulsanti vengono composti dopo la sfocatura e rimangono nitidi.
Il materiale non aggiunge una tinta nera per simulare l'opacità: diffonde davvero
il dettaglio sottostante, mantenendo la rifrazione del contorno arrotondato.

`WindowGlass.frost` seleziona la diffusione aggiuntiva, con zero come valore
predefinito. Il percorso Quickshell lo usa per il materiale FrostedGlass;
il percorso nativo usa livelli mip della cattura già ritagliata. Non aggiunge
una cattura dello schermo, né un secondo blur separabile. I mip vengono generati
solo quando la superficie contiene una card satinata; le altre card campionano
il livello originale. Il margine del ritaglio comprende anche il supporto del
livello più grossolano, tenendo conto della scala del monitor.

Il protocollo `end4glass` con flag Enhanced 2 aggiunge un valore `frost` dopo
l'opacità di ciascuna card. Il parser verifica numeri finiti nell'intervallo
0–32 e accetta anche il precedente formato 0/1. Il loader espone la capacità
`frosted` soltanto per r10: una sessione r9 continua a ricevere il formato precedente,
senza applicare la diffusione dedicata fino al prossimo accesso.

La prova nativa confronta una trama a righe con frost 0, 8 e nuovamente 0,
con intensità generale minima: il contrasto residuo deve scendere sotto il 40%
dei due riferimenti, senza trasformare lo sfondo in un riempimento nero o bianco.
Restano i controlli di angoli, movimento, workspace e ciclo di vita. Passano anche
il parser, il loader e aperture/chiusure delle impostazioni nei percorsi Quickshell.

Con il pannello di prova 800×720 satinato, il confronto annidato r9/r10 misura
4,987/5,068 ms GPU per frame e 1,792/1,912 ms CPU; clock medi 383,5/378,0 MHz.
I passaggi di blur restano a 229.376 pixel e le chiamate di allocazione texture
durante i piccoli spostamenti sono zero. Sono misure brevi con clock variabile,
non una garanzia sugli FPS della sessione reale.

La r10 verificata è installata e nella directory di staging. La sessione corrente
mantiene r9 fino al prossimo login; il backup è in
`~/.cache/end4-pC/native-glass-backup-r9-20261106-121543/`.


## Opaco senza alone e blur stabile: revisione r11

Il materiale con `frost > 0` non aggiunge più Fresnel e riflesso speculare:
su uno sfondo nero anche il bordo resta nero. Il materiale trasparente conserva
il riflesso precedente; la geometria e la rifrazione non cambiano. Lo shader
Quickshell sopprime a sua volta la luce del bordo soltanto nel materiale opaco.

Nel percorso nativo, il satinato non campiona più mipmap grossolane. La loro
griglia seguiva l'origine del buffer ritagliato: spostando il pannello cambiavano
sia le celle visibili sia il colore di punti fermi dello sfondo. Ora un blur
gaussiano separabile prepara il campione del materiale opaco. Copia e passaggi
aggiuntivi sono limitati all'unione delle card opache, con il margine del kernel;
il buffer temporaneo del blur viene riusato. Un solo buffer aggiuntivo conserva
il risultato, con la stessa griglia del campione originale. Le altre card
continuano a leggere il campione precedente.

Il kernel dell'opaco usa campioni adiacenti, accoppiati con filtraggio bilineare,
fino a 64 texel per lato. Non allarga un kernel corto saltando texel: questo
lasciava striature. Alle impostazioni e scale normali copre tre sigma del blur.
Raggi estremi con scale molto alte possono raggiungere il limite; un buffer
opaco ulteriormente ridotto sarebbe il passo successivo per quei casi. Più card
opache nello stesso layer condividono il livello di blur più forte.

La prova nativa confronta il bordo su nero con frost 0/8: r10 restituisce 15/15,
r11 15/0, in livelli su 255. Con una trama fine, r10 lascia un contrasto residuo
23 e varia fino a 23 livelli mentre il riquadro si sposta sopra lo sfondo fermo.
R11 restituisce contrasto e variazione zero sulla stessa trama, mantenendo il
testo del riquadro nitido. Il test conserva le prove degli angoli e verifica
anche movimento live e workspace con il materiale opaco attivo.

Il benchmark ora conta i frame realmente composti, invece di dedurli dai due
passaggi del blur: l'opaco ne aggiunge altri due. La scena misura un pannello
800×720 con sidebar 195×704. Con haze 4: GPU 5,160/5,148 ms per frame per r10/r11,
clock 384,2/391,1 MHz. Con haze 1: 5,463/5,623 ms, clock 425,6/470,0 MHz.
Le allocazioni esplicite di texture durante i piccoli spostamenti sono zero.
La qualità uniforme richiede lavoro aggiuntivo; i clock variabili e la durata
breve impediscono di convertire questi risultati in una promessa sugli FPS.

```sh
END4_GL_BENCH_HAZE=1 python3 tests/native-glass-performance.py /percorso/r10/hyprglass.so /percorso/r11/hyprglass.so
```

Il loader mantiene la compatibilità con r10 e il suo protocollo del materiale.
La nuova build nativa richiede logout/login; riavviare Quickshell lascia attiva
la libreria già caricata nel compositor.

La r11 verificata è installata e nella directory di staging. Il backup della r10
è in `~/.cache/end4-pC/native-glass-backup-r10-20261106-124501/`;
la sessione reale mantiene r10 fino al prossimo login.


## Controlli tagliati e distacco durante il trascinamento: revisione r12

La r11 impostava il ritaglio del blur opaco con `glScissor` direttamente.
[Hyprland 0.55.4 conserva invece una copia dell'ultimo rettangolo](https://github.com/hyprwm/Hyprland/blob/v0.55.4/src/render/OpenGL.cpp#L901)
e salta la chiamata GL se il rettangolo richiesto coincide con quello memorizzato.
Con barra e impostazioni in layer a schermo intero, il compositor poteva quindi
credere di disegnare tutto il layer, mentre la GPU manteneva il piccolo ritaglio
del blur. Sparivano controlli e rimanevano porzioni della maschera precedente
spostando il pannello. La r12 usa `g_pHyprOpenGL->scissor(..., false)` anche per
il ritaglio del blur: stato GPU e cache del compositor rimangono sincronizzati.
Non cambia shader, kernel, rifrazione o dimensioni dei buffer della r11.

La nuova prova usa Settings/SettingsContent reali, una barra in un layer a
schermo intero, desktop senza finestre e navigazione alla pagina Interfaccia.
Verifica i colori di Config file e Reload per tre frame in quattro posizioni.
Con r11 e il materiale forzato soltanto nel compositor isolato, Reload perde
il colore atteso (77,75,77) e mostra (17,17,17). R12 supera i 24 controlli di
pixel e gli spostamenti. Le prove precedenti avevano una barra alta 68 px:
quel diverso ordine dei ritagli nascondeva la regressione.

```sh
python3 tests/native-settings-check.py --plugin /percorso/r12/hyprglass.so
python3 tests/native-settings-check.py --plugin /percorso/r11/hyprglass.so --reproduce-r11
```

La seconda prova deve fallire con `Control missing or detached`; è prevista
solo per riprodurre il difetto in un compositor annidato. Il loader ora riconosce
r11 come compatibile per il vetro standard, ma esclude il suo materiale opaco.
`qs -c end4-pC ipc call glass refresh` rivaluta queste capacità senza sostituire
il plugin caricato. Nella sessione reale sono stati ripristinati e verificati
visivamente i controlli disabilitando temporaneamente solo il satinato della r11;
le preferenze restano invariate. Alla nuova sessione r12 riabilita il materiale.

La r12 supera anche la prova nativa completa: contrasto residuo e deriva dello
sfondo zero, bordo opaco nero, rifrazione degli angoli, movimento live, workspace
e scaricamento/ricaricamento/uscita regolare. Passano inoltre parser, buffer,
loader e applicazione della patch ai sorgenti originali fissati.

La build verificata è installata e nella directory di staging. La sessione
corrente mantiene r11 fino al prossimo login; il backup è in
`~/.cache/end4-pC/native-glass-backup-r11-20261106-130402/`.


## Continuità fra vetro trasparente e satinato annidati: revisione r13

Il bordo antialias di una scheda interna veniva usato come maschera dell'intero
vetro: nella fascia di circa 1–2 px il materiale sottostante perdeva copertura
e lasciava affiorare lo sfondo senza la sua rifrazione. Lo shader ora compone
il colore premoltiplicato delle regioni dall'alto verso il basso. Nei pixel
parzialmente coperti conserva il materiale rifratto sottostante; i pixel
completamente coperti continuano a calcolare solo il materiale superiore.
Non vengono aggiunti passaggi di blur, catture o framebuffer.

La prova ottica verifica sia la copertura lungo i bordi rettilinei e curvi sia
il colore composto di un bordo frazionario: deve contenere la rifrazione del
riquadro esterno. Con lo shader r12 la stessa prova fallisce; r13 la supera.
Le verifiche native controllano inoltre leggibilità e allineamento dei pulsanti
reali delle impostazioni durante gli spostamenti.

Come per le revisioni precedenti, la build viene sostituita su un nuovo inode
e diventa attiva al prossimo accesso; il plugin della sessione corrente rimane
caricato. Il loader continua a riconoscere r12 e il suo materiale satinato.

Confronto sul portatile, stessa scena annidata e intensità 4: r12 misura
5,100 ms GPU per frame, r13 5,116 ms; nessuna nuova allocazione di texture e
stessa copertura dei passaggi di blur. La differenza è entro la variabilità
del campionamento e delle frequenze GPU, non dimostra un rallentamento.

La r13 verificata è installata e nello staging. La sessione attuale conserva
r12 fino al nuovo accesso; il backup è in
`~/.cache/end4-pC/native-glass-backup-r12-20261106-132839/`.


## Riapertura della sidebar: riuso dei riquadri

La sidebar veniva distrutta tre secondi dopo la chiusura. Riaprendola, le sei
schede della home ripetevano creazione, caricamento e animazioni: nella prova
annidata con intensità 1 si misuravano 1,60–1,66 secondi CPU e 65–68 invii di
geometria nei primi 1,6 secondi. Con Glassy ora si conserva una sola sidebar
nascosta, comprese le pagine visitate. Nella stessa prova la riapertura usa
0,24–0,26 secondi CPU e due invii, senza rilanciare le animazioni delle schede.
Il picco iniziale del ciclo eventi non diminuisce sensibilmente nella prova:
Quickshell ricrea comunque la finestra Qt sottostante quando la rimappa.
Non è quindi una misura di FPS né una garanzia di assenza totale di scatti.

Il vetro non rimane attivo a finestra nascosta; timer del player e smoothing
del visualizzatore richiedono anche una finestra visibile. La modalità senza
Glassy mantiene lo scaricamento dopo tre secondi. Il controllo ripetibile è
`python3 tests/sidebar-window-check.py`: verifica tre riaperture oltre il
vecchio timeout, identità del contenuto riutilizzato, nessun vetro attivo da
nascosta e rilascio normale con Glassy disattivato. Nessuna modifica al plugin
nativo, quindi non è necessario un nuovo accesso.


## Rifrazione durante apertura e chiusura native: revisione r14

Il percorso di chiusura saltava il vetro e cancellava immediatamente i buffer
per-layer. L'istantanea di Hyprland conteneva quindi il solo contenuto Qt:
la rifrazione e la satinatura sparivano prima dell'animazione di uscita.
La r14 conserva lo stato fino alla scadenza del riferimento debole alla layer,
compone il contenuto dell'istantanea sopra il vetro e campiona il desktop vivo
anche mentre la finestra si chiude. La creazione dell'istantanea continua a
escludere il vetro: un framebuffer vuoto non viene usato come sfondo.

Ogni layer conserva anche l'ultima geometria Enhanced valida e la relativa
satinatura, necessarie quando Quickshell nasconde la finestra, ritira le regioni
e distrugge la risorsa Wayland. La copia appartiene alla singola layer in uscita
e non viene sostituita dalle geometrie di una successiva riapertura.

`python3 tests/native-glass-close-check.py --plugin /percorso/hyprglass.so`
verifica i pixel in apertura e chiusura con una dissolvenza rallentata e cambia
lo sfondo a metà chiusura per escludere un effetto congelato. R13 fallisce al
primo fotogramma utile; r14 supera sette fotogrammi di chiusura e nove di
apertura. Passano inoltre i controlli nativi completi su angoli, satinatura,
workspace e ciclo di vita, oltre alla verifica dei pulsanti reali delle
impostazioni. La sidebar reale è stata verificata anche con l'uscita
`popin 94%`. L'aspetto e la cache QML della sidebar restano invariati.

La r14 verificata è installata e nello staging; il processo principale mantiene
r13 fino al prossimo accesso. Backup: `~/.cache/end4-pC/native-glass-backup-r13-20261106-165138/`.


## Sidebar: carico di rendering e rilascio dei buffer, revisione r15

La configurazione reale applica `blur=true` e `ignore_alpha=0.79` a tutte le
layer `quickshell:.*`. Il blur di Hyprland si sovrapponeva a quello del plugin;
in chiusura veniva applicato anche all'istantanea a dimensione monitor, con
un effetto scuro esteso fuori dalla sidebar. Riproducendo queste regole nel
test di chiusura, r14 fallisce: il pixel esterno passa da (22, 89, 207) a
(21, 23, 25). Con r15 resta invariato e la rifrazione continua durante il fade.

Il hook esclude ora il blur integrato solo durante la costruzione dei passaggi
che sono già gestiti dal plugin, inclusa la creazione e il rendering delle
istantanee. Uno scope guard ripristina esattamente il valore e la priorità
originali della regola, anche in caso di uscita anticipata. La modalità normale
e i popup che non passano dal vetro nativo mantengono il blur configurato.

La r15 riduce il campionamento della sidebar alle regioni effettive del vetro,
con lo stesso margine necessario al blur già usato per le impostazioni.
La sorgente della rifrazione rimane a piena risoluzione; solo la Gaussian della
satinatura ampia usa una texture a metà risoluzione, con filtro lineare e raggio
riscalato. I blur stretti restano a piena risoluzione. Un buffer temporaneo
separato evita riallocazioni alternando le due risoluzioni.

Il benchmark ora include la home reale con sei schede satinate, barra e sfondo
in movimento, con le regole di blur della sessione reale:

```bash
END4_GL_BENCH_HAZE=1 python3 tests/native-glass-performance.py --sidebar OLD.so NEW.so
```

Sul compositor annidato a 1908 × 1068, nello stesso confronto r14/r15: pixel di blur per
fotogramma 3.068.860 → 1.769.196 (−42%), tempo GPU complessivo 7,621 → 6,748 ms,
CPU 1,987 → 1,386 ms, zero allocazioni di texture dopo il riscaldamento. La
frequenza GPU media passa da 632,4 a 391,4 MHz: il risparmio di lavoro non si
traduce direttamente nella stessa percentuale di FPS. La prova non garantisce
l'assenza di ogni scatto nella sessione completa.

È corretto anche un difetto del rilascio: il distruttore dei framebuffer di
Hyprland lascia associato il framebuffer 0. Liberare i buffer di una layer
scaduta durante un altro fotogramma poteva quindi alterarne la destinazione.
Il distruttore della layer Glassy conserva e ripristina separatamente le
associazioni di lettura e scrittura dopo aver liberato tutti i propri buffer.
Il controllo `native-glass-buffer-check.py` esegue il codice reale di rilascio
contro questo comportamento: r14 fallisce, r15 passa.

Il test di chiusura include ora una barra persistente e controlla anche pixel
esterni al pannello, fino al termine dell'animazione. Il test della satinatura
verifica anche spostamenti di uno e tre pixel, per individuare un'eventuale
oscillazione della griglia ridotta. La patch completa include ora anche il nuovo
header `GlassRegions.hpp`, necessario per ricompilarla da una copia pulita di
HyprGlass v0.6.4.

Passano i controlli di movimento, commutazione True Glassy e impostazioni reali
con `--blur-rules`, oltre al test di apertura/chiusura e al controllo del
rilascio. Satinatura: contrasto residuo 0 e deriva durante il movimento 0;
pulsanti delle impostazioni: 24 pixel verificati durante gli spostamenti.

La r15 è installata e nella directory di staging. Il plugin della sessione
principale resta r14 fino al prossimo logout/login. Backup: `/home/xlini/.cache/end4-pC/native-glass-backup-r14-20261106-172646`.


## Aggiornamenti parziali e larghezza della sidebar: revisione r16

La superficie Wayland della sidebar rimaneva larga 760 pixel anche nella
modalità compatta, in cui il contenuto occupa circa 445 pixel. Con Glassy su
Hyprland ora è larga 470 pixel: durante l'espansione conserva lo spazio ampio,
poi lo rilascia solo quando l'animazione di contrazione termina. Il contenuto
attende la larghezza effettivamente disponibile prima di allargarsi, per evitare
tagli durante il configure Wayland. Le dimensioni visibili e il comportamento
senza Glassy restano quelli precedenti. Il test `sidebar-window-check.py`
verifica anche espansione, contrazione e assenza di tagli a ogni fotogramma.

Alla riapertura Quickshell ricrea la layer e riporta temporaneamente una
larghezza zero. Il layout ora conserva in quel passaggio la larghezza prevista:
evita un'animazione di dimensione spuria e il salto 470 → 760 → 470 pixel
durante l'ingresso. Il test controlla ogni fotogramma delle tre riaperture;
fallisce con il layout precedente e passa con la correzione. Solo QML,
senza aggiornare il plugin o richiedere logout.

Il cambio pagina della sidebar usa ora una dissolvenza sequenziale: uscita di
120 ms, cambio del layout quando è invisibile e ingresso di 200 ms, adattati
alla velocità configurata. La pagina richiesta viene precaricata e mostrata
solo quando il Loader è pronto. Intestazione, contenuto e vetro condividono
la stessa opacità; non restano pagine sovrapposte né timer di permanenza.
Quando si seleziona una tessera della Home, parte prima la sua animazione
originale di uscita insieme alle altre tessere. La dissolvenza del contenitore
attende l'ultima tessera, usando la durata effettiva dello sfalsamento e la
velocità configurata. La prova controlla anche fotogrammi con tessere ancora
visibili in movimento e nessun cambio pagina prima della loro uscita.
`python3 tests/sidebar-transition-check.py` verifica le pagine reali,
Intelligence e Media satinati, ritorno Home e navigazione interrotta.
La prova nativa annidata ha verificato anche l'opacità delle regioni di vetro
su 306 fotogrammi e otto cambi pagina.

Nel percorso nativo Enhanced, con output non ruotati, blur e composizione sono
limitati alle aree danneggiate dal compositor. Il blur include un margine
conservativo per rifrazione, entrambe le direzioni Gaussian e tutte le
iterazioni. La composizione conserva i rettangoli disgiunti: non dipinge sopra
controlli Qt che quel fotogramma non ha ridisegnato. Se il danno non interessa
il vetro, il passaggio di campionamento viene saltato e il suo post-pass non
riusa i vecchi buffer. Le modifiche alle geometrie/materiali via IPC invalidano
esplicitamente le layer del client, anche quando non sporcano la scena Qt.
Gli output ruotati e la modalità standard conservano il percorso completo.

`native-glass-damage-check.py` legge i pixel direttamente dopo il disegno,
senza una richiesta screenshot che possa forzare un ridisegno completo.
Verifica cambi di colore vivi sotto la satinatura, aggiornamenti dei controlli
Qt, nessuna composizione quando cambiano solo aree esterne e ridisegno su
modifiche del solo materiale. Il confronto precedente r15 fallisce quando
continua a ricomporre per aggiornamenti esterni.

Il benchmark ora conta un pannello per passaggio di composizione, anziché
scambiare ogni rettangolo danneggiato per un nuovo fotogramma. Riporta anche
pixel di composizione, larghezza reale della superficie e carico GPU/CPU per
secondo. Con `--sidebar --partial` anima una piccola superficie dietro la
sidebar; `--outside` la sposta all'esterno. `END4_GL_BENCH_WIDE=1` ripristina la
vecchia superficie larga solo nella prova isolata, per confrontare entrambe
le ottimizzazioni insieme.

Su output annidato 951 × 1023, intensità 1 e regole di blur reali:

| Scenario | GPU r15, superficie 760 px | GPU r16, superficie 470 px |
|---|---:|---:|
| Tutto lo sfondo in movimento | 5,245 ms/fotogramma | 5,035 ms/fotogramma |
| Piccola area in movimento dietro | 5,124 ms/fotogramma | 4,099 ms/fotogramma |

Nel secondo caso i pixel sfocati scendono da 1.701.432 a 1.252.856 per
fotogramma e quelli composti da 842.148 a 298.524, senza allocazioni dopo il
riscaldamento. Il confronto separato a parità di superficie larga dà circa
−16% di tempo GPU con aggiornamenti locali e −43% con movimento esterno;
sull'output piccolo l'espansione del danno del compositor raggiunge ancora
parte del pannello. Non è quindi una promessa di zero lavoro con qualsiasi
movimento esterno, né della stessa percentuale di FPS in tutte le scene.

Passano i controlli nativi di movimento e workspace, i cambi True Glassy, i
24 pixel dei controlli delle impostazioni e i fotogrammi di apertura/chiusura.
La prova dei danni parziali verifica 12 campioni vivi più i controlli e i
materiali; la satinatura mantiene contrasto residuo 0 e deriva 0. Sono state
verificate anche Home e Media reali, oltre all'intero ciclo di riapertura ed
espansione della sidebar.

La r16 è installata e nella directory di staging. La sessione principale
continua a usare r15 fino al prossimo logout/login. Backup: `/home/xlini/.cache/end4-pC/native-glass-backup-r15-20261106-210238`.


## Pillole della barra superiore: revisione r19

La taratura scelta nella prova separata viene applicata soltanto al layer
`quickshell:bar` ancorato in alto, con Enhanced attivo: fascia di rifrazione
24% del lato corto, rifrazione 200%, blur interno con sigma 3 px logici e
riflessi 50% (Fresnel 0,35, speculare 0,5, come nel laboratorio).
Il limite di 20 px della fascia rimane: sulle pillole da 32–40 px non interviene.

Il blur nativo usa un raggio di tre sigma e una singola coppia di passaggi a
piena risoluzione, scalati con il monitor. Il contenuto della superficie viene
composto dopo il vetro: testi e icone non sono sfocati. La taratura viene
conservata anche durante lo snapshot di chiusura. Dock, barra inferiore o
verticale, popup e pannelli mantengono i parametri precedenti.
Il fallback QML usa gli stessi valori di fascia/forza/riflessi e haze 3 nel
proprio campionatore: non è una corrispondenza pixel per pixel del Gaussian nativo.

Controlli senza GPU:

```sh
python3 tests/topbar-glass-check.py /percorso/sorgenti-patchati
python3 tests/native-glass-buffer-check.py /percorso/sorgenti-patchati
python3 tests/native-glass-loader-check.py
python3 tests/qml-load-check.py
```

Il laboratorio è stato verificato anche con lo shader della nuova build,
fascia 24%, rifrazione 200%, blur 3 px, usando Firefox e llvmpipe. Nessuna prova
ha scaricato/caricato il plugin nella sessione principale. La build r19 deve
essere caricata al prossimo logout/login; il loader continua ad accettare r18
nel frattempo. `python3 scripts/glass/native/backend.py` restituisce
`topBarOptics: true` soltanto quando è effettivamente caricata r19.


## Blur interno della barra superiore: revisione r20

La r20 riduce il blur interno da sigma 3 a **1 px logico**, con raggio
nativo di 3 px scalato con il monitor. Anche il fallback QML passa a haze 1.
Restano fascia 24%, rifrazione 200% e riflessi 50%, limitati alla barra
superiore con Enhanced attivo. Gli altri materiali mantengono i propri valori.

Il loader accetta anche r19 durante la transizione e segnala `topBarOptics`
per entrambe le revisioni. La nuova build si carica al prossimo logout/login,
senza scaricare il plugin attivo. La riduzione del blur non costituisce una
correzione dimostrata del crash segnalato: nei log consultati non compare un
nuovo coredump di Hyprland.

Build r20 compilata e installata atomicamente, con ABI e hash verificati;
la sessione continua a usare r19. Backup della r19:
`/home/xlini/.cache/end4-pC/native-glass-backup-r19-ks54x8_o`.
Passano i controlli del profilo ottico, dei buffer, del loader e il caricamento
QML con rendering software.


## Pagina Glassy e profili per elemento: revisione r21

In Impostazioni → Interfaccia → Trasparenza, la riga **Glassy UI** apre una
pagina dedicata. La Dashboard offre lo stesso collegamento. In alto restano
attivazione generale, sorgente e Enhanced; sotto ci sono Bar, Dock, Sidebar,
Impostazioni, Lockscreen e Terminale. Ogni scheda salva attivazione, fascia
deformata, rifrazione, sfocatura interna e riflessi, con ripristino separato.
Le regolazioni ottiche richiedono Enhanced. Gli slider applicano il valore al
rilascio; la tastiera applica ogni passo. Non viene aggiunta alcuna cattura.

I predefiniti della barra sono 24%, 200%, 1 px e 50%. Gli altri pannelli
mantengono fascia 7%, rifrazione 135% e riflessi 50%; la sfocatura regola i
box satinati senza sfocare ulteriormente il contenitore trasparente esterno.
La lockscreen usa solo lo sfondo e conserva inizialmente il blur globale.
Gli interruttori ripristinano anche i riempimenti normali dei componenti.
Alla prima installazione della r21 la Dashboard era ancora in quarantena;
la riattivazione del 10 novembre è descritta nello stato attuale in testa al documento.

Il terminale è disattivato per default. Su Hyprland, con sorgente Windows
underneath ed Enhanced attivo, il profilo si applica tramite tag proprietario
a Kitty, Foot, Alacritty, WezTerm e Konsole. I testi sono composti
dall'applicazione dopo il vetro. Occorre uno sfondo del terminale trasparente
(l'opacità dell'applicazione non viene cambiata). Il tag `hyprglass_disabled`
continua ad avere precedenza.

Il 10 novembre il profilo terminale è stato attivato nella configurazione
utente: fascia 7%, rifrazione 135%, blur 3 px e riflessi 50%. Kitty usa già
`background_opacity 0.85`; il tag `hyprglass_owner_<PID_QS>` è stato verificato
sulla finestra esistente e assente dalle altre applicazioni. Gli slider sono
in Impostazioni → Interfaccia → Glassy → Terminale. È stato riutilizzato il
supporto esistente, senza ricaricare il plugin o cambiare l'opacità di Kitty.
Il test QML software della pagina e il controllo nativo dei profili passano.

La build r21 aggiunge l'IPC `end4profiles`: aggiorna un insieme temporaneo
validato, con sei chiavi ammesse, valori finiti e limiti, verifica il PID della
connessione e conserva i profili separati per processo QS. Un messaggio
malformato non modifica l'ultimo insieme valido. La geometria `end4glass`
rimane compatibile con le build precedenti. Il loader distingue la capability
`profiles`: in attesa del nuovo login la UI salva i valori e mostra un avviso;
non invia comandi sconosciuti al plugin caricato.

Controlli senza GPU/compositor di prova:

```sh
python3 tests/glass-profiles-check.py /percorso/sorgenti-patchati
python3 tests/topbar-glass-check.py /percorso/sorgenti-patchati
python3 tests/native-glass-buffer-check.py /percorso/sorgenti-patchati
python3 tests/native-glass-loader-check.py
python3 tests/qml-load-check.py
```

Il controllo QML istanzia la pagina, passa sulle sei schede, verifica
predefiniti, interruttori, isolamento di un cursore, ripristino e ritorno.
La build nativa si installa per il prossimo logout/login, conservando
NODELETE e sostituendo atomicamente i file: non viene ricaricata a caldo.

Installazione r21 completata con verifica ABI/hash. La sessione resta sulla
r20; backup della versione precedente:
`/home/xlini/.cache/end4-pC/native-glass-backup-r20-_shv_q36`.
