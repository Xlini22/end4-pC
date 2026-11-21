# Confronto con origin/main — 18 novembre 2026

Su richiesta dell'utente, caricato il main della repository
`https://github.com/Xlini22/end4-pC.git` in un worktree separato:
`~/.config/quickshell/end4-pC-main`, branch `main`.

Commit locale, origin/main locale e main pubblicato coincidono:
`8135351525a916778bc3ead276a85095c6c1e59b`. Nessun aggiornamento remoto da
applicare, merge upstream, reset o modifica del checkout sperimentale.
Il worktree main risulta pulito dopo l'avvio.

Alle 15:38 caricata la shell `end4-pC-main`, istanza `vwo6gncpot`, PID 312223,
dopo la chiusura della sola istanza `ii` precedente. Nessun riavvio del
compositor. Un primo controllo dell'elenco istanze dopo la chiusura riceveva
output vuoto invece di JSON: ripreso il cambio gestendo esplicitamente tale
caso, senza ripetere la chiusura o lanciare più shell. Main avviato una volta.

Durante quella prova `~/.config/hypr/custom/variables.lua` selezionava
`end4-pC-main`; ricaricata
la configurazione Hyprland. Lista plugin vuota prima e dopo il cambio.
Il binario HyprGlass ordinario resta disabilitato come nel confronto con ii.
Main non contiene il loader nativo sperimentale né GlassCompositor.qml.

La selezione è stata poi riportata a ii e successivamente a end4-pC su richiesta
dell'utente. Al 21 novembre il checkout main resta separato e invariato;
la configurazione sperimentale è sul branch `test/upstream-20261108`.

Backup privato delle impostazioni condivise, variabili e override:
`~/.local/state/end4-pC/shell-switches/main-20261118-153650/`.
Nella stessa directory: `events.jsonl` e `main-launch.log`. Il contenuto delle
impostazioni private non è copiato in questo repository. Il controllo iniziale
del log non trova errori di caricamento/binding nei filtri usati; non è una
validazione di stabilità o assenza di difetti visivi.

Il confronto cambia il codice della shell, mantenendo l'installazione attuale
di Quickshell, Hyprland, kernel e driver e usando la configurazione utente
condivisa `~/.config/illogical-impulse/config.json`. Non è un ambiente completamente
pulito né una prova che il main risolva i blocchi. Nessun benchmark o tentativo
di provocare una schermata nera eseguito.
