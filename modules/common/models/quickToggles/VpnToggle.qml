import QtQuick
import qs.services
import qs.modules.common
import qs.modules.common.widgets

QuickToggleModel {
    name: Translation.tr("VPN")
    statusText: Vpn.statusText
    tooltipText: Vpn.statusText
    icon: Vpn.active ? "enhanced_encryption" : "vpn_key_off"
    available: Vpn.available
    toggled: Vpn.active
    mainAction: () => Vpn.toggle()
    hasMenu: true
}
