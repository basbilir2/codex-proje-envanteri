from pathlib import Path
import json,os,shutil
os.environ['HF_HUB_DISABLE_XET']='1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
import numpy as np
import torch
from PIL import Image
from huggingface_hub import model_info
from transformers import Sam2Model,Sam2Processor
WORK=Path(__file__).resolve().parent;OUT=WORK/'scene'
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
MODEL='facebook/sam2.1-hiera-small'
revision=model_info(MODEL).sha
torch.set_num_threads(8)
print('SAM2: official small model, local photo inference',flush=True)
model=Sam2Model.from_pretrained(MODEL,revision=revision,cache_dir=APP/'.models',use_safetensors=True).eval()
processor=Sam2Processor.from_pretrained(MODEL,revision=revision,cache_dir=APP/'.models')
image=Image.open(OUT/'source.png').convert('RGB');w,h=image.size
positive=[[(.5,.12),(.5,.35),(.15,.531),(.25,.64),(.19,.78),(.2,.91),(.8,.76),(.73,.87),(.2,.44),(.28,.39),(.30,.48),(.77,.55)],
          [(.175,.432),(.28,.40),(.30,.48)],
          [(.78,.52),(.745,.59),(.717,.641)]]
negative=[[(.4,.007),(.57,.75),(.22,.985),(.84,.86),(.13,.31),(.90,.49)],
          [(.25,.378),(.38,.46),(.28,.557),(.127,.44)],
          [(.70,.49),(.825,.617),(.71,.68),(.88,.526)]]
points=[[[x*w,y*h] for x,y in pos+neg] for pos,neg in zip(positive,negative)]
labels=[[1]*len(pos)+[0]*len(neg) for pos,neg in zip(positive,negative)]
boxes=[[.02,.005,.96,.97],[.137,.345,.37,.544],[.598,.453,.858,.677]]
pixel_boxes=[[x0*w,y0*h,x1*w,y1*h] for x0,y0,x1,y1 in boxes]
inputs=processor(images=image,input_points=[points],input_labels=[labels],input_boxes=[pixel_boxes],return_tensors='pt')
with torch.inference_mode():outputs=model(**inputs,multimask_output=True)
candidates=processor.post_process_masks(outputs.pred_masks.cpu(),inputs['original_sizes'])[0].numpy().astype(bool)
scores=outputs.iou_scores.cpu().numpy()[0]
masks=[]
for i,(pos,neg,box) in enumerate(zip(positive,negative,pixel_boxes)):
    x0,y0,x1,y1=map(round,box)
    inside=np.zeros((h,w),bool);inside[y0:y1,x0:x1]=True
    options=candidates[i]&inside
    ranks=[float(scores[i,j])+100*sum(m[round(y*h),round(x*w)] for x,y in pos)-100*sum(m[round(y*h),round(x*w)] for x,y in neg) for j,m in enumerate(options)]
    masks.append(options[int(np.argmax(ranks))])
masks=np.stack(masks)
assert masks.shape==(3,h,w)
masks[0]|=masks[1]|masks[2]
assert not np.any(masks[1]&masks[2])
for i,(pos,neg) in enumerate(zip(positive,negative)):
    assert all(masks[i,round(y*h),round(x*w)] for x,y in pos),(i,'positive')
    assert not any(masks[i,round(y*h),round(x*w)] for x,y in neg),(i,'negative')
backup=OUT/'geometric-mask-draft';backup.mkdir(exist_ok=True)
for key,mask in zip(('person','left_arm','right_arm'),masks):
    shutil.copy2(OUT/f'{key}-mask.png',backup/f'{key}-mask.png')
    Image.fromarray(mask.astype(np.uint8)*255).save(OUT/f'{key}-mask.png')
rgb=np.asarray(image);overlay=rgb.copy().astype(np.float32)
overlay[masks[0]]=.7*rgb[masks[0]]+.3*np.array([70,210,255])
for mask,color in zip(masks[1:],([255,110,60],[230,90,240])):
    overlay[mask]=.55*rgb[mask]+.45*np.array(color)
review=Image.fromarray(overlay.astype(np.uint8));review.thumbnail((730,1210))
review.save(WORK/'semantic-boundaries-final.jpg',quality=96)
record=dict(model=MODEL,revision=revision,quality_scores=outputs.iou_scores.cpu().tolist(),
    points=points,labels=labels,photo_uploaded=False,depth_used=False)
(OUT/'segmentation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(dict(stage='semantic_masks_ready',scores=record['quality_scores'])),flush=True)
