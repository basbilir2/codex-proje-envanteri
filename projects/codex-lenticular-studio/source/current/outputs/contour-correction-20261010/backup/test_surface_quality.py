import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image

from lenticular.objects import edit_objects, region_mask, validate_regions
from lenticular.restoration import matte, complete_color, complete_depth, MODEL
from lenticular.layers import layered_surfaces, reliable_depth_core, extend_depth
from lenticular.pipeline import render_settings
from lenticular.geometry import validate, build_mesh


class SurfaceQualityChecks(unittest.TestCase):
    def test_object_keeps_shape_and_unselected_pixels_and_avoids_clipping(self):
        depth=np.tile(np.linspace(.2,.8,90,dtype=np.float32),(60,1))
        region=dict(points=[[.1,.1],[.8,.1],[.8,.9],[.1,.9]],offset=.05,relief=1.1)
        output,report=edit_objects(depth,[region]);mask=region_mask(region['points'],depth.shape)
        np.testing.assert_array_equal(output[~mask],depth[~mask])
        np.testing.assert_allclose(np.diff(output[mask]),np.diff(depth[mask])*1.1,atol=1e-7)
        limited,info=edit_objects(depth,[region|dict(offset=.45,relief=3)])
        self.assertTrue(info[0]['range_limited']);self.assertLessEqual(float(limited.max()),1)
        self.assertGreater(len(np.unique(limited[mask])),10)
        flat,_=edit_objects(np.full_like(depth,.4),[region]);self.assertEqual(float(np.ptp(flat[mask])),0)

    def test_uncertain_silhouette_depth_cannot_bend_an_opaque_edge(self):
        depth=np.full((160,160),.1,np.float32);mask=np.zeros(depth.shape,bool);mask[30:130,50:110]=True
        depth[mask]=.8
        # A depth predictor can mix background into alternating contour pixels.
        depth[30:130:2,50:52]=.51
        core=reliable_depth_core(mask,depth,.5,1,fine=True)
        geometry=extend_depth(depth,core)
        np.testing.assert_allclose(geometry[mask],.8,atol=1e-7)
        self.assertFalse(np.any(core[30:130,50:52]))

    def test_object_records_and_quality_validation(self):
        for region in (dict(points=[[0,0],[0,0],[0,0]],offset=0,relief=1),
                       dict(points=[[0,0],[1,0],[1,1]],offset=float('nan'),relief=1)):
            with self.assertRaises(ValueError): validate_regions([region])
        with self.assertRaises(ValueError): render_settings({'repair_quality':'missing'})
        with self.assertRaises(ValueError): render_settings({'object_regions':[{}]})

    def test_linear_mesh_sampler_preserves_a_sloping_surface(self):
        depth=np.tile(np.linspace(.1,.7,96,dtype=np.float32),(64,1))
        config=validate(dict(nr=2,ne=2,grid_size=32))
        mesh,_=build_mesh(depth,config,sample_mode='linear')
        x=np.clip(mesh['uv'][:,0]*96-.5,0,95)
        expected=.1+.6*x/95
        actual=(1/(-mesh['vertices'][:,2])-1/config['far'])/(1/config['near']-1/config['far'])
        np.testing.assert_allclose(actual,expected,atol=.0003)

    def test_matte_recovers_fractional_edge_and_preserves_core(self):
        yy,xx=np.mgrid[:96,:128];distance=np.sqrt((xx-64)**2+(yy-48)**2)
        actual=np.clip((27-distance)/3,0,1)
        rgb=np.rint(actual[...,None]*[220,100,30]+(1-actual[...,None])*[25,75,160]).astype(np.uint8)
        mask=actual>.5
        alpha,foreground,report=matte(rgb,mask)
        unknown=(actual>0)&(actual<1)
        self.assertLess(float(np.mean(np.abs(alpha[unknown]-actual[unknown]))),.12)
        self.assertTrue(np.all(alpha[distance<20]==1));self.assertTrue(np.all(alpha[distance>35]==0))
        np.testing.assert_array_equal(foreground[distance<20],rgb[distance<20])
        self.assertEqual(report['unresolved_fraction'],0)

    def test_hidden_depth_bounded_and_visible_values_exact(self):
        depth=np.tile(np.linspace(.2,.6,90,dtype=np.float32),(60,1));valid=np.ones(depth.shape,bool);valid[10:50,20:70]=False
        result=complete_depth(depth,valid,.2,.6)
        np.testing.assert_array_equal(result[valid],depth[valid])
        self.assertTrue(np.all(np.isfinite(result)));self.assertGreaterEqual(float(result.min()),.2-1e-6);self.assertLessEqual(float(result.max()),.6+1e-6)
        self.assertLess(float(np.mean(np.abs(result[~valid]-depth[~valid]))),.03)

    @unittest.skipUnless(MODEL.is_file(),'Local LaMa weights not installed')
    def test_real_lama_preserves_visible_pixels_and_odd_dimensions(self):
        yy,xx=np.mgrid[:65,:97];rgb=np.stack([xx*2,yy*3,np.full_like(xx,80)],axis=2).astype(np.uint8)
        mask=np.zeros((65,97),bool);mask[21:42,35:61]=True
        output,info=complete_color(rgb,mask)
        self.assertEqual(output.shape,rgb.shape)
        np.testing.assert_array_equal(output[~mask],rgb[~mask])
        self.assertGreater(np.std(output[mask]),0)
        self.assertEqual(info['model_size'],[97,65])

    def test_layer_report_masks_and_shared_texture_contract(self):
        h,w=80,96;rgb=np.full((h,w,3),60,np.uint8);rgb[20:60,30:70]=200
        depth=np.full((h,w),.2,np.float32);depth[20:60,30:70]=.8
        config=validate(dict(nr=3,ne=3,grid_size=32))
        def fill(image,mask):
            result=image.copy();result[mask]=60
            return result,dict(engine='test',visible_pixels_unchanged=True)
        with tempfile.TemporaryDirectory() as tmp,patch('lenticular.restoration.complete_color',side_effect=fill):
            layers,stats=layered_surfaces(Image.fromarray(rgb),depth,tmp,config,quality='advanced')
            report=json.loads((Path(tmp)/'repair.json').read_text())
            self.assertGreaterEqual(len(layers),2)
            self.assertTrue(any(l['matting'] for l in report['layers']))
            for layer in layers:
                with Image.open(Path(tmp)/layer['texture']) as texture:self.assertEqual(texture.size,(w,h))
                self.assertTrue((Path(tmp)/layer['mesh']).is_file())
