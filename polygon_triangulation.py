# assume that the polygon is given in the form of a list of vertices
# and the order of the vertices is counter-clockwise

def triangulate_polygon(vertices):
    # vertices: list of vertices
    # returns: list of triangles (each triangle is a list of 3 vertices)
    n = len(vertices)
    if n < 3:
        return []
    triangles = []
    # create a list of indices of vertices
    indices = list(range(n))
    # create a list of the edges of the polygon
    edges = [(indices[i], indices[(i + 1) % n]) for i in range(n)]
    # create a list of the diagonals of the polygon
    diagonals = []
    for i in range(n):
        for j in range(i + 2, n):
            if (j + 1) % n == i:
                continue
            diagonals.append((indices[i], indices[j]))