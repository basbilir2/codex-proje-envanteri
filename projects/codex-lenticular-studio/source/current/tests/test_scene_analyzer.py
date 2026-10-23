import io
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image

from lenticular.analyzer import analyze_scene
from lenticular.depth import proximity_from_depth
from lenticular.pipeline import Studio, render_settings
from lenticular.printing import DEFAULTS, remap_cubic, pitch_label, validate, encoded_strip


class SceneAnalysisChecks(unittest.TestCase):
    def test_large_raster_and_source_keep_samples_and_seams(self):
        source=np.tile((np.arange(40000,dtype=np.uint32)%251).astype(np.uint8)[None,:,None],(4,1,3))
        xs=np.arange(40000,dtype=np.float32)
        actual=remap_cubic(source,xs,np.arange(4,dtype=np.float32))
        np.testing.assert_array_equal(actual,source)
        small=source[:,:100]
        xs=np.linspace(-3,103,35000,dtype=np.float32);ys=np.array([0.,1.3,3.],np.float32)
        actual=remap_cubic(small,xs,ys)
        for start in (0,17498,32765):
            x=xs[start:start+20];mx=np.broadcast_to(x,(3,len(x))).copy();my=np.broadcast_to(ys[:,None],mx.shape).copy()
            expected=cv2.remap(small,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
            np.testing.assert_array_equal(actual[:,start:start+20],expected)

    def test_wide_area_encoding_completes(self):
        s=validate(dict(width_mm=3000,height_mm=5,ppi=300,ne=2,stripe_sampling='area'))
        images={0:np.zeros((8,8,3),np.uint8),1:np.full((8,8,3),255,np.uint8)}
        width=round(s['width_mm']*s['ppi']/25.4)
        result,coverage,_,_=encoded_strip(images,[0,1],width,59,0,1,s,np.eye(2))
        self.assertEqual(result.shape,(1,width,3));self.assertAlmostEqual(float(coverage.sum()),width,places=5)

    def test_pitch_labels_retain_fine_values(self):
        values=50.2+np.arange(-5,6)*.0001
        labels=[pitch_label(v,.0001) for v in values]
        self.assertEqual(len(set(labels)),11)
        np.testing.assert_allclose([float(v.split()[0]) for v in labels],values,atol=1e-9,rtol=0)

    def test_depth_preserves_extremes_and_legacy_is_explicit(self):
        depth=np.linspace(1,10,10000,dtype=np.float32).reshape(100,100)
        preserved,info=proximity_from_depth(depth)
        robust,legacy=proximity_from_depth(depth,'robust')
        self.assertEqual(info['clipped_fraction'],0)
        self.assertEqual(np.unique(preserved).size,10000)
        self.assertAlmostEqual(legacy['clipped_fraction'],.02)
        self.assertLess(np.unique(robust).size,np.unique(preserved).size)

    def test_analysis_reuses_geometry_and_retains_pin(self):
        photo=Image.new('RGB',(120,80),'gray')
        depth=np.tile(np.linspace(0,1,120,dtype=np.float32),(80,1))
        render=dict(reference_point={'x':.3,'y':.5},depth_smoothing=0,edge_refinement=0,nr=3)
        p=dict(ne=7,width_mm=100,ppi=600,effective_lpi=60)
        a,_=analyze_scene(photo,depth,render,p)
        b,_=analyze_scene(photo,depth,render,p|dict(ppi=1200,effective_lpi=50))
        self.assertEqual(a['render_settings']['reference_point'],render['reference_point'])
        self.assertEqual(a['recommendations']['render']['nr'],7)
        self.assertNotEqual(a['sampling_budget']['pixels_per_channel'],b['sampling_budget']['pixels_per_channel'])
        self.assertFalse(a['physical_3d_verified'])
        self.assertEqual(a['edits']['zero_reference'],float(depth[40,36]))
        from lenticular.repair import editable_depth,plan_parallax
        r=render_settings(render);d,edits=editable_depth(depth,r,photo)
        _,expected,_=plan_parallax(d,photo.size,r|{'zero_reference':edits['zero_reference']})
        self.assertEqual(a['parallax'],expected)

    def test_bad_or_mismatched_depth_is_rejected(self):
        photo=Image.new('RGB',(8,8))
        for d in (np.zeros((7,8)),np.full((8,8),np.nan),np.full((8,8),2)):
            with self.assertRaises(ValueError):analyze_scene(photo,d)

    def test_analysis_job_without_depth_calls_inference_with_output(self):
        with tempfile.TemporaryDirectory() as temp:
            studio=Studio(temp)
            try:
                data=io.BytesIO();Image.new('RGB',(32,24),'gray').save(data,format='PNG')
                asset=studio.add_photo(data.getvalue(),'photo.png')
                def estimate(photo,output,process_res):
                    self.assertTrue(Path(photo).is_file());output=Path(output);output.mkdir(parents=True)
                    raw=np.tile(np.linspace(1,4,32,dtype=np.float32),(24,1))
                    np.save(output/'relative_depth.npy',raw)
                    np.save(output/'depth_proximity.npy',proximity_from_depth(raw)[0])
                    (output/'metadata.json').write_text('{}')
                with patch('lenticular.pipeline.estimate',side_effect=estimate) as estimator:
                    identifier=studio.start(dict(asset_id=asset['id'],stage='analyze',render={},print={}))
                    for _ in range(200):
                        if studio.state['jobs'][identifier]['status'] in ('complete','failed'):break
                        time.sleep(.02)
                    job=studio.state['jobs'][identifier]
                    self.assertEqual(job['status'],'complete',job.get('message'))
                    self.assertEqual(estimator.call_count,1)
                    self.assertTrue((Path(job['output'])/'scene-analysis.json').is_file())
                    self.assertFalse((Path(job['output'])/'render').exists())
            finally:studio.close()

    def test_imported_depth_is_not_renormalized(self):
        with tempfile.TemporaryDirectory() as temp:
            d=np.full((4,4),.37,np.float32);np.save(Path(temp)/'depth_proximity.npy',d)
            np.save(Path(temp)/'relative_depth.npy',np.arange(1,17,dtype=np.float32).reshape(4,4))
            asset=dict(depth_folder=temp,supplied_depth=True)
            np.testing.assert_array_equal(Studio.load_depth(asset,{'depth_normalization':'preserve'}),d)


if __name__=='__main__':unittest.main()
