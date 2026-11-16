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
    property bool profilesAvailable: false
    property bool darkeningAvailable: false
    property bool uniformDarkeningAvailable: false
    property bool contrastAvailable: false
    property bool barVisibilityAvailable: false
    property var barVisibility: ({})
    property real barVisibilitySerial: 0
    property var clockVisibility: ({})
    property real clockVisibilitySerial: 0

    function receiveClockVisibility(data) {
        const fields = data.split(",")
        if (fields.length !== 4 || fields[0] !== String(Quickshell.processId)
            || fields[1].length === 0 || fields[1].length > 128 || /[\x00-\x1f,]/.test(fields[1])
            || !["0", "1"].includes(fields[2]) || !/^[0-9]+$/.test(fields[3])) return
        const serial = Number(fields[3])
        if (!Number.isSafeInteger(serial) || serial <= root.clockVisibilitySerial) return
        root.clockVisibilitySerial = serial
        const visibility = Object.assign({}, root.clockVisibility)
        visibility[fields[1]] = fields[2] === "1"
        root.clockVisibility = visibility
    }

    function receiveBarVisibility(data) {
        const fields = data.split(",")
        if (fields.length !== 4 || fields[0] !== String(Quickshell.processId)
            || fields[1].length === 0 || fields[1].length > 128 || /[\x00-\x1f,]/.test(fields[1])
            || !["0", "1"].includes(fields[2]) || !/^[0-9]+$/.test(fields[3])) return
        const serial = Number(fields[3])
        if (!Number.isSafeInteger(serial) || serial <= root.barVisibilitySerial) return
        root.barVisibilitySerial = serial
        const visibility = Object.assign({}, root.barVisibility)
        visibility[fields[1]] = fields[2] === "1"
        root.barVisibility = visibility
    }
    function receiveBarSnapshot(data) {
        const sample = JSON.parse(data)
        if (!Number.isSafeInteger(sample?.serial) || sample.serial < root.barVisibilitySerial
            || !sample.bars || typeof sample.bars !== "object" || Array.isArray(sample.bars)
            || Object.entries(sample.bars).some(([name, visible]) => name.length === 0 || name.length > 128
                || /[\x00-\x1f,]/.test(name) || typeof visible !== "boolean")) return
        root.barVisibilitySerial = sample.serial
        root.barVisibility = sample.bars
        if (sample.serial >= root.clockVisibilitySerial && sample.clocks && !Array.isArray(sample.clocks)
            && typeof sample.clocks === "object" && Object.entries(sample.clocks).every(([name, visible]) =>
                name.length > 0 && name.length <= 128 && !/[\x00-\x1f,]/.test(name) && typeof visible === "boolean")) {
            root.clockVisibility = sample.clocks
            root.clockVisibilitySerial = sample.serial
        }
    }
    Socket {
        id: barVisibilitySocket
        path: regionSocket.path
        property bool receivedReply: false
        onConnectionStateChanged: if (connected) { receivedReply = false; write("/end4barvisibility"); flush() }
        onError: if (!receivedReply) { root.barVisibility = ({}); root.clockVisibility = ({}) }
        parser: SplitParser {
            onRead: data => {
                try { root.receiveBarSnapshot(data); barVisibilitySocket.receivedReply = true }
                catch (error) { console.warn("[GlassCompositor] Invalid bar visibility snapshot", error) }
            }
        }
    }
    property var contrastSamples: []
    property int contrastTick: 0
    readonly property bool contrastActive: enhancedActive && contrastAvailable && Config.options.background.widgets.glass.elements.settings.enable && GlobalStates.settingsOpen
        && Config.options.settings.style !== "dashboard"

    readonly property var contrastMaterialSnapshot: {
        if (!contrastActive || !uniformDarkeningAvailable || !Config.options.background.widgets.glass.elements.settings.automaticDarkening)
            return {regions: []}
        // Share geometry across labels; palette changes must not remap every box for every text update.
        return {tick: contrastTick,
            regions: glassItems.map(item => item?.nativeRegion()).filter(region => !!region)}
    }

    function foreground(item, base, previous) {
        if (!contrastActive || !item.visible || item.QsWindow.window?.WlrLayershell.namespace !== "quickshell:settings") return base
        const win = item.QsWindow.window
        const sample = contrastSamples.find(s => s.monitor === win.screen?.name
            && Math.abs(s.width - win.width) <= 2 && Math.abs(s.height - win.height) <= 2)
        if (!sample) return base
        const box = item.mapToItem(win.contentItem, Qt.rect(0, 0, item.width, item.height))
        let luminance = localLuminance(sample, box)
        if (luminance < 0) return base
        const dimming = darkeningAvailable ? Config.options.background.widgets.glass.elements.settings
            : {darkening: 0, automaticDarkening: false}
        // ponytail: luma-only samples are approximated as grey; exact coloured contrast needs RGB samples.
        const encode = value => value <= .0031308 ? value * 12.92 : 1.055 * Math.pow(value, 1 / 2.4) - .055
        const encoded = encode(luminance)
        let reference = encoded
        if (dimming.automaticDarkening && uniformDarkeningAvailable) {
            let material = Qt.rect(0, 0, win.width, win.height), priority = -Infinity, area = Infinity
            const cx = box.x + box.width / 2, cy = box.y + box.height / 2
            for (const region of contrastMaterialSnapshot.regions) {
                if (region.win !== win) continue
                const [x, y, w, h] = region.values
                if (cx < x || cy < y || cx > x+w || cy > y+h) continue
                if (region.priority > priority || (region.priority === priority && w*h < area)) {
                    material = Qt.rect(x,y,w,h); priority = region.priority; area = w*h
                }
            }
            let brightest = -1
            for (let y = 0; y < 2; ++y) for (let x = 0; x < 2; ++x) {
                const value = localLuminance(sample, Qt.rect(material.x + material.width * (x*.5+.25), material.y + material.height * (y*.5+.25), 0, 0))
                if (value >= 0) brightest = Math.max(brightest, encode(value))
            }
            if (brightest >= 0) reference = brightest
        }
        const darkness = dimming.automaticDarkening ? Math.max(0, 1 - .38 / Math.max(reference, .38))
            : Math.max(0, Math.min(100, dimming.darkening)) / 100
        const shaded = encoded * (1 - darkness)
        luminance = shaded <= .04045 ? shaded / 12.92 : Math.pow((shaded + .055) / 1.055, 2.4)
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
                surface.regions.push(region)
            }
        }
        const values = ["end4glass", Quickshell.processId, enhancedActive ? (frostedAvailable ? 2 : 1) : 0, surfaces.length]
        for (const surface of surfaces) {
            // Modal materials cover underlying cards; preserve nesting within each priority.
            surface.regions.sort((a, b) => a.priority - b.priority
                || b.values[2] * b.values[3] - a.values[2] * a.values[3])
            if (surface.regions.length > 32 || /\s/.test(surface.name + surface.monitor)) return
            values.push(surface.name, surface.monitor, surface.width, surface.height, surface.regions.length)
            for (const region of surface.regions) values.push(...region.values)
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

    function ipcRequest(command) {
        const request = "/" + command
        // ponytail: Hyprland 0.55 reads 1023-byte blocks synchronously; avoid a full final block.
        // Replace this padding with a write-half-close when Quickshell Socket supports it.
        const bytes = encodeURIComponent(request).replace(/%[0-9A-F]{2}/g, "_").length
        return request + (bytes % 1023 === 0 ? " " : "")
    }

    Socket {
        id: regionSocket
        path: Quickshell.env("XDG_RUNTIME_DIR") + "/hypr/" + Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") + "/.socket.sock"
        onConnectionStateChanged: {
            if (connected) { write(root.ipcRequest(root.regionsSent)); flush() }
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

    property string profilesSent: ""
    property string profilesApplied: ""
    property bool profilesBusy: false
    function sendProfiles() {
        if (!profilesAvailable || profilesBusy) return
        const values = ["end4profiles", Quickshell.processId, enhancedActive ? 1 : 0, GlassProfiles.keys.length]
        for (const key of GlassProfiles.keys) values.push(key, GlassProfiles.profile(key).enable ? 1 : 0, ...GlassProfiles.optics(key))
        if (darkeningAvailable) {
            values.push("darkening", active ? 1 : 0)
            for (const key of GlassProfiles.keys) {
                const p = GlassProfiles.profile(key)
                values.push(key, Number.isFinite(p.darkening) ? Math.max(0, Math.min(100, p.darkening)) / 100 : 0, p.automaticDarkening ? 1 : 0)
            }
        }
        const command = values.join(" ")
        if (command === profilesApplied) return
        profilesSent = command
        profilesBusy = true
        profilesSocket.connected = true
    }
    Socket {
        id: profilesSocket
        path: regionSocket.path
        onConnectionStateChanged: {
            if (connected) { write(root.ipcRequest(root.profilesSent)); flush() }
            else { root.profilesBusy = false; if (root.profilesApplied === root.profilesSent) Qt.callLater(root.sendProfiles) }
        }
        onError: { root.profilesBusy = false; console.warn("[GlassCompositor] Profile socket error", error) }
        parser: SplitParser {
            onRead: data => {
                if (data.trim() === "ok") root.profilesApplied = root.profilesSent
                else console.warn("[GlassCompositor] Profiles rejected:", data.trim())
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
            "keyword plugin:hyprglass:layers:namespaces " + namespaces.filter(name => GlassProfiles.enabledFor(name)).join(","),
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
        const owner = "hyprglass_owner_" + Quickshell.processId
        const tagCommand = (tag, address) => root.lua
            ? "eval hl.dispatch(hl.dsp.window.tag({tag=" + JSON.stringify(tag) + ",window=" + JSON.stringify("address:" + address) + "}))"
            : "dispatch tagwindow " + tag + " address:" + address
        for (const client of HyprlandData.windowList) {
            const terminal = ["kitty", "foot", "footclient", "alacritty", "org.wezfurlong.wezterm", "wezterm", "org.kde.konsole", "konsole"].includes((client.class ?? "").toLowerCase())
            for (const tag of client.tags ?? [])
                if (tag.startsWith("hyprglass_owner_") && tag !== owner) commands.push(tagCommand("-" + tag, client.address))
            const owned = client.tags?.includes(owner) ?? false
            const terminalWanted = active && enhancedActive && profilesAvailable && glass.elements.terminal.enable && terminal
            if (owned !== terminalWanted) commands.push(tagCommand((terminalWanted ? "+" : "-") + owner, client.address))
            if (client.pid !== Quickshell.processId) continue
            const tagged = client.tags?.includes("hyprglass_enabled") ?? false
            const wanted = active && glass.elements.settings.enable && windowFrostedAvailable && client.title === "illogical-impulse Settings"
            if (tagged !== wanted) commands.push(tagCommand((wanted ? "+" : "-") + "hyprglass_enabled", client.address))
        }
        sendProfiles()
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
        GlassProfiles.signature, Config.options.background.widgets.glass.enhanced, root.profilesAvailable, root.darkeningAvailable,
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
        function geometry(): string { return root.regionsApplied }
        function status(): string {
            return JSON.stringify({ enabled: root.enabled, available: root.available, active: root.active,
                reason: root.reason, lua: root.lua, pending: applyTimer.running, updating: updater.running,
                writes: root.configurationWrites, captures: GlassLayers.backdropConsumers,
                requested: root.enabled, locked: GlobalStates.screenLocked,
                enhanced: root.enhancedActive, enhancedRequested: Config.options.background.widgets.glass.enhanced,
                enhancedAvailable: root.enhancedAvailable, frostedAvailable: root.frostedAvailable,
                profilesAvailable: root.profilesAvailable, windowFrostedAvailable: root.windowFrostedAvailable, contrastAvailable: root.contrastAvailable, regionWrites: root.regionWrites })
        }
    }

    Timer { id: applyTimer; interval: 150; onTriggered: root.configure() }
    Connections {
        target: Hyprland
        enabled: !root.disabled
        function onRawEvent(event) {
            if (event.name === "end4barvisibility") { root.receiveBarVisibility(event.data); return }
            if (event.name === "end4clockvisibility") { root.receiveClockVisibility(event.data); return }
            if (event.name !== "configreloaded") return
            root.appliedCommand = ""
            root.profilesApplied = ""
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
                    root.profilesAvailable = result.profiles ?? false
                    root.darkeningAvailable = result.darkening ?? false
                    root.uniformDarkeningAvailable = result.uniformDarkening ?? false
                    root.contrastAvailable = result.contrast ?? false
                    root.barVisibilityAvailable = result.barVisibility ?? false
                    if (root.barVisibilityAvailable && !barVisibilitySocket.connected) barVisibilitySocket.connected = true
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
