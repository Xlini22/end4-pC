pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common

Singleton {
    id: root

    property var connections: []
    property var activeConnections: []
    property var activeWireguardInterfaces: []
    readonly property bool available: root.connections.length > 0 || root.active
    readonly property bool active: root.activeConnections.length > 0 || root.activeWireguardInterfaces.length > 0
    readonly property bool busy: connectProcess.running
    readonly property var activeNames: {
        const names = root.activeConnections.map(connection => connection.name)
        for (const interfaceName of root.activeWireguardInterfaces) {
            if (!names.includes(interfaceName)) names.push(interfaceName)
        }
        return names
    }
    readonly property string statusText: root.activeNames.length > 0
        ? root.activeNames.join(", ")
        : root.connections.length > 0 ? Translation.tr("Not connected") : Translation.tr("No VPN profiles")

    function parseNmcliLine(line) {
        const placeholder = "ESCAPED_COLON_PLACEHOLDER"
        return line.replace(/\\:/g, placeholder).split(":")
            .map(part => part.replace(new RegExp(placeholder, "g"), ":"))
    }

    function supportedType(type) {
        return type === "vpn" || type === "wireguard"
    }

    function isActive(connection) {
        if (!connection) return false
        return root.activeConnections.some(active => active.uuid === connection.uuid)
            || root.activeWireguardInterfaces.includes(connection.name)
    }

    function preferredConnection() {
        return root.connections.find(connection => connection.uuid === Config.options.sidebar.quickToggles.lastVpnUuid)
            ?? root.connections.find(connection => connection.autoconnect === "yes")
            ?? root.connections[0] ?? null
    }

    function refreshConnections() {
        if (!connectionsProcess.running) connectionsProcess.running = true
    }

    function refreshStatus() {
        if (!activeConnectionsProcess.running) activeConnectionsProcess.running = true
        if (!wireguardInterfacesProcess.running) wireguardInterfacesProcess.running = true
    }

    function refresh() {
        root.refreshConnections()
        root.refreshStatus()
    }

    function connect(connection) {
        if (!connection || root.busy) return
        Config.options.sidebar.quickToggles.lastVpnUuid = connection.uuid
        connectProcess.command = [
            "bash", "-c",
            "target_uuid=\"$1\"; shift; while [ \"$1\" != \"--\" ]; do [ \"$1\" = \"$target_uuid\" ] || nmcli connection down uuid \"$1\" >/dev/null 2>&1 || true; shift; done; shift; for iface in \"$@\"; do pkexec wg-quick down \"$iface\" >/dev/null 2>&1 || true; done; nmcli connection up uuid \"$target_uuid\"",
            "vpn-connect", connection.uuid,
            ...root.activeConnections.map(active => active.uuid), "--",
            ...root.activeWireguardInterfaces.filter(interfaceName =>
                !root.activeConnections.some(active => active.name === interfaceName || active.device === interfaceName))
        ]
        connectProcess.running = true
    }

    function disconnect(connection) {
        if (!connection || root.busy) return
        if (root.activeConnections.some(active => active.uuid === connection.uuid))
            Quickshell.execDetached(["nmcli", "connection", "down", "uuid", connection.uuid])
        if (root.activeWireguardInterfaces.includes(connection.name)
                && !root.activeConnections.some(active => active.name === connection.name))
            Quickshell.execDetached(["pkexec", "wg-quick", "down", connection.name])
        refreshDelay.restart()
    }

    function disconnectAll() {
        if (root.busy) return
        for (const connection of root.activeConnections)
            Quickshell.execDetached(["nmcli", "connection", "down", "uuid", connection.uuid])
        for (const interfaceName of root.activeWireguardInterfaces) {
            if (!root.activeConnections.some(active => active.name === interfaceName || active.device === interfaceName))
                Quickshell.execDetached(["pkexec", "wg-quick", "down", interfaceName])
        }
        refreshDelay.restart()
    }

    function toggle() {
        if (root.active) root.disconnectAll()
        else root.connect(root.preferredConnection())
    }

    // ponytail: settings keeps import/edit UI state; this singleton only shares runtime status/actions.
    // Move profile editing here only if another management UI needs it.
    Component.onCompleted: {
        console.assert(root.supportedType("vpn") && root.supportedType("wireguard") && !root.supportedType("ethernet"))
        console.assert(root.parseNmcliLine("Office\\: VPN:uuid:vpn:yes")[0] === "Office: VPN")
        root.refresh()
    }

    Timer {
        interval: 2500
        repeat: true
        running: true
        onTriggered: root.refreshStatus()
    }

    Timer {
        interval: 10000
        repeat: true
        running: true
        onTriggered: root.refreshConnections()
    }

    Timer {
        id: refreshDelay
        interval: 800
        repeat: false
        onTriggered: root.refresh()
    }

    Process {
        id: connectionsProcess
        command: ["nmcli", "-t", "-f", "NAME,UUID,TYPE,AUTOCONNECT", "connection", "show"]
        environment: ({ LANG: "C", LC_ALL: "C" })
        stdout: StdioCollector {
            onStreamFinished: {
                root.connections = text.trim().split("\n").filter(Boolean).map(line => {
                    const fields = root.parseNmcliLine(line)
                    return { name: fields[0] ?? "", uuid: fields[1] ?? "", type: fields[2] ?? "", autoconnect: fields[3] ?? "" }
                }).filter(connection => root.supportedType(connection.type)).sort((a, b) => a.name.localeCompare(b.name))
            }
        }
    }

    Process {
        id: activeConnectionsProcess
        command: ["nmcli", "-t", "-f", "NAME,UUID,TYPE,DEVICE", "connection", "show", "--active"]
        environment: ({ LANG: "C", LC_ALL: "C" })
        stdout: StdioCollector {
            onStreamFinished: {
                root.activeConnections = text.trim().split("\n").filter(Boolean).map(line => {
                    const fields = root.parseNmcliLine(line)
                    return { name: fields[0] ?? "", uuid: fields[1] ?? "", type: fields[2] ?? "", device: fields[3] ?? "" }
                }).filter(connection => root.supportedType(connection.type)).sort((a, b) => a.name.localeCompare(b.name))
                if (root.activeConnections.length > 0)
                    Config.options.sidebar.quickToggles.lastVpnUuid = root.activeConnections[0].uuid
            }
        }
    }

    Process {
        id: wireguardInterfacesProcess
        command: ["sh", "-c", "command -v wg >/dev/null 2>&1 && wg show interfaces 2>/dev/null || true"]
        stdout: StdioCollector {
            onStreamFinished: root.activeWireguardInterfaces = text.trim().split(/[ \n\t]+/).filter(Boolean)
        }
    }

    Process {
        id: connectProcess
        onExited: refreshDelay.restart()
    }
}
