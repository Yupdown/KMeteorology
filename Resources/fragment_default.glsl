#version 460 core

uniform sampler2D main_Texture;

in vec3 vert_Position;

out vec4 out_Color;

void main()
{
    out_Color = vec4(0.0, 0.0, 0.0, 1.0);
}