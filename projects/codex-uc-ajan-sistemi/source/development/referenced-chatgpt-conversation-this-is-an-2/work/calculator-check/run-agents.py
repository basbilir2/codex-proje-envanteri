import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'outputs/Hesap-Makinesi'
TEAM=ROOT/'outputs/OpenCode-3-Ajan'
WORK=Path(__file__).resolve().parent
config=json.loads((TEAM/'opencode.json').read_text(encoding='utf-8'))
config['provider']['nvidia-nim']['options']['timeout']=120000
config['permission']={'read':'deny','edit':'deny','bash':'deny','webfetch':'deny',
                      'task':{'*':'deny','glm':'allow','nemotron':'allow'}}
for name,agent in config['agent'].items():
    agent['prompt']=('Review only the supplied calculator code. No tools except the '
                     'primary agent may launch glm and nemotron. Do not edit files. '
                     'Keep the response under 100 words. Do not repeat tests.')
    agent['permission']={'read':'deny','edit':'deny','bash':'deny','webfetch':'deny'}
    if name!='deepseek':agent['permission']['task']='deny'
    agent['steps']=4
for model in config['provider']['nvidia-nim']['models'].values():
    model['limit']['output']=1024
path=WORK/'opencode.json'
path.write_text(json.dumps(config),encoding='utf-8')
env=os.environ.copy()
env['OPENCODE_CONFIG']=str(path)
env.pop('OPENCODE_CONFIG_CONTENT',None)
env.pop('OPENCODE_CONFIG_DIR',None)
env['OPENCODE_DISABLE_AUTOUPDATE']='true'
for key,folder in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),
                   ('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state')]:
    env[key]=str(ROOT/'work/smoke'/folder)
code=(APP/'calculator.js').read_text(encoding='utf-8')
prompt=('Test the three-agent team on this real calculator implementation. '
        'Immediately issue TWO task calls in ONE response: glm must check arithmetic '
        'and state transitions; nemotron must review division by zero and invalid input. '
        'Include the supplied code in each child prompt. Both agents return at most '
        '3 concrete findings, or OK. Do not run tools other than those two task calls. '
        'Collect both results and briefly state your conclusion in Turkish. '
        'No extra agents or repeated reviews. CODE:\n'+code)
cli=ROOT/'work/runtime/node_modules/opencode-ai/bin/opencode.exe'
start=time.monotonic()
report={'test':'real_OpenCode_calculator_review','models_changed':False}
try:
    p=subprocess.run([str(cli),'run','--format','json','--agent','deepseek',prompt],
                     cwd=APP,env=env,capture_output=True,text=True,
                     encoding='utf-8',errors='replace',timeout=80)
    output=p.stdout
    report['exit_code']=p.returncode
    report['status']='failed'
    children={}
    for line in output.splitlines():
        try:e=json.loads(line)
        except json.JSONDecodeError:continue
        part=e.get('part',{});state=part.get('state',{})
        name=state.get('input',{}).get('subagent_type')
        if part.get('tool')=='task' and name in ('glm','nemotron'):
            children[name]={'status':state.get('status'),
                            'model':state.get('metadata',{}).get('model'),
                            'time':state.get('time'),
                            'result':state.get('output','')[:1800]}
    report['children']=children
    if len(children)==2 and all(x['status']=='completed' for x in children.values()):
        a,b=[children[n]['time'] for n in ('glm','nemotron')]
        report['parallel']=max(a['start'],b['start'])<min(a['end'],b['end'])
        report['status']='passed' if report['parallel'] else 'not_parallel'
    (WORK/'agent-events.jsonl').write_text(output,encoding='utf-8')
except subprocess.TimeoutExpired as e:
    output=e.stdout or b''
    if isinstance(output,bytes):output=output.decode('utf-8','replace')
    (WORK/'agent-events.jsonl').write_text(output,encoding='utf-8')
    report.update(status='timeout',reason='No completed three-agent result within the single 80-second attempt')
report['seconds']=round(time.monotonic()-start,1)
(APP/'ajan-test-sonucu.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True,indent=2))
