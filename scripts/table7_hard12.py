#!/usr/bin/env python3
"""Recompute Table 7 (Hard12 total X/N) under the EXACT table89 convention:
first-CAP backend-valid trials per task, deficit -> timeout(failure), X/(12*CAP) total.
gemini models use API-only runs (matching the 表7 note). Also emits per-task
clean/CAP for regenerating fig4 heatmap Hard12 block.
2026-07-05: CAP=10 (20260704_topup10h_* を追加)。CAP=5 で旧表を再現可能。"""
import json, os, math
from collections import defaultdict
CAP=10
def wilson(x,n,z=1.96):
    p=x/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0.0,c-h), min(1.0,c+h))
BASE="/home/tetsuo/dev/github.com/tetsuo-jp/gen_janus"
HARD_TASKS=["h_gray_encode","h_gray_decode","h_rotate_k","h_delta_encode","h_delta_decode",
            "h_bsort01","h_base3","h_cantor_pair","h_cantor_unpair","h_bingcd","h_merge_halves","h_modexp"]
def load(path):
    rows=[]; fp=os.path.join(BASE,path,"log.jsonl")
    if not os.path.exists(fp): return rows
    for l in open(fp):
        l=l.strip()
        if l: rows.append(json.loads(l))
    return rows
def label(e): return e.get("prompt_id", e.get("task"))
def runs(ps):
    out=[]
    for p in ps: out.extend(load(p))
    return out
def trial_outcomes(entries):
    trials=defaultdict(list)
    for e in entries: trials[(e.get("run_id"), label(e), e.get("trial"))].append(e)
    out=[]
    for (rid,lab,tr),rounds in trials.items():
        rounds=sorted(rounds, key=lambda r:r.get("round",0))
        task=rounds[0].get("task",lab)
        succ=next((r for r in rounds if r.get("status")=="SUCCESS"),None)
        if succ is not None: cat="success"; clean=bool(succ.get("clean"))
        else: cat="fail"; clean=False
        out.append(dict(run_id=rid,trial=tr,task=task,cat=cat,clean=clean,
                        backend=all(r.get("status")=="GENERATION_FAIL" for r in rounds)))
    return out
def first5(outs, task):
    ts=[o for o in outs if o["task"]==task]
    ts.sort(key=lambda o:(str(o.get("run_id")), o.get("trial") if o.get("trial") is not None else 0))
    return [o for o in ts if not o["backend"]][:CAP]
MODELS={
 "Opus 4.8/high": ["260612/runs/20260612_claude_opus_hard12","260612/runs/20260704_topup10h_opus_hard12"],
 "Gemini-3-flash-preview": ["260612/runs/20260702_api_gemini-3-flash-preview_hard12","260612/runs/20260704_topup10h_g3fp_hard12"],  # API only
 "GPT-5.4/low": ["260612/runs/20260612_codex_gpt-5.4_hard12"],
 "GPT-5.5/low": ["260612/runs/20260612_codex_gpt-5.5_hard12"],
 "Gemini-3.1-flash-lite": ["260612/runs/20260612_gemini_gemini-3.1-flash-lite_hard12"],
 "Gemini-2.5-flash": ["260612/runs/20260702_api_gemini-2.5-flash_hard12","260612/runs/20260704_topup10h_g25f_hard12","260612/runs/20260704_topup10h_g25f_hard12b"],  # API only
 "GPT-5.4-mini/low": ["260612/runs/20260612_gpt-5.4-mini_low_hard12","260612/runs/20260704_topup10h_gpt54mini_hard12"],
 "Haiku 4.5": ["260612/runs/20260612_claude_haiku_hard12","260612/runs/20260704_topup10h_haiku_hard12"],
}
CURRENT={"Opus 4.8/high":59,"Gemini-3-flash-preview":55,"GPT-5.4/low":48,"GPT-5.5/low":49,
         "Gemini-3.1-flash-lite":38,"Gemini-2.5-flash":24,"GPT-5.4-mini/low":25,"Haiku 4.5":17}  # 表7 n=5 掲載値
print(f"{'model':24s} {'new X/60':>9} {'%':>5}  {'current':>7}  diff  per-task valid(n<5?)")
rates_out={}
for m,ps in MODELS.items():
    outs=trial_outcomes(runs(ps))
    total=0; pertask={}; short_tasks=[]
    for t in HARD_TASKS:
        v=first5(outs,t)
        clean=sum(1 for o in v if o["cat"]=="success" and o["clean"])
        total+=clean
        pertask[t]=clean/float(CAP)
        if len(v)<CAP: short_tasks.append(f"{t[2:]}={len(v)}")
    rates_out[m]=pertask
    n=12*CAP
    lo,hi=wilson(total,n)
    print(f"{m:24s} {total:5d}/{n}  {100*total/n:4.0f}%  CI[{lo*100:.0f},{hi*100:.0f}]  (n=5値:{CURRENT[m]}/60)  {short_tasks if short_tasks else 'all full'}")
# emit per-task rates JSON for fig4
import json as J
J.dump(rates_out, open("/tmp/claude-1000/hard12_rates_new.json","w"))
print("\nper-task rates -> /tmp/claude-1000/hard12_rates_new.json")
