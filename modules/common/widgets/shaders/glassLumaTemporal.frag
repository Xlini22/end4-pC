#version 440
layout(location = 1) in float materialLuma;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float haze;
    vec4 temporalStep;
};
layout(binding = 2) uniform sampler2D historyLuma;
void main() {
    vec4 prior = texture(historyLuma, vec2(0.5));
    if (temporalStep.z < 0.0) {
        float held = temporalStep.w >= 0.0 ? mix(prior.b, prior.g, temporalStep.w) : materialLuma;
        fragColor = vec4(0.0, held, held, materialLuma);
        return;
    }
    float sum = prior.r + prior.a * temporalStep.x;
    if (temporalStep.z > 0.0) {
        float mean = temporalStep.z > 1.0 ? prior.a : sum;
        float from = temporalStep.w >= 0.0 ? mix(prior.b, prior.g, temporalStep.w) : prior.g;
        fragColor = vec4(prior.a * temporalStep.y, mean, from, materialLuma);
    } else fragColor = vec4(sum, prior.g, prior.b, materialLuma);
}
