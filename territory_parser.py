import xml.etree.ElementTree as ET
from OpenGL.GL import *
import numpy as np
import logging

def parse_territory_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all elements with the tag 'path'
    paths = root.findall('.//{http://www.w3.org/2000/svg}path')
    territories = []
    for path in paths:
        # Get the 'id' attribute of the path element
        territory_id = path.get('id')
        # Get the 'd' attribute of the path element
        string_data = path.get('d')
        # split the string by spaces and append to the list as float numbers
        territory_d = []
        territory_c = set()
        for i in string_data.split():
            try:
                territory_d.append(float(i))
            except ValueError:
                if i == 'Z':
                    territory_c.add(len(territory_d) // 2)
        territories.append((territory_id, territory_d, territory_c))
    return territories


class TerritoryMesh:
    def __init__(self, path=None):
        self.vao = None
        self.vbo = None
        self.ebo = None

        self.vertices = []
        self.indices = []

        if path:
            self.load_data(path)
            self.gen_buffer()

    def delete_buffers(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteBuffers(1, [self.ebo])

    def load_data(self, path):
        territories = parse_territory_file(path)
        for territory in territories:
            for i in range(0, len(territory[1]), 2):
                self.vertices.extend((territory[1][i], territory[1][i + 1], 0))
            offset = len(self.vertices) // 3
            for i in range(0, len(self.vertices) // 3):
                if i in territory[2]:
                    continue
                self.indices.append(offset + i)
                self.indices.append(offset + i + 1)

        logging.log(logging.INFO, "Mesh loaded: %s" % path)
        logging.log(logging.INFO, "Vertices: %d" % len(self.vertices))
        logging.log(logging.INFO, "Indices: %d" % len(self.indices))

    def gen_buffer(self):
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        glBindVertexArray(self.vao)

        np_vertices = np.array(self.vertices, dtype=np.float32)
        np_indices = np.array(self.indices, dtype=np.uint32)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, np_vertices.nbytes, np_vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, 3 * sizeof(GLfloat), 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np_indices.nbytes, np_indices, GL_STATIC_DRAW)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)