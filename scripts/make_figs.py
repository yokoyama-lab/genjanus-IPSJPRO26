#!/usr/bin/env python3
"""Generate 4 figures (vector PDF) + 2 LaTeX tables for the gen_janus paper.
Real data only. Aggregation from agg_data.json (produced by dump.py) + paper tables.
Run with the matplotlib venv:
  /home/tetsuo/dev/github.com/tetsuo-jp/gen_janus/260612/.venv/bin/python make_figs.py
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG  = "/home/tetsuo/dev/overleaf/2025_gen_janus_prog_ipsj_pro/fig"
os.makedirs(FIG, exist_ok=True)
D = json.load(open(f"{HERE}/agg_data.json"))

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.titlesize": 11, "axes.labelsize": 10,
    "legend.fontsize": 8.5, "xtick.labelsize": 8.5, "ytick.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})
# categorical hues (validated reference palette)
BLUE="#2a78d6"; AQUA="#1baf7a"; YEL="#eda100"; GREEN="#008300"
VIOL="#4a3aa7"; RED="#e34948"; MAG="#e87ba4"; ORNG="#eb6834"; GREY="#8a8a86"

# ---- Basic19 clean-success at n=10: single source of truth shared by fig_v0v2_grid (Fig.1)
#      and fig_heatmap (Fig.4) so the two figures can never disagree. (success counts, denominators).
#      n=10 everywhere EXCEPT: Opus 4.8/high p19fib = n=4 (only 4 backend-valid trials exist).
#      Haiku 4.5 reached n=10 on 2026-07-04 via topup run 20260703_haiku_paper19_topup10b.
#      Sources: 260607/runs/*_paper19 (+ 2026-07-03 topup10 runs for GPT-5.5 / Gemini-3.1-flash-lite,
#      opus fill 20260703_opus_high_basic19). Same "first-N backend-valid trials" convention as the paper.
BASIC19_PROMPTS = ["p01 swap","p02 swap","p03 cycle3","p04 cycle3","p05 cycle3","p06 cycle3",
    "p07 flipsign","p08 max2","p09 even","p10 fact","p11 gcd","p12 fibp",
    "p13 rev","p14 srchA","p15 srchB","p16 sqrt","p17 rle","p18 perm2code","p19 fib"]
BASIC19_N10 = {  # short model key -> (success counts, denominators) over the 19 prompts
 "Opus 4.8/high":         ([10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10, 4],[10]*18+[4]),
 "GPT-5.4-mini/low":      ([10,10,10,10,10,10,10,10,10,10, 3, 6,10, 3, 8, 3, 0, 0, 0],[10]*19),
 "GPT-5.4/low":           ([10,10,10,10,10,10,10,10,10,10,10,10,10,10, 9,10, 3, 9, 2],[10]*19),
 "GPT-5.5/low":           ([ 9,10,10,10,10,10,10,10,10,10, 8, 9,10,10,10,10, 1, 8, 0],[10]*19),
 "Haiku 4.5":             ([ 9,10,10,10,10,10,10,10,10, 9, 3, 1, 4, 0, 3, 7, 0, 0, 0],[10]*19),
 "Gemini-3-flash-preview":([10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10, 5],[10]*19),
 "Gemini-3.1-flash-lite": ([ 2,10, 7, 9, 8, 9,10,10,10, 8, 4, 3, 6, 2, 6, 9, 0, 1, 4],[10]*19),
}
def basic19_rate(model):
    c,n = BASIC19_N10[model]
    return [100.0*ci/ni for ci,ni in zip(c,n)]

# ---- Hard12 per-task clean/10 rate under the unified table89 convention (first-10 valid,
#      deficit->timeout; gemini API-only). 2026-07-05 n=10化 (20260704_topup10h_* を含む)。
#      Totals match Table tab:hard12 (115/111/94/95/68/39/43/31 per 120).
#      2026-07-07 監査対応: 初回完走attempt優先で mini 45->39, Haiku 32->31 に訂正。
#      Source: scripts/table7_hard12.py (CAP=10). Task order = D["hard_tasks"].
HARD12_RATES = {
  "Opus 4.8/high":         [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5],
  "Gemini-3-flash-preview":[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1],
  "GPT-5.4/low":           [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.5, 0.9, 0.0],
  "GPT-5.5/low":           [1.0, 0.8, 0.9, 1.0, 1.0, 0.7, 1.0, 0.2, 0.7, 1.0, 1.0, 0.2],
  "Gemini-3.1-flash-lite": [1.0, 0.3, 0.1, 1.0, 0.9, 0.1, 0.3, 0.9, 0.9, 0.2, 0.6, 0.5],
  "GPT-5.4-mini/low":      [0.9, 0.4, 0.4, 0.8, 0.5, 0.0, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2],
  "Gemini-2.5-flash":      [1.0, 0.3, 0.4, 0.8, 0.8, 0.0, 0.0, 0.0, 0.1, 0.1, 0.2, 0.6],
  "Haiku 4.5":             [1.0, 0.2, 0.3, 0.3, 0.5, 0.0, 0.0, 0.1, 0.2, 0.2, 0.3, 0.0],
}
# ---- Extreme12 per-task clean rate via table89.model_tables (authoritative; topup pools).
#      2026-07-04/05 n=10化 (first-10 valid; 20260704_topup10_* を含む。G3fp も 07-05 に n=10 到達)。
#      Totals/macro match Table tab:extreme12 & Fig fig:failtypes. G3fp from its own hard2 run.
#      Task order = D["ext_tasks"]. Source: scripts/table89.py (CAP=10).
EXT12_RATES = {
  "Opus 4.8/high":         [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4, 0.9, 1.0, 0.4, 1.0, 0.8],
  "Gemini-3-flash-preview":[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.8, 0.1, 0.2, 0.9, 0.0],
  "GPT-5.4/low":           [0.7, 0.4, 0.8, 0.8, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.4, 0.0],
  "GPT-5.5/low":           [0.3, 1.0, 1.0, 0.4, 0.9, 0.7, 0.1, 0.7, 0.0, 0.1, 0.4, 0.0],
  "Gemini-3.1-flash-lite": [0.0, 0.5, 0.3, 0.0, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  "GPT-5.4-mini/low":      [0.0, 0.4, 0.1, 0.1, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # bwt 2/10->0/10 (2026-07-07 監査: フィードバック逐次暗記を除外)
  # G2.5f: API runは全タスクGF, cli runも8/12タスクでGF全滅。有効試行が得られた4タスク(zeck21/cf8/bitrev7/bwt30, first-10で分母7〜10)のみ表示, クリーン成功は全て0。他はNaN=灰色(測定不能, 表6除外)
  "Gemini-2.5-flash":      [0.0, 0.0, 0.0, float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), 0.0],
  "Haiku 4.5":             [0.0, 0.0, 0.3, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0],
}

# ============================================================ Figure 1
# Monochrome: unique (linestyle, marker) per task + two gray levels.
K="black"; G="0.45"
DASHDOTDOT=(0,(3,1,1,1,1,1))
def fig_selfrefine():
    rounds = list(range(6))
    #  label               values                     color ls           marker
    curves = {   # from Table 6 (GPT-5.4-mini, n=20). Converging=solid/dashed, stagnant=dotted.
        "p01 swap":      ([10,30,55,70,90,100], K, "-",          "o"),
        "p13 rev":       ([5,20,50,70,85,85],   G, "-",          "s"),
        "p15 srchB":     ([10,20,35,45,45,60],  K, "--",         "^"),
        "p12 fibp":      ([0,10,20,30,30,40],   G, "--",         "D"),
        "p16 sqrt":      ([25,30,30,40,40,40],  K, "-.",         "v"),
        "p11 gcd":       ([5,10,15,20,30,35],   G, "-.",         "P"),
        "p18 perm2code": ([0,0,0,5,5,5],        K, ":",          "X"),
        "p17 rle":       ([0,0,0,0,0,0],        G, ":",          "*"),
        "p19 fib":       ([0,0,0,0,0,0],        K, DASHDOTDOT,   "d"),
    }
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for name,(y,c,ls,mk) in curves.items():
        ax.plot(rounds, y, color=c, linestyle=ls, marker=mk, ms=6.5, lw=1.8,
                label=name, markerfacecolor=c, markeredgecolor="white",
                markeredgewidth=0.7, clip_on=False, zorder=3)
    ax.set_xlabel("self-refine round")
    ax.set_ylabel("Cumulative success (%)")
    ax.set_xlim(0,5); ax.set_ylim(-2,103)
    ax.set_xticks(rounds); ax.set_yticks(range(0,101,20))
    ax.grid(axis="y", color="0.85", lw=0.7, zorder=0)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01,1.0), frameon=False,
              handlelength=3.0, title="Task (converging solid/dashed,\nstagnant dotted)",
              title_fontsize=8.5)
    fig.savefig(f"{FIG}/fig_selfrefine.pdf")
    plt.close(fig); print("wrote fig_selfrefine.pdf")

# ============================================================ Figure 2  heatmap
def _viridis_gray():
    # viridis is perceptually uniform -> monotone luminance under grayscale print.
    base = plt.get_cmap("viridis")
    cmap = base.copy(); cmap.set_bad("0.75")   # NaN = mid gray
    return cmap

def fig_heatmap():
    # X labels in "p01 swap" form. Basic19 uses real prompt ids (p01..p19);
    # Hard12 -> sequential h01..h12; Extreme12 -> sequential e01..e12.
    basic_lbl = [f"{t[:3]} {t[3:]}" for t in D["basic_tasks"]]           # p01swap -> "p01 swap"
    hard_lbl  = [f"h{i+1:02d} {t[2:]}" for i,t in enumerate(D["hard_tasks"])]   # h_gray_encode -> "h01 gray_encode"
    ext_lbl   = [f"e{i+1:02d} {t[3:]}" for i,t in enumerate(D["ext_tasks"])]    # h2_zeckendorf -> "e01 zeckendorf"
    # Basic19 block removed 2026-07-04 (now fully shown in fig_v0v2_grid with the same 7 models)
    blocks = [
        ("Hard12",  "hard",  D["hard_tasks"],  hard_lbl),
        ("Extreme12","extreme", D["ext_tasks"], ext_lbl),
    ]
    # success-descending by Hard12 totals (59,55,49,48,38,25,17)
    models = ["Opus 4.8/high","Gemini-3-flash-preview","GPT-5.5/low","GPT-5.4/low",
              "Gemini-3.1-flash-lite","GPT-5.4-mini/low","Gemini-2.5-flash","Haiku 4.5"]
    cmap = _viridis_gray()
    fig = plt.figure(figsize=(8.4, 3.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[12,12], wspace=0.06)
    axes=[]
    for bi,(title,key,tasks,short) in enumerate(blocks):
        ax = fig.add_subplot(gs[0,bi]); axes.append(ax)
        M = np.full((len(models), len(tasks)), np.nan)
        for i,m in enumerate(models):
            if key == "basic":  # Basic19 at n=10 from the shared source (matches Fig. fig:v0v2grid)
                M[i,:] = basic19_rate(m)
                continue
            if key == "hard":   # Hard12 under unified table89 convention (matches Table tab:hard12)
                M[i,:] = [100.0*x for x in HARD12_RATES[m]]
                continue
            if key == "extreme":  # Extreme12 via table89 (matches Table tab:extreme12 / Fig fig:failtypes)
                M[i,:] = [100.0*x for x in EXT12_RATES[m]]
                continue
            row = D[key].get(m, {})
            if isinstance(row, dict) and "rates" in row:  # hard/extreme nest under "rates"
                row = row["rates"]
            for j,t in enumerate(tasks):
                v = row.get(t)
                if v is not None: M[i,j] = 100*v
        im = ax.imshow(np.ma.masked_invalid(M), cmap=cmap, vmin=0, vmax=100,
                       aspect="auto")
        # numeric annotation in every valid cell (text color chosen for contrast)
        fs = 5.2 if len(tasks) > 12 else 6.2
        for i in range(len(models)):
            for j in range(len(tasks)):
                v = M[i,j]
                if np.isnan(v): continue
                txt = f"{v:.0f}"
                tc = "white" if v < 55 else "black"   # viridis: <55 dark -> white text
                ax.text(j, i, txt, ha="center", va="center", fontsize=fs, color=tc)
        ax.set_xticks(range(len(tasks)))
        ax.set_xticklabels(short, rotation=90, fontsize=7)
        ax.set_title(title, fontsize=10.5, pad=5)
        ax.set_yticks(range(len(models)))
        if bi==0:
            ax.set_yticklabels(models, fontsize=8.5)
        else:
            ax.set_yticklabels([])
        ax.set_xticks(np.arange(-.5,len(tasks),1), minor=True)
        ax.set_yticks(np.arange(-.5,len(models),1), minor=True)
        ax.grid(which="minor", color="white", lw=1.1)
        ax.tick_params(which="both", length=0)
    cbar = fig.colorbar(im, ax=axes, fraction=0.018, pad=0.012)
    cbar.set_label("Clean-success rate (%)", fontsize=9)
    fig.savefig(f"{FIG}/fig_heatmap.pdf")
    plt.close(fig); print("wrote fig_heatmap.pdf")

# ============================================================ Figure 3 failtypes
# Monochrome: gray level + hatch pattern per category (double-encoded).
# Confirmed Table 9 (V2 Extreme12, uniform 10 valid trials x 12 tasks = 120 per model;
# 全モデル 10x12=120)。2026-07-04/05 n=10化 (scripts/table89.py CAP=10)。
# Order (macro desc) and counts are the vetted table values; rows sum to 120.
# Plot は割合(%)表示。
#   category  label        gray     hatch    counts per model (see FT9_MODELS order)
FT9_MODELS = ["Fable 5/low","Opus 4.8/high","Gemini-3.5-flash","Sonnet 5/high",
              "Gemini-3-flash-preview",
              "GPT-5.4/low","GPT-5.5/low","Gemini-3.1-flash-lite",
              "GPT-5.4-mini/low","Haiku 4.5"]
FT9_CATS = [  # (label, gray, hatch)
    ("Success",     "0.92", ""),
    ("Wrong output","0.68", "//"),
    ("Irreversible","0.45", "xx"),
    ("Runtime",     "0.58", ".."),
    ("Syntax",      "0.28", "\\\\"),
    ("Timeout",     "0.80", "++"),
]
FT9 = {  # counts in category order: success, wrong, irreversible, runtime, syntax, timeout
 "Fable 5/low":          [112, 0, 0, 0, 0, 8],
 "Opus 4.8/high":        [105, 0, 0, 0, 0,15],
 "Gemini-3.5-flash":     [102, 6, 4, 3, 5, 0],
 "Sonnet 5/high":        [ 82, 0, 0, 0, 0,38],
 "Gemini-3-flash-preview":[80, 2,14, 3,21, 0],
 "GPT-5.4/low":          [ 61,30,17, 6, 6, 0],
 "GPT-5.5/low":          [ 56,39,11, 9, 5, 0],
 "Gemini-3.1-flash-lite":[ 11,54,14,13,28, 0],
 "GPT-5.4-mini/low":     [  9,44,23,17,27, 0],  # 2026-07-07 監査訂正 (逐次暗記2件を wrong へ)
 "Haiku 4.5":            [  5,37,20,11,47, 0],  # 2026-07-07 監査訂正 (初回attempt採用で分類1件移動)
}
def fig_failtypes():
    import matplotlib.patches as mpatches
    order = FT9_MODELS  # already success-descending, matching Table 9
    plt.rcParams["hatch.linewidth"] = 0.6
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    y = np.arange(len(order))
    left = np.zeros(len(order))
    handles=[]
    totals = {m: float(sum(FT9[m])) for m in order}
    for ci,(lab,gray,hatch) in enumerate(FT9_CATS):
        vals = np.array([100.0*FT9[m][ci]/totals[m] for m in order], dtype=float)
        ax.barh(y, vals, left=left, facecolor=gray, hatch=hatch, label=lab,
                height=0.72, edgecolor="black", linewidth=0.9)
        handles.append(mpatches.Patch(facecolor=gray, hatch=hatch,
                                      edgecolor="black", linewidth=0.9, label=lab))
        left += vals
    ax.set_yticks(y); ax.set_yticklabels(order, fontsize=8.7)
    ax.invert_yaxis()
    ax.set_xlabel("Share of trials (%) (n = 120 per model: 10 valid trials $\\times$ 12 tasks)")
    ax.set_xlim(0,100); ax.set_xticks(range(0,101,10))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5,-0.14),
              ncol=3, frameon=False, fontsize=8.3, handleheight=1.6, handlelength=2.4)
    ax.tick_params(length=0)
    for s in ("left",): ax.spines[s].set_visible(False)
    fig.savefig(f"{FIG}/fig_failtypes.pdf")
    plt.close(fig); print("wrote fig_failtypes.pdf")

# ============================================================ Figure 4  V0->V2
def fig_v0v2():
    # V0 = gpt-5.2 (n=100, pass@1). V2 = GPT-5.4/low (n=10; same first-10-valid pool as Fig. fig:v0v2grid).
    # v2_r0 = round-0 clean successes (pass@1); v2 = final (+self-refine). Decomposes model progress vs repair.
    # labels carry the Basic19 prompt number of each task (swap=BNF p02, etc.).
    tasks = ["p02 swap","p03 cycle3","p07 flipsign","p08 max2","p09 even","p10 fact",
             "p11 gcd","p12 fibp","p13 rev","p15 srchB","p16 sqrt","p17 rle","p18 perm2code","p19 fib"]
    v0    = [95,9,5,32,94,16, 0,0,0,0,0,0,0,0]
    v2_r0 = [100,100,100,100,90,100, 70,80,90,60,40,0,40,10]
    v2    = [100,100,100,100,100,100, 100,100,100,90,100,30,90,20]
    plt.rcParams["hatch.linewidth"] = 0.6
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    x = np.arange(len(tasks)); w=0.27
    ax.bar(x-w, v0, w, facecolor="0.88", hatch="///", edgecolor="black", linewidth=0.9,
           label="V0  gpt-5.2 (2025-12, pass@1)", zorder=3)
    ax.bar(x, v2_r0, w, facecolor="0.60", hatch="..", edgecolor="black", linewidth=0.9,
           label="V2  GPT-5.4/low (2026-06, pass@1)", zorder=3)
    ax.bar(x+w, v2, w, facecolor="0.30", hatch="", edgecolor="black", linewidth=0.9,
           label="V2  GPT-5.4/low (2026-06, +self-refine)", zorder=3)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=45, ha="right", fontsize=8.5)
    ax.set_ylabel("Success rate (%)"); ax.set_ylim(0,108)
    ax.set_yticks(range(0,101,20))
    ax.grid(axis="y", color="0.85", lw=0.7, zorder=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5,1.16), ncol=1,
              frameon=False, fontsize=8.6, handleheight=1.4, handlelength=2.2)
    ax.tick_params(length=0)
    fig.savefig(f"{FIG}/fig_v0v2.pdf")
    plt.close(fig); print("wrote fig_v0v2.pdf")

# ============================================================ Figure 5  merged V0 (Table 4) + V2 Basic19 (Table 5)
def fig_v0v2_grid():
    # One heatmap merging Table 4 (V0, 3 models, n=100, %) and Table 5 (V2 Basic19,
    # 6 models, count -> %). Rows = models (V0 block of 3 above V2 block of 6);
    # columns = the 19 Basic19 prompts. Cell = clean-success rate (%). Grayscale-safe.
    prompts = BASIC19_PROMPTS
    # --- V0 rows: values are already percentages out of 100 ---
    v0 = {
        "gpt-5.2":    [0,95, 9, 8,36,36, 5,32,94,16, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "gpt-4.1":    [0,81,26,33,17,21, 7,23,78,13, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "gpt-5-nano": [0,94,72,76,67,69,12,35,61, 6, 0, 2, 6, 0, 0, 0, 0,13, 0],
    }
    # --- V2 rows: (display label, BASIC19_N10 key); numbers come from the shared source ---
    # success-descending by Basic19 totals: 99.5, 97.4, 91.1, 86.8, 70.0, 62.1, 61.1 (%)
    v2_display = [("Claude Opus 4.8/high","Opus 4.8/high"),
                  ("Gemini-3-flash-preview","Gemini-3-flash-preview"),
                  ("GPT-5.4/low","GPT-5.4/low"),
                  ("GPT-5.5/low","GPT-5.5/low"),
                  ("GPT-5.4-mini/low","GPT-5.4-mini/low"),
                  ("Gemini-3.1-flash-lite","Gemini-3.1-flash-lite"),
                  ("Claude Haiku 4.5","Haiku 4.5")]
    v0_models = list(v0.keys())
    v2_models = [disp for disp,_ in v2_display]
    # V2 on TOP, V0 on BOTTOM (failures gravitate to the lower block)
    models = v2_models + v0_models
    n_v2 = len(v2_models)
    M = np.zeros((len(models), len(prompts)))
    for k,(disp,key) in enumerate(v2_display):
        M[k,:] = basic19_rate(key)
    for i,m in enumerate(v0_models):
        M[n_v2+i,:] = v0[m]
    cmap = _viridis_gray()
    fig, ax = plt.subplots(figsize=(12.4, 5.0))
    ax.imshow(M, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(len(models)):
        for j in range(len(prompts)):
            v = M[i,j]
            tc = "white" if v < 55 else "black"
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6.2, color=tc)
    ax.set_xticks(range(len(prompts)))
    ax.set_xticklabels(prompts, rotation=90, fontsize=7.5)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=8.6)
    ax.set_xticks(np.arange(-.5, len(prompts), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(models), 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.1)
    ax.tick_params(which="both", length=0)
    # thick divider between the V2 block (top) and V0 block (bottom)
    ax.axhline(n_v2-0.5, color="black", lw=2.6)
    # generation brackets on the far left
    ax.text(-1.4, (n_v2-1)/2.0, "V2 Basic19\n(n=10)", ha="center", va="center",
            fontsize=9, fontweight="bold", rotation=90)
    ax.text(-1.4, n_v2+(len(v0_models)-1)/2.0, "V0\n(n=100)", ha="center", va="center",
            fontsize=9, fontweight="bold", rotation=90)
    ax.set_xlim(-2.2, len(prompts)-0.5)
    cbar = fig.colorbar(ax.images[0], ax=ax, fraction=0.018, pad=0.012)
    cbar.set_label("Success rate (%)", fontsize=9)
    fig.savefig(f"{FIG}/fig_v0v2_grid.pdf")
    plt.close(fig); print("wrote fig_v0v2_grid.pdf")

# ============================================================ Table 5 failtypes (= Table 9 data)
def table_failtypes():
    lines=[]
    lines.append(r"\begin{table}[tb]")
    lines.append(r"    \caption{V2 Extreme12 における失敗タイプの内訳（各モデル5有効試行$\times$12タスク＝60試行．最終ラウンドの状態で分類．「非可逆」はdelocal条件・非可逆代入・除算剰余などクリーン終了違反，「TO」は生成タイムアウト）}")
    lines.append(r"    \label{tab:failtypes}")
    lines.append(r"    \ecaption{Breakdown of failure types on V2 Extreme12 (60 trials each).}")
    lines.append(r"    \centering\small")
    lines.append(r"    \setlength{\tabcolsep}{3pt}")
    lines.append(r"    \begin{tabular}{l|rrrrrr}\hline")
    lines.append(r"    モデル & 成功 & 誤出力 & 非可逆 & 実行時 & 構文 & TO \\\hline")
    for m in FT9_MODELS:
        c=FT9[m]; mm=m.replace("&",r"\&")
        lines.append(f"    {mm} & {c[0]} & {c[1]} & {c[2]} & {c[3]} & {c[4]} & {c[5]} \\\\")
    lines.append(r"    \hline")
    lines.append(r"    \end{tabular}")
    lines.append(r"\end{table}")
    txt="\n".join(lines)+"\n"
    open(f"{FIG}/../table_failtypes.tex","w").write(txt)
    print("wrote table_failtypes.tex"); return txt

# ============================================================ Table 6 tokens
def table_tokens():
    models = ["Opus 4.8/high","Fable 5/low","Gemini-3.5-flash","Sonnet 5/high",
              "GPT-5.4/low","GPT-5.5/low","Gemini-3.1-flash-lite",
              "GPT-5.4-mini/low","Haiku 4.5"]
    lines=[]
    lines.append(r"\begin{table}[tb]")
    lines.append(r"    \caption{V2 Extreme12 におけるモデル別トークン効率（クリーン成功試行あたりの平均値．in+out トークン，推論トークン，成功に要したself-refineラウンド数．推論トークンを報告しないバックエンドは---）}")
    lines.append(r"    \label{tab:tokens}")
    lines.append(r"    \ecaption{Token efficiency per clean success on V2 Extreme12.}")
    lines.append(r"    \centering\small")
    lines.append(r"    \setlength{\tabcolsep}{2pt}")
    lines.append(r"    \begin{tabular}{l|rrrr}\hline")
    lines.append(r"    モデル & 成功数 & \shortstack{トークン\\/成功} & \shortstack{推論トークン\\/成功} & \shortstack{ラウンド\\/成功} \\\hline")
    for m in models:
        t=D["extreme"][m]["tok"]
        tp=f"{t['tok_per_succ']:,.0f}" if t['tok_per_succ'] else "---"
        rp=f"{t['reason_per_succ']:,.0f}" if t['reason_per_succ'] else "---"
        rd=f"{t['rounds_per_succ']:.2f}" if t['rounds_per_succ'] is not None else "---"
        mm=m.replace("&",r"\&")
        lines.append(f"    {mm} & {t['n_succ']} & {tp} & {rp} & {rd} \\\\")
    lines.append(r"    \hline")
    lines.append(r"    \end{tabular}")
    lines.append(r"\end{table}")
    txt="\n".join(lines)+"\n"
    open(f"{FIG}/../table_tokens.tex","w").write(txt)
    print("wrote table_tokens.tex"); return txt

if __name__=="__main__":
    fig_selfrefine(); fig_heatmap(); fig_failtypes(); fig_v0v2(); fig_v0v2_grid()
    t5=table_failtypes(); t6=table_tokens()
    print("\n----- table_failtypes.tex -----\n"+t5)
    print("\n----- table_tokens.tex -----\n"+t6)
