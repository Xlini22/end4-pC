# Impostazioni: catture stabili durante il trascinamento

Stato: patch applicata ai QML il 16 novembre 2026 dopo autorizzazione
dell'utente. Controlli senza GPU superati; riscontro visivo ancora da raccogliere.

Nel fallback Qt, `WindowGlass.qml` imposta `captureSource` a `null` quando una
finestra non interseca il pannello. Quickshell cancella allora l'immagine; al
successivo incrocio, il primo fotogramma non è necessariamente disponibile.
Questo può mostrare temporaneamente il wallpaper e alterare il darker.
Riferimento: https://quickshell.org/docs/v0.3.2/types/Quickshell.Wayland/ScreencopyView/

La patch mantiene le catture delle finestre ammissibili sul monitor per il solo
pannello principale delle Impostazioni negli stili default/minimal. Spostare
il pannello non cambia più le sorgenti. Restano i filtri su workspace,
visibilità, monitor ed esclusione dello stesso processo. Il Loader distrugge
le catture quando il materiale non è più attivo. Gli altri materiali e lo
stile dashboard mantengono il comportamento precedente.

Shader, rifrazione, satinatura, profili e formula del darker non cambiano.
Il costo possibile è un maggior numero di catture simultanee quando le
Impostazioni sono aperte: anche finestre sul monitor fuori dal pannello.
Non sono state misurate prestazioni sulla GPU.

Verifica senza rendering:

```sh
node tests/settings-backdrop-stability-check.js
```

Il test applica la patch a copie temporanee, riproduce il cambio della sorgente
nel binding originale, verifica la stabilità del binding corretto durante
andata/ritorno, controlla filtri e offset monitor e analizza i QML con Qt 6.
Non avvia Quickshell, compositor, catture o contesti grafici.

La verifica non dimostra ancora che questo spieghi tutto lo sfarfallio riferito.
I quattro campioni del darker continuano a spostarsi sullo sfondo: variazioni
reali della luminanza possono ancora modificare l'oscuramento. La patch elimina
lo sgancio delle catture, senza mascherare queste variazioni.

Prova visiva minima, da concordare prima dell'attivazione: nella sessione
esistente, aprire Impostazioni e trascinare una volta avanti/indietro sul bordo
di una finestra già aperta, per circa cinque secondi. Nessun riavvio di
Hyprland, plugin nativo o registratore. Applicare la patch ai file caricati
può innescare il reload automatico di Quickshell, normalmente abilitato:
https://quickshell.org/docs/v0.3.2/types/Quickshell/Quickshell/#prop.watchFiles

Per applicarla su una copia dello stato precedente (è già applicata qui):

```sh
git apply --check patches/settings-backdrop-stability.patch
git apply patches/settings-backdrop-stability.patch
```

Per annullare questa sola modifica dopo l'applicazione, prima di ulteriori
modifiche ai medesimi punti:

```sh
git apply --reverse --check patches/settings-backdrop-stability.patch
git apply --reverse patches/settings-backdrop-stability.patch
```
