from PyQt6.QtGui import QKeySequence, QShortcut, QColor, QImage, QPainter, QPdfWriter, QPageSize
import json
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QDialog, QDialogButtonBox, QFormLayout,
                             QSpinBox, QLabel, QColorDialog, QCheckBox, QComboBox, QStackedWidget, QScrollArea, QFileDialog)

from PyQt6.QtCore import Qt, QPointF, QRectF

from PyQt6.QtWidgets import QLineEdit
from canvas.view import CanvasView
from tools.select_tool import SelectTool
from tools.iso_tool import DrawIsoBlockTool
from tools.iso_line_tool import DrawIsoLineTool
from tools.iso_shape_tool import DrawIsoShapeTool
from tools.iso_text_tool import DrawIsoTextTool
from tools.iso_polyline_tool import DrawIsoPolylineTool
from items.iso_polyline import IsoPolylineItem
from items.iso_block import IsoBlockItem
from items.iso_line import IsoLineItem
from items.iso_shape import IsoShapeItem
from items.iso_text import IsoTextItem
from items.iso_group import IsoGroupItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("汎用3D概念図エディタ (ファイル分割・配列レイヤー版)")
        self.resize(1200, 800)

        main_layout = QHBoxLayout()
        self.canvas = CanvasView()
        self.canvas.scene.selectionChanged.connect(self.sync_ui_to_selection)

        # History state
        self.history = []
        self.history_index = -1
        self.is_undoing = False

        # Shortcuts
        self.shortcut_copy = QShortcut(QKeySequence.StandardKey.Copy, self)
        self.shortcut_copy.activated.connect(self.copy_item)
        self.shortcut_paste = QShortcut(QKeySequence.StandardKey.Paste, self)
        self.shortcut_paste.activated.connect(self.paste_item)
        self.copied_item = None

        self.shortcut_undo = QShortcut(QKeySequence.StandardKey.Undo, self)
        self.shortcut_undo.activated.connect(self.undo)

        self.shortcut_select_all = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        self.shortcut_select_all.activated.connect(self.select_all)

        self.shortcut_save = QShortcut(QKeySequence.StandardKey.Save, self)
        self.shortcut_save.activated.connect(self.save_file)

        self.shortcut_open = QShortcut(QKeySequence.StandardKey.Open, self)
        self.shortcut_open.activated.connect(self.open_file)

        self.shortcut_export = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut_export.activated.connect(self.export_image)

        self.shortcut_group = QShortcut(QKeySequence("Ctrl+G"), self)
        self.shortcut_group.activated.connect(self.group_items)

        self.shortcut_ungroup = QShortcut(QKeySequence("Ctrl+Shift+G"), self)
        self.shortcut_ungroup.activated.connect(self.ungroup_items)

        self.shortcut_zoom_in = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in.activated.connect(self.zoom_in)
        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.zoom_out)
        self.shortcut_zoom_reset = QShortcut(QKeySequence("Ctrl+0"), self)
        self.shortcut_zoom_reset.activated.connect(self.zoom_reset)

        # Save initial state
        self.save_state()

        panel_layout = QVBoxLayout()

        panel_layout.addWidget(QLabel("<b>【ファイル操作】</b>"))
        h_file = QHBoxLayout()
        btn_open = QPushButton("開く (JSON)")
        btn_open.clicked.connect(self.open_file)
        btn_save = QPushButton("保存 (JSON)")
        btn_save.clicked.connect(self.save_file)
        h_file.addWidget(btn_open)
        h_file.addWidget(btn_save)
        panel_layout.addLayout(h_file)

        self.cb_transparent = QCheckBox("背景を透過する (PNGのみ)")
        panel_layout.addWidget(self.cb_transparent)

        btn_export = QPushButton("画像/PDFエクスポート (Ctrl+E)")
        btn_export.clicked.connect(self.export_image)
        panel_layout.addWidget(btn_export)

        panel_layout.addSpacing(20)

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

        btn_draw_polyline = QPushButton("2D折れ線ツール")
        btn_draw_polyline.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoPolylineTool(self.canvas, self.get_polyline_props)))

        panel_layout.addWidget(btn_select)
        panel_layout.addWidget(btn_draw_iso)
        panel_layout.addWidget(btn_draw_line)
        panel_layout.addWidget(btn_draw_shape)
        panel_layout.addWidget(btn_draw_text)
        panel_layout.addWidget(btn_draw_polyline)
        
        self.cb_snap = QCheckBox("グリッドにスナップ")
        self.cb_snap.setChecked(True)
        self.cb_snap.stateChanged.connect(self.toggle_snap)
        panel_layout.addWidget(self.cb_snap)

        panel_layout.addSpacing(20)

        panel_layout.addWidget(QLabel("<b>【プロパティ】</b>"))
        
        def create_spinbox_layout(label, min_v, max_v, default_v, step=10, layout=None):
            h_layout = QHBoxLayout()
            lbl = QLabel(label)
            h_layout.addWidget(lbl)
            spin = QSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(default_v)
            spin.setSingleStep(step)
            spin.valueChanged.connect(self.update_selected_item)
            h_layout.addWidget(spin)
            if layout is not None:
                layout.addLayout(h_layout)
            return spin, lbl, h_layout

        self.prop_stack = QStackedWidget()

        # Empty props (for select tool when nothing is selected)
        w_empty = QWidget()
        self.prop_stack.addWidget(w_empty)

        # 1. Block Props
        w_block = QWidget()
        l_block = QVBoxLayout(w_block)
        l_block.setContentsMargins(0, 0, 0, 0)

        h_layout_block_type = QHBoxLayout()
        h_layout_block_type.addWidget(QLabel("形状:"))
        self.combo_block_type = QComboBox()
        self.combo_block_type.addItem("直方体", "box")
        self.combo_block_type.addItem("円柱", "cylinder")
        self.combo_block_type.addItem("球体", "sphere")
        self.combo_block_type.currentIndexChanged.connect(self.update_selected_item)
        h_layout_block_type.addWidget(self.combo_block_type)
        l_block.addLayout(h_layout_block_type)

        self.spin_w, self.lbl_w, self.hl_w = create_spinbox_layout("幅 (W):", 10, 500, 200, layout=l_block)
        self.spin_d, self.lbl_d, self.hl_d = create_spinbox_layout("奥行き (D):", 10, 500, 120, layout=l_block)
        self.spin_h, self.lbl_h, self.hl_h = create_spinbox_layout("高さ (H):", 1, 500, 30, step=1, layout=l_block)
        self.prop_stack.addWidget(w_block)

        self.combo_block_type.currentIndexChanged.connect(self.update_block_labels)

        # 2. Line/Arrow Props
        w_line = QWidget()
        l_line = QVBoxLayout(w_line)
        l_line.setContentsMargins(0, 0, 0, 0)
        self.spin_length, _, _ = create_spinbox_layout("長さ (L):", 1, 1000, 100, step=10, layout=l_line)
        self.spin_thickness, _, _ = create_spinbox_layout("線の太さ:", 1, 100, 10, step=1, layout=l_line)

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
        
        self.btn_split_line = QPushButton("貫通用に分割 (前後)")
        self.btn_split_line.clicked.connect(self.split_selected_line)
        l_line.addWidget(self.btn_split_line)

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
        self.spin_shape_size, _, _ = create_spinbox_layout("サイズ:", 10, 1000, 100, step=10, layout=l_shape)
        self.prop_stack.addWidget(w_shape)

        # 4. Text Props
        w_text = QWidget()
        l_text = QVBoxLayout(w_text)
        l_text.setContentsMargins(0, 0, 0, 0)
        self.line_text = QLineEdit("Text")
        self.line_text.textChanged.connect(self.update_selected_item)
        l_text.addWidget(self.line_text)
        self.spin_font_size, _, _ = create_spinbox_layout("フォントサイズ:", 5, 200, 30, step=5, layout=l_text)

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

        # 5. Polyline Props
        w_polyline = QWidget()
        l_polyline = QVBoxLayout(w_polyline)
        l_polyline.setContentsMargins(0, 0, 0, 0)
        self.spin_poly_thickness, _, _ = create_spinbox_layout("線の太さ:", 1, 100, 2, step=1, layout=l_polyline)
        self.prop_stack.addWidget(w_polyline)

        panel_layout.addWidget(self.prop_stack)

        panel_layout.addWidget(QLabel("<b>【共通・回転・色】</b>"))

        self.spin_opacity, _, _ = create_spinbox_layout("透過率 (%):", 10, 100, 100, layout=panel_layout)

        self.spin_rot_x, _, _ = create_spinbox_layout("回転 X:", 0, 359, 0, step=5, layout=panel_layout)
        self.spin_rot_x.setWrapping(True)
        self.spin_rot_y, _, _ = create_spinbox_layout("回転 Y:", 0, 359, 0, step=5, layout=panel_layout)
        self.spin_rot_y.setWrapping(True)
        self.spin_rot_z, _, _ = create_spinbox_layout("回転 Z:", 0, 359, 0, step=5, layout=panel_layout)
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
        btn_draw_polyline.clicked.connect(lambda: self.prop_stack.setCurrentIndex(5))
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
        
        h_group = QHBoxLayout()
        btn_group = QPushButton("グループ化 (Ctrl+G)")
        btn_group.clicked.connect(self.group_items)
        btn_ungroup = QPushButton("グループ解除 (Ctrl+Shift+G)")
        btn_ungroup.clicked.connect(self.ungroup_items)
        h_group.addWidget(btn_group)
        h_group.addWidget(btn_ungroup)
        panel_layout.addLayout(h_group)

        btn_delete = QPushButton("削除 (Del)")
        btn_delete.clicked.connect(self.delete_selected)
        panel_layout.addWidget(btn_delete)

        btn_duplicate = QPushButton("複製 (Ctrl+D)")
        btn_duplicate.clicked.connect(self.duplicate_selected)
        panel_layout.addWidget(btn_duplicate)

        btn_array = QPushButton("配列複製")
        btn_array.clicked.connect(self.show_array_duplicate_dialog)
        panel_layout.addWidget(btn_array)

        panel_widget = QWidget()
        panel_widget.setLayout(panel_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(panel_widget)
        scroll_area.setFixedWidth(300)

        main_layout.addWidget(self.canvas)
        main_layout.addWidget(scroll_area)
        
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def toggle_snap(self, state):
        IsoBlockItem.SNAP_ENABLED = (state == 2)
        IsoLineItem.SNAP_ENABLED = (state == 2)
        IsoShapeItem.SNAP_ENABLED = (state == 2)
        IsoTextItem.SNAP_ENABLED = (state == 2)

    def update_block_labels(self):
        btype = self.combo_block_type.currentData()
        if btype == "box":
            self.lbl_w.setText("幅 (W):")
            self.lbl_w.show(); self.spin_w.show()
            self.lbl_d.setText("奥行き (D):")
            self.lbl_d.show(); self.spin_d.show()
            self.lbl_h.setText("高さ (H):")
            self.lbl_h.show(); self.spin_h.show()
        elif btype == "cylinder":
            self.lbl_w.setText("直径:")
            self.lbl_w.show(); self.spin_w.show()
            self.lbl_d.hide(); self.spin_d.hide()
            self.lbl_h.setText("厚さ/高さ:")
            self.lbl_h.show(); self.spin_h.show()
        elif btype == "sphere":
            self.lbl_w.setText("直径:")
            self.lbl_w.show(); self.spin_w.show()
            self.lbl_d.hide(); self.spin_d.hide()
            self.lbl_h.hide(); self.spin_h.hide()

    def sync_ui_to_selection(self):
        selected = self.canvas.scene.selectedItems()
        if not selected:
            if isinstance(self.canvas.tool_manager.current_tool, SelectTool):
                self.prop_stack.setCurrentIndex(0)
            return

        if selected and isinstance(selected[0], IsoGroupItem):
            self.prop_stack.setCurrentIndex(0)
            item = selected[0]
            if item in self.canvas.block_list:
                self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")
        elif selected and isinstance(selected[0], IsoBlockItem):
            self.prop_stack.setCurrentIndex(1)
            item = selected[0]
            idx = self.combo_block_type.findData(item.block_type)
            if idx >= 0:
                self.combo_block_type.blockSignals(True); self.combo_block_type.setCurrentIndex(idx); self.combo_block_type.blockSignals(False)
                self.update_block_labels()
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
        elif selected and isinstance(selected[0], IsoPolylineItem):
            self.prop_stack.setCurrentIndex(5)
            item = selected[0]
            self.spin_poly_thickness.blockSignals(True); self.spin_poly_thickness.setValue(int(item.thickness)); self.spin_poly_thickness.blockSignals(False)
            self.spin_opacity.blockSignals(True); self.spin_opacity.setValue(item.opacity_val); self.spin_opacity.blockSignals(False)
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
            item.update_geometry(block_type=self.combo_block_type.currentData(),
                                 w=self.spin_w.value(), d=self.spin_d.value(),
                                 h=self.spin_h.value(), base_color=self.current_color,
                                 opacity=self.spin_opacity.value(),
                                 rot_x=self.spin_rot_x.value(),
                                 rot_y=self.spin_rot_y.value(),
                                 rot_z=self.spin_rot_z.value())
        elif selected and isinstance(selected[0], IsoLineItem):
            item = selected[0]
            if getattr(item, 'pierce_peer', None):
                length_val = self.spin_length.value()
                item.logical_length = length_val
                item.pierce_peer.logical_length = length_val
                
                half = max(1, length_val / 2)
                t = self.spin_thickness.value()
                at = self.combo_arrow_type.currentData()
                c = self.current_color
                op = self.spin_opacity.value()
                rx = self.spin_rot_x.value()
                ry = self.spin_rot_y.value()
                rz = self.spin_rot_z.value()
                
                item.update_geometry(length=half, thickness=t, arrow_type=at, base_color=c, opacity=op, rot_x=rx, rot_y=ry, rot_z=rz)
                item.pierce_peer.update_geometry(length=half, thickness=t, arrow_type=at, base_color=c, opacity=op, rot_x=rx, rot_y=ry, rot_z=rz)
                
                # Update positions based on logical_center to keep them rotating around the correct center
                from items.math3d import rotate_3d, project_iso
                center = item.logical_center
                if not center: center = item.pos()
                
                rx_f, ry_f, rz_f = rotate_3d(length_val / 4 * (1 if item.is_front_half else -1), 0, 0, rx, ry, rz)
                sx_f, sy_f = project_iso(rx_f, ry_f, rz_f)
                
                rx_b, ry_b, rz_b = rotate_3d(length_val / 4 * (1 if item.pierce_peer.is_front_half else -1), 0, 0, rx, ry, rz)
                sx_b, sy_b = project_iso(rx_b, ry_b, rz_b)
                
                item._is_syncing = True
                item.pierce_peer._is_syncing = True
                
                item.setPos(center.x() + sx_f, center.y() + sy_f)
                item.pierce_peer.setPos(center.x() + sx_b, center.y() + sy_b)
                
                item._is_syncing = False
                item.pierce_peer._is_syncing = False
            else:
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
        elif selected and isinstance(selected[0], IsoPolylineItem):
            item = selected[0]
            item.update_geometry(thickness=self.spin_poly_thickness.value(), base_color=self.current_color, opacity=self.spin_opacity.value())
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
        return self.combo_block_type.currentData(), self.spin_w.value(), self.spin_d.value(), self.spin_h.value(), self.current_color, self.spin_opacity.value()

    def get_line_props(self):
        return self.spin_thickness.value(), self.combo_arrow_type.currentData(), self.combo_arrow_pos.currentData(), self.current_color, self.spin_opacity.value(), self.spin_rot_x.value(), self.spin_rot_y.value(), self.spin_rot_z.value()

    def get_shape_props(self):
        return self.combo_shape_type.currentData(), self.spin_shape_size.value(), self.current_color, self.spin_opacity.value(), self.spin_rot_x.value(), self.spin_rot_y.value(), self.spin_rot_z.value()

    def get_polyline_props(self):
        return self.spin_poly_thickness.value(), self.current_color, self.spin_opacity.value()

    def get_text_props(self):
        return self.line_text.text(), self.spin_font_size.value(), self.combo_plane.currentData(), self.current_color, self.spin_opacity.value()

    def delete_selected(self):
        for item in self.canvas.scene.selectedItems():
            self.canvas.remove_block(item)

    def split_selected_line(self):
        from items.iso_line import IsoLineItem
        from items.math3d import rotate_3d, project_iso
        from tools.pierce_select_tool import PierceSelectTool
        
        selected = self.canvas.scene.selectedItems()
        if not selected or not isinstance(selected[0], IsoLineItem):
            return
            
        item = selected[0]
        
        if getattr(item, 'pierce_peer', None):
            self.canvas.tool_manager.set_tool(PierceSelectTool(self.canvas, item))
            return
            
        original_length = item.length
        half_length = max(1, original_length / 2)
        
        pos = item.pos()
        rot_x, rot_y, rot_z = item.rot_x, item.rot_y, item.rot_z
        
        back_arrow = "none"
        front_arrow = "none"
        
        if item.arrow_pos == "end":
            front_arrow = "end"
        elif item.arrow_pos == "start":
            back_arrow = "start"
        elif item.arrow_pos == "both":
            back_arrow = "start"
            front_arrow = "end"
            
        back_item = IsoLineItem(length=half_length, thickness=item.thickness, arrow_type=item.arrow_type, arrow_pos=back_arrow, base_color=item.base_color, opacity=item.opacity_val)
        back_item.rot_x, back_item.rot_y, back_item.rot_z = rot_x, rot_y, rot_z
        back_item.is_front_half = False
        back_item.logical_center = QPointF(pos)
        back_item.logical_length = original_length
        back_item.update_geometry()
        
        front_item = IsoLineItem(length=half_length, thickness=item.thickness, arrow_type=item.arrow_type, arrow_pos=front_arrow, base_color=item.base_color, opacity=item.opacity_val)
        front_item.rot_x, front_item.rot_y, front_item.rot_z = rot_x, rot_y, rot_z
        front_item.is_front_half = True
        front_item.logical_center = QPointF(pos)
        front_item.logical_length = original_length
        front_item.update_geometry()
        
        front_item.pierce_peer = back_item
        back_item.pierce_peer = front_item
        
        rx_f, ry_f, rz_f = rotate_3d(original_length / 4, 0, 0, rot_x, rot_y, rot_z)
        sx_f, sy_f = project_iso(rx_f, ry_f, rz_f)
        
        rx_b, ry_b, rz_b = rotate_3d(-original_length / 4, 0, 0, rot_x, rot_y, rot_z)
        sx_b, sy_b = project_iso(rx_b, ry_b, rz_b)
        
        idx = self.canvas.block_list.index(item) if item in self.canvas.block_list else len(self.canvas.block_list)
        
        self.canvas.remove_block(item)
        
        self.canvas.scene.addItem(back_item)
        back_item.setPos(pos.x() + sx_b, pos.y() + sy_b)
        self.canvas.block_list.insert(idx, back_item)
        
        self.canvas.scene.addItem(front_item)
        front_item.setPos(pos.x() + sx_f, pos.y() + sy_f)
        self.canvas.block_list.insert(idx + 1, front_item)
        
        self.canvas.update_z_values()
        
        self.canvas.scene.clearSelection()
        back_item.setSelected(True)
        self.save_state()
        
        self.canvas.tool_manager.set_tool(PierceSelectTool(self.canvas, front_item))

    def duplicate_selected(self):
        selected = self.canvas.scene.selectedItems()
        if not selected:
            return

        new_selection = []
        self.canvas.scene.clearSelection()

        for item in selected:
            if not hasattr(item, 'clone'):
                continue
            new_item = item.clone()

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

        preview_items = []
        base_pos = item.scenePos()

        def update_preview():
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

            # Add the original item to the mix for purely numerical sorting
            preview_data.append({'sx': 0, 'sy': 0, 'depth': 0, 'is_orig': True})
            preview_data.sort(key=lambda d: d['depth'])

            base_z = item.zValue()

            # Find the original item's rank
            orig_index = 0
            for i, d in enumerate(preview_data):
                if d.get('is_orig'):
                    orig_index = i
                    break

            for i, data in enumerate(preview_data):
                if data.get('is_orig'):
                    continue

                p_item = item.clone()
                p_item.setOpacity(item.opacity_val * 0.5)
                p_item.setFlag(p_item.GraphicsItemFlag.ItemIsSelectable, False)
                p_item.setFlag(p_item.GraphicsItemFlag.ItemIsMovable, False)

                self.canvas.scene.addItem(p_item)
                p_item.setPos(base_pos + QPointF(data['sx'], data['sy']))

                # Z index offsets around base_z
                z_offset = (i - orig_index) * 0.001
                p_item.setZValue(base_z + z_offset)

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

            # Add original to the data list to sort everything together
            new_items_data.append({'sx': 0, 'sy': 0, 'depth': 0, 'is_orig': True})
            new_items_data.sort(key=lambda d: d['depth'])

            idx = self.canvas.block_list.index(item) if item in self.canvas.block_list else -1

            if idx >= 0:
                self.canvas.block_list.remove(item)

                for data in new_items_data:
                    if data.get('is_orig'):
                        self.canvas.block_list.insert(idx, item)
                        idx += 1
                    else:
                        new_item = item.clone()
                        self.canvas.scene.addItem(new_item)
                        new_item.setPos(base_pos + QPointF(data['sx'], data['sy']))
                        self.canvas.block_list.insert(idx, new_item)
                        idx += 1

                self.canvas.update_z_values()
            else:
                for data in new_items_data:
                    if not data.get('is_orig'):
                        new_item = item.clone()
                        self.canvas.add_block(new_item, base_pos + QPointF(data['sx'], data['sy']))

    def serialize_scene(self):
        data = []
        for item in self.canvas.block_list:
            if hasattr(item, 'to_dict'):
                data.append(item.to_dict())
        return data

    def _create_item_from_dict(self, item_data):
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import QPointF
        from items.iso_block import IsoBlockItem
        from items.iso_line import IsoLineItem
        from items.iso_shape import IsoShapeItem
        from items.iso_text import IsoTextItem
        from items.iso_polyline import IsoPolylineItem
        from items.iso_group import IsoGroupItem

        item_type = item_data.get('type')
        item = None
        if item_type == 'IsoBlockItem':
            item = IsoBlockItem(block_type=item_data['block_type'], w=item_data['w'], d=item_data['d'], h=item_data['h'],
                                base_color=QColor(item_data['base_color']), opacity=item_data['opacity'])
            item.rot_x = item_data.get('rot_x', 0)
            item.rot_y = item_data.get('rot_y', 0)
            item.rot_z = item_data.get('rot_z', 0)
            item.update_geometry()
        elif item_type == 'IsoLineItem':
            item = IsoLineItem(length=item_data['length'], thickness=item_data['thickness'],
                               arrow_type=item_data['arrow_type'], arrow_pos=item_data['arrow_pos'],
                               base_color=QColor(item_data['base_color']), opacity=item_data['opacity'])
            item.rot_x = item_data.get('rot_x', 0)
            item.rot_y = item_data.get('rot_y', 0)
            item.rot_z = item_data.get('rot_z', 0)
            if 'item_id' in item_data: item.item_id = item_data['item_id']
            if 'pierce_peer_id' in item_data:
                item._pierce_peer_id = item_data['pierce_peer_id']
                item.is_front_half = item_data.get('is_front_half', False)
                item.logical_length = item_data.get('logical_length', item.length)
                lc = item_data.get('logical_center')
                if lc: item.logical_center = QPointF(lc['x'], lc['y'])
            item.update_geometry()
        elif item_type == 'IsoShapeItem':
            item = IsoShapeItem(shape_type=item_data['shape_type'], size=item_data['size'],
                                base_color=QColor(item_data['base_color']), opacity=item_data['opacity'])
            item.rot_x = item_data.get('rot_x', 0)
            item.rot_y = item_data.get('rot_y', 0)
            item.rot_z = item_data.get('rot_z', 0)
            item.update_geometry()
        elif item_type == 'IsoTextItem':
            item = IsoTextItem(text=item_data['text'], font_size=item_data['font_size'], plane=item_data['plane'],
                               base_color=QColor(item_data['base_color']), opacity=item_data['opacity'])
        elif item_type == 'IsoPolylineItem':
            pts = [QPointF(p['x'], p['y']) for p in item_data['points']]
            item = IsoPolylineItem(points=pts, thickness=item_data['thickness'],
                                   base_color=QColor(item_data['base_color']), opacity=item_data['opacity'])
        elif item_type == 'IsoGroupItem':
            item = IsoGroupItem()
            for child_data in item_data.get('children', []):
                child_item = self._create_item_from_dict(child_data)
                if child_item:
                    item.addToGroup(child_item)
                    child_item.setPos(child_data['pos']['x'], child_data['pos']['y'])
                    child_item.setZValue(child_data.get('zValue', 0))

        return item

    def load_scene(self, data):
        self.canvas.scene.clear()
        self.canvas.block_list.clear()
        for item_data in data:
            item = self._create_item_from_dict(item_data)
            if item:
                self.canvas.scene.addItem(item)
                item.setPos(item_data['pos']['x'], item_data['pos']['y'])
                item.setZValue(item_data.get('zValue', 0))
                self.canvas.block_list.append(item)

        # Link pierce peers
        from items.iso_line import IsoLineItem
        from items.iso_group import IsoGroupItem
        all_lines = []
        def collect_lines(group_or_list):
            for i in group_or_list:
                if isinstance(i, IsoLineItem):
                    all_lines.append(i)
                elif isinstance(i, IsoGroupItem):
                    collect_lines(i.childItems())
        collect_lines(self.canvas.block_list)
        id_to_item = {i.item_id: i for i in all_lines}
        for line in all_lines:
            if hasattr(line, '_pierce_peer_id') and line._pierce_peer_id in id_to_item:
                line.pierce_peer = id_to_item[line._pierce_peer_id]
                del line._pierce_peer_id

    def save_state(self):
        if self.is_undoing: return
        data = self.serialize_scene()

        # If we are not at the end of history, truncate it
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        # Avoid saving identical consecutive states
        if self.history and self.history[-1] == data:
            return

        self.history.append(data)
        self.history_index = len(self.history) - 1

    def undo(self):
        if self.history_index > 0:
            self.is_undoing = True
            self.history_index -= 1
            data = self.history[self.history_index]
            self.load_scene(data)
            self.is_undoing = False

    def select_all(self):
        for item in self.canvas.scene.items():
            item.setSelected(True)

    def save_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, '保存', '', 'JSON Files (*.json)')
        if fname:
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(self.serialize_scene(), f, ensure_ascii=False, indent=2)

    def open_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, '開く', '', 'JSON Files (*.json)')
        if fname:
            with open(fname, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.load_scene(data)
            self.save_state()

    # Override key release to catch deletes
    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self.save_state()

    def group_items(self):
        selected = self.canvas.scene.selectedItems()
        if len(selected) < 2:
            return

        group = IsoGroupItem()
        import math
        cx = sum(item.pos().x() for item in selected) / len(selected)
        cy = sum(item.pos().y() for item in selected) / len(selected)
        group_pos = QPointF(cx, cy)
        
        self.canvas.scene.addItem(group)
        group.setPos(group_pos)
        
        min_z_idx = len(self.canvas.block_list)
        for item in selected:
            if item in self.canvas.block_list:
                min_z_idx = min(min_z_idx, self.canvas.block_list.index(item))
                self.canvas.block_list.remove(item)
            
            local_pos = item.pos() - group_pos
            group.addToGroup(item)
            item.setPos(local_pos)

        if min_z_idx <= len(self.canvas.block_list):
            self.canvas.block_list.insert(min_z_idx, group)
        else:
            self.canvas.block_list.append(group)
        
        self.canvas.update_z_values()
        self.canvas.scene.clearSelection()
        group.setSelected(True)
        self.save_state()

    def ungroup_items(self):
        selected = self.canvas.scene.selectedItems()
        changed = False
        for item in selected:
            if isinstance(item, IsoGroupItem):
                group = item
                idx = self.canvas.block_list.index(group) if group in self.canvas.block_list else len(self.canvas.block_list)
                if group in self.canvas.block_list:
                    self.canvas.block_list.remove(group)
                
                children = list(group.childItems())
                for child in children:
                    scene_pos = child.scenePos()
                    group.removeFromGroup(child)
                    self.canvas.scene.addItem(child)
                    child.setPos(scene_pos)
                    self.canvas.block_list.insert(idx, child)
                    idx += 1
                    child.setSelected(True)
                
                self.canvas.scene.removeItem(group)
                group.setSelected(False)
                changed = True
                
        if changed:
            self.canvas.update_z_values()
            self.save_state()

    def zoom_in(self):
        self.canvas.scale(1.15, 1.15)

    def zoom_out(self):
        self.canvas.scale(1 / 1.15, 1 / 1.15)

    def zoom_reset(self):
        self.canvas.resetTransform()

    def export_image(self):
        filters = "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf)"
        fname, selected_filter = QFileDialog.getSaveFileName(self, 'エクスポート', '', filters)
        if not fname:
            return

        # Calculate bounding rect of all items
        rect = self.canvas.scene.itemsBoundingRect()
        if rect.isEmpty():
            rect = QRectF(0, 0, 800, 600)
        else:
            # Add some margin
            margin = 20
            rect.adjust(-margin, -margin, margin, margin)

        is_png = fname.lower().endswith('.png') or 'PNG' in selected_filter
        is_pdf = fname.lower().endswith('.pdf') or 'PDF' in selected_filter
        
        transparent = self.cb_transparent.isChecked() and is_png

        # Clear selection handles so they don't appear in the image
        self.canvas.scene.clearSelection() 

        if is_pdf:
            writer = QPdfWriter(fname)
            writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            painter = QPainter(writer)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # For PDF, map the logical rect to the page layout
            page_rect = writer.pageLayout().fullRectPixels(writer.resolution())
            # Scale rect to fit page_rect while maintaining aspect ratio
            scale = min(page_rect.width() / rect.width(), page_rect.height() / rect.height())
            
            painter.scale(scale, scale)
            painter.translate(-rect.left(), -rect.top())
            self.canvas.scene.render(painter, target=QRectF(rect), source=rect)
            painter.end()
        else:
            width = max(1, int(rect.width()))
            height = max(1, int(rect.height()))
            # Limit maximum size to prevent memory errors
            width = min(width, 8000)
            height = min(height, 8000)

            image = QImage(width, height, QImage.Format.Format_ARGB32)
            if transparent:
                image.fill(Qt.GlobalColor.transparent)
            else:
                image.fill(Qt.GlobalColor.white)

            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.canvas.scene.render(painter, target=QRectF(0, 0, width, height), source=rect)
            painter.end()

            image.save(fname)
