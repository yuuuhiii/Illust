import re

with open('items/iso_block.py', 'r') as f:
    content = f.read()

# Replace imports
content = content.replace(
    'from items.math3d import rotate_3d, project_iso, compute_normal',
    'from items.math3d import rotate_3d, project_iso, compute_normal, generate_sphere, generate_cylinder_vertical'
)

# Update init
content = content.replace(
    'def __init__(self, w=150, d=100, h=40, base_color=QColor(200, 200, 210), opacity=100):',
    'def __init__(self, block_type="box", w=150, d=100, h=40, base_color=QColor(200, 200, 210), opacity=100):'
)

content = content.replace(
    'self.w, self.d, self.h = w, d, h\n        self.base_color = base_color',
    'self.block_type = block_type\n        self.w, self.d, self.h = w, d, h\n        self.base_color = base_color'
)

# Update _generate_mesh
search_mesh = '''    def _generate_mesh(self):
        faces = []

        # Origin maps to front top point as in original implementation.
        # Original:
        # X: right down (w)
        # Y: left down (d)
        # Z: up (h) but drawing went down for height.
        # Let's map X=w, Y=-d, Z=-h in standard space, then translate.

        # To match original IsoBlockItem exactly when rotations are 0:
        # Front top is 0,0.
        # X axis (width) goes in X direction.
        # Y axis (depth) goes in Y direction.
        # Z axis (height) goes down in 2D, which means -Z in our project_iso function?
        # Let's check project_iso: (x-y)*c, (x+y)*s - z.
        # Original v_right_top: (w*c, -w*s). Wait, project_iso for (w, 0, 0) gives (w*c, w*s).
        # Let's see: project_iso(x,y,z) = (x-y)*c, (x+y)*s - z.
        # Original v_right_top: x = w*c, y = w*s ? No, original says: x = w*c, y = -w*s.
        # Oh, if we use project_iso(w, 0, 0), it gives: x = w*c, y = w*s.
        # But wait, original says: v_right_top = (w*cos_a, -w*sin_a) -> this means it goes up-right.
        # Let's adjust coordinate generation for this block to match the original orientation.
        # If we just want a box:
        # We can construct the 8 vertices and then the 6 faces.

        x0, x1 = 0, self.w
        y0, y1 = 0, self.d
        z0, z1 = 0, -self.h

        # 8 vertices
        v000 = (x0, y0, z0)
        v100 = (x1, y0, z0)
        v110 = (x1, y1, z0)
        v010 = (x0, y1, z0)
        v001 = (x0, y0, z1)
        v101 = (x1, y0, z1)
        v111 = (x1, y1, z1)
        v011 = (x0, y1, z1)

        faces = [
            [v000, v100, v110, v010], # Top (z=0)
            [v001, v011, v111, v101], # Bottom (z=-h)
            [v000, v010, v011, v001], # Left (x=0)
            [v100, v101, v111, v110], # Right (x=w)
            [v000, v001, v101, v100], # Front (y=0)
            [v010, v110, v111, v011], # Back (y=d)
        ]

        # We need to correctly align normals. The above vertices are ordered somewhat arbitrarily.
        # Let's order them counter-clockwise when looking from outside.
        faces = [
            [v000, v010, v110, v100], # Top (z=0, looking from top, normal -z. Wait, Z is down, so Top is Z=0. Normal: up)
            [v001, v101, v111, v011], # Bottom
            [v000, v001, v011, v010], # Front-Left (x=0)
            [v100, v110, v111, v101], # Back-Right (x=w)
            [v000, v100, v101, v001], # Front-Right (y=0)
            [v010, v011, v111, v110], # Back-Left (y=d)
        ]

        # Center of rotation should probably be the center of the block.
        cx = self.w / 2
        cy = self.d / 2
        cz = -self.h / 2'''

replace_mesh = '''    def _generate_mesh(self):
        faces = []

        cx = self.w / 2
        cy = self.d / 2
        cz = -self.h / 2

        if self.block_type == "box":
            x0, x1 = 0, self.w
            y0, y1 = 0, self.d
            z0, z1 = 0, -self.h

            v000 = (x0, y0, z0)
            v100 = (x1, y0, z0)
            v110 = (x1, y1, z0)
            v010 = (x0, y1, z0)
            v001 = (x0, y0, z1)
            v101 = (x1, y0, z1)
            v111 = (x1, y1, z1)
            v011 = (x0, y1, z1)

            faces = [
                [v000, v010, v110, v100], # Top
                [v001, v101, v111, v011], # Bottom
                [v000, v001, v011, v010], # Front-Left
                [v100, v110, v111, v101], # Back-Right
                [v000, v100, v101, v001], # Front-Right
                [v010, v011, v111, v110], # Back-Left
            ]
        elif self.block_type == "cylinder":
            radius = min(self.w, self.d) / 2
            cyl_faces = generate_cylinder_vertical(radius, self.h, segments=16)
            for face in cyl_faces:
                faces.append([(x + cx, y + cy, z + cz) for x, y, z in face])
        elif self.block_type == "sphere":
            radius = min(self.w, self.d, self.h) / 2
            sph_faces = generate_sphere(radius, segments_theta=16, segments_phi=8)
            for face in sph_faces:
                faces.append([(x + cx, y + cy, z + cz) for x, y, z in face])'''

content = content.replace(search_mesh, replace_mesh)

# Update update_geometry
content = content.replace(
    'def update_geometry(self, w=None, d=None, h=None, base_color=None, opacity=None, rot_x=None, rot_y=None, rot_z=None):',
    'def update_geometry(self, block_type=None, w=None, d=None, h=None, base_color=None, opacity=None, rot_x=None, rot_y=None, rot_z=None):'
)

content = content.replace(
    'self.prepareGeometryChange()\n\n        if w is not None: self.w = w',
    'self.prepareGeometryChange()\n\n        if block_type is not None: self.block_type = block_type\n        if w is not None: self.w = w'
)

# Add clone
clone_method = '''
    def clone(self):
        new_item = IsoBlockItem(block_type=self.block_type, w=self.w, d=self.d, h=self.h, base_color=self.base_color, opacity=self.opacity_val)
        new_item.rot_x = self.rot_x
        new_item.rot_y = self.rot_y
        new_item.rot_z = self.rot_z
        new_item.update_geometry()
        return new_item
'''
content += clone_method

with open('items/iso_block.py', 'w') as f:
    f.write(content)
