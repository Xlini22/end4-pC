import QtQuick
import QtQuick.Layouts
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.settings.connectivity

ContentPage {
    id: page
    forceWidth: true
    bottomContentPadding: 35

    function goTo(term) {
        const query = term.toLowerCase().trim()

        function findTarget(item) {
            for (let i = 0; i < item.children.length; i++) {
                const child = item.children[i]
                if (child.title && child.title.toLowerCase().includes(query))
                    return child
            }
            for (let i = 0; i < item.children.length; i++) {
                const found = findTarget(item.children[i])
                if (found) return found
            }
            return null
        }

        const target = findTarget(mainLayout)
        if (target) {
            const position = target.mapToItem(mainLayout, 0, 0)
            page.contentY = Math.max(0, position.y)
        }
    }

    ColumnLayout {
        id: mainLayout
        Layout.fillWidth: true
        spacing: 28

        WifiSection {}

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Appearance.colors.colOutlineVariant
            opacity: 0.45
        }

        BluetoothSection {}

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Appearance.colors.colOutlineVariant
            opacity: 0.45
        }

        VpnSection {}
    }
}
