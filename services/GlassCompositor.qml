pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Wayland
import qs
import qs.modules.common
import qs.services

Singleton {
    id: root
    readonly property bool disabled: Quickshell.env("QS_DISABLE_COMPOSITOR_GLASS") === "1"
    readonly property bool enabled: !disabled && WM.compositor === "hyprland"
        && Config.options.background.widgets.glass.enable && Config.options.background.widgets.glass.source === "windows"
        && !GlobalStates.screenLocked
    readonly property var namespaces: ["bar", "verticalBar", "dock", "popup", "popupMorph", "settings",
        "sidebarLeft", "sidebarRight", "wallpaperSelector", "airdrop", "desktopMenu", "dropshelf",
        "onScreenDisplay", "overview", "mediaControls", "notificationPopup", "equalizer", "osk"]
        .map(name => "quickshell:" + name)
    property bool available: false
    property bool enhancedAvailable: false
    property bool frostedAvailable: false
    property bool windowFrostedAvailable: false
    property bool contrastAvailable: false
    property var contrastSamples: []
    property int contrastTick: 0
    readonly property bool contrastActive: enhancedActive && contrastAvailable && GlobalStates.settingsOpen
        && Config.options.settings.style !== "dashboard"

    function foreground(item, base, previous) {
        if (!contrastActive || !item.visible || item.QsWindow.window?.WlrLayershell.namespace !== "quickshell:settings") return base
        const win = item.QsWindow.window
        const sample = contrastSamples.find(s => s.monitor === win.screen?.name
            && Math.abs(s.width - win.width) <= 2 && Math.abs(s.height - win.height) <= 2)
        if (!sample) return base
        const box = item.mapToItem(win.contentItem, Qt.rect(0, 0, item.width, item.height))
        const luminance = localLuminance(sample, box)
        if (luminance < 0) return base
        const light = Qt.rgba(231 / 255, 237 / 255, 242 / 255, base.a)
        const dark = Qt.rgba(27 / 255, 34 / 255, 41 / 255, base.a)
        const linear = v => v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4)
        const ratio = color => {
            const ink = .2126 * linear(color.r) + .7152 * linear(color.g) + .0722 * linear(color.b)
            return (Math.max(ink, luminance) + .05) / (Math.min(ink, luminance) + .05)
        }
        const lightRatio = ratio(light), darkRatio = ratio(dark)
        // Keep one ink for the whole label; hysteresis avoids oscillation near equal contrast.
        const wasDark = previous && previous.r < .2
        const currentRatio = wasDark ? darkRatio : lightRatio
        const otherRatio = wasDark ? lightRatio : darkRatio
        const switchInk = (currentRatio < 4.5 && otherRatio >= 4.5) || otherRatio > currentRatio * 1.15
        const darkInk = switchInk ? !wasDark : wasDark
        return darkInk ? dark : light
    }

    function localLuminance(sample, box) {
        const [x, y, w, h] = sample.rect
        const cx = box.x + box.width / 2, cy = box.y + box.height / 2
        if (cx < x || cy < y || cx > x + w || cy > y + h) return -1
        const col = Math.max(0, Math.min(sample.columns - 1, Math.floor((cx - x) / w * sample.columns)))
        const row = Math.max(0, Math.min(sample.rows - 1, Math.floor((cy - y) / h * sample.rows)))
        let total = 0, count = 0
        for (let j = Math.max(0, row - 1); j <= Math.min(sample.rows - 1, row + 1); ++j)
            for (let i = Math.max(0, col - 1); i <= Math.min(sample.columns - 1, col + 1); ++i) {
                total += sample.luma[j * sample.columns + i] / 255
                ++count
            }
        return total / count
    }

    function validContrast(sample) {
        return sample?.name === "quickshell:settings" && typeof sample.monitor === "string"
            && Number.isFinite(sample.width) && sample.width > 0 && Number.isFinite(sample.height) && sample.height > 0
            && Array.isArray(sample.rect) && sample.rect.length === 4 && sample.rect.every(Number.isFinite)
            && sample.rect[2] > 0 && sample.rect[3] > 0 && sample.columns === 32 && sample.rows === 24
            && Array.isArray(sample.luma) && sample.luma.length === 768
            && sample.luma.every(v => Number.isInteger(v) && v >= 0 && v <= 255)
    }

    onContrastActiveChanged: if (!contrastActive) contrastSamples = []
    Timer {
        interval: 1250; repeat: true; triggeredOnStart: true
        running: root.contrastActive
        onTriggered: if (!contrastSocket.connected) contrastSocket.connected = true
    }
    Socket {
        id: contrastSocket
        property bool receivedReply: false
        path: regionSocket.path
        onConnectionStateChanged: if (connected) { receivedReply = false; write("/end4contrast"); flush() }
        // Hyprland closes each IPC connection after replying; that close must retain the sample.
        onError: if (!receivedReply || !connected) { root.contrastSamples = []; root.contrastTick++ }
        parser: SplitParser {
            onRead: data => {
                try {
                    const samples = JSON.parse(data)
                    if (!Array.isArray(samples) || samples.length > 32 || !samples.every(root.validContrast)) throw new Error("Invalid contrast samples")
                    contrastSocket.receivedReply = true
                    root.contrastSamples = root.contrastActive ? samples : []
                } catch (error) { root.contrastSamples = [] }
                root.contrastTick++
            }
        }
    }
    readonly property bool enhancedActive: active && enhancedAvailable && Config.options.background.widgets.glass.enhanced
    property var glassItems: []
    property bool regionsPending: false
    property bool regionsBusy: false
    property string regionsApplied: ""
    property string regionsSent: ""
    property string regionsRejected: ""
    property int regionWrites: 0
    property bool lua: false
    property string reason: ""
    property string appliedCommand: ""
    property string pendingCommand: ""
    property int configurationWrites: 0
    readonly property bool active: enabled && available

    function registerGlass(item) {
        glassItems = glassItems.concat([item])
        queueRegions()
    }
    function unregisterGlass(item) {
        glassItems = glassItems.filter(other => other && other !== item)
        queueRegions()
    }
    function queueRegions() {
        if (!enhancedAvailable || regionsPending) return
        regionsPending = true
        Qt.callLater(root.sendRegions)
    }
    function sendRegions() {
        regionsPending = false
        if (!enhancedAvailable || regionsBusy) return
        const surfaces = []
        if (enhancedActive) {
            for (const item of glassItems) {
                if (!item) continue
                const region = item.nativeRegion()
                if (!region) continue
                let surface = surfaces.find(entry => entry.win === region.win)
                if (!surface) {
                    surface = { win: region.win, name: region.name, monitor: region.monitor,
                        width: region.win.width, height: region.win.height, regions: [] }
                    surfaces.push(surface)
                }
                surface.regions.push(region.values)
            }
        }
        const values = ["end4glass", Quickshell.processId, enhancedActive ? (frostedAvailable ? 2 : 1) : 0, surfaces.length]
        for (const surface of surfaces) {
            // Larger backgrounds first: nested cards keep their own edge geometry.
            surface.regions.sort((a, b) => b[2] * b[3] - a[2] * a[3])
            if (surface.regions.length > 32 || /\s/.test(surface.name + surface.monitor)) return
            values.push(surface.name, surface.monitor, surface.width, surface.height, surface.regions.length)
            for (const region of surface.regions) values.push(...region)
        }
        const command = values.join(" ")
        if (command === regionsApplied || command === regionsRejected || command.length > 32768) return
        regionsSent = command
        regionsBusy = true
        regionWrites++
        regionSocket.connected = true
    }
    onEnhancedActiveChanged: queueRegions()
    onEnhancedAvailableChanged: queueRegions()
    onFrostedAvailableChanged: queueRegions()
    onWindowFrostedAvailableChanged: { queueRegions(); applyTimer.restart() }

    Socket {
        id: regionSocket
        path: Quickshell.env("XDG_RUNTIME_DIR") + "/hypr/" + Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") + "/.socket.sock"
        onConnectionStateChanged: {
            if (connected) { write("/" + root.regionsSent); flush() }
            else { root.regionsBusy = false; root.queueRegions() }
        }
        onError: {
            if (root.regionsSent !== root.regionsApplied) {
                root.regionsRejected = root.regionsSent
                console.warn("[GlassCompositor] Geometry socket error", error)
            }
            root.regionsBusy = false
        }
        parser: SplitParser {
            onRead: data => {
                if (data.trim() === "ok") root.regionsApplied = root.regionsSent
                else {
                    root.regionsRejected = root.regionsSent
                    console.warn("[GlassCompositor] Geometry rejected:", data.trim())
                }
            }
        }
    }

    function probe() {
        if (disabled || WM.compositor !== "hyprland" || detector.running) return
        detector.command = ["python3", Quickshell.shellPath("scripts/glass/native/backend.py")].concat(enabled ? ["--ensure"] : [])
        detector.running = true
    }

    function configure() {
        if (!available || disabled) return
        const glass = Config.options.background.widgets.glass
        const commands = [
            "keyword plugin:hyprglass:enabled 0",
            "keyword plugin:hyprglass:layers:enabled " + (active ? 1 : 0),
            "keyword plugin:hyprglass:layers:namespaces " + namespaces.join(","),
            "keyword plugin:hyprglass:layers:namespace_mask_thresholds " + namespaces.map(name => name + "=0.03").join(","),
            "keyword plugin:hyprglass:default_theme " + (Appearance.m3colors.darkmode ? "dark" : "light"),
            "keyword plugin:hyprglass:brightness 1",
            "keyword plugin:hyprglass:contrast 1",
            "keyword plugin:hyprglass:adaptive_dim 0",
            "keyword plugin:hyprglass:adaptive_boost 0",
            "keyword plugin:hyprglass:vibrancy 0",
            "keyword plugin:hyprglass:vibrancy_darkness 0",
            "keyword plugin:hyprglass:blur_strength " + Math.max(0.05, Math.min(4, glass.haze / 4)),
            "keyword plugin:hyprglass:blur_iterations 1",
            "keyword plugin:hyprglass:refraction_strength " + Math.max(0, Math.min(1, glass.pull / 80)),
            "keyword plugin:hyprglass:chromatic_aberration " + Math.max(0, Math.min(1, glass.split)),
            "keyword plugin:hyprglass:specular_strength " + Math.max(0, Math.min(1, glass.sheen)),
            "keyword plugin:hyprglass:saturation " + Math.max(0, Math.min(2, glass.vividness)),
            "keyword plugin:hyprglass:glass_opacity 1"
        ]
        const tint = glass.tint === "transparent" ? Qt.rgba(0, 0, 0, 0) : Appearance.getColorFromName(glass.tint)
        const channel = value => Math.round(Math.max(0, Math.min(1, value)) * 255).toString(16).padStart(2, "0")
        commands.push("keyword plugin:hyprglass:tint_color 0x" + channel(tint.r) + channel(tint.g) + channel(tint.b) + channel(glass.tint === "transparent" ? 0 : glass.tintStrength))
        commands.push("keyword plugin:hyprglass:edge_thickness " + Math.max(0, Math.min(0.15, glass.rimWidth / 400)))
        for (const client of HyprlandData.windowList) {
            if (client.pid !== Quickshell.processId) continue
            const tagged = client.tags?.includes("hyprglass_enabled") ?? false
            const wanted = active && windowFrostedAvailable && client.title === "illogical-impulse Settings"
            if (tagged !== wanted) {
                const tag = (wanted ? "+" : "-") + "hyprglass_enabled"
                commands.push(root.lua
                    ? "eval hl.dispatch(hl.dsp.window.tag({tag=" + JSON.stringify(tag) + ",window=" + JSON.stringify("address:" + client.address) + "}))"
                    : "dispatch tagwindow " + tag + " address:" + client.address)
            }
        }
        let batch = commands
        if (root.lua) {
            const values = commands.filter(command => command.startsWith("keyword ")).map(command => {
                const parts = command.split(" ")
                const key = parts[1].replace(/:/g, ".")
                const value = parts.slice(2).join(" ")
                return "[" + JSON.stringify(key) + "]=" + (Number.isFinite(Number(value)) ? value : JSON.stringify(value))
            })
            batch = ["eval hl.config({" + values.join(",") + "})"].concat(commands.filter(command => !command.startsWith("keyword ")))
        }
        const command = batch.join(";")
        if (command === root.appliedCommand) return
        if (updater.running) { applyTimer.restart(); return }
        root.pendingCommand = command
        updater.command = ["hyprctl", "--batch", command]
        root.configurationWrites++
        updater.running = true
    }

    readonly property string settings: JSON.stringify([
        Config.options.background.widgets.glass.haze, Config.options.background.widgets.glass.pull,
        Config.options.background.widgets.glass.split, Config.options.background.widgets.glass.sheen,
        Config.options.background.widgets.glass.vividness, Appearance.m3colors.darkmode,
        Config.options.background.widgets.glass.tint, Config.options.background.widgets.glass.tintStrength,
        Config.options.background.widgets.glass.rimWidth, String(Appearance.colors.colPrimary)
    ])
    onSettingsChanged: applyTimer.restart()
    onActiveChanged: applyTimer.restart()
    onEnabledChanged: { probe(); applyTimer.restart() }
    Component.onCompleted: probe()

    IpcHandler {
        target: "glass"
        function refresh(): void { root.probe() }
        function status(): string {
            return JSON.stringify({ enabled: root.enabled, available: root.available, active: root.active,
                reason: root.reason, lua: root.lua, pending: applyTimer.running, updating: updater.running,
                writes: root.configurationWrites, captures: GlassLayers.backdropConsumers,
                requested: root.enabled, locked: GlobalStates.screenLocked,
                enhanced: root.enhancedActive, enhancedRequested: Config.options.background.widgets.glass.enhanced,
                enhancedAvailable: root.enhancedAvailable, frostedAvailable: root.frostedAvailable,
                windowFrostedAvailable: root.windowFrostedAvailable, contrastAvailable: root.contrastAvailable, regionWrites: root.regionWrites })
        }
    }

    Timer { id: applyTimer; interval: 150; onTriggered: root.configure() }
    Connections {
        target: Hyprland
        enabled: !root.disabled
        function onRawEvent(event) {
            if (event.name !== "configreloaded") return
            root.appliedCommand = ""
            root.regionsApplied = ""
            root.regionsRejected = ""
            root.queueRegions()
            root.probe()
            if (!applyTimer.running) applyTimer.start()
        }
    }
    Connections {
        target: HyprlandData
        function onWindowListChanged() { if (!applyTimer.running) applyTimer.start() }
    }
    Process {
        id: detector
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const result = JSON.parse(text)
                    root.lua = result.lua ?? false
                    root.available = result.available
                    root.enhancedAvailable = result.enhanced ?? false
                    root.frostedAvailable = result.frosted ?? false
                    root.windowFrostedAvailable = result.windowFrosted ?? false
                    root.contrastAvailable = result.contrast ?? false
                    root.reason = result.reason
                    if (root.available) applyTimer.restart()
                } catch (error) { root.available = false; root.reason = String(error) }
            }
        }
    }
    Process {
        id: updater
        stdout: StdioCollector {
            onStreamFinished: {
                if (text.trim().split("\n").some(line => line.trim() && line.trim() !== "ok")) {
                    console.warn("[GlassCompositor]", text.trim())
                } else if (text.trim()) {
                    root.appliedCommand = root.pendingCommand
                }
            }
        }
    }
}
