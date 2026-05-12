with open('ui/main_window.py', 'r') as f:
    content = f.read()

import re

# Replace everything from def update_preview to the end of the file
pattern = r'        def update_preview\(\):.*'

replacement = '''        def update_preview():
            # Clear old previews
            for p_item in preview_items:
                self.canvas.scene.removeItem(p_item)
            preview_items.clear()

            from items.math3d import project_iso
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
                        depth = off_x + off_y - off_z

                        preview_data.append({
                            'sx': sx, 'sy': sy, 'depth': depth
                        })

            preview_data.sort(key=lambda d: d['depth'])
            base_z = item.zValue()

            for i, data in enumerate(preview_data):
                p_item = item.clone()
                p_item.setOpacity(item.opacity_val * 0.5)
                p_item.setFlag(p_item.GraphicsItemFlag.ItemIsSelectable, False)
                p_item.setFlag(p_item.GraphicsItemFlag.ItemIsMovable, False)

                self.canvas.scene.addItem(p_item)
                p_item.setPos(base_pos + QPointF(data['sx'], data['sy']))

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
        preview_items.clear()

        if result == QDialog.DialogCode.Accepted:
            from items.math3d import project_iso

            new_items_data = []

            for ix in range(spin_nx.value()):
                for iy in range(spin_ny.value()):
                    for iz in range(spin_nz.value()):
                        if ix == 0 and iy == 0 and iz == 0:
                            continue

                        off_x = ix * spin_dx.value()
                        off_y = iy * spin_dy.value()
                        off_z = iz * spin_dz.value()

                        sx, sy = project_iso(off_x, off_y, off_z)
                        depth = off_x + off_y - off_z
                        new_items_data.append({
                            'sx': sx, 'sy': sy, 'depth': depth
                        })

            # Sort newly created items by depth
            new_items_data.sort(key=lambda d: d['depth'])

            # Extract items that are behind the original (depth < 0) and in front (depth >= 0)
            items_behind = [d for d in new_items_data if d['depth'] < 0]
            items_front = [d for d in new_items_data if d['depth'] >= 0]

            idx = self.canvas.block_list.index(item) if item in self.canvas.block_list else -1

            if idx >= 0:
                self.canvas.block_list.remove(item)

                # Insert items behind, then the original, then items in front
                for data in items_behind:
                    new_item = item.clone()
                    self.canvas.scene.addItem(new_item)
                    new_item.setPos(base_pos + QPointF(data['sx'], data['sy']))
                    self.canvas.block_list.insert(idx, new_item)
                    idx += 1

                self.canvas.block_list.insert(idx, item)
                idx += 1

                for data in items_front:
                    new_item = item.clone()
                    self.canvas.scene.addItem(new_item)
                    new_item.setPos(base_pos + QPointF(data['sx'], data['sy']))
                    self.canvas.block_list.insert(idx, new_item)
                    idx += 1

                self.canvas.update_z_values()
            else:
                # Fallback if somehow not in block_list
                for data in new_items_data:
                    new_item = item.clone()
                    self.canvas.add_block(new_item, base_pos + QPointF(data['sx'], data['sy']))
'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
with open('ui/main_window.py', 'w') as f:
    f.write(new_content)
