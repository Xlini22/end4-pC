# Dolphin: ripristino della configurazione attuale

## Da fare — richiesta del 13 novembre 2026

- Salvare tutte le impostazioni attuali di grafica e comportamento di Dolphin:
  tema, colori, icone, font, toolbar, pannelli, modalità di visualizzazione,
  navigazione, anteprime, associazioni e altre personalizzazioni effettive.
- Preparare un ripristino automatico che ricrei questa configurazione anche
  dopo una reinstallazione. Includere le dipendenze necessarie e fare un backup
  dei file esistenti prima di modificarli; non salvare credenziali o cronologie.
- Documentare uno schema delle sorgenti di personalizzazione: per ogni aspetto,
  indicare il file o componente che lo controlla, la precedenza degli override,
  le dipendenze e come verificare quale impostazione viene realmente usata.
  Verificare configurazione Dolphin/KDE/Qt, temi e icone, variabili d'ambiente,
  launcher `.desktop` locali e di sistema, scorciatoie Hyprland ed eventuali
  impostazioni delle singole cartelle. Distinguere i percorsi verificati dalle
  ipotesi.
- Verificare che il ripristino mantenga coerente l'avvio dalla dock e da Super+E,
  confrontando aspetto e comportamento con la configurazione attuale.

Questo documento registra il lavoro da fare: il backup completo e il ripristino
automatico non sono ancora stati implementati.

## Riferimenti già verificati

- Super+E è definito in `~/.config/hypr/hyprland/keybinds.lua` e usa
  `fileManager` da `~/.config/hypr/hyprland/variables.lua`, con eventuale override
  in `~/.config/hypr/custom/variables.lua`. Attualmente lo script
  `launch_first_available.sh` seleziona `dolphin`.
- La dock ha fissato `org.kde.dolphin`. Il launcher locale
  `~/.local/share/applications/org.kde.dolphin.desktop` prevale su quello di
  sistema `/usr/share/applications/org.kde.dolphin.desktop`.
- Il launcher locale è stato corretto con `Exec=dolphin %u`, `Hidden=false` e
  `NoDisplay=false`. Prima forzava `QT_QPA_PLATFORMTHEME=qt6ct` e
  `QT_STYLE_OVERRIDE=Kvantum`, producendo l'aspetto indesiderato segnalato
  dall'utente. Non reintrodurre quelle forzature nel ripristino.
