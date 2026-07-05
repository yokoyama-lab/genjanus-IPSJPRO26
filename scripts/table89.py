#!/usr/bin/env python3
"""Uniform-N recompute of Table 8 (macro) and Table 9 (fail breakdown),
replicating fig/dump.py classify() + trial_outcomes() exactly, with
denominator fixed at CAP per task (first-CAP backend-valid; deficits -> timeout).

2026-07-04: CAP=10 (n=10化; 20260704_topup10_* run を追加)。CAP=5 で旧表(n=5)を再現可能。
G3fp のみ有効試行が各タスク7のため MODEL_CAP で cap=7（分母84）。"""
import json, collections, os, math
from collections import defaultdict

BASE="/home/tetsuo/dev/github.com/tetsuo-jp/gen_janus"
EXT_TASKS=["h2_zeckendorf","h2_cf_expand","h2_bitrev","h2_modinv","h2_mtf","h2_oesort",
           "h2_heapify","h2_lehmer_rank","h2_perm_inverse","h2_kmp_failure","h2_hilbert","h2_bwt"]
CAP=10

# ---- verbatim from fig/dump.py ----
def load(path):
    rows=[]
    fp=os.path.join(BASE,path,"log.jsonl")
    if not os.path.exists(fp): return rows
    for l in open(fp):
        l=l.strip()
        if l: rows.append(json.loads(l))
    return rows
def label(e): return e.get("prompt_id", e.get("task"))
def runs(patterns):
    out=[]
    for p in patterns: out.extend(load(p))
    return out
def classify(status, error):
    e=error or ""
    if status=="GENERATION_FAIL": return "backend"
    if status=="SUCCESS": return "success"
    if status=="SYNTAX_ERROR" or "parsing error" in e or "Expecting identifier" in e or "Expecting statement" in e or "has not been declared" in e:
        return "syntax"
    if "Division remains" in e or "for local" in e or "Variable names does not match" in e:
        return "irreversible"
    if status=="WRONG_OUTPUT" or "Assertion failed" in e or "Passed case" in e or "Expected s=" in e or "got s=" in e:
        return "wrong"
    return "runtime"
def trial_outcomes(entries):
    trials=defaultdict(list)
    for e in entries: trials[(e.get("run_id"), label(e), e.get("trial"))].append(e)
    out=[]
    for (rid,lab,tr),rounds in trials.items():
        rounds=sorted(rounds, key=lambda r:r.get("round",0))
        task=rounds[0].get("task",lab); diff=rounds[0].get("difficulty",0)
        succ=next((r for r in rounds if r.get("status")=="SUCCESS"),None)
        if succ is not None:
            cat="success"; clean=bool(succ.get("clean")); nround=succ.get("round",0)
        else:
            last=rounds[-1]
            cat=classify(last.get("status"), last.get("error")); clean=False; nround=last.get("round",0)
        out.append(dict(run_id=rid,trial=tr,label=lab,task=task,difficulty=diff,cat=cat,clean=clean))
    return out
# ---- end verbatim ----

def firstN_valid_by_task(outs, task, cap):
    # order by (run_id, trial); valid = cat != backend ; take first cap
    trials=[o for o in outs if o["task"]==task]
    trials.sort(key=lambda o:(str(o.get("run_id")), o.get("trial") if o.get("trial") is not None else 0))
    valid=[o for o in trials if o["cat"]!="backend"][:cap]
    return valid

def wilson(x, n, z=1.96):
    if n==0: return (0.0,0.0)
    p=x/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0.0,c-h), min(1.0,c+h))

# category -> table9 column
COL={"success":"succ","wrong":"wrong","irreversible":"irrev","runtime":"runtime","syntax":"syntax"}

def model_tables(patterns, cap):
    outs=trial_outcomes(runs(patterns))
    per_task_rate={}
    fail=collections.Counter()
    for t in EXT_TASKS:
        v=firstN_valid_by_task(outs,t,cap)
        clean=sum(1 for o in v if o["cat"]=="success" and o["clean"])
        per_task_rate[t]=clean/float(cap)   # denominator fixed at cap (0-fill deficits)
        # table9 categories
        for o in v:
            if o["cat"]=="success" and o["clean"]:
                fail["succ"]+=1
            elif o["cat"]=="success" and not o["clean"]:
                # success but overfit/not-clean -> count as wrong (not a clean success)
                fail["wrong"]+=1
            else:
                fail[COL.get(o["cat"],"runtime")]+=1
        deficit=cap-len(v)
        fail["timeout"]+=deficit
    macro=sum(per_task_rate.values())/len(EXT_TASKS)*100
    return macro, per_task_rate, fail

MODELS={
 "Opus 4.8/high": ["260612/runs/20260613_claude_opus_hard2","260612/runs/20260703_topup_opus_hard2","260612/runs/20260703_topup_opus_hard2b","260612/runs/20260704_topup10_opus_hard2"],
 "Fable 5/low": ["260612/runs/20260703_claude_fable5_low_hard2","260612/runs/20260704_topup10_fable5_hard2"],
 "Gemini-3.5-flash": ["260612/runs/20260624_api_gemini-3.5-flash_hard2","260612/runs/20260704_topup10_g35flash_hard2"],
 "Sonnet 5/high": ["260612/runs/20260702_claude_sonnet5_hard2","260612/runs/20260703_topup_sonnet5_hard2","260612/runs/20260704_topup10_sonnet5_hard2"],
 "GPT-5.4/low": ["260612/runs/20260618_codex_gpt-5.4_hard2","260612/runs/20260703_topup_gpt54_hard2","260612/runs/20260704_topup10_gpt54_hard2"],
 "GPT-5.5/low": ["260612/runs/20260613_codex_gpt-5.5_hard2"],
 "Gemini-3-flash-preview": ["260612/runs/20260703_api_g3fp_hard2","260612/runs/20260704_topup10_g3fp_hard2"],
 "Gemini-3.1-flash-lite": ["260612/runs/20260616_gemini_gemini-3.1-flash-lite_hard2"],
 "GPT-5.4-mini/low": ["260612/runs/20260618_codex_gpt-5.4-mini_hard2"],
 "Haiku 4.5": ["260612/runs/20260613_claude_haiku_hard2"],
}
# 2026-07-05: G3fp も topup10 で n=10 化済み（cap 例外なし）
MODEL_CAP={}
ORDER=list(MODELS)

if __name__=="__main__":
    print(f"=== TABLE 8: macro (uniform-{CAP*12}) + per-task clean/cap + Wilson95 ===")
    results={}
    for m in ORDER:
        cap=MODEL_CAP.get(m,CAP)
        macro,rates,fail=model_tables(MODELS[m],cap)
        results[m]=(macro,rates,fail,cap)
        x=fail['succ']; n=cap*12
        lo,hi=wilson(x,n)
        print(f"\n{m:24s} cap={cap} MACRO={macro:5.1f}%  clean={x}/{n}  Wilson95=[{lo*100:.0f}, {hi*100:.0f}]")
        for t in EXT_TASKS:
            print(f"    {t:16s} {int(round(rates[t]*cap))}/{cap} = {rates[t]*100:5.1f}%")
    print("\n\n=== TABLE 9: fail breakdown (row sum must = 12*cap) ===")
    print(f"{'model':24s} {'succ':>4} {'wrong':>5} {'irrev':>5} {'run':>4} {'syn':>4} {'TO':>4} {'sum':>4}")
    for m in ORDER:
        _,_,f,cap=results[m]
        s=f['succ']; w=f['wrong']; ir=f['irrev']; ru=f['runtime']; sy=f['syntax']; to=f['timeout']
        tot=s+w+ir+ru+sy+to
        print(f"{m:24s} {s:4d} {w:5d} {ir:5d} {ru:4d} {sy:4d} {to:4d} {tot:4d}")
    print("\n=== LaTeX rows (モデル & マクロ% & [CI]) ===")
    for m in ORDER:
        macro,_,f,cap=results[m]
        x=f['succ']; n=cap*12
        lo,hi=wilson(x,n)
        print(f"    {m} & {macro:.1f}\\% & [{lo*100:.0f}, {hi*100:.0f}] \\\\  % {x}/{n}")
