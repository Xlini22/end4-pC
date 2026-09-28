pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.functions
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    readonly property var player: MprisController.activePlayer
    readonly property string trackPageUrl: String(root.player?.metadata?.["xesam:url"] ?? "")
    readonly property string trackTitle: String(root.player?.trackTitle ?? "")
    readonly property string trackArtist: String(root.player?.trackArtist ?? "")
    readonly property string trackAlbum: String(root.player?.trackAlbum ?? "")
    readonly property string mprisArtUrl: String(root.player?.trackArtUrl ?? "")

    function youtubeIdFromUrl(url) {
        const value = String(url ?? "")
        if (!value.includes("youtube.com") && !value.includes("youtu.be")) return ""
        const match = value.match(/(?:[?&]v=|youtu\.be\/|shorts\/|embed\/|live\/)([A-Za-z0-9_-]{11})/)
        return match?.[1] ?? ""
    }

    function normalized(value) {
        return String(value ?? "").trim().toLowerCase()
    }

    function comparableTrackTitle(value) {
        return root.normalized(value)
            .replace(/[\[\](){}.,:;_\-/]+/g, " ")
            .split(/\s+/)
            .filter(token => token.length > 0 && token !== "feat" && token !== "featuring")
            .sort()
            .join(" ")
    }

    readonly property string youtubeVideoId: root.youtubeIdFromUrl(root.trackPageUrl)
    readonly property bool isAppleMusic: root.trackPageUrl.includes("music.apple.com/")
        && root.trackTitle.length > 0 && root.trackArtist.length > 0
    readonly property string youtubeArtUrl: root.youtubeVideoId.length > 0
        ? `https://i.ytimg.com/vi/${root.youtubeVideoId}/maxresdefault.jpg` : ""
    readonly property string youtubeSdArtUrl: root.youtubeVideoId.length > 0
        ? `https://i.ytimg.com/vi/${root.youtubeVideoId}/sddefault.jpg` : ""
    readonly property string youtubeHqArtUrl: root.youtubeVideoId.length > 0
        ? `https://i.ytimg.com/vi/${root.youtubeVideoId}/hqdefault.jpg` : ""

    // Apple Music uses one cache entry and one catalog request per album.
    // Include the title only when the browser does not expose an album.
    readonly property string appleAlbumKey: root.isAppleMusic
        ? `apple-music:${root.trackArtist}\n${root.trackAlbum || root.trackTitle}` : ""
    readonly property string artworkKey: root.youtubeArtUrl
        || root.appleAlbumKey
        || root.mprisArtUrl
    readonly property string cacheHash: artworkKey.length > 0 ? Qt.md5(artworkKey) : ""
    readonly property string artFilePath: cacheHash.length > 0
        ? `${Directories.coverArt}/${cacheHash}` : ""
    readonly property string albumDataPath: cacheHash.length > 0
        ? `${Directories.coverArt}/${cacheHash}.json` : ""
    readonly property bool directSource: !root.isAppleMusic
        && root.youtubeVideoId.length === 0
        && root.mprisArtUrl.length > 0
        && !root.mprisArtUrl.startsWith("http://")
        && !root.mprisArtUrl.startsWith("https://")

    property bool ready: false
    property int requestId: 0
    property var appleAlbumData: ({ "tracks": [] })
    property var durationCache: ({})
    property real cachedTrackLength: 0

    readonly property string trackIdentity: `${root.trackTitle}\n${root.trackArtist}\n${root.trackAlbum}`
    readonly property real rawPlaybackLength: Number(root.player?.length ?? 0)
    readonly property real rawPlaybackPosition: Number(root.player?.position ?? 0)

    readonly property var appleTracks: root.appleAlbumData?.tracks ?? []
    readonly property int appleTrackIndex: {
        const title = root.normalized(root.trackTitle)
        for (let i = 0; i < root.appleTracks.length; i++) {
            if (root.normalized(root.appleTracks[i]?.trackName) === title)
                return i
        }
        const comparableTitle = root.comparableTrackTitle(root.trackTitle)
        for (let i = 0; i < root.appleTracks.length; i++) {
            if (root.comparableTrackTitle(root.appleTracks[i]?.trackName) === comparableTitle)
                return i
        }
        return -1
    }
    readonly property var appleTrack: root.appleTrackIndex >= 0
        ? root.appleTracks[root.appleTrackIndex] : null
    readonly property real appleTrackLength: Number(root.appleTrack?.trackTimeMillis ?? 0) / 1000
    readonly property real appleTrackOffset: {
        if (root.appleTrackIndex <= 0) return 0
        let milliseconds = 0
        for (let i = 0; i < root.appleTrackIndex; i++)
            milliseconds += Number(root.appleTracks[i]?.trackTimeMillis ?? 0)
        return milliseconds / 1000
    }
    readonly property bool appleCumulativeTimeline: root.isAppleMusic
        && root.appleTrackLength > 0
        && root.appleTrackOffset > 0
        && Number(root.player?.length ?? 0) > root.appleTrackLength + 2

    readonly property real playbackLength: Math.max(0,
        root.appleTrackLength > 0
            ? root.appleTrackLength
            : root.cachedTrackLength)
    readonly property bool durationKnown: root.playbackLength > 0
    readonly property real playbackPosition: {
        const rawPosition = Number(root.player?.position ?? 0)
        if (!root.isAppleMusic || root.appleTrackLength <= 0)
            return Math.max(0, rawPosition)
        const relative = root.appleCumulativeTimeline
            ? rawPosition - root.appleTrackOffset : rawPosition
        return Math.max(0, Math.min(root.playbackLength, relative))
    }

    function rawPositionFor(relativePosition) {
        const value = Math.max(0, Math.min(root.playbackLength, Number(relativePosition ?? 0)))
        return root.appleCumulativeTimeline ? root.appleTrackOffset + value : value
    }

    function rememberDuration(duration) {
        const value = Number(duration ?? 0)
        if (root.trackIdentity.length === 0 || value <= 0) return
        const updated = Object.assign({}, root.durationCache)
        updated[root.trackIdentity] = value
        root.durationCache = updated
        root.cachedTrackLength = value
    }

    function updateDuration() {
        if (root.appleTrackLength > 0) {
            root.rememberDuration(root.appleTrackLength)
            return
        }

        // Apple Music may temporarily expose the album timeline or simply
        // copy the current position into length. Never cache that value.
        if (root.isAppleMusic) return

        if (root.rawPlaybackLength > root.rawPlaybackPosition + 0.5
                || (root.rawPlaybackPosition < 1 && root.rawPlaybackLength > 0))
            root.rememberDuration(root.rawPlaybackLength)
    }

    function scheduleDurationRetry() {
        durationRetryTimer.stop()
        if (root.isAppleMusic && !root.durationKnown
                && root.trackTitle.length > 0 && root.trackArtist.length > 0)
            durationRetryTimer.start()
    }

    function durationFromAppleResults(results) {
        const title = root.normalized(root.trackTitle)
        const comparableTitle = root.comparableTrackTitle(root.trackTitle)
        const artist = root.normalized(root.trackArtist)
        const album = root.normalized(root.trackAlbum)
        let bestDuration = 0
        let bestScore = -1

        for (const result of results ?? []) {
            const duration = Number(result?.trackTimeMillis ?? 0) / 1000
            if (duration <= 0) continue

            const resultTitle = root.normalized(result?.trackName)
            const exactTitle = resultTitle === title
            const comparable = root.comparableTrackTitle(result?.trackName) === comparableTitle
            if (!exactTitle && !comparable) continue

            let score = exactTitle ? 100 : 80
            if (root.normalized(result?.artistName) === artist) score += 30
            if (album.length > 0 && root.normalized(result?.collectionName) === album) score += 20
            if (score > bestScore) {
                bestScore = score
                bestDuration = duration
            }
        }
        return bestDuration
    }

    onTrackIdentityChanged: {
        durationResolver.running = false
        root.cachedTrackLength = Number(root.durationCache[root.trackIdentity] ?? 0)
        Qt.callLater(() => {
            root.updateDuration()
            root.scheduleDurationRetry()
        })
    }
    onAppleTrackLengthChanged: root.updateDuration()
    onIsAppleMusicChanged: Qt.callLater(root.scheduleDurationRetry)
    onDurationKnownChanged: {
        if (root.durationKnown)
            durationRetryTimer.stop()
    }

    Connections {
        target: root.player
        function onLengthChanged() { root.updateDuration() }
    }

    // MPRIS position is queried lazily. Resource polling normally refreshes it
    // every three seconds, which makes elapsed time jump in the media widgets.
    // Keep media time on its own one-second clock while playback is active.
    Timer {
        interval: 1000
        repeat: true
        running: root.player?.isPlaying ?? false
        onTriggered: root.player?.positionChanged()
    }

    Timer {
        id: durationRetryTimer
        interval: 10000
        repeat: false
        onTriggered: {
            if (!root.isAppleMusic || root.durationKnown || durationResolver.running)
                return
            durationResolver.trackIdentity = root.trackIdentity
            durationResolver.title = root.trackTitle
            durationResolver.artist = root.trackArtist
            durationResolver.album = root.trackAlbum
            durationResolver.running = true
        }
    }

    // If the album lookup did not yield this track's duration, retry only the
    // lightweight song lookup after ten seconds. Artwork and album cache stay untouched.
    Process {
        id: durationResolver

        property string trackIdentity: ""
        property string title: ""
        property string artist: ""
        property string album: ""

        readonly property string escapedSearch: StringUtils.shellSingleQuoteEscape(
            `${title} ${artist} ${album}`)
        readonly property string escapedTitle: StringUtils.shellSingleQuoteEscape(title)
        readonly property string escapedArtist: StringUtils.shellSingleQuoteEscape(artist)
        readonly property string escapedAlbum: StringUtils.shellSingleQuoteEscape(album)

        command: ["bash", "-c",
            `search_file=$(mktemp); lookup_file=$(mktemp); `
            + `trap 'rm -f "$search_file" "$lookup_file"' EXIT; `
            + `curl -4 -fsSG --retry 2 --retry-delay 1 'https://itunes.apple.com/search' `
            + `--data-urlencode 'term=${escapedSearch}' --data 'entity=song' --data 'limit=25' `
            + `-o "$search_file"; `
            + `collection=$(jq -r --arg title '${escapedTitle}' --arg artist '${escapedArtist}' --arg album '${escapedAlbum}' `
            + `'def norm: ascii_downcase; `
            + `([.results[] | select(((.trackName // "") | norm) == ($title | norm) `
            + `and ((.artistName // "") | norm) == ($artist | norm) `
            + `and (($album | length) == 0 or ((.collectionName // "") | norm) == ($album | norm)))][0] `
            + `// [.results[] | select(((.artistName // "") | norm) == ($artist | norm) `
            + `and (($album | length) == 0 or ((.collectionName // "") | norm) == ($album | norm)))][0] `
            + `// [.results[] | select(((.trackName // "") | norm) == ($title | norm) `
            + `and ((.artistName // "") | norm) == ($artist | norm))][0]) `
            + `| .collectionId // empty' "$search_file"); `
            + `[ -n "$collection" ]; `
            + `curl -4 -fsSG --retry 2 --retry-delay 1 'https://itunes.apple.com/lookup' `
            + `--data-urlencode "id=$collection" --data 'entity=song' -o "$lookup_file"; `
            + `cat "$lookup_file"`]

        stdout: StdioCollector {
            onStreamFinished: {
                if (durationResolver.trackIdentity !== root.trackIdentity
                        || root.durationKnown || text.trim().length === 0)
                    return
                try {
                    const response = JSON.parse(text)
                    const duration = root.durationFromAppleResults(response?.results ?? [])
                    if (duration > 0)
                        root.rememberDuration(duration)
                } catch (error) {
                    console.warn("[MediaArtwork] Could not parse duration retry response:", error)
                }
            }
        }

        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim().length > 0)
                    console.warn("[MediaArtwork] duration retry error:", text.trim())
            }
        }
    }

    readonly property string source: {
        if (!root.ready) return ""
        if (root.directSource) return root.mprisArtUrl
        return root.artFilePath.length > 0 ? Qt.resolvedUrl(root.artFilePath) : ""
    }

    function refresh() {
        root.requestId++
        root.ready = false
        restartTimer.stop()

        if (root.artworkKey.length === 0) {
            artDownloader.running = false
            root.appleAlbumData = ({ "tracks": [] })
            return
        }
        if (!root.isAppleMusic)
            root.appleAlbumData = ({ "tracks": [] })
        if (root.directSource) {
            artDownloader.running = false
            root.ready = true
            return
        }
        restartTimer.restart()
    }

    onArtworkKeyChanged: root.refresh()
    Component.onCompleted: {
        root.refresh()
        Qt.callLater(root.scheduleDurationRetry)
    }

    Timer {
        id: restartTimer
        // Browser MPRIS metadata arrives in multiple updates. Debounce them
        // so title, artist and album form one stable request.
        interval: 250
        repeat: false
        onTriggered: {
            if (artDownloader.running) {
                artDownloader.running = false
                restartTimer.restart()
                return
            }
            artDownloader.requestId = root.requestId
            artDownloader.outputPath = root.artFilePath
            artDownloader.albumDataPath = root.albumDataPath
            artDownloader.targetUrl = root.youtubeArtUrl || root.mprisArtUrl
            artDownloader.sdUrl = root.youtubeSdArtUrl
            artDownloader.hqUrl = root.youtubeHqArtUrl
            artDownloader.videoId = root.youtubeVideoId
            artDownloader.appleMusic = root.isAppleMusic
            artDownloader.title = root.trackTitle
            artDownloader.artist = root.trackArtist
            artDownloader.album = root.trackAlbum
            artDownloader.fallbackArtUrl = root.mprisArtUrl
            artDownloader.running = true
        }
    }

    Process {
        id: artDownloader

        property int requestId: 0
        property string outputPath: ""
        property string albumDataPath: ""
        property string targetUrl: ""
        property string sdUrl: ""
        property string hqUrl: ""
        property string videoId: ""
        property bool appleMusic: false
        property string title: ""
        property string artist: ""
        property string album: ""
        property string fallbackArtUrl: ""

        readonly property string escapedPath: StringUtils.shellSingleQuoteEscape(outputPath)
        readonly property string escapedDataPath: StringUtils.shellSingleQuoteEscape(albumDataPath)
        readonly property string escapedCacheDir: StringUtils.shellSingleQuoteEscape(Directories.coverArt)
        readonly property string escapedTarget: StringUtils.shellSingleQuoteEscape(targetUrl)
        readonly property string escapedSd: StringUtils.shellSingleQuoteEscape(sdUrl)
        readonly property string escapedHq: StringUtils.shellSingleQuoteEscape(hqUrl)
        readonly property string escapedSearch: StringUtils.shellSingleQuoteEscape(
            `${title} ${artist} ${album}`)
        readonly property string escapedTitle: StringUtils.shellSingleQuoteEscape(title)
        readonly property string escapedArtist: StringUtils.shellSingleQuoteEscape(artist)
        readonly property string escapedAlbum: StringUtils.shellSingleQuoteEscape(album)
        readonly property string escapedFallbackPath: StringUtils.shellSingleQuoteEscape(
            fallbackArtUrl.startsWith("file://")
                ? decodeURIComponent(fallbackArtUrl.substring(7)) : "")

        command: {
            if (videoId.length > 0) {
                return ["bash", "-c",
                    `mkdir -p '${escapedCacheDir}'; [ -s '${escapedPath}' ] || { `
                    + `curl -4 -fsSL '${escapedTarget}' -o '${escapedPath}' `
                    + `|| curl -4 -fsSL '${escapedSd}' -o '${escapedPath}' `
                    + `|| curl -4 -fsSL '${escapedHq}' -o '${escapedPath}' `
                    + `|| { rm -f '${escapedPath}'; exit 1; }; }`]
            }
            if (appleMusic) {
                return ["bash", "-c",
                    `mkdir -p '${escapedCacheDir}'; `
                    + `if [ ! -s '${escapedPath}' ] || [ ! -s '${escapedDataPath}' ]; then `
                    + `search_file=$(mktemp); lookup_file=$(mktemp); `
                    + `trap 'rm -f "$search_file" "$lookup_file"' EXIT; `
                    + `curl -4 -fsSG --retry 2 --retry-delay 1 'https://itunes.apple.com/search' `
                    + `--data-urlencode 'term=${escapedSearch}' --data 'entity=song' --data 'limit=10' `
                    + `-o "$search_file"; `
                    + `collection=$(jq -r --arg title '${escapedTitle}' --arg artist '${escapedArtist}' --arg album '${escapedAlbum}' `
                    + `'def norm: ascii_downcase; `
                    + `([.results[] | select(((.trackName // "") | norm) == ($title | norm) `
                    + `and ((.artistName // "") | norm) == ($artist | norm) `
                    + `and (($album | length) == 0 or ((.collectionName // "") | norm) == ($album | norm)))][0] `
                    + `// [.results[] | select(((.artistName // "") | norm) == ($artist | norm) `
                    + `and (($album | length) == 0 or ((.collectionName // "") | norm) == ($album | norm)))][0] `
                    + `// .results[0]) | .collectionId // empty' "$search_file"); `
                    + `artwork=$(jq -r --arg title '${escapedTitle}' --arg artist '${escapedArtist}' --arg album '${escapedAlbum}' `
                    + `'def norm: ascii_downcase; `
                    + `([.results[] | select(((.trackName // "") | norm) == ($title | norm) `
                    + `and ((.artistName // "") | norm) == ($artist | norm) `
                    + `and (($album | length) == 0 or ((.collectionName // "") | norm) == ($album | norm)))][0] `
                    + `// [.results[] | select(((.artistName // "") | norm) == ($artist | norm) `
                    + `and (($album | length) == 0 or ((.collectionName // "") | norm) == ($album | norm)))][0] `
                    + `// .results[0]) | .artworkUrl100 // empty' "$search_file"); `
                    + `[ -n "$collection" ]; `
                    + `curl -4 -fsSG --retry 2 --retry-delay 1 'https://itunes.apple.com/lookup' --data-urlencode "id=$collection" `
                    + `--data 'entity=song' -o "$lookup_file"; `
                    + `jq --arg artwork "$artwork" `
                    + `'{artwork: $artwork, tracks: [.results[] | select(.wrapperType == "track") `
                    + `| {trackName, trackTimeMillis, trackNumber, discNumber}]}' `
                    + `"$lookup_file" > '${escapedDataPath}.tmp'; `
                    + `mv '${escapedDataPath}.tmp' '${escapedDataPath}'; `
                    + `highres=$(printf '%s' "$artwork" | sed -E 's#/[^/]+$#/1200x1200bb.jpg#'); `
                    + `{ [ -n "$highres" ] && curl -4 -fsSL "$highres" -o '${escapedPath}'; } `
                    + `|| { rm -f '${escapedPath}'; `
                    + `[ -n '${escapedFallbackPath}' ] && cp -- '${escapedFallbackPath}' '${escapedPath}'; } `
                    + `|| { rm -f '${escapedPath}' '${escapedDataPath}'; exit 1; }; `
                    + `fi; cat '${escapedDataPath}'`]
            }
            return ["bash", "-c",
                `mkdir -p '${escapedCacheDir}'; [ -s '${escapedPath}' ] `
                + `|| curl -4 -fsSL '${escapedTarget}' -o '${escapedPath}'`]
        }

        stdout: StdioCollector {
            onStreamFinished: {
                if (!artDownloader.appleMusic || artDownloader.requestId !== root.requestId)
                    return
                if (text.trim().length === 0)
                    return
                try {
                    const parsed = JSON.parse(text)
                    root.appleAlbumData = parsed?.tracks ? parsed : ({ "tracks": [] })
                } catch (error) {
                    root.appleAlbumData = ({ "tracks": [] })
                    console.warn("[MediaArtwork] Could not parse Apple Music album metadata:", error)
                }
            }
        }

        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim().length > 0)
                    console.warn("[MediaArtwork] downloader error:", text.trim())
            }
        }

        onExited: (exitCode, exitStatus) => {
            if (requestId === root.requestId)
                root.ready = exitCode === 0
        }
    }
}
