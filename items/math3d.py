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
