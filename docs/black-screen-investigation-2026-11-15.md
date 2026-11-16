# Schermate nere: indagine del 15 novembre 2026

## Stato e priorità

La causa dei blocchi non è stata identificata. Le prove GPU sono sospese.
Nessun tentativo di riprodurre il blocco, reset GPU, aggiornamento firmware,
cambio kernel o riavvio della sessione è stato eseguito durante questa indagine.
Tutti gli orari sotto sono Europe/Rome, CET.

L'utente riferisce almeno un blocco nel menu di boot, prima della selezione
del sistema operativo; altri episodi hanno richiesto spegnimento forzato e
rimozione dell'alimentazione per poter ripartire. Non sono semplici crash
di una finestra. Il mancato accesso alla TTY è un sintomo riferito, non una
prova autonoma che tutti i core CPU fossero fermi.

Precisazione successiva dell'utente: almeno un episodio con glitch grafici
e blocco completo è avvenuto dopo aver selezionato il sistema operativo,
mentre lo stava caricando. Quell'episodio non va classificato come certamente
precedente a Linux: il driver amdgpu può già essere in inizializzazione.
Resta distinta la precedente segnalazione di blocco nel menu di scelta.
La posizione visiva della schermata non identifica da sola lo stadio di
esecuzione. Non attribuire l'intera serie a firmware/hardware su questa base.

Nuovo indizio riferito: alcuni blocchi sono avvenuti muovendo il portatile
o lo schermo. Questo aumenta la priorità di un controllo fisico di cavo
display/connettori, zona cerniera e possibili contatti o flessioni della
scheda. Non dimostra un corto né un guasto GPU. Una correlazione con il
movimento non va ricercata provocando altri blocchi o manipolando connettori
sotto alimentazione. L'eventuale ispezione interna richiede anche la
disconnessione della batteria interna, oltre all'alimentatore.

## Contenimento verificato

- `end4-freeze-recorder.service`: inactive e disabled.
- Il comando `run` di `tests/native-glass-stage-profile.py` esce immediatamente.
- Il plugin installato è conservato come
  `~/.local/share/end4-pC/native-glass/hyprglass.so.quarantined-1794749565745448853`.
  Hash SHA-256 uguale al manifest installato:
  `a48592e2a25730538c618f5d7a0d0e89431181771f4870ca2889ec6a65520103`.
- Al nuovo accesso delle 15:48, `hyprctl plugin list -j` restituisce `[]`.
  L'utente non riferisce un nuovo nero in questo avvio al momento della verifica.
- Prima del contenimento, le mappe di Hyprland mostravano il plugin r34
  installato. Nessun LD_PRELOAD diagnostico o plugin dalla directory del
  profiler era presente nella sessione principale verificata.

La rimozione simultanea di recorder e plugin serve a ridurre l'esposizione;
non è un confronto controllato che possa attribuire un eventuale miglioramento
a uno solo dei due. Non ripristinare componenti per provocare un altro blocco.

## Cronologia verificata

| Evento | Evidenza | Limite |
|---|---|---|
| 14 novembre, circa 23:33 | Precedente nero durante il banco annidato, con processi di test nel recorder remoto; nuovo boot 23:34 | Nessun messaggio conclusivo sul motivo del blocco |
| 15 novembre, 12:19 | Primo tentativo TTY, `runs/1794741547912141589`: `IndentationError` nella fixture generata | Si ferma prima dell'avvio del compositor di test |
| 12:20:54–56 | Journal con sequenza normale di reboot dopo il comando dell'utente | Non spiega il successivo nero prima del boot visibile |
| 12:27:57 | Avvio con ultime scritture journal alle 12:28:02 | Il termine del journal non coincide necessariamente con l'istante del blocco |
| 13:46–47 | Secondo tentativo TTY, `runs/1794746791216348275`: avvia compositor e QS ma termina con `ready:false,width:0,cards:0` | Nessuna misura valida; non arriva alla build con timer GPU |
| 13:47:39–41 | Sequenza normale di reboot nel journal | I blocchi successivi vanno analizzati separatamente |
| 13:49:56 | Ultimo campione remoto di quel boot, senza record finale del mittente | Il Raspberry continua i propri heartbeat; non distingue rete da hang del PC |
| 14:06:01 | Ultimo campione remoto del boot successivo, senza record finale | Nessun timeout/reset GPU conclusivo nei dati ricevuti |
| 14:17:08 | Ultimo campione remoto del boot delle 14:07, senza record finale | Il journal locale si fermava già alle 14:14:28: perdita degli ultimi eventi persistiti |
| 14:26:22 e 14:28:33 | Ultimi campioni remoti di due nuovi avvii, senza record finale | Mostrano che il PC funzionava oltre le ultime scritture dei journal locali |
| 14:31–32 | Stop/disabilitazione recorder e quarantena del plugin | Nessuno scaricamento del plugin dalla sessione ancora aperta |
| 14:33:59 | Uscita dalla sessione e nuovo greeter SDDM X11 nel journal | L'ultima scrittura non prova che il blocco sia avvenuto precisamente lì |
| 15:48:32 | Nuovo boot; login senza plugin e recorder | Stabilità da osservare nell'uso normale, senza stress test |

## Cosa hanno modificato le prove

Il primo tentativo TTY ha creato il runner, snapshot Glassy e stato sotto
la directory diagnostica; il runner compila una libreria di conteggio in
una directory temporanea prima della compilazione della fixture Python.
L'errore di sintassi impedisce l'esecuzione della fixture e il caricamento
di quella libreria nel compositor. Non è una prova di assenza di problemi
nelle altre prove effettuate prima o dopo.

La procedura richiedeva però un logout: alle 12:17:13 si chiude Hyprland,
con disconnessioni Wayland e SIGABRT di hyprsunset. Questa transizione
grafica precede l'esecuzione Python e non può essere ignorata nell'analisi.
Un altro SIGABRT di hyprsunset coincide con il logout delle 13:46:10.
Non ci sono evidenze che quei crash di hyprsunset siano la causa dei blocchi;
resta da distinguere l'effetto della chiusura della sessione da quello del
codice del banco. Il fallimento precoce del Python non esclude un ruolo
della procedura complessiva nell'aver innescato il problema.

Il secondo tentativo ha usato un compositor diretto con configurazione e
directory XDG temporanee, caricando `baseline.so`. `profile.so` non risulta
eseguito: il primo giro non supera il controllo della pagina Settings.
Il log della fixture riporta `Unknown compositor: unknown`: `services/WM.qml`
deduce il compositor da `XDG_CURRENT_DESKTOP` e `XDG_SESSION_DESKTOP`, che il
banco diretto non imposta esplicitamente per QS avviato dalla TTY. Con
`WM.compositor == "unknown"`, `GlassCompositor.enabled` è false e `probe()`
non parte. Questo spiega perché `ready` rimane false; non identifica la
causa dei neri successivi. La prova rimane sospesa, senza correzioni QML
o rilanci per verificare l'ipotesi sul rendering.
Il file del test non scrive parametri GPU sysfs, sysctl, modprobe, GRUB o
firmware. LD_PRELOAD è passato al solo subprocess del compositor di prova.
Non viene installato nelle configurazioni della sessione principale.

I file Hyprland esaminati e GRUB hanno timestamp precedenti alla serie di
incidenti; `/etc/modprobe.d` e `/etc/sysctl.d` sono vuote. La riga di avvio
è `loglevel=3 quiet amd_pstate=active`; il driver CPU effettivo rilevato è
`acpi-cpufreq`. Non sono emerse modifiche persistenti ai clock introdotte
dal percorso del test TTY. La revisione non può escludere ogni cambiamento
fatto in altre sessioni: non è disponibile uno snapshot integrale precedente.

## Risultati dei log e interpretazione

Sono stati confrontati undici avvii e tredici file del Raspberry, circa
48 MB di dati remoti, conservati con le evidenze del caso.

1. Non è stato trovato nei kernel log raccolti un nuovo `ring gfx timeout`,
   un reset GPU conclusivo, un panic, un OOM kill o un machine check che
   identifichi la causa della serie. L'assenza non esclude un blocco tanto
   grave da impedire l'emissione o la persistenza del messaggio.
2. Gli avvisi TSC instabile e PSP `LOAD_TA ... 0x7` compaiono anche nell'avvio
   del 14 novembre, prima del primo test TTY. Non sono nuovi indicatori
   sufficienti per spiegare il peggioramento del 15 novembre.
3. Il sensore `amdgpu` edge ha raggiunto 90–97 °C in alcuni avvii. In altri
   ultimi campioni prima dell'interruzione erano presenti temperature più
   basse. Il calore richiede attenzione, ma non è dimostrato un arresto
   termico. Non confrontare automaticamente il sensore edge con il limite
   CPU Tjmax: sono misure diverse.
4. `gpu_busy_percent=100` compare anche in TTY senza processi grafici nel
   primo log. Nelle ultime finestre di circa 12 secondi prima di due
   interruzioni, i contatori gfx di Hyprland aumentano di circa 0,19 e
   0,10 secondi. Questi due processi non spiegano da soli il 100% globale;
   non è una misura di tutti i client GPU né una prova di sensore guasto.
5. La memoria disponibile negli ultimi campioni dei blocchi esaminati è
   circa 1,4–2,7 GB decimali; alcuni avvii hanno pressione di memoria e I/O.
   Sono comparsi due campioni isolati di processi grafici in stato D, non
   un'attesa persistente rilevata che identifichi un guasto del disco.
6. Il recorder aggiornato leggeva `/proc/PID/syscall`, provocando avvisi
   Yama ripetuti. La lettura è stata rimossa; in seguito compaiono ancora
   acquisizioni interrotte senza record finale. Questo difetto non basta
   a spiegare l'intera serie. Il recorder resta comunque disabilitato.

Nel nuovo avvio senza plugin il valore busy è stato osservato sia al 10%
sia al 100%, anche con sensore a 51–60 °C. In una lettura separata di circa
1,024 secondi, i contatori gfx dei client accessibili di Hyprland, QS e
VS Code aumentano complessivamente di circa 0,099 secondi, mentre il
valore sysfs resta 100. Le finestre e la copertura dei due contatori non
sono identiche: questo impedisce di usare il 100% da solo come diagnosi
di carico, guasto o responsabilità del plugin. La lettura non ha avviato
rendering, attese GPU o tracing.

Il blocco riferito prima della scelta del sistema operativo amplia
l'indagine a firmware, alimentazione e hardware, oltre allo stack grafico
Linux. Non dimostra un danno permanente. Un eventuale stato problematico
lasciato dal precedente arresto è un'ipotesi non verificata.

## Hardware e riferimenti

Lenovo 81UT, BIOS BUCN28WW (data DMI 01/12/2021), Ryzen 5 3500U, GPU
AMD 1002:15d8 rev c2; kernel corrente 6.18.36-1-lts. Non sono stati
applicati aggiornamenti o parametri alternativi durante l'indagine.

La documentazione kernel conferma che `gpu_recovery=-1` è un valore auto,
non una prova che una precedente prova abbia disabilitato la recovery:
https://docs.kernel.org/6.18/gpu/amdgpu/module-parameters.html
Scheda ufficiale del processore, per distinguere i limiti CPU dai sensori:
https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-3000-series/amd-ryzen-5-3500u.html

## Passo successivo

Verifica delle 16:41 circa: stesso boot iniziato alle 15:48, uptime 3171 s
(circa 53 minuti), sensore edge 49 °C, lista plugin vuota e recorder
inactive/disabled. Nessun nuovo messaggio conclusivo GPU nel journal
esaminato. È una finestra di funzionamento, non prova della causa né
garanzia di stabilità futura.

È stata verificata l'esistenza della sessione `Plasma (Wayland)` e dei
binari startplasma-wayland/kwin_wayland. Non è stata avviata. Non proporre
`Plasma (X11)`: kwin_x11 e la relativa voce di sessione non sono presenti.
Non è necessario installare un altro desktop per avere questa alternativa.

La patch archiviata `20261114-interface-bands/r34.patch` e la patch corrente
hanno lo stesso SHA-256 (`014055dd17175881bed1e1624946e8cda81a63a16ab0f090e6b54af93a3acc92`).
La baseline diagnostica privata dei simboli e il plugin quarantinato
hanno stessa dimensione (574840 byte), ma hash diversi: non attribuire
identità binaria alle due build. Nessuna delle due è stata caricata
durante questo controllo di provenienza.

Mantenere il desktop senza plugin nativo e senza recorder aggiunto; usare
i log persistenti già configurati. Non riattivare le prove per confrontare.
La sessione Plasma risulta disponibile nel selettore SDDM: se Hyprland resta
inutilizzabile, è una possibilità di accesso al lavoro senza la shell QS
specifica di Hyprland, non una garanzia contro un guasto di sistema.

Se ricompare un blocco nel menu firmware/boot, l'indagine software dal
desktop non può identificarne da sola la causa: occorrono diagnosi hardware
e firmware fuori da Quickshell. Non prescrivere modifiche casuali a GRUB,
reset live GPU, aggiornamenti BIOS o test di carico come tentativi rapidi.
