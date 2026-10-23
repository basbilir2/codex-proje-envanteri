from prepare import download, ROOT, MANIFEST
a=MANIFEST['accelerator']
download(f"https://huggingface.co/{a['repo']}/resolve/{a['revision']}/{a['name']}",ROOT/'models'/a['name'],a['size'],a['sha256'])
