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


def align_mask(rgb, initial):
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
    return (trimap==cv2.GC_FGD)|(trimap==cv2.GC_PR_FGD)


def layered_surfaces(photo, depth, output, config, count=3, radius=5):
    output = Path(output)
    if not 1<=count<=8 or not 1<=radius<=20:
        raise ValueError("Katman ayarı geçersiz.")
    rgb = np.asarray(photo.convert("RGB"))
    original_alpha = np.asarray(photo.convert("RGBA"))[:,:,3]
    # At least two surfaces are needed to separate a silhouette from its background.
    # Cover the near end too: area quantiles can leave the entire horse and
    # its projecting legs in one surface when the background occupies most pixels.
    thresholds = (depth.min()+(depth.max()-depth.min())*np.linspace(.15,.9,count-1)
        if count>=4 else np.unique(np.quantile(depth,np.linspace(.35,.8,max(2,count)-1))))
    thresholds = thresholds[(thresholds>depth.min()+.01)&(thresholds<depth.max()-.01)]
    masks = [np.ones(depth.shape,dtype=bool)]
    cuts = []
    for threshold in thresholds:
        candidate = align_mask(rgb,depth>threshold)&masks[-1]
        if np.count_nonzero(candidate)<16 or np.count_nonzero(masks[-1]&~candidate)<16:
            continue
        masks.append(candidate)
        cuts.append(float(threshold))
    width,height = photo.size
    focal = width*config["focal_mm"]/config["sensor_width_mm"]
    span = max(abs(x) for x in config["positions"])
    padding = 8+int(np.ceil(focal*span*(1/config["near"]-1/config["far"])))
    layers,details = [],[]
    for i,mask in enumerate(masks):
        hidden = masks[i+1] if i+1<len(masks) else np.zeros_like(mask)
        visible = mask&~hidden
        low = cuts[i-1] if i else 0.0
        high = cuts[i] if i<len(cuts) else 1.0
        # Refined alpha may include a former background pixel. Its depth must come
        # from the actual layer interior rather than the old cliff at that pixel.
        reliable = visible&(depth>=low)&(depth<=high)
        if not np.any(reliable):
            reliable = visible
        geometry = extend_depth(depth,reliable)
        color = rgb.copy()
        if np.any(hidden):
            removal = cv2.dilate(hidden.astype(np.uint8),np.ones((5,5),np.uint8))*255
            filled = cv2.inpaint(rgb,removal,radius,cv2.INPAINT_TELEA)
            # Remove the complete collar too: source edge pixels outside the
            # refined mask otherwise reappear as a displaced second silhouette.
            color[removal>0] = filled[removal>0]
        # A completed distant layer is always present. Closer layers only draw
        # their own silhouette; none bridge foreground and background depth.
        geometry = np.clip(geometry,low,high).astype(np.float32)
        # Each band stays continuous; alpha separates the larger depth jumps.
        mesh_config = config|{"edge_threshold":1.0}
        mesh,stats = build_mesh(geometry,mesh_config,padding=padding if i==0 else 0)
        name = f"layer_{i:02d}"
        texture = Image.fromarray(color).convert("RGBA")
        texture.putalpha(Image.fromarray((mask.astype(np.uint16)*original_alpha).astype(np.uint8)))
        texture.save(output/(name+".png"))
        np.savez_compressed(output/(name+".npz"),**mesh)
        Image.fromarray((mask*255).astype(np.uint8)).save(output/(name+"_mask.png"))
        layers.append(dict(name=f"Depth layer {i+1}",mesh=name+".npz",texture=name+".png",extend=i==0))
        details.append(dict(depth_interval=[low,high],alpha_fraction=float(np.mean(mask)),
            estimated_fraction=float(np.mean(hidden)),mesh=stats))
    report=dict(engine="Depth layers / constrained GrabCut alpha / nearest depth extension / Telea color",layers=details,
        padding_px=padding,note="Hidden color is estimated. Alpha refinement is not hair or veil matting.")
    (output/"repair.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return layers,dict(vertices=sum(d["mesh"]["vertices"] for d in details),triangles=sum(d["mesh"]["triangles"] for d in details),
        cut_triangles=sum(d["mesh"]["cut_triangles"] for d in details),
        split_triangles=sum(d["mesh"]["split_triangles"] for d in details),focal_px=focal,layer_count=len(layers))
