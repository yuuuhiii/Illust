import re
with open('items/iso_line.py', 'r') as f:
    content = f.read()

# Restore original pen first
content = content.replace("Qt.PenStyle.NoPen", "Qt.PenStyle.SolidLine")

# Find the loop body
old_loop = """        for vf in visible_faces:
            item = QGraphicsPolygonItem()
            item.setPolygon(vf['poly'])
            r = min(255, max(0, int(self.base_color.red() * vf['factor'])))
            g = min(255, max(0, int(self.base_color.green() * vf['factor'])))
            b = min(255, max(0, int(self.base_color.blue() * vf['factor'])))
            item.setBrush(QBrush(QColor(r, g, b)))
            item.setPen(sel_pen if self.isSelected() else norm_pen)
            item.setParentItem(self)
            self.poly_items.append(item)"""

new_loop = """        for vf in visible_faces:
            item = QGraphicsPolygonItem()
            item.setPolygon(vf['poly'])
            r = min(255, max(0, int(self.base_color.red() * vf['factor'])))
            g = min(255, max(0, int(self.base_color.green() * vf['factor'])))
            b = min(255, max(0, int(self.base_color.blue() * vf['factor'])))
            brush_color = QColor(r, g, b)
            item.setBrush(QBrush(brush_color))
            if self.isSelected():
                item.setPen(sel_pen)
            else:
                if self.arrow_type == "flat" or vf.get('is_flat_part', False):
                    item.setPen(norm_pen)
                else:
                    item.setPen(QPen(brush_color, 1.0))
            item.setParentItem(self)
            self.poly_items.append(item)"""

content = content.replace(old_loop, new_loop)

# Let's also increase the segment count for cylinder and cone to make it look smooth!
content = content.replace("def generate_cylinder(radius, length, segments=12, offset_x=0):", "def generate_cylinder(radius, length, segments=36, offset_x=0):")
content = content.replace("def generate_cone(radius, length, segments=12, offset_x=0):", "def generate_cone(radius, length, segments=36, offset_x=0):")
content = content.replace("segments=12", "segments=36")

with open('items/iso_line.py', 'w') as f:
    f.write(content)
