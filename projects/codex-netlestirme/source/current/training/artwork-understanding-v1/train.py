"""One bounded supervised LoRA pilot for artwork observations, not image generation."""
import pathlib,json,time,hashlib,random,os,gc,math
import torch
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration,AutoProcessor
from peft import LoraConfig,get_peft_model
from artwork_plan import ANALYSIS_PROMPT,analyze
ROOT=pathlib.Path(__file__).resolve().parent
MODELS=ROOT/'models';BASE=MODELS/'Qwen/Qwen-Image/text_encoder';PROC=MODELS/'Qwen/Qwen-Image-Edit/processor'
def main():
    guard=json.load(open('/tmp/recovery-stop-guard.json'));assert guard['armed'] and guard['pod_id']==os.environ['RUNPOD_POD_ID'] and guard['deadline_unix']>time.time()+1200
    os.kill(guard['pid'],0)
    torch.manual_seed(42);random.seed(42)
    data=json.loads((ROOT/'train.json').read_text());heldout=json.loads((ROOT/'heldout.json').read_text())
    for row in data+heldout:assert hashlib.sha256((ROOT/row['image']).read_bytes()).hexdigest()==row['source_sha256']
    assert not {r['source_sha256'] for r in data}&{r['source_sha256'] for r in heldout}
    model=Qwen2_5_VLForConditionalGeneration.from_pretrained(BASE,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).to('cuda')
    model.config.use_cache=False
    model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.05,target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM',bias='none'))
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads();model.train()
    processor=AutoProcessor.from_pretrained(PROC,local_files_only=True,min_pixels=56*56,max_pixels=448*448)
    trainable=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(trainable,lr=1e-4,weight_decay=0.01)
    report=dict(kind='Qwen2.5-VL artwork-understanding LoRA',training_examples=len(data),heldout_examples=len(heldout),epochs=2,planned_steps=len(data)*2,steps=0,trainable_parameters=sum(p.numel() for p in trainable),losses=[],seed=42,r=8,alpha=16,lr=1e-4,base_revision='75e0b4be04f60ec59a75f475837eced720f823b6',status='training',validation_quality_accepted=False)
    started=time.monotonic()
    for epoch in range(2):
        order=list(data);random.Random(42+epoch).shuffle(order)
        for row in order:
            if time.time()>guard['deadline_unix']-600:raise TimeoutError('Preserving time to save/evaluate/download; no extra steps')
            image=Image.open(ROOT/row['image']).convert('RGB')
            user={'role':'user','content':[{'type':'image','image':image},{'type':'text','text':ANALYSIS_PROMPT}]}
            prefix=processor.apply_chat_template([user],add_generation_prompt=True,tokenize=True,return_dict=True,return_tensors='pt')
            answer=json.dumps(row['observation'],ensure_ascii=False,separators=(',',':'))
            batch=processor.apply_chat_template([user,{'role':'assistant','content':[{'type':'text','text':answer}]}],add_generation_prompt=False,tokenize=True,return_dict=True,return_tensors='pt')
            count=prefix['input_ids'].shape[1]
            assert torch.equal(prefix['input_ids'],batch['input_ids'][:,:count]),'Assistant-only loss prefix mismatch'
            labels=batch['input_ids'].clone();labels[:,:count]=-100
            assert (labels!=-100).sum()>0 and batch['input_ids'].shape[1]<4096
            batch=batch.to('cuda');labels=labels.to('cuda');optimizer.zero_grad(set_to_none=True)
            loss=model(**batch,labels=labels).loss
            if not torch.isfinite(loss):raise ValueError('Non-finite loss; stop without claiming training completed')
            loss.backward();norm=torch.nn.utils.clip_grad_norm_(trainable,1.0)
            if not torch.isfinite(norm):raise ValueError('Non-finite gradient')
            optimizer.step();report['steps']+=1;report['losses'].append(float(loss.detach()))
            print(json.dumps(dict(step=report['steps'],total=report['planned_steps'],loss=report['losses'][-1],example=row['id'])),flush=True)
            (ROOT/'progress.json').write_text(json.dumps(report,indent=2))
    output=ROOT/'adapter';model.save_pretrained(output,safe_serialization=True)
    report.update(status='trained',seconds=round(time.monotonic()-started,2),adapter_sha256=hashlib.sha256((output/'adapter_model.safetensors').read_bytes()).hexdigest(),adapter_bytes=(output/'adapter_model.safetensors').stat().st_size)
    (ROOT/'training-result.json').write_text(json.dumps(report,indent=2))
    print('UNDERSTANDING_ADAPTER_SAVED',flush=True)
    del optimizer,model,trainable;gc.collect();torch.cuda.empty_cache()
    validation=ROOT/'validation';validation.mkdir(exist_ok=True)
    # No extra diffusion inference: verify the component actually being trained.
    analyze([ROOT/r['image'] for r in heldout],[validation/(r['id']+'.json') for r in heldout],MODELS,'cuda',output,reject_incomplete=False)
    print('UNDERSTANDING_HELDOUT_ANALYSIS_COMPLETED',flush=True)
if __name__=='__main__':main()
