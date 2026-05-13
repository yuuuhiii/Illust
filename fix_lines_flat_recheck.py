import re
with open('items/iso_line.py', 'r') as f:
    content = f.read()

# Make sure flat arrow lines inside are not black
# We changed generate_box to have 1 segment
content = content.replace("length_segments = max(1, int(length / 10))", "length_segments = 1")

with open('items/iso_line.py', 'w') as f:
    f.write(content)
