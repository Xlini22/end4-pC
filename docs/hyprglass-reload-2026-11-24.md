# HyprGlass: namespace filter cache after reload

After an unchanged Hyprland configuration reload, workspace transitions and
sidebar animations became persistently slow with HyprGlass loaded. The same
reload without the plugin remained fluid. Changing only the wallpaper image
also remained fluid; theme generation triggered the problem through a reload.

## Cause and correction

The reload callback parsed temporarily reset configuration strings, clearing
the namespace sets. `shouldGlassLayer()` retained a separate function-static
signature of the old strings. When Quickshell restored those same strings, the
signature comparison skipped reparsing and left the whitelist empty. Empty
whitelists intentionally match every namespace, so background, desktop clock,
screen corners and frame surfaces acquired unwanted glass processing.

`patches/native-glass-reload-filters.patch` moves the signature beside the
parsed state and updates it inside every parser call, including reloads.
It preserves empty-whitelist semantics, Lua additions and all optical effects.
The native builder applies the patch and runs its CPU regression check.

## Evidence and validation

- Configuration getters returned identical strings before and after reload;
  the faulty state was the parsed cache, not the published settings.
- A diagnostic build observed 13 layer objects after reload, including
  unexpected background and clock processing at approximately 60 samples/sec.
  Listener counts did not increase. These counters measure sampling, not FPS.
- Reordering and restoring the exact same namespace list forced reparsing
  without reload, plugin replacement or session restart. Unwanted sampling
  stopped and the user confirmed fluid workspace/sidebar animations again.
- The CPU check reproduces the bug on the old parser and passes on the fix,
  including repeated reloads, exclusions, preset/mask restoration, intentional
  wildcard behavior and retained Lua entries.
- The fixed native binary was compiled and installed for the next login with
  a backup. The user subsequently rebooted and confirmed that a timer-driven
  wallpaper change remained fluid. A controlled reload of the fixed build
  still needs the final visual confirmation.

Run without rendering:

```sh
python3 tests/native-glass-reload-filters-check.py PATH_TO_PATCHED_NATIVE_SOURCE
```

Local diagnostic sources, captures, binaries and installation backups remain
under ignored `diagnostics/`. The production fix does not require diagnostic
counters and does not change darker timing, shaders, buffer allocation or the
set of configured surfaces.
