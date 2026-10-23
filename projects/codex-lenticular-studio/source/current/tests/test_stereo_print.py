import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image,PngImagePlugin

from lenticular.frames import FrameSet
from lenticular.printing import DEFAULTS, encode, encode_frames, frame_mapping, validate, verify_raster, color_transform
from lenticular.pipeline import render_settings
from lenticular.repair import editable_depth, plan_parallax
from lenticular.layers import align_mask


class StereoPrintChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def source(self, axis='x'):
        folder = self.root/axis
        (folder/'views').mkdir(parents=True)
        for i,color in enumerate(('red','green','blue')):
            Image.new('RGB',(64,64),color).save(folder/f'views/view_{i:04d}.png')
        Image.new('RGB',(64,64),'green').save(folder/'center.png')
        job = dict(config=dict(nr=3,zero=2,positions=[-.1,0,.1],camera_axis=axis))
        (folder/'job.json').write_text(json.dumps(job),encoding='utf-8')
        return folder,job

    def settings(self, **kwargs):
        return DEFAULTS | dict(width_mm=25.4,height_mm=5.08,ppi=60,ne=3,
            effective_lpi=10,nominal_lpi=10,fit='cover') | kwargs

    def test_optical_x_order_and_explicit_override(self):
        folder,job = self.source()
        settings = self.settings()
        self.assertEqual(FrameSet(folder).plan(settings)['source_indices'],[2,1,0])
        self.assertEqual(frame_mapping(job,settings),[2,1,0])
        self.assertEqual(FrameSet(folder).plan(settings|{'reverse_views':True})['source_indices'],[0,1,2])
        self.assertTrue(FrameSet(folder).plan(settings)['orthoscopic'])

    def test_y_up_camera_vs_raster_rows_down(self):
        folder,job = self.source('y')
        settings = self.settings(axis='horizontal')
        self.assertEqual(FrameSet(folder).plan(settings)['source_indices'],[0,1,2])
        self.assertEqual(frame_mapping(job,settings),[0,1,2])

    def test_saved_tiff_has_right_camera_in_left_strip(self):
        folder,_ = self.source()
        settings = self.settings()
        report = encode(folder,self.root/'print',settings)
        actual = tifffile.imread(self.root/'print/interlaced.tif')
        # Independent expected ray order: left strips -> right camera (blue).
        expected = np.array([[0,0,255]]*2+[[0,128,0]]*2+[[255,0,0]]*2,np.uint8)
        np.testing.assert_array_equal(actual[0,:6],expected)
        self.assertEqual(report['source_indices'],[2,1,0])
        self.assertTrue(report['raster_integrity']['sampled_pixels_verified'])
        self.assertFalse(report['physical_validation']['physical_3d_verified'])
        self.assertFalse(report['simulation_error']['physical_3d_verified'])
        self.assertTrue(report['simulation_error']['zero_error_is_not_physical_pass'])
        self.assertEqual(report['simulation_error']['model_kind'],'assumed_channel_mixing')
        self.assertEqual(report['status'],'calibration_draft')

    def test_stale_camera_plan_rejected(self):
        folder,_ = self.source()
        plan = dict(ne=3,source_indices=[0,1,2])
        with self.assertRaisesRegex(ValueError,'Eski/ters'):
            encode_frames(FrameSet(folder),plan,self.root/'bad',self.settings())

    def test_identical_camera_images_cannot_be_approved_as_3d(self):
        folder,_ = self.source()
        for i in (1,2):
            info=PngImagePlugin.PngInfo();info.add_text('unique_metadata',str(i))
            Image.open(folder/'views/view_0000.png').save(folder/f'views/view_{i:04d}.png',pnginfo=info)
        with self.assertRaisesRegex(ValueError,'aynı karelerin'):
            encode(folder,self.root/'identical',self.settings())

    def test_saved_pixel_corruption_is_rejected(self):
        folder,_ = self.source()
        settings = self.settings()
        encode(folder,self.root/'print',settings)
        target = self.root/'print/interlaced.tif'
        raster = tifffile.memmap(target,mode='r+')
        raster[0,0] = [1,2,3]
        raster.flush()
        del raster
        images = {i:np.asarray(Image.open(folder/f'views/view_{i:04d}.png')) for i in range(3)}
        transform,_ = color_transform(settings)
        with self.assertRaisesRegex(ValueError,'TIFF seçilen'):
            verify_raster(target,images,[2,1,0],settings,transform,60,12)

    def test_calibration_flags_require_real_booleans(self):
        for key in ('lens_angle_verified','raster_ppi_verified'):
            with self.assertRaises(ValueError):
                validate(self.settings(**{key:'true'}))

    def test_nose_pin_uses_full_precision_and_stays_at_zero(self):
        settings = render_settings(dict(reference_point={'x':.5,'y':.5},zero_reference=.43,
            effect_strength=1.8,depth_smoothing=0,edge_refinement=0,angle_deg=5))
        depth = np.linspace(.1,.9,121,dtype=np.float32).reshape(11,11)
        depth[5,5] = .430876
        edited,info = editable_depth(depth,settings)
        self.assertAlmostEqual(info['zero_reference'],float(depth[5,5]),places=7)
        self.assertEqual(float(edited[5,5]),float(depth[5,5]))
        _,_,disparity = plan_parallax(edited,(11,11),settings|{'zero_reference':info['zero_reference']})
        self.assertLess(abs(float(disparity[5,5])),.00001)
        for point in ({'x':True,'y':0},{'x':1.1,'y':0},{'x':0}):
            with self.assertRaises(ValueError):render_settings({'reference_point':point})

    def test_silhouette_refinement_keeps_reliable_core_and_outside(self):
        import cv2
        initial=np.zeros((80,80),bool);initial[20:60,20:60]=True
        rgb=np.full((80,80,3),30,np.uint8);rgb[initial]=210
        refined=align_mask(rgb,initial)
        kernel=np.ones((5,5),np.uint8)
        core=cv2.erode(initial.astype(np.uint8),kernel)>0
        outside=cv2.dilate(initial.astype(np.uint8),kernel)==0
        self.assertTrue(np.all(refined[core]))
        self.assertFalse(np.any(refined[outside]))

    def test_portrait_checks_cannot_accept_thumb_only_depth(self):
        from tools.refine_portrait_regions import check_regions
        good=dict(burun=0,basparmak=-62,sol_yanak=42,sag_yanak=32,
            diger_el=-30,sol_diz=-20,sag_diz=-22,govde=18,duvar_sol=40,duvar_sag=38)
        check_regions(good,-62)
        for name,value in dict(burun=1,basparmak=-70,sol_yanak=25,sag_yanak=18,
                diger_el=0,sol_diz=20,sag_diz=18,govde=8,duvar_sol=0,duvar_sag=0).items():
            with self.subTest(region=name),self.assertRaises(ValueError):
                check_regions(good|{name:value},-62)

    def test_skin_motion_requires_two_agreeing_reliable_scales(self):
        from tools.refine_portrait_regions import consistent_motion
        def sample(px,score):return dict(endpoint_px=px,correlations=[score,score])
        self.assertEqual(consistent_motion([sample(-18,.87),sample(-17,.798),sample(-17,.87)]),-17.5)
        with self.assertRaises(ValueError):consistent_motion([sample(-18,.87),sample(-2,.95)])
        with self.assertRaises(ValueError):consistent_motion([sample(-18,.87),sample(-18,.79)])


if __name__ == '__main__':
    unittest.main()
