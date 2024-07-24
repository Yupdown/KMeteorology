#version 460 core

layout(location = 0) in vec2 in_Position;
layout(location = 1) in float in_Value;

layout(std140, binding = 0) uniform GlobalUniform
{
	mat4 view_Transform;
	mat4 proj_Transform;
	mat4 viewproj_TransformInv;
};

uniform mat4 model_Transform;

out float vert_Value;

void main()
{
	vec3 vert_Position = vec3(model_Transform * vec4(in_Position, 0.0, 1.0));
	gl_Position = proj_Transform * view_Transform * vec4(vert_Position, 1.0);
    vert_Value = in_Value;
}