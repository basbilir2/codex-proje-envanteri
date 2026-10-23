from prepare import download, ROOT
REV='962e67969ec6acec9c19fab76acee4f5e22e990c'
REPO='studioludens/birefnet-lite-512'
for name,size,sha in [
    ('config.json',None,None),('preprocessor_config.json',None,None),
    ('onnx/model.onnx',191877254,'1cb0fb360dadd15af77c639085d77a9df67db0c64315560c3de005f676345ac2')]:
    download(f'https://huggingface.co/{REPO}/resolve/{REV}/{name}',ROOT/'background-model'/REPO/name,size,sha)
