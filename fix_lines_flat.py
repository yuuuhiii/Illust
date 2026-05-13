import re
with open('items/iso_line.py', 'r') as f:
    content = f.read()

# Make flat arrow edges explicitly black while unselected
# We just need to check if vf['is_flat_part'] exists, but we haven't added that flag yet.
# We can just check self.arrow_type == "flat". If it is, the whole line + arrow is flat. So all faces get a black border. This matches the logic we wrote: `if self.arrow_type == "flat" or vf.get('is_flat_part', False): item.setPen(norm_pen)`
