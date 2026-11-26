import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Qt.labs.synchronizer
import Qt5Compat.GraphicalEffects
import Quickshell.Io
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland

Scope { // Scope
    id: root
    property var tabButtonList: [
        {
            "icon": "keyboard",
            "name": Translation.tr("Keybinds")
        },
        {
            "icon": "experiment",
            "name": Translation.tr("Elements")
        },
    ]

    Loader {
        id: cheatsheetLoader
        active: false

        sourceComponent: PanelWindow { // Window
            id: cheatsheetRoot
            visible: cheatsheetLoader.active

            anchors {
                top: true
                bottom: true
                left: true
                right: true
            }

            function hide() {
                cheatsheetLoader.active = false;
            }
            exclusionMode: ExclusionMode.Ignore
            implicitWidth: cheatsheetBackground.width + Appearance.sizes.elevationMargin * 2
            implicitHeight: cheatsheetBackground.height + Appearance.sizes.elevationMargin * 2
            WlrLayershell.namespace: "quickshell:cheatsheet"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
            color: "transparent"

            mask: Region {
                item: cheatsheetBackground
            }

            Component.onCompleted: {
                GlobalFocusGrab.addDismissable(cheatsheetRoot);
            }
            Component.onDestruction: {
                GlobalFocusGrab.removeDismissable(cheatsheetRoot);
            }
            Connections {
                target: GlobalFocusGrab
                function onDismissed() {
                    cheatsheetRoot.hide();
                }
            }

            // Background
            StyledRectangularShadow {
                target: cheatsheetBackground
            }
            Rectangle {
                id: cheatsheetBackground
                anchors.centerIn: parent
                color: Appearance.colors.colLayer0
                border.width: 1
                border.color: Appearance.colors.colLayer0Border
                radius: Appearance.rounding.windowRounding
                property real padding: 20
                implicitWidth: cheatsheetColumnLayout.implicitWidth + padding * 2
                implicitHeight: cheatsheetColumnLayout.implicitHeight + padding * 2

                Keys.onPressed: event => { // Esc to close
                    if (event.key === Qt.Key_Escape) {
                        cheatsheetRoot.hide();
                    }
                    if (event.modifiers === Qt.ControlModifier) {
                        if (event.key === Qt.Key_PageDown) {
                            tabBar.incrementCurrentIndex();
                            event.accepted = true;
                        } else if (event.key === Qt.Key_PageUp) {
                            tabBar.decrementCurrentIndex();
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Tab) {
                            tabBar.setCurrentIndex((tabBar.currentIndex + 1) % root.tabButtonList.length);
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Backtab) {
                            tabBar.setCurrentIndex((tabBar.currentIndex - 1 + root.tabButtonList.length) % root.tabButtonList.length);
                            event.accepted = true;
                        }
                    }
                }

                RippleButton { // Close button
                    id: closeButton
                    focus: cheatsheetRoot.visible
                    implicitWidth: 40
                    implicitHeight: 40
                    buttonRadius: Appearance.rounding.full
                    anchors {
                        top: parent.top
                        right: parent.right
                        topMargin: 20
                        rightMargin: 20
                    }

                    onClicked: {
                        cheatsheetRoot.hide();
                    }

                    contentItem: MaterialSymbol {
                        anchors.centerIn: parent
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: Appearance.font.pixelSize.title
                        text: "close"
                    }
                }

                ColumnLayout { // Real content
                    id: cheatsheetColumnLayout
                    anchors.centerIn: parent
                    spacing: 10

                    Toolbar {
                        Layout.alignment: Qt.AlignHCenter
                        enableShadow: false
                        ToolbarTabBar {
                            id: tabBar
                            tabButtonList: root.tabButtonList

                            Synchronizer on currentIndex {
                                property alias source: swipeView.currentIndex
                            }
                        }
                    }

                    SwipeView { // Content pages
                        id: swipeView
                        Layout.topMargin: 5
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 10
                        currentIndex: Persistent.states.cheatsheet.tabIndex
                        onCurrentIndexChanged: {
                            Persistent.states.cheatsheet.tabIndex = currentIndex;
                        }

                        implicitWidth: Math.min(1400, cheatsheetRoot.screen.width - 80)
                        implicitHeight: Math.min(800, cheatsheetRoot.screen.height - 160)

                        clip: true
                        layer.enabled: true
                        layer.effect: OpacityMask {
                            maskSource: Rectangle {
                                width: swipeView.width
                                height: swipeView.height
                                radius: Appearance.rounding.small
                            }
                        }

                        ScrollView {
                            clip: true
                            CheatsheetKeybinds { objectName: "cheatsheet-keybinds" }
                        }
                        ScrollView {
                            clip: true
                            CheatsheetPeriodicTable {}
                        }
                    }
                }
            }
        }
    }

    IpcHandler {
        target: "cheatsheet"

        function toggle(): void {
            cheatsheetLoader.active = !cheatsheetLoader.active;
        }

        function close(): void {
            cheatsheetLoader.active = false;
        }

        function open(): void {
            cheatsheetLoader.active = true;
        }
    }

    CompositorGlobalShortcut {
        name: "cheatsheetToggle"
        description: "Toggles cheatsheet on press"

        onPressed: {
            cheatsheetLoader.active = !cheatsheetLoader.active;
        }
    }

    CompositorGlobalShortcut {
        name: "cheatsheetOpen"
        description: "Opens cheatsheet on press"

        onPressed: {
            cheatsheetLoader.active = true;
        }
    }

    CompositorGlobalShortcut {
        name: "cheatsheetClose"
        description: "Closes cheatsheet on press"

        onPressed: {
            cheatsheetLoader.active = false;
        }
    }
}
