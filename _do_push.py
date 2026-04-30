# encoding: utf-8
import subprocess, os

repo = r'H:\yt-dlp-easyuse'

# 1. Check file content
with open(os.path.join(repo, 'worker.py'), encoding='utf-8') as f:
    w = f.read()
print(f'worker.py has urllib.parse: {"urllib.parse" in w}')
print(f'worker.py has write_own_pid: {"def write_own_pid" in w}')

# 2. git add
r = subprocess.run(['git', 'add', '-A'], cwd=repo, capture_output=True, text=True)
print(f'git add: {r.stderr or "OK"}')

# 3. git status
r = subprocess.run(['git', 'status', '--short'], cwd=repo, capture_output=True, text=True)
print(f'Files to commit:\n{r.stdout or "(none)"}')

# 4. git commit (only if there are changes)
r = subprocess.run(['git', 'diff', '--cached', '--stat'], cwd=repo, capture_output=True, text=True)
if r.stdout.strip():
    r = subprocess.run(['git', 'commit', '-m', 'fix: worker crash, CORS, run.bat encoding, path traversal'], cwd=repo, capture_output=True, text=True)
    print(f'commit: {r.stdout}{r.stderr}')
else:
    print('No changes to commit')

# 5. git push
r = subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo, capture_output=True, text=True)
print(f'push: {r.stdout}{r.stderr}')

input('Press Enter to finish...')
