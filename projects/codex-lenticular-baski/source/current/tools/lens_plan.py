"""Calculate new lens trials from a reviewed depth cache; never render or infer AI depth."""
import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
APP = Path(r"C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1")
sys.path.insert(0, str(APP))
from lenticular.analyzer import analyze_scene, save_analysis
from lenticular.depth import MODEL_REVISION
from lenticular.pipeline import RENDER_ENGINE_VERSION, render_settings
from lenticular.printing import validate as print_settings

VERSION = 1
DEPTH_FIELDS = ('process_res', 'depth_normalization', 'detail_enabled', 'detail_strength', 'surface_strength')
ENGINE_FILES = ('pipeline.py', 'analyzer.py', 'repair.py', 'optics.py', 'printing.py', 'geometry.py', 'depth.py', 'detail_depth.py', 'runner.py')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lpi', nargs='+', type=float, required=True)
    parser.add_argument('--ppi', type=float, default=1200)
    parser.add_argument('--max-width-mm', type=float, default=130)
    args = parser.parse_args()
    lenses = sorted(set(args.lpi))
    if any(not math.isfinite(v) or not 1 <= v <= 300 for v in lenses):
        raise ValueError('Lens LPI must be finite and between 1 and 300.')
    if not math.isfinite(args.ppi) or not 30 <= args.ppi <= 4800 or not math.isfinite(args.max_width_mm) or not 5 <= args.max_width_mm <= 3000:
        raise ValueError('Invalid raster PPI or panel width.')
    baseline = read(ROOT / 'vd-three-variant-settings.json')
    cache = read(ROOT / 'knowledge/depth-cache.json')
    source = Path(baseline['source'])
    depth_path = Path(cache['path'])
    depth_recipe = {k: baseline['variants'][0]['render'][k] for k in DEPTH_FIELDS}
    if cache['source_sha256'] != sha(source) or cache['depth_sha256'] != sha(depth_path) or cache['depth_recipe'] != depth_recipe or cache['model_revision'] != MODEL_REVISION:
        raise ValueError('Reviewed depth cache no longer matches source/model/settings. Do not silently reuse or overwrite it.')
    engine_hashes = {name: sha(APP / 'lenticular' / name) for name in ENGINE_FILES}
    if engine_hashes['depth.py'] != cache['depth_engine_hashes']['depth.py'] or engine_hashes['detail_depth.py'] != cache['depth_engine_hashes']['detail_depth.py']:
        raise ValueError('Depth engines changed; review depth-cache provenance before reuse.')
    identity = dict(planner_version=VERSION, baseline_sha256=sha(ROOT/'vd-three-variant-settings.json'), source_sha256=cache['source_sha256'], depth_sha256=cache['depth_sha256'], engine_hashes=engine_hashes, lpi=lenses, ppi=args.ppi, max_width_mm=args.max_width_mm)
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    folder = ROOT / 'plans' / ('vd-' + '-'.join(f'{v:g}' for v in lenses) + f'-{args.ppi:g}ppi-' + key[:8])
    if (folder / 'plan.json').is_file():
        existing = read(folder / 'plan.json')
        if existing['input_identity'] == identity and all((folder / item['analysis_path']).is_file() for item in existing['variants']):
            print(json.dumps({'cached_plan': str(folder/'plan.json'), 'status': 'existing plan reused; no calculation or render repeated'}))
            return
    photo = ImageOps.exif_transpose(Image.open(source)).convert('RGB')
    depth = np.load(depth_path, allow_pickle=False)
    if depth.shape != (photo.height, photo.width) or not np.isfinite(depth).all() or depth.min() < 0 or depth.max() > 1:
        raise ValueError('Invalid reviewed depth array.')
    pixel_width = math.floor(args.max_width_mm * args.ppi / 25.4)
    pixel_height = round(pixel_width * photo.height / photo.width)
    width_mm, height_mm = pixel_width * 25.4 / args.ppi, pixel_height * 25.4 / args.ppi
    plan = dict(schema_version=1, created_utc=datetime.now(timezone.utc).isoformat(), input_identity=identity, source=str(source), app_root=str(APP), depth_cache=str(depth_path), status='analyzer calculated; not rendered or physically verified', render_engine_version=RENDER_ENGINE_VERSION, rationale='Preserve baseline selected-camera motion in lenticule units at the same print scale. Nr=Ne; each channel is a distinct view. Two raster pixels per channel is a planning heuristic, not measured lens capacity.', panel_size_px=[pixel_width, pixel_height], panel_size_mm=[width_mm, height_mm], shared_depth_recipe=depth_recipe, variants=[], sheets=[])
    rows = []
    for lpi in lenses:
        ne = min(10, math.floor(args.ppi / lpi / 2))
        if ne < 2:
            raise ValueError('Requested raster does not meet the two-pixel heuristic for at least two channels.')
        sheet_items = []
        for i, old in enumerate(baseline['variants']):
            code = 'ABC'[i]
            old_print, old_render = old['print'], old['render']
            factor = ((ne-1)/(old_print['ne']-1) * old_print['effective_lpi']/lpi * old_print['width_mm']/width_mm)
            angle = math.degrees(2*math.atan(math.tan(math.radians(old_render['angle_deg'])/2)*factor))
            r = render_settings(old_render | dict(nr=ne, angle_deg=angle, front_parallax_percent=old_render['front_parallax_percent']*factor, back_parallax_percent=old_render['back_parallax_percent']*factor, max_parallax_percent=max(.1, old_render['max_parallax_percent']*factor)))
            p = print_settings(old_print | dict(width_mm=width_mm, height_mm=height_mm, ppi=args.ppi, nominal_lpi=lpi, effective_lpi=lpi, ne=ne, phase=0, pitch_verified=False, raster_ppi_verified=False, lens_angle_verified=False, crosstalk_matrix=None, compensation=0))
            report, diagnostic = analyze_scene(photo, depth, r, p)
            relative = Path(f'{lpi:g}lpi/analysis_{code}')
            save_analysis(folder / relative, report, diagnostic)
            selected = report['source_indices']
            if len(set(selected)) != ne or report['edits']['clipped_fraction'] != 0:
                raise ValueError('Repeated channels or clipped depth: plan cannot be delivered.')
            reference = r['reference_point']
            render_dir = ROOT / f'vd_{lpi:g}lpi' / f'render_{code}'
            item = dict(lpi=lpi, code=code, name=old['name'], render=r, print=p, scale_from_baseline=factor, sheet_x_px=i*pixel_width, sheet_phase=(i*pixel_width*lpi/args.ppi)%1, analysis_path=str(relative/'scene-analysis.json'), output_root=str(render_dir.parent), render_output=str(render_dir), render_cache_identity=dict(source_sha256=cache['source_sha256'], depth_sha256=cache['depth_sha256'], render=r, engine_hashes=engine_hashes), metrics=dict(effective_angle_deg=report['parallax']['effective_angle_deg'], max_parallax_percent=report['parallax']['max_parallax_percent'], step_p95_lenticules=report['depth_sampling']['adjacent_step_lenticules_p95'], step_max_lenticules=report['depth_sampling']['adjacent_step_lenticules_max'], pixels_per_channel=report['sampling_budget']['pixels_per_channel'], reference_point=reference), physical_3d_verified=False)
            plan['variants'].append(item)
            sheet_items.append(dict(code=code, x_px=i*pixel_width, phase=item['sheet_phase']))
            rows.append(f"| {lpi:g} | {code} | {ne} | {angle:.3f} | {r['front_parallax_percent']:.3f} | {r['back_parallax_percent']:.3f} | {item['metrics']['step_p95_lenticules']:.3f} | {args.ppi/lpi/ne:.3f} |")
        plan['sheets'].append(dict(lpi=lpi, output_root=str(ROOT/f'vd_{lpi:g}lpi'), image_size_px=[3*pixel_width,pixel_height], image_size_mm=[3*width_mm,height_mm], label_strip_mm=6, panels=sheet_items, separate_lens_from_other_lpi=True))
    save(folder / 'plan.json', plan)
    table = '\n'.join(['# Yeniden hesaplanan lens denemeleri', '', '| LPI | Varyant | Nr=Ne | Açı ° | Ön % | Arka % | Adım p95 lens | Piksel/kanal |', '|---|---|---|---|---|---|---|---|', *rows, '', 'Hesaplama tamamlandı. Blender, AI çıkarımı ve baskı üretimi başlatılmadı. LPI değerleri nominaldir; gerçek pitch, lens açısı ve RIP ayrımı ölçülmüş değildir.'])
    (folder/'calculation.md').write_text(table, encoding='utf-8')
    save(ROOT/'knowledge/current-task.json', dict(plan=str(folder/'plan.json'), status=plan['status'], physical_3d_verified=False))
    print(json.dumps({'plan':str(folder/'plan.json'), 'calculation':str(folder/'calculation.md'), 'variants':[{k:v[k] for k in ('lpi','code','metrics')} for v in plan['variants']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
