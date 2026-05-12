import re

with open('ui/main_window.py', 'r') as f:
    content = f.read()

pattern = r'        def update_preview\(\):.*?preview_items\.clear\(\)'

replacement = '''        def update_preview():
            # Clear old previews
            for p_item in preview_items:
                self.canvas.scene.removeItem(p_item)
            preview_items.clear()

            from items.math3d import project_iso

            # Collect data for sorting
            preview_data = []

            for ix in range(spin_nx.value()):
                for iy in range(spin_ny.value()):
                    for iz in range(spin_nz.value()):
                        if ix == 0 and iy == 0 and iz == 0:
                            continue

                        off_x = ix * spin_dx.value()
                        off_y = iy * spin_dy.value()
                        off_z = iz * spin_dz.value()

                        sx, sy = project_iso(off_x, off_y, off_z)

                        # Depth formula matching the block rendering
                        # X goes right-down (+depth), Y goes left-down (+depth), Z goes up (-depth)
                        # So depth is roughly x + y - z. Let's use the offset for sorting.
                        # Wait, Z goes down in Qt screen space but up in 3D space.
                        # In items/iso_block.py, Z=0 to -h means it goes UP physically, so depth = cx + cy + cz
                        depth = off_x + off_y - off_z

                        preview_data.append({
                            'sx': sx, 'sy': sy, 'depth': depth
                        })

            # Include the original item in the logical depth sort to figure out relative Z values
            # But we can't change the original item's Z value easily without messing up block_list.
            # So let's just sort the preview items based on their offset depth.
            # The preview items will all be drawn roughly at the same Z level as the original item.
            preview_data.sort(key=lambda d: d['depth'])

            base_z = item.zValue()

            for i, data in enumerate(preview_data):
                p_item = item.clone()
                p_item.setOpacity(item.opacity() * 0.5)
                p_item.setFlag(p_item.GraphicsItemFlag.ItemIsSelectable, False)
                p_item.setFlag(p_item.GraphicsItemFlag.ItemIsMovable, False)

                self.canvas.scene.addItem(p_item)
                p_item.setPos(base_pos + QPointF(data['sx'], data['sy']))

                # Interleave previews using fractional Z values
                # Original item is at base_z. If depth > 0, it should be in front (+z).
                # If depth < 0, it should be behind (-z).
                if data['depth'] >= 0:
                    p_item.setZValue(base_z + 0.001 * (i + 1))
                else:
                    p_item.setZValue(base_z - 0.001 * (len(preview_data) - i))

                preview_items.append(p_item)

        # Connect signals for live preview
        spin_nx.valueChanged.connect(lambda: update_preview())
        spin_ny.valueChanged.connect(lambda: update_preview())
        spin_nz.valueChanged.connect(lambda: update_preview())
        spin_dx.valueChanged.connect(lambda: update_preview())
        spin_dy.valueChanged.connect(lambda: update_preview())
        spin_dz.valueChanged.connect(lambda: update_preview())

        update_preview()

        result = dialog.exec()

        # Cleanup previews
        for p_item in preview_items:
            self.canvas.scene.removeItem(p_item)
        preview_items.clear()'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
with open('ui/main_window.py', 'w') as f:
    f.write(new_content)
