# encoding: utf-8
import subprocess, os

repo = r'H:\yt-dlp-easyuse'
log = []

# 1. Check files
w = open(os.path.join(repo, 'worker.py'), encoding='utf-8').read()
log.append(f'write_own_pid: {"def write_own_pid" in w}')
log.append(f'urllib.parse: {"urllib.parse" in w}')

# 2. git add
r = subprocess.run(['git', 'add', '-A'], cwd=repo, capture_output=True, text=True)
log.append(f'add: {r.stderr or "OK"}')

# 3. git status
r = subprocess.run(['git', 'status', '--short'], cwd=repo, capture_output=True, text=True)
log.append(f'status:\n{r.stdout or "(clean)"}')

# 4. commit
r = subprocess.run(['git', 'commit', '-m', 'fix: worker crash, CORS, run.bat encoding, path traversal'],
                   cwd=repo, capture_output=True, text=True)
log.append(f'commit: {r.stdout.strip() or r.stderr.strip()}')

# 5. push
r = subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo, capture_output=True, text=True)
log.append(f'push: {r.stdout.strip() or r.stderr.strip()}')

log.append('DONE!')
result = '\n'.join(log)
print(result)
