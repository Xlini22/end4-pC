"""Check moving pixels and workspace switches with the production WindowGlass.
Run in a Wayland session: python3 tests/native-glass-motion-check.py --plugin /path/to/hyprglass.so
Starts and cleans up an isolated nested compositor; never switches the main desktop.
Requires existing Hyprland, Quickshell, grim and Python Pillow.
"""
import atexit
import tempfile
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image

FIXTURE = '''//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets
ShellRoot {
    id: root
    property bool cornerProbe: false
    property bool cornerDigits: false
    property bool largePanel: false
    property bool frostProbe: false
    property real frost: 0
    property bool benchmarking: false
    property real panelOffsetY: 0
    property real panelOffsetX: 0
    property bool blackProbe: false
    IpcHandler {
        target: "glass-check"
        function useNative(value: bool): void { Config.options.background.widgets.glass.trueGlassy = value }
        function useEnhanced(value: bool): void { Config.options.background.widgets.glass.enhanced = value }
        function moveCard(): void { secondCard.x += 12 }
        function scaleCard(): void { cardScale.xScale = 0.85; cardScale.yScale = 0.85 }
        function probeCorners(value: bool): void {
            root.cornerProbe = value
            Config.options.background.widgets.glass.haze = value ? 0 : 4
        }
        function showCornerDigits(): void { root.cornerDigits = true }
        function probeLargePanel(value: bool): void { root.largePanel = value }
        function benchmarkPanel(): void { root.largePanel = true; root.benchmarking = true; secondCard.visible = false }
        function setBlur(value: real): void { Config.options.background.widgets.glass.haze = value }
        function setFrost(value: real): void { root.frost = value }
        function probeFrost(): void { root.frostProbe = true; root.blackProbe = false; secondCard.visible = false }
        function probeBlack(): void { root.blackProbe = true }
        function moveFrost(value: real): void { root.panelOffsetX = value }
        function shiftPanel(value: bool): void { root.panelOffsetY = value ? -230 : 0; secondCard.visible = !value }
        function jigglePanel(): void { root.panelOffsetY = root.panelOffsetY > 0 ? -8 : 8 }
        function churnClients(): void { HyprlandData.windowList = HyprlandData.windowList.slice() }
        function state(): string {
            return JSON.stringify({native: pane.nativeGlass, windows: pane.windowBackdrop,
                captures: GlassLayers.backdropConsumers, writes: GlassCompositor.configurationWrites,
                enhanced: GlassCompositor.enhancedActive, frosted: GlassCompositor.frostedAvailable, regions: GlassCompositor.regionsApplied})
        }
    }
    component Scene: Window {
        id: scene
        required property color baseColor
        visible: true
        width: 1000; height: 1100
        color: baseColor
        Repeater {
            model: 36
            Rectangle {
                required property int index
                x: (index % 6) * 180; y: Math.floor(index / 6) * 180
                width: 80; height: 80
                color: "#44ffffff"
            }
        }
        Rectangle {
            x: 0; y: scene.height / 2 + 100
            width: parent.width; height: 12
            color: "white"
        }
        Rectangle {
            width: 80; height: parent.height
            color: "white"
            SequentialAnimation on x {
                loops: Animation.Infinite
                NumberAnimation { from: 0; to: scene.width - 80; duration: 2200 }
                NumberAnimation { from: scene.width - 80; to: 0; duration: 2200 }
            }
        }
        Canvas {
            anchors.fill: parent
            visible: root.cornerProbe
            property bool digits: root.cornerDigits
            property bool large: root.largePanel
            property bool stripes: root.frostProbe
            property bool black: root.blackProbe
            onBlackChanged: requestPaint()
            onStripesChanged: requestPaint()
            onDigitsChanged: requestPaint()
            onLargeChanged: requestPaint()
            onVisibleChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                const c = getContext("2d")
                if (black) { c.fillStyle = "black"; c.fillRect(0, 0, width, height); return }
                if (stripes) {
                    c.fillStyle = "#202020"; c.fillRect(0, 0, width, height)
                    c.fillStyle = "#eeeeee"
                    for (let x = 0; x < width; x += 12) c.fillRect(x, 0, 6, height)
                    return
                }
                const w = large ? 800 : 420, h = large ? 720 : 280, inset = large ? 32 : 16
                c.fillStyle = "#101010"; c.fillRect(0, 0, width, height)
                c.fillStyle = "#1976d2"; c.fillRect(width / 2 - w / 2, height / 2 - h / 2, w, h)
                c.fillStyle = "#20d040"; c.fillRect(width / 2 - w / 2 + inset, height / 2 - h / 2 + inset, w - inset * 2, h - inset * 2)
                if (digits) {
                    c.font = "bold 40px sans-serif"; c.fillStyle = "white"
                    for (const dx of [-w / 2 + 3, w / 2 - 28]) for (const dy of [-h / 2 + 43, h / 2 - 4])
                        c.fillText("6", width / 2 + dx, height / 2 + dy)
                }
            }
        }
    }
    Timer {
        interval: 1000; repeat: true; running: true
        onTriggered: console.log("NATIVE PRODUCTION", pane.nativeGlass, GlassCompositor.available, GlassLayers.backdropConsumers)
    }
    Scene { title: "glass-red"; baseColor: "#c62828" }
    Scene { title: "glass-blue"; baseColor: "#1565c0" }
    // A second, differently sized surface exercises independent blur buffers.
    PanelWindow {
        anchors { top: true; left: true; right: true }
        implicitHeight: 68
        exclusiveZone: 0
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "quickshell:bar"
        color: "transparent"
        WindowGlass { anchors.fill: parent; cardRadius: 20; tint: "white" }
        Item {
            x: 200; y: 8; width: 300; height: 52
            WindowGlass { anchors.fill: parent; cardRadius: 18; tint: "white" }
        }
    }
    PanelWindow {
        anchors { top: true; bottom: true; left: true; right: true }
        exclusiveZone: 0
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "quickshell:settings"
        color: "transparent"
        // Opaque content outside every glass card must survive sample cropping.
        Rectangle { x: parent.width - 40; y: parent.height - 40; width: 30; height: 30; color: "#ff00cc" }
        Rectangle {
            id: secondCard
            x: 20; y: 20; width: 180; height: 90; radius: 22
            color: "transparent"
            transform: Scale { id: cardScale; origin.x: 90; origin.y: 45 }
            WindowGlass { anchors.fill: parent; cardRadius: 22; tint: "white" }
        }
        Rectangle {
            id: mainCard
            width: root.largePanel ? 800 : 420; height: root.largePanel ? 720 : 280
            anchors.centerIn: parent
            transform: Translate { x: root.panelOffsetX; y: root.panelOffsetY }
            radius: root.largePanel ? 23 : 12
            color: "transparent"
            WindowGlass { id: pane; anchors.fill: parent; cardRadius: mainCard.radius; tint: "white"; frost: root.frost }
            Item {
                x: 8; y: 8; width: 195; height: parent.height - 16
                visible: root.benchmarking
                WindowGlass { anchors.fill: parent; cardRadius: 16; frost: 8 }
            }
            Text { anchors.centerIn: parent; text: "COMPOSITOR GLASS"; color: "white"; font.pixelSize: 20 }
        }
    }
}
'''

if sys.argv[1] == '--plugin':
    plugin = Path(sys.argv[2]).resolve(strict=True)
    temporary = tempfile.TemporaryDirectory(prefix='hg-', dir='/tmp')
    base = Path(temporary.name)
    base.chmod(0o700)
    processes = []

    def cleanup():
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        temporary.cleanup()
    atexit.register(cleanup)
    config = base / ('hyprland.conf' if '--legacy' in sys.argv else 'hyprland.lua')
    if '--legacy' in sys.argv:
        config.write_text("monitor = ,960x640@60,auto,1\nmisc:disable_hyprland_logo = true\nmisc:disable_splash_rendering = true\nmisc:disable_autoreload = true\nanimations:enabled = true\n")
    else:
        config.write_text('hl.monitor({output="",mode="960x640@60",position="auto",scale=1})\nhl.config({misc={disable_hyprland_logo=true,disable_splash_rendering=true,disable_autoreload=true},animations={enabled=true}})\n')
    if '--blur-rules' in sys.argv:
        assert '--legacy' not in sys.argv
        with config.open('a') as rules:
            rules.write('hl.config({decoration={blur={enabled=true,xray=true,size=10,passes=3}}})\n')
            rules.write('hl.layer_rule({match={namespace="quickshell:.*"},blur=true,ignore_alpha=0.79})\n')
    display = Path(os.environ.get('WAYLAND_DISPLAY', 'wayland-1'))
    if not display.is_absolute():
        display = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / display
    nested_env = {**os.environ, 'XDG_RUNTIME_DIR': str(base), 'WAYLAND_DISPLAY': str(display)}
    for key in ('HYPRLAND_INSTANCE_SIGNATURE', 'HYPRLAND_CONFIG', 'NOTIFY_SOCKET', 'WATCHDOG_PID', 'WATCHDOG_USEC'):
        nested_env.pop(key, None)
    nested_env.update(HYPRLAND_NO_SD_VARS='1', HYPRLAND_NO_SD_NOTIFY='1')
    log = open(base / 'hyprland.log', 'w')
    processes.append(subprocess.Popen(['Hyprland', '--config', str(config)], env=nested_env,
                                     stdout=log, stderr=subprocess.STDOUT))
    for attempt in range(100):
        sockets = list((base / 'hypr').glob('*/.socket.sock'))
        displays = list(base.glob('wayland-*'))
        displays = [p for p in displays if not p.name.endswith('.lock')]
        if sockets and displays:
            break
        assert processes[0].poll() is None, (base / 'hyprland.log').read_text()
        time.sleep(0.1)
    assert sockets and displays, 'Nested compositor did not start'
    nested_env.update(HYPRLAND_INSTANCE_SIGNATURE=sockets[0].parent.name, WAYLAND_DISPLAY=str(displays[0]))
    assert nested_env['HYPRLAND_INSTANCE_SIGNATURE'] != os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    for attempt in range(100):
        outputs = subprocess.check_output(['hyprctl', 'monitors', '-j'], env=nested_env, text=True)
        if json.loads(outputs):
            break
        time.sleep(0.1)
    assert json.loads(outputs), (base / 'hyprland.log').read_text()[-10000:]
    result = subprocess.check_output(['hyprctl', 'plugin', 'load', str(plugin)], env=nested_env, text=True)
    assert result.strip() == 'ok', result
    time.sleep(0.5)
    repo = Path(__file__).resolve().parents[1]
    shell = base / 'shell'
    shell.mkdir()
    for name in ('assets', 'defaults', 'modules', 'panelFamilies', 'scripts', 'services', 'translations'):
        (shell / name).symlink_to(repo / name, target_is_directory=True)
    for component in repo.glob('*.qml'):
        if component.name != 'shell.qml':
            (shell / component.name).symlink_to(component)
    for key in ('CONFIG', 'STATE', 'CACHE', 'DATA'):
        path = base / key.lower()
        path.mkdir()
        nested_env['XDG_' + key + '_HOME'] = str(path)
    directory = base / 'config/illogical-impulse'
    directory.mkdir()
    (directory / 'config.json').write_text(json.dumps({'background': {'widgets': {'glass': {'enable': True, 'source': 'windows', 'haze': 4}}}}))
    (shell / 'shell.qml').write_text(FIXTURE)
    nested_env.pop('QS_DISABLE_COMPOSITOR_GLASS', None)
    nested_env['QT_QPA_PLATFORM'] = 'wayland'
    fixture_log = open(base / 'fixture.log', 'w')
    processes.append(subprocess.Popen(['qs', '--no-color', '-p', str(shell / 'shell.qml')],
                                     env=nested_env, stdout=fixture_log, stderr=subprocess.STDOUT))
    metadata = {'base': str(base), 'env': {key: nested_env[key] for key in ('XDG_RUNTIME_DIR', 'WAYLAND_DISPLAY', 'HYPRLAND_INSTANCE_SIGNATURE')}}
else:
    metadata = json.loads(Path(sys.argv[1]).read_text())

env = {**os.environ, **metadata['env']}
base = Path(metadata['base'])
assert base.resolve().is_relative_to(Path('/tmp'))
assert Path(env['XDG_RUNTIME_DIR']).resolve() == base.resolve()
assert env['HYPRLAND_INSTANCE_SIGNATURE'] != os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')


def control(*args):
    if sys.argv[1] == '--plugin' and '--legacy' not in sys.argv and args[0] == 'dispatch':
        command = args[1]
        if command == 'workspace':
            action = 'focus({workspace=' + json.dumps(args[2]) + '})'
        elif command == 'exit':
            action = 'exit()'
        elif command == 'setfloating':
            action = 'window.float({action="set",window=' + json.dumps(args[2]) + '})'
        elif command in ('resizewindowpixel', 'movewindowpixel'):
            geometry, address = args[2].split(',', 1)
            _, x, y = geometry.split()
            method = 'resize' if command == 'resizewindowpixel' else 'move'
            action = f'window.{method}({{x={x},y={y},relative=false,window={json.dumps(address)}}})'
        else:
            assert command == 'movetoworkspacesilent', args
            workspace, address = args[2].split(',', 1)
            action = 'window.move({workspace=' + json.dumps(workspace) + ',follow=false,window=' + json.dumps(address) + '})'
        args = ('eval', 'hl.dispatch(hl.dsp.' + action + ')')
    result = subprocess.check_output(['hyprctl', *args], env=env, text=True, timeout=10)
    return result.strip()


plugins = json.loads(control('plugin', 'list', '-j'))
assert any(p['name'] == 'hyprglass' for p in plugins), plugins
for attempt in range(100):
    clients = json.loads(control('clients', '-j'))
    if {'glass-red', 'glass-blue'} <= {c['title'] for c in clients}:
        break
    time.sleep(0.1)
assert {'glass-red', 'glass-blue'} <= {c['title'] for c in clients}, clients
last_size, stable = None, 0
for attempt in range(100):
    monitors = json.loads(control('monitors', '-j'))
    if monitors:
        size = (monitors[0]['width'], monitors[0]['height'], monitors[0]['scale'])
        stable = stable + 1 if size == last_size else 0
        last_size = size
        if stable >= 8:
            break
    time.sleep(0.1)
assert monitors and stable >= 8, 'Nested output did not settle after parent tiling'
monitor = monitors[0]
width, height = monitor['width'], monitor['height']
left, right = width / 2 - 210, width / 2 + 210
for client in clients:
    if client['title'] not in ('glass-red', 'glass-blue'):
        continue
    address = 'address:' + client['address']
    control('dispatch', 'setfloating', address)
    control('dispatch', 'resizewindowpixel', f'exact {width} {height},{address}')
    control('dispatch', 'movewindowpixel', 'exact 0 0,' + address)
    workspace = '1' if client['title'] == 'glass-red' else '2'
    control('dispatch', 'movetoworkspacesilent', workspace + ',' + address)
if sys.argv[1] == '--plugin':
    for attempt in range(150):
        if 'NATIVE PRODUCTION true true 0' in (base / 'fixture.log').read_text():
            break
        time.sleep(0.1)
    assert 'NATIVE PRODUCTION true true 0' in (base / 'fixture.log').read_text(), (base / 'fixture.log').read_text()
    for option, expected in (('brightness', 1), ('contrast', 1), ('adaptive_dim', 0), ('adaptive_boost', 0)):
        actual = json.loads(control('getoption', 'plugin:hyprglass:' + option, '-j'))
        assert actual.get('float') == expected, (option, actual)

    def ipc(function, *args):
        result = subprocess.run(['qs', '-p', str(shell / 'shell.qml'), 'ipc', 'call', 'glass-check', function, *args],
                                env=nested_env, text=True, capture_output=True, timeout=5)
        assert result.returncode == 0, (result.stdout, result.stderr)
        return result.stdout.strip()

    time.sleep(0.5)
    before = json.loads(ipc('state'))
    for attempt in range(8):
        ipc('churnClients')
        time.sleep(0.1)
    time.sleep(0.3)
    assert json.loads(ipc('state'))['writes'] == before['writes'], 'Unchanged clients rewrote compositor settings'
    ipc('useNative', 'false')
    time.sleep(0.7)
    fallback = json.loads(ipc('state'))
    assert not fallback['native'] and fallback['windows'] and fallback['captures'] > 0, fallback
    assert json.loads(control('getoption', 'plugin:hyprglass:layers:enabled', '-j'))['int'] == 0
    ipc('useNative', 'true')
    time.sleep(0.7)
    resumed = json.loads(ipc('state'))
    assert resumed['native'] and resumed['captures'] == 0, resumed
    assert json.loads(control('getoption', 'plugin:hyprglass:layers:enabled', '-j'))['int'] == 1
if sys.argv[1] == '--plugin':
    ipc('useEnhanced', 'true')
    for attempt in range(50):
        state = json.loads(ipc('state'))
        stats = json.loads(control('end4glass'))
        if state['enhanced'] and stats['surfaces'] == 2 and stats['regions'] == 4:
            break
        time.sleep(0.1)
    assert state['enhanced'] and stats['surfaces'] == 2 and stats['regions'] == 4, (state, stats)
    time.sleep(0.5)
    before = json.loads(control('end4glass'))['updates']
    assert control('end4glass', '1 1 0').startswith('error:'), 'Geometry sender can spoof another PID'
    time.sleep(0.8)
    assert json.loads(control('end4glass'))['updates'] == before, 'Stationary cards keep publishing geometry'
    ipc('moveCard')
    time.sleep(0.4)
    assert json.loads(control('end4glass'))['updates'] > before, 'Moved card did not publish geometry'
    before = json.loads(control('end4glass'))['updates']
    ipc('scaleCard')
    time.sleep(0.4)
    assert json.loads(control('end4glass'))['updates'] > before, 'Scale transform did not publish geometry'
    assert json.loads(ipc('state'))['captures'] == 0
    assert control('dispatch', 'workspace', '2') == 'ok'
    time.sleep(1)
    edge_colors = []
    for enhanced in ('true', 'false', 'true'):
        ipc('useEnhanced', enhanced)
        time.sleep(0.5)
        path = base / 'enhanced-edge.png'
        subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
        with Image.open(path).convert('RGB') as frame:
            edge_colors.append(min(frame.getpixel((int(width / 2 + dx), int(height / 2 + 138)))[0] for dx in (-110, 110)))
            if enhanced == 'true':
                frame.save('/tmp/end4-enhanced-native.png')
                assert frame.getpixel((100, 95))[2] > 150, 'Blur clip lost the separate upper card'
                # The nested compositor's startup warning covers the upper right on large outputs.
                for x in range(270, width // 2, 180):
                    assert max(abs(a - b) for a, b in zip(frame.getpixel((x, 34)), frame.getpixel((x, 100)))) <= 3, ('Enhanced bar center is tinted or blurred', x, frame.getpixel((x, 34)), frame.getpixel((x, 100)))
    assert min(edge_colors[0], edge_colors[2]) > edge_colors[1] + 20, ('Card edge does not refract independently of the fullscreen layer', edge_colors)
    # The diagonal point lies on blue; actual inward refraction must bring in the green interior.
    ipc('probeCorners', 'true')
    time.sleep(0.7)
    path = Path('/tmp/end4-corner-native.png')
    subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
    with Image.open(path).convert('RGB') as frame:
        for sx in (-1, 1):
            for sy in (-1, 1):
                x = round(width / 2 - 210) + (14 if sx < 0 else 405)
                y = round(height / 2 - 140) + (14 if sy < 0 else 265)
                color = frame.getpixel((x, y))
                assert color[1] > color[2] + 80, ('Corner must refract the green interior', sx, sy, color)
    ipc('showCornerDigits')
    time.sleep(0.3)
    subprocess.run(['grim', '/tmp/end4-corner-digits-native.png'], env=env, check=True, timeout=10)
    ipc('probeLargePanel', 'true')
    time.sleep(0.6)
    path = Path('/tmp/end4-glass-large-panel.png')
    subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
    with Image.open(path).convert('RGB') as frame:
        color = frame.getpixel((round(width / 2 + 400) - 28, height // 2))
        assert max(abs(a - b) for a, b in zip(color, (25, 118, 210))) <= 3, ('Large panel refracts beyond the 20px rim', color)
    ipc('setBlur', '4')
    time.sleep(0.5)
    subprocess.run(['grim', '/tmp/end4-settings-blur-native.png'], env=env, check=True, timeout=10)
    ipc('probeLargePanel', 'false')
    ipc('shiftPanel', 'true')
    time.sleep(0.5)
    subprocess.run(['grim', '/tmp/end4-settings-blur-shifted.png'], env=env, check=True, timeout=10)
    with Image.open('/tmp/end4-settings-blur-shifted.png').convert('RGB') as frame:
        assert frame.getpixel((width - 25, height - 25)) == (255, 0, 204), 'Sample crop clipped opaque foreground'
        # The small card moved above the fixed blue/green reference, onto its dark surround.
        color = frame.getpixel((width // 2 - 80, height // 2 - 230))
        assert max(color) <= 20, ('Cropped sample did not follow the moved card', color)
    ipc('shiftPanel', 'false')
    if json.loads(ipc('state'))['frosted']:
        ipc('probeBlack')
        rim = []
        for frost in ('0', '8'):
            ipc('setFrost', frost)
            time.sleep(0.4)
            path = base / ('black-' + frost + '.png')
            subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
            with Image.open(path).convert('RGB') as frame:
                rim.append(max(frame.getpixel((round(width / 2 - 210) + x, height // 2))[0] for x in range(1, 16)))
        assert rim[0] > 5 and rim[1] <= 2, ('White rim must disappear only from frosted glass', rim)
        ipc('probeFrost')
        ipc('setBlur', '1')
        contrast = []
        for frost in ('0', '8', '0'):
            ipc('setFrost', frost)
            time.sleep(0.4)
            path = base / ('frost-' + frost + '.png')
            subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
            with Image.open(path).convert('RGB') as frame:
                if frost == '8': frame.save('/tmp/end4-frosted-native.png')
                pixels = [frame.getpixel((width // 2 + x, height // 2 + 80))[0] for x in range(-100, 100)]
                assert 60 < sum(pixels) / len(pixels) < 200, ('Frosted background became black or white', pixels)
                contrast.append(max(pixels) - min(pixels))
        assert contrast[1] < min(contrast[0], contrast[2]) * 0.4, ('Frosted material leaves background detail readable', contrast)
        assert contrast[1] <= 3, ('Gaussian blur leaves a sampling grid on fine stripes', contrast)
        ipc('setFrost', '8')
        samples = []
        for offset in (0, 1, 3, 4, 8, 12):
            ipc('moveFrost', str(offset))
            time.sleep(0.3)
            path = base / 'frost-motion.png'
            subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
            with Image.open(path).convert('RGB') as frame:
                samples.append([frame.getpixel((width // 2 + x, height // 2 + 80))[0] for x in range(-100, 100)])
        drift = max(abs(a - b) for row in samples[1:] for a, b in zip(row, samples[0]))
        assert drift <= 2, ('Moving frost changes fixed background pixels', drift)
        print('Frosted material: black rim', rim, 'contrast', contrast, 'motion drift', drift, flush=True)
        ipc('moveFrost', '0')
        ipc('shiftPanel', 'false')
    ipc('probeCorners', 'false')
    time.sleep(0.4)
positions = []
assert control('dispatch', 'workspace', '2') == 'ok'
time.sleep(1)
for index in range(36):
    path = base / 'motion-check.png'
    subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
    with Image.open(path).convert('RGB') as frame:
        # The white bar moves over a blue patterned window. Compare its real position
        # outside the pane with its refracted/blurred position inside, away from text.
        outside = [x for x in range(width) if min(frame.getpixel((x, 120))) > 235]
        inside = [x for x in range(int(left + 30), int(right - 30))
                  if frame.getpixel((x, height // 2 + 70))[0] > 110]
        if outside:
            center = sum(outside) / len(outside)
            if left + 80 < center < right - 80:
                assert inside, f'Backdrop froze while the bar passed at x={center}'
                actual = sum(inside) / len(inside)
                assert abs(actual - center) < 80, (actual, center)
                positions.append(actual)
    time.sleep(0.1)
assert len(positions) >= 2 and max(positions) - min(positions) > 70, positions
# Both workspaces must actually appear through the pane, not only the selected client list.
colors = []
for workspace in ('1', '2'):
    assert control('dispatch', 'workspace', workspace) == 'ok'
    time.sleep(1)
    path = base / ('workspace-' + workspace + '.png')
    subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
    with Image.open(path).convert('RGB') as frame:
        samples = [frame.getpixel((x, height // 2 + 70)) for x in range(int(left + 40), int(right - 40))]
        colors.append(sum(b - r for r, g, b in samples) / len(samples))
assert colors[0] < -10 and colors[1] > 10, colors
if sys.argv[1] == '--plugin':
    # Unload while clients are alive, then reload and stop the compositor with the plugin loaded.
    assert control('plugin', 'unload', str(plugin)) == 'ok'
    assert not json.loads(control('plugin', 'list', '-j'))
    assert control('plugin', 'load', str(plugin)) == 'ok'
    for attempt in range(50):
        if json.loads(control('end4glass'))['regions'] == 4: break
        time.sleep(0.1)
    assert json.loads(control('end4glass'))['regions'] == 4, 'Geometry not restored after plugin reload'
    assert control('dispatch', 'exit') == 'ok'
    result = processes[0].wait(timeout=10)
    assert result == 0, (result, (base / 'hyprland.log').read_text()[-10000:])
print('True Glassy toggle, unchanged-setting suppression, live pixels, workspaces and compositor lifecycle passed')
