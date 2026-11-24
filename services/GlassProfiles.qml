pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Wayland
import qs
import qs.modules.common

Singleton {
    id: root
    readonly property var keys: ["bar", "dock", "sidebar", "settings", "lockscreen", "terminal"]
    readonly property string signature: JSON.stringify(keys.map(key => {
        const p = profile(key)
        return [key, p.enable, p.rim, p.refraction, p.blur, p.reflections, p.darkening, p.automaticDarkening, p.automaticDarkeningStrength]
    }))

    function profile(key) { return Config.options.background.widgets.glass.elements[key] ?? null }
    function keyFor(namespace, fullscreen = false) {
        if (fullscreen) return "lockscreen"
        if (["quickshell:bar", "quickshell:verticalBar"].includes(namespace)) return "bar"
        if (namespace === "quickshell:dock") return "dock"
        if (["quickshell:sidebarLeft", "quickshell:sidebarRight"].includes(namespace)) return "sidebar"
        if (["quickshell:settings", "quickshell:dashboard"].includes(namespace)) return "settings"
        return ""
    }
    function enabledFor(namespace, fullscreen = false) {
        return profile(keyFor(namespace, fullscreen))?.enable ?? true
    }
    function enabledForItem(item) {
        const win = item.QsWindow.window
        if (GlobalStates.screenLocked) return profile("lockscreen").enable
        if (!win || win.anchor !== undefined) return true
        return enabledFor(win.anchors === undefined ? (win.title === "illogical-impulse Settings" ? "quickshell:settings" : "") : win.WlrLayershell.namespace)
    }
    function defaults(key) {
        return { enable: key !== "terminal", rim: key === "bar" ? 24 : 7,
            refraction: key === "bar" ? 200 : 135,
            blur: key === "bar" ? 1 : key === "lockscreen" ? Config.options.background.widgets.glass.haze : key === "terminal" ? 3 : Math.max(8, Config.options.background.widgets.glass.haze), reflections: 50, darkening: 0, automaticDarkening: false, automaticDarkeningStrength: 100 }
    }
    function darkeningStrength(profile) {
        return Number.isFinite(profile?.automaticDarkeningStrength) ? Math.max(0, Math.min(100, profile.automaticDarkeningStrength)) / 100 : 1
    }
    function reset(key) {
        const p = profile(key), values = defaults(key)
        for (const name of Object.keys(values)) p[name] = values[name]
    }
    function optics(key) {
        const p = profile(key)
        const limit = (value, min, max, fallback) => Number.isFinite(value) ? Math.max(min, Math.min(max, value)) : fallback
        return [limit(p.rim, 0, 40, 7) / 100, limit(p.refraction, 0, 200, 135) / 100,
            limit(p.blur, 0, ["bar", "terminal"].includes(key) ? 8 : 16, 0), limit(p.reflections, 0, 100, 50) / 100]
    }
}
