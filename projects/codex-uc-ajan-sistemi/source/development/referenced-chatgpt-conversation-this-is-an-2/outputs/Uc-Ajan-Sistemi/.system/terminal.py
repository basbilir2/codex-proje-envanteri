"""Independent terminal project picker. Inference and chats run inside OpenCode."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime
from nim_adapter import nim_connection

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parent
PROJECTS = ROOT / 'Projeler'
REGISTRY = SYSTEM / 'projects.json'
CLI = SYSTEM / 'opencode.exe'
MODEL = 'nvidia-nim/deepseek-ai/deepseek-v4.1-flash'


def load_projects():
    if not REGISTRY.exists(): return []
    return json.loads(REGISTRY.read_text(encoding='utf-8'))


def save_projects(projects):
    pending = REGISTRY.with_suffix('.tmp')
    pending.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding='utf-8')
    pending.replace(REGISTRY)


def folder_for(project):
    path = Path(project['path'])
    return path if path.is_absolute() else ROOT / path


def new_project(name):
    name = name.strip()
    if not name: raise ValueError('Proje adı boş olamaz.')
    safe = re.sub(r'[^\w -]', '', name, flags=re.UNICODE).strip(' .')[:60]
    if not safe: safe = 'Proje'
    # Prefix also avoids Windows device names such as CON and PRN.
    folder = PROJECTS / ('Proje-' + safe)
    number = 2
    while folder.exists():
        folder = PROJECTS / ('Proje-' + safe + '-' + str(number))
        number += 1
    folder.mkdir(parents=True)
    project = {'name': name, 'path': str(folder.relative_to(ROOT)),
               'created': datetime.now().isoformat(timespec='seconds')}
    projects = load_projects()
    projects.append(project)
    save_projects(projects)
    return project, False


def existing_project(raw):
    folder = Path(raw.strip().strip('"')).expanduser().resolve(strict=True)
    if not folder.is_dir(): raise ValueError('Bu bir klasör değil.')
    projects = load_projects()
    for project in projects:
        if folder_for(project).resolve() == folder: return project, True
    project = {'name': folder.name, 'path': str(folder),
               'created': datetime.now().isoformat(timespec='seconds')}
    projects.append(project)
    save_projects(projects)
    return project, False


def choose_project():
    projects = load_projects()
    print('\nÜÇ AJAN — DeepSeek V4.1 · GLM 5.3 · NVIDIA Nemotron')
    print('N  Yeni proje    E  Mevcut uygulama klasörünü ekle    Q  Kapat')
    for index, project in enumerate(projects, 1):
        print(f'{index:2}  {project["name"]}')
    choice = input('\nSeçimin: ').strip()
    if choice.lower() == 'q': return None
    if choice.lower() == 'n': return new_project(input('Yeni projenin adı: '))
    if choice.lower() == 'e': return existing_project(input('Uygulama klasörünün yolu: '))
    if choice.isdigit() and 1 <= int(choice) <= len(projects):
        return projects[int(choice) - 1], True
    raise ValueError('N, E, Q veya proje numarasını yaz.')


def last_session(folder, env):
    # Non-Git folders share OpenCode's global project id. Match the actual folder,
    # so a new application never resumes another application's conversation.
    result = subprocess.run([str(CLI), 'session', 'list', '--pure', '--format', 'json'],
                            cwd=folder, env=env, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=20)
    if result.returncode: return None
    for session in json.loads(result.stdout):
        if Path(session.get('directory', '')).resolve() == folder:
            return session['id']
    return None


def start_chat(project, resume):
    folder = folder_for(project).resolve(strict=True)
    if not folder.is_dir(): raise ValueError('Proje klasörü bulunamadı.')
    print(f'\nProje: {project["name"]}\nKlasör: {folder}')
    print('İsteğini Türkçe yaz. Üç ajanı DeepSeek yönetecek.')
    print('OpenCode içinde /exit ile bu proje menüsüne dönebilirsin.\n', flush=True)
    command = [str(CLI), str(folder), '--pure', '--agent', 'deepseek', '--model', MODEL]
    key = os.environ['NVIDIA_API_KEY']
    with nim_connection(key, SYSTEM / 'last-requests.jsonl') as (url, token):
        env = os.environ.copy()
        env['NVIDIA_API_KEY'] = token
        env['OPENCODE_CONFIG_CONTENT'] = json.dumps({'provider': {'nvidia-nim': {
            'options': {'baseURL': url, 'apiKey': '{env:NVIDIA_API_KEY}'}}}})
        if resume:
            session_id = last_session(folder, env)
            if session_id: command.extend(['--session', session_id])
        result = subprocess.run(command, cwd=folder, env=env)
    if result.returncode: print('OpenCode oturumu kapandı. Yukarıdaki hata ayrıntısına bak.')
    return result.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Local startup check; no model requests.')
    parser.add_argument('--project', help='Open an existing application folder directly.')
    options = parser.parse_args()
    if options.check:
        assert CLI.is_file(), 'OpenCode bulunamadı.'
        assert (SYSTEM / 'opencode.json').is_file(), 'Yapılandırma bulunamadı.'
        assert os.environ.get('NVIDIA_API_KEY'), 'NVIDIA anahtarı yüklenemedi.'
        config = json.loads((SYSTEM / 'opencode.json').read_text(encoding='utf-8'))
        assert set(config['agent']) == {'deepseek', 'glm', 'nemotron'}
        assert config['enabled_providers'] == ['nvidia-nim']
        print('Başlatıcı, üç ajan yapılandırması ve şifreli anahtar yükleme: TAMAM.')
        return
    if options.project:
        project, resume = existing_project(options.project)
        start_chat(project, resume)
        return
    while True:
        try:
            selected = choose_project()
            if selected is None: break
            start_chat(*selected)
        except (EOFError, KeyboardInterrupt): break
        except (ValueError, OSError, json.JSONDecodeError) as error:
            print(f'\nAçılamadı: {error}')


if __name__ == '__main__': main()
