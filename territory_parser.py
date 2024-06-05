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
        for s in string_data.split('Z M'):
            territory_d = []
            for i in s.split():
                try:
                    territory_d.append(float(i))
                except ValueError:
                    pass
            territories.append((territory_id, territory_d))
    return territories


class TerritoryMesh:
    def __init__(self, path=None):
        self.vao = None
        self.vbo = None
        self.ebo = None

        self.vertices = []
        self.indices = []
        self.params = []

        if path:
            self.load_data(path)
            self.gen_buffer()

    def delete_buffers(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteBuffers(1, [self.ebo])

    def load_data(self, path):

        polar_n = None
        polar_s = None
        polar_w = None
        polar_e = None

        territories = parse_territory_file(path)
        for territory in territories:
            offset = len(self.vertices) // 3
            for i in range(0, len(territory[1]), 2):
                self.vertices.extend((territory[1][i], territory[1][i + 1], 0))
                if polar_n is None or territory[1][i + 1] < polar_n[1]:
                    polar_n = (territory[1][i], territory[1][i + 1])
                if polar_s is None or territory[1][i + 1] > polar_s[1]:
                    polar_s = (territory[1][i], territory[1][i + 1])
                if polar_w is None or territory[1][i] < polar_w[0]:
                    polar_w = (territory[1][i], territory[1][i + 1])
                if polar_e is None or territory[1][i] > polar_e[0]:
                    polar_e = (territory[1][i], territory[1][i + 1])
            for i in range(0, len(self.vertices) // 3 - offset):
                self.indices.append(offset + i)
            self.params.append((offset, len(self.vertices) // 3 - offset))

        logging.log(logging.INFO, "Mesh loaded: %s" % path)
        logging.log(logging.INFO, "Vertices: %d" % len(self.vertices))
        logging.log(logging.INFO, "Indices: %d" % len(self.indices))

        logging.log(logging.INFO, "Polar N: %s" % str(polar_n))
        logging.log(logging.INFO, "Polar S: %s" % str(polar_s))
        logging.log(logging.INFO, "Polar W: %s" % str(polar_w))
        logging.log(logging.INFO, "Polar E: %s" % str(polar_e))

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
