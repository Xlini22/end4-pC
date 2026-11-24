# Wallpaper themes without compositor reload

The image-only wallpaper transition remained fluid. Applying only the theme,
or issuing one unchanged Hyprland configuration reload, reproduced persistent
lag with the old HyprGlass namespace cache. Manual and timer wallpaper changes
remained fluid after moving generated colors outside the watched config tree.
The native cache correction is documented separately in
[hyprglass-reload-2026-11-24.md](hyprglass-reload-2026-11-24.md).

`switchwall.sh` now applies generated colors using `hyprland-colors.py` and
`hyprctl eval`. It preserves custom border roles, handles delayed settings
writes, updates the named pinned-window rule without duplicates, and includes
the cached Lua palette in color-lock snapshots. It does not remove theme
updates or wallpaper animations.

## External configuration migration

The installed migration also changed three files outside this repository.
Retain the other Matugen templates and settings when reproducing it:

1. Set `[templates.hyprland].output_path` in `~/.config/matugen/config.toml`
   to the absolute path of
   `$XDG_STATE_HOME/quickshell/user/generated/hyprland-colors.lua`
   (default state root: `~/.local/state`).
2. In the existing Hyprland Matugen template, give the pinned-window rule the
   stable name `end4-pC-pinned-colours`:

   ```lua
   hl.window_rule({
       name = "end4-pC-pinned-colours",
       match = { pin = 1 },
       border_color = "rgba({{colors.primary.default.hex_stripped}}AA) rgba({{colors.primary.default.hex_stripped}}77)",
   })
   ```

3. Seed the cached palette from the existing generated colors before replacing
   the watched `~/.config/hypr/hyprland/colors.lua` with the `STARTUP_LOADER`
   constant from `scripts/colors/hyprland-colors.py`. This stable loader uses
   `io.open` and `load`, avoiding dependency tracking of the generated palette.

The helper deliberately does nothing if the cached palette is absent, so the
existing unmodified installation keeps its previous behavior. The external
migration is already installed locally; these instructions preserve it without
publishing a personal Matugen configuration or overwriting unrelated settings.

## Checks

```sh
python3 tests/hyprland-live-colors-check.py
python3 tests/wallpaper-scheduling-check.py
```

The checks mock Lua/IPC and use temporary settings. No rendering or session
reload is required. Both manual and timer wallpaper changes were confirmed
fluid by the user after installation.
