import qs.modules.common
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property int magnifyId: -1
    readonly property var magnifyValue: DockStyle.magnifying ? DockMagnify.values[root.magnifyId] : null
    transformOrigin: Item.Bottom
    scale: root.magnifyValue?.scale ?? 1
    z: root.magnifyValue?.scale ?? 0
    transform: Translate {
        x: root.magnifyValue?.shift ?? 0
    }
    Component.onCompleted: root.magnifyId = DockMagnify.register(root)
    Component.onDestruction: DockMagnify.unregister(root.magnifyId)
    Layout.topMargin: DockStyle.mTop(DockStyle.separatorInnerMargin, DockStyle.separatorOuterMargin)
    Layout.bottomMargin: DockStyle.mBottom(DockStyle.separatorInnerMargin, DockStyle.separatorOuterMargin)
    Layout.leftMargin: DockStyle.mLeft(DockStyle.separatorInnerMargin, DockStyle.separatorOuterMargin)
    Layout.rightMargin: DockStyle.mRight(DockStyle.separatorInnerMargin, DockStyle.separatorOuterMargin)
    Layout.fillHeight: !DockStyle.vertical
    Layout.fillWidth: DockStyle.vertical
    implicitWidth: 1
    implicitHeight: 1
    color: Appearance.colors.colOutlineVariant
}
