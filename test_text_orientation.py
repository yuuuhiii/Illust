from items.math3d import project_iso

print("X axis (1, 0, 0):", project_iso(1, 0, 0)) # Should be right, down
print("Y axis (0, 1, 0):", project_iso(0, 1, 0)) # Should be left, down
print("Z axis (0, 0, 1):", project_iso(0, 0, 1)) # Should be up

# Right wall is XZ plane (X goes down-right, Z goes up)
# Left wall is YZ plane (Y goes down-left, Z goes up)

# Floor plane is XY plane (X goes down-right, Y goes down-left)
