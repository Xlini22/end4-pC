import QtQuick
import QtQuick.Layouts
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.functions

ContentPage {
    id: root
    forceWidth: true
    baseWidth: Math.max(280, Math.min(720, width - 40))
    property int selectedTab: 0
    readonly property string target: GlassProfiles.keys[selectedTab] ?? ""
    readonly property var profile: GlassProfiles.profile(target)
    property bool preview: false
    onPreviewChanged: syncPreview()
    onVisibleChanged: if (!visible) preview = false
    Component.onDestruction: if (GlobalStates.glassyPreviewPage === root) GlobalStates.glassyPreviewPage = null
    function syncPreview() {
        if (preview && visible && GlobalStates.settingsOpen && !GlobalStates.screenLocked)
            GlobalStates.glassyPreviewPage = root;
        else if (GlobalStates.glassyPreviewPage === root) GlobalStates.glassyPreviewPage = null;
    }
    Connections {
        target: GlobalStates
        function onSettingsOpenChanged() { if (!GlobalStates.settingsOpen) root.preview = false }
        function onScreenLockedChanged() { if (GlobalStates.screenLocked) root.preview = false }
    }
    readonly property bool satinProfileTabs: Config.options.background.widgets.glass.enable
        && Config.options.background.widgets.glass.elements.settings.enable
        && GlassCompositor.enhancedActive && GlassCompositor.frostedAvailable
    property bool multiEdit: false
    property var selectedProfiles: []
    readonly property var targets: multiEdit ? selectedProfiles : target ? [target] : []
    readonly property var automaticMode: commonValue("automaticDarkening")
    readonly property bool profileControlsEnabled: Config.options.background.widgets.glass.enable
        && targets.length > 0 && commonValue("enable") !== false
    readonly property real blurLimit: targets.some(key => ["bar", "terminal"].includes(key)) ? 8 : 16
    readonly property bool hasWindowTarget: targets.some(key => key !== "lockscreen")

    function commonValue(name) {
        if (targets.length === 0) return null;
        const value = GlassProfiles.profile(targets[0])[name];
        return targets.every(key => GlassProfiles.profile(key)[name] === value) ? value : null;
    }
    function writeValue(name, value, keys = targets) {
        for (const key of keys) {
            const p = GlassProfiles.profile(key);
            if (p[name] !== value) p[name] = value;
        }
    }
    function toggleMultiEdit() {
        if (!multiEdit) selectedProfiles = target ? [target] : [];
        multiEdit = !multiEdit;
    }
    function toggleProfile(key) {
        if (!GlassProfiles.keys.includes(key)) return;
        selectedProfiles = selectedProfiles.includes(key)
            ? selectedProfiles.filter(other => other !== key) : selectedProfiles.concat([key]);
    }
    function sliderPressed(control, name) {
        if (control.pressed) {
            control.editKeys = targets.slice();
            control.edited = false;
            control.editValue = control.value;
        } else {
            const keys = control.editKeys;
            control.editKeys = [];
            if (control.edited && control.enabled) writeValue(name, control.editValue, keys);
            control.edited = false;
        }
    }
    function sliderMoved(control, name) {
        if (control.pressed) { control.edited = true; control.editValue = control.value; }
        else if (control.enabled) writeValue(name, control.value);
    }
    function resetSelected() {
        for (const key of targets) GlassProfiles.reset(key);
    }
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
                buttonIcon: "extension"
                text: "HyprGlass"
                visible: WM.compositor === "hyprland"
                enabled: !GlassCompositor.pluginBusy
                checked: Config.options.background.widgets.glass.nativePlugin
                onClicked: {
                    GlassCompositor.setPluginEnabled(!Config.options.background.widgets.glass.nativePlugin)
                    checked = Qt.binding(() => Config.options.background.widgets.glass.nativePlugin)
                }
            }
            ConfigSwitch {
                buttonIcon: "auto_awesome"
                text: Translation.tr("Enhanced")
                checked: Config.options.background.widgets.glass.enhanced
                enabled: Config.options.background.widgets.glass.enable
                onCheckedChanged: if (checked !== Config.options.background.widgets.glass.enhanced) Config.options.background.widgets.glass.enhanced = checked
            }
        }
        StyledText {
            Layout.fillWidth: true
            visible: WM.compositor === "hyprland"
            text: GlassCompositor.pluginError || (GlassCompositor.pluginBusy
                ? Translation.tr("Saving HyprGlass settings…")
                : Translation.tr("HyprGlass changes require logging out and back in. Enabling it selects Windows underneath. Disabling it stops its effects without unloading the plugin in this session."))
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
    }
    Flow {
        Layout.fillWidth: true
        spacing: 8
        RippleButtonWithIcon {
            objectName: "glass-multi-edit"
            materialIcon: root.multiEdit ? "done" : "checklist"
            mainText: root.multiEdit ? Translation.tr("Edit one profile") : Translation.tr("Edit multiple profiles")
            toggled: root.multiEdit
            Accessible.name: mainText
            onClicked: root.toggleMultiEdit()
        }
        RippleButtonWithIcon {
            objectName: "glass-preview"
            materialIcon: root.preview ? "visibility_off" : "visibility"
            mainText: root.preview ? Translation.tr("Hide preview") : Translation.tr("Show selected elements")
            toggled: root.preview
            enabled: root.targets.length > 0 || root.preview
            Accessible.name: mainText
            onClicked: root.preview = !root.preview
        }
    }
    StyledText {
        Layout.fillWidth: true
        visible: root.preview
        text: Translation.tr("Preview keeps the selected bar, dock and sidebars visible while you edit. It ends when you leave this page.")
        wrapMode: Text.WordWrap
        color: Appearance.colors.colSubtext
    }
    StyledText {
        Layout.fillWidth: true
        visible: root.preview && (root.targets.includes("lockscreen") || root.targets.includes("terminal"))
        text: Translation.tr("For Terminal, use an open terminal. The lockscreen cannot be shown alongside Settings; preview does not lock the session.")
        wrapMode: Text.WordWrap
        color: Appearance.colors.colSubtext
    }
    Flow {
        Layout.fillWidth: true
        visible: root.multiEdit
        spacing: 6
        Repeater {
            model: GlassProfiles.keys
            RippleButtonWithIcon {
                id: profileButton
                required property string modelData
                required property int index
                objectName: "glass-select-" + modelData
                mainText: root.tabs[index]
                materialIcon: root.selectedProfiles.includes(modelData) ? "check_box" : "check_box_outline_blank"
                toggled: root.selectedProfiles.includes(modelData)
                colBackground: root.satinProfileTabs ? "transparent" : Appearance.colors.colLayer2
                colBackgroundHover: root.satinProfileTabs ? ColorUtils.transparentize(Appearance.colors.colLayer1Hover, 0.8) : Appearance.colors.colLayer1Hover
                colBackgroundToggled: root.satinProfileTabs ? ColorUtils.transparentize(Appearance.colors.colPrimary, 0.8) : Appearance.colors.colPrimary
                colBackgroundToggledHover: root.satinProfileTabs ? ColorUtils.transparentize(Appearance.colors.colPrimaryHover, 0.8) : Appearance.colors.colPrimaryHover
                property WindowGlass tabGlass: WindowGlass {
                    parent: profileButton.background
                    anchors.fill: parent
                    glassEnabled: root.satinProfileTabs
                    trackGeometry: false
                    nativeClip: root
                    cardRadius: parent.radius
                    tint: Appearance.colors.colLayer1
                    frost: root.satinProfileTabs ? Math.max(8, Config.options.background.widgets.glass.haze) : 0
                }
                Accessible.role: Accessible.CheckBox
                Accessible.name: mainText
                Accessible.checkable: true
                Accessible.checked: toggled
                onClicked: root.toggleProfile(modelData)
            }
        }
    }
    StyledText {
        Layout.fillWidth: true
        visible: root.multiEdit
        text: root.targets.length === 0 ? Translation.tr("Select at least one profile.")
            : Translation.tr("Only the controls you change are applied to the selected profiles. Mixed values are preserved until edited.")
        wrapMode: Text.WordWrap
        color: Appearance.colors.colSubtext
    }
    SecondaryTabBar {
        id: tabBar
        wheelNavigationEnabled: false
        wheelEnabled: false
        visible: !root.multiEdit
        Layout.fillWidth: true
        currentIndex: root.selectedTab
        onCurrentIndexChanged: root.selectedTab = currentIndex
        Repeater {
            model: root.tabs
            SecondaryTabButton {
                id: profileTab
                required property string modelData
                buttonText: modelData
                colBackground: root.satinProfileTabs
                    ? ColorUtils.transparentize(Appearance.colors.colSecondaryContainer, checked ? 0.8 : 1)
                    : ColorUtils.transparentize(Appearance.colors.colSurfaceContainer)
                colBackgroundHover: root.satinProfileTabs
                    ? ColorUtils.transparentize(checked ? Appearance.colors.colSecondaryContainerHover : Appearance.colors.colLayer1Hover, 0.8)
                    : ColorUtils.transparentize(Appearance.colors.colOnSurface, checked ? 1 : 0.95)
                property WindowGlass tabGlass: WindowGlass {
                    parent: profileTab.background
                    anchors.fill: parent
                    glassEnabled: root.satinProfileTabs
                    trackGeometry: false
                    nativeClip: root
                    cardRadius: parent.radius
                    tint: Appearance.colors.colLayer1
                    frost: root.satinProfileTabs ? Math.max(8, Config.options.background.widgets.glass.haze) : 0
                }
                font.pixelSize: Appearance.font.pixelSize.small
                Accessible.name: modelData
            }
        }
    }
    ContentSection {
        visible: root.targets.length > 0
        title: root.multiEdit ? Translation.tr("Selected profiles (%1)").arg(root.targets.length) : root.tabs[root.selectedTab]
        icon: root.multiEdit ? "checklist" : ["toast", "dock_to_bottom", "side_navigation", "settings", "lock", "terminal"][root.selectedTab]
        collapsible: false
        GroupedList {
            ConfigSwitch {
                buttonIcon: "water_drop"
                text: root.multiEdit ? Translation.tr("Enable Glassy for selected profiles") : Translation.tr("Enable Glassy for this element")
                readonly property bool groupedListCollapsed: root.commonValue("enable") === null
                visible: !groupedListCollapsed
                checked: root.commonValue("enable") === true
                enabled: Config.options.background.widgets.glass.enable
                onClicked: {
                    root.writeValue("enable", !root.commonValue("enable"));
                    checked = Qt.binding(() => root.commonValue("enable") === true);
                }
            }
            ConfigSelectionArray {
                readonly property bool groupedListCollapsed: root.commonValue("enable") !== null
                visible: !groupedListCollapsed
                icon: "water_drop"
                text: Translation.tr("Enable Glassy for selected profiles") + " (" + Translation.tr("Mixed") + ")"
                currentValue: null
                enabled: Config.options.background.widgets.glass.enable
                options: [{displayName: Translation.tr("Yes"), value: true}, {displayName: Translation.tr("No"), value: false}]
                onSelected: value => root.writeValue("enable", value)
            }
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.targets.includes("terminal")
            text: Translation.tr("Applies to Kitty, Foot, Alacritty, WezTerm and Konsole. The terminal background must be transparent to show the effect.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.targets.includes("terminal") && Config.options.background.widgets.glass.source !== "windows"
            text: Translation.tr("Choose Windows underneath to use Glassy in the terminal.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.targets.includes("lockscreen")
            text: Translation.tr("The lockscreen uses only its wallpaper as the glass background.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: Config.options.background.widgets.glass.source === "windows" && !GlassCompositor.profilesAvailable && root.hasWindowTarget
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
        GroupedList {
            ConfigSwitch {
                objectName: "glass-automatic-darkening"
                buttonIcon: "brightness_auto"
                text: Translation.tr("Automatic darkening")
                readonly property bool groupedListCollapsed: root.automaticMode === null
                visible: !groupedListCollapsed
                checked: root.automaticMode === true
                enabled: root.profileControlsEnabled
                onClicked: {
                    root.writeValue("automaticDarkening", !root.automaticMode);
                    checked = Qt.binding(() => root.automaticMode === true);
                }
            }
            ConfigSelectionArray {
                readonly property bool groupedListCollapsed: root.automaticMode !== null
                visible: !groupedListCollapsed
                icon: "brightness_auto"
                text: Translation.tr("Automatic darkening") + " (" + Translation.tr("Mixed") + ")"
                currentValue: null
                enabled: root.profileControlsEnabled
                options: [{displayName: Translation.tr("Yes"), value: true}, {displayName: Translation.tr("No"), value: false}]
                onSelected: value => root.writeValue("automaticDarkening", value)
            }
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.automaticMode === null
            text: Translation.tr("Automatic darkening is mixed. Choose a mode to show its slider; both saved values are preserved.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        ColumnLayout {
            Layout.fillWidth: true
            visible: root.automaticMode === true
            enabled: root.profileControlsEnabled
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                StyledText { Layout.fillWidth: true; text: Translation.tr("Automatic darkening intensity"); adaptiveGlass: true }
                StyledText { text: root.commonValue("automaticDarkeningStrength") === null && !automaticStrengthControl.pressed ? Translation.tr("Mixed") : Math.round(automaticStrengthControl.value) + "%"; color: Appearance.colors.colPrimary }
            }
            StyledSlider {
                id: automaticStrengthControl
                property var editKeys: []
                property bool edited: false
                property real editValue: 0
                objectName: "glass-automatic-darkening-strength"
                Layout.fillWidth: true
                animateValue: false
                from: 0
                to: 100
                stepSize: 1
                stopIndicatorValues: []
                value: root.commonValue("automaticDarkeningStrength") ?? 50
                tooltipContent: Math.round(value) + "%"
                Accessible.description: root.commonValue("automaticDarkeningStrength") === null ? Translation.tr("Mixed values. Adjust to apply a value to the selected profiles.") : ""
                Accessible.name: Translation.tr("Automatic darkening intensity")
                onPressedChanged: root.sliderPressed(automaticStrengthControl, "automaticDarkeningStrength")
                onMoved: root.sliderMoved(automaticStrengthControl, "automaticDarkeningStrength")
            }
            StyledText {
                Layout.fillWidth: true
                visible: Config.options.background.widgets.glass.source === "windows" && root.hasWindowTarget && !GlassCompositor.darkeningStrengthAvailable
                text: Translation.tr("Log out and back in to apply automatic darkening intensity to native glass.")
                wrapMode: Text.WordWrap
                color: Appearance.colors.colSubtext
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            visible: root.automaticMode === false
            enabled: root.profileControlsEnabled
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                StyledText { Layout.fillWidth: true; text: Translation.tr("Darkening"); adaptiveGlass: true }
                StyledText { text: root.commonValue("darkening") === null && !darkeningControl.pressed ? Translation.tr("Mixed") : Math.round(darkeningControl.value) + "%"; color: Appearance.colors.colPrimary }
            }
            StyledSlider {
                id: darkeningControl
                property var editKeys: []
                property bool edited: false
                property real editValue: 0
                animateValue: false
                objectName: "glass-darkening"
                Layout.fillWidth: true
                from: 0
                to: 100
                stepSize: 1
                stopIndicatorValues: []
                value: root.commonValue("darkening") ?? 50
                tooltipContent: Math.round(value) + "%"
                Accessible.description: root.commonValue("darkening") === null ? Translation.tr("Mixed values. Adjust to apply a value to the selected profiles.") : ""
                Accessible.name: Translation.tr("Darkening")
                onPressedChanged: root.sliderPressed(darkeningControl, "darkening")
                onMoved: root.sliderMoved(darkeningControl, "darkening")
            }
        }
        StyledText {
            Layout.fillWidth: true
            visible: root.automaticMode === true
            text: Translation.tr("Bright areas of the glass background are darkened automatically. Your manual value is preserved.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        StyledText {
            Layout.fillWidth: true
            visible: Config.options.background.widgets.glass.source === "windows"
                && (!GlassCompositor.darkeningAvailable || (root.automaticMode === true && !GlassCompositor.uniformDarkeningAvailable)) && root.hasWindowTarget
            text: Translation.tr("Darkening is saved. Log out and back in after updating the Glassy engine to apply it to windows underneath.")
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
        }
        Repeater {
            model: [
                { key: "rim", title: Translation.tr("Deformed edge"), max: 40, step: 1, unit: "%" },
                { key: "refraction", title: Translation.tr("Refraction"), max: 200, step: 5, unit: "%" },
                { key: "blur", title: Translation.tr("Internal blur"), max: root.blurLimit, step: 0.5, unit: " px" },
                { key: "reflections", title: Translation.tr("Edge reflections"), max: 100, step: 5, unit: "%" }
            ]
            ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                enabled: Config.options.background.widgets.glass.enable && Config.options.background.widgets.glass.enhanced && root.profileControlsEnabled
                spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    StyledText { Layout.fillWidth: true; text: modelData.title; adaptiveGlass: true }
                    StyledText { text: root.commonValue(modelData.key) === null && !control.pressed ? Translation.tr("Mixed") : (Math.round(control.value * 10) / 10) + modelData.unit; color: Appearance.colors.colPrimary }
                }
                StyledSlider {
                    id: control
                    property var editKeys: []
                    property bool edited: false
                    property real editValue: 0
                    objectName: "glass-" + modelData.key
                    Layout.fillWidth: true
                    from: 0
                    to: modelData.max
                    stepSize: modelData.step
                    stopIndicatorValues: []
                    value: root.commonValue(modelData.key) ?? modelData.max / 2
                    tooltipContent: (Math.round(value * 10) / 10) + modelData.unit
                    Accessible.name: modelData.title
                    Accessible.description: root.commonValue(modelData.key) === null ? Translation.tr("Mixed values. Adjust to apply a value to the selected profiles.") : ""
                    // ponytail: commit once on release; applying compositor changes every drag frame causes stalls.
                    onPressedChanged: root.sliderPressed(control, modelData.key)
                    onMoved: root.sliderMoved(control, modelData.key)
                }
            }
        }
        RippleButtonWithIcon {
            materialIcon: "restart_alt"
            mainText: root.multiEdit ? Translation.tr("Reset selected profiles") : Translation.tr("Reset this element")
            onClicked: root.resetSelected()
        }
    }
}
