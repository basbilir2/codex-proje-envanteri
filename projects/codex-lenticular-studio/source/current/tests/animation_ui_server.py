"""Isolated manual UI smoke server. Never reads or writes production state."""
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from lenticular.pipeline import Studio
from lenticular.studio import Server, handler

with tempfile.TemporaryDirectory(prefix='lenticular-animation-ui-') as temporary:
    root = Path(temporary)
    studio = Studio(root)
    for index,offset in enumerate((0,24)):
        image=Image.new('RGB',(256,192),'black')
        ImageDraw.Draw(image).rectangle((80+offset,70,110+offset,120),fill='white')
        path=root/f'animation-test-{index+1}.png';image.save(path)
        studio.add_photo(path.read_bytes(),path.name)
    server=Server(('127.0.0.1',8876),handler(studio,'animation-ui-check'))
    try:
        server.serve_forever()
    finally:
        studio.close();server.server_close()
