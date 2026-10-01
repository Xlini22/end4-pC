.pragma library

function sourceText(player) {
    if (!player) return ""
    return [
        player.identity ?? "",
        player.desktopEntry ?? "",
        player.dbusName ?? "",
        player.metadata?.["xesam:url"] ?? ""
    ].join("\n").toLowerCase()
}

function matches(player, query) {
    const needle = String(query ?? "").trim().toLowerCase()
    return needle.length > 0 && sourceText(player).includes(needle)
}

function terms(value) {
    return String(value ?? "").split(/[,\n]/).map(term => term.trim().toLowerCase()).filter(Boolean)
}

function isAllowed(player, preferredSource, exclusive, blacklist) {
    if (terms(blacklist).some(term => sourceText(player).includes(term))) return false
    const preferred = String(preferredSource ?? "").trim()
    return !exclusive || preferred.length === 0 || matches(player, preferred)
}

function launchCommand(preferredSource, sourceUrl, desktopEntry) {
    const preferred = String(preferredSource ?? "").trim().toLowerCase()
    const url = String(sourceUrl ?? "")
    const entry = String(desktopEntry ?? "")
    const safeWebUrl = /^https?:\/\//.test(url) ? url : ""
    const safeDesktopEntry = /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(entry) ? entry : ""
    if (preferred.includes(".") && safeWebUrl.length > 0) return ["xdg-open", safeWebUrl]
    if (safeDesktopEntry.length > 0) return ["gtk-launch", safeDesktopEntry]
    if (safeWebUrl.length > 0) return ["xdg-open", safeWebUrl]
    return []
}
