"""Same pinned Qwen artifacts on development GPU and local CPU. No network calls."""
import argparse, json, pathlib, subprocess, time
ROOT = pathlib.Path(__file__).resolve().parent
PROMPT = ('Enhance the quality of this exact image. Restore clarity and natural fine details, reduce blur, noise and compression artifacts. '
          'Preserve the entire original scene, subject identity, facial structure, expression, all existing text and letter shapes, '
          'objects, illustration style, colors, geometry, composition and background. Keep every existing element in its original position. '
          'Do not invent text, objects or decorations. Do not crop, change the viewpoint or replace the background. '
          'Produce a clean, sharp and faithful high-quality version of the same image.')

def run(args):
    manifest = json.loads((ROOT / 'models.json').read_text(encoding='utf-8'))
    files = {f['role']:ROOT/'models'/f['name'] for f in manifest['files']}
    for path in [args.input, *files.values()]:
        if not pathlib.Path(path).is_file():
            raise FileNotFoundError(str(path))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pending = args.output.with_name(args.output.stem + '.pending.png')
    command = [str(args.exe), '--diffusion-model',str(files['diffusion']), '--llm',str(files['text']),
               '--llm_vision',str(files['vision']), '--vae',str(files['vae']), '-r',str(args.input), '-p',PROMPT,
               '--model-args','qwen_image_zero_cond_t=true','--cfg-scale','2.5','--sampling-method','euler',
               '--flow-shift','3','--steps',str(args.steps),'--seed','42','--width',str(args.width),
               '--height',str(args.height),'--threads','8','--diffusion-fa','--vae-tiling','-o',str(pending)]
    if args.cpu:
        command += ['--backend','cpu']
    start = time.monotonic()
    record = {'model':manifest['model'],'runtime':manifest['runtime']['revision'],'parameters':{'steps':args.steps,'cfg':2.5,'seed':42,'width':args.width,'height':args.height},'prompt':PROMPT,'status':'running'}
    report = args.output.with_suffix('.json')
    report.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        with args.output.with_suffix('.log').open('w',encoding='utf-8') as log:
            subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=args.timeout)
        if not pending.is_file() or pending.stat().st_size < 100:
            raise RuntimeError('Motor görüntü üretmedi.')
        pending.replace(args.output)
        record['status']='completed'
    except Exception as error:
        record.update(status='failed',error=str(error))
        raise
    finally:
        record['seconds']=round(time.monotonic()-start,2)
        report.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--exe',type=pathlib.Path,required=True)
    p.add_argument('--input',type=pathlib.Path,required=True)
    p.add_argument('--output',type=pathlib.Path,required=True)
    p.add_argument('--width',type=int,required=True)
    p.add_argument('--height',type=int,required=True)
    p.add_argument('--steps',type=int,default=40)
    p.add_argument('--timeout',type=int,default=1800)
    p.add_argument('--cpu',action='store_true')
    args=p.parse_args()
    if min(args.width,args.height)<128 or args.width%16 or args.height%16 or args.width*args.height>1536*1536:
        p.error('Geçersiz çıktı boyutu.')
    run(args)
