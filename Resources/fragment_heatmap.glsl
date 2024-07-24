#version 460 core

in float vert_Value;

uniform sampler2D main_Texture;
uniform vec2 u_PointValueRange;

out vec4 out_Color;

void main()
{
    float value = (vert_Value - u_PointValueRange.x) / (u_PointValueRange.y - u_PointValueRange.x);
    out_Color = texture(main_Texture, vec2(0.5f, 1.0f - value));
}