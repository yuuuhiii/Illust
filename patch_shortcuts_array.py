import re

with open('ui/main_window.py', 'r') as f:
    content = f.read()

# Add imports for array dialog and QKeySequence
import_search = 'from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,'
import_repl = 'from PyQt6.QtGui import QKeySequence, QShortcut\nfrom PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QDialog, QDialogButtonBox, QFormLayout,'
content = content.replace(import_search, import_repl)

# Add Array Duplicate action to UI
array_search = '        panel_layout.addWidget(btn_delete)'
array_repl = '''        panel_layout.addWidget(btn_delete)

        btn_array = QPushButton("配列複製")
        btn_array.clicked.connect(self.show_array_duplicate_dialog)
        panel_layout.addWidget(btn_array)'''
content = content.replace(array_search, array_repl)

# Add shortcuts
shortcut_search = '        self.canvas.scene.selectionChanged.connect(self.sync_ui_to_selection)'
shortcut_repl = '''        self.canvas.scene.selectionChanged.connect(self.sync_ui_to_selection)

        # Shortcuts
        self.shortcut_copy = QShortcut(QKeySequence.StandardKey.Copy, self)
        self.shortcut_copy.activated.connect(self.copy_item)
        self.shortcut_paste = QShortcut(QKeySequence.StandardKey.Paste, self)
        self.shortcut_paste.activated.connect(self.paste_item)
        self.copied_item = None'''
content = content.replace(shortcut_search, shortcut_repl)

# Add copy, paste, array methods
methods = '''
    def copy_item(self):
        selected = self.canvas.scene.selectedItems()
        if selected:
            self.copied_item = selected[0]

    def paste_item(self):
        if self.copied_item:
            try:
                new_item = self.copied_item.clone()
                # Offset slightly so it's visible
                offset_pos = self.copied_item.pos() + QPointF(20, 20)
                self.canvas.add_block(new_item, offset_pos)
                self.canvas.scene.clearSelection()
                new_item.setSelected(True)
            except AttributeError:
                pass # Item might not have clone method

    def show_array_duplicate_dialog(self):
        selected = self.canvas.scene.selectedItems()
        if not selected:
            return
        item = selected[0]
        if not hasattr(item, 'clone'):
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("配列複製")
        layout = QFormLayout(dialog)

        spin_nx = QSpinBox(); spin_nx.setRange(1, 100); spin_nx.setValue(1)
        spin_ny = QSpinBox(); spin_ny.setRange(1, 100); spin_ny.setValue(1)
        spin_nz = QSpinBox(); spin_nz.setRange(1, 100); spin_nz.setValue(1)

        spin_dx = QSpinBox(); spin_dx.setRange(-1000, 1000); spin_dx.setValue(150); spin_dx.setSingleStep(10)
        spin_dy = QSpinBox(); spin_dy.setRange(-1000, 1000); spin_dy.setValue(100); spin_dy.setSingleStep(10)
        spin_dz = QSpinBox(); spin_dz.setRange(-1000, 1000); spin_dz.setValue(0); spin_dz.setSingleStep(10)

        layout.addRow("X方向の個数:", spin_nx)
        layout.addRow("Y方向の個数:", spin_ny)
        layout.addRow("Z方向の個数:", spin_nz)
        layout.addRow("X方向の間隔:", spin_dx)
        layout.addRow("Y方向の間隔:", spin_dy)
        layout.addRow("Z方向の間隔:", spin_dz)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            from items.math3d import project_iso
            base_pos = item.scenePos()

            for ix in range(spin_nx.value()):
                for iy in range(spin_ny.value()):
                    for iz in range(spin_nz.value()):
                        if ix == 0 and iy == 0 and iz == 0:
                            continue # Skip original

                        # Calculate 3D offset
                        off_x = ix * spin_dx.value()
                        off_y = iy * spin_dy.value()
                        off_z = iz * spin_dz.value()

                        # Project offset to screen space
                        sx, sy = project_iso(off_x, off_y, off_z)

                        new_item = item.clone()
                        self.canvas.add_block(new_item, base_pos + QPointF(sx, sy))
'''
content += methods

with open('ui/main_window.py', 'w') as f:
    f.write(content)
