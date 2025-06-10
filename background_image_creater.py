import numpy as np
from PIL import Image

# Image dimensions
height = 1080
width = 1920

# Create a blank image (all zeros) with 3 color channels (RGB)
image = np.zeros((height, width, 3), dtype=np.uint8)

# Set the left part (columns 0 to 755) to red: [255, 0, 0]
image[:756, :] = [255, 150, 150]

# Set the right part (columns 756 to 1919) to green: [0, 255, 0]
image[756:, :] = [150, 255, 150]

# Convert to image and save or show
img = Image.fromarray(image)
img.save("red_green_split.png")  # or use img.show() to preview
