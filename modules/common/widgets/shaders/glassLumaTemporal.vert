#version 440
layout(location = 0) in vec4 qt_Vertex;
layout(location = 1) in vec2 qt_MultiTexCoord0;
layout(location = 0) out vec2 qt_TexCoord0;
layout(location = 1) out float materialLuma;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float haze;
    vec4 temporalStep;
};
layout(binding = 1) uniform sampler2D backdrop;
void main() {
    gl_Position = qt_Matrix * qt_Vertex;
    qt_TexCoord0 = qt_MultiTexCoord0;
    materialLuma = 0.0;
    float lod = log2(max(haze, 1.0));
    for (int y = 0; y < 2; ++y)
        for (int x = 0; x < 2; ++x) {
            vec3 reference = textureLod(backdrop, vec2(float(x), float(y)) * 0.5 + 0.25, lod).rgb;
            materialLuma = max(materialLuma, dot(max(reference, vec3(0.0)), vec3(0.2126, 0.7152, 0.0722)));
        }
}
