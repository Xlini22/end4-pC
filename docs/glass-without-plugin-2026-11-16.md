# Vetro Quickshell senza HyprGlass: fattibilità e proposta

Analisi statica del 16 novembre 2026. Nessuna modifica ai QML, shader/QSB,
configurazione Hyprland o sessione. Plugin list `[]`, binario operativo assente,
registratore inactive/disabled. Nessun rendering, compreso llvmpipe.

## Risultato

Qualità della satinatura, tinta, oscuramento e coerenza del movimento sono
migliorabili nel percorso Qt. Non è possibile promettere la stessa scena
completa del plugin utilizzando soltanto l'attuale ricostruzione da wallpaper
e finestre applicative. Il supporto del compositor non implica necessariamente
un plugin: il blur incorporato è un'alternativa per la satinatura, ma non
esporta a QML la texture completa su cui calcolare la rifrazione.

| Richiesta | Percorso possibile | Limite |
| --- | --- | --- |
| Schede satinate senza trama grossolana | Sorgente Qt condivisa e prefiltro per il profilo Impostazioni | Resa e costo da verificare visivamente; non ancora implementato. |
| Movimento solidale di contenitore e contenuti | Mantenere il loro unico albero Qt e la geometria locale | Le catture delle altre finestre hanno tempi indipendenti. |
| Wallpaper coerente con parallax/transizioni | Riutilizzare gli stessi dati e trasformazioni in una rappresentazione nella finestra Impostazioni | Non equivale a catturare il desktop composito. |
| Orologio visibile nel vetro Qt | Vista aggiuntiva del solo contenuto, con stato/rotazione/trasformazioni condivisi | Ricostruzione, non cattura del layer; un secondo ClockWidget indipendente divergerebbe. |
| Tutti i layer e transizione workspace esatti | Composizione/blur incorporato di Hyprland oppure una vera esportazione del backdrop dal compositor | Il blur incorporato non produce da solo rifrazione Glassy e non restituisce quella texture al QML. |

## Sfondo: che cosa manca e perché

`modules/common/widgets/WindowGlass.qml` crea una `Image` del wallpaper e un
`ScreencopyView` per ogni finestra applicativa ammessa. `windowVisible()` esclude
lo stesso PID, finestre non mappate/nascoste e workspace non attivi, salvo pinned
e special workspace. `windowOrder()` approssima lo stacking con tipo di finestra
e cronologia del focus: non riceve l'ordine di composizione esatto.

Non entrano nel backdrop:

- i layer-shell del desktop e di altre shell, comprese le superfici Quickshell;
- bordi, ombre e geometrie applicati dal compositor alle finestre esportate;
- animazioni di posizionamento e trasformazione workspace del compositor;
- la composizione reale del wallpaper con parallax, video, collage, dimming,
  work safety e transizioni: qui è caricata soltanto un'immagine/thumbnail.

L'orologio cookie corrente passa da `WidgetsLoader.qml` a `WindowedClock.qml`.
Quest'ultimo può spostarlo in un piccolo `PanelWindow` Bottom separato,
`end4-background-clock`, per localizzare il danno. In altre condizioni rimane
nell'albero di `quickshell:background`. Nessuna delle due superfici appartiene
ai toplevel applicativi catturati. La sua assenza non è risolvibile togliendo
il filtro sul PID.

La [API ScreencopyView](https://quickshell.org/docs/v0.2.1/types/Quickshell.Wayland/ScreencopyView/)
accetta monitor e toplevel, non un layer-shell arbitrario. Il
[protocollo toplevel export](https://github.com/hyprwm/hyprland-protocols/blob/main/protocols/hyprland-toplevel-export-v1.xml)
esporta le superfici applicative senza decorazioni e geometrie del compositor.

`ShaderEffectSource` non consente di prendere direttamente l'Item dell'orologio
o del desktop da un'altra QQuickWindow: il
[codice Qt](https://github.com/qt/qtdeclarative/blob/v6.11.1/src/quick/items/qquickshadereffectsource.cpp#L255)
rifiuta questa configurazione. Una cattura dello schermo include le Impostazioni
stesse; il QML attuale non dispone di un'esclusione del proprio layer e non va
usata come texture del vetro, per evitare feedback. Non proporre hide/capture/show
periodici del pannello.

## Schede e pixelatura: riscontri distinti dalle ipotesi

Configurazione salvata osservata: stile default, glass enabled/enhanced,
source windows, haze globale 1, profilo settings blur 8 e darker automatico.

**Differenza certa:** `DashboardCard.qml` abilita `cardGlass` soltanto con
`GlassCompositor.windowFrostedAvailable`. Senza plugin quel flag è false.
Se non riceve un altro `blurSource`, la scheda mostra il colore `glassDimmed`
semitrasparente; non esegue il proprio filtro frost. Il riquadro Glassy della
pagina Interface e le schede derivate vanno verificati singolarmente prima di
estendere la correzione. La navigation rail usa invece `WindowGlass` anche nel
fallback: non tutti i box percorrono lo stesso ramo.

Lo sfondo principale, con frost 0, usa haze globale 1 nella configurazione
osservata; una tinta semitrasparente su quello sfondo lascia visibili dettagli
che il filtro satinato del plugin attenuava. È una spiegazione plausibile della
percezione di pixel/trama, non una diagnosi visiva conclusiva.

**Seconda differenza certa:** `liquidLens.frag` usa mipmap con
`lod = log2(max(haze, 1))` e un campione centrale più sei campioni circolari.
Non è lo stesso filtro separabile del plugin. Se questo filtro produce una
trama, cambiare la sola opacità non la corregge. Il suo contributo al difetto
osservato resta da verificare.

Non è stato trovato rumore casuale/dithering intenzionale in liquidLens.
`ShaderEffectSource` ottico è live e usa mipmap; solo i due valori di luminanza
del debounce sono texture da un pixel. Non confondere queste con il backdrop.
`smooth` è già true per default in Qt; aggiungerlo non è una soluzione provata.
Il wallpaper viene decodificato alla risoluzione dello schermo corretta per DPR.
Non introdurre supersampling globale, RGBA16F o formati già problematici come
tentativo generico di eliminare la pixelatura.

## Workspace e movimento

`WindowGlass` decide l'inclusione sul workspace attivo, posiziona le catture con
`client.at`/`client.size` e non applica gli offset animati dei workspace.
`GlassLayers.qml` aggiorna i client a 10 Hz; `HyprlandData` aggiunge un debounce
eventi di 60 ms. Questi dati descrivono lo stato delle finestre, non una sequenza
sincronizzata di trasformazioni del compositor. Aumentare il polling non
fornisce l'informazione mancante e aggiunge carico.

Il desktop ha inoltre un parallax Qt animato per 600 ms, assente dall'Image del
backdrop. Sono due disallineamenti distinti: wallpaper Qt e finestre animate da
Hyprland. Il primo è riproducibile condividendo gli stessi dati/trasformazioni;
il secondo richiede dati/esportazione del compositor per una corrispondenza
esatta durante tutta la transizione.

La finestra Impostazioni default è un layer fullscreen con un Rectangle mobile
e contenuti suoi figli. Il fallback deve mantenere questo albero: nessun
trasferimento dei controlli in altre finestre, ritardo sulle loro coordinate,
ricostruzione delle loro posizioni via IPC o nuovo debounce sul movimento.
`stableBackdropCapture: true` mantiene le catture delle finestre vicine al
pannello durante il drag. Il debounce di 1,5 secondi deve restare confinato al
calcolo del darker; sorgente ottica e geometria restano live.

## Correzione proposta prima di implementare

Prima fase solo per le Impostazioni, senza toccare il compositor:

1. Esporre ai materiali della stessa finestra la sorgente backdrop già creata
   dal pannello. Una serie di stream delle finestre per pannello, non una serie
   per ogni scheda. Condividere la sorgente non significa necessariamente
   catturare l'intero monitor in una nuova texture per ciascun materiale.
2. Preparare un prefiltro satinato condiviso per il profilo settings e usare
   quel risultato soltanto nei materiali frost. Valutare prima
   `QtQuick.Effects.MultiEffect`, già installato, senza una nuova dipendenza.
   Rifrazione/bordi mantengono la sorgente nitida; tinta e darker mantengono
   il loro ruolo. Il filtro e la luminanza devono riferirsi allo stesso
   materiale. Nessuna promessa che il filtro standard sia identico a quello
   nativo o più veloce prima della verifica sul portatile.
3. Collegare le schede a questa sorgente, eliminando il vincolo sulla capability
   nativa solo dopo che è disponibile il percorso Qt condiviso. Togliere oggi
   il vincolo da solo moltiplicherebbe i backdrop/stream per scheda.
4. Preservare crop, culling, lifecycle e catture stabili già presenti; nessun
   cambio alle animazioni del contenitore o dei figli.

Seconda fase: allineare la rappresentazione del wallpaper ai dati/parallax reali.
Una vista aggiuntiva dell'orologio è un'opzione limitata, da valutare solo se
può riusare lo stato animato esistente senza duplicare controller, interazione
e timer. Non ricreare l'intero widget tree in ogni materiale e non disattivare
l'ottimizzazione del piccolo layer orologio per aggirare il problema.

Alternativa per il vero sfondo: il blur **incorporato** di Hyprland, senza
HyprGlass. È attualmente spento, verificato con `getoption
decoration:blur:enabled`; lo spegne `hyprland/shellOverrides/main.lua`.
Le regole esistenti includono anche xray e ignore_alpha: non basta accendere il
flag globale. Richiederebbe una proposta separata con maschera alpha adeguata
e valutazione delle altre superfici coinvolte. Può mostrare il vero sfondo
attraverso materiali trasparenti/satinati, ma non sostituisce la rifrazione
personalizzata. L'attuale shader emette alpha piena dentro il materiale,
quindi il blur sottostante non lo attraverserebbe automaticamente.
Non è una modifica applicata né un equivalente completo promesso.

## Verifica minima proposta, non avviata

Solo dopo una candidata controllata staticamente, primo cambiamento limitato
alla satinatura condivisa delle Impostazioni. Nella sessione esistente,
senza plugin/recorder e senza fixture grafica separata:

1. Aprire una pagina con poche schede, con una finestra contenente testo dietro.
2. Confrontare per pochi secondi resa delle schede e della rail; un solo breve
   trascinamento per verificare che contenitore, testi e controlli restino solidali.
3. Fermarsi per almeno 1,5 secondi e controllare il darker, senza congelare il
   backdrop. Chiudere Impostazioni.

Questa prima prova non validerebbe clock o transizioni workspace: avrebbero
una verifica separata solo dopo una soluzione specifica. Nessuna nuova prova
di carico prolungata; nessun FPS o miglioramento visivo dichiarato senza misura.

Controllo CPU eseguito: `node --max-old-space-size=128
tests/settings-backdrop-stability-check.js`, su copie temporanee, passato.
Verifica le condizioni reali di inclusione, assenza di detach durante il drag,
filtri e parsing QML. Il primo lancio sandbox non poteva avviare `git`; la
ripetizione con accesso ai sottoprocessi è passata. Nessun rendering eseguito.
Non è una validazione degli effetti o della fluidità.
