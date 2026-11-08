import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

DockButton {
    magnifiable: true
    magnifyBaseline: contentItem.y + (contentItem.height + contentItem.iconSize) / 2
    visible: Config.options.dock.showAppsButton
    Layout.topMargin: 0
    Layout.leftMargin: 0
    innerInset: DockStyle.appsButtonInnerInset
    outerInset: DockStyle.appsButtonOuterInset

    contentItem: MaterialSymbol {
        renderType: Text.QtRendering
        anchors.fill: parent
        horizontalAlignment: Text.AlignHCenter
        iconSize: DockStyle.buttonBase / 2
        text: "apps"
        color: Appearance.colors.colOnLayer0
    }
}
