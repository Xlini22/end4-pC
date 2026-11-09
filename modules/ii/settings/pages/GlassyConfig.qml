import QtQuick
import QtQuick.Layouts
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

ContentPage {
    id: root
    forceWidth: true
    baseWidth: Math.max(280, Math.min(720, width - 40))
    property int selectedTab: 0
    readonly property string target: GlassProfiles.keys[selectedTab]
    readonly property var profile: GlassProfiles.profile(target)
    readonly property var tabs: [Translation.tr("Bar"), Translation.tr("Dock"), Translation.tr("Sidebar"),
        Translation.tr("Settings"), Translation.tr("Lockscreen"), Translation.tr("Terminal")]

    RowLayout {
        Layout.fillWidth: true
        RippleButtonWithIcon {
            objectName: "glassy-back"
            materialIcon: "arrow_back"
            mainText: Translation.tr("Back")
            onClicked: GlobalStates.settingsSubpage = ""
        }
        StyledText {
            Layout.fillWidth: true
            text: Translation.tr("Glassy")
            font.pixelSize: Appearance.font.pixelSize.title
            font.weight: Font.DemiBold
            adaptiveGlass: true
        }
    }
    ContentSection {
        title: Translation.tr("General")
        icon: "water_drop"
        collapsible: false
        GroupedList {
            ConfigSwitch {
                buttonIcon: "water_drop"
                text: Translation.tr("Glassy UI")
                checked: Config.options.background.widgets.glass.enable
                onCheckedChanged: if (checked !== Config.options.background.widgets.glass.enable) Config.options.background.widgets.glass.enable = checked
            }
            ConfigSelectionArray {
                text: Translation.tr("Glass source")
                icon: "layers"
                visible: WM.compositor === "hyprland"
                enabled: Config.options.background.widgets.glass.enable
                currentValue: Config.options.background.widgets.glass.source
                onSelected: value => Config.options.background.widgets.glass.source = value
                options: [
                    { displayName: Translation.tr("Wallpaper"), icon: "wallpaper", value: "wallpaper" },
                    { displayName: Translation.tr("Windows underneath"), icon: "select_window", value: "windows" }
                ]
            }
            ConfigSwitch {
                buttonIcon: "auto_awesome"
                text: Translation.tr("Enhanced")
                checked: Config.options.background.widgets.glass.enhanced
                enabled: Config.options.background.widgets.glass.enable
                onCheckedChanged: if (checked !== Config.options.background.widgets.glass.enhanced) Config.options.background.widgets.glass.enhanced = checked
            }
        }
    }
    SecondaryTabBar {
        id: tabBar
        Layout.fillWidth: true
        currentIndex: root.selectedTab
        onCurrentIndexChanged: root.selectedTab = currentIndex
        Repeater {
            model: root.tabs
            SecondaryTabButton {
                required property string modelData
                buttonText: modelData
                font.pixelSize: Appearance.font.pixelSize.small
                Accessible.name: modelData
            }
        }
    }
    ContentSection {
        title: root.tabs[root.selectedTab]
        icon: ["toast", "dock_to_bottom", "side_navigation", "settings", "lock", "terminal"][root.selectedTab]
        collapsible: false
        GroupedList {
            ConfigSwitch {
                buttonIcon: "water_drop"
                text: Translation.tr("Enable Glassy for this element")
                checked: root.profile.enable
                enabled: Config.options.background.widgets.glass.enable
                onCheckedChanged: if (checked !== root.profile.enable) root.profile.enable = checked
            }
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.target === "terminal"
            text: Translation.tr("Applies to Kitty, Foot, Alacritty, WezTerm and Konsole. The terminal background must be transparent to show the effect.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.target === "terminal" && Config.options.background.widgets.glass.source !== "windows"
            text: Translation.tr("Choose Windows underneath to use Glassy in the terminal.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.target === "lockscreen"
            text: Translation.tr("The lockscreen uses only its wallpaper as the glass background.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: Config.options.background.widgets.glass.source === "windows" && !GlassCompositor.profilesAvailable && root.target !== "lockscreen"
            text: Translation.tr("The controls are saved. Log out and back in to load the updated Glassy engine.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: !Config.options.background.widgets.glass.enhanced
            text: Translation.tr("Enable Enhanced to use the individual optical controls.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        Repeater {
            model: [
                { key: "rim", title: Translation.tr("Deformed edge"), max: 40, step: 1, unit: "%" },
                { key: "refraction", title: Translation.tr("Refraction"), max: 200, step: 5, unit: "%" },
                { key: "blur", title: Translation.tr("Internal blur"), max: ["bar", "terminal"].includes(root.target) ? 8 : 16, step: 0.5, unit: " px" },
                { key: "reflections", title: Translation.tr("Edge reflections"), max: 100, step: 5, unit: "%" }
            ]
            ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                enabled: Config.options.background.widgets.glass.enable && Config.options.background.widgets.glass.enhanced && root.profile.enable
                spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    StyledText { Layout.fillWidth: true; text: modelData.title; adaptiveGlass: true }
                    StyledText { text: (Math.round(control.value * 10) / 10) + modelData.unit; color: Appearance.colors.colPrimary }
                }
                StyledSlider {
                    id: control
                    objectName: "glass-" + modelData.key
                    Layout.fillWidth: true
                    from: 0
                    to: modelData.max
                    stepSize: modelData.step
                    stopIndicatorValues: []
                    value: root.profile[modelData.key]
                    tooltipContent: (Math.round(value * 10) / 10) + modelData.unit
                    Accessible.name: modelData.title
                    // ponytail: commit once on release; applying compositor changes every drag frame causes stalls.
                    onPressedChanged: if (!pressed) root.profile[modelData.key] = value
                    onMoved: if (!pressed) root.profile[modelData.key] = value
                }
            }
        }
        RippleButtonWithIcon {
            materialIcon: "restart_alt"
            mainText: Translation.tr("Reset this element")
            onClicked: GlassProfiles.reset(root.target)
        }
    }
}
