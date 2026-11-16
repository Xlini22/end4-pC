# Candidata nativa: buffer, stato GL e damage delle Impostazioni

Preparata il 16 novembre 2026 su richiesta dell'utente, **non installata**.
Patch incrementale: `patches/native-glass-safety.patch`, da applicare dopo la
patch r35 `scripts/glass/native/live-background.patch` su upstream
`22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5`.
Identificativo sorgente: `end4-live-0.6.4-r36-candidate`.
SHA256 patch: `8f60efb7363ebc1a047f9ab970e2717a066c7f7f674de56a24b2fac6bd1b61c0`.

Il file r35 di produzione e il backend non sono cambiati. Nessun binario nuovo
compilato o installato, nessun reload, rendering, plugin load/unload, recorder,
compositor di prova o modifica di driver/clock. Restano in quarantena le build
precedenti. I sorgenti esaminati sono in `/tmp/end4-r36-safety`; la patch
persistente consente di ricostruirli dopo la pulizia di `/tmp`.

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
