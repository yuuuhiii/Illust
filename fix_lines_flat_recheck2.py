with open('items/iso_line.py', 'r') as f:
    content = f.read()

# Make sure flat arrow lines inside are not black
# The problem with flat arrows having crossing lines is because generate_flat_arrow ALSO draws its inner faces.
# But generate_flat_arrow returns outer boundaries so it shouldn't have lines crossing the plane.
# Let's run the flat screenshot script to see!
