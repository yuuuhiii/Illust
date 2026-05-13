import re
with open('items/iso_line.py', 'r') as f:
    content = f.read()

content = content.replace("Qt.PenStyle.SolidLine", "Qt.PenStyle.NoPen")

with open('items/iso_line.py', 'w') as f:
    f.write(content)
