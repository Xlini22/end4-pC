pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Wayland
import qs
import qs.modules.common
import qs.services

ClockWidget {
    id: root
    required property Item canvas
    property bool surfaceEnabled: true
    property Item homeParent: null
    property bool detached: false
    readonly property int padding: 32
    rotationPaused: root.detached && !GlobalStates.screenLocked
        && GlassCompositor.clockVisibility[clockWindow.screen?.name] === false
    readonly property bool windowWanted: surfaceEnabled && homeParent && homeParent.visible
        && !GlobalStates.screenLocked && !Config.options.background.widgets.blurWidgets
        && root.clockStyle === "cookie" && canvas.scale === 1
        && !canvas.registeredWidgets.some(widget => widget !== root && widget.visible && widget.z > root.z
            && widget.x < root.x + root.width + padding && widget.x + widget.width > root.x - padding
            && widget.y < root.y + root.height + padding && widget.y + widget.height > root.y - padding)
    readonly property real inheritedOpacity: {
        let opacity = 1;
        for (let item = homeParent; item; item = item.parent) opacity *= item.opacity;
        return opacity;
    }

    // Keep the canvas coordinates and selection/drag controller when the visual parent is another window.
    function findCanvas(item) { return root.canvas; }
    function syncParent() {
        if (!root.containsPress || GlobalStates.screenLocked) root.detached = root.windowWanted;
    }
    onWindowWantedChanged: syncParent()
    onContainsPressChanged: syncParent()
    Component.onCompleted: {
        root.homeParent = parent;
        root.syncParent();
    }
    Binding {
        target: root
        property: "parent"
        when: root.homeParent !== null
        value: root.detached ? host : root.homeParent
    }

    // ponytail: a small unblurred clock surface localizes damage; blur and overlapping higher widgets retain the canvas path.
    PanelWindow {
        id: clockWindow
        visible: root.detached
        screen: root.canvas.QsWindow.window?.screen ?? Quickshell.screens[0]
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "end4-background-clock"
        WlrLayershell.keyboardFocus: GlobalStates.desktopWidgetKeyboardFocus ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
        color: "transparent"
        anchors { top: true; left: true }
        margins.left: Math.floor(root.x + root.canvas.x - root.padding)
        margins.top: Math.floor(root.y + root.canvas.y - root.padding)
        implicitWidth: Math.max(1, Math.ceil(root.width + root.padding * 2 + 1))
        implicitHeight: Math.max(1, Math.ceil(root.height + root.padding * 2 + 1))
        mask: Region { item: root.detached ? root : null }
        Item {
            id: host
            // The host's global origin stays at the canvas origin even while dragging the window.
            x: root.canvas.x - clockWindow.margins.left
            y: root.canvas.y - clockWindow.margins.top
            width: root.homeParent?.width ?? 0
            height: root.homeParent?.height ?? 0
            opacity: root.inheritedOpacity
            focus: true
            Keys.forwardTo: [root.canvas]
        }
    }
}
