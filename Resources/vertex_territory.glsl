#version 460 core

layout(location = 0) in vec3 in_Position;

layout(std140, binding = 0) uniform GlobalUniform
{
	mat4 view_Transform;
	mat4 proj_Transform;
	mat4 viewproj_TransformInv;
};

uniform mat4 model_Transform;

out vec2 uv_Coords;

void main()
{
	vec3 vert_Position = vec3(model_Transform * vec4(in_Position, 1.0));
	gl_Position = proj_Transform * view_Transform * vec4(vert_Position, 1.0);
	uv_Coords = gl_Position.xy * 0.5 + 0.5;
}