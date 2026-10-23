"""Depth layers with image-aligned alpha and separate, extrapolated geometry."""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .geometry import build_mesh


def extend_depth(depth, valid):
    """Nearest valid depth outside a layer; alpha, not a depth cliff, defines its edge."""
    if not np.any(valid):
        raise ValueError("Katmanda geçerli derinlik örneği yok.")
    holes = (~valid).astype(np.uint8)
    _, labels = cv2.distanceTransformWithLabels(holes,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    values = depth[valid]
    return values[np.maximum(labels-1,0)].astype(np.float32)


def reliable_depth_core(visible, depth, low, high, fine=False):
    reliable = visible & (depth>=low) & (depth<=high)
    if not np.any(reliable): reliable = visible.copy()
    if fine:
        # Alpha can align perfectly while blended depth at its boundary bends
        # the silhouette into a sawtooth in side views. Extrapolate geometry
        # from the interior, keeping that uncertain collar out of the mesh.
        band = max(2,round(min(depth.shape)*.006))
        kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*band+1,2*band+1))
        core=cv2.erode(reliable.astype(np.uint8),kernel)>0
        if np.any(core):
            # Erosion must not delete a separate thin object and then borrow
            # geometry from an unrelated, larger object in the same band.
            _,labels=cv2.connectedComponents(reliable.astype(np.uint8))
            surviving=np.zeros(int(labels.max())+1,dtype=bool)
            surviving[np.unique(labels[core])]=True
            core|=reliable&~surviving[labels]
            reliable=core
    return reliable


def separate_depth_jumps(depth, thresholds):
    """Split depth cliffs missed by area quantiles, with a bounded layer count.

    Quantiles alone can put a projecting hand and the shirt behind it in the
    same connected surface. Refining only the outside alpha cannot repair that
    internal bridge. These cuts require jointly reconciled mattes and completed
    backgrounds; independent masks can erase continuous cloth at a new cut.
    This is a discontinuity heuristic, not semantic segmentation.
    """
    h,w=depth.shape
    scale=min(1.,768/max(h,w))
    small=cv2.resize(depth,(max(2,round(w*scale)),max(2,round(h*scale))),interpolation=cv2.INTER_AREA)
    low,high=[],[]
    jump_limit=max(.025,float(np.ptp(small))*.08)
    for a,b in ((small[:,:-1],small[:,1:]),(small[:-1,:],small[1:,:])):
        keep=np.abs(a-b)>jump_limit
        low.append(np.minimum(a,b)[keep]);high.append(np.maximum(a,b)[keep])
    low,high=np.concatenate(low),np.concatenate(high)
    cuts=list(map(float,thresholds));added=[]
    candidates=np.linspace(float(small.min())+.01,float(small.max())-.01,256)
    minimum_edges=max(8,round(small.size*.0001))
    def covered():
        return np.any([(low<c)&(high>c) for c in cuts],axis=0) if cuts else np.zeros(low.shape,bool)
    for _ in range(min(4,max(0,7-len(cuts)))):
        remaining=~covered()
        a,b=low[remaining],high[remaining]
        if len(a)<minimum_edges: break
        gap=b-a;weight=gap**2
        # Keep the cut inside the depth gap, away from noisy endpoints.
        scores=np.array([np.sum(weight[(a+.2*gap<c)&(b-.2*gap>c)]) for c in candidates])
        best=int(np.argmax(scores));cut=float(candidates[best])
        hits=(a+.2*gap<cut)&(b-.2*gap>cut)
        if int(hits.sum())<minimum_edges or scores[best]<=0: break
        cuts.append(cut);added.append(cut)
    coverage=covered()
    return np.array(sorted(cuts)),dict(method='depth discontinuities at bounded working resolution',
        added_thresholds=added,detected_edge_pairs=len(low),separated_edge_pairs=int(coverage.sum()),
        remaining_edge_pairs=int((~coverage).sum()),maximum_layers=8)


def align_mask(rgb, initial, fine=False):
    """Refine depth silhouettes within a resolution-scaled color boundary band."""
    band = max(2,round(min(initial.shape)*.005))
    kernel = np.ones((2*band+1,2*band+1),np.uint8)
    core = cv2.erode(initial.astype(np.uint8),kernel)>0
    outside = cv2.dilate(initial.astype(np.uint8),kernel)==0
    if np.count_nonzero(core)<16 or np.count_nonzero(outside)<16:
        return initial.copy()
    trimap = np.where(initial,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8)
    trimap[core],trimap[outside] = cv2.GC_FGD,cv2.GC_BGD
    cv2.setRNGSeed(0)
    cv2.grabCut(rgb,trimap,None,np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),2,cv2.GC_INIT_WITH_MASK)
    refined=((trimap==cv2.GC_FGD)|(trimap==cv2.GC_PR_FGD)).astype(np.uint8)
    # Suppress single-pixel saw teeth without moving the reliable depth core.
    if not fine:
        refined=cv2.morphologyEx(refined,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
        refined=cv2.morphologyEx(refined,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
    refined[core],refined[outside]=1,0
    return refined>0


def layered_surfaces(photo, depth, output, config, count=3, radius=5, quality='classic', checkpoint=lambda: None):
    output = Path(output)
    if not 1<=count<=8 or not 1<=radius<=20:
        raise ValueError("Katman ayarı geçersiz.")
    rgb = np.asarray(photo.convert("RGB"))
    if quality not in ('classic','advanced'):
        raise ValueError('Katman kalitesi geçersiz.')
    advanced = quality == 'advanced'
    if advanced:
        from .restoration import matte, complete_color, complete_depth, linear_rgb, reconcile_matte
    original_alpha = np.asarray(photo.convert("RGBA"))[:,:,3]
    # At least two surfaces are needed to separate a silhouette from its background.
    # Cover the near end too: area quantiles can leave the entire horse and
    # its projecting legs in one surface when the background occupies most pixels.
    thresholds = (depth.min()+(depth.max()-depth.min())*np.linspace(.15,.9,count-1)
        if count>=4 else np.unique(np.quantile(depth,np.linspace(.35,.8,max(2,count)-1))))
    thresholds = thresholds[(thresholds>depth.min()+.01)&(thresholds<depth.max()-.01)]
    # Area quantiles can land on both endpoints of a two-plane scene and all
    # get discarded. Such a scene still needs two separate alpha surfaces.
    if not len(thresholds) and float(np.ptp(depth)) > .02:
        thresholds = np.array([(float(depth.min())+float(depth.max()))/2])
    partition=None
    if advanced:
        thresholds,partition=separate_depth_jumps(depth,thresholds)
    masks = [np.ones(depth.shape,dtype=bool)]
    cuts = []
    for threshold in thresholds:
        candidate = align_mask(rgb,depth>threshold,fine=advanced)&masks[-1]
        if np.count_nonzero(candidate)<16 or np.count_nonzero(masks[-1]&~candidate)<16:
            continue
        masks.append(candidate)
        cuts.append(float(threshold))
    width,height = photo.size
    focal = width*config["focal_mm"]/config["sensor_width_mm"]
    span = max(abs(x) for x in config["positions"])
    padding = 8+int(np.ceil(focal*span*(1/config["near"]-1/config["far"])))
    # Keep only this matte and the next one, even for large print images.
    current_matte=(masks[0].astype(np.float32),rgb.copy(),None) if advanced else None
    composite=np.zeros(rgb.shape,np.float32) if advanced else None
    layers,details = [],[]
    for i,mask in enumerate(masks):
        checkpoint()
        hidden = masks[i+1] if i+1<len(masks) else np.zeros_like(mask)
        # A lower surface needs the actual alpha above it, not just the depth mask.
        next_matte=matte(rgb,hidden) if advanced and i+1<len(masks) else None
        visible = mask&~hidden
        low = cuts[i-1] if i else 0.0
        high = cuts[i] if i<len(cuts) else 1.0
        # Refined alpha may include a former background pixel. Its depth must come
        # from the actual layer interior rather than the old cliff at that pixel.
        reliable = reliable_depth_core(visible,depth,low,high,fine=advanced)
        geometry = complete_depth(depth,reliable,low,high,surface_mask=visible) if advanced else extend_depth(depth,reliable)
        color = rgb.copy()
        matte_report = None
        completion_report = None
        if advanced:
            alpha,color,matte_report = current_matte
        else:
            alpha=(cv2.GaussianBlur(mask.astype(np.float32),(0,0),.7) if i else mask.astype(np.float32))
        # Complete the frame border together with the hidden background. Edge
        # repetition produced visible vertical bands in the old side views.
        texture_padding=padding if advanced and i==0 else 0
        if np.any(hidden) or texture_padding:
            collar = max(2,min(12,round(min(depth.shape)*.004))) if advanced else 2
            removal = cv2.dilate(hidden.astype(np.uint8),np.ones((2*collar+1,2*collar+1),np.uint8))*255
            if advanced:
                if texture_padding:
                    padded=np.pad(rgb,((padding,padding),(padding,padding),(0,0)),mode='edge')
                    holes=np.pad(removal>0,((padding,padding),(padding,padding)),constant_values=True)
                    filled,completion_report=complete_color(padded,holes)
                else:
                    filled,completion_report = complete_color(rgb,removal>0)
            else:
                filled = cv2.inpaint(rgb,removal,radius,cv2.INPAINT_TELEA)
            # Cleanup and foreground coverage share exactly the same support.
            # A wider model context must not erase pixels beyond that support.
            replace=(cv2.dilate(hidden.astype(np.uint8),cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,(2*collar+1,2*collar+1)))>0) if next_matte is not None else removal>0
            next_support=replace.copy()
            if texture_padding:
                color=np.pad(color,((padding,padding),(padding,padding),(0,0)),mode='edge')
                replace=np.pad(replace,((padding,padding),(padding,padding)),constant_values=True)
                color[replace]=filled[replace]
            else:
                color[replace] = filled[replace]
        if advanced:
            visible_color=color[padding:-padding,padding:-padding] if texture_padding else color
            opacity=(np.rint(alpha*original_alpha)/255)[...,None]
            composite=linear_rgb(visible_color)*opacity+composite*(1-opacity)
            if next_matte is not None:
                a,f,info=next_matte
                a,f,consistency=reconcile_matte(rgb,f,a,composite,next_support&(original_alpha==255))
                next_matte=(a,f,info|consistency)
        # A completed distant layer is always present. Closer layers only draw
        # their own silhouette; none bridge foreground and background depth.
        # Adjacent inclusive ranges can create coincident faces at a cut.
        # Their ray order then becomes unstable even in the source camera.
        # Keep a subpixel gap so alpha composition has a strict depth order.
        epsilon=min(1e-4,(high-low)*.01)
        geometry_low=low+epsilon if i else low
        geometry_high=high-epsilon if i+1<len(masks) else high
        geometry = np.clip(geometry,geometry_low,geometry_high).astype(np.float32)
        # Each band stays continuous; alpha separates the larger depth jumps.
        mesh_config = config|{"edge_threshold":1.0}
        mesh,stats = build_mesh(geometry,mesh_config,padding=padding if i==0 else 0,
            sample_mode='linear' if advanced else 'nearest')
        texture_alpha=alpha*original_alpha
        if texture_padding:
            # New texture includes real pixels in the padded strip. Map source
            # UVs into its interior so source-camera registration stays exact.
            mesh['uv']=(mesh['uv']*[width,height]+padding)/[width+2*padding,height+2*padding]
            mesh['uv']=mesh['uv'].astype(np.float32)
            texture_alpha=np.pad(texture_alpha,((padding,padding),(padding,padding)),mode='edge')
        name = f"layer_{i:02d}"
        texture = Image.fromarray(color).convert("RGBA")
        texture.putalpha(Image.fromarray(np.rint(texture_alpha).astype(np.uint8)))
        texture.save(output/(name+".png"))
        np.savez_compressed(output/(name+".npz"),**mesh)
        Image.fromarray((mask*255).astype(np.uint8)).save(output/(name+"_mask.png"))
        layers.append(dict(name=f"Depth layer {i+1}",mesh=name+".npz",texture=name+".png",extend=i==0 and not advanced))
        details.append(dict(depth_interval=[low,high],alpha_fraction=float(np.mean(mask)),
            estimated_fraction=float(np.mean(hidden)),matting=matte_report,completion=completion_report,
            texture_padding_px=texture_padding,geometry_interval=[geometry_low,geometry_high],mesh=stats))
        current_matte=next_matte
    report=dict(engine=("Depth layers / PyMatting / bounded hidden depth / shared LaMa color" if advanced else
        "Depth layers / constrained GrabCut alpha / nearest depth extension / Telea color"),layers=details,
        padding_px=padding,partition=partition,border_method='shared LaMa completion' if advanced else 'edge repeat',
        alpha_feather_sigma_px=None if advanced else .7,
        note="Hidden color and geometry are inferred. Matting depends on correct initial silhouettes; ambiguous hair/veil still needs review." if advanced else "Hidden color is estimated. Alpha refinement is not hair or veil matting.")
    (output/"repair.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return layers,dict(vertices=sum(d["mesh"]["vertices"] for d in details),triangles=sum(d["mesh"]["triangles"] for d in details),
        cut_triangles=sum(d["mesh"]["cut_triangles"] for d in details),
        split_triangles=sum(d["mesh"]["split_triangles"] for d in details),focal_px=focal,layer_count=len(layers))
