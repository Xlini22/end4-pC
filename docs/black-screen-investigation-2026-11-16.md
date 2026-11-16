# Blocco durante i test del darker — 16 novembre 2026

L'utente riferisce schermo nero e blocco completo senza aver mosso il portatile.
Questo episodio non richiede un movimento della cerniera come innesco; non
dimostra da solo la causa software né esclude guasti hardware o firmware.

Avvio precedente: `a158fd45c0df458588feb2b85acbca88`.
Nuovo avvio: `9646c69bc53b4641a76cac911c526cf7`, ore 12:10:16 CET.

## Riscontri

- Fra 12:03:42 e 12:07:14 si registrano cinque crash di
  `python3 [ -X faulthandler ] tests/settings-darker-debounce-check.py`.
  Il test usava Qt RenderControl offscreen e il renderer CPU llvmpipe,
  verificato nel processo. I confronti pixel arrivavano al PASS, ma il
  processo non terminava correttamente: non è un controllo superato.
- I crash coinvolgono QtGui e la gestione dei wrapper PySide/Shiboken durante
  la distruzione degli oggetti. Il loro nesso con il blocco dell'intero sistema
  non è provato. I rilanci ripetuti sono stati una scelta sbagliata.
- Il journal termina alle 12:07:14.490, dopo il dump dell'ultimo test. Non
  documenta la causa del successivo silenzio né l'istante esatto dello schermo nero.
- Registrati 190 avvisi `QSGRhiLayer: Attempted to set unsupported texture
  format 8` e sei avvisi sull'attributo vertex 1. Il formato RGBA16F è stato
  rimosso dalla patch candidata e l'interfaccia vertex completata. Queste
  revisioni non sono state provate con rendering.
- Nei dump i test hanno circa 200 MB di picco RSS ciascuno, senza crescita
  evidente fra i processi, e cinque/sei thread al crash. I file compressi
  occupano circa 43 MB complessivi. Nessuna evidenza che i test abbiano da soli
  esaurito RAM o disco; manca però la telemetria globale al momento del blocco.
- Dopo il riavvio il filesystem `/` è al 99%, circa 2.3 GB disponibili; gli
  inode sono occupati al 13%. È poco spazio, ma non è dimostrato che il disco
  fosse saturo durante l'episodio. Nessuna cancellazione eseguita.
- Nel kernel precedente non risultano OOM kill, GPU reset/ring timeout o
  errori I/O pertinenti. Non c'è un nuovo report di crash Hyprland. L'assenza
  di messaggi non esclude un hard lock che non riesce a scrivere il journal.
- HyprGlass: plugin list `[]`. Registratore: inactive/disabled.
- La patch debounce era soltanto in copie temporanee: nessun nuovo shader o
  QML del debounce era caricato dalla sessione. Rimane applicata la precedente
  patch delle catture stabili, che non aveva eliminato lo sfarfallio.

## Contenimento e lavoro conservato

Il programma di test con rendering è stato archiviato come testo e sostituito
con verifiche statiche in `tests/settings-darker-debounce-check.py`. Il comando
ora applica la patch a copie temporanee, analizza i QML, compila cinque shader
e verifica le callback JavaScript con un orologio simulato. Non importa
PySide, non apre finestre o contesti grafici e non esegue rendering llvmpipe.
Questi controlli passano e non sostituiscono la verifica visiva.

La candidata `patches/settings-darker-debounce.patch` resta non applicata.
Proseguire con analisi statica; non rilanciare rendering, neppure software,
come continuazione automatica di questo lavoro. Nessuna modifica a plugin,
registratore, driver o clock.

Evidenze private:
`~/.local/state/end4-pC/diagnostics/20261116-black-screen-during-cpu-test/`:
journal filtrato senza ambiente dei processi, kernel completo, elenco dump,
stato filesystem, hash dei sorgenti e sorgente del test sospeso.
