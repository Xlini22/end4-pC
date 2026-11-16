#version 440
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float blend;
};
layout(binding = 1) uniform sampler2D previousLuma;
layout(binding = 2) uniform sampler2D targetLuma;
void main() {
    fragColor = mix(texture(previousLuma, vec2(0.5)), texture(targetLuma, vec2(0.5)), blend);
}
