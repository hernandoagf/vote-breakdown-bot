from PIL import Image, ImageDraw

# create an image
img = Image.new("RGB", (1024, 768), (255, 255, 255))

# get a font
# get a drawing context
draw = ImageDraw.Draw(img)

x, y = (300, 300)
width, height = (150, 15)
primary = (211, 211, 211)
secondary = (15, 15, 15)

# Draw the background
draw.rectangle((x + (height / 2), y, x + width + (height / 2), y + height), fill=secondary, width=10)
draw.ellipse((x + width, y, x + height + width, y + height), fill=secondary)
draw.ellipse((x, y, x + height, y + height), fill=secondary)

# Draw the part of the progress bar that is actually filled
progress = 0.3
width = int(width * progress)
draw.rectangle((x + (height / 2), y, x + width + (height / 2), y + height), fill=primary, width=10)
draw.ellipse((x + width, y, x + height + width, y + height), fill=primary)
draw.ellipse((x, y, x + height, y + height), fill=primary)

img.show()