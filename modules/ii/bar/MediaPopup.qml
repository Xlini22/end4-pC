import qs
import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import Quickshell.Services.Mpris

StyledPopup {
    id: root

    readonly property MprisPlayer activePlayer: MprisController.activePlayer

    popupContentMargin: 0
    popupColor: "transparent"
    popupRadius: 0
    popupBorderWidth: 0
    active: !GlobalStates.mediaControlsOpen
        && root.activePlayer !== null
        && root.hoverTarget && root.hoverTarget.containsMouse
        && Config.options.bar.tooltips.enable

    Player {
        player: root.activePlayer
        visualizerPoints: GlobalStates.visualizerPoints
        implicitWidth: Appearance.sizes.mediaControlsWidth
        implicitHeight: Appearance.sizes.mediaControlsHeight
        radius: Appearance.rounding.screenRounding - Appearance.sizes.hyprlandGapsOut + 1
        showLyrics: false
    }
}
