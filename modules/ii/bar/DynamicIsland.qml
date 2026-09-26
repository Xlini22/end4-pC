import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Services.Mpris
import Qt5Compat.GraphicalEffects
import QtQuick.Controls
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

Item {
    id: root
    property bool mirrored: false
    readonly property bool centerWorkspaces: Config.options.bar.dynamicIsland.centerWorkspaces && !root.vertical
    readonly property real workspaceSpacing: 8
    readonly property real badgesWidth: root.badgeProviders.length > 0
        ? root.badgeProviders.length * root.badgeSize + (root.badgeProviders.length - 1) * root.badgeSpacing : 0

    readonly property real pillHeight: 32
    readonly property real idleCollapsedWidth: 144
    readonly property real sessionWidth: 164
    property real idleTextContentWidth: 0
    readonly property real idleWidth: Math.max(root.idleCollapsedWidth, root.idleTextContentWidth)
    property real mediaCollapsedWidth: 72
    readonly property real mediaExpandedWidthCap: 220
    property real mediaTextContentWidth: 0
    property bool mediaTrackInfoVisible: root.componentInteractionReady && mediaHoverHandler.hovered
    readonly property real mediaExpandedWidth: Math.max(root.mediaCollapsedWidth, Math.min(root.mediaExpandedWidthCap, root.mediaTextContentWidth))
    readonly property real mediaWidth: root.mediaTrackInfoVisible ? root.mediaExpandedWidth : root.mediaCollapsedWidth
    readonly property real timerWidth: 130
    readonly property real osdWidth: 132
    readonly property real notificationWidth: 220
    readonly property real batteryWidth: 170
    readonly property real badgeSize: 32
    readonly property real badgeSpacing: 6
    readonly property bool isMaterial: Config.options.bar.cornerStyle === 3
    property bool vertical: Config.options.bar.vertical

    property string manualFocusId: ""

    property bool forceIdle: false

    readonly property var displayedProvider: root.forceIdle ? null : root.activeProvider

    onActiveProviderChanged: {
        if (root.activeProvider && root.alwaysWinIds.includes(root.activeProvider.id)) {
            root.forceIdle = false
        }
    }

    readonly property MprisPlayer activePlayer: MprisController.activePlayer
    readonly property bool hasMedia: root.activePlayer !== null
        && ((root.activePlayer.trackTitle ?? "") !== "" || root.activePlayer.isPlaying)
    readonly property var latestNotification: Notifications.popupList.length > 0
        ? Notifications.popupList[Notifications.popupList.length - 1]
        : null
    readonly property bool isRecording: Persistent.states.record.enable
    property int recordingElapsedSeconds: 0

    onIsRecordingChanged: {
        if (!isRecording) recordingElapsedSeconds = 0
    }

    function formatRecordingTime(s) {
        return Math.floor(s / 60).toString().padStart(2, '0') + ":" + (s % 60).toString().padStart(2, '0')
    }

    Timer {
        interval: 1000
        repeat: true
        running: root.isRecording
        onTriggered: root.recordingElapsedSeconds++
    }

    property string engagedTimerKind: ""
    readonly property bool hasActiveTimer: root.engagedTimerKind !== ""

    Connections {
        target: TimerService
        function onPomodoroRunningChanged() { if (TimerService.pomodoroRunning) root.engagedTimerKind = "pomodoro" }
        function onCountdownRunningChanged() { if (TimerService.countdownRunning) root.engagedTimerKind = "countdown" }
        function onStopwatchRunningChanged() { if (TimerService.stopwatchRunning) root.engagedTimerKind = "stopwatch" }
    }

    function timerIcon() {
        switch (root.engagedTimerKind) {
            case "pomodoro":  return TimerService.pomodoroBreak ? "coffee" : "visibility"
            case "countdown": return "hourglass_top"
            case "stopwatch": return "timer"
            default:          return "timer"
        }
    }

    function timerValueText() {
        switch (root.engagedTimerKind) {
            case "pomodoro":  return TimerService.formatSeconds(TimerService.pomodoroSecondsLeft)
            case "countdown": return TimerService.formatSeconds(TimerService.countdownSecondsLeft)
            case "stopwatch": return TimerService.formatSeconds(TimerService.stopwatchTime / 100)
            default:          return ""
        }
    }

    function timerRunning() {
        switch (root.engagedTimerKind) {
            case "pomodoro":  return TimerService.pomodoroRunning
            case "countdown": return TimerService.countdownRunning
            case "stopwatch": return TimerService.stopwatchRunning
            default:          return false
        }
    }

    function toggleActiveTimer() {
        switch (root.engagedTimerKind) {
            case "pomodoro":  TimerService.togglePomodoro(); break
            case "countdown": TimerService.toggleCountdown(); break
            case "stopwatch": TimerService.toggleStopwatch(); break
        }
    }

    function resetActiveTimer() {
        switch (root.engagedTimerKind) {
            case "pomodoro":  TimerService.resetPomodoro(); break
            case "countdown": TimerService.resetCountdown(); break
            case "stopwatch": TimerService.stopwatchReset(); break
        }
        root.engagedTimerKind = ""
    }

    property bool batteryAlertActive: false
    property string batteryAlertKind: "" 
    readonly property int batteryAlertDuration: 4000

    Timer {
        id: batteryAlertTimer
        interval: root.batteryAlertDuration
        repeat: false
        onTriggered: root.batteryAlertActive = false
    }

    function triggerBatteryAlert(kind) {
        root.batteryAlertKind = kind
        root.batteryAlertActive = true
        batteryAlertTimer.restart()
    }

    Connections {
        target: Battery
        function onIsCriticalAndNotChargingChanged() {
            if (Battery.isCriticalAndNotCharging) root.triggerBatteryAlert("critical")
        }
        function onIsLowAndNotChargingChanged() {
            if (Battery.isLowAndNotCharging && !Battery.isCriticalAndNotCharging) root.triggerBatteryAlert("low")
        }
        function onIsPluggedInChanged() {
            if (Battery.isPluggedIn) root.triggerBatteryAlert("charging")
        }
    }

    function batteryStatusText() {
        switch (root.batteryAlertKind) {
            case "critical": return Translation.tr("Critical Battery")
            case "charging": return Translation.tr("Charging")
            default:         return Translation.tr("Low Battery")
        }
    }

    function batteryIcon() {
        if (root.batteryAlertKind === "charging" || Battery.isCharging) return "battery_android_frame_bolt"
        const pct = Battery.percentage
        if (pct <= 0.1) return "battery_android_frame_alert"
        if (pct <= 0.2) return "battery_android_frame_1"
        if (pct <= 0.4) return "battery_android_frame_2"
        if (pct <= 0.6) return "battery_android_frame_3"
        if (pct <= 0.8) return "battery_android_frame_4"
        if (pct < 1)    return "battery_android_frame_5"
        return "battery_android_full"
    }

    function batteryAlertColor() {
        return root.batteryAlertKind === "charging" ? Appearance.m3colors.m3success : Appearance.colors.colError
    }

    readonly property var contentProviders: [
        { id: "notification", active: root.latestNotification !== null, component: notificationComponent, width: root.notificationWidth },
        { id: "battery",      active: root.batteryAlertActive,          component: batteryComponent,      width: root.batteryWidth },
        { id: "recording",    active: root.isRecording,                 component: recordingComponent,    width: root.recordingWidth },
        { id: "timer",        active: root.hasActiveTimer,              component: timerComponent,        width: root.timerWidth },
        { id: "osd",          active: GlobalStates.osdVolumeOpen,       component: osdComponent,          width: root.osdWidth },
        { id: "media",        active: root.hasMedia,                    component: mediaComponent,        width: root.mediaWidth },
        { id: "session",      active: GlobalStates.diSessionOpen,       component: sessionComponent,      width: root.sessionWidth },
    ]

    readonly property var alwaysWinIds: ["session", "notification", "battery", "osd"]

    readonly property var activeOthers: root.contentProviders.filter(p => !root.alwaysWinIds.includes(p.id) && p.active)

    readonly property var activeProvider: {
        const forcedTop = root.contentProviders.find(p => root.alwaysWinIds.includes(p.id) && p.active)
        if (forcedTop) return forcedTop
        if (root.manualFocusId !== "") {
            const forced = root.activeOthers.find(p => p.id === root.manualFocusId)
            if (forced) return forced
        }
        return root.activeOthers[0] ?? null
    }

    readonly property var badgeProviders: {
        if (root.alwaysWinIds.some(id => root.contentProviders.find(p => p.id === id)?.active)) return []
        return root.activeOthers.filter(p => p.id !== root.activeProvider?.id)
    }

    function iconForProviderId(id) {
        switch (id) {
            case "media":     return "music_note"
            case "recording": return "screen_record"
            case "timer":     return root.timerIcon()
            case "battery":   return root.batteryIcon()
            case "osd":
                switch (GlobalStates.osdIndicatorType) {
                    case "brightness": return Hyprsunset.temperatureActive ? "routine" : "light_mode"
                    case "gamma":      return "wb_twilight"
                    default:           return "volume_up"
                }
            default: return "circle"
        }
    }

    readonly property string activeContentId: root.displayedProvider?.id ?? "idle"

    // BarContent also feeds hover from the complete central bar area. The
    // local handler remains useful when this component is used elsewhere.
    property bool barHovered: false
    readonly property bool expanded: root.barHovered || islandHover.hovered
    property bool componentInteractionReady: false

    onExpandedChanged: {
        if (expanded) {
            componentInteractionTimer.restart();
        } else {
            componentInteractionTimer.stop();
            componentInteractionReady = false;
        }
    }

    Timer {
        id: componentInteractionTimer
        interval: 350
        repeat: false
        onTriggered: root.componentInteractionReady = true
    }
    readonly property real contentPadding: 8
    property real primaryWidth: root.displayedProvider?.width ?? root.idleWidth
    Behavior on primaryWidth {
        NumberAnimation { duration: 350; easing.type: Easing.OutCubic }
    }
    readonly property real leftContentWidth: leftWidgets.implicitWidth
        + (leftWidgets.implicitWidth > 0 ? root.workspaceSpacing : 0) + root.primaryWidth
    readonly property real rightContentWidth: root.badgesWidth
        + (root.badgesWidth > 0 && rightWidgets.implicitWidth > 0 ? root.workspaceSpacing : 0)
        + rightWidgets.implicitWidth
    readonly property real wingWidth: Math.max(root.leftContentWidth, root.rightContentWidth)
    readonly property real leftStart: root.contentPadding
    readonly property real rightStart: root.width - root.contentPadding - root.rightContentWidth

    implicitHeight: root.pillHeight
    implicitWidth: 2 * root.contentPadding + (root.centerWorkspaces
        ? workspaceLoader.implicitWidth + 2 * (root.workspaceSpacing + root.wingWidth)
        : root.leftContentWidth + root.rightContentWidth + (root.rightContentWidth > 0 ? root.workspaceSpacing : 0))

    HoverHandler { id: islandHover }

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: root.isMaterial ? "transparent" : Config.options.bar.followFrameColor
            ? Appearance.getColorFromName(Config.options.bar.frameColor) : Appearance.colors.colLayer0
    }

    component SideWidgets: RowLayout {
        id: sideWidgetsRoot
        property var widgets: []
        spacing: root.workspaceSpacing
        Repeater {
            model: sideWidgetsRoot.widgets.filter(name => name !== "dynamicIsland"
                && !(name === "workspaces" && root.centerWorkspaces))
            delegate: Loader {
                id: sideLoader
                required property string modelData
                readonly property bool supportsExpansion: ["clockWidget", "resources"].includes(modelData)
                readonly property string displayMode: Config.options.bar.dynamicIsland.widgetModes[modelData] ?? "dynamic"
                // Side-widget hover/click behavior starts after the island has
                // completed its opening animation.
                enabled: root.componentInteractionReady
                Layout.alignment: Qt.AlignVCenter
                source: Qt.resolvedUrl("./" + modelData.charAt(0).toUpperCase() + modelData.slice(1) + ".qml")
                Binding {
                    target: sideLoader.supportsExpansion ? sideLoader.item : null
                    property: "islandMode"
                    value: true
                    when: sideLoader.supportsExpansion && sideLoader.status === Loader.Ready
                }
                Binding {
                    target: sideLoader.supportsExpansion ? sideLoader.item : null
                    property: "islandExpanded"
                    value: sideLoader.displayMode === "expanded"
                        || (sideLoader.displayMode !== "compact" && root.expanded)
                    when: sideLoader.supportsExpansion && sideLoader.status === Loader.Ready
                }
            }
        }
    }

    SideWidgets {
        id: leftWidgets
        widgets: Config.options.bar.dynamicIsland.leftWidgets
        x: root.leftStart
        anchors.verticalCenter: parent.verticalCenter
    }
    SideWidgets {
        id: rightWidgets
        widgets: Config.options.bar.dynamicIsland.rightWidgets
        x: root.rightStart + root.badgesWidth
            + (root.badgesWidth > 0 && implicitWidth > 0 ? root.workspaceSpacing : 0)
        anchors.verticalCenter: parent.verticalCenter
    }

    // Symmetric side reservations keep the workspace strip on the screen center
    // even while the primary activity changes width or secondary badges appear.
    Loader {
        id: workspaceLoader
        active: root.centerWorkspaces
        anchors.centerIn: parent
        // Preserve Workspaces' native bar dimensions, as in the regular bar.
        // Forcing the island's pill height offsets icons relative to indicators.
        sourceComponent: Workspaces {}
    }

    // Animate content widths at their source. The island and its positions follow
    // those widths directly, keeping both outer margins equal on every frame.
    Rectangle {
        id: pill
        x: root.leftStart + leftWidgets.implicitWidth
            + (leftWidgets.implicitWidth > 0 ? root.workspaceSpacing : 0)
        width: root.primaryWidth
        height: root.pillHeight
        color: "transparent"
        radius: height / 2
        clip: true
        visible: !root.vertical

        HoverHandler {
            id: mediaHoverHandler
            enabled: root.activeContentId === "media" && root.componentInteractionReady
        }

        WheelHandler {
            id: idleToggleWheelHandler
            target: pill
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            property bool coolingDown: false
            onWheel: (event) => {
                if (coolingDown) return
                coolingDown = true
                idleToggleDebounceTimer.restart()
                root.forceIdle = !root.forceIdle
            }
        }

        Timer {
            id: idleToggleDebounceTimer
            interval: 200
            onTriggered: idleToggleWheelHandler.coolingDown = false
        }

        Loader {
            id: contentLoader
            anchors.fill: parent
            sourceComponent: root.displayedProvider?.component ?? idleComponent
            active: !root.vertical

            onLoaded: {
                if (root.displayedProvider?.id === "session" && item) {
                    item.forceActiveFocus()
                }
            }
        }

        Component {
            id: idleComponent
            DiIdle { di: root }
        }

        Component {
            id: mediaComponent
            DiMedia { di: root }
        }

        Component {
            id: osdComponent
            DiOsd { di: root }
        }

        Component {
            id: notificationComponent
            DiNotifs { di: root }
        }

        Component {
            id: timerComponent
            DiTimers { di: root }
        }

        Component {
            id: sessionComponent
            DiSession { di: root }
        }

        Component {
            id: recordingComponent
            RowLayout {
                anchors {
                    fill: parent
                    leftMargin: root.isMaterial ? 4 : 8
                    rightMargin: 10
                }
                spacing: 6

                Item {
                    id: stopButton
                    Layout.alignment: Qt.AlignVCenter
                    implicitWidth: 16
                    implicitHeight: 16

                    MaterialSymbol {
                        anchors.fill: parent
                        text: "stop_circle"
                        fill: 1
                        iconSize: root.isMaterial ? 26 : 16
                        color: Appearance.colors.colError
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Quickshell.execDetached([Directories.recordScriptPath])
                    }
                }

                Item { Layout.fillWidth: true }

                StyledText {
                    Layout.alignment: Qt.AlignVCenter
                    text: root.formatRecordingTime(root.recordingElapsedSeconds)
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.features: { "tnum": 1 }
                    color: Appearance.colors.colOnLayer0
                }
            }
        }

        Component {
            id: batteryComponent
            RowLayout {
                anchors {
                    fill: parent
                    leftMargin: 10
                    rightMargin: 10
                }
                spacing: 6

                StyledText {
                    Layout.alignment: Qt.AlignVCenter
                    text: root.batteryStatusText()
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.weight: Font.DemiBold
                    color: root.batteryAlertColor()
                }

                Item { Layout.fillWidth: true }

                MaterialSymbol {
                    Layout.alignment: Qt.AlignVCenter
                    text: root.batteryIcon()
                    fill: 1
                    iconSize: 16
                    color: root.batteryAlertColor()
                }

                StyledText {
                    Layout.alignment: Qt.AlignVCenter
                    text: `${Math.round(Battery.percentage * 100)}`
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.features: { "tnum": 1 }
                    color: root.batteryAlertColor()
                }
            }
        }
    }

    Row {
        id: badgesRow
        visible: root.badgeProviders.length > 0 && !root.vertical
        x: root.rightStart
        anchors.verticalCenter: parent.verticalCenter
        spacing: root.badgeSpacing

        Repeater {
            model: root.badgeProviders
            delegate: Item {
                id: badgeItem
                required property var modelData
                width: root.badgeSize
                height: root.badgeSize

                MaterialShapeWrappedMaterialSymbol {
                    anchors.fill: parent
                    wrappedShape: MaterialShape.Shape.Cookie7Sided
                    color: root.isMaterial ? Appearance.colors.colPrimary : Appearance.colors.colLayer0
                    colSymbol: root.isMaterial ? Appearance.colors.colOnPrimary : Appearance.colors.colOnLayer0
                    text: root.iconForProviderId(badgeItem.modelData.id)
                    iconSize: 16
                    fill: 1
                    padding: 4
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.manualFocusId = badgeItem.modelData.id
                }
            }
        }
    }
}
