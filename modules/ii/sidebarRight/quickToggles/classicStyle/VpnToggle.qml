import QtQuick
import qs.services
import qs.modules.common
import qs.modules.common.widgets

QuickToggleButton {
    visible: Vpn.available
    toggled: Vpn.active
    buttonIcon: Vpn.active ? "enhanced_encryption" : "vpn_key_off"
    onClicked: Vpn.toggle()

    StyledToolTip {
        text: Vpn.statusText
    }
}
