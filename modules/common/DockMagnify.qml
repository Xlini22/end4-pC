pragma Singleton

import QtQuick
import Quickshell

Singleton {
    id: root

    property var entries: []
    property int nextId: 0
    property var values: ({})
    property real leftExtra: 0
    property real rightExtra: 0
    readonly property real totalExtra: leftExtra + rightExtra
    property real amplitude: 0
    property real pointer: NaN
    property var window: null

    // Build UI's 40px icons, 110px influence and 40px nudge at 2.25x, scaled to our settings.
    readonly property real influenceDistance: 110 * DockStyle.iconSize / 40
    readonly property real nudge: DockStyle.iconSize * (DockStyle.magnification - 1) / 1.25

    function register(item) {
        const id = root.nextId++;
        root.entries.push({ id: id, item: item });
        return id;
    }

    function unregister(id) {
        root.entries = root.entries.filter(entry => entry.id !== id);
    }

    function clear() {
        if (Object.keys(root.values).length > 0) root.values = ({});
        root.leftExtra = 0;
        root.rightExtra = 0;
    }

    function recompute() {
        if (!DockStyle.magnifying || root.amplitude <= 0.001 || !isFinite(root.pointer) || root.window === null) {
            root.clear();
            return;
        }

        const list = [];
        for (const entry of root.entries) {
            const item = entry.item;
            if (!item || !item.visible || !item.parent || item.QsWindow.window !== root.window) continue;
            const center = item.parent.mapToItem(null, item.x + item.width / 2, 0).x;
            list.push({ id: entry.id, center: center, base: Math.max(1, item.width) });
        }
        if (list.length === 0) {
            root.clear();
            return;
        }
        list.sort((a, b) => a.center - b.center);

        const next = {};
        for (const entry of list) {
            const distance = root.pointer - entry.center;
            const fraction = Math.min(1, Math.abs(distance) / root.influenceDistance);
            const scale = 1 + (DockStyle.magnification - 1) * root.amplitude * (1 - fraction);
            const shift = -Math.sign(distance) * root.nudge * root.amplitude
                * (fraction < 1 ? fraction * scale : 1);
            next[entry.id] = { scale: scale, shift: shift };
        }
        root.values = next;
        const first = list[0], last = list[list.length - 1];
        root.leftExtra = Math.max(0, -next[first.id].shift + (next[first.id].scale - 1) * first.base / 2);
        root.rightExtra = Math.max(0, next[last.id].shift + (next[last.id].scale - 1) * last.base / 2);
    }

    onPointerChanged: root.recompute()
    onAmplitudeChanged: root.recompute()
    onWindowChanged: root.recompute()
    Connections {
        target: DockStyle
        function onMagnifyingChanged() { root.recompute() }
        function onMagnificationChanged() { root.recompute() }
        function onIconSizeChanged() { root.recompute() }
    }
}
