import qs.modules.common
import qs.modules.common.widgets
import qs.services
import qs.modules.ii.sidebarRight.notifications
import Qt5Compat.GraphicalEffects
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    WindowGlass {
        id: notificationGlass
        anchors.fill: parent
        cardRadius: root.radius
        tint: Appearance.colors.colLayer1
        frost: Math.max(8, Config.options.background.widgets.glass.haze)
    }
    radius: Appearance.rounding.normal
    color: notificationGlass.live ? "transparent" : Appearance.colors.colLayer1

    NotificationList {
        anchors.fill: parent
        anchors.margins: 5
    }
}
