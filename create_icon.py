from PIL import Image, ImageDraw, ImageFont
import os

# Create assets folder
if not os.path.exists('assets'):
    os.makedirs('assets')

# Create icon (512x512)
icon = Image.new('RGB', (512, 512), color='#0A0A0F')
draw = ImageDraw.Draw(icon)

# Draw simple icon - gold circle with "FI" text
draw.ellipse([100, 100, 412, 412], fill='#E6B800', outline='#B38F00', width=5)

# Add text (use default font)
try:
    font = ImageFont.truetype("arial.ttf", 120)
except:
    font = ImageFont.load_default()

# Center text
text = "FI"
bbox = draw.textbbox((0, 0), text, font=font)
text_x = (512 - (bbox[2] - bbox[0])) // 2
text_y = (512 - (bbox[3] - bbox[1])) // 2 - 20
draw.text((text_x, text_y), text, fill='#0A0A0F', font=font)

icon.save('assets/icon.png')
print("Icon created: assets/icon.png")

# Create splash screen (1080x1920)
splash = Image.new('RGB', (1080, 1920), color='#0A0A0F')
draw = ImageDraw.Draw(splash)

# Draw gold line
draw.rectangle([200, 900, 880, 920], fill='#E6B800')

# Add title
try:
    font_title = ImageFont.truetype("arial.ttf", 80)
    font_sub = ImageFont.truetype("arial.ttf", 40)
except:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

title = "FADAKKA INDEX"
bbox = draw.textbbox((0, 0), title, font=font_title)
title_x = (1080 - (bbox[2] - bbox[0])) // 2
draw.text((title_x, 800), title, fill='#E6B800', font=font_title)

sub = "buy cheap, sell high!"
bbox = draw.textbbox((0, 0), sub, font=font_sub)
sub_x = (1080 - (bbox[2] - bbox[0])) // 2
draw.text((sub_x, 950), sub, fill='#666666', font=font_sub)

splash.save('assets/splash.png')
print("Splash created: assets/splash.png")