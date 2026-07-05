import json, glob
from collections import defaultdict

BASE="/home/tetsuo/dev/github.com/tetsuo-jp/gen_janus"
OUT="/tmp/claude-1000/-home-tetsuo-dev-overleaf-2025-gen-janus-prog-ipsj-pro/ae8922f4-512d-40ef-a41c-63f1e6ba70d2/scratchpad"

def load(path):
    out=[]
    for line in open(path):
        line=line.strip()
        if not line: continue
        try: out.append(json.loads(line))
        except: pass
    return out
def label(e): return e.get("prompt_id", e.get("task"))
def runs(patterns):
    e=[]
    for p in patterns:
        for f in glob.glob(f"{BASE}/{p}/log.jsonl"): e+=load(f)
    return e

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
    # group by (run_id, prompt_label, trial) so pooled runs never merge trials.
    trials=defaultdict(list)
    for e in entries: trials[(e.get("run_id"), label(e), e.get("trial"))].append(e)
    out=[]
    for (rid,lab,tr),rounds in trials.items():
        rounds=sorted(rounds, key=lambda r:r.get("round",0))
        task=rounds[0].get("task",lab); diff=rounds[0].get("difficulty",0)
        succ=next((r for r in rounds if r.get("status")=="SUCCESS"),None)
        if succ is not None:
            cutoff=succ.get("round",0)
            rr=[r for r in rounds if r.get("round",0)<=cutoff]
            cat="success"; clean=bool(succ.get("clean")); nround=cutoff
        else:
            last=rounds[-1]; rr=rounds
            cat=classify(last.get("status"), last.get("error")); clean=False; nround=last.get("round",0)
        # Generation timeout (counts as a FAILURE in the denominator): a claude-cli
        # subprocess that did not finish extended thinking within the limit
        # (Opus/Sonnet/Fable on bwt/heapify/perm_inverse etc.). This is a genuine
        # model-side failure defining the frontier.
        # In contrast, gemini-cli "timed out" is an INFRASTRUCTURE hang (the paper
        # documents this and re-ran gemini via API); such timeouts stay EXCLUDED as
        # backend failures, so first-5 selection uses the clean API re-run instead.
        last=rounds[-1]
        is_timeout = (cat=="backend" and last.get("backend")=="claude-cli"
                      and "timed out" in (last.get("error") or "").lower())
        ti=sum(r.get("tokens_in") or 0 for r in rr)
        to=sum(r.get("tokens_out") or 0 for r in rr)
        rt=sum(r.get("reasoning_tokens") or 0 for r in rr)
        out.append(dict(run_id=rid,trial=tr,label=lab,task=task,difficulty=diff,
                        cat=cat,clean=clean,is_timeout=is_timeout,ti=ti,to=to,rt=rt,nround=nround))
    return out

def rate_by(outs, keys, keyfn, cap=5):
    """Table 7/8/9 convention (timeout-as-failure). Cell = clean successes / (eligible trials).
       - Eligible = trials that are NOT a clear backend failure (rate limit / auth /
         CLI-API crash). Generation TIMEOUTS ARE eligible and count as failures.
       - Take the first `cap` (=5) eligible trials in (run_id, trial) order.
       - Denominator = number of eligible trials actually taken (<=5). We do NOT pad a
         task that was simply run fewer than 5 times up to 5 (that would misreport a
         3/3-clean task as 3/5=60% and contradict Table 8). Padding-to-5 only matters
         when >=5 attempts exist, which is already handled since timeouts are in-denominator.
       - rate=None only if there is no eligible (real) attempt at all."""
    per=defaultdict(list)
    for o in outs: per[keyfn(o)].append(o)
    result={}
    for k in keys:
        trials=sorted(per.get(k,[]), key=lambda o:(str(o.get("run_id")),
                      o.get("trial") if o.get("trial") is not None else 0))
        eligible=[o for o in trials if o["cat"]!="backend" or o.get("is_timeout")][:cap]
        if not eligible: result[k]=None; continue
        c=sum(1 for o in eligible if o["cat"]=="success" and o["clean"])
        result[k]=c/len(eligible)
    return result

EXTREME = {
 "Opus 4.8/high": ["260612/runs/20260613_claude_opus_hard2"],
 "Gemini-3-flash-preview": ["260612/runs/20260703_api_g3fp_hard2"],  # fill (2026-07-03)
 "Fable 5/low":   ["260612/runs/20260703_claude_fable5_low_hard2"],
 "Gemini-3.5-flash": ["260612/runs/20260624_api_gemini-3.5-flash_hard2"],
 "Sonnet 5/high": ["260612/runs/20260702_claude_sonnet5_hard2"],
 "GPT-5.4/low":   ["260612/runs/20260618_codex_gpt-5.4_hard2","260612/runs/20260702_codex_gpt-5.4_extreme3fill"],
 "GPT-5.5/low":   ["260612/runs/20260613_codex_gpt-5.5_hard2"],
 "Gemini-3.1-flash-lite": ["260612/runs/20260616_gemini_gemini-3.1-flash-lite_hard2"],
 "GPT-5.4-mini/low": ["260612/runs/20260618_codex_gpt-5.4-mini_hard2"],
 "Haiku 4.5":     ["260612/runs/20260613_claude_haiku_hard2"],
}
EXT_TASKS=["h2_zeckendorf","h2_cf_expand","h2_bitrev","h2_modinv","h2_mtf","h2_oesort",
           "h2_heapify","h2_lehmer_rank","h2_perm_inverse","h2_kmp_failure","h2_hilbert","h2_bwt"]
HARD = {
 "Opus 4.8/high": ["260612/runs/20260612_claude_opus_hard12"],
 "Gemini-3-flash-preview": ["260612/runs/20260612_gemini_gemini-3-flash-preview_hard12","260612/runs/20260702_api_gemini-3-flash-preview_hard12"],
 "GPT-5.4/low": ["260612/runs/20260612_codex_gpt-5.4_hard12"],
 "GPT-5.5/low": ["260612/runs/20260612_codex_gpt-5.5_hard12"],
 "Gemini-3.1-flash-lite": ["260612/runs/20260612_gemini_gemini-3.1-flash-lite_hard12"],
 "Gemini-2.5-flash": ["260612/runs/20260612_gemini_gemini-2.5-flash_hard12","260612/runs/20260702_api_gemini-2.5-flash_hard12"],
 "GPT-5.4-mini/low": ["260612/runs/20260612_gpt-5.4-mini_low_hard12"],
 "Haiku 4.5": ["260612/runs/20260612_claude_haiku_hard12"],
}
HARD_TASKS=["h_gray_encode","h_gray_decode","h_rotate_k","h_delta_encode","h_delta_decode",
            "h_bsort01","h_base3","h_cantor_pair","h_cantor_unpair","h_bingcd","h_merge_halves","h_modexp"]

def per_task_rate(outs, tasks):
    # heatmap basis: first 5 backend-valid trials per task (Convention B).
    return rate_by(outs, tasks, lambda o:o["task"], cap=5)

def failbreak(outs):
    c=defaultdict(int)
    for o in outs:
        k="success" if (o["cat"]=="success" and o["clean"]) else o["cat"]
        c[k]+=1
    return dict(c)

def tokenstats(outs):
    # exclude backend fails
    valid=[o for o in outs if o["cat"]!="backend"]
    succ=[o for o in valid if o["cat"]=="success" and o["clean"]]
    n_valid=len(valid); n_succ=len(succ)
    def mean(xs): return sum(xs)/len(xs) if xs else 0
    return dict(
        n_valid=n_valid, n_succ=n_succ,
        succ_rate=(n_succ/n_valid if n_valid else 0),
        tok_per_succ=(mean([o["ti"]+o["to"] for o in succ]) if succ else None),
        reason_per_succ=(mean([o["rt"] for o in succ]) if succ else None),
        rounds_per_succ=(mean([o["nround"] for o in succ]) if succ else None),
        tok_per_valid=mean([o["ti"]+o["to"] for o in valid]),
    )

data={"extreme":{}, "hard":{}}
for m,ps in EXTREME.items():
    outs=trial_outcomes(runs(ps))
    data["extreme"][m]={"rates":per_task_rate(outs,EXT_TASKS),"fail":failbreak(outs),"tok":tokenstats(outs)}
for m,ps in HARD.items():
    outs=trial_outcomes(runs(ps))
    data["hard"][m]={"rates":per_task_rate(outs,HARD_TASKS),"fail":failbreak(outs),"tok":tokenstats(outs)}
data["ext_tasks"]=EXT_TASKS; data["hard_tasks"]=HARD_TASKS
json.dump(data, open(f"{OUT}/agg_data.json","w"), indent=1)

# report token + fail tables
print("=== Extreme12 token stats ===")
print(f"{'model':22s} {'nsucc':>5} {'tok/succ':>9} {'reason/succ':>11} {'rounds/succ':>11}")
for m in EXTREME:
    t=data['extreme'][m]['tok']
    tp=f"{t['tok_per_succ']:.0f}" if t['tok_per_succ'] else "-"
    rp=f"{t['reason_per_succ']:.0f}" if t['reason_per_succ'] else "-"
    rd=f"{t['rounds_per_succ']:.2f}" if t['rounds_per_succ'] is not None else "-"
    print(f"{m:22s} {t['n_succ']:5d} {tp:>9} {rp:>11} {rd:>11}")
print("\n=== Extreme12 fail breakdown ===")
for m in EXTREME: print(f"{m:22s} {data['extreme'][m]['fail']}")

# ---- Basic19 canonical runs ----
BASIC = {
 "Opus 4.8/high": ["260607/runs/20260703_opus_high_basic19"],  # fill (2026-07-03, effort=high; replaces backend-failed 20260610b run)
 "GPT-5.5/low": ["260607/runs/20260610b_codex_gpt-5.5_paper19"],
 "GPT-5.4/low": ["260607/runs/20260610b_codex_gpt-5.4_paper19"],
 "Gemini-3-flash-preview": ["260607/runs/20260609_gemini_gemini-3-flash-preview_paper19","260607/runs/20260610b_gemini_gemini-3-flash-preview_paper19","260607/runs/20260612_gemini_gemini-3-flash-preview_paper19"],
 "Gemini-3.1-flash-lite": ["260607/runs/20260610b_gemini_gemini-3.1-flash-lite_paper19"],
 "GPT-5.4-mini/low": ["260607/runs/20260609_gpt-5.4-mini_low_paper19"],
 "Haiku 4.5": ["260607/runs/20260609_haiku_paper19"],
}
BASIC_TASKS=['p01swap','p02swap','p03cycle3','p04cycle3','p05cycle3','p06cycle3','p07flipsign','p08max2','p09even','p10fact','p11gcd','p12fibp','p13rev','p14srchA','p15srchB','p16sqrt','p17rle','p18perm2code','p19fib']

def per_label_rate(entries, tasks):
    # Basic19: key by prompt_id (label). First 5 backend-valid trials per prompt.
    return rate_by(trial_outcomes(entries), tasks, lambda o:o["label"], cap=5)

data["basic"]={}
for m,ps in BASIC.items():
    data["basic"][m]=per_label_rate(runs(ps), BASIC_TASKS)
data["basic_tasks"]=BASIC_TASKS
json.dump(data, open(f"{OUT}/agg_data.json","w"), indent=1)

print("\n===== BASIC19 clean-success rate (%) =====")
short=[t[3:] for t in BASIC_TASKS]
print("model".ljust(22), " ".join(s[:5].rjust(5) for s in short))
for m in BASIC:
    r=data["basic"][m]
    print(m.ljust(22), " ".join((("  - " if r[t] is None else f"{100*r[t]:4.0f}").rjust(5)) for t in BASIC_TASKS))
