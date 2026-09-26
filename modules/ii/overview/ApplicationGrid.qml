pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell

import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

Item {
    id: root

    property real gridWidth: 980
    property real navigationGutter: 50
    readonly property int columns: 7
    readonly property int rows: 2
    readonly property int appsPerPage: columns * rows
    readonly property var applications: AppSearch.list
        .filter(entry => entry && !entry.noDisplay && (entry.name ?? "") !== "")
        .slice()
        .sort((a, b) => {
            const first = (a.name ?? "").toLocaleLowerCase();
            const second = (b.name ?? "").toLocaleLowerCase();
            return first < second ? -1 : first > second ? 1 : 0;
        })
    readonly property int pageCount: Math.max(1, Math.ceil(applications.length / appsPerPage))
    property bool swipeCoolingDown: false

    implicitWidth: gridBackground.implicitWidth + Appearance.sizes.elevationMargin * 2 + navigationGutter * 2
    implicitHeight: gridBackground.implicitHeight + Appearance.sizes.elevationMargin * 2

    function showPage(index) {
        const next = Math.max(0, Math.min(root.pageCount - 1, index));
        if (next === appPages.currentIndex) return;

        pageSlideAnimation.stop();
        pageSlideAnimation.from = appPages.contentX;
        pageSlideAnimation.to = next * (appPages.width + appPages.spacing);
        appPages.currentIndex = next;
        pageSlideAnimation.start();
    }

    function showRelativePage(offset) {
        showPage(appPages.currentIndex + offset);
    }

    function handlePageWheel(event) {
        const horizontalDelta = event.pixelDelta.x !== 0
            ? event.pixelDelta.x : event.angleDelta.x;
        if (horizontalDelta === 0) return;

        event.accepted = true;
        swipeReset.restart();
        if (root.swipeCoolingDown) return;

        root.swipeCoolingDown = true;
        const pageDelta = Config.options.hyprland.input.touchpad.naturalScroll
            ? -horizontalDelta : horizontalDelta;
        root.showRelativePage(pageDelta > 0 ? 1 : -1);
    }

    function launchApplication(entry) {
        GlobalStates.overviewOpen = false;
        if (!entry.runInTerminal) {
            entry.execute();
            return;
        }

        const terminalCommand = Config.options.apps.terminal.trim().split(/\s+/);
        Quickshell.execDetached(terminalCommand.concat(["-e"]).concat(entry.command));
    }

    StyledRectangularShadow {
        target: gridBackground
    }

    RippleButton {
        id: previousPageButton
        z: 2
        anchors {
            right: gridBackground.left
            rightMargin: 8
            verticalCenter: gridBackground.verticalCenter
        }
        width: 34
        height: 34
        buttonRadius: 17
        enabled: appPages.currentIndex > 0
        visible: root.pageCount > 1
        onClicked: root.showRelativePage(-1)
        contentItem: MaterialSymbol {
            anchors.centerIn: parent
            text: "chevron_left"
            iconSize: 24
            color: Appearance.colors.colOnLayer1
        }
    }

    RippleButton {
        id: nextPageButton
        z: 2
        anchors {
            left: gridBackground.right
            leftMargin: 8
            verticalCenter: gridBackground.verticalCenter
        }
        width: 34
        height: 34
        buttonRadius: 17
        enabled: appPages.currentIndex < root.pageCount - 1
        visible: root.pageCount > 1
        onClicked: root.showRelativePage(1)
        contentItem: MaterialSymbol {
            anchors.centerIn: parent
            text: "chevron_right"
            iconSize: 24
            color: Appearance.colors.colOnLayer1
        }
    }

    Rectangle {
        id: gridBackground
        anchors {
            fill: parent
            leftMargin: Appearance.sizes.elevationMargin + root.navigationGutter
            rightMargin: Appearance.sizes.elevationMargin + root.navigationGutter
            topMargin: Appearance.sizes.elevationMargin
            bottomMargin: Appearance.sizes.elevationMargin
        }
        implicitWidth: root.gridWidth
        implicitHeight: 232
        radius: Appearance.rounding.verylarge
        color: Appearance.colors.colBackgroundSurfaceContainer
        clip: true

        MouseArea {
            id: swipeArea
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            hoverEnabled: false
            scrollGestureEnabled: true
            onWheel: event => root.handlePageWheel(event)
        }

        ListView {
            id: appPages
            parent: swipeArea
            anchors {
                fill: parent
                leftMargin: 12
                rightMargin: 12
                topMargin: 10
                bottomMargin: pageIndicators.height + 13
            }
            orientation: ListView.Horizontal
            model: root.pageCount
            interactive: false
            clip: true
            spacing: 0
            snapMode: ListView.SnapOneItem
            highlightRangeMode: ListView.NoHighlightRange
            preferredHighlightBegin: 0
            preferredHighlightEnd: 0
            highlightMoveDuration: 280
            boundsBehavior: Flickable.StopAtBounds

            NumberAnimation {
                id: pageSlideAnimation
                target: appPages
                property: "contentX"
                duration: 320
                easing.type: Easing.OutCubic
            }

            delegate: Item {
                id: appPage
                required property int index
                width: appPages.width
                height: appPages.height
                readonly property var pageApps: root.applications.slice(
                    index * root.appsPerPage,
                    (index + 1) * root.appsPerPage
                )

                Grid {
                    anchors.fill: parent
                    columns: root.columns
                    rows: root.rows
                    columnSpacing: 4
                    rowSpacing: 4

                    Repeater {
                        model: appPage.pageApps

                        delegate: RippleButton {
                            id: appButton
                            required property var modelData
                            width: (appPage.width - 6 * 4) / root.columns
                            height: (appPage.height - 4) / root.rows
                            buttonRadius: Appearance.rounding.large
                            colBackground: "transparent"
                            colBackgroundHover: Appearance.colors.colLayer1Hover
                            colRipple: Appearance.colors.colLayer1Active

                            onClicked: root.launchApplication(modelData)

                            contentItem: ColumnLayout {
                                spacing: 5

                                AppIcon {
                                    Layout.alignment: Qt.AlignHCenter
                                    implicitSize: 48
                                    source: Quickshell.iconPath(appButton.modelData.icon, "image-missing")
                                }

                                StyledText {
                                    Layout.fillWidth: true
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: Appearance.font.pixelSize.small
                                    color: Appearance.colors.colOnLayer1
                                    text: appButton.modelData.name
                                    elide: Text.ElideRight
                                    maximumLineCount: 1
                                }
                            }

                            StyledToolTip {
                                text: appButton.modelData.name
                                delay: 500
                            }
                        }
                    }
                }
            }
        }

        Timer {
            id: swipeReset
            interval: 180
            onTriggered: root.swipeCoolingDown = false
        }

        Row {
            id: pageIndicators
            parent: swipeArea
            z: 101
            anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                bottomMargin: 8
            }
            spacing: 2
            visible: root.pageCount > 1

            Repeater {
                model: root.pageCount
                delegate: RippleButton {
                    id: pageButton
                    required property int index
                    readonly property bool selected: index === appPages.currentIndex
                    width: 18
                    height: 18
                    buttonRadius: 9
                    rippleEnabled: false
                    colBackground: "transparent"
                    colBackgroundHover: "transparent"
                    onClicked: root.showPage(index)

                    contentItem: Rectangle {
                        anchors.centerIn: parent
                        width: pageButton.selected ? 8 : 6
                        height: width
                        radius: width / 2
                        color: pageButton.selected
                            ? Appearance.colors.colPrimary
                            : Appearance.colors.colOutlineVariant

                        Behavior on width {
                            NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }
                        Behavior on height {
                            NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }
                    }
                }
            }
        }
    }
}
