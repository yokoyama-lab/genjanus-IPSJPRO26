import re, csv, sys, os
from pathlib import Path
from collections import deque
V0 = Path('/home/claude/gen_janus/251226')
ART = Path('/home/claude/gen_janus/paper260703_evidence/v0_251226')
dirs = sorted(d.name for d in ART.iterdir() if d.is_dir())
MODEL_RE = re.compile(r'_out\d+_(gpt5_2|gpt4_1|gpt5-nano)_')
def normalize_lines(s):
    s = s.replace("\r\n","\n").replace("\r","\n")
    lines=[l.rstrip() for l in s.split("\n")]
    while lines and lines[-1]=="": lines.pop()
    return lines
SECTIONS = {"成功したファイル（正しい出力）":"SUCCESS","成功したファイル（誤った出力）":"WRONG_OUTPUT",
            "構文エラーのあったファイル":"SYNTAX_ERROR","実行エラーのあったファイル":"RUNTIME_ERROR"}
def parse_stat(p):
    res={}; cur=None
    for line in p.read_text(encoding='utf-8').splitlines():
        m=re.match(r'^\S+ (.+?) \((\d+)件\)', line)
        if m:
            cur=SECTIONS.get(m.group(1)); continue
        if cur and line.startswith('  ') and line.strip().endswith('.janus'):
            res[os.path.basename(line.strip())]=cur
    return res
def parse_log(logp, answer_lines):
    # same algorithm as analyze_jana_results_detailed2.py
    file_pat=re.compile(r"^=== 検証: (.+\.janus) ==="); rt=re.compile(r"^\[ERROR \(line"); sy=re.compile(r'^File "')
    results={}; correct={}; cur=None; win=deque(maxlen=len(answer_lines))
    for raw in logp.read_text(encoding='utf-8',errors='replace').splitlines():
        s=raw.rstrip(); m=file_pat.match(s)
        if m: cur=os.path.basename(m.group(1)); results[cur]="SUCCESS"; win.clear(); continue
        if cur is None: continue
        if sy.match(s): results[cur]="SYNTAX_ERROR"; win.clear(); continue
        if rt.match(s): results[cur]="RUNTIME_ERROR"; win.clear(); continue
        if results[cur]!="SUCCESS": continue
        win.append(s)
        if len(win)==len(answer_lines) and list(win)==answer_lines: correct[cur]=True
    return {f:(("SUCCESS" if correct.get(f) else "WRONG_OUTPUT") if st=="SUCCESS" else st) for f,st in results.items()}
w=csv.writer(sys.stdout); w.writerow(["file","dir","prompt","model","jana_status","jana_source"])
for d in dirs:
    dp=V0/d
    if not dp.exists(): print("MISSING", d, file=sys.stderr); continue
    prompt=d.split('_')[0]
    ans=V0/f"{prompt}_answer.txt"
    files=sorted(dp.glob('*.janus'))
    if not files: continue
    verdict={}; src="none"
    stats=[p for p in dp.glob('stat_*.txt')]
    for sp in stats:
        v=parse_stat(sp)
        if v: verdict=v; src="stat"; break
    if not verdict:
        logs=list(dp.glob('jana_check_results*.log'))
        if logs and ans.exists():
            verdict=parse_log(logs[0], normalize_lines(ans.read_text(encoding='utf-8'))); src="log"
    for f in files:
        m=MODEL_RE.search(f.name); model=m.group(1) if m else "unknown"
        w.writerow([f"251226/{d}/{f.name}", d, prompt, model, verdict.get(f.name,"NA"), src if f.name in verdict else "none"])
