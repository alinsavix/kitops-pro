from mathutils import *

def vector_sum(vectors):
    return sum(vectors, Vector())


def coordinates_dimension(coordinates):
    x = [coord[0] for coord in coordinates]
    y = [coord[1] for coord in coordinates]
    z = [coord[2] for coord in coordinates]

    return  Vector((max(x), max(y), max(z))) - Vector((min(x), min(y), min(z)))
