from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QSpinBox, QLabel, QColorDialog, QCheckBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from canvas.view import CanvasView
from tools.select_tool import SelectTool
from tools.iso_tool import DrawIsoBlockTool
from items.iso_block import IsoBlockItem

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

        panel_layout.addWidget(btn_select)
        panel_layout.addWidget(btn_draw_iso)
        
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
        else:
            self.label_z_index.setText("現在のレイヤー: -")

    def update_selected_item(self):
        selected = self.canvas.scene.selectedItems()
        if selected and isinstance(selected[0], IsoBlockItem):
            item = selected[0]
            item.update_geometry(w=self.spin_w.value(), d=self.spin_d.value(), 
                                 h=self.spin_h.value(), base_color=self.current_color,
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

    def delete_selected(self):
        for item in self.canvas.scene.selectedItems():
            self.canvas.remove_block(item) # 配列からも削除

    def change_z_index(self, direction):
        selected = self.canvas.scene.selectedItems()
        if selected and isinstance(selected[0], IsoBlockItem):
            item = selected[0]
            if direction == "front":
                self.canvas.move_front(item)
            elif direction == "back":
                self.canvas.move_back(item)
            
            # 移動後のインデックスを更新
            self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self.delete_selected()
        super().keyPressEvent(event)