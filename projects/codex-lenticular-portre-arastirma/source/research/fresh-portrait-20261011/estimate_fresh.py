from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
from lenticular.depth import estimate
WORK=Path(__file__).resolve().parent
SOURCE=Path(r'C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg')
photo,depth=estimate(SOURCE,WORK/'inference',process_res=1008)
im=Image.open(photo).convert('RGB')
d=np.load(depth,allow_pickle=False)
panel=Image.new('RGB',(1120,940),'#202833');draw=ImageDraw.Draw(panel)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
for col,(label,pic) in enumerate([('Kaynak fotoğraf',im),('Yeni derinlik · 1008',Image.fromarray(np.rint(d*255).astype(np.uint8)).convert('RGB'))]):
    pic=pic.copy();pic.thumbnail((540,894))
    panel.paste(pic,(col*560,40));draw.text((col*560+10,7),label,font=font,fill='white')
panel.save(WORK/'fresh-depth-review.jpg',quality=96)
print(json.dumps(dict(source_size=im.size,nose=float(d[432,958]),range=[float(d.min()),float(d.max())],output=str(WORK/'fresh-depth-review.jpg'))),flush=True)
