# Darker: debounce del movimento

Stato: applicata il 16 novembre 2026 alle 12:42 CET dopo autorizzazione
dell'utente alla prova nella sessione esistente. Quickshell ha registrato
`Configuration Loaded`; riscontro visivo ancora da raccogliere. La precedente
patch sulle catture non aveva eliminato lo sfarfallio.

Aggiornamento: l'utente riferisce sfarfallio persistente anche con questa patch
e l'assenza dell'orologio desktop nel vetro. La causa dello sfondo incompleto è
preesistente; il congelamento del darker resta da verificare a runtime. Vedere
`../docs/settings-glass-investigation-2026-11-16.md`. Nessuna soluzione confermata.

Backup persistente dei file precedenti e manifest:
`~/.local/state/end4-pC/diagnostics/20261116-darker-debounce-activation/`.

La luminanza automatica attuale viene ricalcolata con quattro campioni nei
vertex shader. Muovere il materiale cambia i punti dello sfondo campionati,
senza un filtro temporale. È una fonte plausibile di variazioni rapide;
non prova da sola la causa esclusiva dello sfarfallio osservato.

La candidata aggiunge il debounce ai materiali del profilo Impostazioni nel
fallback Qt, inclusi quelli interni. Durante spostamenti o variazioni della
geometria campionata conserva la luminanza mostrata. Ogni cambiamento riavvia
un timer singolo di 1500 ms. Alla scadenza conserva il valore attuale, acquisisce
il nuovo e avvia una transizione di 800 ms. Un nuovo movimento interrompe
la transizione al valore raggiunto; le callback di richieste ormai superate
non avviano una nuova transizione. A riposo, dopo la transizione, i contenuti
dello sfondo continuano ad aggiornare l'automatismo come prima.

Due piccole texture, richieste da 1×1 pixel, conservano le luminanze. Lo sfondo
ottico resta live; non vengono congelati rifrazione o satinatura. Nessun
readback verso la CPU, FrameAnimation o timer periodico. La ricorsione della
texture precedente usa `live: false`, evitando un ciclo continuo di ridisegno.
Il backend nativo e la precedente ottimizzazione delle catture restano invariati.

La curva del darker e tutto il codice ottico del fragment shader sono preservati.
I quattro campioni restano nei vertex shader: nei materiali non interessati il
percorso è identico; nel percorso debounced il shader di misura li esegue per
una piccola texture e il vertex principale miscela le due luminanze conservate.
Questo aggiunge risorse/passaggi piccoli, quindi non è un'ottimizzazione a costo
zero: prestazioni e stabilità hardware non sono state validate.

```sh
python3 tests/settings-darker-debounce-check.py
```

Il controllo attuale non esegue rendering: verifica sintassi, compilazione,
invarianti ottiche, debounce, interruzioni e callback tardive su copie temporanee.
Il precedente test llvmpipe non è valido come prova finale: dava PASS sui pixel
ma terminava con crash ed è temporalmente vicino al blocco completo del PC.
È stato ritirato; vedere `../docs/black-screen-investigation-2026-11-16.md`.

Non applicare la sola patch senza preparare anche i cinque QSB corrispondenti.
La prova autorizzata usa la sessione esistente: trascinare Impostazioni,
fermarsi 1500 ms e osservare la transizione; riprendere il movimento durante
la transizione per verificare congelamento e nuova attesa. Non è stato avviato
un programma di rendering separato. HyprGlass e registratore restano disattivati.
