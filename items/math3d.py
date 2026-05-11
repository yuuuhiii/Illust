import math

def rotate_3d(x, y, z, rx, ry, rz):
    if rx != 0:
        rad = math.radians(rx)
        c, s = math.cos(rad), math.sin(rad)
        y, z = y * c - z * s, y * s + z * c
    if ry != 0:
        rad = math.radians(ry)
        c, s = math.cos(rad), math.sin(rad)
        x, z = x * c + z * s, -x * s + z * c
    if rz != 0:
        rad = math.radians(rz)
        c, s = math.cos(rad), math.sin(rad)
        x, y = x * c - y * s, x * s + y * c
    return x, y, z

def project_iso(x, y, z):
    angle = math.radians(30)
    c, s = math.cos(angle), math.sin(angle)
    return (x - y) * c, (x + y) * s - z

def compute_normal(face):
    if len(face) < 3: return (0,0,1)
    p0, p1, p2 = face[0], face[1], face[2]
    ux, uy, uz = p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]
    vx, vy, vz = p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]
    nx = uy*vz - uz*vy
    ny = uz*vx - ux*vz
    nz = ux*vy - uy*vx
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length == 0: return (0,0,1)
    return (nx/length, ny/length, nz/length)

def generate_sphere(radius, segments_theta=16, segments_phi=8):
    faces = []
    for i in range(segments_phi):
        phi1 = math.pi * i / segments_phi
        phi2 = math.pi * (i + 1) / segments_phi
        for j in range(segments_theta):
            theta1 = 2 * math.pi * j / segments_theta
            theta2 = 2 * math.pi * (j + 1) / segments_theta

            x1 = radius * math.sin(phi1) * math.cos(theta1)
            y1 = radius * math.sin(phi1) * math.sin(theta1)
            z1 = radius * math.cos(phi1)

            x2 = radius * math.sin(phi1) * math.cos(theta2)
            y2 = radius * math.sin(phi1) * math.sin(theta2)
            z2 = radius * math.cos(phi1)

            x3 = radius * math.sin(phi2) * math.cos(theta2)
            y3 = radius * math.sin(phi2) * math.sin(theta2)
            z3 = radius * math.cos(phi2)

            x4 = radius * math.sin(phi2) * math.cos(theta1)
            y4 = radius * math.sin(phi2) * math.sin(theta1)
            z4 = radius * math.cos(phi2)

            # Counter-clockwise for normals
            faces.append([(x1, y1, z1), (x4, y4, z4), (x3, y3, z3), (x2, y2, z2)])
    return faces

def generate_cylinder_vertical(radius, height, segments=16):
    faces = []
    # Bottom and top
    z0 = height / 2
    z1 = -height / 2

    # Side faces
    for i in range(segments):
        a1 = i * 2 * math.pi / segments
        a2 = (i + 1) * 2 * math.pi / segments

        x1, y1 = math.cos(a1) * radius, math.sin(a1) * radius
        x2, y2 = math.cos(a2) * radius, math.sin(a2) * radius

        faces.append([(x1, y1, z1), (x2, y2, z1), (x2, y2, z0), (x1, y1, z0)])

    # Caps
    faces.append([(math.cos(j * 2 * math.pi / segments) * radius, math.sin(j * 2 * math.pi / segments) * radius, z0) for j in range(segments)])
    faces.append([(math.cos(j * 2 * math.pi / segments) * radius, math.sin(j * 2 * math.pi / segments) * radius, z1) for j in range(segments)][::-1])

    return faces
