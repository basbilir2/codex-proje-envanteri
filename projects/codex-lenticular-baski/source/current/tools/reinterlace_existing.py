"""Change only LPI using a verified portrait's existing camera frames."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0, str(APP))
from lenticular import printing


def read(path):
    return Path(path).read_text(encoding='utf-8')


def load(path):
    return json.loads(read(path))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--lpi', type=float, nargs='+', required=True)
    args = parser.parse_args()
    reference = args.reference.resolve()
    pointer = load(reference/'render-current.json')
    render = Path(pointer['folder'])
    job = load(render/'job.json')
    baseline = load(reference/'print/print-report.json')
    scene = load(reference/'prepared/scene-plan.json')
    assert digest(render/'job.json') == baseline['source_job_sha256']
    assert job['config'] == pointer['identity']['config']
    assert digest(reference/'prepared/depth.npy') == pointer['identity']['depth_sha256'] == scene['depth_sha256']
    assert digest(render/'depth_proximity.npy') == scene['depth_sha256']
    source = Path(job['source_inputs']['photo'])
    assert digest(source) == job['source_inputs']['photo_sha256']
    finalization = load(render/'alpha-finalization.json')
    frame_hashes = {record['file']: record['after_sha256'] for record in finalization['files'] if record['file'].startswith('view_')}
    assert len(frame_hashes) == baseline['nr'] == baseline['ne'] == 6
    for name, expected in frame_hashes.items():
        assert digest(render/'views'/name) == expected
    args.output.mkdir(parents=True, exist_ok=True)
    identity = dict(render_folder=str(render), render_job_sha256=baseline['source_job_sha256'], depth_sha256=scene['depth_sha256'], camera_config=job['config'], frame_sha256=frame_hashes, source_indices=baseline['source_indices'], printing_engine_sha256=digest(APP/'lenticular/printing.py'), frames_engine_sha256=digest(APP/'lenticular/frames.py'))
    # These optional calibration sheets are not requested for this interlace-only
    # job. Suppress their side effects in this process; core source stays intact.
    original_pitch, original_registration = printing.pitch_test, printing.registration
    printing.pitch_test = lambda *a, **k: None
    printing.registration = lambda *a, **k: None
    records = []
    try:
        for lpi in args.lpi:
            settings = printing.validate(baseline['settings'] | dict(nominal_lpi=lpi, effective_lpi=lpi))
            changed = {key for key in settings if settings[key] != baseline['settings'][key]}
            assert changed <= {'nominal_lpi', 'effective_lpi'}
            folder = args.output/(f'{lpi:g}'.replace('.', '_')+'lpi')
            manifest = identity | dict(settings=settings)
            if (folder/'reuse-manifest.json').is_file() and load(folder/'reuse-manifest.json') == manifest:
                report = load(folder/'print-report.json')
                assert (folder/'interlaced.tif').is_file()
                print(f'{lpi:g} LPI: existing matching print reused.', flush=True)
            else:
                report = printing.encode(render, folder, settings)
                assert report['source_indices'] == baseline['source_indices']
                assert report['distinct_source_images'] == baseline['distinct_source_images'] == 6
                assert report['raster_integrity']['metadata_passed'] and report['raster_integrity']['sampled_pixels_verified']
                assert report['nonopaque_source_fraction'] == 0
                write(folder/'reuse-manifest.json', manifest)
                print(f'{lpi:g} LPI: encoded once; camera/depth/frame identity preserved.', flush=True)
            records.append(dict(lpi=lpi, folder=str(folder), settings=report['settings'], source_indices=report['source_indices'], raster_size=report['raster_size'], pixels_per_channel=report['pixels_per_channel'], interlaced_sha256=report['interlaced_sha256'], raster_integrity=report['raster_integrity'], physical_validation=report['physical_validation'], warnings=report['warnings']))
    finally:
        printing.pitch_test, printing.registration = original_pitch, original_registration
    write(args.output/'execution.json', dict(identity=identity, prints=records, ai_or_blender_started=False, camera_or_depth_changed=False, calibration_sheets_generated=False, reused_preview=str(reference/'hareketli-onizleme.gif')))


if __name__ == '__main__':
    main()
