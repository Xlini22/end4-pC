-- Tab release applies focus; the MRU snapshot survives until Alt release.
local order, index, direction = nil, 0, 1

local function eligible(window)
    return window and window.mapped and not window.hidden and window.accepts_input
end

local function step(delta)
    direction = delta
    if not order then
        order = {}
        local active = hl.get_active_window()
        for _, window in ipairs(hl.get_windows({ mapped = true })) do
            if eligible(window) then
                local rank = window.focus_history_id
                table.insert(order, { address = window.address,
                    rank = rank >= 0 and rank or math.huge })
            end
        end
        table.sort(order, function(a, b)
            if a.rank == b.rank then return a.address < b.address end
            return a.rank < b.rank
        end)
        index = delta == 1 and 0 or 1
        for i, entry in ipairs(order) do
            if active and entry.address == active.address then index = i; break end
        end
    end
    for _ = 1, #order do
        index = (index - 1 + delta) % #order + 1
        if eligible(hl.get_window("address:" .. order[index].address)) then return end
    end
end

local function commit()
    if not order then return end
    -- A window can close while Alt is held. Continue in the chosen direction.
    for offset = 0, #order - 1 do
        local candidate = (index - 1 + offset * direction) % #order + 1
        local entry = order[candidate]
        if eligible(hl.get_window("address:" .. entry.address)) then
            index = candidate
            hl.dispatch(hl.dsp.focus({ window = "address:" .. entry.address }))
            return
        end
    end
end

hl.bind("ALT + Tab", function() step(1) end,
    { description = "Window: Select next recently used window" })
hl.bind("ALT + SHIFT + Tab", function() step(-1) end,
    { description = "Window: Select previous recently used window" })
hl.bind("Tab", commit, { release = true, ignore_mods = true, transparent = true,
    non_consuming = true })
for _, key in ipairs({ "Alt_L", "Alt_R" }) do
    hl.bind(key, function() order, index = nil, 0 end,
        { release = true, ignore_mods = true, transparent = true,
        non_consuming = true })
end
