pragma Singleton
pragma ComponentBehavior: Bound

import Quickshell
import Quickshell.Bluetooth
import Quickshell.Io
import QtQuick

Singleton {
    id: root

    readonly property bool available: Bluetooth.adapters.values.length > 0
    property bool enabled: false

    function poweredFromBluetoothctl(output): bool {
        return /^\s*Powered:\s*yes\s*$/mi.test(String(output ?? ""));
    }

    function refreshPowerState() {
        if (!powerStateProcess.running)
            powerStateProcess.running = true;
    }

    // BlueZ can leave Device1.Connected false when a device reconnects on its
    // own, while audio, AVRCP and battery reporting are all live
    // (https://github.com/bluez/bluez/issues/2485). Battery1 is only exported
    // while a device is connected, so count it as a connection too.
    function isConnected(device): bool {
        return !!device && (device.connected || device.batteryAvailable);
    }

    readonly property BluetoothDevice firstActiveDevice: Bluetooth.devices.values.find(device => root.isConnected(device)) ?? null
    readonly property int activeDeviceCount: Bluetooth.devices.values.filter(device => root.isConnected(device)).length
    readonly property bool connected: Bluetooth.devices.values.some(d => root.isConnected(d))

    function sortFunction(a, b) {
        // Ones with meaningful names before MAC addresses
        const macRegex = /^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$/;
        const aIsMac = macRegex.test(a.name);
        const bIsMac = macRegex.test(b.name);
        if (aIsMac !== bIsMac)
            return aIsMac ? 1 : -1;

        // Alphabetical by name
        return a.name.localeCompare(b.name);
    }
    property list<var> connectedDevices: Bluetooth.devices.values.filter(d => root.isConnected(d)).sort(sortFunction)
    property list<var> pairedButNotConnectedDevices: Bluetooth.devices.values.filter(d => d.paired && !root.isConnected(d)).sort(sortFunction)
    property list<var> unpairedDevices: Bluetooth.devices.values.filter(d => !d.paired && !root.isConnected(d)).sort(sortFunction)
    readonly property list<var> connectedBatteryDevices: connectedDevices.filter(device => device.batteryAvailable && Number.isFinite(Number(device.battery)))
    readonly property var primaryConnectedDevice: firstActiveDevice ?? connectedDevices[0] ?? null
    readonly property var primaryBatteryDevice: hasBattery(primaryConnectedDevice)
        ? primaryConnectedDevice
        : connectedBatteryDevices[0] ?? null
    property list<var> friendlyDeviceList: [
        ...connectedDevices,
        ...pairedButNotConnectedDevices,
        ...unpairedDevices
    ]

    function hasBattery(device): bool {
        return !!device && device.batteryAvailable && Number.isFinite(Number(device.battery));
    }

    function togglePower() {
        if (!root.available || togglePowerProcess.running) return;
        togglePowerProcess.command = root.enabled
            ? ["bluetoothctl", "power", "off"]
            : ["bash", "-lc", "rfkill unblock bluetooth && bluetoothctl power on"];
        togglePowerProcess.running = true;
    }

    // ponytail: poll BlueZ because Quickshell's adapter.enabled is stale on this hardware;
    // replace with an Adapter1 PropertiesChanged subscription if sub-second updates become necessary.
    Timer {
        interval: 2000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.refreshPowerState()
    }

    Process {
        id: powerStateProcess
        command: ["bluetoothctl", "show"]

        stdout: StdioCollector {
            onStreamFinished: root.enabled = root.poweredFromBluetoothctl(text)
        }
    }

    Process {
        id: togglePowerProcess

        onExited: {
            powerRefreshDelay.restart();
        }
    }

    Timer {
        id: powerRefreshDelay
        interval: 250
        repeat: false
        onTriggered: root.refreshPowerState()
    }

    Component.onCompleted: {
        console.assert(root.poweredFromBluetoothctl("Powered: yes"));
        console.assert(!root.poweredFromBluetoothctl("Powered: no"));
    }
}
