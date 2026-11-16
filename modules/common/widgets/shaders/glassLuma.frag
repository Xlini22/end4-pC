#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 1) in float materialLuma;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float haze;
};
void main() { fragColor = vec4(materialLuma, 0.0, 0.0, 1.0); }
