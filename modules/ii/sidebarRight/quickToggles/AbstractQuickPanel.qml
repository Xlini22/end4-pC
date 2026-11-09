import QtQuick
import qs.modules.common

Rectangle {
    id: root

    radius: Appearance.rounding.normal
    color: (Config.options.background.widgets.glass.enable && Config.options.background.widgets.glass.elements.sidebar.enable) ? "transparent" : Appearance.colors.colLayer1

    signal openAudioOutputDialog()
    signal openAudioInputDialog()
    signal openBluetoothDialog()
    signal openNightLightDialog()
    signal openWifiDialog()
    signal openVpnDialog()
}
