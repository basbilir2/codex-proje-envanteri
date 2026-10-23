"""Download only pinned model artifacts; resume interrupted transfers and verify SHA256."""
import concurrent.futures, hashlib, json, pathlib, sys, time, urllib.request, zipfile
ROOT = pathlib.Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / 'models.json').read_text(encoding='utf-8'))

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def download(url, target, size=None, checksum=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt = target.with_suffix(target.suffix + '.verified.json')
    if target.exists() and receipt.exists():
        info = json.loads(receipt.read_text())
        stat = target.stat()
        if info.get('sha256') == checksum and info.get('size') == stat.st_size and info.get('mtime_ns') == stat.st_mtime_ns:
            return
    if target.exists() and checksum and digest(target) == checksum:
        pass
    else:
        part = target.with_suffix(target.suffix + '.part')
        failures = 0
        while True:
            offset = part.stat().st_size if part.exists() else 0
            if size and offset == size:
                break
            end = min(offset + 64 * 1024 * 1024, size) - 1 if size else None
            range_header = {'Range':f'bytes={offset}-{end}'} if size else ({'Range':f'bytes={offset}-'} if offset else {})
            request = urllib.request.Request(url, headers={'User-Agent':'Netlestirme/0.1', **range_header})
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    if size and response.status != 206:
                        raise RuntimeError('Sunucu parcali indirmeyi kabul etmedi.')
                    resume = offset and response.status == 206
                    with part.open('ab' if resume else 'wb') as output:
                        for block in iter(lambda: response.read(1024 * 1024), b''):
                            output.write(block)
                failures = 0
                if not size:
                    break
            except Exception:
                failures += 1
                if failures == 3:
                    raise
                time.sleep(2)
        if size and part.stat().st_size != size:
            raise RuntimeError(f'Boyut doğrulanamadı: {target.name}')
        if checksum and digest(part) != checksum:
            raise RuntimeError(f'SHA256 doğrulanamadı: {target.name}')
        part.replace(target)
    stat = target.stat()
    receipt.write_text(json.dumps({'sha256':checksum or digest(target),'size':stat.st_size,'mtime_ns':stat.st_mtime_ns}), encoding='utf-8')
    print('HAZIR', target.name, flush=True)

def model_file(item):
    url = f"https://huggingface.co/{item['repo']}/resolve/{item['revision']}/{item['path']}?download=true"
    download(url, ROOT / 'models' / item['name'], item['size'], item['sha256'])

if __name__ == '__main__':
    if sys.platform == 'win32':
        archive = ROOT / 'runtime.zip'
        download(MANIFEST['runtime']['windows_cpu'], archive)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(ROOT / 'runtime')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(model_file, MANIFEST['files']))
    print('MODEL_DOSYALARI_DOGRULANDI', flush=True)
