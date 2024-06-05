#version 460 core

in vec3 vert_Position;

out vec4 out_Color;

void main()
{
    out_Color = vec4(fract(vert_Position * 4.0) * 0.5, 1.0);
}