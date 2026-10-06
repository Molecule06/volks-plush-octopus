"""Publish only this toy to its dedicated GitHub repository.

Authentication stays in process memory via Git Credential Manager.
No credentials are written to files or printed.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import urllib.error

ROOT = Path(__file__).parent
OWNER = 'Molecule06'
NAME = 'volks-plush-octopus'
API = 'https://api.github.com'
env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
cred = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, env=env, check=True, timeout=20)
fields = dict(line.split('=', 1) for line in cred.stdout.splitlines() if '=' in line)
token = fields.get('password')
if not token:
    raise RuntimeError('GitHub authentication is required.')

def api(path, method='GET', data=None):
    headers = {'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'Volks-games'}
    req = urllib.request.Request(API+path, data=json.dumps(data).encode() if data is not None else None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        # HTTP responses don't contain the credential, but retain only the useful message.
        body = json.loads(error.read() or '{}')
        raise RuntimeError(f'GitHub HTTP {error.code}: '+body.get('message', 'Request failed')) from None

def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, env=env, text=True, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()

if api('/user')['login'] != OWNER:
    raise RuntimeError('The authenticated GitHub account does not match the requested account.')

repo_path = f'/repos/{OWNER}/{NAME}'
if sys.argv[-1] == 'status':
    pages = api(repo_path+'/pages')
    try:
        build = api(repo_path+'/pages/builds/latest')
    except RuntimeError:
        build = {}
    print(json.dumps({'url': pages.get('html_url'), 'status': pages.get('status'), 'build': build.get('status'), 'error': build.get('error')}))
    sys.exit()

status_path = ROOT/'hosting-status.json'
if status_path.exists():
    status = json.loads(status_path.read_text())
    repo = api(repo_path)
else:
    # Do not modify an unrelated repository with this name.
    try:
        repo = api(repo_path)
    except RuntimeError as error:
        if 'HTTP 404' not in str(error):
            raise
        repo = api('/user/repos', 'POST', {'name': NAME, 'description': 'Volks games — interactive plush octopus, based on the Claude Opus material study.', 'private': False, 'auto_init': False})
        status_path.write_text(json.dumps({'repository': repo['html_url'], 'created_by_this_task': True}))
    else:
        raise RuntimeError('A repository with this name already exists. Choose a different dedicated name before publishing.')

# GitHub Pages publishes only docs; the original and adapters remain editable in source.
(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/index.html').write_bytes((ROOT/'dist/index.html').read_bytes())
(ROOT/'docs/.nojekyll').write_text('')
git('branch', '-M', 'main')
remotes = git('remote').splitlines()
if 'origin' not in remotes:
    git('remote', 'add', 'origin', repo['clone_url'])
elif git('remote', 'get-url', 'origin') != repo['clone_url']:
    raise RuntimeError('The local origin points to another repository.')
git('add', '--', '.gitignore', 'README.md', 'adapt.py', 'webgl-fallback.js', 'publish-github.py', 'dist', 'reference', 'docs')
git('-c', 'user.name=Volks', '-c', 'user.email=27095855+Molecule06@users.noreply.github.com', 'commit', '-m', 'Add Opus plush octopus with mobile controls and Volks games branding')
git('push', '-u', 'origin', 'main')
try:
    pages = api(repo_path+'/pages')
except RuntimeError as error:
    if 'HTTP 404' not in str(error):
        raise
    pages = api(repo_path+'/pages', 'POST', {'source': {'branch': 'main', 'path': '/docs'}, 'build_type': 'legacy'})
status_path.write_text(json.dumps({'repository': repo['html_url'], 'url': pages.get('html_url'), 'created_by_this_task': True}))
print(json.dumps({'repository': repo['html_url'], 'url': pages.get('html_url'), 'status': pages.get('status'), 'commit': git('rev-parse', 'HEAD')}))
