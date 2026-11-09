import json,collections,os,csv,sys
POOL={
 "Opus 4.8/high":["20260703_opus_high_basic19"],
 "Gemini-3-flash-preview":["20260609_gemini_gemini-3-flash-preview_paper19","20260610b_gemini_gemini-3-flash-preview_paper19","20260612_gemini_gemini-3-flash-preview_paper19","20260703_gemini_api_gemini-3-flash-preview_paper19_topup10","20260702_gemini_api_gemini-3-flash-preview_p17rle"],
 "GPT-5.4/low":["20260610b_codex_gpt-5.4_paper19"],
 "GPT-5.5/low":["20260610b_codex_gpt-5.5_paper19","20260703_codex_gpt-5.5_paper19_topup10"],
 "GPT-5.4-mini/low":["20260609_gpt-5.4-mini_low_paper19"],
 "Gemini-3.1-flash-lite":["20260610b_gemini_gemini-3.1-flash-lite_paper19","20260703_gemini_api_gemini-3.1-flash-lite_paper19_topup10"],
 "Haiku 4.5":["20260609_haiku_paper19","20260703_haiku_paper19_topup","20260703_haiku_paper19_topup10","20260703_haiku_paper19_topup10b"],
}
PROMPTS=["p01swap","p02swap","p03cycle3","p04cycle3","p05cycle3","p06cycle3","p07flipsign","p08max2","p09even","p10fact","p11gcd","p12fibp","p13rev","p14srchA","p15srchB","p16sqrt","p17rle","p18perm2code","p19fib"]
def ok(x): return x['status']=='SUCCESS' and x.get('clean',True) and not x.get('overfit',False)
out=csv.writer(open(sys.argv[1],'w')); out.writerow(["model","prompt","n_valid_trials","round0_success","final_success","round0_rate","final_rate","first10_success","first10_n"])
summary={}
for m,runs in POOL.items():
    trials=collections.OrderedDict()  # (run_idx, run, prompt, trial) -> {round: row}
    for ri,r in enumerate(runs):
        for l in open(f'260607/runs/{r}/log.jsonl'):
            x=json.loads(l); k=(ri,r,x['prompt_id'],x['trial'])
            trials.setdefault(k,{}).setdefault(x['round'],x)  # first attempt wins
    for p in PROMPTS:
        ts=[(k,v) for k,v in trials.items() if k[2]==p]
        valid=[(k,v) for k,v in ts if not all(x['status']=='GENERATION_FAIL' for x in v.values())]
        valid.sort(key=lambda kv:(kv[0][0],kv[0][3]))
        r0=sum(1 for k,v in valid if 0 in v and ok(v[0]))
        fin=sum(1 for k,v in valid if any(ok(x) for x in v.values()))
        f10=valid[:10]; f10s=sum(1 for k,v in f10 if any(ok(x) for x in v.values()))
        n=len(valid)
        out.writerow([m,p,n,r0,fin,f"{r0/n:.3f}" if n else "",f"{fin/n:.3f}" if n else "",f10s,len(f10)])
        summary[(m,p)]=(n,r0,fin,f10s,len(f10))
json.dump({f"{m}|{p}":v for (m,p),v in summary.items()}, open(sys.argv[1].replace('.csv','.json'),'w'))
# cross-check vs paper BASIC19_N10
N10={"Opus 4.8/high":[10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,4],
"GPT-5.4-mini/low":[10,10,10,10,10,10,10,10,10,10,3,6,10,3,8,3,0,0,0],
"GPT-5.4/low":[10,10,10,10,10,10,10,10,10,10,10,10,10,10,9,10,3,9,2],
"GPT-5.5/low":[9,10,10,10,10,10,10,10,10,10,8,9,10,10,10,10,1,8,0],
"Haiku 4.5":[9,10,10,10,10,10,10,10,10,9,3,1,4,0,3,7,0,0,0],
"Gemini-3-flash-preview":[10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,5],
"Gemini-3.1-flash-lite":[2,10,7,9,8,9,10,10,10,8,4,3,6,2,6,9,0,1,4]}
mism=0
for m in POOL:
    mine=[summary[(m,p)][3] for p in PROMPTS]
    diff=[(p,a,b) for p,a,b in zip(PROMPTS,mine,N10[m]) if a!=b]
    print(m, "first10 mine vs paper mismatches:", diff); mism+=len(diff)
print("total mismatches", mism)
