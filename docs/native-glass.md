# Glassy UI: sfondo live in Hyprland

Con `Glassy UI`, `True Glassy` e `Glass source → Windows underneath` attivi, il backend nativo
campiona il framebuffer del compositor a ogni frame disegnato. Segue quindi
contenuto animato, spostamenti e transizioni tra workspace, senza ricostruire lo
sfondo dalle singole finestre esportate a Quickshell.

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

## Compilazione e verifica

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

Con Glassy UI, True Glassy e Windows underneath selezionati, Quickshell verifica
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
