# Sfondo incompleto e sfarfallio delle Impostazioni

Esito della prova reale: l'utente riferisce ancora sfarfallio dopo il debounce
attivato alle 12:42 CET. La modifica non è confermata come soluzione.
Nessun rendering, nemmeno llvmpipe, eseguito in questa indagine. Nessuna modifica
ai file QML/QSB caricati dalla sessione. HyprGlass assente dalla plugin list;
registratore inactive/disabled.

## Sfondo: causa individuata

`WindowGlass.qml` ricostruisce il backdrop con un'Image del file wallpaper e
ScreencopyView dei `ToplevelManager.toplevels`. `windowVisible()` esclude le
finestre dello stesso processo e filtra workspace/visibilità. Il modello
contiene finestre applicative; non i layer-shell del desktop.

L'orologio viene creato da `modules/ii/background/WidgetsLoader.qml`, dentro
il PanelWindow `quickshell:background` di `Background.qml`, sul layer Bottom.
Il vetro non include questo albero né il pannello composito. Anche il wallpaper
ricostruito può differire dal desktop reale per video, collage o transizioni.

Il commit `53d3f4d7` del 7 novembre presenta già Image + ToplevelManager e
l'esclusione dello stesso processo: il limite precede le patch del 16 novembre.
Non rimuovere l'esclusione del processo: non rende esportabile il layer desktop
e può introdurre catture delle proprie finestre/feedback.

Una cattura dell'intero schermo comprende anche Impostazioni e non è una
sorgente sicura da reinserire nel suo vetro. Anche un riferimento diretto a
`bgRoot.contentItem` tramite ShaderEffectSource non è una correzione valida:
il desktop e Impostazioni hanno finestre Qt distinte. Qt richiede che sorgente
e ShaderEffectSource appartengano alla stessa finestra:
https://raw.githubusercontent.com/qt/qtdeclarative/v6.11.1/src/quick/items/qquickshadereffectsource.cpp

Per la composizione completa occorre progettare una sorgente del desktop che
possa essere condivisa fra finestre o un'esportazione composita prima del layer
Impostazioni. Il backend nativo è un percorso da rivalutare in seguito, ma resta
disattivato. Non duplicare il widget tree in ogni materiale: aggiungerebbe costo,
possibili divergenze e cicli nei widget che usano a loro volta il vetro.

## Darker: riscontri e incertezza

- I 12 file sorgente/QSB installati corrispondono agli hash del manifest di
  attivazione. Il log contiene `Configuration Loaded` alle 12:42:36.
- La configurazione salvata è `source: windows`, stile default, profilo
  Impostazioni con oscuramento automatico attivo. `WindowGlass` collega il
  debounce a `profileKey === "settings"`, quindi anche ai materiali interni
  che passano per quel componente, inclusa la navigation rail.
- Non è stata trovata un'altra formula del darker nel percorso Qt esaminato:
  il fragment shader applica la curva al valore fornito dal vertex. Colore
  dello sfondo, rifrazione e satinatura continuano invece a cambiare durante
  il movimento, anche se la luminanza di riferimento fosse davvero congelata.
- Lo stato IPC letto riportava `contentReady: false`, nessuna prova con
  Impostazioni visibili è stata avviata. `windows: false` in quello stato non
  dimostra un cambio della sorgente configurata o una regressione della cattura.
- L'IPC corrente non espone timer, stato del Loader, seriali di campionamento
  o flag live delle texture. Non consente quindi di verificare a runtime che
  il debounce sia attivo durante il trascinamento.
- I controlli statici precedenti simulano le callback, non la gestione delle
  texture da parte di Qt. Non dimostrano il congelamento dei pixel. Il codice
  Qt distingue `live`, richieste esplicite e dirty state; il segnale di
  completamento può arrivare anche senza un nuovo grab. Non è stato provato
  che questo spieghi il difetto specifico:
  https://raw.githubusercontent.com/qt/qtdeclarative/v6.11.1/src/quick/scenegraph/qsgrhilayer.cpp

## Prossimo passo preparato, non applicato

Aggiornamento successivo: l'utente ha autorizzato l'introduzione dell'aggiornamento
e la reintroduzione del plugin. La diagnostica sotto è stata applicata e la
risposta IPC verificata (`darker: null` con Impostazioni chiuso). HyprGlass r34
è ripristinato su disco con caricamento rinviato alla prossima sessione;
plugin list ancora vuota, registratore disattivato. Vedere `native-glass.md`.

`patches/settings-darker-observation.patch` estende la sola risposta IPC
`settings glassStatus` con profilo, attivazione automatica/debounce, rettangolo
campionato e stato del materiale: seriali di movimento/campione, busy, attesa,
transizione, blend e flag live delle due texture. Restituisce null se il materiale
non è caricato. Sono getter su richiesta: niente timer, log per frame,
acquisizioni, letture GPU o modifiche agli shader.

Controllo: `node tests/settings-darker-observation-check.js` passa su copie
temporanee, verifica assenza di effetti collaterali e parsing QML. Non dimostra
correttezza visiva né sicurezza/stabilità hardware.

Prima di attivare questa diagnostica occorre descrivere il reload della shell
e la prova minima: un trascinamento breve nella sessione esistente, letture dello
stato durante il movimento e dopo 1.5 secondi di quiete. Se waiting non resta
attivo o targetLive resta true durante il movimento, correggere prima quel
percorso. Se lo stato risulta congelato, distinguere il darker dagli altri
effetti del materiale prima di cambiare nuovamente algoritmo.
