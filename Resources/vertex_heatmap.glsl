#version 460 core

layout(location = 0) in vec3 in_Position;

layout(std140, binding = 0) uniform GlobalUniform
{
	mat4 view_Transform;
	mat4 proj_Transform;
};

out vec3 vert_Position;

void main()
{
	vert_Position = in_Position;
	gl_Position = vec4(in_Position, 1.0);
}