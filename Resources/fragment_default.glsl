#version 460 core

uniform sampler2D main_Texture;

uniform vec4 model_Color;

in vec3 vert_Position;

out vec4 out_Color;

void main()
{
    out_Color = model_Color;
}