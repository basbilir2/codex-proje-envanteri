"""Package reviewed data and the current runtime without unrelated user files."""
import pathlib,zipfile,json
root=pathlib.Path(__file__).resolve().parent;data=root/'user-recovery-v2'
cfg=json.loads((data/'pilot.json').read_text())
rows=json.loads((data/'train.json').read_text())
assert len(rows)*cfg['dataset_repeat']==cfg['planned_optimizer_steps']
with zipfile.ZipFile(data/'cloud-user-training.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in ['cloud-setup.sh','cloud-download.py','seeded-train.py','cloud-pilot.py','cloud-evaluate.py']:
        archive.write(root/name,'recovery-training/'+name)
    for name in ['train.json','validation.json','manifest.json','pilot.json','weights.json','initial-lora.safetensors']:
        archive.write(data/name,'recovery-training/pilot-20261022/'+name)
    for path in sorted((data/'images').iterdir()):
        archive.write(path,'recovery-training/pilot-20261022/images/'+path.name)
print('Reviewed-data bundle:',(data/'cloud-user-training.zip').stat().st_size,'bytes')
