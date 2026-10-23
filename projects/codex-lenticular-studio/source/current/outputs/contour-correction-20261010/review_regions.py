from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
OLD=ROOT/'outputs/surface-upgrade-20261009-220345/native-portrait-final';NEW=OUT/'coupled'
right=NEW/('views/view_0011.png' if (NEW/'views/view_0011.png').exists() else 'views/view_0001.png')
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',17)
boxes=[(590,60,990,440),(0,1550,400,1930),(1400,540,1800,920),(0,620,400,1000)]
items=[('Kaynak',OLD/'source.png'),('Merkez',NEW/'center.png'),('Sol uç',NEW/'views/view_0000.png'),('Sağ uç',right)]
canvas=Image.new('RGB',(1600,1640),'#222933');d=ImageDraw.Draw(canvas)
for row,box in enumerate(boxes):
    for col,(label,p) in enumerate(items):
        with Image.open(p) as im:canvas.paste(im.crop(box).convert('RGB'),(col*400,row*410+30))
        d.text((col*400+6,row*410+4),label,font=font,fill='white')
canvas.save(OUT/'regional-review.png')
