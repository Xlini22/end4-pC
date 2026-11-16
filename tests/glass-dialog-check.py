"""Run: python3 tests/glass-dialog-check.py. Offscreen CPU-only composition check.
Use the production mask and region sender; never render on the hardware GPU.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
sidebar = (repo / 'modules/ii/sidebarRight/SidebarRightContent.qml').read_text()
mask = re.search(r'            layer.enabled: root.activeDialog[\s\S]*?\n            \}', sidebar)[0]
compositor = (repo / 'services/GlassCompositor.qml').read_text()
sender = re.search(r'    function sendRegions\([\s\S]*?\n    \}', compositor)[0]
ordering = r'''
const assert = require('node:assert/strict'), vm = require('node:vm');
const win = {width: 470, height: 1080};
function region(x, width, height, priority = 0) {
    return {win, name: 'quickshell:sidebarRight', monitor: 'eDP-1', priority,
        values: [x, 0, width, height, 20, 20, 20, 20, 0, 0, 0, 0, 0, 1, 8]};
}
const outer = region(0, 450, 1060), card = region(10, 420, 180);
const modal = region(50, 350, 600, 1), button = region(25, 50, 36);
const context = {enhancedAvailable: true, enhancedActive: true, frostedAvailable: true,
    regionsBusy: false, regionsPending: true, regionsApplied: '', regionsRejected: '',
    regionWrites: 0, regionsSent: '', regionSocket: {connected: false},
    Quickshell: {processId: 42}};
context.root = context;
vm.createContext(context); vm.runInContext(SENDER, context);
for (const items of [[outer, modal, card, button], [button, card, modal, outer], [button, outer, card]]) {
    context.glassItems = items.map(value => ({nativeRegion: () => value}));
    context.regionsBusy = false;
    context.sendRegions();
    const wire = context.regionsSent.split(' '), values = wire.slice(9).map(Number);
    assert.deepEqual(wire.slice(0, 8), ['end4glass','42','2','1','quickshell:sidebarRight','eDP-1','470','1080']);
    assert.equal(Number(wire[8]), items.length);
    assert.equal(values.length, items.length * 15); // Priority never changes the native IPC format.
    assert.deepEqual(items.map((_, i) => values[i * 15]), items.length === 4 ? [0, 10, 25, 50] : [0, 10, 25]);
}
'''.replace('SENDER', json.dumps(sender))

with tempfile.TemporaryDirectory(prefix='glass-dialog-check-') as directory:
    temporary = Path(directory)
    script = temporary / 'order.js'
    script.write_text(ordering)
    subprocess.run(['node', str(script)], check=True, timeout=10)
    os.chmod(temporary, 0o700)
    os.environ.update(QT_QPA_PLATFORM='offscreen', QT_QPA_PLATFORMTHEME='',
                      XDG_RUNTIME_DIR=directory, XDG_CACHE_HOME=directory,
                      LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe',
                      MESA_LOADER_DRIVER_OVERRIDE='llvmpipe', MESA_SHADER_CACHE_DISABLE='true',
                      LP_NUM_THREADS='2', QT_QUICK_BACKEND='rhi', QSG_RHI_BACKEND='opengl',
                      QSG_RENDER_LOOP='basic', PULSE_SERVER='unix:' + directory + '/no-pulse')
    from PySide6.QtCore import QObject, QSize, QUrl
    from PySide6.QtGui import QGuiApplication, QOpenGLContext, QOffscreenSurface
    from PySide6.QtQml import QQmlEngine, QQmlComponent
    from PySide6.QtOpenGL import QOpenGLFramebufferObject
    from PySide6.QtQuick import (QQuickWindow, QSGRendererInterface, QQuickRenderControl,
                                QQuickRenderTarget, QQuickGraphicsDevice)

    app = QGuiApplication([])
    surface = QOffscreenSurface()
    surface.create()
    context = QOpenGLContext()
    assert context.create() and context.makeCurrent(surface), 'Offscreen software OpenGL unavailable'
    renderer = context.functions().glGetString(0x1F01)
    assert 'llvmpipe' in renderer.lower(), 'Refusing hardware renderer: ' + renderer
    context.doneCurrent()
    QQuickWindow.setSceneGraphBackend('rhi')
    QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGL)
    effect = re.search(r'    ShaderEffect \{[\s\S]*?\n    \}', (repo/'modules/common/widgets/FrostedGlass.qml').read_text())[0]
    (temporary/'shaders').symlink_to(repo/'modules/common/widgets/shaders', target_is_directory=True)
    glass_fixture = '''
    Loader { anchors.fill: parent; active: root.checkGlass; sourceComponent: Item {
    id: glassRoot; anchors.fill: parent
    property real darkening: root.testDarkening
    property real automaticDarkening: root.testAutomatic
    property real topLeftRadius: 0; property real topRightRadius: 0
    property real bottomRightRadius: 0; property real bottomLeftRadius: 0
    property real rimWidth: 1; property real pull: 0; property real split: 0
    property real haze: 1; property real vividness: 1; property real sheen: 0
    property real flareLeft: 0; property real flareRight: 0
    property real hangLeft: 0; property real hangRight: 0; property real edge: 0
    property bool enhanced: true; property real frost: 8
    property color washColor: "black"; property real washOpacity: 0
    Item {
        id: source; width: 320; height: 240
        Rectangle { width: 320; height: 120; color: "#e6e6e6" }
        Rectangle { y: 120; width: 320; height: 120; color: "#b4b4b4" }
    }
    ShaderEffectSource { id: capture; sourceItem: source; hideSource: true; mipmap: true; visible: false }
    EFFECT
}
    }
'''.replace('EFFECT', effect.replace('root.', 'glassRoot.'))
    fixture = temporary / 'mask.qml'
    fixture.write_text('''import QtQuick
import Qt5Compat.GraphicalEffects
Rectangle {
    id: root; width: 320; height: 240; color: "black"
    property Item activeDialog: modal
    property bool checkGlass: false
    property real testDarkening: 0
    property real testAutomatic: 0
    Item { id: modal; objectName: "modal"; property bool glassActive: true; property Item backgroundItem: pane }
    Rectangle { id: pane; objectName: "pane"; x: 80; y: 70; width: 140; height: 100; radius: 20; visible: false }
    Item {
        id: sectionColumn; width: 320; height: 240; visible: !root.checkGlass
        Rectangle { anchors.fill: parent; color: "#00ff00" }
        MASK
    }
    GLASS_FIXTURE
}'''.replace('MASK', mask).replace('GLASS_FIXTURE', glass_fixture))
    context.makeCurrent(surface)
    control = QQuickRenderControl()
    window = QQuickWindow(control)
    window.setGraphicsDevice(QQuickGraphicsDevice.fromOpenGLContext(context))
    window.setGeometry(0, 0, 320, 240)
    framebuffer = QOpenGLFramebufferObject(QSize(320, 240), QOpenGLFramebufferObject.CombinedDepthStencil)
    assert framebuffer.isValid()
    window.setRenderTarget(QQuickRenderTarget.fromOpenGLTexture(framebuffer.texture(), QSize(320, 240)))
    assert control.initialize()
    engine = QQmlEngine()
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(fixture)))
    assert component.status() == QQmlComponent.Ready, component.errors()
    scene = component.create()
    scene.setParentItem(window.contentItem())

    def capture(expected):
        # Render successive frames so both source and mask textures reflect the changed geometry.
        for _ in range(12):
            app.processEvents()
            context.makeCurrent(surface)
            control.polishItems()
            control.beginFrame()
            control.sync()
            control.render()
            control.endFrame()
            context.makeCurrent(surface)
            context.functions().glFinish()
            image = framebuffer.toImage()
            assert window.rendererInterface().graphicsApi() == QSGRendererInterface.OpenGL
            if not image.isNull() and all(image.pixelColor(x, y).name() == color for x, y, color in expected):
                return image
        raise AssertionError([(x, y, color, image.pixelColor(x, y).name()) for x, y, color in expected])

    capture([(20, 100, '#00ff00'), (120, 110, '#000000'), (81, 71, '#00ff00')])
    pane = scene.findChild(QObject, 'pane')
    modal = scene.findChild(QObject, 'modal')
    pane.setProperty('x', 140)
    capture([(110, 110, '#00ff00'), (180, 110, '#000000')])
    modal.setProperty('glassActive', False)
    capture([(180, 110, '#00ff00')])
    modal.setProperty('glassActive', True)
    capture([(180, 110, '#000000')])
    pane.setProperty('height', 1)
    capture([(180, 110, '#00ff00')])
    scene.setProperty('activeDialog', None)
    capture([(180, 110, '#00ff00')])
    scene.setProperty('checkGlass', True)
    capture([(160,60,'#e6e6e6'),(160,180,'#b4b4b4')])
    scene.setProperty('testDarkening', .5)
    capture([(160,60,'#737373'),(160,180,'#5a5a5a')])
    scene.setProperty('testAutomatic', 1)
    capture([(160,60,'#616161'),(160,180,'#4c4c4c')])
    scene.setParentItem(None)
    control.invalidate()
print('CPU llvmpipe pixels: rounded modal cutout, movement, toggles, reopen/close native material ordering and Qt vertex darkening passed.')
