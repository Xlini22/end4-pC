# Candidata nativa: buffer, stato GL e damage delle Impostazioni

## Stato al 21 novembre 2026

Ripristinati end4-pC e installazione permanente di HyprGlass su richiesta
dell'utente. `qs-switch ii` predispone ii senza plugin; `qs-switch end4`
predispone end4-pC, vetro abilitato e sorgente `windows`. Il controllo HyprGlass
è disponibile in Impostazioni → Glassy → Generale. I cambi di installazione
escludono la sessione corrente tramite `deferInstance`: serve un nuovo accesso,
senza caricamento/scaricamento a caldo.

Le patch popup aggiungono ereditarietà del darker della barra, riferimento
automatico comune, conservazione della maschera nei ridisegni parziali e
damage limitato al popup interessato. Con il plugin la dissolvenza appartiene
al compositor; il percorso senza plugin conserva le animazioni Qt. L'ultima
patch conserva i parametri del darker anche dopo il ritiro del client Wayland,
durante la chiusura.

Revisione installata: `close-darkening-2026-11-21`, SHA256
`756b653d6ad6ece39c076c042dcfecfcd40719ce58fc8b867de7e9297e3dfa46`.
Compilazione completa, test del darker in chiusura e controlli di sicurezza
con GL simulato superati. Il caricamento di questa revisione è rinviato al
prossimo accesso; la relativa resa visiva resta da verificare. L'utente ha
valutato positivamente lo stato popup precedente a questa ultima patch.

L'utente ha inoltre riferito errori in Memtest86+ fuori da Linux: questo lavoro
non dimostra di avere risolto i blocchi hardware/sistema. Vedi
`black-screen-investigation-2026-11-17.md`. Le sezioni seguenti sono storiche.

## Stato successivo: confronto con Illogical Impulse, 18 novembre

Alle 10:20, su richiesta dell'utente, selezionata la configurazione `ii` per
i prossimi accessi e disabilitato il caricamento automatico di HyprGlass.
Il binario permanente è conservato come
`~/.local/share/end4-pC/native-glass/hyprglass.so.disabled-for-ii-20261118-102005`.
Nessun ticket monouso pendente. Il plugin era già caricato nella sessione:
non scaricato live, serve logout/login per il confronto senza plugin.
Repository end4-pC e configurazioni preservati. Backup privato di variabili,
configurazione condivisa e override in
`~/.local/state/end4-pC/shell-switches/20261118-102005/`.
Non copiato il contenuto delle impostazioni private nel repository.
Le sezioni seguenti descrivono gli stati precedenti.

## Stato aggiornato al 18 novembre 2026

Su richiesta esplicita dell'utente, r36-candidate è ora installata in modo
permanente in `~/.local/share/end4-pC/native-glass/hyprglass.so`.
ABI e SHA256 verificati; binario identico a quello di staging del 17 novembre
(`21c8dcadd863cb4a7cc64b8ac8553f42c2d29598fca5ebba5da6689dea864e2d`).
Manifest precedente salvato nella stessa directory. Nessun ticket pendente.
Il manifest permanente esclude soltanto la sessione di installazione tramite
`deferInstance`: caricamento previsto dal prossimo accesso, anche dopo reboot.
Non vale più la disattivazione automatica del percorso monouso dopo un reboot.
Al controllo di installazione la lista plugin era vuota; nessun hot load/unload
o riavvio di sessione eseguito. Nessuna nuova validazione grafica né causa dei
blocchi risolta da questa installazione. Le sezioni successive sono storiche.
Registro: `diagnostics/native-glass-permanent-install-20261118.json`.

Preparata il 16 novembre 2026 su richiesta dell'utente, **non installata**.
Patch incrementale: `patches/native-glass-safety.patch`, da applicare dopo la
patch r35 `scripts/glass/native/live-background.patch` su upstream
`22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5`.
Identificativo sorgente: `end4-live-0.6.4-r36-candidate`.
SHA256 patch: `8f60efb7363ebc1a047f9ab970e2717a066c7f7f674de56a24b2fac6bd1b61c0`.

Nella prima analisi del 16 novembre il file r35 di produzione e il backend
non erano cambiati; l'aggiornamento successivo del loader è descritto sotto.
Nessun binario nuovo
compilato o installato, nessun reload, rendering, plugin load/unload, recorder,
compositor di prova o modifica di driver/clock. Restano in quarantena le build
precedenti. I sorgenti esaminati sono in `/tmp/end4-r36-safety`; la patch
persistente consente di ricostruirli dopo la pulizia di `/tmp`.

## Prova predisposta su richiesta del 17 novembre, ore 17 circa

Questa sezione aggiorna lo stato storico precedente: candidata compilata e
ticket monouso predisposto, **non caricata nella sessione di preparazione**.
Nessuna correzione dei blocchi certificata e nessuna verifica grafica eseguita.

Directory persistente (relativa alla root del repository):
`diagnostics/native-glass-once-20261117-170152/`.
Contiene sorgenti fissati, log per fase, `events.jsonl` con scritture fsync,
binario e manifest in `staging/`. SHA256 del binario:
`21c8dcadd863cb4a7cc64b8ac8553f42c2d29598fca5ebba5da6689dea864e2d`.

Applicate r35 e patch safety con hash verificati; passati i controlli safety,
buffer (`--pending-target`), frost e visibility, tutti con GL simulato.
Build `make -j1`, nice 10, limite memoria virtuale 1536 MiB per processo,
`-fPIC -g0 -O2 -std=c++23 -fno-gnu-unique`; simboli non necessari rimossi.
Un controllo iniziale della stringa completa nel binario ha fermato la
preparazione prima di creare manifest o ticket: il compilatore non conserva
la stringa in forma contigua. Verificati invece costante sorgente compilata
e suffisso candidato nel binario, oltre a identità ABI e hash del file.
Nessun caricamento nativo eseguito per ricavare la versione.

Verifica finale: lista plugin `[]`, registratore inactive/disabled, binario
ordinario assente, ticket `test-once.json` riferito al binario di staging.
Il prossimo logout/login in Hyprland **nello stesso boot** può consumarlo;
il solo reload di QS non basta, un reboot lo rende scaduto. Non è stato
forzato logout, riavvio o scaricamento di plugin. La prova grafica minima
descritta prima della preparazione resta apertura Settings e breve drag,
senza benchmark, renderer di prova o registratore.

## Loader monouso: completamento del 17 novembre 2026

Il loader Python ora include il percorso monouso verificato con mock. Questo
non valida la candidata r36 sulla GPU né risolve la causa dei blocchi.
Nessuna prova reale predisposta o avviata durante il completamento.

Condizioni e comportamento:

- La posizione ordinaria `~/.local/share/end4-pC/native-glass/hyprglass.so`
  deve restare assente (anche un link pendente viene rifiutato). Il binario
  da provare rimane nella directory di staging, con manifest ABI/SHA256 valido.
- `--arm-once STAGING_DIRECTORY` richiede l'identità della sessione corrente
  e rifiuta un plugin già caricato. Crea un ticket valido soltanto nel boot
  corrente e utilizzabile dalla successiva sessione Hyprland dello stesso
  boot; reload di QS nella sessione di preparazione e identità assente non
  possono consumarlo. Un ticket esistente non viene sovrascritto.
- Un semplice probe non consuma il ticket. `--ensure` ricontrolla boot,
  sessione, ABI e hash, poi rinomina e sincronizza su disco il ticket consumato
  **prima** di invocare il caricamento nativo. Se la sincronizzazione fallisce,
  il caricamento non parte. Errore o timeout di caricamento non riarmano nulla.
- Le operazioni arm/cancel/ensure usano lo stesso `flock` non bloccante:
  richieste concorrenti vengono rifiutate, senza attendere un caricamento.
- Al riavvio cambia il boot ID: un ticket ancora pendente risulta scaduto.
  Uno già consumato non è più cercato dal loader. Senza binario ordinario
  non c'è quindi un caricamento automatico successivo attraverso questo
  percorso, anche se il tentativo precedente ha bloccato il sistema.
- `--cancel-once` elimina un ticket pendente, anche scaduto, senza interrogare
  il compositor. Non scarica un plugin già caricato. I record `test-used-*`
  restano per diagnosi; una nuova prova richiede un nuovo arm esplicito.

Il codice non annulla altri percorsi di caricamento manuali o configurati
fuori da questo loader e non può garantire che il PC riparta dopo un guasto
hardware, firmware o driver. Non esegue un recupero GPU o un rollback live.

Verifica ripetibile, senza contesto grafico, eseguibile o manifest reali:

```sh
python3 -B tests/native-glass-loader-check.py
```

La verifica copre anche file ordinario/link pendente, staging non valido,
plugin già presente, preparazione duplicata, probe, sessione sconosciuta,
scadenza a reboot, persistenza prima del load, errore/timeout, errori fsync,
UUID invalido, tentativo già registrato, cancellazione e lock concorrenti.
Tutti gli accessi al compositor sono sostituiti da risposte simulate e tutti
i ticket sono creati in directory temporanee. Non sono stati eseguiti
`--arm-once`, `--ensure` o `--cancel-once` sull'installazione reale.

Un'eventuale verifica grafica resta separata: prima si deve scegliere e
verificare il binario candidato, lasciando assente quello ordinario. La prova
minima proposta è un solo accesso nello stesso boot, apertura delle Impostazioni
e breve trascinamento normale, senza benchmark o registratore. Non eseguita.

## 1. Durata, rilascio e dimensioni dei buffer

Ownership esaminata: per layer, un sample, uno scratch clear se necessario,
tre buffer frost r35 (input/output/intermedio), una maschera a dimensione
monitor e, su richiesta, il framebuffer contrasto 32×24 con PBO da 3072 byte
e al massimo un fence. Il target originale è trattenuto soltanto tra pre e
post; i pass mantengono lo stato tramite shared_ptr e il layer è un riferimento
debole. La mappa degli stati elimina layer scaduti al successivo hook renderLayer.
Non è stato riprodotto un leak crescente nei mock CPU.

Correzioni:

- Riuso del sample e dello scratch blur controlla **formato oltre a dimensioni**.
  Lo stesso vale per frost delle finestre e maschera ARGB8888 dei layer.
- I tre framebuffer satinati del layer vengono rilasciati quando non ci sono
  più materiali frost. Il target source viene ricollegato dopo il rilascio.
- Il distruttore del layer azzera anche `m_savedCurrentFB` prima di ripristinare
  i binding. Prima quel membro veniva distrutto automaticamente *dopo* il corpo
  del distruttore: con un target ancora trattenuto, il suo rilascio poteva
  riportare i binding a zero dopo il ripristino.

Il caso del target trattenuto è riproducibile con GL simulato: r35 fallisce il
controllo `--pending-target`, la candidata passa. Non è stato dimostrato che
quel percorso avvenga negli episodi reali segnalati.

Restano riuso dei buffer e capacità crop a blocchi da 64 texel. Per la geometria
di drag già analizzata, pannello completamente visibile, nessun cambio delle
dimensioni del crop. La maschera resta a dimensione monitor per preservare il
mapping del foreground; si riduce il clear, non la risoluzione.

Non è stato aggiunto un limite RAM arbitrario al compositor. I mock non misurano
VRAM reale o allocazioni ancora in volo nel driver. L'allocatore Hyprland può
eseguire un RASSERT su framebuffer incompleto: la candidata non lo trasforma
in un errore recuperabile e non garantisce sopravvivenza a OOM del driver.

## 2. Stato OpenGL e campionamento del contrasto

Difetto riprodotto: `sampleContrast` spegneva lo scissor e poteva alterare il
binding texture durante l'allocazione, ma ripristinava soltanto framebuffer,
PBO e pack state. Il mock esegue la funzione reale con stato iniziale non
predefinito: r35 lo altera, la candidata lo conserva.

Il guard ora ripristina anche box/abilitazione scissor tramite le API di
Hyprland, mantenendone coerente la cache, e il binding texture 2D sull'unità
attiva. Nel codice della versione Hyprland fissata l'allocatore non cambia
l'unità texture attiva. Non si aggiungono questi query a ogni fragment/draw:
sono nel percorso di campionamento già limitato a 4 Hz.

Il fence continua a essere interrogato con flag 0 e timeout 0; il PBO non viene
mappato prima del completamento. Se resta pendente oltre due secondi, il
campionatore si dichiara fallito: smette di richiedere frame/campioni e conserva
il singolo buffer pendente fino alla distruzione della superficie. Nessun
glFinish o attesa bloccante introdotti. Guardie anche sul monitor mancante.

Questo limite interrompe i tentativi successivi, **non** può interrompere una
chiamata glReadPixels/glFlush bloccata nel driver. La formula dell'oscuramento
automatico nel vertex shader non dipende dal readback CPU del contrasto e
rimane invariata. La perdita del campione fa usare il fallback del colore testo.

## 3. Invalidazioni e clear

Per `quickshell:settings` enhanced con monitor non ruotato, l'handler geometria
invalida separatamente l'impronta vecchia e quella nuova, con margine conservativo
per rifrazione, Gaussiane e antialiasing. Le coordinate sono logiche globali,
inclusi origine monitor e scala; viene arrotondato verso l'esterno.

La selezione della superficie applicabile è condivisa con il renderer. Geometria
mancante, duplicati ambigui, dimensioni incompatibili, cambio di modalità o
monitor ruotato conservano il danno completo. Le altre superfici non cambiano
politica di invalidazione.

Il contrasto e le transizioni del darker richiedono a loro volta il ridisegno
del materiale settings, anziché di tutto il layer quando la geometria è nota.
Gli aggiornamenti espliciti del profilo possono ancora invalidare il layer
completo: non sono il percorso continuo di drag.

Il clear della maschera settings già allocata segue i rettangoli disgiunti del
damage corrente. I pixel fuori danno restano disponibili come il foreground Qt
che non viene ridisegnato lì. Un buffer appena allocato o il percorso legacy/
ruotato mantiene il clear completo previsto. Non viene congelato il backdrop.

Nel controllo CPU, due rettangoli da 10×20 e 30×40 puliscono 1400 pixel invece
di 2.073.600; è un conteggio del caso simulato, **non** un miglioramento FPS
misurato né una previsione del danno reale durante il drag.

## Verifiche e limiti

Passati, senza contesti grafici:

```sh
python3 tests/native-glass-safety-check.py /tmp/end4-r36-safety
python3 tests/native-glass-buffer-check.py /tmp/end4-r36-safety --pending-target
python3 tests/native-glass-frost-check.py /tmp/end4-r36-safety
python3 tests/native-glass-visibility-check.py /tmp/end4-r36-safety
python3 tests/glass-profiles-check.py /tmp/end4-r36-safety
```

Il nuovo controllo esegue codice reale estratto dai sorgenti per readback,
errori/timeout, riuso buffer, handler damage e clear; GL è simulato. Applicazione
pulita della patch verificata e contenuto risultante confrontato con la candidata.
I quattro translation unit modificati passano `g++ -fsyntax-only` con le
intestazioni Hyprland installate, un processo per volta e limite di memoria
virtuale di 1 GB. Avvisi narrowing preesistenti nel renderer; nessun errore finale.
Gli shader sono byte per byte r35: nessuna modifica a rifrazione, satinatura,
riflessi o formula del darker. L'invalidazione della cache frost al movimento
resta attiva per correttezza.

Questi risultati correggono difetti e casi di cleanup riproducibili; non provano
la causa o la risoluzione delle schermate nere, la correttezza visiva del clear
parziale, la fluidità o l'assenza di stalli Mesa/AMDGPU. Non installare la candidata
come automatica continuazione: prima serve definire un ambiente di verifica che
non esponga di nuovo il desktop ai blocchi osservati. Nessuna verifica grafica
è stata avviata o autorizzata da questa sola preparazione.
