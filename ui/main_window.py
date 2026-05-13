import json
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QSpinBox, QLabel, QColorDialog, QCheckBox, QComboBox, QFileDialog, QMessageBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QPointF

from canvas.view import CanvasView
from tools.select_tool import SelectTool
from tools.iso_tool import DrawIsoBlockTool
from tools.iso_line_tool import DrawIsoLineTool
from items.iso_block import IsoBlockItem
from items.iso_line import IsoLineItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("汎用3D概念図エディタ (ファイル分割・配列レイヤー版)")
        self.resize(1100, 700)

        main_layout = QHBoxLayout()
        self.canvas = CanvasView()
        self.canvas.scene.selectionChanged.connect(self.sync_ui_to_selection)

        panel_layout = QVBoxLayout()
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        panel_layout.addWidget(QLabel("<b>【ツール】</b>"))
        btn_select = QPushButton("選択・移動ツール")
        btn_select.clicked.connect(lambda: self.canvas.tool_manager.set_tool(SelectTool(self.canvas)))
        
        btn_draw_iso = QPushButton("3Dブロック配置ツール")
        btn_draw_iso.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoBlockTool(self.canvas, self.get_block_props)))

        btn_draw_line = QPushButton("線・矢印ツール")
        btn_draw_line.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoLineTool(self.canvas, self.get_line_props)))

        panel_layout.addWidget(btn_select)
        panel_layout.addWidget(btn_draw_iso)
        panel_layout.addWidget(btn_draw_line)
        
        self.cb_snap = QCheckBox("グリッドにスナップ")
        self.cb_snap.setChecked(True)
        self.cb_snap.stateChanged.connect(self.toggle_snap)
        panel_layout.addWidget(self.cb_snap)

        panel_layout.addSpacing(20)

        panel_layout.addWidget(QLabel("<b>【プロパティ】</b>"))
        
        def create_spinbox(label, min_v, max_v, default_v, step=10):
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(label))
            spin = QSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(default_v)
            spin.setSingleStep(step)
            spin.valueChanged.connect(self.update_selected_item)
            h_layout.addWidget(spin)
            panel_layout.addLayout(h_layout)
            return spin

        self.spin_w = create_spinbox("幅 (W):", 10, 500, 200)
        self.spin_d = create_spinbox("奥行き (D):", 10, 500, 120)
        self.spin_h = create_spinbox("高さ (H):", 1, 500, 30, step=1)
        self.spin_opacity = create_spinbox("透過率 (%):", 10, 100, 100)

        panel_layout.addWidget(QLabel("<b>【線・矢印プロパティ】</b>"))
        self.spin_length = create_spinbox("長さ (L):", 1, 1000, 100, step=10)
        self.spin_thickness = create_spinbox("線の太さ:", 1, 100, 10, step=1)

        h_layout_arrow = QHBoxLayout()
        h_layout_arrow.addWidget(QLabel("矢印の形:"))
        self.combo_arrow_type = QComboBox()
        self.combo_arrow_type.addItem("なし", "none")
        self.combo_arrow_type.addItem("フラット", "flat")
        self.combo_arrow_type.addItem("立体", "cylinder")
        self.combo_arrow_type.currentIndexChanged.connect(self.update_selected_item)
        h_layout_arrow.addWidget(self.combo_arrow_type)
        panel_layout.addLayout(h_layout_arrow)

        h_layout_pos = QHBoxLayout()
        h_layout_pos.addWidget(QLabel("矢印の位置:"))
        self.combo_arrow_pos = QComboBox()
        self.combo_arrow_pos.addItem("終点", "end")
        self.combo_arrow_pos.addItem("始点", "start")
        self.combo_arrow_pos.addItem("両端", "both")
        self.combo_arrow_pos.currentIndexChanged.connect(self.update_selected_item)
        h_layout_pos.addWidget(self.combo_arrow_pos)
        panel_layout.addLayout(h_layout_pos)

        self.spin_rot_x = create_spinbox("回転 X:", 0, 359, 0, step=5)
        self.spin_rot_x.setWrapping(True)
        self.spin_rot_y = create_spinbox("回転 Y:", 0, 359, 0, step=5)
        self.spin_rot_y.setWrapping(True)
        self.spin_rot_z = create_spinbox("回転 Z:", 0, 359, 0, step=5)
        self.spin_rot_z.setWrapping(True)

        self.current_color = QColor(150, 170, 220)
        self.btn_color = QPushButton("色を選択")
        self.update_color_btn_style()
        self.btn_color.clicked.connect(self.choose_color)
        panel_layout.addWidget(self.btn_color)
        
        panel_layout.addSpacing(20)

        panel_layout.addWidget(QLabel("<b>【レイヤー・操作】</b>"))
        self.label_z_index = QLabel("現在のレイヤー: -")
        self.label_z_index.setStyleSheet("color: blue; font-weight: bold;")
        panel_layout.addWidget(self.label_z_index)

        h_layer = QHBoxLayout()
        btn_front = QPushButton("前面へ")
        btn_front.clicked.connect(lambda: self.change_z_index("front"))
        btn_back = QPushButton("背面へ")
        btn_back.clicked.connect(lambda: self.change_z_index("back"))
        h_layer.addWidget(btn_front)
        h_layer.addWidget(btn_back)
        panel_layout.addLayout(h_layer)
        
        btn_delete = QPushButton("削除 (Del)")
        btn_delete.clicked.connect(self.delete_selected)
        panel_layout.addWidget(btn_delete)

        btn_duplicate = QPushButton("複製 (Ctrl+D)")
        btn_duplicate.clicked.connect(self.duplicate_selected)
        panel_layout.addWidget(btn_duplicate)

        panel_layout.addSpacing(20)
        panel_layout.addWidget(QLabel("<b>【ファイル】</b>"))

        h_file = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_to_json)
        btn_load = QPushButton("読み込み")
        btn_load.clicked.connect(self.load_from_json)
        h_file.addWidget(btn_save)
        h_file.addWidget(btn_load)
        panel_layout.addLayout(h_file)

        panel_widget = QWidget()
        panel_widget.setLayout(panel_layout)
        panel_widget.setFixedWidth(250)
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(panel_widget)
        
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def toggle_snap(self, state):
        IsoBlockItem.SNAP_ENABLED = (state == 2)
        IsoLineItem.SNAP_ENABLED = (state == 2)

    def sync_ui_to_selection(self):
        selected = self.canvas.scene.selectedItems()
        if selected and isinstance(selected[0], IsoBlockItem):
            item = selected[0]
            self.spin_w.blockSignals(True); self.spin_w.setValue(item.w); self.spin_w.blockSignals(False)
            self.spin_d.blockSignals(True); self.spin_d.setValue(item.d); self.spin_d.blockSignals(False)
            self.spin_h.blockSignals(True); self.spin_h.setValue(item.h); self.spin_h.blockSignals(False)
            self.spin_opacity.blockSignals(True); self.spin_opacity.setValue(item.opacity_val); self.spin_opacity.blockSignals(False)
            self.current_color = item.base_color
            self.update_color_btn_style()
            
            # 配列内のインデックスを表示
            if item in self.canvas.block_list:
                self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")
        elif selected and isinstance(selected[0], IsoLineItem):
            item = selected[0]
            self.spin_length.blockSignals(True); self.spin_length.setValue(int(item.length)); self.spin_length.blockSignals(False)
            self.spin_thickness.blockSignals(True); self.spin_thickness.setValue(int(item.thickness)); self.spin_thickness.blockSignals(False)
            self.spin_opacity.blockSignals(True); self.spin_opacity.setValue(item.opacity_val); self.spin_opacity.blockSignals(False)
            self.spin_rot_x.blockSignals(True); self.spin_rot_x.setValue(int(item.rot_x) % 360); self.spin_rot_x.blockSignals(False)
            self.spin_rot_y.blockSignals(True); self.spin_rot_y.setValue(int(item.rot_y) % 360); self.spin_rot_y.blockSignals(False)
            self.spin_rot_z.blockSignals(True); self.spin_rot_z.setValue(int(item.rot_z) % 360); self.spin_rot_z.blockSignals(False)

            idx = self.combo_arrow_type.findData(item.arrow_type)
            if idx >= 0:
                self.combo_arrow_type.blockSignals(True); self.combo_arrow_type.setCurrentIndex(idx); self.combo_arrow_type.blockSignals(False)

            idx_pos = self.combo_arrow_pos.findData(getattr(item, 'arrow_pos', 'end'))
            if idx_pos >= 0:
                self.combo_arrow_pos.blockSignals(True); self.combo_arrow_pos.setCurrentIndex(idx_pos); self.combo_arrow_pos.blockSignals(False)

            self.current_color = item.base_color
            self.update_color_btn_style()

            if item in self.canvas.block_list:
                self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")
        else:
            self.label_z_index.setText("現在のレイヤー: -")

    def update_selected_item(self):
        selected = self.canvas.scene.selectedItems()
        if selected and isinstance(selected[0], IsoBlockItem):
            item = selected[0]
            item.update_geometry(w=self.spin_w.value(), d=self.spin_d.value(),
                                 h=self.spin_h.value(), base_color=self.current_color,
                                 opacity=self.spin_opacity.value())
        elif selected and isinstance(selected[0], IsoLineItem):
            item = selected[0]
            item.update_geometry(length=self.spin_length.value(),
                                 thickness=self.spin_thickness.value(),
                                 arrow_type=self.combo_arrow_type.currentData(),
                                 arrow_pos=self.combo_arrow_pos.currentData(),
                                 base_color=self.current_color,
                                 opacity=self.spin_opacity.value(),
                                 rot_x=self.spin_rot_x.value(),
                                 rot_y=self.spin_rot_y.value(),
                                 rot_z=self.spin_rot_z.value())

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.update_color_btn_style()
            self.update_selected_item()

    def update_color_btn_style(self):
        self.btn_color.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid gray; padding: 5px;")

    def get_block_props(self):
        return self.spin_w.value(), self.spin_d.value(), self.spin_h.value(), self.current_color, self.spin_opacity.value()

    def get_line_props(self):
        return self.spin_thickness.value(), self.combo_arrow_type.currentData(), self.combo_arrow_pos.currentData(), self.current_color, self.spin_opacity.value(), self.spin_rot_x.value(), self.spin_rot_y.value(), self.spin_rot_z.value()

    def delete_selected(self):
        for item in self.canvas.scene.selectedItems():
            self.canvas.remove_block(item)

    def duplicate_selected(self):
        selected = self.canvas.scene.selectedItems()
        if not selected:
            return

        new_selection = []
        self.canvas.scene.clearSelection()

        for item in selected:
            if hasattr(item, 'w') and hasattr(item, 'd') and hasattr(item, 'h'):
                new_item = __import__('items.iso_block', fromlist=['IsoBlockItem']).IsoBlockItem(w=item.w, d=item.d, h=item.h, base_color=item.base_color, opacity=item.opacity_val)
            elif hasattr(item, 'length') and hasattr(item, 'thickness'):
                new_item = __import__('items.iso_line', fromlist=['IsoLineItem']).IsoLineItem(length=item.length, thickness=item.thickness, arrow_type=item.arrow_type, arrow_pos=item.arrow_pos, base_color=item.base_color, opacity=item.opacity_val)
                new_item.update_geometry(rot_x=item.rot_x, rot_y=item.rot_y, rot_z=item.rot_z)
            else:
                continue

            # Offset by one grid step in isometric space
            import math
            c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
            offset_sx = -10 * c
            offset_sy = -10 * s

            self.canvas.add_block(new_item, item.pos() + QPointF(offset_sx, offset_sy))
            new_item.setSelected(True)
            new_selection.append(new_item)

    def change_z_index(self, direction):
        selected = self.canvas.scene.selectedItems()
        if selected:
            item = selected[0]
            if direction == "front":
                self.canvas.move_front(item)
            elif direction == "back":
                self.canvas.move_back(item)
            
            if item in self.canvas.block_list:
                self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self.delete_selected()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
            self.duplicate_selected()
        super().keyPressEvent(event)

    def save_to_json(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "保存", "", "JSON Files (*.json)")
        if not filepath:
            return

        data = []
        for block in self.canvas.block_list:
            if hasattr(block, 'to_dict'):
                data.append(block.to_dict())

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "保存しました。")
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"保存に失敗しました: {e}")

    def load_from_json(self):
        from items.iso_block import IsoBlockItem
        from items.iso_line import IsoLineItem

        filepath, _ = QFileDialog.getOpenFileName(self, "読み込み", "", "JSON Files (*.json)")
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Clear current canvas
            for item in list(self.canvas.block_list):
                self.canvas.remove_block(item)

            for item_data in data:
                item_type = item_data.get('type')
                if item_type == 'IsoBlockItem':
                    item = IsoBlockItem.from_dict(item_data)
                    self.canvas.add_block(item, item.pos())
                elif item_type == 'IsoLineItem':
                    item = IsoLineItem.from_dict(item_data)
                    self.canvas.add_block(item, item.pos())

            QMessageBox.information(self, "成功", "読み込みました。")
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"読み込みに失敗しました: {e}")
