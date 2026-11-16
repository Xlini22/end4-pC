# Bozza locale della PR AirDrop

Branch: `feat/airdrop`.
Base: `pctrade/end4-pC:main`, commit `157a46fb` aggiornato da upstream.
Checkout di revisione: `../end4-pC-airdrop`.

Commit:

- `e0844044` — `chore(airdrop): add portable Omdrop desktop adaptation`
- `1362a0f1` — `feat(bar): add optional AirDrop widget`
- `302a12d3` — `style(bar): match AirDrop to utility button behaviour`
- `242edbeb` — `feat(airdrop): upgrade Omdrop integration to 0.18.7`
- `8114e99` — `fix(airdrop): preserve name edits and dismiss popup on outside click`

Branch e bozza restano locali. Il checkout della shell in uso resta su `latest`.

## Titolo proposto

feat(bar): add optional AirDrop widget

## Descrizione proposta

Users with Omdrop and a compatible radio backend can add an AirDrop widget from
the bar settings, receive for ten minutes or until one file arrives, and send
files to discovered Apple devices. The popup shows backend-reported visibility,
remaining time, prerequisites and command failures, and lets users change the
advertised name and destination folder. Adding or opening the widget does not
start the radio.

The bar entry reuses the existing utility button components: Material buttons
expand on hover, keyboard focus and active receiving, while other bar styles
use the existing circular button. The transparent AirDrop icon follows the
theme. The popup shares bar popup colours, rounding and shadow, accepts keyboard
input independently of the bar, and dismisses on outside click or Escape.
Unsaved name edits survive polling, closing and failed saves. Horizontal, vertical and legacy geometry are covered by the smoke test.

The integration uses the external Omdrop CLI rather than bundling its receiver
or drivers. It includes a desktop compatibility patch for pinned Omdrop 0.18.7
(`c73e8a696bee6ade33c3aad920bba9240de2481a`),
retains its MIT notice, and documents backend setup, file chooser requirements,
Wi-Fi suspension and hardware limitations. The patch adds native notification,
browser and terminal fallbacks and correct service argument quoting for paths
with spaces. It preserves upstream's HEIC previews and file-manager fallback.
The widget backs off repeated name lookups and rolls back names from a failed
stream, including exit 65 for suspected forged rows. The shell's default bar
layout is unchanged. On Owly, the tested setup retains the Python fallback;
omdrop-core is not installed by this integration.

Validation:

- `python3 tests/omdrop-ui-check.py`: status/peer parsing, command serialization,
  cancellation, shutdown guard, missing CLI and literal arguments.
- `python3 tests/omdrop-ui-check.py --smoke --visible`: eight isolated Wayland
  scenarios (ready, missing backend, unsupported hardware, invalid status and
  failed start, forged name stream, repeated fruitless lookups and name editing), peer
  delegates, repeated popup openings and failure reporting. Name checks run
  with a hidden parent so focus changes cannot cancel the lookup under test.
  Editing covers polling, focus loss, reopening, successful and failed saves.
  Native keyboard/mouse checks confirmed typing, Save, duration selection and
  outside-click dismissal on a simulated popup.
  Command logs verify that radio activation only occurs in the explicit fake
  start test.
- `python3 tests/omdrop-desktop-check.py /path/to/omdrop-plugin`: patch application
  against the pinned revision, systemd validation with spaces, and native
  notification/browser/terminal actions with literal arguments, file-manager
  fallback and preview forwarding.
- Omdrop 0.18.7 Python suite: 413 cases, 4 skipped, no failures, both before
  the desktop adaptation and after it. The adapted suite took 215.139 seconds.
  No Rust suite was run; automated tests do not acquire the radio.
- Qt 6 QML syntax checks and Git whitespace checks passed.
- The user confirmed receiving and sending on the 0.16.1 development installation.
  That machine uses a separate radio workaround outside this PR. The final
  upstream-based checkout was tested with a fake CLI; the upgraded installed
  0.18.7 reports ready and its service validates. The user also confirmed the
  0.18.7 worked after disabling the same iPhone’s Personal Hotspot; the two
  directions were not separately reported in that confirmation. This is not
  a claim of compatibility with every Wi-Fi card.

Limitations: radio compatibility and throughput depend on the backend and
hardware. Exclusive mode can suspend Wi-Fi; channel 6 can be slow. The widget
selects Everyone; Contacts Only and identity management remain CLI features.
The one-file deadline and cancellation of a real transfer still need dedicated
hardware checks. The backend's ten-minute shutdown was observed in development.

## File inclusi e motivazioni

| File | Scopo |
| --- | --- |
| `.gitattributes` | Permette le righe vuote del contesto nei diff della patch, mantenendo i controlli whitespace per il codice. |
| `modules/ii/bar/Omdrop.qml` | Controller del widget, lettura dello stato, comandi espliciti e gestione del popup. CLI esterna configurabile con `OMDROP_CLI`. |
| `modules/ii/bar/OmdropPopup.qml` | Interfaccia di ricezione, invio, preferenze ed errori. |
| `assets/icons/airdrop-symbolic.svg` | Icona vettoriale trasparente, colorata dal tema. |
| `modules/ii/settings/pages/BarConfig.qml` | Una voce per aggiungere il widget dalle impostazioni. |
| `scripts/airdrop/omdrop-desktop.patch` | Adattamenti desktop portabili al plugin esterno. |
| `scripts/airdrop/LICENSE.omdrop` | Avviso MIT e copyright originali del plugin. |
| `tests/omdrop-ui-check.py` | Controlli dello stato e collaudo QML isolato. |
| `tests/omdrop-desktop-check.py` | Verifica ripetibile della patch e del servizio con systemd. |
| `docs/airdrop.md` | Installazione, dipendenze, comportamento, limiti e verifiche. |
| `README.md` | Collegamento alla documentazione AirDrop opzionale. |

## File esclusi e motivazioni

- `omdrop-plugin/`: checkout esterno con cronologia e interfaccia Omarchy;
  il branch distribuisce solo la patch desktop, la licenza e le istruzioni per
  il commit verificato `c73e8a696bee6ade33c3aad920bba9240de2481a`. Anche la copia
  fornita in `omdrop-plugin-aggiornato/` resta fuori dalla proposta. La versione
  in uso è installata indipendentemente in `~/.local/share/omdrop`.
- `tools/airdrop/`: pacchetto compilato, PKGBUILD, patch QCA9377, drop-in systemd
  e installer specifico della macchina. Appartengono al lavoro sul backend,
  non all'integrazione generica della shell.
- `PIANO-AIRDROP.md`: diario e documentazione del collaudo hardware locale,
  conservati nella configurazione originaria.
- `PR-AIRDROP.md`: questa bozza di revisione, conservata localmente.
- Modifiche preesistenti a `BarWidgetSwitcher.qml`, `BarWidgetSwitcherArea.qml`,
  `ClockWidget.qml`, `DiMedia.qml`, `DynamicIsland.qml`, `Resource.qml`,
  `Resources.qml`, `Visualizer.qml`, `tests/activity-exit-check.py` e il file
  `tests/island-stages-check.py`: lavoro estraneo, conservato nel checkout
  originale. Il ramo non eredita neppure gli altri commit personali di `latest`.
- Configurazioni di `/etc/owly`, unità installate, log, foto di prova, identità
  e chiavi: stato della macchina e dati personali, non presenti nella proposta.

## Revisione locale

Dal checkout originale:

```bash
git -C "../end4-pC-airdrop" log --oneline upstream/main..HEAD
git -C "../end4-pC-airdrop" diff upstream/main...HEAD
```

Non sono stati eseguiti push e non è stata aperta una PR.
