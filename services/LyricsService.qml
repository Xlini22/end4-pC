pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris
import qs.modules.common
import qs.modules.common.functions

Singleton {
    id: root

    readonly property MprisPlayer activePlayer: MprisController.activePlayer

    property var lyricsLines: []
    property int activeIndex: -1
    property string status: "loading"
    property var slots: ["", "", "", "", "", "", ""]
    property int requestId: 0

    readonly property int before: 3
    readonly property int after:  3
    readonly property int total:  7

    function buildSlots(idx) {
        let result = []
        for (let i = 0; i < root.total; i++) {
            let lineIdx = idx - root.before + i
            if (lineIdx >= 0 && lineIdx < root.lyricsLines.length)
                result.push(root.lyricsLines[lineIdx].text || "♪")
            else
                result.push("")
        }
        return result
    }

    Timer {
        id: syncTimer
        interval: 300
        repeat: true
        running: root.status === "ok" && root.lyricsLines.length > 0
        onTriggered: {
            const pos = MediaArtwork.playbackPosition
            let idx = -1
            for (let i = 0; i < root.lyricsLines.length; i++) {
                if (root.lyricsLines[i].time <= pos) idx = i
                else break
            }
            if (idx !== root.activeIndex) {
                root.activeIndex = idx
                root.slots = root.buildSlots(idx)
            }
        }
    }

    Process {
        id: lyricsProc
        running: false
        property int requestId: 0
        stdout: SplitParser {
            onRead: data => {
                if (lyricsProc.requestId !== root.requestId) return
                const trimmed = data.trim()
                if (trimmed === "not_found") { root.status = "not_found"; return }
                if (trimmed === "no_info")   { root.status = "no_info";   return }

                const parts = trimmed.split("§")
                if (parts.length < 3) return
                if (parts[parts.length - 1].trim() !== "ok") return

                let lines = []
                for (let i = 0; i < parts.length - 1; i += 2) {
                    const t = parseFloat(parts[i])
                    const txt = parts[i + 1] || ""
                    if (!isNaN(t)) lines.push({ time: t, text: txt })
                }

                if (lines.length === 0) { root.status = "not_found"; return }

                root.lyricsLines = lines
                root.activeIndex = -1
                root.slots = root.buildSlots(-1)
                root.status = "ok"
            }
        }
        onExited: (exitCode, exitStatus) => {
            if (requestId === root.requestId && root.status === "loading")
                root.status = "not_found"
        }
    }

    function restartLyrics() {
        root.requestId++
        lyricsRestartTimer.stop()
        root.lyricsLines = []
        root.activeIndex = -1
        root.slots = ["", "", "", "", "", "", ""]
        root.status = "loading"
        lyricsRestartTimer.restart()
    }

    Timer {
        id: lyricsRestartTimer
        interval: 250
        repeat: false
        onTriggered: {
            if (lyricsProc.running) {
                lyricsProc.running = false
                lyricsRestartTimer.restart()
                return
            }
        const title    = root.activePlayer?.trackTitle  ?? ""
        const artist   = root.activePlayer?.trackArtist ?? ""
        const duration = MediaArtwork.playbackLength

            if (!title || !artist) {
                root.status = "no_info"
                return
            }

            lyricsProc.requestId = root.requestId
            lyricsProc.command = [
                "python3",
                `${Directories.scriptPath}/lyrics/lyrics.py`,
                title, artist, String(Math.floor(duration))
            ]
            lyricsProc.running = true
        }
    }

    Connections {
        target: root.activePlayer
        function onTrackTitleChanged() { root.restartLyrics() }
    }

    Component.onCompleted: root.restartLyrics()
}
