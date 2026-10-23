import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image

from lenticular.objects import edit_objects, region_mask, validate_regions
from lenticular.restoration import matte, complete_color, complete_depth, MODEL, linear_rgb, reconcile_matte
from lenticular.layers import layered_surfaces, reliable_depth_core, extend_depth, separate_depth_jumps
from lenticular.pipeline import render_settings
from lenticular.geometry import validate, build_mesh


class SurfaceQualityChecks(unittest.TestCase):
    def test_matte_and_completed_background_reconstruct_source_together(self):
        source=np.array([[[45,100,210],[220,170,140],[30,70,100],[120,120,120]]],np.uint8)
        background=linear_rgb(np.array([[[80,90,30],[20,50,80],[30,70,100],[10,10,10]]],np.uint8))
        prior=np.array([[0,.25,0,1]],np.float32);foreground=source.copy();support=np.array([[True,True,True,False]])
        a,f,info=reconcile_matte(source,foreground,prior,background,support)
        self.assertGreater(a[0,0],0);self.assertEqual(a[0,2],0);self.assertEqual(a[0,3],1)
        actual=linear_rgb(f)*a[...,None]+background*(1-a[...,None])
        np.testing.assert_allclose(actual,linear_rgb(source),atol=.004)
        np.testing.assert_array_equal(f[~support],foreground[~support])

    def test_small_near_object_is_not_bridged_to_midground_by_area_quantiles(self):
        depth=np.full((160,200),.1,np.float32)
        depth[40:150,20:180]=.5
        depth[70:130,70:95]=.85
        cuts,info=separate_depth_jumps(depth,np.array([.2,.4]))
        self.assertTrue(any(.5<c<.85 for c in cuts))
        self.assertLessEqual(len(cuts),7)
        self.assertEqual(info['remaining_edge_pairs'],0)
        flat=np.tile(np.linspace(.1,.8,200,dtype=np.float32),(160,1))
        smooth_cuts,smooth_info=separate_depth_jumps(flat,np.array([.2,.4]))
        np.testing.assert_array_equal(smooth_cuts,[.2,.4])
        self.assertEqual(smooth_info['added_thresholds'],[])
        # Distinct lower-band cliffs need separation too; source-color
        # preservation across those cuts is tested by the composite regression.
        depth[10:30,10:190]=.26
        depth[12:28,40:100]=.36
        guarded,_=separate_depth_jumps(depth,np.array([.2,.4]))
        self.assertTrue(any(.2<c<.4 for c in guarded))
        self.assertTrue(any(.5<c<.85 for c in guarded))

    def test_core_retains_separate_thin_components(self):
        depth=np.full((160,160),.1,np.float32);mask=np.zeros(depth.shape,bool)
        mask[30:130,50:110]=True;depth[mask]=.8
        mask[20:140,130:132]=True;depth[20:140,130:132]=.6
        core=reliable_depth_core(mask,depth,.5,1,fine=True)
        geometry=extend_depth(depth,core)
        np.testing.assert_allclose(geometry[20:140,130:132],.6,atol=1e-7)

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
            prior_nearest=None
            for layer in layers:
                pad=report['layers'][layers.index(layer)]['texture_padding_px']
                with Image.open(Path(tmp)/layer['texture']) as texture:self.assertEqual(texture.size,(w+2*pad,h+2*pad))
                self.assertTrue((Path(tmp)/layer['mesh']).is_file())
                with np.load(Path(tmp)/layer['mesh']) as data:
                    mesh={key:data[key] for key in data.files}
                proximity=(1/(-mesh['vertices'][:,2])-1/config['far'])/(1/config['near']-1/config['far'])
                if prior_nearest is not None:self.assertGreater(float(proximity.min()),prior_nearest+1e-5)
                prior_nearest=float(proximity.max())
                if pad:
                    # Source-camera projection recovers pixel coordinates in
                    # the padded texture, not the old stretched frame edges.
                    z=-mesh['vertices'][:,2];focal=w*config['focal_mm']/config['sensor_width_mm']
                    source_x=mesh['vertices'][:,0]*focal/z+w/2
                    source_y=mesh['vertices'][:,1]*focal/z+h/2
                    np.testing.assert_allclose(mesh['uv'][:,0]*(w+2*pad),source_x+pad,atol=2e-5)
                    np.testing.assert_allclose(mesh['uv'][:,1]*(h+2*pad),source_y+pad,atol=2e-5)
                    self.assertFalse(layer['extend'])

    def test_completion_context_does_not_erase_visible_background(self):
        h,w=80,96;rgb=np.full((h,w,3),60,np.uint8);rgb[20:60,30:70]=200
        # Detail directly beside the object lies inside the model's context
        # collar, but is visible in the source camera and must stay untouched.
        rgb[25:55,27:30]=[20,120,80]
        depth=np.full((h,w),.2,np.float32);depth[20:60,30:70]=.8
        def fill(image,mask):
            result=image.copy();result[mask]=[190,30,210]
            return result,dict(engine='test')
        def hard_matte(image,mask):return mask.astype(np.float32),image.copy(),{}
        with tempfile.TemporaryDirectory() as tmp,patch('lenticular.restoration.complete_color',side_effect=fill),patch('lenticular.restoration.matte',side_effect=hard_matte):
            layers,_=layered_surfaces(Image.fromarray(rgb),depth,tmp,validate(dict(nr=2,grid_size=32)),quality='advanced')
            report=json.loads((Path(tmp)/'repair.json').read_text());composite=np.zeros(rgb.shape,np.float32)
            for item,detail in zip(layers,report['layers']):
                with Image.open(Path(tmp)/item['texture']) as image:data=np.asarray(image).copy()
                pad=detail['texture_padding_px']
                if pad:data=data[pad:-pad,pad:-pad]
                a=data[:,:,3:4]/255
                composite=linear_rgb(data[:,:,:3])*a+composite*(1-a)
            np.testing.assert_allclose(composite,linear_rgb(rgb),atol=.004)
