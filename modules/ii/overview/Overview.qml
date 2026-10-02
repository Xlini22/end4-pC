import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import Qt.labs.synchronizer
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

Scope {
    id: overviewScope
    property bool dontAutoCancelSearch: false

    PanelWindow {
        id: panelWindow
        property string searchingText: ""
        property bool presented: GlobalStates.overviewOpen
        property bool contentShown: GlobalStates.overviewOpen
        readonly property HyprlandMonitor monitor: Hyprland.monitorFor(panelWindow.screen)
        readonly property bool barCenterOnly: Config.options.bar.layouts.leftLayout.length === 0
            && Config.options.bar.layouts.rightLayout.length === 0
            && !Config.options.bar.vertical

        readonly property bool barOverlapActive: panelWindow.barCenterOnly
            && Config.options.bar.centerOnlyReserveFrame
            && !Config.options.bar.bottom
            && !Config.options.bar.autoHide.enable
        property bool monitorIsFocused: (Hyprland.focusedMonitor?.id == monitor?.id)
        visible: panelWindow.presented

        WlrLayershell.namespace: "quickshell:overview"
        WlrLayershell.layer: WlrLayer.Top
        WlrLayershell.keyboardFocus: GlobalStates.overviewOpen ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
        color: "transparent"

        mask: Region {
            item: GlobalStates.overviewOpen ? overviewInputArea : null
            Region {
                item: searchWidget.clipboardPopover.visible ? searchWidget.clipboardPopover : null
            }
        }

        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }

        Connections {
            target: GlobalStates
            function onOverviewOpenChanged() {
                if (!GlobalStates.overviewOpen) {
                    panelWindow.contentShown = false;
                    closeAnimationTimer.restart();
                    searchWidget.disableExpandAnimation();
                    overviewScope.dontAutoCancelSearch = false;
                    GlobalFocusGrab.dismiss();
                } else {
                    closeAnimationTimer.stop();
                    panelWindow.presented = true;
                    panelWindow.contentShown = false;
                    Qt.callLater(function() {
                        if (GlobalStates.overviewOpen)
                            panelWindow.contentShown = true;
                    });
                    if (!overviewScope.dontAutoCancelSearch)
                        searchWidget.cancelSearch();
                    GlobalFocusGrab.addDismissable(panelWindow);
                }
            }
        }

        Connections {
            target: GlobalFocusGrab
            function onDismissed() {
                GlobalStates.overviewOpen = false;
            }
        }
        implicitWidth: columnLayout.implicitWidth
        implicitHeight: columnLayout.implicitHeight

        Timer {
            id: closeAnimationTimer
            interval: 420
            onTriggered: {
                if (!GlobalStates.overviewOpen)
                    panelWindow.presented = false;
            }
        }

        function setSearchingText(text) {
            searchWidget.setSearchingText(text);
            searchWidget.focusFirstItem();
        }

        Item {
            id: overviewInputArea
            anchors.fill: parent
            z: 0
        }

        MouseArea {
            anchors {
                top: parent.top
                bottom: columnLayout.top
                left: parent.left
                right: parent.right
            }
            onClicked: GlobalStates.overviewOpen = false
        }

        MouseArea {
            anchors {
                top: columnLayout.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }
            onClicked: GlobalStates.overviewOpen = false
        }

        MouseArea {
            anchors {
                top: columnLayout.top
                bottom: columnLayout.bottom
                left: parent.left
                right: columnLayout.left
            }
            onClicked: GlobalStates.overviewOpen = false
        }

        MouseArea {
            anchors {
                top: columnLayout.top
                bottom: columnLayout.bottom
                left: columnLayout.right
                right: parent.right
            }
            onClicked: GlobalStates.overviewOpen = false
        }

        Column {
            id: columnLayout
            z: 1
            visible: panelWindow.presented
            opacity: panelWindow.contentShown ? 1 : 0
            scale: panelWindow.contentShown ? 1 : 0.85
            transformOrigin: Item.Top
            anchors {
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                topMargin: (panelWindow.barOverlapActive
                    ? Appearance.sizes.barHeight - Config.options.bar.frameThickness
                    : 0) + 40
            }
            spacing: 6

            Behavior on opacity {
                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
            }
            Behavior on scale {
                NumberAnimation { duration: 400; easing.type: Easing.BezierSpline; easing.bezierCurve: Appearance.animationCurves.expressiveDefaultSpatial }
            }

            Keys.onPressed: event => {
                if (event.key === Qt.Key_Escape) {
                    GlobalStates.overviewOpen = false;
                } else if (event.key === Qt.Key_Left) {
                    if (!panelWindow.searchingText)
                        Hyprland.dispatch("workspace r-1");
                } else if (event.key === Qt.Key_Right) {
                    if (!panelWindow.searchingText)
                        Hyprland.dispatch("workspace r+1");
                }
            }

            SearchWidget {
                id: searchWidget
                anchors.horizontalCenter: parent.horizontalCenter
                Synchronizer on searchingText {
                    property alias source: panelWindow.searchingText
                }
            }

            Loader {
                id: overviewLoader
                active: panelWindow.visible && (Config?.options.overview.enable ?? true)
                sourceComponent: (Config?.options.overview.style ?? "default") === "niri" ? niriComponent : defaultComponent

                Component {
                    id: defaultComponent
                    OverviewWidget {
                        screen: panelWindow.screen
                        visible: panelWindow.searchingText === ""
                    }
                }

                Component {
                    id: niriComponent
                    NiriOverview {
                        screen: panelWindow.screen
                        panelWindow: panelWindow
                        visible: panelWindow.searchingText === ""
                    }
                }
            }

            ApplicationGrid {
                id: applicationGrid
                anchors.horizontalCenter: parent.horizontalCenter
                visible: panelWindow.searchingText === ""
                gridWidth: Math.max(760, overviewLoader.implicitWidth
                    - Appearance.sizes.elevationMargin * 2 - 100)
            }
        }
    }

    function toggleClipboard() {
        if (GlobalStates.overviewOpen && overviewScope.dontAutoCancelSearch) {
            GlobalStates.overviewOpen = false;
            return;
        }
        overviewScope.dontAutoCancelSearch = true;
        panelWindow.setSearchingText(Config.options.search.prefix.clipboard);
        GlobalStates.overviewOpen = true;
    }

    function toggleEmojis() {
        if (GlobalStates.overviewOpen && overviewScope.dontAutoCancelSearch) {
            GlobalStates.overviewOpen = false;
            return;
        }
        overviewScope.dontAutoCancelSearch = true;
        panelWindow.setSearchingText(Config.options.search.prefix.emojis);
        GlobalStates.overviewOpen = true;
    }

    function toggleSymbols() {
        if (GlobalStates.overviewOpen && overviewScope.dontAutoCancelSearch) {
            GlobalStates.overviewOpen = false;
            return;
        }
        overviewScope.dontAutoCancelSearch = true;
        panelWindow.setSearchingText(Config.options.search.prefix.symbols);
        GlobalStates.overviewOpen = true;
    }

    IpcHandler {
        target: "search"

        function toggle() {
            GlobalStates.overviewOpen = !GlobalStates.overviewOpen;
        }
        function workspacesToggle() {
            GlobalStates.overviewOpen = !GlobalStates.overviewOpen;
        }
        function close() {
            GlobalStates.overviewOpen = false;
        }
        function open() {
            GlobalStates.overviewOpen = true;
        }
        function toggleReleaseInterrupt() {
            GlobalStates.superReleaseMightTrigger = false;
        }
        function clipboardToggle() {
            overviewScope.toggleClipboard();
        }
    }

    CompositorGlobalShortcut {
        name: "searchToggle"
        description: "Toggles search on press"

        onPressed: {
            GlobalStates.overviewOpen = !GlobalStates.overviewOpen;
        }
    }
    CompositorGlobalShortcut {
        name: "overviewWorkspacesClose"
        description: "Closes overview on press"

        onPressed: {
            GlobalStates.overviewOpen = false;
        }
    }
    CompositorGlobalShortcut {
        name: "overviewWorkspacesToggle"
        description: "Toggles overview on press"

        onPressed: {
            GlobalStates.overviewOpen = !GlobalStates.overviewOpen;
        }
    }
    CompositorGlobalShortcut {
        name: "searchToggleRelease"
        description: "Toggles search on release"

        onPressed: {
            GlobalStates.superReleaseMightTrigger = true;
        }

        onReleased: {
            if (!GlobalStates.superReleaseMightTrigger) {
                GlobalStates.superReleaseMightTrigger = true;
                return;
            }
            GlobalStates.overviewOpen = !GlobalStates.overviewOpen;
        }
    }
    CompositorGlobalShortcut {
        name: "overviewClipboardToggle"
        description: "Toggle clipboard query on overview widget"
        onPressed: overviewScope.toggleClipboard()
    }

    CompositorGlobalShortcut {
        name: "overviewEmojiToggle"
        description: "Toggle emoji query on overview widget"
        onPressed: overviewScope.toggleEmojis()
    }

    CompositorGlobalShortcut {
        name: "overviewSymbolsToggle"
        description: "Toggle material symbols search on overview widget"
        onPressed: overviewScope.toggleSymbols()
    }

    CompositorGlobalShortcut {
        name: "searchToggleReleaseInterrupt"
        description: "Interrupts possibility of search being toggled on release. " + "This is necessary because GlobalShortcut.onReleased in quickshell triggers whether or not you press something else while holding the key. " + "To make sure this works consistently, use binditn = MODKEYS, catchall in an automatically triggered submap that includes everything."

        onPressed: {
            GlobalStates.superReleaseMightTrigger = false;
        }
    }
}
