# Darker automatico: media temporale su 1,5 secondi

Stato: **r44 installata** su `feat/bar-app-overlap`, con storico per materiale
stabile e intensità automatica per profilo. Preservate inizializzazione r43 e
correzioni precedenti. Caricamento nativo rinviato al prossimo logout/login;
nessun reload o test grafico avviato.

## Percorsi individuati

- Quickshell: `FrostedGlass.qml`, con misura spaziale in `glassLuma.vert` e
  applicazione in `liquidLens.vert` / `liquidLens.frag`. Il vecchio debounce
  era limitato al movimento delle Impostazioni; gli altri materiali misuravano
  direttamente lo sfondo corrente.
- HyprGlass: `darkening.vert` in `Shaders.hpp`, che calcola l'indicatore di
  luminosità dai quattro campioni esistenti; `darkenGlass` applica il darker.
  Sono interessate sia le superfici layer-shell sia le decorazioni delle finestre.
- `GlassCompositor.qml` invia intensità manuale e modalità automatica e misura
  anche il contrasto del testo. Quest'ultima misura non viene rallentata.

## Correzione

La media temporale viene applicata all'indicatore di luminosità esistente,
prima della conversione in oscuramento. Restano invariati campionamento
spaziale, soglia adattiva, intensità manuale e trattamento ottico dello sfondo.

Gli intervalli sono fissi: i cambiamenti continui non riavviano l'attesa.
I campioni sono ponderati per il tempo trascorso, evitando che una fase con
più frame pesi più di una fase con meno frame. Si integra il campione precedente
fino al successivo, dividendo correttamente il contributo ai confini degli
intervalli. È una stima da campioni, non la registrazione di ogni istante dello
sfondo. Gli intervalli senza nuovi campioni conservano l'ultimo campione noto.

Ogni 1,5 secondi si pubblica la media dell'intervallo concluso. Il target resta
fermo fino alla pubblicazione successiva; solo il raccordo di 800 ms evolve tra
due target. Dalla r42, un materiale appena creato inizializza il darker con la misura corrente
dello sfondo; questa misura non viene conteggiata come un intervallo completo.
Il darker manuale resta invariato.

### Quickshell

`patches/glass-temporal-darkening-qml.patch` sostituisce il debounce con un
accumulatore ricorsivo da un pixel RGBA32F, campionato al massimo a 10 Hz mentre
il materiale è visibile e l'automatismo è attivo. Le richieste non si accodano:
un aggiornamento ancora pendente fa conservare l'ultimo campione.
Il ping-pong è gestito da `ShaderEffectSource.recursive`; l'effetto che scrive
i dati disattiva il blending. La cattura ottica principale rimane `live`.
La patch include gli shader sorgente e i relativi QSB compilati offline.

### HyprGlass

`patches/native-glass-temporal-darkening.patch` aggiunge due texture RGBA32F
da 33×1 pixel per superficie: un campione per il materiale base e fino a 32
regioni. I dati delle due texture occupano complessivamente 1056 byte per
superficie, oltre agli oggetti GL. Non vengono conservati frame dello sfondo.

Il primo passaggio misura lo sfondo corrente e aggiorna l'accumulatore;
il passaggio visivo usa soltanto la media pubblicata. Non ci sono letture verso
la CPU, fence, attese sincrone o timer che forzano frame continui. Si usano i
rendering già richiesti: la media viene pubblicata al primo rendering dopo
la scadenza. Durante una pausa si usa l’ultimo campione noto. Il raccordo
parte dalla pubblicazione effettiva, anche se il frame arriva in ritardo.
La transizione invalida solo il materiale con le
funzioni di damage esistenti; dopo 800 ms termina.

Le bande ottimizzate delle Impostazioni mantengono i loro ritagli: la misura
usa l'elenco completo una volta e gli indici stabili riallineano ogni banda
alla propria media. Le chiusure conservano lo storico già acquisito.
Texture, framebuffer, viewport, sampler, maschera colore e capacità GL vengono
gestiti esplicitamente. Le risorse sono limitate e rilasciate con la superficie.
Se il formato floating point non è supportato, l'automatismo non ripiega sul
frame corrente: resta l'intensità manuale e non vengono ritentate allocazioni.

## Verifiche eseguite

Applicazione di tutte le patch alla sorgente upstream pulita, fissata a
`22acd5db6ef73fa34cad2d5ce8b76cf37e9acaa5`.

```sh
python tests/darker-temporal-check.py diagnostics/darker-temporal-20261123/source --qml-patch
python tests/native-glass-temporal-state-check.py diagnostics/darker-temporal-20261123/source
```

Il primo comando prepara una copia QML temporanea applicando la relativa patch:
non modifica i file caricati dalla sessione. Verifica le implementazioni reali
del clock C++ e JavaScript e l'aritmetica estratta dagli shader: tempi irregolari,
alternanze continue, target fermi, confini di intervallo, pause e reset. Compila
e collega gli shader nativi con `glslangValidator`, e genera i QSB con `qsb`,
senza creare contesti grafici.

Il secondo compila il percorso GL reale contro funzioni simulate, verificando
stato ripristinato, indici delle bande, modo manuale, snapshot di chiusura,
numero di allocazioni, fallimento del framebuffer e distruzione delle risorse.

Superati anche i controlli esistenti senza rendering su fade del darker,
buffer, sicurezza GL, frost, visibilità, profili, top bar ed eventi della barra.
Non eseguiti rendering, llvmpipe, compositor di prova, registrazioni o stress test.
Compilazione completa della candidata r37 riuscita, sequenziale con limite
di memoria virtuale di 512 MiB per il processo di compilazione. Verificati ELF,
entry point esportati e corrispondenza ABI con la sessione Hyprland 0.55.4.
Resa visiva non verificata. Candidata installata con `deferInstance` della
sessione corrente: sarà caricabile dopo logout/login. Backup precedente in
`~/.local/share/end4-pC/native-glass/before-temporal-darkening-20261123-123114-323851`.

Artefatti locali: `diagnostics/darker-temporal-20261123/hyprglass.so`,
`manifest.json`, `verification.json` e log di compilazione persistente.
SHA-256 della libreria: `d8f2c072793bf05afed7184b334ded7291b8f0b1baef5370cef5f9b2cde4827e`.

Il builder applica la nuova patch e richiama entrambi i nuovi controlli. I
vecchi test che creano un contesto GL sono ora espliciti tramite
`HYPRGLASS_RENDER_TESTS=1`; il percorso predefinito non li esegue.

## Attivazione e prova minima proposta

La candidata nativa è identificata come `end4-live-0.6.4-r37-candidate`;
il caricatore ora la riconosce mantenendo compatibili le versioni precedenti.
Prima di attivare occorre verificare l’ABI e conservare hash e copia precedente. La patch QML si applica separatamente;
non sostituisce da sola il percorso del plugin. Per HyprGlass evitare
sostituzioni o unload/load nella sessione: installare per il prossimo accesso.

La prova visiva minima usa una sola finestra già aperta, con scene chiare e scure
per circa 5–10 secondi: verificare il raccordo lento del darker e, contemporaneamente,
che movimento dello sfondo e rifrazione restino fluidi. Concludere controllando
il darker manuale e la chiusura di un popup. Non avviare registratori o compositor
aggiuntivi. I controlli statici non certificano né l'assenza di flash visibili
né la stabilità del driver sulla macchina.

## Correzione r38: formato di allocazione OpenGL ES

Dopo il primo accesso con r37, l’utente segnala oscuramento automatico assente.
Le letture IPC confermano r37 caricata e Glassy attivo; il log esistente indica
OpenGL ES 3.2. Individuato nella candidata un abbinamento non valido:
`GL_RGBA32F` con tipo `GL_HALF_FLOAT`. La tabella 3.2 della
[specifica Khronos OpenGL ES 3.0.6](https://registry.khronos.org/OpenGL/specs/es/3.0/es_spec_3.0.pdf#page=124)
richiede `GL_FLOAT` per RGBA32F. La chiamata non valida può lasciare incompleto
il framebuffer: il fallback previsto disattiva l’automatismo e mantiene soltanto
il darker manuale. Non è stata letta diagnostica GL dal contesto in uso, quindi
la corrispondenza con il difetto visivo resta da confermare.

La r38 corregge soltanto il tipo a `GL_FLOAT`, mantenendo formato, dimensioni,
media temporale e rendering invariati. Il test con GL simulato ora valida anche
formato interno, formato esterno e tipo: fallisce sulla sorgente r37 e passa su
r38. Il caricatore riconosce entrambe le versioni. Nessun rendering di prova.
La r37 resta conservata in `diagnostics/darker-temporal-20261123`; la correzione
viene compilata in `diagnostics/darker-temporal-r38-20261123`.

R38 installata con backup della r37 in
`~/.local/share/end4-pC/native-glass/before-temporal-darkening-20261123-123922-786703`.
Hash: `da6b8a1998e5409e091b002de113c26caecc9100eda1c2f5c69c2e8f332222ab`.
Il manifest esclude la sessione corrente; occorre logout/login. Nessun hot reload.
Il difetto visivo non è ancora verificato dopo la correzione.

## R39: ricomparsa senza hover

La r38 può conservare l’ultimo campione durante una pausa. Alla ricomparsa,
un intervallo che comprende la pausa può quindi pubblicare quel campione
precedente. Inoltre il clock avanza soltanto dentro il rendering: se l’apertura
termina prima di 1,5 secondi, nessun frame successivo è garantito alla scadenza.
L’hover fornisce quel frame mancante. Questi sono difetti del percorso rilevati
nel codice e riprodotti nel modello; la resa sul desktop resta da verificare.

La dock, come le barre in autohide, resta mappata e sposta il contenuto fuori
dalla finestra. La sola visibilità Wayland non identifica la sua chiusura.
La candidata QML comunica quindi il loro stato esplicito di apertura. Il nuovo
formato `end4glass` modo 3 aggiunge un booleano per superficie, accettando anche
i formati precedenti. Il caricatore negozia la capacità: con r38 e precedenti
si continua a inviare il formato precedente. I materiali dello stesso pannello
condividono il segnale della finestra. Popup e sidebar che vengono smappati
seguono invece lo stato reale della superficie; le chiusure mantengono lo snapshot.

Alla ricomparsa si scartano somma, ultimo campione e tempo trascorso prima di
nascondersi. Resta solo il tono visualizzato, usato come origine del raccordo:
non entra nella nuova media. Il primo campione visibile apre un nuovo intervallo
completo di 1,5 secondi; un timer Wayland singolo richiede il ridisegno alla sua
scadenza, anche senza mouse. Il timer non viene riavviato dai campioni o dalla
geometria. Dopo la pubblicazione resta il raccordo di 800 ms già esistente.
Il timer si disarma alla pubblicazione, al nascondimento e alla distruzione:
non genera un ciclo periodico di frame quando il desktop è fermo.

I ridisegni usano i limiti dei materiali e il supporto blur/rifrazione esistenti
sui monitor con trasformazione normale; gli altri casi mantengono il fallback
al rettangolo del pannello. Nessuna nuova invalidazione globale del monitor.
La correzione riguarda i pannelli layer-shell. Le decorazioni native di normali
finestre applicative non hanno il ciclo di autohide della dock e non sono state
estese con un timer. Non si cambia il loro percorso ottico.

La patch QML candidata conserva lo storico visivo quando un materiale si
nasconde, sospende il campionamento e riparte con un intervallo nuovo. Gestisce
anche una risposta di campionamento ancora pendente durante hide/reveal.
Sfondo, rifrazione, satinatura, geometria, magnificazione e policy autohide
continuano ad usare i percorsi precedenti.

Verifiche senza rendering:

```sh
python3 tests/darker-reappearance-check.py diagnostics/darker-temporal-r39-20261123/source --qml-patch
python3 tests/darker-temporal-check.py diagnostics/darker-temporal-r39-20261123/source --qml-patch
python3 tests/native-glass-temporal-state-check.py diagnostics/darker-temporal-r39-20261123/source
python3 tests/native-glass-loader-check.py
```

Il primo test esegue i metodi nativi reali con un timer simulato e le funzioni
QML estratte tramite Node: apertura senza input, timer non rinviato, nessun
riarmo dopo la prima pubblicazione, hide/unmap/close/distruzione, ripresa durante
un campione pendente, serializzazione e parsing compatibili dei due formati.
Il test degli shader verifica che una ripresa con luminosità 1 produca media 1
indipendentemente da somma e campione precedenti, conservando il tono del raccordo.
Superati anche i controlli esistenti su fade, buffer, GL simulato, visibilità,
profili, frost e barra. Qt 6 qmllint controlla soltanto la sintassi; mancano alcuni
metadati dei tipi della shell nella copia temporanea. Build nativa completa
sequenziale riuscita con limite di 512 MiB; ELF e simboli esportati verificati.
Nessun contesto GL, llvmpipe, compositor o registratore avviato.

Artefatti r39: `diagnostics/darker-temporal-r39-20261123/`, con libreria,
manifest, hash delle due patch e log persistenti. Per attivarla serviranno
insieme plugin r39 e patch QML; non è sufficiente sostituire soltanto la libreria.
La r39 è stata installata su richiesta, per il prossimo login. Backup della r38:
`~/.local/share/end4-pC/native-glass/before-temporal-darkening-20261123-131258-689048`.
Backup QML e lista dei file nuovi:
`diagnostics/darker-temporal-r39-20261123/qml-before-install-20261123-131249/`.
I test senza rendering passano anche sui file QML installati. La lettura IPC
conferma che Glassy è attivo e che Hyprland mantiene r38 in questa sessione.

Prova minima proposta dopo l’attivazione: dock su sfondo scuro, nasconderla,
passare a uno sfondo bianco, farla riapparire e togliere il cursore dalle icone.
Senza altre interazioni, attendere circa 2,5 secondi: deve pubblicare la nuova
media e completare il raccordo. Ripetere invertendo chiaro/scuro e con un popup;
fare inoltre una chiusura/riapertura rapida durante l’attesa. Niente registrazioni
né compositor aggiuntivi. Solo questa prova può confermare il risultato visivo.

## R40: cambio scena con dock sempre visibile

Nella r39 il timer si fermava dopo la prima pubblicazione (`clock.published`).
Una dock che passa direttamente dalla sovrapposizione su un’app al workspace
vuoto resta visibile: non riceve la transizione di visibilità che apriva un nuovo
intervallo. I frame della transizione possono raccogliere i nuovi campioni,
ma a transizione conclusa manca un frame garantito per pubblicare l’intervallo.
Il modello riproduce questa mancanza senza attribuirla al driver.

La r40 segnala esplicitamente i cambi esterni sul monitor interessato: workspace
attivo, focus/fullscreen/spostamento di finestre e apertura/chiusura. Durante i
render già richiesti osserva inoltre le animazioni di offset/alpha del workspace,
comprese quelle che tornano indietro dopo un gesto annullato. Non riutilizza il
contatore generico della scena, che viene incrementato anche da layer del vetro.
I ridisegni del darker non producono questo segnale esterno.

Il primo cambiamento dopo una pausa apre una nuova raccolta mantenendo il tono
visualizzato. Le notifiche successive non riavviano il clock né rinviano il timer:
le pubblicazioni continuano su intervalli fissi di 1,5 secondi. Quando la scena
smette di cambiare, si completa anche il primo intervallo interamente successivo
all’ultimo cambiamento osservato; poi il timer si disarma. Possono quindi servire
due intervalli per ottenere il target completamente assestato, ma il primo
aggiornamento non viene rimandato. Resta il raccordo di 800 ms. L’autohide continua
a cancellare l’attesa se il materiale si nasconde. Riavvii ripetuti prima del primo
campione conservano il tono precedente invece di azzerarlo.

Non vengono introdotti altri buffer, readback o invalidazioni globali. Gli eventi
richiedono soltanto il ridisegno dei materiali del monitor coinvolto, con le
funzioni di damage della r39. Non cambia la politica di sovrapposizione/autohide,
la magnificazione o il percorso ottico. Il rilevamento riguarda gli eventi e le
animazioni indicati: non è una scansione continua dei pixel di tutti gli sfondi.

Esteso `tests/darker-reappearance-check.py` per eseguire i metodi reali con clock
e timer simulati: dock continuamente visibile, scene che cambiano oltre la prima
scadenza, pubblicazioni a 1,5 secondi senza debounce, finestra finale assestata,
stop durante i soli frame di fade, cancellazione del gesto, isolamento per monitor
e visibilità persa durante l’attesa. Il clock viene iniettato solo nel test.
Superati controlli senza rendering di aritmetica/shader offline, stato GL simulato,
loader, buffer, fade, profili, visibilità, frost e barra. Build completa r40
sequenziale con limite di 512 MiB riuscita; ELF, entry point e ABI verificati.
Resa visiva ancora non confermata. Nessun contesto GL di prova o llvmpipe avviato.

Artefatti: `diagnostics/darker-temporal-r40-20261123/`. Hash della libreria:
`d746f3cf7111fbb615a4b37502f2479cc49a57236692be01aa544417c830a463`.
Installata su richiesta per il prossimo login; il manifest esclude questa sessione.
Backup r39:
`~/.local/share/end4-pC/native-glass/before-temporal-darkening-20261123-141832-024008`.
La patch QML r39 già presente rimane compatibile; non sono stati cambiati file QML
per questo aggiornamento.

Prova minima dopo logout/login: ripetere il passaggio al workspace vuoto prima
da un’app senza sovrapposizione della dock, poi da una con sovrapposizione.
In entrambi i casi lasciare il cursore fuori dalle icone e attendere circa 4 secondi
senza ulteriori gesti. Controllare poi una transizione inversa e un breve gesto
annullato. Il darker deve aggiornarsi senza hover, mantenendo il tono nell’attesa
e terminando la transizione; registrazioni e compositor aggiuntivi non servono.

## R41: riflessi sui bordi della dock satinata

L’utente conferma darker corretto e riflessi apparentemente assenti sulla dock.
La lettura della configurazione indica riflessi 50%, blur 1,5 px; la geometria
IPC conferma `frost=1.5`. Le due condizioni native `frost <= 0.0` escludevano
Fresnel e specular per qualunque materiale satinato. Il corpo di `shadeGlass`
è identico alla baseline r36: l’esclusione precede il darker temporale.

Patch separata `patches/native-glass-frost-reflections.patch`: elimina le sole
esclusioni per satinatura, preservando i controlli di intensità. Il percorso
veloce del centro piano resta invariato e i riflessi vengono aggiunti dopo il
darker. Il blur, il campionamento, lo storico e i timer r40 non cambiano.
Per il percorso Quickshell senza plugin,
`patches/glass-frost-reflections-qml.patch` elimina la stessa esclusione e collega
l’intensità enhanced a `sheen` (slider riflessi), prima fissata al 50%. Il valore
50% sui materiali trasparenti mantiene i coefficienti precedenti. QSB compilato
offline e installato insieme al sorgente.

`tests/glass-reflections-check.py` compila l’aritmetica estratta dai due shader
contro tipi scalari simulati, senza GL. Verifica 0/50/100%, satinatura 0/1,5/8/32,
centro invariato e corrispondenza native/fallback. Fallisce sulla r40 e passa
sulla r41. Superati anche loader, shader offline/media temporale, ciclo di
visibilità/cambio scena e parametri della barra. Build incrementale e link
riusciti; ABI, ELF e entry point verificati. Nessun rendering di prova.

Installata r41 per il prossimo login, con esclusione esplicita della sessione
corrente. Backup r40:
`~/.local/share/end4-pC/native-glass/before-frost-reflections-20261123-160724-226438`.
Shader precedenti:
`diagnostics/glass-reflections-r41-20261123/qml-before-install-20261123-160713/`.
Artefatti e hash: `diagnostics/glass-reflections-r41-20261123/manifest.json`.

Prova minima proposta dopo logout/login: dock con blur 1,5 px invariato su sfondo
scuro/intermedio; confrontare riflessi 0% e 100%. Deve cambiare la luce sul bordo,
con blur e darker stabili; ripristinare poi il valore preferito. La resa visiva
resta da confermare sul desktop: i controlli statici non la certificano.

## R42: valore iniziale sullo sfondo corrente

La r41 inizializzava i canali target dello storico a zero, benché il passaggio
esistente avesse già calcolato la luminosità corrente. La r42 usa questa misura
per entrambi i target iniziali. L’accumulatore resta a zero: gli aggiornamenti
successivi conservano finestre fisse di 1,5 secondi e raccordo di 800 ms.

Nel percorso nativo il piccolo passaggio temporale precede già la composizione
del materiale nel medesimo frame. Il materiale campiona la texture appena scritta,
senza readback, attese GPU, nuovi passaggi o invalidazioni globali. La ricomparsa
forza una nuova misura; un cambio di scena a superficie continuamente visibile
conserva invece il tono applicato, come nella r40. La r41 sui riflessi è invariata.

Nel fallback Quickshell, durante l’inizializzazione asincrona del singolo pixel
si usa il ramo di misura corrente già presente nello shader ottico. Un completamento
pendente appartenente alla vecchia visibilità non rende valido il vecchio storico.
Limite: senza una texture di sfondo ancora disponibile non si può conoscere il suo
contenuto prima del primo frame senza ritardare l’apertura. Non si aggiungono attese:
la misura corretta arriva appena la cattura esistente diventa disponibile.

Controlli senza rendering superati: aritmetica shader con casi iniziali e medie
ponderate, lifecycle e ricomparsa, cambi scena e timer, stato GL simulato con
verifica della texture scritta prima del composite, buffer, safety, riflessi e
loader. Il controllo del nuovo valore iniziale fallisce sulla r41. Build completa
sequenziale r42 riuscita; QSB offline, qmllint, ELF ed entry point verificati.
Nessun contesto GL, llvmpipe o compositor di prova avviato.

Patch aggiuntive: `patches/native-glass-initial-darkening.patch` e
`patches/glass-initial-darkening-qml.patch`. Manifest, hash e verifica installazione:
`diagnostics/glass-initial-darkening-r42-20261123/`.
Backup nativo: `~/.local/share/end4-pC/native-glass/before-initial-darkening-20261123-173442-816226`.
Backup QML: `diagnostics/glass-initial-darkening-r42-20261123/qml-before-install-20261123-173451/`.
Installazione permanente con esclusione della sessione corrente; nessun reload.

Prova minima dopo logout/login: aprire sidebar e popup della barra su uno sfondo
chiaro, quindi ripetere su uno scuro dopo un cambio workspace. Verificare il tono
fin dal primo frame e osservare oltre 2,5 secondi gli aggiornamenti successivi.
Verificare anche ricomparsa della dock, cambio workspace con dock sempre visibile
e riflessi sui bordi. Non occorre registrare. Risultato visivo non ancora confermato.

## R43: sidebar animate e sonde fuori schermo

L’utente conferma corretti i popup dopo r42, ma non le sidebar. Verificato in sola
lettura: HyprGlass r42 caricato. Le regole Hyprland usano `slide left/right` per le
sidebar; la cattura segue la posizione animata e azzera le aree fuori dal monitor.
Le quattro sonde della r42 continuavano invece a riferirsi al box completo: una
misura iniziale nel tratto fuori schermo poteva quindi fissare un falso zero.
Questa è una causa individuata nel codice; il risultato sul desktop resta da verificare.

La r43 passa al solo shader di luminosità l’intersezione tra geometria animata e
framebuffer del monitor. Le sonde vengono distribuite sulla parte visibile di
ciascun materiale. Un box interamente fuori schermo o non ancora registrato ha
un campione non valido, distinto dal nero reale, e si inizializza al primo campione
valido senza aspettare la pubblicazione successiva. Un reset di scena non riusa
uno storico non valido. I box interamente dentro lo schermo conservano esattamente
coordinate e misura precedenti, senza errori di confronto dovuti agli arrotondamenti.

Quando un box è tagliato dal bordo, le sole sonde usano la cattura chiara, evitando
che il blur includa il nero delle aree fuori schermo. La texture ottica e il blur
disegnati restano invariati. Non si aggiungono catture, texture, readback, timer,
invalidazioni globali o rendering continuo. Nel primo intervallo parziale di un box
comparso più tardi si estende all’indietro il suo primo campione valido; non si usa
uno storico di un altro box. Le scadenze fisse di 1,5 secondi e il fade di 800 ms
restano invariati. Nessuna modifica QML a sidebar, popup, barra o dock.

Esteso `tests/darker-temporal-check.py`: esegue il vero helper dello shader per
l’ingresso dai quattro bordi, assenza d’intersezione e coordinate interne identiche;
esegue anche l’aritmetica reale di inizializzazione dei singoli box, reset di scena
e completamento della finestra parziale. La r42 fallisce il nuovo controllo.
Superati shader offline, medie temporali, lifecycle, GL simulato, loader r43,
buffer, safety, chiusura, frost e riflessi. Build completa e successivo aggiornamento
dello shader riusciti, con compilazione sequenziale e limite di memoria di 512 MiB.
Verificati ELF, entry point, hash e applicazione inversa/diretta della patch.

Patch: `patches/native-glass-sidebar-initial-darkening.patch`, applicata dopo r42.
Artefatti: `diagnostics/sidebar-initial-darkening-r43-20261123/`.
Backup r42: `~/.local/share/end4-pC/native-glass/before-sidebar-initial-darkening-20261123-184254-215814`.
Installata per il prossimo login con esclusione della sessione corrente.

Prova minima descritta prima dell’installazione: aprire entrambe le sidebar su uno
sfondo chiaro, osservando il tono durante l’ingresso; chiuderle, cambiare workspace
con sfondo scuro e riaprirle. Attendere poi oltre 2,5 secondi per gli aggiornamenti
ordinari e verificare che i popup restino corretti. Nessuna prova grafica eseguita.

## R44: identità dei materiali e intensità automatica

Il timer nativo era già condiviso da tutti i materiali di una superficie. Lo
storico GPU era però associato alla posizione nella lista ordinata per area:
inserimenti, cambi di dimensione o riordinamenti potevano assegnare a un box
lo storico di un altro. Questo difetto nel codice è corretto; resta da verificare
se spiega interamente gli sfasamenti osservati sulla sidebar destra e nel meteo.
I materiali con sfondi diversi continuano correttamente ad avere target diversi.
Il colore sovrapposto alle card, per esempio il primary container al 72% della
card meteo, resta parte della loro resa e non viene eliminato per uniformarle.

Ogni WindowGlass riceve ora un ID stabile per la propria durata, conservato anche
tra unregister/register. Il protocollo geometrico 4 trasmette ID positivi e unici
per superficie, con limiti di parsing invariati. Durante il piccolo passaggio GPU
si rimappa lo storico precedente per ID, anche dopo riordino o resize; un materiale
nuovo riceve il marcatore non valido e usa l’inizializzazione fresca della r43.
Il composite a bande usa la stessa identità. Per i mittenti precedenti, senza ID,
si conserva il confronto geometrico. Scadenza, accumulatore e fade sono ancora
condivisi per superficie: non vengono creati clock o timer per singolo box.

La formula esistente usa il massimo di quattro sonde e la soglia 0,38, producendo
fino a circa 62% di nero sul bianco. L’automatismo sostituisce il valore manuale,
non lo somma; i materiali sovrapposti vengono composti con alpha, non oscurati
in cascata dalla medesima formula. Non sono stati verificati i pixel effettivi
del workspace corrente: l’estimatore resta basato su quattro punti, non sulla
copertura completa dello sfondo. Non si usa lo slider per correggere coordinate
di cattura o per nascondere il difetto di associazione dello storico.

Nuovo parametro `automaticDarkeningStrength`, 0–100%, default 100%, nei sei
JsonObject persistenti dei profili Glassy. Lo slider “Intensità dell’oscuramento
automatico” appare con l’automatismo abilitato. Il profilo Bar governa anche i
popup; Sidebar governa entrambe le sidebar. Reset e firma del profilo includono
il parametro. Il valore manuale resta salvato e indipendente.
La formula diventa `neroAutomatico * intensità`; quindi 100% conserva la resa,
50% dimezza il contributo, 0% elimina solo il contributo automatico. Restano
invariati soglia, frequenza, medie temporali e durata delle transizioni.

Il parser dei profili accetta una coda opzionale `strength`, con controlli di
finitezza, intervallo, duplicati, completezza e aggiornamento atomico. I messaggi
precedenti implicano intensità 100%. La capacità r44 negozia coda e protocollo 4;
con il plugin precedente Quickshell mantiene i messaggi precedenti e mostra che
serve un nuovo login per l’intensità nativa. Il parametro passa anche ai materiali
Quickshell e alla stima del contrasto del testo. Cambiare intensità usa il raccordo
di 800 ms esistente, senza resettare l’intervallo di luminosità. La chiusura conserva
anche l’intensità applicata, quando il profilo del proprietario non è più disponibile.

Restano due texture 33×1 per superficie. Si conserva sul lato CPU una lista di al
massimo 32 regioni e si invia una mappa di indici al passaggio già esistente: nessuna
nuova cattura, lettura GPU, allocazione GPU per frame o invalidazione globale.
Nessuna modifica alle animazioni di barra/dock, al percorso ottico o ai riflessi.

Controlli senza rendering: codice reale di rimappatura GL simulato con riordino,
resize e nuovo ID, stessa scadenza e nessuna allocazione aggiuntiva; shader reali
nativo/fallback per intensità 0/25/50/100%, soglia, nero/bianco e isolamento dal
manuale; parser di ID/intensità con input malformati e stato precedente conservato;
registrazione QML stabile e limite degli ID; valori predefiniti e clamp dei profili;
ricomparsa, timer, medie e fade; loader, buffer, safety, frost e riflessi. I nuovi
controlli di rimappatura/intensità falliscono sulla r43. Build nativa completa,
QSB offline, qmllint, ELF ed entry point verificati. Nessun contesto GL creato.

Patch: `patches/native-glass-darker-coherence.patch` e
`patches/glass-darker-coherence-qml.patch`. Artefatti, hash e verifiche:
`diagnostics/darker-coherence-r44-20261123/`.
Backup r43: `~/.local/share/end4-pC/native-glass/before-darker-coherence-20261123-200315-739879`.
Backup QML: `diagnostics/darker-coherence-r44-20261123/qml-before-install-20261123-200336/`.
Installata con esclusione della sessione corrente. Nessun riavvio di Quickshell,
caricamento/scaricamento del plugin, compositor di prova o registratore avviato.

Prova minima descritta prima dell’installazione: dopo logout/login aprire sidebar
destra e popup meteo sopra contenuto che cambia da chiaro a scuro, per almeno due
intervalli; confrontare poi intensità 100%/50%, controllando che cambino i livelli
ma non le scadenze. Verificare anche ricomparsa dopo cambio workspace e chiusura.
Risultato visivo e risoluzione completa degli sfasamenti restano da confermare.

## Pagina Glassy: modifica di più profili e slider alternativi

Su `feat/bar-app-overlap`, il pulsante “Modifica più profili” sostituisce la barra
delle tab con selettori indipendenti. La modalità singola mantiene le tab e il
profilo corrente; entrare/uscire dalla modalità multipla o cambiare selezione non
scrive configurazioni. La selezione è locale alla pagina, senza nuovi campi nella
configurazione persistente. Una selezione vuota nasconde la sezione dei controlli.

I controlli leggono il valore comune oppure mostrano “Misto”. Per le opzioni
booleane miste si mostrano scelte esplicite Sì/No, senza fingere uno stato spento.
Le scritture avvengono solo su interazioni dell’utente e per il solo parametro
modificato, verso i profili selezionati tramite il sistema di persistenza esistente.
Gli slider conservano il commit al rilascio; tastiera e rotellina usano `moved`.
Un trascinamento conserva selezione e ultimo valore effettivamente scelto, così
un ricalcolo del binding prima del rilascio non viene salvato come input dell’utente.
Pressione senza movimento, stato iniziale o cambio di selezione non uniformano valori.

Con automatismo attivo compare solo l’intensità automatica; con automatismo spento
compare solo il darker manuale. In modalità mista non compare nessuno dei due,
finché non si sceglie una modalità comune. Le colonne usano `visible`, quindi non
riservano spazio nel layout. Entrambi i valori salvati restano indipendenti.
Il blur usa il limite comune più restrittivo: 8 px se è selezionato Bar o Terminal,
altrimenti 16 px; la selezione non corregge o riduce automaticamente valori salvati.
Il reset agisce sui profili selezionati, usando per ciascuno i suoi valori predefiniti.

Riutilizzati pulsanti, ConfigSwitch, ConfigSelectionArray e StyledSlider esistenti.
Traduzioni italiane e descrizioni accessibili dei valori misti incluse. Nessuna
modifica al plugin, ai materiali, ai timer, alle ottimizzazioni o alle impostazioni
salvate dell’utente durante l’installazione della pagina.

Controllo riproducibile senza rendering:
`python3 tests/glassy-multiedit-check.py`. Esegue le funzioni reali della pagina
in Node e verifica stato misto, assenza di scritture alla selezione, isolamento
per parametro e profilo, slider alternativi, valori conservati, trascinamento,
tastiera, controlli disabilitati, selezione vuota, limiti blur e reset distinti.
Superati anche qmllint e controlli materiali/IPC del darker. Il vecchio contenuto
della pagina fallisce il nuovo controllo. Aggiornato il test QML grafico per i
nuovi comportamenti, ma non eseguito. Le fixture dei test materiali escludono
pagina e traduzioni dalle patch storiche: l’interfaccia ha ora il controllo CPU dedicato.

Pagina e traduzioni applicate dopo aver descritto la prova minima; nessun comando
di riavvio/caricamento del plugin o test grafico avviato. Backup e verifica:
`diagnostics/glassy-multiedit-20261123/`. Il manifest del plugin è rimasto invariato.
Prova grafica da fare: selezionare Bar+Dock con valori diversi, verificare “Misto”
e assenza di cambi automatici, cambiare un parametro, poi alternare oscuramento
manuale/automatico e verificare uno slider per volta e conservazione dei valori.
Infine verificare che in modalità automatica mista entrambi siano nascosti e che
uscendo dalla selezione multipla si ritorni alle tab singole. Resa visiva non verificata.

### Anteprima dei profili durante la modifica

Accanto alla modifica multipla, “Mostra elementi selezionati” mantiene visibili
barra, dock e sidebar dei profili selezionati. La selezione segue le tab singole
o multiple senza scrivere configurazioni né cambiare i normali flag di apertura.
L'anteprima termina disattivando il pulsante, lasciando la pagina, chiudendo le
Impostazioni o bloccando lo schermo. Una pagina precedente non può cancellare
l'anteprima appartenente a una nuova istanza.

Barra e dock passano temporaneamente sul livello overlay; la visibilità forzata
non aggiunge spazio riservato. Le sidebar in anteprima non intercettano input o
focus, per lasciare utilizzabili le Impostazioni. La preview usa i materiali reali:
non introduce catture, timer o rendering aggiuntivi indipendenti dai pannelli.
Le Impostazioni sono già aperte; per Terminal serve un terminale aperto. Il blocco
schermo non viene avviato e non può essere mostrato insieme alle Impostazioni.

Controllo CPU riproducibile: `python3 tests/glassy-preview-check.py`. Verifica
selezione dinamica, fine anteprima, proprietà dell'istanza, conservazione dello
stato normale, visibilità della dock, spazio della barra e input delle sidebar.
Le sorgenti precedenti falliscono il controllo. Superati anche multi-edit,
qmllint Qt 6 e controlli CPU di visibilità/materiali della barra.
Backup, candidata e impronte: `diagnostics/glassy-preview-20261123/`.
Applicati i file QML e le traduzioni; binario nativo invariato. Nessun riavvio
comandato, rendering o test grafico eseguito.

Prova grafica descritta prima dell'applicazione: attivare l'anteprima per barra,
dock e sidebar, cambiare un parametro e la selezione, quindi disattivarla o
lasciare la pagina. Verificare resa, accessibilità delle Impostazioni e ritorno
alla normale visibilità/autohide. Risultato visivo ancora da verificare.

### Scroll delle tab Glassy e righe vuote

La pagina Glassy disabilita la navigazione con rotella del SecondaryTabBar
mediante `wheelNavigationEnabled: false`; il valore predefinito rimane true
per tutte le altre pagine. Un MouseArea senza pulsanti accetta rotella e gesti
di scroll sopra le tab, anche nella selezione multipla, impedendone la
propagazione alla pagina. I clic e la navigazione da tastiera restano disponibili.

I riquadri vuoti erano i contenitori GroupedList dei selettori per valori misti:
nascondere il controllo non nascondeva lo sfondo con il relativo padding.
Le quattro righe alternative di abilitazione/automatic darker ora usano il
contratto `groupedListCollapsed` esistente. Rimane una riga per gruppo, con
switch per valori uniformi oppure scelta Sì/No per valori misti. Nessuna
modifica ai valori salvati o ai materiali.

Superati `tests/glassy-input-check.py`, multi-edit, preview e qmllint Qt 6;
il nuovo controllo fallisce sulle sorgenti precedenti. Backup e impronte in
`diagnostics/glassy-tabs-input-20261123/`. Modifiche applicate dopo aver
descritto la prova minima: mouse/trackpad sulle tab, clic, scroll fuori area,
assenza di righe vuote con valori uniformi e misti. Nessun rendering o
riavvio eseguito; propagazione reale degli eventi e resa visiva da verificare.

### Tab: scroll della pagina e sfondi opachi

Revisione successiva: rimosse le MouseArea che bloccavano lo scroll sopra le
tab singole e multiple. Il WheelHandler di navigazione resta disabilitato
solo per Glassy; anche il controllo nativo ha `wheelEnabled: false`, così
rotella e gesti possono raggiungere il normale scorrimento della pagina.
La selezione resta gestita da clic e tastiera. La modalità multipla torna
a un semplice Flow, eliminando il contenitore aggiunto per il blocco input.

Con Glassy globale e profilo Settings abilitati, gli sfondi dei selettori
usano i colori esistenti con alpha 1 tramite ColorUtils.applyAlpha.
Normale, selezionato e hover hanno colori distinti; disattivando Glassy
per Settings si ripristina la resa precedente. Nessuna modifica agli altri
materiali, alla persistenza, alla selezione multipla o all'anteprima.

Superati il controllo CPU aggiornato `tests/glassy-input-check.py`,
multi-edit, preview e qmllint Qt 6. Il controllo verifica anche gli stati
dei colori e l'attivazione condizionata, e fallisce sulle sorgenti precedenti.
Backup e impronte: `diagnostics/glassy-tabs-scroll-style-20261123/`.
Prova minima descritta prima dell'applicazione: scroll sopra le tab in
entrambe le modalità, profilo invariato, clic e colori normale/hover/selezionato.
File applicati, nessun rendering o riavvio eseguito; verifica grafica pendente.

### Correzione del materiale delle tab: satinatura HyprGlass

Chiarimento dell'utente: per box opaco intende il materiale satinato nativo,
non una tinta piena. Rimosso l'alpha forzato a 1. Ogni selettore, singolo o
multiplo, ora possiede un WindowGlass collegato al suo background, con frost
come nei GroupedList delle Impostazioni e nativeClip sulla pagina per evitare
che la satinatura esca dal viewport durante lo scroll. Il materiale si abilita
con profilo Settings attivo, enhancedActive e frostedAvailable; trackGeometry
rimane false come per le righe satinate. Una tinta leggera conserva gli stati
di selezione/hover senza coprire il materiale; percorso non satinato invariato.

Controlli CPU input/materiali, multi-edit, preview e qmllint Qt 6 superati.
Backup e impronte in `diagnostics/glassy-tabs-satin-20261123/`.
Prova minima descritta prima dell'applicazione: confronto con un box satinato
delle Impostazioni, tab singole/multiple e scroll. File applicati, nessun
riavvio o rendering avviato; resa visiva non confermata.

### r45 — darker indipendente per le tre sezioni della barra (24 novembre)

La barra orizzontale con HyprGlass r45 campiona le sezioni sinistra/centro/destra
con 2/3/2 punti, lungo la mediana verticale. Le posizioni orizzontali sono
25%/75% per i lati e 1/6, 1/2, 5/6 per il centro. La media aritmetica locale
sostituisce il massimo dei quattro punti del precedente riferimento comune.
Restano invariati formula, intensità, finestre fisse di 1500 ms, inizializzazione
e transizioni di 800 ms. La modifica riguarda il percorso nativo della barra;
dock, popup, sidebar e fallback Quickshell conservano il campionamento precedente.

BarContent identifica esplicitamente le sezioni; WindowGlass ne eredita identità
e geometria senza campionare separatamente i widget annidati. Il carrier del
layout center-only rimanda allo stesso riferimento del contenuto centrale.
Il protocollo v5 aggiunge gruppo e rettangolo di riferimento per materiale,
validati atomicamente, solo con la capacità r45. Un plugin precedente continua
a ricevere v4. Il renderer riduce i materiali a tre righe temporali con identità
interne stabili: ricreazione, ordinamento e ridimensionamento dei widget non
scambiano lo storico delle sezioni. Sezioni assenti non aggiungono campioni.
Il fondo/corner senza gruppo riusa la media delle sezioni presenti senza nuove
letture; i client privi di metadati conservano il riferimento legacy della barra.
I sette punti sono condivisi dai materiali: non vengono ripetuti per widget.
Restano i buffer temporali esistenti, senza nuove letture sincrone dalla GPU,
timer di rendering o invalidazioni globali.

Controlli senza GPU: `tests/bar-section-darkening-check.py` esegue il ramo GLSL
della media come C++, verifica punti/medie, parser v4/v5 e rifiuto atomico,
riduzione dei gruppi, eredità QML e serializzazione reale di sendRegions in Node.
Il controllo dello stato GL simulato verifica anche il riordino/ridimensionamento
delle tre identità negative e il fallback del materiale senza gruppo. Superati
inoltre buffer, sicurezza, fade, temporalità, ricomparsa, profili, riflessi,
visibilità, loader, multi-edit, anteprima, input Glassy e qmllint Qt 6.
Shader verificati offline, senza contesto GL. La build sequenziale usa nice 15
e limite di memoria 512 MiB; artefatto e ABI verificati. Build.sh applica la nuova
patch e usa le sorgenti QML correnti per i test, senza riprodurre patch storiche
su file modificati successivamente.

Artefatto, sorgenti, log di compilazione, manifest e backup sono in
`diagnostics/bar-section-darkening-r45-20261124/`; patch riproducibili:
`patches/native-glass-bar-sections.patch` e `patches/glass-bar-sections-qml.patch`.
File applicati e r45 installata atomicamente con `deferInstance` per escludere
la sessione attuale. Backup del plugin precedente in `installed-before-r45/`.
Nessun caricamento/scaricamento del plugin, riavvio o test grafico eseguito.

Prova minima descritta prima dell'installazione: dopo il prossimo accesso,
porre sfondi chiari/scuri dietro sezioni diverse e attendere almeno un intervallo
completo, verificando adattamento locale; controllare cambio workspace e
ridimensionamento dei gruppi. Risultato visivo ancora da confermare.

### r46 — continuità del fade e autohide (24 novembre)

Riprodotto senza GPU un salto nel ramo GLSL usato dopo più intervalli senza
campionamento: destinazione e origine venivano entrambe impostate a prior.a,
annullando il fade anche quando il valore disegnato precedente era diverso.
La pubblicazione ora conserva come origine la miscela effettivamente disegnata,
anche per una transizione interrotta. Il renderer memorizza il fattore dopo il
disegno e lo usa anche per i reset della scena, anziché stimarlo dal solo tempo
trascorso. Il fallback QML passa il proprio fattore e sospende il vecchio fade
mentre viene pubblicata la nuova texture. L'inizializzazione di un materiale
nuovo o realmente riapparso rimane immediata sullo sfondo corrente.

Il timer esistente pubblicava a intervalli di 1,5 s; i frame intermedi del fade
dipendevano dal damage richiesto durante il rendering. Ora lo stesso timer
richiede damage del solo materiale anche durante gli 800 ms, fino a 60 Hz,
includendo il frame finale se la callback arriva dopo la scadenza. Rimosse le
richieste del fade dal corpo del disegno. Il timer non si riarma senza rendering,
si ferma al termine o quando l'elemento è nascosto e non marca la scena come
cambiata: nessuna invalidazione globale o ciclo di rendering permanente.

Inoltre i flag automaticDarkeningVisible di barra/dock diventavano falsi già
all'inizio della chiusura. Invertirla mentre il pannello era ancora visibile
poteva quindi attivare una nuova inizializzazione istantanea. I flag includono
ora le animazioni di autohide in corso, mantenendo lo storico durante la loro
inversione. Le vere ricomparse conservano la misura iniziale fresca della r43.

Il controllo `tests/darker-fade-continuity-check.py` esegue il ramo GLSL reale
come C++ per entrambi i versi, pause lunghe, fade interrotto, comparsa e reset;
verifica anche i flag autohide in Node. La r45 fallisce il caso della pausa lunga.
Il controllo lifecycle con clock simulato verifica tutti i tick, il frame finale
ritardato, l'arresto e il mantenimento dei termini di pubblicazione; i suoi casi
preesistenti isolano la pubblicazione simulando fade già terminati. Il controllo
dello stato GL verifica la ripresa dal fattore dell'ultimo disegno e conserva
copertura di slot, ID stabili, ripristino, errori e numero limitato di buffer.
Superati anche temporalità, inizializzazione/ricomparsa, campionamento 2/3/2,
negoziazione/deferral del loader, qmllint e shader/QSB offline. Nessun rendering.
I file DarkeningWindow.hpp e i tempi PERIOD/FADE sono invariati rispetto alla r45.

Il blocco riferito durante il lavoro ha interrotto la prima compilazione su
GlassLayerSurface.cpp: la r46 non era stata installata o caricata. Questo log
non stabilisce la causa del blocco. La compilazione è stata ripresa con quota
CPU 25%, MemoryMax 600 MiB e limite AS del compilatore 512 MiB, verificando
cpu.max e memory.max del cgroup; completata con successo. Nessun clock/driver
modificato, nessun compositor, registratore o contesto GL avviato.

Artefatto, sorgenti, log, profilo risorse e backup:
`diagnostics/darker-fade-continuity-r46-20261124/`.
Patch native e QML/QSB riprodotte e verificate. File applicati e plugin
installato atomicamente per il prossimo accesso, con esclusione della sessione
attuale e backup `installed-before-r46/`. Nessun caricamento/scaricamento o
riavvio eseguito. Prova minima descritta prima dell'installazione: sfondi chiari
e scuri sotto barra/dock, ripetizione dopo una pausa e inversione dell'autohide;
controllare il fade in entrambi i versi. Resa visiva ancora da confermare.
