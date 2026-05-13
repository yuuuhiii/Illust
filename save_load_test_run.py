import sys, json, os
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()

# create items
b1 = __import__('items.iso_block', fromlist=['IsoBlockItem']).IsoBlockItem()
l1 = __import__('items.iso_line', fromlist=['IsoLineItem']).IsoLineItem()

window.canvas.add_block(b1, __import__('PyQt6.QtCore', fromlist=['QPointF']).QPointF(10, 20))
window.canvas.add_block(l1, __import__('PyQt6.QtCore', fromlist=['QPointF']).QPointF(30, 40))

# save
data = []
for block in window.canvas.block_list:
    if hasattr(block, 'to_dict'):
        data.append(block.to_dict())

with open('test.json', 'w') as f:
    json.dump(data, f)

# load
with open('test.json', 'r') as f:
    loaded_data = json.load(f)

for item_data in loaded_data:
    item_type = item_data.get('type')
    print(f"Loaded: {item_type} at ({item_data['x']}, {item_data['y']})")

os.remove('test.json')
