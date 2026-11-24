#version 440
layout(location = 0) in vec4 qt_Vertex;
layout(location = 1) in vec2 qt_MultiTexCoord0;
layout(location = 0) out vec2 qt_TexCoord0;
layout(location = 1) out float materialLuma;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    vec4 radii;
    vec4 wash;
    float qt_Opacity;
    vec2 size;
    float rimWidth;
    float pull;
    float split;
    float haze;
    float vividness;
    float sheen;
    vec2 flares;
    vec2 hangs;
    float edge;
    float enhanced;
    float frosted;
    float darkening;
    float automaticDarkening;
    float holdDarkening;
    float darkeningBlend;
    float automaticDarkeningStrength;
};

layout(binding = 1) uniform sampler2D backdrop;
layout(binding = 2) uniform sampler2D previousLuma;
layout(binding = 3) uniform sampler2D targetLuma;
void main() {
    gl_Position = qt_Matrix * qt_Vertex;
    qt_TexCoord0 = qt_MultiTexCoord0;
    materialLuma = 0.0;
    if (automaticDarkening <= 0.0) return;
    if (holdDarkening > 0.5) {
        materialLuma = mix(textureLod(previousLuma, vec2(0.5), 0.0).b,
            textureLod(targetLuma, vec2(0.5), 0.0).g, darkeningBlend);
        return;
    }
    float lod = log2(max(haze, 1.0));
    // Same four probes as the native renderer, evaluated only at the quad vertices.
    float backdropLuma = 0.0;
    for (int y = 0; y < 2; ++y)
        for (int x = 0; x < 2; ++x) {
            vec3 reference = textureLod(backdrop, vec2(float(x), float(y)) * 0.5 + 0.25, lod).rgb;
            backdropLuma = max(backdropLuma, dot(max(reference, vec3(0.0)), vec3(0.2126, 0.7152, 0.0722)));
        }

    materialLuma = backdropLuma;
}
