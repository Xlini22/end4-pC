-- Run from the project root: lua tests/alt-tab-check.lua
local binds, options, windows, active, focused = {}, {}, {}, nil, {}
hl = {
    bind = function(key, callback, opts) binds[key], options[key] = callback, opts end,
    get_windows = function() return windows end,
    get_active_window = function() return active end,
    get_window = function(selector)
        for _, window in ipairs(windows) do
            if selector == "address:" .. window.address then return window end
        end
    end,
    dsp = { focus = function(spec) return spec end },
    dispatch = function(spec)
        local target = assert(hl.get_window(spec.window))
        for _, window in ipairs(windows) do
            if window.focus_history_id >= 0 and window.focus_history_id < target.focus_history_id then
                window.focus_history_id = window.focus_history_id + 1
            end
        end
        target.focus_history_id, active = 0, target
        focused[#focused + 1] = target.address
    end,
}
dofile("scripts/hyprland/alt-tab.lua")
local function reset(count)
    binds.Alt_L()
    windows, focused = {}, {}
    for i = 1, count do
        windows[i] = { address = "0x" .. i, mapped = true, hidden = false,
            accepts_input = true, focus_history_id = i - 1, workspace = i }
    end
    active = windows[1]
end
local next, previous = binds["ALT + Tab"], binds["ALT + SHIFT + Tab"]
local commit, finish = binds.Tab, binds.Alt_L
local function tap(reverse)
    if reverse then previous() else next() end
    commit()
end

reset(4)
next()
assert(#focused == 0 and active.address == "0x1", "Focus must wait for Tab release")
commit()
assert(active.address == "0x2" and active.workspace == 2, "Tab release must switch workspace while Alt stays down")
next()
assert(active.address == "0x2", "The next press must not change focus")
commit()
assert(active.address == "0x3", "Intermediate focus must not reorder the snapshot")
local before = #focused
finish()
assert(#focused == before, "Alt release must only finish the sequence")
tap(); finish()
assert(active.address == "0x2", "A new sequence must use the updated MRU history")
tap(); finish()
assert(active.address == "0x3", "Separate gestures must toggle the last two windows")

reset(4)
tap(true); binds.Alt_R()
assert(active.address == "0x4", "Reverse must wrap to the least recent window")
reset(4)
tap(); tap(); tap(true); finish()
assert(active.address == "0x2", "Direction can change without rebuilding the snapshot")
reset(4)
for _ = 1, 5 do tap() end
finish()
assert(active.address == "0x2", "Forward cycling must wrap with intermediate focus changes")

reset(4)
next()
windows[2].focus_history_id, windows[3].focus_history_id = 2, 1
windows[5] = { address = "0x5", mapped = true, accepts_input = true, focus_history_id = 0 }
commit(); tap(); finish()
assert(active.address == "0x3", "MRU changes and new windows must not reorder a gesture")
reset(4)
next(); windows[2].mapped = false; commit()
assert(active.address == "0x3", "Skip a selected window closed before Tab release")
tap(); finish()
assert(active.address == "0x4", "Continue from the fallback window after a closure")
reset(4)
windows[2].hidden, windows[3].accepts_input = true, false
tap(); finish()
assert(active.address == "0x4", "Skip hidden and noninteractive windows")
reset(4)
tap(); windows[3].mapped = false; tap(); finish()
assert(active.address == "0x4", "Skip windows closed while cycling")

reset(0)
tap(); tap(true); finish()
assert(#focused == 0, "Empty desktops must be harmless")
reset(1)
tap(); tap(true); finish()
assert(active.address == "0x1", "One-window desktops must be harmless")
reset(3)
active = nil
tap(); finish()
assert(active.address == "0x1", "A layer with keyboard focus must still allow switching")
before = #focused
commit(); finish()
assert(#focused == before, "Tab or Alt alone must not change focus")
next(); finish(); commit()
assert(#focused == before, "Alt release must end the snapshot even if Tab is still held")
for _, key in ipairs({ "Tab", "Alt_L", "Alt_R" }) do
    assert(options[key].release and options[key].ignore_mods and options[key].transparent
        and options[key].non_consuming and not options[key].locked)
end
print("Alt+Tab Tab-release focus, stable MRU, reverse, wrap and closure checks passed")
