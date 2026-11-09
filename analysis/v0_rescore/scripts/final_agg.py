import csv, json, collections, re, sys
S='/tmp/claude-0/-home-claude-gen-janus/a9f98304-a34e-5004-9730-997e9a370906/scratchpad'
OUT='/home/claude'
# ---- Basic19 mapping (V0 prompt -> paper id)
MAP={'p01swap':'p01swap','p02swap':'p02swap','p03cycle3':'p03cycle3','p04cycle3':'p04cycle3','p05cycle3':'p05cycle3','p06cycle3':'p06cycle3',
 'p08flipsign':'p07flipsign','p07max':'p08max2','p09even':'p09even','p11factorial':'p10fact','p12gcd':'p11gcd','p15fibpair':'p12fibp',
 'p10arrayreverse':'p13rev','p13linearsearch':'p14srchA','p14linearsearch':'p15srchB','p19sqrt':'p16sqrt','p16rle':'p17rle','p20perm2code':'p18perm2code','p17fib':'p19fib','p18fib':'(dropped)'}
PROMPTS=["p01swap","p02swap","p03cycle3","p04cycle3","p05cycle3","p06cycle3","p07flipsign","p08max2","p09even","p10fact","p11gcd","p12fibp","p13rev","p14srchA","p15srchB","p16sqrt","p17rle","p18perm2code","p19fib"]
MODELS=['gpt5_2','gpt4_1','gpt5-nano']; MNAME={'gpt5_2':'gpt-5.2','gpt4_1':'gpt-4.1','gpt5-nano':'gpt-5-nano'}
PAPER={"gpt5_2":[0,95,9,8,36,36,5,32,94,16,0,0,0,0,0,0,0,0,0],"gpt4_1":[0,81,26,33,17,21,7,23,78,13,0,0,0,0,0,0,0,0,0],"gpt5-nano":[0,94,72,76,67,69,12,35,61,6,0,2,6,0,0,0,0,13,0]}
man={r['file']:r for r in csv.DictReader(open(f'{S}/manifest.csv')) if not r['file'].endswith('stat_p19sqrt_251228_160316.janus')}
# ---- canonical dir selection: topups always; plus latest non-topup dir with n==100, else the one making n+topup closest to 100
dirs=collections.defaultdict(lambda: collections.defaultdict(list))
for f,r in man.items(): dirs[(r['prompt'],r['model'])][r['dir']].append(f)
canon=set(); canon_dirs={}
for (p,m),dd in dirs.items():
    top=[d for d in dd if 'topup' in d]; non=[d for d in dd if 'topup' not in d]
    ntop=sum(len(dd[d]) for d in top)
    def ts(d):
        mm=re.search(r'_(\d{6}_\d{6})',d); return mm.group(1) if mm else ''
    non.sort(key=ts)
    pick=None
    if ntop==0:
        full=[d for d in non if len(dd[d])==100]
        pick = full[-1] if full else (non[-1] if non else None)
    else:
        cands=sorted(non, key=lambda d:(abs(len(dd[d])+ntop-100), -non.index(d)))
        pick=cands[0] if cands else None
    chosen=top+([pick] if pick else [])
    canon_dirs[(p,m)]=chosen
    if MAP[p]!='(dropped)':
        for d in chosen: canon.update(dd[d])
# ---- scores
sc={}
raw_status=collections.Counter()
for row in csv.reader(open(f'{S}/scores_raw.csv')):
    if len(row)<7: continue
    f,p,_,std,st,rc,head=row[:7]
    raw_status[st]+=1
    if st=='OTHER_ERROR' and re.search(r'preprocessor|already defined|already bound|No main procedure',head): st='SYNTAX_ERROR'   # PyJanus preprocessing/validation errors == jana 'File ...' syntax-class errors
    sc[(f,std)]=(st,rc,head)
STDS=['jana2014','jana2014_in_out']
# ---- per-file CSV
w=csv.writer(open(f'{OUT}/v0_pyjanus_rescore.csv','w'))
w.writerow(['file','v0_prompt','basic19_id','model','canonical','jana_status','std','pyjanus_status','rc','error_head'])
missing=0
for f,r in sorted(man.items()):
    for std in STDS:
        if (f,std) not in sc: missing+=1; continue
        st,rc,head=sc[(f,std)]
        w.writerow([f,r['prompt'],MAP[r['prompt']],r['model'],int(f in canon),r['jana_status'],std,st,rc,head])
print("scored files:", len({f for f,_ in sc}), "of", len(man), "; missing (file,std) pairs:", missing)
print("raw PyJanus status counts (both stds):", dict(raw_status))
# ---- confusion matrices
CATS=['SUCCESS','WRONG_OUTPUT','SYNTAX_ERROR','RUNTIME_ERROR','TIMEOUT','OTHER_ERROR','NA']
def confusion(files, a, b, title):
    M=collections.Counter()
    for f in files:
        x=a(f); y=b(f)
        if x is None or y is None: continue
        M[(x,y)]+=1
    rows=[c for c in CATS if any(M[(c,d)] for d in CATS)]; cols=[c for c in CATS if any(M[(d,c)] for d in CATS)]
    lines=[f"**{title}** (rows = first, cols = second; n={sum(M.values())})", "| | "+" | ".join(cols)+" | total |","|---|"+"---|"*(len(cols)+1)]
    for r in rows: lines.append(f"| {r} | "+" | ".join(str(M[(r,c)]) for c in cols)+f" | {sum(M[(r,c)] for c in cols)} |")
    lines.append("| total | "+" | ".join(str(sum(M[(r,c)] for r in rows)) for c in cols)+f" | {sum(M.values())} |")
    return "\n".join(lines)
J=lambda f: man[f]['jana_status']
P14=lambda f: sc.get((f,'jana2014'),(None,))[0]
PIO=lambda f: sc.get((f,'jana2014_in_out'),(None,))[0]
canon_scored=[f for f in canon if (f,'jana2014') in sc]
all_scored=[f for f in man if (f,'jana2014') in sc]
report=[]
report.append(confusion(canon_scored, J, P14, "Confusion: jana (paper verdict) x PyJanus jana2014 — canonical V0 files"))
report.append(confusion(all_scored, J, P14, "Confusion: jana x PyJanus jana2014 — ALL scored V0 files (incl. duplicate/superseded runs)"))
report.append(confusion(canon_scored, P14, PIO, "Confusion: PyJanus jana2014 x PyJanus jana2014_in_out — canonical files"))
# ---- per prompt x model table
tab=[]; hdr="| Basic19 | V0 prompt | model | n | jana ✓ | jana % | paper % | Py2014 ✓ | Py2014 % | Py_in_out ✓ | Py_in_out % | Py2014: W/SY/RT/TO |"
tab.append(hdr); tab.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
cellcsv=csv.writer(open(f'{OUT}/v0_rescore_by_prompt_model.csv','w')); cellcsv.writerow(['basic19_id','v0_prompt','model','canonical_dirs','n','jana_success','jana_pct','paper_pct','py2014_success','py2014_pct','py_inout_success','py_inout_pct','py2014_wrong','py2014_syntax','py2014_runtime','py2014_timeout','py2014_other'])
V0PY={}
inv={v:k for k,v in MAP.items()}
for i,b in enumerate(PROMPTS):
    vp=inv[b]
    for m in MODELS:
        files=[f for f in canon_scored if man[f]['prompt']==vp and man[f]['model']==m]
        n=len(files)
        if not n: continue
        js=sum(1 for f in files if J(f)=='SUCCESS'); ps=sum(1 for f in files if P14(f)=='SUCCESS'); ios=sum(1 for f in files if PIO(f)=='SUCCESS')
        c=collections.Counter(P14(f) for f in files)
        V0PY[(b,m)]=(n,js,ps,ios)
        tab.append(f"| {b} | {vp} | {MNAME[m]} | {n} | {js} | {100*js/n:.0f} | {PAPER[m][i]} | {ps} | {100*ps/n:.0f} | {ios} | {100*ios/n:.0f} | {c['WRONG_OUTPUT']}/{c['SYNTAX_ERROR']}/{c['RUNTIME_ERROR']}/{c['TIMEOUT']} |")
        cellcsv.writerow([b,vp,m,';'.join(canon_dirs[(vp,m)]),n,js,f"{100*js/n:.1f}",PAPER[m][i],ps,f"{100*ps/n:.1f}",ios,f"{100*ios/n:.1f}",c['WRONG_OUTPUT'],c['SYNTAX_ERROR'],c['RUNTIME_ERROR'],c['TIMEOUT'],c['OTHER_ERROR']])
report.append("\n".join(tab))
# paper reproduction check
bad=[(b,m,V0PY[(b,m)][1],PAPER[m][i]) for i,b in enumerate(PROMPTS) for m in MODELS if (b,m) in V0PY and round(100*V0PY[(b,m)][1]/V0PY[(b,m)][0])!=PAPER[m][i]]
report.append("Canonical-run selection reproduces the paper's Table-4 jana percentages: " + ("ALL 57 cells" if not bad else f"mismatches {bad}"))
# totals per model
tot=[]
for m in MODELS:
    n=sum(v[0] for (b,mm),v in V0PY.items() if mm==m); js=sum(v[1] for (b,mm),v in V0PY.items() if mm==m); ps=sum(v[2] for (b,mm),v in V0PY.items() if mm==m); io=sum(v[3] for (b,mm),v in V0PY.items() if mm==m)
    tot.append(f"| {MNAME[m]} | {n} | {js} ({100*js/n:.1f}%) | {ps} ({100*ps/n:.1f}%) | {io} ({100*io/n:.1f}%) |")
report.append("| V0 model (19 prompts pooled) | n | jana ✓ | PyJanus jana2014 ✓ | PyJanus in_out ✓ |\n|---|---|---|---|---|\n"+"\n".join(tot))
# ---- cross-generation table
v2={tuple(k.split('|')):v for k,v in json.load(open(f'{S}/v2_basic19_agg.json')).items()}
V2M=["Opus 4.8/high","Gemini-3-flash-preview","GPT-5.4/low","GPT-5.5/low","GPT-5.4-mini/low","Gemini-3.1-flash-lite","Haiku 4.5"]
# V1 alignment
V1MAP={'p01swap':'swap','p02swap':'swap','p03cycle3':'cycle3','p04cycle3':'cycle3','p05cycle3':'cycle3','p06cycle3':'cycle3','p07flipsign':'negate','p08max2':'max_min*','p10fact':'factorial','p11gcd':'gcd','p16sqrt':'isqrt','p19fib':'fibonacci*'}
v1=collections.defaultdict(dict)
for l in open('/home/claude/gen_janus/paper260703_evidence/v1_260308/experiment_log.jsonl'):
    r=json.loads(l); v1[(r['task'],r['trial'])].setdefault(r['round'],r['status'])
def v1stat(task):
    ts=[v for (t,_),v in v1.items() if t==task]; n=len(ts)
    gf=sum(1 for v in ts if all(s=='GENERATION_FAIL' for s in v.values())); valid=n-gf
    r0=sum(1 for v in ts if v.get(0)=='SUCCESS'); fin=sum(1 for v in ts if 'SUCCESS' in v.values())
    return n,valid,r0,fin
lines=["| Basic19 | V0 gpt-5.2 Py2014 % (r0) | V0 gpt-4.1 | V0 gpt-5-nano | V1 Opus4.7 task | V1 r0 % / final % (valid n; all-100 n) | "+" | ".join(f"V2 {m} r0/final % (n)" for m in V2M)+" |"]
lines.append("|---|---|---|---|---|---|"+"---|"*len(V2M))
xg=csv.writer(open(f'{OUT}/cross_generation_table.csv','w'))
xg.writerow(['basic19_id']+[f'V0_{MNAME[m]}_py2014_pct' for m in MODELS]+['V1_task','V1_n_valid','V1_round0_pct_valid','V1_final_pct_valid','V1_round0_pct_all100','V1_final_pct_all100']+sum([[f'V2_{m}_n_valid',f'V2_{m}_round0_pct',f'V2_{m}_final_pct',f'V2_{m}_first10_success'] for m in V2M],[]))
for b in PROMPTS:
    v0c=[f"{100*V0PY[(b,m)][2]/V0PY[(b,m)][0]:.0f}" if (b,m) in V0PY else "-" for m in MODELS]
    t=V1MAP.get(b);
    if t:
        n,valid,r0,fin=v1stat(t.rstrip('*')); v1c=f"{t}"; v1v=f"{100*r0/valid:.0f} / {100*fin/valid:.0f} (n={valid}; {100*r0/n:.0f} / {100*fin/n:.0f})"
        v1row=[t,valid,f"{100*r0/valid:.1f}",f"{100*fin/valid:.1f}",f"{100*r0/n:.1f}",f"{100*fin/n:.1f}"]
    else: v1c="—"; v1v="—"; v1row=['','','','','','']
    v2c=[]; v2row=[]
    for m in V2M:
        n,r0,fin,f10s,f10n=v2[(m,b)]
        v2c.append(f"{100*r0/n:.0f}/{100*fin/n:.0f} ({n})" if n else "—"); v2row+= [n, f"{100*r0/n:.1f}" if n else '', f"{100*fin/n:.1f}" if n else '', f"{f10s}/{f10n}"]
    lines.append(f"| {b} | "+" | ".join(v0c)+f" | {v1c} | {v1v} | "+" | ".join(v2c)+" |")
    xg.writerow([b]+v0c+v1row+v2row)
report.append("\n".join(lines))
# V1 non-aligned tasks
extra=[t for t in sorted({t for t,_ in v1}) if t not in {x.rstrip('*') for x in V1MAP.values()}]
report.append("V1 tasks with no Basic19 counterpart (not in table): "+", ".join(extra))
open(f'{S}/report_parts.md','w').write("\n\n".join(report))
print("\n\n".join(report))

# ---- disagreement summary (canonical files, jana2014)
dis=collections.defaultdict(collections.Counter)
for f in canon_scored:
    j=J(f); p=P14(f)
    if j not in ('NA',) and j!=p:
        head=sc[(f,'jana2014')][2]
        head=re.sub(r"`[^`]*'", "`X'", head)
        if p in ('SUCCESS','WRONG_OUTPUT'): head='(ran to completion)'
        dis[(j,p)][head]+=1
lines=["| jana verdict → PyJanus(jana2014) | n | top PyJanus messages |","|---|---|---|"]
for k,c in sorted(dis.items(), key=lambda kv:-sum(kv[1].values())):
    lines.append(f"| {k[0]} → {k[1]} | {sum(c.values())} | "+"; ".join(f"{m} ({n})" for m,n in c.most_common(3))+" |")
open(f'{S}/report_disagree.md','w').write("\n".join(lines)); print("\n".join(lines))
to=sum(1 for f in canon_scored if P14(f)=='TIMEOUT'); oth=[(f,sc[(f,'jana2014')][2]) for f in canon_scored if P14(f)=='OTHER_ERROR']
print("canonical timeouts (jana2014):", to, "; leftover OTHER_ERROR:", len(oth), oth[:5])
agree=sum(1 for f in canon_scored if J(f)==P14(f)); print(f"agreement jana vs PyJanus(jana2014) on canonical files: {agree}/{len(canon_scored)} = {100*agree/len(canon_scored):.1f}%")
sb=sum(1 for f in canon_scored if J(f)=='SUCCESS'); pb=sum(1 for f in canon_scored if P14(f)=='SUCCESS'); print(f"canonical SUCCESS: jana {sb}, PyJanus {pb}")
