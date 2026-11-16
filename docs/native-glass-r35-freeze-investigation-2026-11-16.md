# R35: schermate nere e costo del trascinamento — 16 novembre 2026

L'utente riferisce tre nuovi blocchi completi poco dopo la reintroduzione del
plugin, trascinando le Impostazioni, dopo circa un giorno senza schermate nere.
È un indizio concreto contro il percorso nativo, non una prova del punto esatto
di guasto. Il risultato precedente dei mock CPU non autorizzava a considerare
r35 validata sul driver o sicura contro i freeze.

## Contenimento verificato

- `hyprctl plugin list -j` restituisce `[]` nella sessione successiva alla rimozione.
- `~/.local/share/end4-pC/native-glass/hyprglass.so` è assente.
- R35 conservata in `hyprglass.so.quarantined-1794847246327774723`.
- Registratore `inactive` e `disabled`. Nessun nuovo recorder attivato.
- Nessun load/unload, riavvio, rendering hardware/software, compositor di prova,
  ricompilazione del plugin o modifica di clock/driver durante questa indagine.

Non ripristinare r34 come presunta versione sicura: condivide gran parte della
pipeline esaminata e non dispone di una verifica di stabilità per questo caso.

## Cronologia ricostruibile, orari CET

Installazione su disco r35: **17:26:26**, esclusa dall'istanza allora attiva.
Nuovo login registrato alle **17:30:55**. La presenza effettiva di r35 è stata
verificata via IPC nella conversazione prima della rimozione; i log persistenti
non registrano ogni caricamento del plugin.

| Boot ID | Intervallo delle voci persistenti | Riscontro |
| --- | --- | --- |
| `9646c69bc53b4641a76cac911c526cf7` | 12:10:16–17:32:01 | Include il login delle 17:30:55; termina senza chiusura del sistema registrata. |
| `4eb74d55b14e4ef5b63fbf604fb6639b` | 17:36:11–17:36:26 | Nei dati salvati arriva all'avvio SDDM; nessun login utente/avvio Hyprland registrato. |
| `16bdd558cbe64fc88e58cf43efbb8e69` | 17:37:44–17:38:26 | Login delle 17:37:59; termina senza chiusura del sistema registrata. |
| `3a77b7d35b6842b78488451b386fdd18` | avvio 17:39:24 | Logout/login alle 17:41; sessione dell'indagine senza plugin. |

L'ultima voce salvata non è necessariamente l'istante del freeze. Il journal può
perdere la coda non ancora persistita. In particolare il secondo boot non prova
che il blocco sia avvenuto prima del login, ma impedisce di attribuire con
certezza tutti gli episodi a un plugin già caricato.

Nei tre boot precedenti non risultano GPU reset, ring timeout, page fault AMDGPU,
OOM kill o segfault pertinenti. Nessun nuovo crash report Hyprland; i due file
presenti nella cache risalgono a giugno/luglio. I dump dopo le 17:00 riguardano
`hyprsunset`, non Hyprland. La terminazione di hyprsunset durante la chiusura
della sessione non identifica la causa dei blocchi completi. Archivio systemd
pstore vuoto; nessun accesso forzato al pstore del kernel.

## Cause concrete di lavoro aggiuntivo

Sorgenti r35 ricostruiti dall'upstream fissato
`22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5` e dalla patch locale, senza eseguire
la build o il rendering.

1. **Damage esteso a tutto il layer.** `src/main.cpp`, handler `end4glass`,
   verifica correttamente la superficie cambiata ma poi passa a `damageBox`
   l'intera geometria del layer. Le Impostazioni sono un `PanelWindow` ancorato
   ai quattro bordi: spostare la scheda interna può invalidare tutto lo schermo.
   Questo comportamento è condiviso con r34.
2. **Maschera e clear a dimensione monitor.**
   `CGlassLayerSurface::sampleAndRedirect` conserva un framebuffer ARGB8888
   dell'intero monitor e lo pulisce sul `transformBox` del layer più padding.
   A 1920×1080, scala 1 attuale, sono 2.073.600 pixel / 7,91 MiB di storage
   colore per questo solo buffer. È un conteggio geometrico, non banda o tempo
   GPU misurati: compressione, tile e altri passaggi cambiano il costo reale.
3. **La cache parziale non vale durante lo spostamento.** La chiave
   `m_frostMapping` comprende crop, coordinate e bounds dei materiali.
   Quando cambiano, viene filtrata l'intera area satinata necessaria, non il
   solo rettangolo danneggiato. Serve a evitare pixel vecchi: rimuovere questa
   invalidazione senza rimappare i dati reintrodurrebbe errori visivi.
4. **R35 aggiunge un buffer grezzo separato.** Impedisce la sovrascrittura dei
   pixel filtrati esterni al danno. Aumenta la memoria rispetto a r34; la copia
   limitata al danno aiuta soprattutto a geometria ferma. Il vantaggio durante
   il trascinamento non è stato misurato e non può essere dato per acquisito.

La combinazione spiega perché proprio le Impostazioni possano costare di più.
Non dimostra un leak o un hang GPU. In un driver funzionante, più lavoro può
ridurre la fluidità senza implicare un blocco completo del computer.

## Ipotesi controllate e limiti

- Il blur usa framebuffer distinti per input, intermedio e output nel percorso
  satinato r35 esaminato. Non è stato individuato un feedback texture/render
  target in quel percorso. Non è un audit completo dello stato GL condiviso
  con il compositor.
- Molte allocazioni native non gestiscono un fallimento recuperabile nel
  plugin. Nella versione Hyprland fissata, `internalAlloc` esegue un `RASSERT`
  se il framebuffer non è completo e al termine cambia i binding GL. È un
  punto da verificare per memoria/formati, non la prova del freeze osservato.
  [Sorgente Hyprland corrispondente](https://github.com/hyprwm/Hyprland/blob/a0136d8c04687bb36eb8a28eb9d1ff92aea99704/src/render/gl/GLFramebuffer.cpp).
- La lettura del contrasto usa PBO e `glClientWaitSync(..., 0, 0)`, quindi non
  contiene un'attesa esplicita bloccante sul fence. La capability `contrast`
  è abilitata per r35: a Impostazioni aperte il QML interroga il plugin ogni
  1,25 secondi, mentre il codice nativo limita l'avvio dei campioni a uno ogni
  250 ms. `glReadPixels` e `glFlush` restano operazioni reali sul driver: il PBO
  non permette di escludere blocchi interni. È un secondo percorso da isolare
  in un ambiente sicuro prima di qualsiasi futura prova sul portatile.
- Traccia CPU del **codice crop reale**, scheda 980×720, frost 8, layer
  1920×1080, scala 1: tra x=0 e x=940, **zero cambi di dimensioni**; tra x=-300
  e x=1240, **10 cambi**. L'ipotesi di riallocazioni a ogni frame per normale
  movimento completamente visibile è smentita per questo caso. Dimensioni,
  contenuto e quantità di regioni reali possono dare risultati differenti.
- Snapshot successivo, senza plugin: circa 1,8 GiB RAM disponibili, VRAM usata
  490 MiB su 2 GiB, GTT usata 92 MiB su circa 2,8 GiB. Non descrive le risorse
  al freeze. Root al 99%, circa 2,3 GiB disponibili: resta poco spazio, ma
  nessuna prova che fosse esaurito durante gli episodi.
- `gpu_recovery=-1`, `lockup_timeout` vuoto: valori automatici osservati, non
  un override di test trovato. Non dedurre da `-1` che il recupero sia spento:
  il [codice Linux 6.18](https://github.com/torvalds/linux/blob/v6.18/drivers/gpu/drm/amd/amdgpu/amdgpu_device.c#L5295)
  decide per ASIC e condizioni. Nessun parametro modificato.

## Verifiche svolte e seguito

Passati, senza contesto grafico:

```sh
python3 tests/native-glass-frost-check.py /tmp/end4-r35-static-audit
python3 tests/native-glass-buffer-check.py /tmp/end4-r35-static-audit
```

La directory temporanea contiene soltanto sorgenti ricostruiti per l'analisi.
I mock non esercitano Mesa/AMDGPU, GL reale, tutte le interazioni con Hyprland o
il costo degli shader; non certificano la risoluzione del freeze.

Evidenze private persistenti e sorgente della traccia geometrica CPU:
`~/.local/state/end4-pC/diagnostics/20261116-r35-freezes/`.
La traccia geometrica è compilabile con C++23, include `src/GlassRegions.hpp`
dei sorgenti r35 e richiede i flag `pkg-config --cflags --libs hyprutils`;
non va collegata a OpenGL e non apre contesti grafici.

La priorità per una futura correzione è limitare l'invalidazione all'unione
dei vecchi/nuovi materiali più ombre e supporto ottico, verificare il ripristino
di stato/binding GL anche nei percorsi di errore e ridurre il clear della
maschera preservando la composizione. Il filtro deve continuare a vedere lo
sfondo aggiornato: congelarlo o eliminare invalidazioni necessarie maschera il
problema. Nessuna di queste correzioni è applicata o validata in questa indagine.
La causa precisa dei blocchi totali resta non accertata; plugin in quarantena.

## Ipotesi pressione memoria, dopo il ricordo dei vecchi blocchi senza swap

L'utente ricorda blocchi completi quando il sistema era privo di swap e la RAM
si esauriva. La somiglianza rende pertinente verificare pressione RAM, risorse
GPU e attese I/O; non identifica da sola lo stesso meccanismo.

Nei kernel dei boot coinvolti è registrata l'attivazione di `/swapfile`, circa
12 GiB, prima del login. Il caso attuale quindi non coincide con assenza di
swap. Nessun OOM kill pertinente nei log conservati. Le righe OOM killer
disabled/enabled delle 13:08:57 sono lontane dai nuovi blocchi e distanti circa
28 ms fra loro; non provano che l'OOM killer fosse disabilitato ai freeze.

Nuovo snapshot senza plugin: RAM disponibile 2240 MiB su 5793 MiB, swap usata
2123 MiB su 12287 MiB, VRAM usata circa 493 MiB su 2 GiB e GTT usata circa
100 MiB. PSI memory some/full avg10/60/300 tutti 0; contatore oom_kill del
boot corrente 0. La swap occupata non dimostra thrashing attuale. Questi dati
non descrivono lo stato al momento dei freeze.

AMDGPU gestisce buffer in VRAM e memoria di sistema e può mantenerne alcuni
vincolati per l'accesso GPU: swap libera non garantisce che ogni allocazione
grafica sia recuperabile. Vedere [gestione buffer AMDGPU](https://docs.kernel.org/gpu/amdgpu/driver-core.html).
La [PSI](https://docs.kernel.org/accounting/psi.html) distingue memoria occupata
da tempo effettivo passato bloccati per scarsità di risorse.

Prima di sostenere che il plugin esaurisca la memoria servirebbe una crescita
dei buffer/VRAM/GTT, calo di MemAvailable e/o aumento PSI/reclaim/I/O vicino
all'evento. Con memoria stabile e attese su fence GPU, l'ipotesi di errore di
sincronizzazione/driver diventerebbe più forte. Nessuna delle due sequenze è
documentata nei dati disponibili. Non aumentata la swap, imposto un limite
arbitrario al compositor o riattivato il recorder per verificarle.

## Nuovo blocco durante la preparazione del loader monouso

L'utente riferisce un nuovo blocco completo durante il lavoro, poi un avvio
senza retroilluminazione né boot visibile, un ulteriore avvio con glitch e
blocco nella schermata di caricamento del sistema, infine un accesso riuscito.
Le modifiche in corso riguardavano il sorgente Python del loader: nessun
caricamento del plugin o test grafico avviato. Il loader monouso è incompleto
e non validato; la sua preparazione è sospesa.

Dopo il riavvio, controlli su file e journal soltanto:

- `hyprglass.so` ordinario assente; nessun `test-once.json` o record monouso.
- Boot precedente `3a77b7d35b6842b78488451b386fdd18`: ultimo messaggio
  persistito alle 18:27:55 CET del 16 novembre, non necessariamente l'ora
  esatta del freeze. Boot corrente `8e8dd9c40e644b1289f4d8f4b947caf1`:
  primo messaggio alle 18:38:40. Nessun boot persistito intermedio trovato.
- Nessun OOM o reset/timeout GPU pertinente trovato nel kernel conservato.
  La riga di avvio «MCE: In-kernel MCE decoding enabled» non segnala un guasto.
- I messaggi `check` delle 18:25:30 con core disabilitato appartengono alla
  verifica negativa intenzionale dei mock CPU sul codice precedente, non
  a un crash del compositor né a un'esecuzione OpenGL.

La mancata comparsa del boot riferita dall'utente precede l'esecuzione di
Quickshell in quell'avvio. Non è spiegata dalla sola esecuzione del plugin
nella sessione corrente. Non identifica però da sola hardware, firmware o
driver come causa, né prova un danno alla GPU o esclude un ruolo del plugin
negli episodi precedenti. L'assenza di errori persistiti non esclude un guasto
che impedisca di salvare il journal. Nessuna nuova prova grafica autorizzata
o svolta in risposta all'episodio.

## Audit software successivo, senza rendering

- Kernel in esecuzione 6.18.36-1-lts; installato anche linux 7.0.13.arch1-1.
  Mesa 26.1.3-2, firmware AMD 20260622-1, Hyprland 0.55.4-1.
  Il registro pacman colloca gli ultimi aggiornamenti di questi componenti
  a giugno, non in coincidenza con il primo test TTY di novembre.
- Riga kernel: `loglevel=3 quiet amd_pstate=active`, oltre a root/BOOT_IMAGE.
  Nessun override AMDGPU trovato nei percorsi di configurazione esaminati:
  modprobe, udev, tmpfiles, servizi, ambiente e configurazione Hyprland.
  Questo non sostituisce uno snapshot precedente dell'intero sistema.
- Confrontati i kernel di 28 boot dal 5 al 16 novembre: lo stesso avviso
  PSP `LOAD_TA(0x1) ... (0x7)` è presente in tutti, inclusi quelli precedenti
  al primo test TTY. Nessun nuovo timeout/reset GPU, panic/Oops, OOM o
  hardware error corrispondente ai blocchi trovato con i filtri usati.
- `pacman -Qk`: nessun file mancante per linux-lts, Mesa, libdrm, firmware
  AMD, Hyprland, Aquamarine. `-Qkk` sugli stessi componenti grafici escluso
  kernel: solo avvisi UID/GID, spiegati dalla mappatura del namespace del
  sandbox (root host visibile come 65534). Nessun altro avviso: non è
  una verifica crittografica del contenuto.
- RAM disponibile circa 1803 MiB, swap 1384/12287 MiB, PSI memoria
  avg10/avg60 zero al controllo. Sono misure successive, non al blocco.
  Root al 99%, circa 2,3 GiB liberi: problema concreto di margine disco,
  non causa dimostrata di mancato boot o blocchi GPU.
- `amd-ucode` non risulta installato; revisione CPU registrata dal kernel
  `0x08108102`. Non dedurre che non esista microcode fornito dal BIOS.
  L'initramfs e grub.cfg richiedono root anche fuori dal sandbox: contenuto
  del microcode di avvio non verificato. Il microcode riguarda la CPU e
  non identifica da solo la causa grafica.
- `/var/lib/systemd/pstore` vuoto; `/sys/fs/pstore` non accessibile senza
  root. Non descrivere il secondo come verificato vuoto.
- Verifica fuori sandbox via bus utente: `end4-freeze-recorder.service`
  inactive/dead/disabled. Nessun processo record-freeze.py trovato.
  Nessun binario ordinario del plugin o ticket monouso predisposto.

Riletta la ricostruzione del primo test in
`black-screen-investigation-2026-11-15.md`: l'errore Python precede il lancio
del compositor di prova, ma non il logout della sessione principale. La
procedura complessiva resta un possibile innesco non dimostrato. Il runner
attuale interrompe subito `run`; non rilanciato. Nessun rendering, accesso
diretto alla GPU, modifica di sessione, pacchetto o parametro effettuato.

### Approfondimento fonti e letture root

`sudo -n` non disponibile: richiede password. Non lette immagini initramfs,
grub.cfg o pstore root; non tentato alcun aggiramento delle autorizzazioni.
Preparato `scripts/hyprland/read-boot-diagnostics.sh` per lettura dal terminale
attuale, senza TTY/logout; sintassi verificata con `bash -n`. Lo script legge
solo voci GRUB, elenco archivio early initramfs e pstore (64 KiB per record).

Segnalazione pertinente per hardware, non diagnosi del caso:
[bug kernel 222109, copia del rapporto originale dell'autore](https://www.mail-archive.com/dri-devel%40lists.freedesktop.org/msg642811.html),
10 ottobre 2026: Ryzen 3500U, GPU 1002:15d8 rev c2, anche LTS 6.18;
fault/timeout dopo cold boot con DPM forzato high e primo carico OpenGL.
L'autore riferisce assenza di fault con auto. Qui non trovate impostazioni
high nei percorsi controllati, né pacchetti TLP, power-profiles-daemon,
tuned, CoreCtrl o LACT. Non letto o cambiato il profilo GPU runtime.
Mancano anche i fault/timeout persistiti necessari per collegare i due casi.

[Mesa 26.1.4](https://docs.mesa3d.org/relnotes/26.1.4.html) corregge anche
un freeze video H264/VA e [26.1.5](https://docs.mesa3d.org/relnotes/26.1.5.html)
un deadlock OpenGL/X11. Condizioni diverse da un blocco dimostrato di
Hyprland/Glassy: non sostenere che l'aggiornamento risolva questo caso.
Non aggiornati pacchetti.

Individuata la [pagina BIOS Lenovo DS540493](https://pcsupport.lenovo.com/sr/en/products/laptops-and-netbooks/ideapad-s-series-netbooks/s145-15api/downloads/DS540493)
per S145-14API/S145-15API. La pagina pubblica letta non esponeva versione
e changelog sufficienti a stabilire un fix pertinente: nessuna conclusione
su disponibilità o utilità di un BIOS successivo a BUCN28WW, nessun flash.

### Output privilegiato fornito dall'utente

Lo script conferma entrambe le voci kernel (linux-lts predefinito e linux),
ciascuna con la propria initramfs e senza initrd microcode separato. Nessun
parametro AMDGPU aggiuntivo nelle voci riportate. Nessuna voce microcode
nell'elenco early di entrambe le immagini. `/sys/fs/pstore` e
`/var/lib/systemd/pstore` risultano effettivamente vuoti in questa lettura.
Questo non esclude un hang senza record persistente.

CPU corrente: famiglia 23 (0x17), modello 24 (0x18), stepping 1,
microcode 0x08108102. Il
[README upstream linux-firmware](https://kernel.googlesource.com/pub/scm/linux/kernel/git/firmware/linux-firmware/+/refs/heads/main/amd-ucode/README)
consultato non elenca una patch per famiglia 0x17/modello 0x18/stepping 1.
Non attribuire quindi valore diagnostico all'installazione di amd-ucode né
promettere un aggiornamento effettivo per questo processore: il solo pacchetto
assente non prova che la revisione CPU sia correggibile tramite quel pacchetto.
Nessun pacchetto installato o immagine rigenerata.
