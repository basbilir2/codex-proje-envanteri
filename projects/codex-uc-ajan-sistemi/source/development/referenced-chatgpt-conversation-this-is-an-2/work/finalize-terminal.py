import importlib.util
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / 'outputs/Uc-Ajan-Sistemi/.system'
path = SYSTEM / 'opencode.json'
config = json.loads(path.read_text(encoding='utf-8'))
config['provider']['nvidia-nim']['options']['timeout'] = 240000
for name, model in config['provider']['nvidia-nim']['models'].items():
    model['limit']['output'] = 8192 if 'nemotron' not in name else 4096
    if name.startswith('deepseek'):
        model['options'] = {'reasoning_effort': 1}
    elif name.startswith('z-ai'):
        model['options'] = {'reasoningEffort': 'low', 'chat_template_kwargs': {'clear_thinking': True}}
    else:
        model['options'] = {'chat_template_kwargs': {'enable_thinking': False}}
for name, agent in config['agent'].items():
    agent['steps'] = 24 if name == 'deepseek' else 12 if name == 'glm' else 6
path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
prompt = SYSTEM / 'prompts/deepseek.md'
content = prompt.read_text(encoding='utf-8')
content = content.replace('then request a final Nemotron review of the integrated changes when relevant.',
                          'request another review only if later integration introduced a concrete new risk.')
content += ('\nYou are the primary agent in a standalone terminal application, independent of Codex. '
            'For application development the user wants all three models involved: allocate precise '
            'parallel tasks to glm and nemotron in your first substantive development step. '
            'You may implement only disjoint files while they run. Do not repeat reviews or passing tests. '
            'Keep final answers short. Do not modify the launcher, credentials, or system configuration.\n')
prompt.write_text(content, encoding='utf-8')
spec = importlib.util.spec_from_file_location('terminal_app', SYSTEM / 'terminal.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if not module.load_projects():
    project, _ = module.new_project('Hesap Makinesi')
    for filename in ('calculator.js', 'index.html'):
        shutil.copy2(ROOT / 'outputs/Hesap-Makinesi' / filename, module.folder_for(project) / filename)
print('Bağımsız sistem ayarlandı; Hesap Makinesi projesi menüye eklendi.')
