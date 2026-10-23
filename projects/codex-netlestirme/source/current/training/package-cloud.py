"""Package only this pilot's inputs and controls. No model execution."""
import json
import pathlib
import shutil
import zipfile

root = pathlib.Path(__file__).resolve().parent
data = root / 'pilot-20261022'
shutil.copyfile(root.parent / 'app/inputs/mavi.jpeg', data / 'holdout-mavi.jpeg')
cfg = json.loads((data / 'pilot.json').read_text())
train = json.loads((data / 'train.json').read_text())
validation = json.loads((data / 'validation.json').read_text())
assert len(train) * cfg['dataset_repeat'] * cfg['epochs'] == cfg['planned_optimizer_steps']
assert not ({r['image'] for r in train} & {r['image'] for r in validation})
assert all('mavi' not in str(r).lower() for r in train)
files = [root / p for p in ['cloud-setup.sh', 'cloud-download.py', 'seeded-train.py', 'cloud-pilot.py', 'cloud-evaluate.py']]
files += [data / p for p in ['pilot.json', 'weights.json', 'manifest.json', 'train.json', 'validation.json', 'holdout-mavi.jpeg']]
files += sorted((data / 'images').glob('*.png'))
with zipfile.ZipFile(data / 'cloud-pilot.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, 'recovery-training/' + path.relative_to(root).as_posix())
print('Pilot bundle ready:', (data / 'cloud-pilot.zip').stat().st_size, 'bytes; planned steps:', cfg['planned_optimizer_steps'])
