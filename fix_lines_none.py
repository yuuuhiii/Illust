import re
with open('items/iso_line.py', 'r') as f:
    content = f.read()

# I notice if arrow_type is "none", it's currently a cylinder but will use brush_color as pen border. This is what we want! (gradient styling without black borders).
