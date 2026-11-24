#!/usr/bin/env python3
"""Apply generated Hyprland colours without reloading its configuration."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

STARTUP_LOADER = '''-- Read colours without registering the generated file as a config dependency.
local root = os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")
local file = io.open(root .. "/quickshell/user/generated/hyprland-colors.lua", "r")
if file then
    local code = file:read("*a")
    file:close()
    local chunk, err = load(code, "end4-colours", "t", _ENV)
    if chunk then chunk() else print("[end4-colours] " .. tostring(err)) end
end
'''


def lua_string(value):
    equals = ""
    while "]" + equals + "]" in value:
        equals += "="
    return "[" + equals + "[" + value + "]" + equals + "]"


def command(source, custom_borders, borders=None):
    if borders is not None and (len(borders) not in (0, 2)
            or any(not re.fullmatch(r"rgba\([0-9a-fA-F]{8}\)", c) for c in borders)):
        raise ValueError("Expected two rgba(RRGGBBAA) border colours")
    # Keep user-selected border roles when the generated palette arrives later.
    # ponytail: a local Lua environment filters only these two options; no global hl mutation.
    code = "local api=hl; local env=setmetatable({hl=setmetatable({config=function(t) "
    if custom_borders:
        code += "if t.general and t.general.col then t.general.col.active_border=nil; t.general.col.inactive_border=nil end; "
    code += "api.config(t) end},{__index=api})},{__index=_G}); "
    code += "assert(load(" + lua_string(source) + ",'end4-colours','t',env))(); "
    if borders:
        code += "hl.config({general={col={active_border=" + lua_string(borders[0])
        code += ",inactive_border=" + lua_string(borders[1]) + "}}})"
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--borders", nargs="*")
    args = parser.parse_args()
    state = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    source = state / "quickshell/user/generated/hyprland-colors.lua"
    # Until the migration is installed, retain the existing behaviour.
    if not source.is_file():
        return 0
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    config = json.loads((config_home / "illogical-impulse/config.json").read_text())
    custom = config.get("hyprland", {}).get("general", {}).get("borderColor", {}).get("enable", False)
    if args.borders is not None:
        # QML's config write is delayed: the explicit UI state wins over the old JSON.
        custom = bool(args.borders)
    code = command(source.read_text(), custom, args.borders)
    result = subprocess.run(["hyprctl", "eval", code], capture_output=True, text=True, timeout=5)
    # hyprctl can report a Lua failure in stdout even with an exit status of zero.
    if result.returncode or result.stdout.strip() != "ok":
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Colour update failed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"[hyprland-colors] {error}", file=sys.stderr)
        sys.exit(1)
