import re

# IsoLineItem clone
with open('items/iso_line.py', 'r') as f:
    content = f.read()
clone_method = '''
    def clone(self):
        new_item = IsoLineItem(length=self.length, thickness=self.thickness, arrow_type=self.arrow_type, arrow_pos=self.arrow_pos, base_color=self.base_color, opacity=self.opacity_val)
        new_item.rot_x = self.rot_x
        new_item.rot_y = self.rot_y
        new_item.rot_z = self.rot_z
        new_item.update_geometry()
        return new_item
'''
content += clone_method
with open('items/iso_line.py', 'w') as f:
    f.write(content)

# IsoShapeItem clone
with open('items/iso_shape.py', 'r') as f:
    content = f.read()
clone_method = '''
    def clone(self):
        new_item = IsoShapeItem(shape_type=self.shape_type, size=self.size, base_color=self.base_color, opacity=self.opacity_val)
        new_item.rot_x = self.rot_x
        new_item.rot_y = self.rot_y
        new_item.rot_z = self.rot_z
        new_item.update_geometry()
        return new_item
'''
content += clone_method
with open('items/iso_shape.py', 'w') as f:
    f.write(content)

# IsoTextItem clone
with open('items/iso_text.py', 'r') as f:
    content = f.read()
clone_method = '''
    def clone(self):
        new_item = IsoTextItem(text=self.text, font_size=self.font_size, plane=self.plane, base_color=self.base_color, opacity=self.opacity_val)
        new_item.update_geometry()
        return new_item
'''
content += clone_method
with open('items/iso_text.py', 'w') as f:
    f.write(content)
