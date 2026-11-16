"""Run: python3 tests/native-glass-shader-check.py PATCHED_SOURCE_DIR.
Compare actual native GLSL pixels with the previous path using CPU-only Mesa.
No compositor connection, desktop changes or hardware GPU rendering.
"""
import ctypes as C
import os
from pathlib import Path
import re
import sys
import subprocess
import tempfile
import time

os.environ.update(LIBGL_ALWAYS_SOFTWARE='1', MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',
                  EGL_PLATFORM='surfaceless', MESA_SHADER_CACHE_DISABLE='true', LP_NUM_THREADS='2')
egl, gl = C.CDLL('libEGL.so.1'), C.CDLL('libGLESv2.so.2')
I, U, F, P = C.c_int, C.c_uint, C.c_float, C.c_void_p


def api(library, name, result, *args):
    function = getattr(library, name)
    function.restype, function.argtypes = result, list(args)
    return function


display = api(egl, 'eglGetDisplay', P, P)(None)
major, minor = I(), I()
assert api(egl, 'eglInitialize', U, P, P, P)(display, C.byref(major), C.byref(minor))
assert api(egl, 'eglBindAPI', U, U)(0x30A0)
config, count = P(), I()
assert api(egl, 'eglChooseConfig', U, P, P, P, I, P)(
    display, (I * 5)(0x3040, 0x40, 0x3033, 1, 0x3038), C.byref(config), 1, C.byref(count)) and count.value
context = api(egl, 'eglCreateContext', P, P, P, P, P)(display, config, None, (I * 3)(0x3098, 3, 0x3038))
assert context
make_current = api(egl, 'eglMakeCurrent', U, P, P, P, P)
assert make_current(display, None, None, context)
renderer = api(gl, 'glGetString', C.c_char_p, U)(0x1F01).decode()
assert 'llvmpipe' in renderer.lower(), 'Refusing to test on a hardware GPU: ' + renderer

create_shader = api(gl, 'glCreateShader', U, U)
shader_source = api(gl, 'glShaderSource', None, U, I, C.POINTER(C.c_char_p), P)
compile_shader = api(gl, 'glCompileShader', None, U)
shader_status = api(gl, 'glGetShaderiv', None, U, U, P)
shader_log = api(gl, 'glGetShaderInfoLog', None, U, I, P, P)
create_program = api(gl, 'glCreateProgram', U)
attach_shader = api(gl, 'glAttachShader', None, U, U)
link_program = api(gl, 'glLinkProgram', None, U)
program_status = api(gl, 'glGetProgramiv', None, U, U, P)
use_program = api(gl, 'glUseProgram', None, U)
location = api(gl, 'glGetUniformLocation', I, U, C.c_char_p)
uniform_i = api(gl, 'glUniform1i', None, I, I)
uniform_f = api(gl, 'glUniform1f', None, I, F)
uniform_2 = api(gl, 'glUniform2f', None, I, F, F)
uniform_2v = api(gl, 'glUniform2fv', None, I, I, P)
uniform_4 = api(gl, 'glUniform4fv', None, I, I, P)
gen_textures = api(gl, 'glGenTextures', None, I, P)
active_texture = api(gl, 'glActiveTexture', None, U)
bind_texture = api(gl, 'glBindTexture', None, U, U)
texture_image = api(gl, 'glTexImage2D', None, U, I, I, I, I, I, U, U, P)
texture_parameter = api(gl, 'glTexParameteri', None, U, U, I)
framebuffer = U()
api(gl, 'glGenFramebuffers', None, I, P)(1, C.byref(framebuffer))
api(gl, 'glBindFramebuffer', None, U, U)(0x8D40, framebuffer)
attach_texture = api(gl, 'glFramebufferTexture2D', None, U, U, U, U, I)
draw = api(gl, 'glDrawArrays', None, U, I, I)
read = api(gl, 'glReadPixels', None, I, I, I, I, U, U, P)
width, height = 128, 96
api(gl, 'glViewport', None, I, I, I, I)(0, 0, width, height)


def shader(kind, text):
    handle = create_shader(kind)
    source = C.c_char_p(text.encode())
    shader_source(handle, 1, C.byref(source), None)
    compile_shader(handle)
    status = I()
    shader_status(handle, 0x8B81, C.byref(status))
    log = C.create_string_buffer(8192)
    shader_log(handle, len(log), None, log)
    assert status.value, log.value.decode()
    return handle


header = (Path(sys.argv[1]) / 'src/Shaders.hpp').read_text()
fragment = re.search(r'\{"liquidglass.frag", R"GLSL\(([\s\S]*?)\)GLSL"', header)[1]
# Reconstruct r24 by undoing only the new flat-interior/neutral-colour shortcuts.
flat_start = fragment.index('    // Enhanced mode uses neutral colour/lens uniforms')
flat_end = fragment.index('    vec2 inwardDir = selected >= 0', flat_start)
flat = fragment[flat_start:flat_end]
r24 = fragment.replace(flat, '')
normal = '    vec2 inwardDir = selected >= 0 ? vec2(0.0) : enhanced == 1 ? edgeNormal(uv) : refractionDir(uv);'
r24 = r24.replace(normal + '\n', '').replace('    float visibility =', normal + '\n    float visibility =')
r24 = r24.replace('(max(q.x, q.y) > 0.0 ? lpNorm(max(q, 0.0), roundingPower) : 0.0)', 'lpNorm(max(q, 0.0), roundingPower)')
tone = re.search(r'    if \(enhanced != 1\) \{\n([\s\S]*?color = mix\(color, tintColor, tintAlpha\);)\n    \}', r24)
assert tone, 'Neutral-colour shortcut not found'
r24 = r24.replace(tone[0], '\n'.join(line[4:] if line.startswith('    ') else line for line in tone[1].split('\n')))
# These are the production invariants required by the enhanced shortcuts.
renderer_source = (Path(sys.argv[1]) / 'src/GlassRenderer.cpp').read_text()
for uniform, value in [('SHADER_BRIGHTNESS', '1.0f'), ('SHADER_CONTRAST', '1.0f'), ('SHADER_VIBRANCY', '0.0f')]:
    assert f'shader->setUniformFloat({uniform}, {value});' in renderer_source
for uniform, value in [('saturation', '1.0f'), ('vibrancyDarkness', '0.0f'), ('adaptiveDim', '0.0f'), ('adaptiveBoost', '0.0f')]:
    assert f'glUniform1f(uniforms.{uniform}, {value});' in renderer_source
assert 'enhanced ? 0.0f : resolvePresetFloat' in renderer_source
assert 'enhanced ? 0.0f : static_cast<float>(tintColorValue & 0xFF)' in renderer_source
# Remove only the optimized routes to exercise the old full scan and general SDF.
early_exit = '                if (!hasMask && glass.a >= 0.999) break;\n'
plain = '    if (all(equal(regionFeatures[i], vec4(0.0)))) return roundedDist(pixel - regionRects[i].xy - size * 0.5, size * 0.5, radii);\n'
assert fragment.count(early_exit) == fragment.count(plain) == 1
previous = r24.replace(early_exit, '').replace(plain, '')
previous = previous.replace('selected >= 0 ? vec2(0.0) : enhanced == 1 ? edgeNormal(uv)', 'enhanced == 1 ? edgeNormal(uv)')
previous = previous.replace('(depth < bezelWidthPx ? edgeRefraction(inwardDir, depth, bezelWidthPx) / fullSize : vec2(0.0))',
                            'edgeRefraction(inwardDir, depth, bezelWidthPx) / fullSize')
previous = previous.replace('''            if (hasMask) {
                float coverage = 1.0 - smoothstep(-0.5, 0.5, d);
                transmission *= 1.0 - (16.0 / 255.0) * regionDetails[i].y * coverage;
            }''', '''            float coverage = 1.0 - smoothstep(-0.5, 0.5, d);
            transmission *= 1.0 - (16.0 / 255.0) * regionDetails[i].y * coverage;''')
assert previous != fragment
vertex_base = '''#version 300 es
out vec2 v_texcoord;
void main() {
    vec2 p = vec2((gl_VertexID & 1) == 0 ? -1.0 : 1.0, (gl_VertexID & 2) == 0 ? -1.0 : 1.0);
    v_texcoord = (p + 1.0) * 0.5; gl_Position = vec4(p, 0.0, 1.0);
}'''
vertex_extension = re.search(r'\{"darkening.vert", R"GLSL\(([\s\S]*?)\)GLSL"', header)[1]
vertex_text = vertex_base.replace('\n', '\n#define main hyprglassMain\n', 1) + '\n#undef main\n' + vertex_extension
vertex = shader(0x8B31, vertex_text)
base_vertex = shader(0x8B31, vertex_base)
def program_for(text, vertex_shader=vertex):
    program = create_program()
    attach_shader(program, vertex_shader)
    attach_shader(program, shader(0x8B30, text))
    link_program(program)
    status = I()
    program_status(program, 0x8B82, C.byref(status))
    log = C.create_string_buffer(8192)
    api(gl, 'glGetProgramInfoLog', None, U, I, P, P)(program, len(log), None, log)
    assert status.value, 'Shader link failed: ' + log.value.decode()
    return program


programs = [program_for(text) for text in (previous, fragment)]
probe_function = vertex_extension[vertex_extension.index('float sampleMaterialLuma('):vertex_extension.index('\nvoid main()')]
reference = fragment.replace('flat in highp vec4 materialLuma[9];', 'uniform vec4 darkeningReference;')
reference = reference.replace('vec3 darkenGlass(', probe_function + '\nvec3 darkenGlass(', 1)
reference = reference.replace('materialLuma[slot / 4][slot % 4]', 'sampleMaterialLuma(selected)')
reference_program = program_for(reference, base_vertex)


textures = (U * 4)()
gen_textures(4, textures)
for unit, texture in enumerate(textures):
    active_texture(0x84C0 + unit)
    bind_texture(0x0DE1, texture)
    data = bytes(channel for y in range(height) for x in range(width)
                 for channel in ((x * 13 + y * 7) % 256, (x * 5 + y * 19) % 256, 220 if (x // 5 + y // 7) % 2 else 30, 255))
    if unit == 1:  # A translucent premultiplied foreground makes carrier errors observable.
        data = bytes((15, 25, 35, 115)) * (width * height)
    texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401, C.create_string_buffer(data))
    for param, value in ((0x2801, 0x2601), (0x2800, 0x2601), (0x2802, 0x812F), (0x2803, 0x812F)):
        texture_parameter(0x0DE1, param, value)
attach_texture(0x8D40, 0x8CE0, 0x0DE1, textures[3], 0)
assert api(gl, 'glCheckFramebufferStatus', U, U)(0x8D40) == 0x8CD5
pixels = (C.c_ubyte * (width * height * 4))()


def render(program, boxes, radii, features, details, masked, opacity, rim, enhanced=1, power=2, darkness=0, automatic=0, reference=(0,0,0,0)):
    use_program(program)
    uniform_2(location(program, b'darkening'), darkness, automatic)
    uniform_4(location(program, b'darkeningReference'), 1, (F * 4)(*reference))
    for name, value in dict(tex=0, maskTex=1, frostTex=2, enhanced=enhanced, useMask=int(masked), regionCount=len(boxes)).items():
        uniform_i(location(program, name.encode()), value)
    for name, value in dict(radius=12, roundingPower=power, refractionStrength=2, chromaticAberration=.1,
                            fresnelStrength=.35, specularStrength=.5, glassOpacity=opacity,
                            edgeThickness=rim, maxRimWidth=20, brightness=1, contrast=1, saturation=1,
                            maskAlphaThreshold=.001, lensDistortion=0 if enhanced else .4,
                            tintAlpha=0 if enhanced else .2, vibrancy=0 if enhanced else .3,
                            adaptiveDim=0 if enhanced else .2).items():
        uniform_f(location(program, name.encode()), value)
    for name, value in dict(fullSize=(width, height), uvPadding=(.02, .025), sampleUVScale=(1, 1), maskUVScale=(1, 1)).items():
        uniform_2(location(program, name.encode()), *value)
    for name, values in [('regionRects', boxes), ('regionRadii', radii), ('regionFeatures', features), ('regionDetails', details)]:
        if values:
            uniform_4(location(program, name.encode()), len(values), (F * (len(values) * 4))(*(v for row in values for v in row)))
    api(gl, 'glClear', None, U)(0x4000)
    draw(0x0005, 0, 4)
    read(0, 0, width, height, 0x1908, 0x1401, pixels)
    assert api(gl, 'glGetError', U)() == 0
    return bytes(pixels)


# A faint Qt shadow outside a pill is foreground, not a glass region.
# On white, darkening must not turn a 1/255-alpha shadow pixel into an opaque black dot.
for unit in (0, 2):
    active_texture(0x84C0 + unit)
    bind_texture(0x0DE1, textures[unit])
    texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401,
                  C.create_string_buffer(bytes((255, 255, 255, 255)) * width * height))
active_texture(0x84C1)
bind_texture(0x0DE1, textures[1])
texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401,
              C.create_string_buffer(bytes((0, 0, 0, 1)) * width * height))
for darkness, automatic in ((0, 0), (.55, 0), (1, 0), (0, 1)):
    image = render(programs[1], [(20, 14, 88, 64)], [(32, 32, 32, 32)], [(0, 0, 0, 0)], [(0, 1, 0, 0)], True, 1, .24,
                   darkness=darkness, automatic=automatic)
    for x, y in ((18, 46), (22, 17), (105, 17), (22, 74), (105, 74)):
        at = (y * width + x) * 4
        assert image[at:at+4] == bytes((0, 0, 0, 1)), ('Glass leaked beyond pill', darkness, automatic, x, y, tuple(image[at:at+4]))
# Restore the translucent foreground for the remaining comparisons.
active_texture(0x84C1)
bind_texture(0x0DE1, textures[1])
texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401,
              C.create_string_buffer(bytes((15, 25, 35, 115)) * width * height))
print('PASS: pill corners preserve faint Qt shadow pixels outside glass with manual/automatic darkening.')

# A black wash must preserve light bands and RGB ratios inside the same material.
for palette in (((230,230,230), (180,180,180)), ((230,220,210), (170,190,205))):
    for unit in (0, 2):
        active_texture(0x84C0 + unit)
        bind_texture(0x0DE1, textures[unit])
        bands = bytes(c for y in range(height) for x in range(width)
                      for c in (*palette[0 if y < height//2 else 1], 255))
        texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401, C.create_string_buffer(bands))
    args = (programs[1], [(8, 8, 110, 80)], [(12, 12, 12, 12)], [(0, 0, 0, 0)], [(0, 1, 0, 0)], False, 1, .24)
    for darkness, automatic in ((.5, 0), (0, 1)):
        shaded = render(*args, darkness=darkness, automatic=automatic)
        old_args = (reference_program, *args[1:])
        before_move = render(*old_args, darkness=darkness, automatic=automatic)
        assert max(abs(a-b) for a,b in zip(shaded,before_move)) <= 1, 'Moving probes to vertices changed pixels' 
        high, low = (35 * width + 64) * 4, (60 * width + 64) * 4
        assert shaded[high] - shaded[low] >= 20, ('Light bands flattened', darkness, automatic, shaded[high], shaded[low])
        gains = [shaded[pixel+c] / original[c] for pixel, original in ((high,palette[0]),(low,palette[1])) for c in range(3)]
        assert max(gains)-min(gains) <= 2/170, 'Black opacity must be uniform and preserve RGB ratios within a box'
print('PASS: automatic/manual black wash preserves light/coloured bands and relative contrast within a box.')



# A moving pill must not move the automatic-darkening probes across a bright edge.
for unit in (0, 2):
    active_texture(0x84C0 + unit)
    bind_texture(0x0DE1, textures[unit])
    bands = bytes(c for y in range(height) for x in range(width)
                  for c in ((220,220,220,255) if x >= 80 else (100,100,100,255)))
    texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401, C.create_string_buffer(bands))
center = (48 * width + 64) * 4
local, stable = [], []
for boxes in ([(40,24,48,48)], [(8,24,112,48)], [(8,24,112,48),(52,34,24,28)]):
    args = (programs[1], boxes, [(8,8,8,8)] * len(boxes), [(0,0,0,0)] * len(boxes), [(0,1,0,0)] * len(boxes), False, 1, .24)
    local.append(render(*args, automatic=1)[center])
    stable.append(render(*args, automatic=1, reference=(0,.25,1,.5))[center])
assert abs(local[0] - local[1]) > 10, ('Fixture must reproduce moving-probe flash', local)
assert max(stable) - min(stable) <= 1, ('Bar expansion/nested widgets changed darkening', stable)
print('PASS: fixed bar reference preserves darkness across expansion and nested-widget reveal on a contrasting background.')


# Exercise actual production pixels; the darkening changes only the backdrop, once per selected material.
for value in (0, 64, 128, 255):
    for unit in (0, 2):
        active_texture(0x84C0 + unit)
        bind_texture(0x0DE1, textures[unit])
        texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401,
                      C.create_string_buffer(bytes((value, value, value, 255)) * width * height))
    for enhanced in (0, 1):
        for frost in (0, 8):
            args = (programs[1], [(8, 8, 110, 80)], [(12, 12, 12, 12)], [(0, 0, 0, 0)], [(0, 1, frost, 0)], False, 1, .24)
            before = render(*args, enhanced=enhanced)
            for darkness in (0, .25, .5, 1):
                after = render(*args, enhanced=enhanced, darkness=darkness)
                center = (height // 2 * width + width // 2) * 4
                for c in range(3):
                    assert abs(after[center+c] - before[center+c] * (1-darkness)) <= 1, (value, enhanced, frost, darkness)
                assert after[center+3] == before[center+3]
            auto = render(*args, enhanced=enhanced, automatic=1)
            # In enhanced mode colour processing is neutral; auto caps bright grey at 38% sRGB.
            if enhanced:
                assert abs(auto[center] - min(value, .38 * 255)) <= 1, (value, frost, auto[center])
                if value < 96: assert auto == before, 'Automatic must leave dark backgrounds unchanged'
# Return the textured inputs used by the regression comparisons below.
for unit in (0, 2):
    active_texture(0x84C0 + unit)
    bind_texture(0x0DE1, textures[unit])
    texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401, C.create_string_buffer(bytes(channel for y in range(height) for x in range(width)
        for channel in ((x*13+y*7)%256, (x*5+y*19)%256, 220 if (x//5+y//7)%2 else 30, 255))))
# An opaque surface represents foreground UI; neither manual nor automatic may darken it.
active_texture(0x84C1)
bind_texture(0x0DE1, textures[1])
texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401, C.create_string_buffer(bytes((80, 130, 180, 255))*width*height))
args=(programs[1], [(8,8,110,80)], [(12,12,12,12)], [(0,0,0,0)], [(0,1,8,0)], True, 1, .24)
before=render(*args)
assert render(*args, darkness=1) == before and render(*args, automatic=1) == before
texture_image(0x0DE1, 0, 0x8058, width, height, 0, 0x1908, 0x1401, C.create_string_buffer(bytes((15,25,35,115))*width*height))
print('PASS: manual 0/25/50/100%, per-material automatic black/grey/white, clear/frosted and standard/enhanced backgrounds; foreground pixels unchanged.')

checks = 0
for nested in (False, True):
    for count in (0, 1, 8, 32):
        boxes = [(8 + i * .4, 8 + i * .2, 110 - i * .8, 80 - i * .4) if nested else
                 (2 + i % 8 * 16, 4 + i // 8 * 22, 13, 18) for i in range(count)]
        radii = [(2, 5, 3, 4)] * count
        for flared in (False, True):
            features = [(3, 2, 1, 0) if flared else (0, 0, 0, 0)] * count
            for masked in (False, True):
                for fade in (1, .6, .02):
                    details = [(i % 4, fade if nested else 1, 8 if i % 2 else 0, 0) for i in range(count)]
                    for rim in (.07, .24):
                        before, after = [render(p, boxes, radii, features, details, masked, fade, rim) for p in programs]
                        error = max(abs(a - b) for a, b in zip(before, after))
                        assert error <= 1, (nested, count, flared, masked, fade, rim, error)
                        automatic = render(programs[1], boxes, radii, features, details, masked, fade, rim, automatic=1)
                        before_move = render(reference_program, boxes, radii, features, details, masked, fade, rim, automatic=1)
                        assert max(abs(a-b) for a,b in zip(automatic,before_move)) <= 1, ('Vertex probes changed material', nested, count, flared, masked, fade, rim)
                        checks += 1
# r24 against r25, including the actual compositor rounding power and thin lips.
r24_program = program_for(r24)
for power in (1, 2, 2.5, 4):
    for enhanced in (0, 1):
        for masked in (False, True):
            for rim in (.00001, .07, .24):
                for fade in (.02, .6, 1):
                    boxes = [(4, 4, 120, 88), (8, 8, 56, 36), (68, 45, 56, 42)]
                    radii = [(12, 12, 12, 12), (0, 3, 18, 9), (15, 2, 4, 10)]
                    features = [(0, 0, 0, 0), (3, 2, 1, 0), (0, 0, 0, 0)]
                    details = [(0, fade, 0, 0), (1, fade, 8, 0), (0, fade, 8, 0)]
                    before, after = [render(p, boxes, radii, features, details, masked, fade, rim, enhanced, power)
                                     for p in (r24_program, programs[1])]
                    error = max(abs(a - b) for a, b in zip(before, after))
                    assert error <= 1, ('r24/r25', power, enhanced, masked, rim, fade, error)
                    checks += 1
print(f'PASS: {checks} old/new native GLSL image comparisons on {renderer}; rounded/flared corners, 0–32 cards, nested layers, carrier, fades, rounding powers 1–4, legacy/enhanced and thin lips within 1/255.')
# Informational CPU-only timing: same framebuffer, state and pixels, no readback inside the draw loop.
finish = api(gl, 'glFinish', None)
for automatic in (0, 1):
    timings = []
    for program in (reference_program, programs[1]):
        render(program, [(4,4,120,88)], [(12,12,12,12)], [(0,0,0,0)], [(0,1,8,0)], False, 1, .24, automatic=automatic)
        finish()
        start = time.perf_counter()
        for _ in range(40): draw(0x0005, 0, 4)
        finish()
        timings.append((time.perf_counter()-start)*1000/40)
    print(f'CPU llvmpipe, auto={automatic}: fragment probes {timings[0]:.3f} ms/draw; vertex probes {timings[1]:.3f} ms/draw (informational).')
# Compile the production coefficient block, rather than a Python reimplementation.
renderer_source = (Path(sys.argv[1]) / 'src/GlassRenderer.cpp').read_text()
start = renderer_source.index('    std::array<float, 64> taps{};')
end = renderer_source.index('    glUniform2fv(blurUniforms.taps', start)
coefficient_code = renderer_source[start:end]
with tempfile.TemporaryDirectory() as temporary:
    source, library = Path(temporary) / 'kernel.cpp', Path(temporary) / 'kernel.so'
    source.write_text('#include <algorithm>\n#include <array>\n#include <cmath>\n'
                      'extern "C" int coefficients(float radius, int kernelLimit, float* out, float* total) {\n'
                      + coefficient_code + '\nstd::copy(taps.begin(), taps.end(), out);'
                      '*total = totalWeight; return tapCount; }\n')
    subprocess.run(['c++', '-std=c++23', '-shared', '-fPIC', '-O2', str(source), '-o', str(library)], check=True)
    coefficients = C.CDLL(str(library)).coefficients
    coefficients.argtypes, coefficients.restype = [F, I, P, P], I

    blur_fragment = re.search(r'\{"gaussianblur.frag", R"GLSL\(([\s\S]*?)\)GLSL"', header)[1]
    # Previous Gaussian kernel: same bilinear samples and normalization, per pixel.
    blur_previous = """#version 300 es
precision highp float;
uniform sampler2D tex;
uniform vec2 direction;
uniform float blurRadius;
uniform int kernelLimit;
in vec2 v_texcoord;
layout(location = 0) out vec4 fragColor;
void main() {
    float sigma = max(blurRadius / 3.0, 0.001);
    float invSigma2 = -0.5 / (sigma * sigma);
    int samples = min(int(ceil(blurRadius)), kernelLimit);
    float w0 = 1.0;
    vec4 result = texture(tex, v_texcoord) * w0;
    float totalWeight = w0;
    for (int i = 1; i <= samples; i += 2) {
        float x1 = float(i);
        float x2 = float(i + 1);
        float w1 = exp(x1 * x1 * invSigma2);
        float w2 = (i + 1 <= samples) ? exp(x2 * x2 * invSigma2) : 0.0;
        float wSum = w1 + w2;
        if (wSum < 0.0001) continue;
        float offset = (x1 * w1 + x2 * w2) / wSum;
        result += texture(tex, v_texcoord + direction * offset) * wSum;
        result += texture(tex, v_texcoord - direction * offset) * wSum;
        totalWeight += 2.0 * wSum;
    }
    fragColor = result / totalWeight;
}"""
    blur_programs = [program_for(text) for text in (blur_previous, blur_fragment)]

    def blur(program, radius, limit, directions):
        use_program(program)
        uniform_i(location(program, b'tex'), 0)
        uniform_f(location(program, b'blurRadius'), radius)
        uniform_i(location(program, b'kernelLimit'), limit)
        taps, total = (F * 64)(), F()
        count = coefficients(radius, limit, taps, C.byref(total))
        assert 0 <= count <= 32 and total.value >= 1
        uniform_2v(location(program, b'taps[0]'), count, taps)
        uniform_i(location(program, b'tapCount'), count)
        uniform_f(location(program, b'totalWeight'), total)
        active_texture(0x84C0)
        source_texture = textures[0]
        for index, direction in enumerate(directions):
            target = textures[3 if index % 2 == 0 else 1]
            attach_texture(0x8D40, 0x8CE0, 0x0DE1, target, 0)
            bind_texture(0x0DE1, source_texture)
            uniform_2(location(program, b'direction'), *direction)
            draw(0x0005, 0, 4)
            source_texture = target
        read(0, 0, width, height, 0x1908, 0x1401, pixels)
        assert api(gl, 'glGetError', U)() == 0
        return bytes(pixels)

    blur_checks = 0
    for radius in (.001, .1, .5, 1, 1.01, 2, 3, 4.5, 6, 7.5, 8, 12, 20, 32, 63, 64, 96):
        for limit in (8, 64):
            for directions in ([(1 / width, 0)], [(0, 1 / height)], [(1 / width, 0), (0, 1 / height)] * 2):
                before, after = [blur(p, radius, limit, directions) for p in blur_programs]
                error = max(abs(a - b) for a, b in zip(before, after))
                assert error <= 1, (radius, limit, directions, error)
                blur_checks += 1
    print(f'PASS: {blur_checks} Gaussian image comparisons within 1/255; actual CPU coefficients, fractional radii, 8/64 samples and repeated horizontal/vertical passes.')
make_current(display, None, None, None)
api(egl, 'eglDestroyContext', U, P, P)(display, context)
api(egl, 'eglTerminate', U, P)(display)
