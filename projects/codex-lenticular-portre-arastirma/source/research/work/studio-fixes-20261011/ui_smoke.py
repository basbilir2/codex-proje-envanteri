from pathlib import Path
import sys,io,json
import numpy as np
from PIL import Image
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
from lenticular.pipeline import Studio
from lenticular.studio import Server,handler
root=Path(__file__).parent/'ui-test-state'
root.mkdir(exist_ok=True)
studio=Studio(root)
rgb=np.zeros((120,180,3),np.uint8);rgb[:]=[55,80,115];rgb[20:100,50:130]=[195,150,105]
photo=io.BytesIO();Image.fromarray(rgb).save(photo,format='PNG')
asset=studio.add_photo(photo.getvalue(),'Analiz kontrol fotoğrafı.png')
depth=io.BytesIO();np.save(depth,np.tile(np.linspace(.05,.95,180,dtype=np.float32),(120,1)))
studio.add_depth(asset['id'],depth.getvalue(),'depth.npy')
server=Server(('127.0.0.1',0),handler(studio,'scene-analysis-ui-smoke'))
(root/'address.json').write_text(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/?t=scene-analysis-ui-smoke'}))
try:server.serve_forever()
finally:studio.close();server.server_close()
