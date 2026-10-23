import json
import math
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

from lenticular.optics import sampling_budget, depth_sampling, invalidate_calibration
from lenticular.pipeline import render_settings, Studio
from lenticular.printing import (DEFAULTS, area_channel_weights, encode, color_transform,
    verify_raster, pitch_test)
from lenticular.repair import editable_depth, plan_parallax


class OpticalQualityChecks(unittest.TestCase):
    def test_exact_fractional_pixel_area_and_partition(self):
        s = DEFAULTS | dict(ne=2,ppi=60,effective_lpi=12,phase=.13)
        weights = list(area_channel_weights(20,0,2,s))
        # First boundary is at x=1.85: pixel [1,2] is 85% channel 0.
        self.assertAlmostEqual(float(weights[0][0,1]),.85,places=10)
        np.testing.assert_allclose(sum(weights),1,atol=1e-10)
        for tilt in (0,1e-7,-.25,10):
            for ratio in (.01,.873,10):
                w = list(area_channel_weights(25,3,4,s|dict(tilt_deg=tilt,ne=7,effective_lpi=ratio*60)))
                np.testing.assert_allclose(sum(w),1,atol=2e-7)
        # Allowed high-PPI / low-LPI extremes must not lose constant light.
        for tilt in (.00001,.0001,.001):
            w=list(area_channel_weights(20,0,3,s|dict(ppi=4800,effective_lpi=1,phase=.473,tilt_deg=tilt)))
            np.testing.assert_allclose(sum(w),1,atol=1e-12)

    def test_tilted_mirrored_coverage_against_independent_dense_integral(self):
        samples=(np.arange(900)+.5)/900
        for axis in ('vertical','horizontal'):
            for mirror in (False,True):
                s=DEFAULTS|dict(ne=5,ppi=113,effective_lpi=37.4,phase=-.217,tilt_deg=-7.1,axis=axis,mirror=mirror,bleed_mm=1.3)
                actual=np.array([w[1,5] for w in area_channel_weights(13,3,3,s)])
                x=(5+samples)[None,:]; y=(4+samples)[:,None]
                if mirror:x=13-x
                x=x-1.3*113/25.4;y=y-1.3*113/25.4
                a=math.radians(-7.1)
                u=x*math.cos(a)+y*math.sin(a) if axis=='vertical' else y*math.cos(a)+x*math.sin(a)
                channels=np.floor(((u*37.4/113-.217)%1)*5).astype(int)
                expected=np.bincount(channels.ravel(),minlength=5)/channels.size
                np.testing.assert_allclose(actual,expected,atol=.0003)

    def test_independent_front_back_budgets_keep_reference_and_shape(self):
        d=np.tile(np.linspace(.45,1,111,dtype=np.float32),(11,1));d[5,10]=.5
        s=render_settings(dict(depth_curve='balanced',angle_deg=8,zero_reference=.5,
            front_parallax_percent=1,back_parallax_percent=2.5,depth_smoothing=0,
            edge_refinement=0,edge_guard=False,reference_point={'x':10/110,'y':.5}))
        out,info=editable_depth(d,s)
        _,_,disp=plan_parallax(out,(111,11),s|{'zero_reference':info['zero_reference']})
        self.assertAlmostEqual(float(-disp.min()/111*100),1,places=5)
        self.assertAlmostEqual(float(disp.max()/111*100),2.5,places=5)
        self.assertEqual(float(out[5,10]),.5)
        self.assertTrue(np.all(np.diff(out[0])>=0))
        self.assertEqual(info['clipped_fraction'],0)
        stronger,_=editable_depth(d,s|dict(back_parallax_percent=2.8))
        np.testing.assert_array_equal(stronger[d>=.5],out[d>=.5])
        flat,_=editable_depth(np.full_like(d,.5),s)
        np.testing.assert_array_equal(flat,.5)

    def test_print_risk_uses_selected_ne_not_render_nr(self):
        config=dict(positions=np.linspace(-.1,.1,25).tolist(),near=1.5,far=3.,zero=2.,focal_mm=50,sensor_width_mm=36)
        depth=np.tile(np.linspace(0,1,101),(70,1))
        s=DEFAULTS|dict(width_mm=130,height_mm=90,effective_lpi=50)
        sparse,_=depth_sampling(depth,config,(101,70),s,[24,12,0])
        dense,_=depth_sampling(depth,config,(101,70),s,list(range(24,-1,-1)))
        self.assertAlmostEqual(sparse['adjacent_step_lenticules_p95']/dense['adjacent_step_lenticules_p95'],12)
        self.assertGreater(sparse['sides']['back']['internal_relief_p10_p90_mm'],0)
        flat,_=depth_sampling(np.zeros((70,101)),config,(101,70),s,[24,12,0])
        self.assertTrue(any('kendi iç hacmi' in x for x in flat['warnings']))

    def test_edge_guard_uses_common_scale_for_preview_and_final(self):
        s=render_settings(dict(angle_deg=20,parallax_guard=False,edge_guard=True))
        reports=[]
        for width in (512,2048):
            # Pixel-center samples of the same continuous sloping surface.
            x=(np.arange(width)+.5)/width
            d=np.tile((.5+.4*np.sin(30*x)).astype(np.float32),(100,1))
            reports.append(plan_parallax(d,(width,100),s)[1])
        self.assertAlmostEqual(reports[0]['effective_angle_deg'],reports[1]['effective_angle_deg'],delta=.02)

    def test_calibration_invalidation_and_sampling_sensitivity(self):
        old=DEFAULTS|dict(pitch_verified=True,raster_ppi_verified=True,lens_angle_verified=True,
            crosstalk_matrix=np.eye(10).tolist(),compensation=.8)
        revised,cleared=invalidate_calibration(old,old|{'ppi':1200})
        self.assertFalse(revised['pitch_verified']);self.assertFalse(revised['raster_ppi_verified'])
        self.assertTrue(revised['lens_angle_verified']);self.assertIsNone(revised['crosstalk_matrix'])
        self.assertEqual(revised['compensation'],0)
        self.assertEqual(invalidate_calibration(old,old)[1],[])
        b=sampling_budget(DEFAULTS|dict(ppi=1200,effective_lpi=50,width_mm=130,ne=12))
        self.assertEqual(b['two_pixel_channel_start'],12)
        self.assertAlmostEqual(b['quarter_channel_pitch_error_lpi']*130/25.4*12,.25)

    def test_reprint_clears_old_matrix_before_new_ne_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio=Studio(tmp)
            try:
                old=DEFAULTS|dict(ne=3,crosstalk_matrix=np.eye(3).tolist(),compensation=.5)
                studio.state['assets']['photo']={'id':'photo'}
                studio.state['jobs']['prior']=dict(id='prior',asset_id='photo',status='complete',
                    print=old,render=render_settings({}),render_folder=str(Path(tmp)/'render'))
                with patch.object(studio.executor,'submit'):
                    identifier=studio.start(dict(asset_id='photo',stage='print',render_job='prior',print=old|{'ne':4}))
                job=studio.state['jobs'][identifier]
                self.assertIsNone(job['print']['crosstalk_matrix'])
                self.assertEqual(job['print']['compensation'],0)
                self.assertIn('crosstalk_matrix',job['invalidated_calibration'])
                self.assertTrue(job['warnings'])
            finally:studio.close()

    def test_saved_area_and_compensated_raster_verified_and_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'views';folder.mkdir()
            for i,color in enumerate(('red','green','blue')):Image.new('RGB',(48,48),color).save(folder/f'view_{i:04d}.png')
            Image.new('RGB',(48,48),'green').save(root/'center.png')
            (root/'job.json').write_text(json.dumps(dict(config=dict(nr=3,zero=2,positions=[-.1,0,.1],camera_axis='x'))))
            s=DEFAULTS|dict(ppi=60,width_mm=25.4,height_mm=5.08,ne=3,effective_lpi=10.7,
                stripe_sampling='area',tilt_deg=4,phase=.127,compensation=.3,crosstalk=.1)
            report=encode(root,root/'print',s)
            self.assertTrue(report['raster_integrity']['sampled_pixels_verified'])
            self.assertEqual(report['stripe_coverage_method'],'analytic square-pixel integral')
            np.testing.assert_allclose(sum(report['raster_channel_coverage_fraction']),1,atol=1e-10)
            raster=tifffile.memmap(root/'print/interlaced.tif',mode='r+');raster[0,0]=0;raster.flush();del raster
            images={i:np.asarray(Image.open(folder/f'view_{i:04d}.png')) for i in range(3)}
            transform,_=color_transform(s)
            with self.assertRaisesRegex(ValueError,'TIFF seçilen'):
                verify_raster(root/'print/interlaced.tif',images,[2,1,0],s,transform,60,12)

    def test_horizontal_pitch_spans_print_height(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=DEFAULTS|dict(ppi=60,width_mm=25.4,height_mm=50.8,axis='horizontal',pitch_candidates=3)
            pitch_test(tmp,s,include_response=False)
            with Image.open(Path(tmp)/'pitch-test.tif') as image:
                self.assertEqual(image.height,120+round(22*60/25.4))


if __name__=='__main__':unittest.main()
