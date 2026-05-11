import re

with open('ui/main_window.py', 'r') as f:
    content = f.read()

# Add imports
content = content.replace(
    'from tools.iso_text_tool import DrawIsoTextTool',
    'from tools.iso_text_tool import DrawIsoTextTool\nfrom tools.iso_polyline_tool import DrawIsoPolylineTool\nfrom items.iso_polyline import IsoPolylineItem'
)

# Add tool button
btn_search = 'btn_draw_text.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoTextTool(self.canvas, self.get_text_props)))\n\n        panel_layout.addWidget(btn_select)'
btn_replace = 'btn_draw_text.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoTextTool(self.canvas, self.get_text_props)))\n\n        btn_draw_polyline = QPushButton("2D折れ線ツール")\n        btn_draw_polyline.clicked.connect(lambda: self.canvas.tool_manager.set_tool(DrawIsoPolylineTool(self.canvas, self.get_polyline_props)))\n\n        panel_layout.addWidget(btn_select)'
content = content.replace(btn_search, btn_replace)

add_btn = 'panel_layout.addWidget(btn_draw_text)'
add_btn_repl = 'panel_layout.addWidget(btn_draw_text)\n        panel_layout.addWidget(btn_draw_polyline)'
content = content.replace(add_btn, add_btn_repl)

# Add stacked widget page for Polyline Props
stack_search = '        panel_layout.addWidget(self.prop_stack)'
stack_repl = '''        # 5. Polyline Props
        w_polyline = QWidget()
        l_polyline = QVBoxLayout(w_polyline)
        l_polyline.setContentsMargins(0, 0, 0, 0)
        self.spin_poly_thickness = create_spinbox_layout("線の太さ:", 1, 100, 2, step=1, layout=l_polyline)
        self.prop_stack.addWidget(w_polyline)

        panel_layout.addWidget(self.prop_stack)'''
content = content.replace(stack_search, stack_repl)

# Update stacked widget indexing connections
index_search = 'btn_draw_text.clicked.connect(lambda: self.prop_stack.setCurrentIndex(4))'
index_repl = 'btn_draw_text.clicked.connect(lambda: self.prop_stack.setCurrentIndex(4))\n        btn_draw_polyline.clicked.connect(lambda: self.prop_stack.setCurrentIndex(5))'
content = content.replace(index_search, index_repl)

# Update sync_ui
sync_search = '        elif selected and isinstance(selected[0], IsoTextItem):'
sync_repl = '''        elif selected and isinstance(selected[0], IsoPolylineItem):
            self.prop_stack.setCurrentIndex(5)
            item = selected[0]
            self.spin_poly_thickness.blockSignals(True); self.spin_poly_thickness.setValue(int(item.thickness)); self.spin_poly_thickness.blockSignals(False)
            self.spin_opacity.blockSignals(True); self.spin_opacity.setValue(item.opacity_val); self.spin_opacity.blockSignals(False)
            self.current_color = item.base_color
            self.update_color_btn_style()
            if item in self.canvas.block_list:
                self.label_z_index.setText(f"現在のレイヤー: {self.canvas.block_list.index(item)}")
        elif selected and isinstance(selected[0], IsoTextItem):'''
content = content.replace(sync_search, sync_repl)

# Update update_geometry
geom_search = '        elif selected and isinstance(selected[0], IsoTextItem):'
geom_repl = '''        elif selected and isinstance(selected[0], IsoPolylineItem):
            item = selected[0]
            item.update_geometry(thickness=self.spin_poly_thickness.value(), base_color=self.current_color, opacity=self.spin_opacity.value())
        elif selected and isinstance(selected[0], IsoTextItem):'''
content = content.replace(geom_search, geom_repl)

# Add getter
prop_search = '    def get_text_props(self):'
prop_repl = '''    def get_polyline_props(self):
        return self.spin_poly_thickness.value(), self.current_color, self.spin_opacity.value()

    def get_text_props(self):'''
content = content.replace(prop_search, prop_repl)

with open('ui/main_window.py', 'w') as f:
    f.write(content)
