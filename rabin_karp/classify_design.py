#!/usr/bin/env python3
"""再現性 run の各成功解を設計分類する。

各タスク（rk1d/rk2d/rk3）の成功トライアル（log.jsonl の SUCCESS かつ clean・非overfit）の
最終 .jan を読み、可逆 Rabin-Karp の実装設計を3類に分ける:
  - forward-only : 主手続き内に局所ハッシュ配列があり modinv 無し（配列に前進ロール）
  - modinv-roll  : 法逆元 modinv/dinv を使う単一ハッシュのローリング
  - recompute    : 窓ごとにハッシュ手続きを呼んで再計算（配列・ロール無し）
  - other        : 上のどれにも当てはまらない

  python classify_design.py <run_dir>
"""
import json, os, re, sys, collections


def classify(code):
    main = re.search(r"procedure\s+rabinkarp\d.*\Z", code, re.S)
    body = main.group(0) if main else code
    # modinv は「定義」ではなく「使用」で判定（dead code を除外）。
    has_modinv = (bool(re.search(r"(un)?call\s+\w*modinv\w*", code))
                  or bool(re.search(r"%\s*q\s*=\s*1", code))
                  or bool(re.search(r"\bdinv\b", code)))
    # 主手続き内の局所ハッシュ配列（2D/3D の R/W や 1D の H）
    local_arr = bool(re.search(r"local\s+int\s+\w+\s*\[", body))
    # 窓ハッシュ手続き（%q とループを持つ）を主ループ内で call しているか
    hashprocs = set()
    for blk in re.split(r"(?=^procedure )", code, flags=re.M):
        m = re.match(r"procedure\s+(\w+)", blk)
        if m and re.search(r"%\s*q", blk) and re.search(r"\b(from|iterate)\b", blk):
            hashprocs.add(m.group(1))
    loop_start = re.search(r"\b(from|iterate)\b", body)
    recompute = False
    if loop_start:
        inner = body[loop_start.start():]
        recompute = any(re.search(rf"\bcall\s+{n}\b", inner) for n in hashprocs)
    # 法逆元なしで単一ハッシュをクリーン可逆にロールするには配列か逆元が要る。
    # よって: modinv あり→inverse ロール / 局所配列あり→forward-only /
    # どちらも無し→窓ごと再計算（uncall で消す）。
    if has_modinv:
        label = "modinv-roll"
    elif local_arr:
        label = "forward-only"
    else:
        label = "recompute"
    return label, dict(modinv=has_modinv, local_arr=local_arr, recompute=recompute)


def main(run_dir):
    log = os.path.join(run_dir, "log.jsonl")
    rs = [json.loads(l) for l in open(log) if l.strip()] if os.path.exists(log) else []
    for task in ["rk1d", "rk2d", "rk3"]:
        oks = [r for r in rs if r.get("task") == task and r.get("status") == "SUCCESS"
               and r.get("clean") and not r.get("overfit")]
        labels = collections.Counter()
        print(f"\n### {task}: 成功 {len(oks)} 件")
        for r in oks:
            jf = os.path.join(run_dir, "trials", task,
                              f"trial_{r['trial']:03d}_round_{r['round']:02d}.jan")
            if not os.path.exists(jf):
                continue
            label, sig = classify(open(jf).read())
            labels[label] += 1
            print(f"  t{r['trial']}/r{r['round']}: {label:13s} {sig}")
        print(f"  → {dict(labels)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "runs/20260629_claude_opus_rk_repro")
