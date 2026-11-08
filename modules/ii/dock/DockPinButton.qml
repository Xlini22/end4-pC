import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

VerticalButtonGroup {
    id: root

    property bool pinned: false
    property int magnifyId: -1
    readonly property var magnifyValue: DockStyle.magnifying ? DockMagnify.values[root.magnifyId] : null
    transformOrigin: Item.Bottom
    scale: root.magnifyValue?.scale ?? 1
    z: root.magnifyValue?.scale ?? 0
    transform: Translate {
        x: root.magnifyValue?.shift ?? 0
        y: (root.scale - 1) * (root.height - pinButton.parent.y - pinButton.y
            - pinButton.contentItem.y - (pinButton.contentItem.height + pinButton.contentItem.iconSize) / 2)
    }
    Component.onCompleted: root.magnifyId = DockMagnify.register(root)
    Component.onDestruction: DockMagnify.unregister(root.magnifyId)
    readonly property real alongMargin: Appearance.sizes.hyprlandGapsOut + (pinned ? 4 : 0)
    signal toggled()

    visible: Config.options.dock.showPinButton
    Layout.alignment: DockStyle.vertical ? Qt.AlignHCenter : Qt.AlignVCenter
    Layout.topMargin: DockStyle.mTop(DockStyle.pinInnerMargin, 0, alongMargin)
    Layout.bottomMargin: DockStyle.mBottom(DockStyle.pinInnerMargin, 0, alongMargin)
    Layout.leftMargin: DockStyle.mLeft(DockStyle.pinInnerMargin, 0, alongMargin)
    Layout.rightMargin: DockStyle.mRight(DockStyle.pinInnerMargin, 0, alongMargin)

    GroupButton {
        id: pinButton
        baseWidth: DockStyle.pinButtonSize
        baseHeight: DockStyle.pinButtonSize
        clickedWidth: baseWidth
        clickedHeight: baseHeight + 20
        buttonRadius: Appearance.rounding.normal
        toggled: root.pinned
        onClicked: root.toggled()
        contentItem: MaterialSymbol {
            renderType: Text.QtRendering
            text: "keep"
            horizontalAlignment: Text.AlignHCenter
            iconSize: Appearance.font.pixelSize.larger
            color: root.pinned ? Appearance.m3colors.m3onPrimary : Appearance.colors.colOnLayer0
        }
    }
}
