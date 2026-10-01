const fs = require("node:fs")
const assert = require("node:assert/strict")
const vm = require("node:vm")

const source = fs.readFileSync("services/MprisFilter.js", "utf8").replace(/^\.pragma library\s*/, "")
vm.runInThisContext(source, { filename: "services/MprisFilter.js" })

const appleMusic = {
    identity: "Firefox",
    desktopEntry: "firefox",
    dbusName: "org.mpris.MediaPlayer2.firefox.instance1",
    metadata: { "xesam:url": "https://music.apple.com/it/album/example" }
}
const twitch = {
    identity: "Chromium",
    desktopEntry: "chromium",
    dbusName: "org.mpris.MediaPlayer2.chromium.instance2",
    metadata: { "xesam:url": "https://www.twitch.tv/example" }
}
const spotify = {
    identity: "Spotify",
    desktopEntry: "spotify",
    dbusName: "org.mpris.MediaPlayer2.spotify",
    metadata: {}
}

assert(matches(appleMusic, "music.apple.com"))
assert(matches(spotify, "spotify"))
assert(!isAllowed(twitch, "", false, "twitch.tv, vlc"))
assert(isAllowed(appleMusic, "music.apple.com", true, "twitch.tv"))
assert(!isAllowed(spotify, "music.apple.com", true, ""))
assert.deepEqual(launchCommand("music.apple.com", appleMusic.metadata["xesam:url"], "firefox"),
    ["xdg-open", appleMusic.metadata["xesam:url"]])
assert.deepEqual(launchCommand("spotify", "https://open.spotify.com/track/example", "spotify"),
    ["gtk-launch", "spotify"])
assert.deepEqual(launchCommand("example", "javascript:alert(1)", "--unsafe"), [])
