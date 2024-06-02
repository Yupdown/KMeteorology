from OpenGL.GL import *
import ctypes
import pyassimp as assimp
import numpy as np
import logging


class Mesh:
    def __init__(self, path=None):
        self.vao = None
        self.vbo = None
        self.ebo = None

        self.vertices = []
        self.normals = []
        self.colors = []
        self.uvs = []
        self.indices = []

        self.center = [0.0, 0.0, 0.0]
        self.radius = 0.0

        if path:
            self.load_data(path)
            self.gen_buffer()

    def delete_buffers(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(4, self.vbo)
        glDeleteBuffers(1, [self.ebo])

    def load_data(self, path):
        with assimp.load(path) as scene:
            if not scene:
                raise Exception("No mesh in file")
            meshes = scene.meshes

        self.vertices = []
        self.normals = []
        self.colors = []
        self.uvs = []
        self.indices = []

        min_coords = [float('inf') for _ in range(3)]
        max_coords = [-float('inf') for _ in range(3)]

        for mesh in meshes:
            for i in range(len(mesh.vertices)):
                for j in range(3):
                    min_coords[j] = min(min_coords[j], mesh.vertices[i][j])
                    max_coords[j] = max(max_coords[j], mesh.vertices[i][j])
                self.vertices.extend(mesh.vertices[i])
                if mesh.normals.any():
                    self.normals.extend(mesh.normals[i])
                else:
                    self.normals.extend((0.0, 0.0, 0.0))
                self.colors.extend((1.0, 1.0, 1.0))
                if mesh.texturecoords.any():
                    self.uvs.extend(mesh.texturecoords[0][i])
                else:
                    self.uvs.extend((0.0, 0.0))

            for i in range(len(mesh.faces)):
                self.indices.extend(mesh.faces[i])

        self.center = [(min_coords[i] + max_coords[i]) / 2 for i in range(3)]
        self.radius = max([max_coords[i] - min_coords[i] for i in range(3)]) / 2

        logging.log(logging.INFO, "Mesh loaded: %s" % path)
        logging.log(logging.INFO, "Vertices: %d" % len(self.vertices))
        logging.log(logging.INFO, "Indices: %d" % len(self.indices))
        logging.log(logging.INFO, "Center: %s" % str(self.center))
        logging.log(logging.INFO, "Radius: %f" % self.radius)

    def gen_buffer(self):
        np_vertices = np.array(self.vertices, dtype=np.float32)
        np_normals = np.array(self.normals, dtype=np.float32)
        np_colors = np.array(self.colors, dtype=np.float32)
        np_uvs = np.array(self.uvs, dtype=np.float32)
        np_indices = np.array(self.indices, dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(4)
        self.ebo = glGenBuffers(1)
        glBindVertexArray(self.vao)

        # position
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo[0])
        glBufferData(GL_ARRAY_BUFFER, np_vertices.nbytes, np_vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # normals
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo[1])
        glBufferData(GL_ARRAY_BUFFER, np_normals.nbytes, np_normals, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # colors
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo[2])
        glBufferData(GL_ARRAY_BUFFER, np_colors.nbytes, np_colors, GL_STATIC_DRAW)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(2)

        # uv
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo[3])
        glBufferData(GL_ARRAY_BUFFER, np_uvs.nbytes, np_uvs, GL_STATIC_DRAW)
        glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, 3 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(3)

        # indices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np_indices.nbytes, np_indices, GL_STATIC_DRAW)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)