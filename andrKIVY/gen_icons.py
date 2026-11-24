from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (512, 512), color=(30, 30, 80))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 200)
except:
    font = ImageFont.load_default()
draw.text((120, 120), 'FM', fill=(100, 200, 255), font=font)
img.save('icon.png')

img2 = Image.new('RGB', (512, 512), color=(30, 30, 80))
img2.save('presplash.png')
print('Created icon.png and presplash.png')
