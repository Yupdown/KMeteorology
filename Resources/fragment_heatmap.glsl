#version 460 core

in vec3 vert_Position;

uniform sampler2D main_Texture;
uniform int u_PointCount;
uniform vec2 u_PointValueRange;
uniform vec2 u_PointCoords[114];
uniform float u_PointValues[114];

out vec4 out_Color;

void main()
{
    float value = 0.0f;
    float weight_sum = 0.0f;

    for (int i = 0; i < u_PointCount; i++)
    {
        if (u_PointValues[i] <= -50.0f)
            continue;
        vec2 delta = vert_Position.xy + u_PointCoords[i];
        float distance_sqr = dot(delta, delta);
        float weight = 1.0f / distance_sqr;
        value += u_PointValues[i] * weight;
        weight_sum += weight;
    }

    if (weight_sum != 0.0f)
        value /= weight_sum;

    value = (value - u_PointValueRange.x) / (u_PointValueRange.y - u_PointValueRange.x);
    out_Color = texture(main_Texture, vec2(0.5f, 1.0f - value));
}