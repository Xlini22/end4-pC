pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

Scope {
    id: bar
    property bool showBarBackground: Config.options.bar.showBackground

    Variants {
        // For each monitor
        model: {
            const screens = Quickshell.screens;
            const list = Config.options.bar.screenList;
            if (!list || list.length === 0)
                return screens;
            return screens.filter(screen => list.includes(screen.name));
        }
        LazyLoader {
            id: barLoader
            active: GlobalStates.barOpen && !GlobalStates.screenLocked && !GlobalStates.startupLockPending
            required property ShellScreen modelData
            component: PanelWindow { // Bar window
                id: barRoot
                screen: barLoader.modelData

                Timer {
                    id: showBarTimer
                    interval: (Config?.options.bar.autoHide.showWhenPressingSuper.delay ?? 100)
                    repeat: false
                    onTriggered: {
                        barRoot.superShow = true
                    }
                }
                Connections {
                    target: GlobalStates
                    function onSuperDownChanged() {
                        if (!Config?.options.bar.autoHide.showWhenPressingSuper.enable) return;
                        if (GlobalStates.superDown) showBarTimer.restart();
                        else {
                            showBarTimer.stop();
                            barRoot.superShow = false;
                        }
                    }
                }

                property bool showCorners: !Config.options.bar.autoHide.enable || mustShow

                Timer {
                    id: cornerRevealTimer
                    interval: 65
                    onTriggered: barRoot.showCorners = true
                }

                onMustShowChanged: {
                    if (!Config.options.bar.autoHide.enable) return;
                    if (mustShow) {
                        cornerRevealTimer.restart()
                    } else {
                        cornerRevealTimer.stop()
                        barRoot.showCorners = false
                    }
                }
                property bool superShow: false
                property bool mustShow: hoverRegion.containsMouse || superShow
                    || (Config.options.bar.autoHide.enable && GlobalStates.isFrameHovered(barRoot.screen?.name, Config.options.bar.bottom ? "bottom" : "top"))
                property var thisMonitorData: HyprlandData.monitors.find(m => m.name === barRoot.screen?.name)
                property bool monitorHasFullscreen: HyprlandData.workspaceById[thisMonitorData?.activeWorkspace?.id]?.hasfullscreen ?? false
                property bool monitorHasSpecialOpen: (thisMonitorData?.specialWorkspace?.name ?? "") !== ""
                readonly property var compositorBarVisible: GlassCompositor.barVisibility[barRoot.screen?.name ?? ""]
                readonly property bool fullscreenCoversBar: typeof compositorBarVisible === "boolean"
                    ? !compositorBarVisible : WM.fullscreenOnMonitor(barRoot.screen?.name) && !monitorHasSpecialOpen
                readonly property real visibleTopHeight: Config.options.bar.bottom || fullscreenCoversBar
                    || barContent.y + barContent.height <= 0.5 ? 0
                    : barRoot.margins.top + hoverRegion.y + barContent.y + barContent.height
                exclusionMode: ExclusionMode.Ignore
                readonly property bool appOverlapEnabled: WM.compositor === "hyprland"
                    && Config.options.bar.bottom && !Config.options.bar.vertical && Config.options.bar.appOverlap.enable
                readonly property var overlapMonitor: appOverlapEnabled ? Hyprland.monitorFor(barRoot.screen) : null
                readonly property var overlapCandidate: {
                    const win = appOverlapEnabled ? ToplevelManager.activeToplevel : null;
                    return win && win.HyprlandToplevel?.handle?.monitor?.name === barRoot.screen?.name ? win : null;
                }
                // Keep the last client when a layer-shell popup takes focus, or another monitor is focused.
                property var overlapWindow: null
                onOverlapCandidateChanged: {
                    if (overlapCandidate) overlapWindow = overlapCandidate;
                }
                function matchesOverlapWindow() {
                    const win = barRoot.overlapWindow;
                    if (!barRoot.appOverlapEnabled || !win || !ToplevelManager.toplevels.values.includes(win)) return false;
                    const hypr = win.HyprlandToplevel?.handle;
                    if (hypr?.monitor?.name !== barRoot.screen?.name) return false;
                    const client = HyprlandData.clientForToplevel(win);
                    const workspace = hypr.workspace?.id;
                    const special = barRoot.thisMonitorData?.specialWorkspace?.id ?? 0;
                    if (!client?.pinned && workspace !== barRoot.overlapMonitor?.activeWorkspace?.id
                        && !(special !== 0 && workspace === special)) return false;
                    return Config.options.bar.appOverlap.classes.some(name =>
                        name.length > 0 && (name === win.appId || name === client?.initialClass));
                }
                readonly property bool wantsAppOverlap: matchesOverlapWindow()
                property bool appOverlapActive: false
                onAppOverlapEnabledChanged: {
                    if (!appOverlapEnabled) {
                        appOverlapTimer.stop();
                        appOverlapActive = false;
                    }
                }
                onWantsAppOverlapChanged: appOverlapTimer.restart()
                Timer {
                    id: appOverlapTimer
                    interval: 150
                    onTriggered: barRoot.appOverlapActive = barRoot.wantsAppOverlap
                }
                property int normalExclusiveZone: (Config?.options.bar.autoHide.enable && (!mustShow || !Config?.options.bar.autoHide.pushWindows))
                    ? 0
                    : Appearance.sizes.baseBarHeight
                        + (Config.options.bar.cornerStyle === 1 ? Appearance.sizes.hyprlandGapsOut : 0)
                        + (Config.options.bar.cornerStyle === 2 ? -6 : 0)

                readonly property int contentExclusiveZone: (barContent.centerOnly && Config.options.bar.centerOnlyReserveFrame)
                    ? Config.options.bar.frameThickness
                    : (Config.options.bar.cornerStyle === 4 || Config.options.bar.cornerStyle === 5 || Config.options.bar.cornerStyle === 6) ? normalExclusiveZone + 4 : normalExclusiveZone
                // The former top layer-shell margin contributed to the reserved area.
                // Preserve that space now that the hover strip lives inside the window.
                exclusiveZone: appOverlapEnabled && appOverlapActive ? 0
                    : contentExclusiveZone > 0 ? contentExclusiveZone + islandTopInset : contentExclusiveZone
                WlrLayershell.namespace: "quickshell:bar"
                WlrLayershell.keyboardFocus: GlobalStates.diSessionOpen
                    && barRoot.screen?.name === Hyprland.focusedMonitor?.name
                    ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
                // Overlay layer only while special workspace sits on top of a fullscreen window on this monitor,
                // else Top layer so fullscreen apps cover the bar as normal (Hyprland buries Top layer under fullscreen+special).
                WlrLayershell.layer: (monitorHasFullscreen && monitorHasSpecialOpen) ? WlrLayer.Overlay : WlrLayer.Top
                // Keep the Material bar's visual gap, but include it in the window
                // so hovering above the island can reach its pointer handler.
                readonly property int islandTopInset: GlobalStates.dynamicIslandEnabled
                    && Config.options.bar.cornerStyle === 3 && !Config.options.bar.bottom ? 5 : 0
                implicitHeight: Appearance.sizes.barHeight + Appearance.rounding.screenRounding + islandTopInset
                // When Overlay-layer, bar shares a layer with the screen-corner click zones (ScreenCorners.qml)
                // and same-layer overlap is resolved by stacking, not layer priority - bar was winning and
                // swallowing the tiny corner-open hit rects. Carve them out of the bar's own mask so clicks
                // reach the corners underneath. Only relevant on the edge the bar and corners share.
                property bool cutOutCornerOpenZones: (monitorHasFullscreen && monitorHasSpecialOpen) && (Config.options.bar.bottom === Config.options.sidebar.cornerOpen.bottom)
                property int cornerOpenCutWidth: cutOutCornerOpenZones ? Config.options.sidebar.cornerOpen.cornerRegionWidth : 0
                property int cornerOpenCutHeight: cutOutCornerOpenZones ? Config.options.sidebar.cornerOpen.cornerRegionHeight : 0
                mask: Region {
                    item: hoverMaskRegion
                    Region {
                        intersection: Intersection.Subtract
                        x: 0
                        y: Config.options.bar.bottom ? (barRoot.height - barRoot.cornerOpenCutHeight) : 0
                        width: barRoot.cornerOpenCutWidth
                        height: barRoot.cornerOpenCutHeight
                    }
                    Region {
                        intersection: Intersection.Subtract
                        x: barRoot.width - barRoot.cornerOpenCutWidth
                        y: Config.options.bar.bottom ? (barRoot.height - barRoot.cornerOpenCutHeight) : 0
                        width: barRoot.cornerOpenCutWidth
                        height: barRoot.cornerOpenCutHeight
                    }
                }
                color: "transparent"

                // Positioning
                anchors {
                    top: !Config.options.bar.bottom
                    bottom: Config.options.bar.bottom
                    left: true
                    right: true
                }

                margins {
                    top: (Config.options.bar.cornerStyle === 3 ? 5 : 0) - barRoot.islandTopInset
                    right: (Config.options.interactions.deadPixelWorkaround.enable && barRoot.anchors.right) * -1
                    bottom: (Config.options.interactions.deadPixelWorkaround.enable && barRoot.anchors.bottom) * -1 || Config.options.bar.cornerStyle === 3 ? 5 : 0
                }

                // Include in focus grab
                Component.onCompleted: {
                    if (overlapCandidate) overlapWindow = overlapCandidate;
                    GlobalFocusGrab.addPersistent(barRoot);
                    GlobalFocusGrab.addBarWindow(barRoot);
                }
                Component.onDestruction: {
                    GlobalFocusGrab.removePersistent(barRoot);
                    GlobalFocusGrab.removeBarWindow(barRoot);
                }

                MouseArea  {
                    id: hoverRegion
                    Binding {
                        target: GlassLayers
                        property: "barZone"
                        value: Math.max(0, barRoot.exclusiveZone)
                        restoreMode: Binding.RestoreBinding
                    }
                    Binding {
                        target: GlassLayers
                        property: "barEdge"
                        value: Config.options.bar.bottom ? "bottom" : "top"
                        restoreMode: Binding.RestoreBinding
                    }

                    hoverEnabled: true
                    anchors {
                        fill: parent
                        topMargin: barRoot.islandTopInset
                        rightMargin: (Config.options.interactions.deadPixelWorkaround.enable && barRoot.anchors.right) * 1
                        bottomMargin: (Config.options.interactions.deadPixelWorkaround.enable && barRoot.anchors.bottom) * 1
                    }

                    Item {
                        id: hoverMaskRegion
                        anchors {
                            fill: barContent
                            topMargin: -Config.options.bar.autoHide.hoverRegionWidth - barRoot.islandTopInset
                            bottomMargin: -Config.options.bar.autoHide.hoverRegionWidth
                        }
                    }

                    BarContent {
                        id: barContent
                        popupInteractionReady: (!Config.options.bar.autoHide.enable || barRoot.mustShow)
                            && !(barTopAnimation.animation?.running ?? false) && !(barBottomAnimation.animation?.running ?? false)
                        islandTopInset: barRoot.islandTopInset
                        
                        implicitHeight: Appearance.sizes.barHeight
                        anchors {
                            right: parent.right
                            left: parent.left
                            top: parent.top
                            bottom: undefined
                            topMargin: (Config?.options.bar.autoHide.enable && !mustShow) ? -Appearance.sizes.barHeight : 0
                            bottomMargin: (Config.options.interactions.deadPixelWorkaround.enable && barRoot.anchors.bottom) * -1
                            rightMargin: (Config.options.interactions.deadPixelWorkaround.enable && barRoot.anchors.right) * -1
                        }
                        Behavior on anchors.topMargin {
                            id: barTopAnimation
                            animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
                        }
                        Behavior on anchors.bottomMargin {
                            id: barBottomAnimation
                            animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
                        }

                        states: State {
                            name: "bottom"
                            when: Config.options.bar.bottom
                            AnchorChanges {
                                target: barContent
                                anchors {
                                    right: parent.right
                                    left: parent.left
                                    top: undefined
                                    bottom: parent.bottom
                                }
                            }
                            PropertyChanges {
                                target: barContent
                                anchors.topMargin: 0
                                anchors.bottomMargin: (Config?.options.bar.autoHide.enable && !mustShow) ? -Appearance.sizes.barHeight : 0
                            }
                        }
                    }
                    
                    // Round decorators
                    Loader {
                        id: roundDecorators
                        anchors {
                            left: parent.left
                            right: parent.right
                            top: barContent.bottom
                            bottom: undefined
                        }
                        height: Appearance.rounding.screenRounding
                        active: !barContent.glassTabs && !barContent.glassHug && ((showBarBackground && Config.options.bar.cornerStyle === 0 && !barContent.centerOnly)
                             || (Config.options.bar.cornerStyle === 4 || Config.options.bar.cornerStyle === 6))

                        states: State {
                            name: "bottom"
                            when: Config.options.bar.bottom
                            AnchorChanges {
                                target: roundDecorators
                                anchors {
                                    right: parent.right
                                    left: parent.left
                                    top: undefined
                                    bottom: barContent.top
                                }
                            }
                        }

                        sourceComponent: Item {
                            implicitHeight: Appearance.rounding.screenRounding

                            readonly property color decoratorColor: (Config.options.bar.cornerStyle === 4 || Config.options.bar.cornerStyle === 6 || showBarBackground)
                                ? (Config.options.bar.followFrameColor && Config.options.bar.frameColor
                                    ? Appearance.getColorFromName(Config.options.bar.frameColor)
                                    : Appearance.colors.colUiBackground)
                                : "transparent"

                            RoundCorner {
                                id: leftCorner
                                glass: true
                                visible: Config.options.bar.cornerStyle === 0 || barContent.effectiveLeftLayout.length > 0
                                anchors {
                                    top: parent.top
                                    bottom: parent.bottom
                                    left: parent.left
                                }

                                implicitSize: Appearance.rounding.screenRounding
                                color: parent.decoratorColor

                                corner: RoundCorner.CornerEnum.TopLeft
                                states: State {
                                    name: "bottom"
                                    when: Config.options.bar.bottom
                                    PropertyChanges {
                                        leftCorner.corner: RoundCorner.CornerEnum.BottomLeft
                                    }
                                }
                            }
                            RoundCorner {
                                id: rightCorner
                                glass: true
                                visible: Config.options.bar.cornerStyle === 0 || barContent.effectiveRightLayout.length > 0
                                anchors {
                                    right: parent.right
                                    top: !Config.options.bar.bottom ? parent.top : undefined
                                    bottom: Config.options.bar.bottom ? parent.bottom : undefined
                                }
                                implicitSize: Appearance.rounding.screenRounding
                                color: parent.decoratorColor

                                corner: RoundCorner.CornerEnum.TopRight
                                states: State {
                                    name: "bottom"
                                    when: Config.options.bar.bottom
                                    PropertyChanges {
                                        rightCorner.corner: RoundCorner.CornerEnum.BottomRight
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    IpcHandler {
        target: "bar"

        function toggle(): void {
            GlobalStates.barOpen = !GlobalStates.barOpen
        }

        function close(): void {
            GlobalStates.barOpen = false
        }

        function open(): void {
            GlobalStates.barOpen = true
        }
    }

    CompositorGlobalShortcut {
        name: "barToggle"
        description: "Toggles bar on press"

        onPressed: {
            GlobalStates.barOpen = !GlobalStates.barOpen;
        }
    }

    CompositorGlobalShortcut {
        name: "barOpen"
        description: "Opens bar on press"

        onPressed: {
            GlobalStates.barOpen = true;
        }
    }

    CompositorGlobalShortcut {
        name: "barClose"
        description: "Closes bar on press"

        onPressed: {
            GlobalStates.barOpen = false;
        }
    }
}
