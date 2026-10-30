import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common
import qs.services
import qs.modules.common.widgets

Item {
    id: root
    property color contentColor: Appearance.colors.colOnLayer2
    property bool contentColorOverridden: false
    property bool vertical: Config.options.bar.vertical
    property bool isMaterial: Config.options.bar.cornerStyle === 3 || Config.options.bar.cornerStyle === 4
    property string cli: Quickshell.env("OMDROP_CLI") || `${Quickshell.env("HOME")}/.local/bin/omdrop`
    // ponytail: a shell exec returns 127 for a missing CLI, including on cold start.
    // Arguments stay separate so device names and paths cannot become shell code.
    readonly property var cliCommand: ["/bin/sh", "-c", 'exec "$@"', "omdrop", cli]
    property bool popupOpen: false
    property bool popupCreated: false
    property bool shuttingDown: false
    property bool stateKnown: false
    property var status: ({receiving: false, visible: false, remaining: null, name: "", dir: ""})
    property var peers: []
    property var peerNames: ({})
    property int namesMisses: 0
    readonly property bool namesWanted: peers.length === 0 || peers.some(peer => !peer.name && !peerNames[peer.mac])
    property string duration: "10m"
    property string message: ""
    property string stateError: ""
    property bool failed: false
    property bool ready: false
    property string prerequisite: Translation.tr("Checking the AirDrop backend…")
    property string operation: ""
    property bool cancelled: false
    property bool choosing: false
    readonly property bool busy: action.running
    readonly property bool receiving: stateKnown && status.receiving
    readonly property bool scanning: popupOpen && receiving && !busy
    readonly property string stateText: {
        if (busy && operation === "on") return Translation.tr("Starting…")
        if (busy && operation === "off") return Translation.tr("Stopping…")
        if (!stateKnown) return Translation.tr("Status unavailable")
        if (!receiving) return Translation.tr("Off")
        if (!status.visible) return Translation.tr("Starting visibility…")
        if (status.mode === "once") return Translation.tr("Until one file arrives")
        if (status.remaining !== null) {
            const seconds = Math.max(0, Math.ceil(status.remaining))
            return `${Translation.tr("Receiving")} · ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`
        }
        return Translation.tr("Receiving")
    }

    implicitWidth: isMaterial && !vertical ? buttonLoader.implicitWidth
        : vertical ? Appearance.sizes.verticalBarWidth - 14 : buttonLoader.implicitWidth + 4
    implicitHeight: isMaterial && vertical ? buttonLoader.implicitHeight
        : isMaterial ? 32 : vertical ? buttonLoader.implicitHeight + 4 : Appearance.sizes.barHeight

    Loader {
        id: buttonLoader
        objectName: "omdropButtonLoader"
        anchors.centerIn: parent
        sourceComponent: root.isMaterial ? materialButton : legacyButton
    }
    Component {
        id: materialButton
        UtilButton {
            id: button
            objectName: "omdropMaterialButton"
            property bool vertical: root.vertical
            iconText: ""
            forceHovered: root.popupOpen || root.receiving || activeFocus
            activeFocusOnTab: true
            Accessible.role: Accessible.Button
            Accessible.name: `AirDrop · ${root.stateText}`
            Accessible.onPressAction: root.popupOpen = !root.popupOpen
            onClicked: root.popupOpen = !root.popupOpen
            Keys.onSpacePressed: root.popupOpen = !root.popupOpen
            Keys.onReturnPressed: root.popupOpen = !root.popupOpen
            Keys.onEnterPressed: root.popupOpen = !root.popupOpen

            CustomIcon {
                anchors.centerIn: parent
                width: Appearance.font.pixelSize.large
                height: width
                source: "airdrop-symbolic.svg"
                colorize: true
                color: button.hovered ? Appearance.colors.colOnPrimary
                    : root.failed || root.stateError ? Appearance.colors.colError
                    : root.contentColorOverridden ? root.contentColor : Appearance.colors.colPrimary
                Behavior on color {
                    ColorAnimation { duration: Appearance.animation.elementMoveFast.duration }
                }
            }
            TapHandler {
                acceptedButtons: Qt.RightButton
                onTapped: root.popupOpen = !root.popupOpen
            }
        }
    }
    Component {
        id: legacyButton
        CircleUtilButton {
            id: button
            objectName: "omdropLegacyButton"
            Accessible.name: `AirDrop · ${root.stateText}`
            colBackground: root.popupOpen || root.receiving ? Appearance.colors.colPrimaryContainer : "transparent"
            buttonRadius: root.popupOpen || root.receiving ? Appearance.rounding.normal : implicitHeight / 2
            border: visualFocus
            colBorder: Appearance.colors.colPrimary
            onClicked: root.popupOpen = !root.popupOpen
            altAction: () => { root.popupOpen = !root.popupOpen }
            Behavior on buttonRadius {
                NumberAnimation { duration: Appearance.animation.elementMoveFast.duration }
            }
            CustomIcon {
                implicitWidth: Appearance.font.pixelSize.large
                implicitHeight: implicitWidth
                width: implicitWidth
                height: implicitHeight
                source: "airdrop-symbolic.svg"
                colorize: true
                color: root.failed || root.stateError ? Appearance.colors.colError
                    : root.receiving ? Appearance.colors.colPrimary : root.contentColor
            }
        }
    }

    // Keep the CLI as the state owner. Invalid output must never confirm visibility.
    function parseStatus(text) {
        const value = JSON.parse(text)
        if (!value || typeof value.receiving !== "boolean"
            || !(value.visible === null || typeof value.visible === "boolean")
            || !(value.remaining === null || (Number.isFinite(value.remaining) && value.remaining >= 0))
            || typeof value.dir !== "string"
            || !(value.name === null || typeof value.name === "string"))
            throw new Error("Invalid AirDrop status")
        return value
    }

    function parsePeers(text) {
        const values = JSON.parse(text)
        if (!Array.isArray(values)) throw new Error("Invalid AirDrop device list")
        return values.filter(peer => peer && typeof peer.mac === "string"
            && /^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$/i.test(peer.mac)
            && (peer.name === null || typeof peer.name === "string"))
    }

    function refresh() {
        if (!stateProcess.running) stateProcess.running = true
    }

    function learnPeerName(peer) {
        if (!peer || typeof peer.name !== "string" || !peers.some(known => known.mac === peer.mac)) return false
        let name = peer.name.replace(/[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202e\u2066-\u2069\ufeff]/g, "").trim().slice(0, 255)
        if (/[\uD800-\uDBFF]$/.test(name)) name = name.slice(0, -1)
        if (!name || peerNames[peer.mac] === name) return false
        peerNames = Object.assign({}, peerNames, { [peer.mac]: name })
        return true
    }

    function run(args, label) {
        if (busy || shuttingDown) return
        message = label
        failed = false
        cancelled = false
        operation = args[0]
        choosing = args.includes("--pick")
        action.command = cliCommand.concat(args)
        action.running = true
        if (choosing) popupOpen = false
    }

    function cancel() {
        if (!busy) return
        cancelled = true
        message = Translation.tr("Cancelling…")
        action.signal(15)
    }

    onPopupOpenChanged: {
        if (popupOpen) {
            namesMisses = 0
            popupCreated = true
            refresh()
            if (!doctor.running) doctor.running = true
        }
    }
    onReceivingChanged: {
        if (!receiving) { peers = []; peerNames = ({}) }
    }
    onScanningChanged: {
        if (scanning) {
            namesTimer.interval = 250
            namesTimer.restart()
        } else {
            namesTimer.stop()
            if (namesProcess.running) { namesProcess.stopped = true; namesProcess.signal(15) }
            if (peersProcess.running) peersProcess.signal(15)
        }
    }
    Component.onCompleted: { refresh(); doctor.running = true }
    Component.onDestruction: {
        shuttingDown = true
        if (action.running) action.signal(15)
        if (namesProcess.running) namesProcess.signal(15)
    }

    Timer {
        interval: root.popupOpen || root.receiving ? 2000 : 15000
        running: true
        repeat: true
        onTriggered: root.refresh()
    }
    Process {
        id: stateProcess
        command: root.cliCommand.concat(["status", "--json"])
        stdout: StdioCollector { waitForEnd: true; id: stateOutput }
        stderr: StdioCollector {}
        onExited: code => {
            if (root.shuttingDown) return
            try {
                if (code !== 0) throw new Error(code === 127
                    ? Translation.tr("Install and set up Omdrop to use AirDrop. See docs/airdrop.md.")
                    : Translation.tr("Cannot read AirDrop status"))
                root.status = root.parseStatus(stateOutput.text)
                root.stateKnown = true
                root.stateError = ""
            } catch (error) {
                root.stateKnown = false
                root.stateError = String(error)
            }
        }
    }
    Process {
        id: doctor
        command: root.cliCommand.concat(["doctor", "--json"])
        stdout: StdioCollector { waitForEnd: true; id: doctorOutput }
        onExited: code => {
            if (root.shuttingDown) return
            try {
                const report = JSON.parse(doctorOutput.text)
                root.ready = code === 0 && report.ready === true
                root.prerequisite = root.ready ? "" : (report.missing ?? []).map(item => item.say).join("\n")
                if (!root.ready && !root.prerequisite) root.prerequisite = Translation.tr("Check the AirDrop backend installation")
            } catch (error) {
                root.ready = false
                root.prerequisite = Translation.tr("Install and set up Omdrop to use AirDrop. See docs/airdrop.md.")
            }
        }
    }
    Process {
        id: action
        property string errorText: ""
        onStarted: errorText = ""
        stdout: SplitParser {
            onRead: line => {
                if (root.shuttingDown) return
                if (!line.trim()) return
                root.message = line.trim().slice(-1000)
                if (root.choosing) { root.choosing = false; root.popupOpen = true }
            }
        }
        stderr: SplitParser {
            onRead: line => {
                if (root.shuttingDown) return
                if (!line.trim()) return
                action.errorText = line.trim().slice(-1000)
                root.message = action.errorText
            }
        }
        onExited: code => {
            if (root.shuttingDown) return
            const chooserCancelled = root.choosing && code === 1 && !errorText
            root.failed = code !== 0 && !root.cancelled && !chooserCancelled
            root.message = root.cancelled ? Translation.tr("Cancelled")
                : root.failed ? (errorText || `${Translation.tr("AirDrop failed")} (${code})`)
                : code !== 0 ? Translation.tr("Operation cancelled")
                : root.operation === "send" ? Translation.tr("Transfer complete") : ""
            if (root.choosing || root.failed) root.popupOpen = true
            root.choosing = false
            root.refresh()
        }
    }
    Timer {
        interval: 3000
        running: root.scanning
        repeat: true
        triggeredOnStart: true
        onTriggered: if (!peersProcess.running) peersProcess.running = true
    }
    Process {
        id: peersProcess
        command: root.cliCommand.concat(["peers", "--json"])
        stdout: StdioCollector { waitForEnd: true; id: peersOutput }
        onExited: code => {
            if (root.shuttingDown) return
            if (code !== 0 || !root.scanning) return
            try {
                const peers = root.parsePeers(peersOutput.text)
                const appeared = peers.some(peer => !root.peers.some(known => known.mac === peer.mac))
                root.peers = peers
                if (appeared && root.namesMisses < 2 && root.namesWanted && !namesProcess.running) {
                    namesTimer.interval = 250
                    namesTimer.restart()
                }
            } catch (error) {
                root.message = String(error); root.failed = true
            }
        }
    }
    Timer {
        id: namesTimer
        // ponytail: two fruitless lookups back off globally for this popup.
        // Per-peer retry counters are unnecessary until this conservative cap is limiting.
        interval: 5000
        onTriggered: if (root.scanning && !namesProcess.running) namesProcess.running = true
    }
    Process {
        id: namesProcess
        property var namesBefore: ({})
        property bool learnt: false
        property bool stopped: false
        onStarted: { namesBefore = root.peerNames; learnt = false; stopped = false }
        command: root.cliCommand.concat(["peers", "--json", "-n", "--stream"])
        stdout: SplitParser {
            onRead: line => {
                if (root.shuttingDown) return
                try {
                    const values = root.parsePeers(`[${line}]`)
                    if (values.length && root.learnPeerName(values[0])) namesProcess.learnt = true
                } catch (error) { /* A terminated lookup can end with a partial line. */ }
            }
        }
        onExited: code => {
            if (root.shuttingDown) return
            if (code !== 0 && root.receiving) root.peerNames = namesBefore
            if (!stopped) root.namesMisses = code === 0 && learnt ? 0 : Math.min(2, root.namesMisses + 1)
            if (root.scanning) {
                namesTimer.interval = root.namesMisses >= 2 || !root.namesWanted ? 60000 : code !== 0 ? 10000 : 250
                namesTimer.restart()
            }
        }
    }
    // ponytail: create after the bar is mapped, then retain the native window.
    // Focus callbacks hide it; they must not destroy their own Wayland surface.
    Loader {
        objectName: "omdropPopupLoader"
        active: root.popupCreated
        sourceComponent: OmdropPopup {
            backend: root
            anchorTarget: root
            onDismissed: if (!root.shuttingDown) root.popupOpen = false
        }
    }
}
