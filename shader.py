from OpenGL.GL import *
from OpenGL.GL import shaders
import glm


class Shader:
    def __init__(self, vertex_shader_path, fragment_shader_path):
        self.vertex_shader_path = vertex_shader_path
        self.fragment_shader_path = fragment_shader_path
        self.active_shader = None
        self.active_shader_info = None

    def load_shaders(self):
        self.vertex_shader = open(self.vertex_shader_path, 'r').read()
        self.fragment_shader = open(self.fragment_shader_path, 'r').read()

        self.active_shader = shaders.compileProgram(
            shaders.compileShader(self.vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(self.fragment_shader, GL_FRAGMENT_SHADER),
        )

        self.active_shader_info = 'NORMAL_VERTEX'

        glUseProgram(self.active_shader)

    def change_shader(self, shader):
        self.active_shader_info = shader

        if shader == 'NIGHT_VERTEX':
            glClearColor(0.0, 0.0, 0.0, 0.0)
        else:
            glClearColor(1.0, 1.0, 1.0, 1.0)

    def load_matrixes(self):
        self.model = glm.mat4(1)
        self.view_matrix = glm.mat4(1)