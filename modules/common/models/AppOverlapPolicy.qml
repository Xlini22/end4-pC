pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services

Scope {
    id: root
    required property var screen
    required property list<string> classes
    property bool appOverlapEnabled: false
    readonly property var thisMonitorData: appOverlapEnabled
        ? HyprlandData.monitors.find(m => m.name === root.screen?.name) : null

    readonly property var overlapMonitor: appOverlapEnabled ? Hyprland.monitorFor(root.screen) : null
    readonly property var overlapCandidate: {
        const win = appOverlapEnabled ? ToplevelManager.activeToplevel : null;
        return win && win.HyprlandToplevel?.handle?.monitor?.name === root.screen?.name ? win : null;
    }
    // Keep the last client when a layer-shell popup takes focus, or another monitor is focused.
    property var overlapWindow: null
    onOverlapCandidateChanged: {
        if (overlapCandidate) overlapWindow = overlapCandidate;
    }
    function matchesOverlapWindow() {
        const win = root.overlapWindow;
        if (!root.appOverlapEnabled || !win || !ToplevelManager.toplevels.values.includes(win)) return false;
        const hypr = win.HyprlandToplevel?.handle;
        if (hypr?.monitor?.name !== root.screen?.name) return false;
        const client = HyprlandData.clientForToplevel(win);
        const workspace = hypr.workspace?.id;
        const special = root.thisMonitorData?.specialWorkspace?.id ?? 0;
        if (!client?.pinned && workspace !== root.overlapMonitor?.activeWorkspace?.id
            && !(special !== 0 && workspace === special)) return false;
        return root.classes.some(name =>
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
        onTriggered: root.appOverlapActive = root.wantsAppOverlap
    }
    Component.onCompleted: {
        if (overlapCandidate) overlapWindow = overlapCandidate;
    }
}
