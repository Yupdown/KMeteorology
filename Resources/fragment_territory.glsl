#version 460 core

uniform sampler2D main_Texture;

in vec2 uv_Coords;

out vec4 out_Color;

void main()
{
    out_Color = texture(main_Texture, uv_Coords);
}