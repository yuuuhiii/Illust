from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QSpinBox, QLabel, QColorDialog, QCheckBox, QComboBox, QStackedWidget)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QLineEdit
from canvas.view import CanvasView
from tools.select_tool import SelectTool
from tools.iso_tool import DrawIsoBlockTool
from tools.iso_line_tool import DrawIsoLineTool
from tools.iso_shape_tool import DrawIsoShapeTool
from tools.iso_text_tool import DrawIsoTextTool
from items.iso_block import IsoBlockItem
from items.iso_line import IsoLineItem
from items.iso_shape import IsoShapeItem
from items.iso_text import IsoTextItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("汎用3D概念図エディタ (ファイル分割・配列レイヤー版)")
        self.resize(1200, 800)

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

        btn_draw_shape = QPushButton("2D図形ツール")
        btn_draw_shape.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoShapeTool(self.canvas, self.get_shape_props)))

        btn_draw_text = QPushButton("3Dテキストツール")
        btn_draw_text.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoTextTool(self.canvas, self.get_text_props)))

        panel_layout.addWidget(btn_select)
        panel_layout.addWidget(btn_draw_iso)
        panel_layout.addWidget(btn_draw_line)
        panel_layout.addWidget(btn_draw_shape)
        panel_layout.addWidget(btn_draw_text)
        
        self.cb_snap = QCheckBox("グリッドにスナップ")
        self.cb_snap.setChecked(True)
        self.cb_snap.stateChanged.connect(self.toggle_snap)
        panel_layout.addWidget(self.cb_snap)

        panel_layout.addSpacing(20)

        panel_layout.addWidget(QLabel("<b>【プロパティ】</b>"))
        
        def create_spinbox_layout(label, min_v, max_v, default_v, step=10, layout=None):
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(label))
            spin = QSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(default_v)
            spin.setSingleStep(step)
            spin.valueChanged.connect(self.update_selected_item)
            h_layout.addWidget(spin)
            if layout is not None:
                layout.addLayout(h_layout)
            return spin

        self.prop_stack = QStackedWidget()

        # Empty props (for select tool when nothing is selected)
        w_empty = QWidget()
        self.prop_stack.addWidget(w_empty)

        # 1. Block Props
        w_block = QWidget()
        l_block = QVBoxLayout(w_block)
        l_block.setContentsMargins(0, 0, 0, 0)
        self.spin_w = create_spinbox_layout("幅 (W):", 10, 500, 200, layout=l_block)
        self.spin_d = create_spinbox_layout("奥行き (D):", 10, 500, 120, layout=l_block)
        self.spin_h = create_spinbox_layout("高さ (H):", 1, 500, 30, step=1, layout=l_block)
        self.prop_stack.addWidget(w_block)

        # 2. Line/Arrow Props
        w_line = QWidget()
        l_line = QVBoxLayout(w_line)
        l_line.setContentsMargins(0, 0, 0, 0)
        self.spin_length = create_spinbox_layout("長さ (L):", 1, 1000, 100, step=10, layout=l_line)
        self.spin_thickness = create_spinbox_layout("線の太さ:", 1, 100, 10, step=1, layout=l_line)

        h_layout_arrow = QHBoxLayout()
        h_layout_arrow.addWidget(QLabel("矢印の形:"))
        self.combo_arrow_type = QComboBox()
        self.combo_arrow_type.addItem("なし", "none")
        self.combo_arrow_type.addItem("フラット", "flat")
        self.combo_arrow_type.addItem("立体", "cylinder")
        self.combo_arrow_type.currentIndexChanged.connect(self.update_selected_item)
        h_layout_arrow.addWidget(self.combo_arrow_type)
        l_line.addLayout(h_layout_arrow)

        h_layout_pos = QHBoxLayout()
        h_layout_pos.addWidget(QLabel("矢印の位置:"))
        self.combo_arrow_pos = QComboBox()
        self.combo_arrow_pos.addItem("終点", "end")
        self.combo_arrow_pos.addItem("始点", "start")
        self.combo_arrow_pos.addItem("両端", "both")
        self.combo_arrow_pos.currentIndexChanged.connect(self.update_selected_item)
        h_layout_pos.addWidget(self.combo_arrow_pos)
        l_line.addLayout(h_layout_pos)
        self.prop_stack.addWidget(w_line)

        # 3. Shape Props
        w_shape = QWidget()
        l_shape = QVBoxLayout(w_shape)
        l_shape.setContentsMargins(0, 0, 0, 0)
        h_layout_shape = QHBoxLayout()
        h_layout_shape.addWidget(QLabel("図形:"))
        self.combo_shape_type = QComboBox()
        self.combo_shape_type.addItem("四角", "square")
        self.combo_shape_type.addItem("円", "circle")
        self.combo_shape_type.currentIndexChanged.connect(self.update_selected_item)
        h_layout_shape.addWidget(self.combo_shape_type)
        l_shape.addLayout(h_layout_shape)
        self.spin_shape_size = create_spinbox_layout("サイズ:", 10, 1000, 100, step=10, layout=l_shape)
        self.prop_stack.addWidget(w_shape)

        # 4. Text Props
        w_text = QWidget()
        l_text = QVBoxLayout(w_text)
        l_text.setContentsMargins(0, 0, 0, 0)
        self.line_text = QLineEdit("Text")
        self.line_text.textChanged.connect(self.update_selected_item)
        l_text.addWidget(self.line_text)
        self.spin_font_size = create_spinbox_layout("フォントサイズ:", 5, 200, 30, step=5, layout=l_text)

        h_layout_plane = QHBoxLayout()
        h_layout_plane.addWidget(QLabel("配置面:"))
        self.combo_plane = QComboBox()
        self.combo_plane.addItem("床面 (XY)", "XY")
        self.combo_plane.addItem("右壁面 (XZ)", "XZ")
        self.combo_plane.addItem("左壁面 (YZ)", "YZ")
        self.combo_plane.addItem("画面水平 (Screen)", "Screen")
        self.combo_plane.currentIndexChanged.connect(self.update_selected_item)
        h_layout_plane.addWidget(self.combo_plane)
        l_text.addLayout(h_layout_plane)
        self.prop_stack.addWidget(w_text)

        panel_layout.addWidget(self.prop_stack)

        panel_layout.addWidget(QLabel("<b>【共通・回転・色】</b>"))

        self.spin_opacity = create_spinbox_layout("透過率 (%):", 10, 100, 100, layout=panel_layout)

        self.spin_rot_x = create_spinbox_layout("回転 X:", 0, 359, 0, step=5, layout=panel_layout)
        self.spin_rot_x.setWrapping(True)
        self.spin_rot_y = create_spinbox_layout("回転 Y:", 0, 359, 0, step=5, layout=panel_layout)
        self.spin_rot_y.setWrapping(True)
        self.spin_rot_z = create_spinbox_layout("回転 Z:", 0, 359, 0, step=5, layout=panel_layout)
        self.spin_rot_z.setWrapping(True)

        self.current_color = QColor(150, 170, 220)
        self.btn_color = QPushButton("色を選択")
        self.update_color_btn_style()
        self.btn_color.clicked.connect(self.choose_color)
        panel_layout.addWidget(self.btn_color)

        btn_draw_iso.clicked.connect(lambda: self.prop_stack.setCurrentIndex(1))
        btn_draw_line.clicked.connect(lambda: self.prop_stack.setCurrentIndex(2))
        btn_draw_shape.clicked.connect(lambda: self.prop_stack.setCurrentIndex(3))
        btn_draw_text.clicked.connect(lambda: self.prop_stack.setCurrentIndex(4))
        btn_select.clicked.connect(lambda: self.sync_ui_to_selection())
        
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
        IsoShapeItem.SNAP_ENABLED = (state == 2)
        IsoTextItem.SNAP_ENABLED = (state == 2)

    def sync_ui_to_selection(self):
        selected = self.canvas.scene.selectedItems()
        if not selected:
            if isinstance(self.canvas.tool_manager.current_tool, SelectTool):
                self.prop_stack.setCurrentIndex(0)
            return

        if selected and isinstance(selected[0], IsoBlockItem):
            self.prop_stack.setCurrentIndex(1)
            item = selected[0]
            self.spin_w.blockSignals(True); self.spin_w.setValue(item.w); self.spin_w.blockSignals(False)
            self.spin_d.blockSignals(True); self.spin_d.setValue(item.d); self.spin_d.blockSignals(False)
            self.spin_h.blockSignals(True); self.spin_h.setValue(item.h); self.spin_h.blockSignals(False)
            self.spin_opacity.blockSignals(True); self.spin_opacity.setValue(item.opacity_val); self.spin_opacity.blockSignals(False)
            self.spin_rot_x.blockSignals(True); self.spin_rot_x.setValue(int(item.rot_x) % 360); self.spin_rot_x.blockSignals(False)
            self.spin_rot_y.blockSignals(True); self.spin_rot_y.setValue(int(item.rot_y) % 360); self.spin_rot_y.blockSignals(False)
            self.spin_rot_z.blockSignals(True); self.spin_rot_z.setValue(int(item.rot_z) % 360); self.spin_rot_z.blockSignals(False)
            self.current_color = item.base_color
            self.update_color_btn_style()
            
            # 配列内のインデックスを表示
            if item in self.canvas.block_list:
                self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")
        elif selected and isinstance(selected[0], IsoLineItem):
            self.prop_stack.setCurrentIndex(2)
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
        elif selected and isinstance(selected[0], IsoShapeItem):
            self.prop_stack.setCurrentIndex(3)
            item = selected[0]
            self.spin_shape_size.blockSignals(True); self.spin_shape_size.setValue(int(item.size)); self.spin_shape_size.blockSignals(False)
            self.spin_opacity.blockSignals(True); self.spin_opacity.setValue(item.opacity_val); self.spin_opacity.blockSignals(False)
            self.spin_rot_x.blockSignals(True); self.spin_rot_x.setValue(int(item.rot_x) % 360); self.spin_rot_x.blockSignals(False)
            self.spin_rot_y.blockSignals(True); self.spin_rot_y.setValue(int(item.rot_y) % 360); self.spin_rot_y.blockSignals(False)
            self.spin_rot_z.blockSignals(True); self.spin_rot_z.setValue(int(item.rot_z) % 360); self.spin_rot_z.blockSignals(False)

            idx = self.combo_shape_type.findData(item.shape_type)
            if idx >= 0:
                self.combo_shape_type.blockSignals(True); self.combo_shape_type.setCurrentIndex(idx); self.combo_shape_type.blockSignals(False)

            self.current_color = item.base_color
            self.update_color_btn_style()

            if item in self.canvas.block_list:
                self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")
        elif selected and isinstance(selected[0], IsoTextItem):
            self.prop_stack.setCurrentIndex(4)
            item = selected[0]
            self.line_text.blockSignals(True); self.line_text.setText(item.text); self.line_text.blockSignals(False)
            self.spin_font_size.blockSignals(True); self.spin_font_size.setValue(int(item.font_size)); self.spin_font_size.blockSignals(False)
            self.spin_opacity.blockSignals(True); self.spin_opacity.setValue(item.opacity_val); self.spin_opacity.blockSignals(False)

            idx = self.combo_plane.findData(item.plane)
            if idx >= 0:
                self.combo_plane.blockSignals(True); self.combo_plane.setCurrentIndex(idx); self.combo_plane.blockSignals(False)

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
                                 opacity=self.spin_opacity.value(),
                                 rot_x=self.spin_rot_x.value(),
                                 rot_y=self.spin_rot_y.value(),
                                 rot_z=self.spin_rot_z.value())
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
        elif selected and isinstance(selected[0], IsoShapeItem):
            item = selected[0]
            item.update_geometry(shape_type=self.combo_shape_type.currentData(),
                                 size=self.spin_shape_size.value(),
                                 base_color=self.current_color,
                                 opacity=self.spin_opacity.value(),
                                 rot_x=self.spin_rot_x.value(),
                                 rot_y=self.spin_rot_y.value(),
                                 rot_z=self.spin_rot_z.value())
        elif selected and isinstance(selected[0], IsoTextItem):
            item = selected[0]
            item.update_geometry(text=self.line_text.text(),
                                 font_size=self.spin_font_size.value(),
                                 plane=self.combo_plane.currentData(),
                                 base_color=self.current_color,
                                 opacity=self.spin_opacity.value())

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

    def get_shape_props(self):
        return self.combo_shape_type.currentData(), self.spin_shape_size.value(), self.current_color, self.spin_opacity.value(), self.spin_rot_x.value(), self.spin_rot_y.value(), self.spin_rot_z.value()

    def get_text_props(self):
        return self.line_text.text(), self.spin_font_size.value(), self.combo_plane.currentData(), self.current_color, self.spin_opacity.value()

    def delete_selected(self):
        for item in self.canvas.scene.selectedItems():
            self.canvas.remove_block(item)

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
        super().keyPressEvent(event)
