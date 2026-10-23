"""Small local MCP stdio server used by the application's AI agents."""
import argparse
import base64
import json
from pathlib import Path
import sys
from workbench import Workbench

def schema(properties,required):return {'type':'object','properties':properties,'required':required,'additionalProperties':False}
workspace={'type':'string','description':'Absolute path of the active work project.'}
TOOLS=[
 {'name':'inspect_project','description':'Identify this registered project, installed local SDKs, scripts, and missing prerequisites. No installs or model calls.',
  'inputSchema':schema({'workspace':workspace},['workspace'])},
 {'name':'checkpoint_project','description':'Create a deduplicated, hash-verified source checkpoint. Live databases, secrets, dependency caches are excluded. The user can restore it in the UI.',
  'inputSchema':schema({'workspace':workspace,'label':{'type':'string'}},['workspace'])},
 {'name':'browser_check','description':'Run the local web app in a fresh headless browser, click/fill/press controls, assert visible outcomes, capture screenshot and JS/HTTP errors. External network is blocked. Use include_image=true for visual review only when your model accepts images. On failure fix relevant source and rerun once; do not repeat a passing check on unchanged code.',
  'inputSchema':schema({'workspace':workspace,'steps':{'type':'array','maxItems':20,'items':{'type':'object','properties':{
      'action':{'type':'string','enum':['click','fill','press','hold','wait','expect_text','expect_visible','expect_stable','expect_motion']},
      'role':{'type':'string'},'name':{'type':'string'},'label':{'type':'string'},'selector':{'type':'string'},'text':{'type':'string'},
      'value':{'type':'string'},'key':{'type':'string'},'ms':{'type':'integer','minimum':0,'maximum':3000},'exact':{'type':'boolean'}},'required':['action'],'additionalProperties':False}},
      'width':{'type':'integer','minimum':320,'maximum':1920},'height':{'type':'integer','minimum':320,'maximum':1200},'include_image':{'type':'boolean'}},['workspace'])},
 {'name':'project_action','description':'Run the project build or relevant test, or produce a real distributable ZIP. Supports static web, npm build/test, .NET build/test/publish, Python syntax/pytest/PyInstaller, Godot headless check. Missing SDKs are reported. No deployment or publishing. Passing unchanged checks are reused. For Python syntax passing alone is not a functional GUI test.',
  'inputSchema':schema({'workspace':workspace,'action':{'type':'string','enum':['build','test','package']},'entry':{'type':'string','description':'Optional .csproj or Python entry path within the project.'}},['workspace','action'])}
]
TOOLS.append({'name':'desktop_check','description':'Run ONLY a newly packaged Windows EXE of this project. Inspect its own window via Windows UI Automation, invoke controls, fill fields, assert labels and capture only that window. No installed user applications or other windows are controlled. Publish via project_action first; use its executables path. App test data must honor UC_AI_TEST_MODE / UC_AI_TEST_PROFILE. Save these steps under studio-checks.json desktop.steps for automatic verification.',
 'inputSchema':schema({'workspace':workspace,'executable':{'type':'string'},'window_title':{'type':'string'},'include_image':{'type':'boolean'},
 'steps':{'type':'array','maxItems':20,'items':{'type':'object','properties':{'action':{'type':'string','enum':['click','fill','press','wait','expect_text','expect_visible']},'name':{'type':'string'},'automation_id':{'type':'string'},'text':{'type':'string'},'value':{'type':'string'},'key':{'type':'string'},'ms':{'type':'integer','minimum':0,'maximum':3000}},'required':['action'],'additionalProperties':False}}},['workspace','executable'])})
TOOLS.append({'name':'blender_asset','description':'Create a REAL game 3D asset using installed Blender on CPU. First interpret the user reference image and write a project-local Python script using bpy to build the approximate mesh, materials and optionally rig/actions. Script only constructs the asset; this tool handles cameras, lights, UV if missing, two renders, packed .blend, GLB export and GLB reimport validation, triangle budget and ZIP. Results appear in project assets3d/ and UI Checks. No paid service or neural image-to-mesh model is used; hidden surfaces are assumptions. For image-capable models include_image=true returns actual render for visual comparison. Fix a failed build from its error; reuse passing unchanged outputs.',
 'inputSchema':schema({'workspace':workspace,'script':{'type':'string','description':'Relative .py path in project; use import bpy, construct the asset in meters. Front is -Y, Z up. Never render/export/open other files outside project.'},'name':{'type':'string'},'reference':{'type':'string','description':'Optional relative reference image path copied into project.'},'max_triangles':{'type':'integer','minimum':12,'maximum':200000},'include_image':{'type':'boolean'}},['workspace','script'])})

def main():
    p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);a=p.parse_args()
    bench=Workbench(a.data_dir)
    try:
        for line in sys.stdin:
            try:
                request=json.loads(line);method=request.get('method');rid=request.get('id')
                if method=='initialize':result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'Uc AI Development Workbench','version':'1.1.0'}}
                elif method=='tools/list':result={'tools':TOOLS}
                elif method=='ping':result={}
                elif method=='tools/call':
                    params=request['params'];args=params.get('arguments',{});name=params['name']
                    try:
                        if name=='inspect_project':value=bench.inspect(**args)
                        elif name=='checkpoint_project':value=bench.checkpoint(**args)
                        elif name=='browser_check':value=bench.browser(**args)
                        elif name=='project_action':value=bench.action(**args)
                        elif name=='desktop_check':value=bench.desktop(**args)
                        elif name=='blender_asset':value=bench.blender(**args)
                        else:raise ValueError('Bilinmeyen araç.')
                        content=[{'type':'text','text':json.dumps(value,ensure_ascii=False)}]
                        if name in ('browser_check','desktop_check','blender_asset') and args.get('include_image') and value.get('screenshot') and Path(value['screenshot']).is_file():
                            content.append({'type':'image','mimeType':'image/png','data':base64.b64encode(Path(value['screenshot']).read_bytes()).decode()})
                        result={'content':content,'isError':not value.get('passed',True)}
                    except Exception as e:result={'content':[{'type':'text','text':str(e)[:3500]}],'isError':True}
                elif method.startswith('notifications/'):continue
                else:
                    if rid is not None:print(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method not found'}}),flush=True)
                    continue
                if rid is not None:print(json.dumps({'jsonrpc':'2.0','id':rid,'result':result},ensure_ascii=False),flush=True)
            except (ValueError,KeyError,TypeError) as e:
                if 'rid' in locals() and rid is not None:print(json.dumps({'jsonrpc':'2.0','id':rid,'error':{'code':-32602,'message':str(e)}}),flush=True)
    finally:bench.close()

if __name__=='__main__':main()
