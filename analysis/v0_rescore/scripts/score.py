import subprocess, sys, os, csv
from collections import deque
from pathlib import Path
ROOT='/home/claude/gen_janus'
path, std = sys.argv[1], sys.argv[2]
prompt = path.split('/')[1].split('_')[0]
ans = Path(ROOT)/'251226'/f'{prompt}_answer.txt'
def norm(s):
    s=s.replace("\r\n","\n").replace("\r","\n"); L=[l.rstrip() for l in s.split("\n")]
    while L and L[-1]=="": L.pop()
    return L
answer=norm(ans.read_text(encoding='utf-8'))
cmd=['timeout','20','python3','-m','jana_py.cli','--std',std,'-s','-t','10',path]
env=dict(os.environ, PYTHONPATH='/home/claude/pyjanus')
p=subprocess.run(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out=p.stdout.decode('utf-8','replace'); lines=[l.rstrip() for l in out.split("\n")]
rc=p.returncode
if rc==124: status='TIMEOUT'
elif any(l.startswith('PyJanus parsing error') for l in lines): status='SYNTAX_ERROR'
elif any(l.startswith('PyJanus execution error') for l in lines): status='RUNTIME_ERROR'
elif rc!=0: status='OTHER_ERROR'
else:
    win=deque(maxlen=len(answer)); ok=False
    for l in lines:
        win.append(l)
        if len(win)==len(answer) and list(win)==answer: ok=True; break
    status='SUCCESS' if ok else 'WRONG_OUTPUT'
head=''
for l in lines:
    if l.startswith('  message:'): head=l.split(':',1)[1].strip(); break
if not head and status in ('OTHER_ERROR','WRONG_OUTPUT'):
    nz=[l for l in lines if l.strip()]; head=(nz[-1] if nz else '')[:120]
w=csv.writer(sys.stdout); w.writerow([path, prompt, '', std, status, rc, head[:200]])
