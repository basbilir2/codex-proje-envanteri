import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import tifffile
from PIL import Image

from lenticular.animation import DEFAULTS, generate, validate, cache_key, RifeInterpolator, capabilities
from lenticular.frames import FrameSet
from lenticular.interpolation import MotionInterpolator, MeshMorph
from lenticular.pipeline import Studio
from lenticular.printing import encode, DEFAULTS as PRINT, channel_pattern
from lenticular.runner import digest


class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def assets(self, images):
        result=[]
        for i,rgb in enumerate(images):
            path=self.root/f'source_{i}.png';Image.fromarray(rgb).save(path)
            result.append(dict(id=str(i),photo=str(path),size=[rgb.shape[1],rgb.shape[0]],sha256=digest(path)))
        return result

    def moving_pair(self):
        a=np.zeros((256,256,3),np.uint8);b=a.copy()
        a[80:160,60:120]=255;b[80:160,84:144]=255
        return a,b

    def test_real_motion_endpoints_and_centroid(self):
        a,b=self.moving_pair();engine=MotionInterpolator(a,b)
        self.assertTrue(np.array_equal(engine.frame(0),a));self.assertTrue(np.array_equal(engine.frame(1),b))
        mid=engine.frame(.5);mask=mid[:,:,0]>128
        self.assertLessEqual(abs(np.nonzero(mask)[1].mean()-101.5),1)
        self.assertEqual(np.count_nonzero(mask),80*60)
        self.assertTrue(np.array_equal(MotionInterpolator(a,a).frame(.37),a))
        with self.assertRaises(ValueError):engine.frame(float('nan'))

    def test_guided_morph_and_invalid_points(self):
        a,b=self.moving_pair();engine=MeshMorph(a,b,[[.35,.45,.44,.45]])
        self.assertTrue(np.array_equal(engine.frame(0),a));self.assertTrue(np.array_equal(engine.frame(1),b))
        self.assertEqual(engine.frame(.5).shape,a.shape)
        with self.assertRaises(ValueError):MeshMorph(a,b,[])
        with self.assertRaises(ValueError):MeshMorph(a,b,[[2,0,.4,.5]])
        with self.assertRaises(ValueError):MeshMorph(a,b,[[.25,.25,.75,.75],[.75,.75,.25,.25]])

    def test_generated_frames_pingpong_and_cache(self):
        sources=self.assets(self.moving_pair());spec=validate(dict(mode='motion',engine='flow',nt=5,long_edge=256,pingpong=True))
        data=generate(sources,self.root/'animation',spec)
        self.assertEqual(len(data['frames']),8)
        frames=FrameSet(self.root/'animation')
        self.assertEqual(frames.kind,'time_sequence');self.assertEqual(data['ns'],2)
        self.assertEqual(data['frames'][1]['sha256'],data['frames'][-1]['sha256'])
        self.assertEqual(cache_key(sources,spec),cache_key(sources,spec|{'preview_fps':24}))
        self.assertTrue(data['frames'][1]['generated'])
        self.assertTrue(np.array_equal(np.asarray(frames.image(0))[:,:,:3],self.moving_pair()[0]))

    def test_flip_tiff_actual_channels_and_white(self):
        images=[np.full((64,64,3),color,np.uint8) for color in ([255,0,0],[0,0,255])]
        folder=self.root/'flip';generate(self.assets(images),folder,dict(mode='flip',long_edge=64))
        settings=PRINT|dict(width_mm=25.4,height_mm=5.08,ppi=100,printer_dpi=720,effective_lpi=10,nominal_lpi=10,ne=8,white_underbase=True)
        frames=FrameSet(folder);self.assertEqual(frames.plan(settings)['source_indices'],[0]*4+[1]*4)
        report=encode(folder,self.root/'print',settings)
        actual=tifffile.imread(self.root/'print/interlaced.tif')
        pattern=channel_pattern(actual.shape[1],0,actual.shape[0],settings)
        expected=np.where((pattern<4)[:,:,None],np.array([255,0,0]),np.array([0,0,255]))
        self.assertTrue(np.array_equal(actual,expected))
        self.assertIsNone(report['nr']);self.assertEqual(report['nt'],2);self.assertEqual(report['ns'],2)
        self.assertEqual(report['settings']['printer_dpi'],720)
        self.assertTrue(np.all(tifffile.imread(self.root/'print/white-underbase.tif')==255))
        self.assertTrue((self.root/'print/channel-plan.json').is_file())

    def test_time_selection_axis_mirror_and_tamper(self):
        images=[np.full((64,64,3),i*100,np.uint8) for i in range(3)]
        folder=self.root/'seq';generate(self.assets(images),folder,dict(mode='sequence',long_edge=64))
        frames=FrameSet(folder);settings=PRINT|dict(ne=6,axis='horizontal',mirror=True)
        self.assertEqual(frames.plan(settings)['source_indices'],[0,0,1,1,2,2])
        report=encode(folder,self.root/'print',settings|dict(width_mm=5,height_mm=5,ppi=60,effective_lpi=10))
        self.assertEqual(report['frame_kind'],'time_sequence')
        Image.new('RGB',(64,64),'green').save(folder/'views/view_0001.png')
        with self.assertRaises(ValueError):FrameSet(folder)

    def test_cancel_has_no_complete_manifest(self):
        from concurrent.futures import CancelledError
        def cancel(message=None,percent=None):
            if message:raise CancelledError()
        with self.assertRaises(CancelledError):generate(self.assets(self.moving_pair()),self.root/'cancel',dict(engine='flow',nt=3),cancel)
        self.assertFalse((self.root/'cancel/frameset.json').exists())

    def test_legacy_pixels_identical_to_saved_encoder(self):
        baseline=Path(__file__).resolve().parents[1]/'.studio/code-backups/animation-e68e4e3296fe4ce085eeb4b2343ca944/lenticular/printing.py'
        if not baseline.is_file():self.skipTest('Pre-change encoder snapshot unavailable')
        spec=importlib.util.spec_from_file_location('lenticular._baseline_print',baseline)
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        folder=self.root/'legacy';(folder/'views').mkdir(parents=True)
        for i,color in enumerate(['red','green','blue']):Image.new('RGB',(64,64),color).save(folder/f'views/view_{i:04d}.png')
        Image.new('RGB',(64,64),'green').save(folder/'center.png')
        (folder/'job.json').write_text(json.dumps(dict(config=dict(nr=3,zero=1,positions=[-.1,0,.1],camera_axis='x'))))
        settings=PRINT|dict(width_mm=10,height_mm=8,ppi=90,effective_lpi=12.13,ne=3,phase=.13,mirror=True,stripe_sampling='area',compensation=.25,crosstalk=.1)
        # The old encoder needed manual reversal; camera-X ordering is now optical by default.
        legacy_settings={k:v for k,v in settings.items() if k in old.DEFAULTS}
        before=old.encode(folder,self.root/'old',legacy_settings|{'reverse_views':not settings['reverse_views']});after=encode(folder,self.root/'new',settings)
        self.assertTrue(np.array_equal(tifffile.imread(self.root/'old/interlaced.tif'),tifffile.imread(self.root/'new/interlaced.tif')))
        for key in ('raster_size','physical_size_mm','source_indices'):
            self.assertEqual(before[key],after[key])
        with tifffile.TiffFile(self.root/'old/interlaced.tif') as old_tif,tifffile.TiffFile(self.root/'new/interlaced.tif') as new_tif:
            # LittleCMS embeds creation time; compare the remaining ICC contents.
            aa=old_tif.pages[0].tags[34675].value;bb=new_tif.pages[0].tags[34675].value
            self.assertEqual(aa[:24]+aa[36:],bb[:24]+bb[36:])

    def test_pipeline_no_blender_and_reuse(self):
        studio=Studio(self.root)
        try:
            images=self.moving_pair();ids=[]
            import io
            for i,image in enumerate(images):
                blob=io.BytesIO();Image.fromarray(image).save(blob,format='PNG');ids.append(studio.add_photo(blob.getvalue(),f'{i}.png')['id'])
            seq=studio.add_sequence(ids)
            with patch('lenticular.pipeline.render',side_effect=AssertionError('Blender must not run')),patch('lenticular.pipeline.estimate',side_effect=AssertionError('Depth must not run')):
                job=studio.start(dict(asset_id=seq['id'],stage='animation_full',animation=dict(engine='flow',nt=3,long_edge=256),print=dict(width_mm=5,height_mm=5,ppi=60,ne=3,effective_lpi=10)))
                studio.executor.submit(lambda:None).result(timeout=60)
                self.assertEqual(studio.state['jobs'][job]['status'],'complete',studio.state['jobs'][job].get('message'))
                original=studio.state['jobs'][job]['frames_folder']
                again=studio.start(dict(asset_id=seq['id'],stage='animation_full',animation=dict(engine='flow',nt=3,long_edge=256,preview_fps=24),print=dict(width_mm=6,height_mm=5,ppi=80,ne=3,effective_lpi=10)))
                studio.executor.submit(lambda:None).result(timeout=60)
                self.assertEqual(studio.state['jobs'][again]['frames_folder'],original)
                self.assertEqual(studio.state['jobs'][again]['status'],'complete')
                self.assertTrue(studio.snapshot()['jobs'][again]['files']['channel_plan'])
        finally:
            studio.close()

    @unittest.skipUnless(capabilities()['rife'],'Local RIFE not installed')
    def test_real_rife_arbitrary_time(self):
        a,b=self.moving_pair();folder=self.root/'rife';folder.mkdir()
        engine=RifeInterpolator(a,b,folder,'0',lambda:None)
        mid=engine.frame(.37)
        self.assertEqual(mid.shape,a.shape);self.assertFalse(np.array_equal(mid,a));self.assertFalse(np.array_equal(mid,b))
        self.assertLess(abs(np.nonzero(mid[:,:,0]>128)[1].mean()-(89.5+24*.37)),2)


if __name__=='__main__':unittest.main()
