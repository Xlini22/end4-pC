import QtQuick
import QtQml
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs
import qs.services
import qs.modules.common

Item {
    id: root
    property real cardRadius: 0
    property real topLeftRadius: cardRadius
    property real topRightRadius: cardRadius
    property real bottomRightRadius: cardRadius
    property real bottomLeftRadius: cardRadius
    property color tint: "transparent"
    property bool glassEnabled: true
    property bool fullscreenSurface: false
    property real tintStrength: 0
    property real frost: 0
    property real flareLeft: 0
    property real flareRight: 0
    property real hangLeft: 0
    property real hangRight: 0
    property int edge: 0
    readonly property bool live: glassEnabled && (Config.options?.background?.widgets?.glass?.enable ?? false)
    readonly property bool tracking: live && visible && (win?.visible ?? true)
    readonly property bool windowBackdrop: live && Config.options.background.widgets.glass.source === "windows"
        && WM.compositor === "hyprland" && !GlobalStates.screenLocked && !fullscreenSurface
        && !!win && (floating || popup || win.WlrLayershell.layer >= WlrLayer.Top)
    readonly property bool nativeGlass: windowBackdrop && GlassCompositor.active
        && (floating ? win.title === "illogical-impulse Settings"
            : !popup && GlassCompositor.namespaces.includes(win.WlrLayershell.namespace))
    // ponytail: rotated layer outputs retain standard glass until card geometry also carries output transforms.
    readonly property bool enhancedNative: nativeGlass && GlassCompositor.enhancedActive
        && (root.floating || (root.backdropMonitor?.lastIpcObject?.transform ?? 0) === 0)
    readonly property bool clearMaterial: !!win && !floating && !popup
        && ["quickshell:bar", "quickshell:verticalBar"].includes(win.WlrLayershell.namespace)
    readonly property bool wantsBackdropTracking: windowBackdrop && tracking && !nativeGlass
    readonly property var backdropMonitor: windowBackdrop && win?.screen ? Hyprland.monitorFor(win.screen) : null
    readonly property int specialWorkspace: backdropMonitor?.lastIpcObject?.specialWorkspace?.id ?? 0

    readonly property var win: QsWindow.window
    readonly property var surfaceScreen: ({
        name: "",
        width: root.Window.width,
        height: root.Window.height,
        devicePixelRatio: root.Window.window?.devicePixelRatio ?? 1
    })
    readonly property var scr: win?.screen ?? (fullscreenSurface && root.Window.window ? surfaceScreen : null)
    readonly property bool floating: !fullscreenSurface && !!win && win.anchors === undefined && win.anchor === undefined
    readonly property bool popup: !fullscreenSurface && !!win && win.anchor !== undefined

    readonly property var floatPos: GlassFloating.positions[win?.title ?? ""] ?? null
    readonly property var floatMonitor: scr ? HyprlandData.monitors.find(m => m.name === scr.name) : null
    readonly property real floatX: floatPos ? floatPos.x - (floatMonitor?.x ?? 0) : 0
    readonly property real floatY: floatPos ? floatPos.y - (floatMonitor?.y ?? 0) : 0
    readonly property bool wantsFloatTracking: live && floating && !!win?.visible && !nativeGlass
    property bool claimed: false
    property bool backdropClaimed: false

    function syncClaim() {
        if (root.wantsBackdropTracking !== root.backdropClaimed) {
            GlassLayers.backdropConsumers += root.wantsBackdropTracking ? 1 : -1
            root.backdropClaimed = root.wantsBackdropTracking
        }
        if (root.wantsFloatTracking && !root.claimed) {
            GlassFloating.claim()
            root.claimed = true
        } else if (!root.wantsFloatTracking && root.claimed) {
            GlassFloating.release()
            root.claimed = false
        }
    }

    onWantsFloatTrackingChanged: syncClaim()
    onWantsBackdropTrackingChanged: syncClaim()
    Component.onDestruction: {
        GlassCompositor.unregisterGlass(root)
        if (root.claimed) GlassFloating.release()
        if (root.backdropClaimed) GlassLayers.backdropConsumers--
    }

    function nativeRegion() {
        if (!enhancedNative || !tracking || floating || width <= 0 || height <= 0 || !win?.screen) return null
        const rect = mapToItem(win.contentItem, Qt.rect(0, 0, width, height))
        if (rect.width <= 0 || rect.height <= 0) return null
        let opacity = root.opacity
        for (let item = parent; item; item = item.parent) opacity *= item.opacity
        if (opacity <= 0.001) return null
        const scale = Math.min(rect.width / width, rect.height / height)
        const radius = value => Math.max(0, Math.min(value * scale, rect.width / 2, rect.height / 2))
        const values = [rect.x, rect.y, rect.width, rect.height,
                radius(topLeftRadius), radius(topRightRadius), radius(bottomRightRadius), radius(bottomLeftRadius),
                flareLeft * scale, flareRight * scale, hangLeft * scale, hangRight * scale, edge, opacity]
        if (GlassCompositor.frostedAvailable) values.push(Math.max(0, Math.min(32, frost)) * scale)
        return { win, name: win.WlrLayershell.namespace, monitor: win.screen.name,
            values: values.map(value => Math.round(value * 1000) / 1000) }
    }
    readonly property string nativeShape: JSON.stringify([topLeftRadius, topRightRadius, bottomRightRadius,
        bottomLeftRadius, flareLeft, flareRight, hangLeft, hangRight, edge, root.opacity, frost])
    onNativeShapeChanged: GlassCompositor.queueRegions()
    onEnhancedNativeChanged: GlassCompositor.queueRegions()

    function windowVisible(client, workspace, special, processId) {
        return !!client && client.mapped && !client.hidden && client.pid !== processId
            && client.size?.[0] > 0 && client.size?.[1] > 0
            && (client.pinned || client.workspace?.id === workspace || (special !== 0 && client.workspace?.id === special))
    }

    function windowIntersects(client, monitorX, monitorY, rect) {
        return !!client?.at && client.at[0] - monitorX < rect.x + rect.width
            && client.at[1] - monitorY < rect.y + rect.height
            && client.at[0] - monitorX + client.size[0] > rect.x
            && client.at[1] - monitorY + client.size[1] > rect.y
    }

    function windowOrder(client, special) {
        // ponytail: export supplies application surfaces, not compositor decorations or layer-shell panels.
        // Focus history orders overlapping peers; exact compositor stacking requires a compositor-side effect.
        return (special !== 0 && client?.workspace?.id === special ? 300000 : 0)
            + (client?.fullscreen ? 200000 : client?.floating ? 100000 : 0)
            - (client?.focusHistoryID >= 0 ? client.focusHistoryID : 99999)
    }

    function panelOffset(w, s) {
        const a = w.anchors
        const m = w.margins
        const pushed = w.exclusionMode !== ExclusionMode.Ignore
        const x = a?.left ? (m?.left ?? 0) + (pushed ? GlassLayers.leftZone : 0)
            : a?.right ? s.width - w.width - (m?.right ?? 0) - (pushed ? GlassLayers.rightZone : 0)
            : (s.width - w.width) / 2
        const y = a?.top ? (m?.top ?? 0) + (pushed ? GlassLayers.topZone : 0)
            : a?.bottom ? s.height - w.height - (m?.bottom ?? 0) - (pushed ? GlassLayers.bottomZone : 0)
            : (s.height - w.height) / 2
        return layerOffset(w, s, Qt.point(x, y))
    }

    function layerOffset(w, s, guess) {
        const mon = GlassLayers.layers[s.name]
        if (!mon) return guess
        const monitor = HyprlandData.monitors.find(m => m.name === s.name)
        const ox = monitor?.x ?? 0
        const oy = monitor?.y ?? 0
        let best = null
        let bestDist = Infinity
        for (const level of Object.values(mon.levels ?? {})) {
            for (const layer of level) {
                if (!layer.namespace.startsWith("quickshell:")) continue
                if (layer.w !== Math.round(w.width) || layer.h !== Math.round(w.height)) continue
                const dist = Math.abs(layer.x - ox - guess.x) + Math.abs(layer.y - oy - guess.y)
                if (dist < bestDist) {
                    bestDist = dist
                    best = layer
                }
            }
        }
        return best ? Qt.point(best.x - ox, best.y - oy) : guess
    }

    function popupOffset(w, s) {
        const an = w.anchor
        const host = an.window
        if (!host) return Qt.point(0, 0)
        const base = host.anchor !== undefined ? popupOffset(host, s) : panelOffset(host, s)
        let rx = an.rect.x, ry = an.rect.y, rw = an.rect.width, rh = an.rect.height
        if (an.item) {
            const p = an.item.mapToItem(null, 0, 0)
            rx = p.x; ry = p.y; rw = an.item.width; rh = an.item.height
        }
        const e = an.edges, g = an.gravity
        const ax = (e & Qt.LeftEdge) ? rx : (e & Qt.RightEdge) ? rx + rw : rx + rw / 2
        const ay = (e & Qt.TopEdge) ? ry : (e & Qt.BottomEdge) ? ry + rh : ry + rh / 2
        const gx = (g & Qt.LeftEdge) ? ax - w.width : (g & Qt.RightEdge) ? ax : ax - w.width / 2
        const gy = (g & Qt.TopEdge) ? ay - w.height : (g & Qt.BottomEdge) ? ay : ay - w.height / 2
        const x = Math.max(0, Math.min(base.x + gx, s.width - w.width))
        const y = Math.max(0, Math.min(base.y + gy, s.height - w.height))
        return Qt.point(x, y)
    }

    readonly property point winPos: {
        if (!live || !win || !scr) return Qt.point(0, 0)
        if (fullscreenSurface) return Qt.point(0, 0)
        if (floating) return Qt.point(floatX, floatY)
        if (popup) return popupOffset(win, scr)
        return panelOffset(win, scr)
    }
    readonly property real winX: winPos.x
    readonly property real winY: winPos.y

    property rect sceneRect: Qt.rect(0, 0, width, height)

    function refresh() {
        // ponytail: popup motion is axis-aligned; rotation would need transformed texture coordinates.
        const rect = mapToItem(null, Qt.rect(0, 0, width, height))
        if (rect.x !== sceneRect.x || rect.y !== sceneRect.y || rect.width !== sceneRect.width || rect.height !== sceneRect.height)
            sceneRect = rect
        if (enhancedNative) GlassCompositor.queueRegions()
    }

    function kick() {
        GlassCompositor.queueRegions()
        if (!tracking) return
        refresh()
        if (win && !floating && !fullscreenSurface && !nativeGlass) GlassLayers.refresh()
    }

    readonly property var ancestorGeometry: {
        if (!tracking) return []
        const sig = []
        for (let it = root; it; it = it.parent) {
            sig.push(it.x, it.y, it.width, it.height, it.scale, it.opacity)
            for (const transform of it.transform ?? [])
                sig.push(transform.x, transform.y, transform.xScale, transform.yScale,
                    transform.origin?.x, transform.origin?.y)
        }
        return sig
    }

    onAncestorGeometryChanged: { kick(); Qt.callLater(root.refresh) }
    onTrackingChanged: kick()
    onParentChanged: kick()
    onXChanged: kick()
    onYChanged: kick()
    onWidthChanged: kick()
    onHeightChanged: kick()
    onVisibleChanged: kick()
    Component.onCompleted: {
        GlassCompositor.registerGlass(root)
        syncClaim()
        kick()
    }

    Connections {
        target: root.win
        enabled: root.live
        function onWidthChanged() { root.kick() }
        function onHeightChanged() { root.kick() }
        function onVisibleChanged() { root.kick() }
        function onScreenChanged() { root.kick() }
    }

    Connections {
        target: root.Window.window
        enabled: root.tracking && !root.nativeGlass
        function onAfterAnimating() { root.refresh(); Qt.callLater(root.refresh) }
    }

    readonly property string wallpaper: {
        const lockWall = Config.options.background.lockWall ?? ""
        const path = GlobalStates.screenLocked && lockWall !== "" ? lockWall : Config.options.background.wallpaperPath
        return /\.(mp4|webm|mkv|avi|mov)$/.test(path) ? Config.options.background.thumbnailPath : path
    }

    Rectangle {
        anchors.fill: parent
        visible: root.nativeGlass
        color: root.enhancedNative ? Qt.rgba(0, 0, 0, (floating ? 0 : 16 / 255)) : Qt.rgba(root.tint.r, root.tint.g, root.tint.b, 0.08)
        topLeftRadius: root.topLeftRadius
        topRightRadius: root.topRightRadius
        bottomLeftRadius: root.bottomLeftRadius
        bottomRightRadius: root.bottomRightRadius
    }

    Loader {
        anchors.fill: parent
        active: root.tracking && !root.nativeGlass && !!root.scr && (root.wallpaper !== "" || root.windowBackdrop)

        sourceComponent: Item {
            Item {
                id: backdrop
                width: root.scr.width
                height: root.scr.height

                Image {
                    anchors.fill: parent
                    source: root.wallpaper !== "" ? "file://" + root.wallpaper : ""
                    fillMode: Image.PreserveAspectCrop
                    sourceSize: Qt.size(Math.ceil(root.scr.width * root.scr.devicePixelRatio), Math.ceil(root.scr.height * root.scr.devicePixelRatio))
                    asynchronous: true
                    cache: true
                    z: -1000000
                }

                Repeater {
                    model: root.wantsBackdropTracking ? ToplevelManager.toplevels : null
                    delegate: ScreencopyView {
                        required property var modelData
                        readonly property var client: HyprlandData.clientForToplevel(modelData)
                        readonly property bool included: root.windowVisible(client, root.backdropMonitor?.activeWorkspace?.id, root.specialWorkspace, Quickshell.processId)
                            && root.windowIntersects(client, root.backdropMonitor?.x ?? 0, root.backdropMonitor?.y ?? 0,
                                Qt.rect(root.winX + root.sceneRect.x, root.winY + root.sceneRect.y, root.sceneRect.width, root.sceneRect.height))
                        x: (client?.at?.[0] ?? 0) - (root.backdropMonitor?.x ?? 0)
                        y: (client?.at?.[1] ?? 0) - (root.backdropMonitor?.y ?? 0)
                        width: client?.size?.[0] ?? 0
                        height: client?.size?.[1] ?? 0
                        z: root.windowOrder(client, root.specialWorkspace)
                        captureSource: included ? modelData : null
                        live: true
                        visible: hasContent
                    }
                }
            }

            FrostedGlass {
                anchors.fill: parent
                blurSource: backdrop
                clearMaterial: root.clearMaterial
                frost: root.frost
                hideSource: true
                cardRadius: root.cardRadius
                topLeftRadius: root.topLeftRadius
                topRightRadius: root.topRightRadius
                bottomRightRadius: root.bottomRightRadius
                bottomLeftRadius: root.bottomLeftRadius
                tint: root.tint
                tintOpacity: root.tintStrength
                flareLeft: root.flareLeft
                flareRight: root.flareRight
                hangLeft: root.hangLeft
                hangRight: root.hangRight
                edge: root.edge
                sourceRect: Qt.rect(root.winX + root.sceneRect.x, root.winY + root.sceneRect.y, root.sceneRect.width, root.sceneRect.height)
            }
        }
    }
}
