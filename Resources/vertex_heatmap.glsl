#version 460 core

layout(location = 0) in vec3 in_Position;

layout(std140, binding = 0) uniform GlobalUniform
{
	mat4 view_Transform;
	mat4 proj_Transform;
	mat4 viewproj_TransformInv;
};

out vec3 vert_Position;

void main()
{
    vert_Position = vec3(viewproj_TransformInv * vec4(in_Position, 1.0));
	gl_Position = vec4(in_Position, 1.0);
}