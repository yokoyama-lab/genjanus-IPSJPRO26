#!/usr/bin/env python3
"""Hard12・Extreme12 の Janus プログラムを、Python 参照実装（refs.py）と照合する。

テストケース（課題ごとに 4〜5 個）より広い入力で、次の 2 つを確かめる。

  前向き: 参照実装の出力と一致し、期待外の非ゼロ変数（ゴミ）が残らない
  往復  : call P(...) の後に uncall P(...) して、全変数が入力に戻る

入力の選び方:
  --domain      refs.domains() の有界な定義域をすべて列挙する（39〜6651 入力／課題）
  --random N    定義域より大きな入力を課題ごとに N 個（乱数の種は課題名から固定）

使い方（リポジトリの根から）:
  python3 programs/checks/check.py --domain --interp pyjanus
  python3 programs/checks/check.py --random 150 --interp pyjanus
  python3 programs/checks/check.py --domain --interp jana --thomsen --task h2_bitrev

--interp は pyjanus（--std jana2014_in_out -s で呼ぶ）か、Thomsen の jana、またはその実行ファイルのパス。
"""
import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
import tempfile
import zlib
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAMS = HERE.parent
sys.path.insert(0, str(HERE))
import refs  # noqa: E402

SPECS = json.loads((PROGRAMS / "tasks.json").read_text())


# ---------------------------------------------------------------- 実行

def params(spec):
    out = []
    for p in spec["params"]:
        name = p.split()[-1]
        out.append((name[:-2], True) if name.endswith("[]") else (name, False))
    return out


def build(code, spec, inputs, roundtrip):
    """手続き code に main を付けたプログラムを返す。長さ 0 の配列が要るときは None。"""
    ps = params(spec)
    lines = [code.rstrip(), "", "procedure main()"]
    for name, arr in ps:
        if arr:
            if len(inputs[name]) == 0:
                return None
            lines.append(f"    int {name}[{len(inputs[name])}]")
        else:
            lines.append(f"    int {name}")
    for name, arr in ps:
        val = inputs[name]
        for idx, v in (enumerate(val) if arr else [(None, val)]):
            lv = f"{name}[{idx}]" if arr else name
            if v > 0:
                lines.append(f"    {lv} += {v}")
            elif v < 0:
                lines.append(f"    {lv} -= {-v}")
    call = f"{spec['proc_name']}({', '.join(n for n, _ in ps)})"
    lines.append(f"    call {call}")
    if roundtrip:
        lines.append(f"    uncall {call}")
    return "\n".join(lines) + "\n"


def run(interp, code, timeout):
    with tempfile.NamedTemporaryFile("w", suffix=".jan", delete=False) as f:
        f.write(code)
        path = f.name
    if Path(interp).name == "pyjanus":
        cmd = [interp, "--std", "jana2014_in_out", "-s", "-t", str(timeout), path]
    else:
        cmd = [interp, f"-t{timeout}", path]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    finally:
        os.unlink(path)


def parse(out):
    res = {}
    for line in out.splitlines():
        if "=" not in line:
            continue
        var, val = (s.strip() for s in line.split("=", 1))
        m = re.match(r"(\w+)\[\d+\]$", var)
        try:
            if m and val.startswith("{") and val.endswith("}"):
                res[m.group(1)] = [int(v) for v in val[1:-1].split(",") if v.strip()]
            else:
                res[var] = int(val)
        except ValueError:
            pass
    return res


def agrees(out, want):
    """出力が want（全パラメータの値）と一致し、それ以外に非ゼロ変数が無いか。"""
    got = parse(out)
    for k, v in want.items():
        zero = [0] * len(v) if isinstance(v, list) else 0
        if got.get(k, zero) != v:
            return False
    for k, v in got.items():
        if k not in want and (any(v) if isinstance(v, list) else v):
            return False
    return True


# ---------------------------------------------------------------- 入力

def random_inputs(name, n):
    r = random.Random(zlib.crc32(name.encode()))

    def a(k, lo, hi):
        return [r.randint(lo, hi) for _ in range(k)]

    def merge():
        m, k = r.randint(1, 7), r.randint(1, 7)
        return {"a": sorted(a(m, -20, 20)) + sorted(a(k, -20, 20)), "b": [0] * (m + k),
                "m": m, "n": k, "trace": 0}

    def modinv():
        while True:
            m = r.randint(2, 500)
            x = r.randint(1, m - 1)
            if math.gcd(x, m) == 1:
                return {"a": x, "m": m, "inv": 0, "q": [0] * 8, "cnt": 0}

    def mtf():
        k, m = r.randint(2, 6), r.randint(1, 8)
        return {"a": a(m, 0, k - 1), "sym": list(range(k)), "n": m, "k": k}

    def perm():
        k = r.randint(1, 8)
        p = list(range(k))
        r.shuffle(p)
        return {"p": p, "n": k}

    def heap():
        k = r.randint(2, 12)
        return {"a": a(k, -9, 9), "n": k, "steps": [0] * (k // 2), "trace": 0}

    def kmp():
        k = r.randint(1, 12)
        return {"s": a(k, 1, 3), "pi": [0] * k, "n": k, "fb": [0] * k}

    def arr(lo, hi, nmax, extra=None):
        def g():
            k = r.randint(1, nmax)
            return {"a": a(k, lo, hi), "n": k, **(extra or {})}
        return g

    def rot():
        k = r.randint(2, 10)
        return {"a": a(k, -9, 9), "n": k, "k": r.randint(1, k - 1)}

    def modexp():
        e = r.randint(1, 8)
        return {"base": r.randint(1, 50), "e": e, "m": r.randint(2, 60), "r": 1, "q": [0] * e}

    def hil():
        k = r.randint(1, 6)
        return {"d": r.randint(0, 4 ** k - 1), "k": k, "x": 0, "y": 0}

    def bitrev():
        k = r.randint(1, 5)
        return {"a": a(1 << k, -9, 9), "k": k}

    gens = {
        "h_gray_encode": lambda: {"n": r.randint(0, 10**6), "g": 0},
        "h_gray_decode": lambda: {"g": r.randint(1, 10**6), "n": 0, "steps": 0},
        # 1 歩ずつ数える作りなので、x・y を大きくすると時間制限に当たる
        "h_cantor_pair": lambda: {"x": r.randint(0, 200), "y": r.randint(0, 200), "z": 0},
        "h_cantor_unpair": lambda: {"z": r.randint(0, 10**6), "x": 0, "y": 0},
        "h_rotate_k": rot,
        "h_delta_encode": arr(-50, 50, 10),
        "h_delta_decode": arr(-50, 50, 10),
        "h_bsort01": arr(0, 1, 12, {"trace": 0}),
        "h_base3": lambda: {"n": r.randint(1, 10**5), "trits": 0, "cnt": 0},
        "h_bingcd": lambda: {"x": r.randint(1, 3000), "y": r.randint(1, 3000), "steps": 0, "flags": 0},
        "h_merge_halves": merge,
        "h_modexp": modexp,
        "h2_zeckendorf": lambda: {"n": r.randint(1, 10**5), "z": 0, "cnt": 0},
        "h2_cf_expand": lambda: {"a": r.randint(1, 300), "b": r.randint(1, 300), "q": [0] * 8, "cnt": 0},
        "h2_bitrev": bitrev,
        "h2_modinv": modinv,
        "h2_mtf": mtf,
        "h2_oesort": arr(-9, 9, 10, {"trace": 0}),
        "h2_heapify": heap,
        "h2_lehmer_rank": lambda: {**perm(), "r": 0},
        "h2_perm_inverse": perm,
        "h2_kmp_failure": kmp,
        "h2_hilbert": hil,
        "h2_bwt": lambda: (lambda k: {"s": a(k, 1, 5), "n": k, "idx": 0})(r.randint(1, 7)),
    }
    xs, tries = [], 0
    while len(xs) < n and tries < 50 * n:
        tries += 1
        x = gens[name]()
        try:
            # 前提を満たすものだけ使う。参照実装は前提の外で assert か、
            # 固定長の配列（cf_expand・modinv の q[8]）があふれて IndexError を出す
            refs.REFS[name](json.loads(json.dumps(x)))
        except (AssertionError, IndexError):
            continue
        xs.append(x)
    return xs


# ---------------------------------------------------------------- 本体

def check(job):
    name, args = job
    spec = SPECS[name]
    path = PROGRAMS / spec["suite"] / f"{name}.jan"
    alt = PROGRAMS / spec["suite"] / "thomsen" / f"{name}.jan"
    if args["thomsen"] and alt.exists():
        path = alt
    code = path.read_text()
    xs = list(refs.domains()[name]) if args["random"] is None else random_inputs(name, args["random"])
    res = {"task": name, "program": str(path.relative_to(PROGRAMS)), "inputs": len(xs),
           "skipped": 0, "forward": 0, "roundtrip": 0, "first_forward_fail": None,
           "first_roundtrip_fail": None}
    for x in xs:
        want = refs.REFS[name](json.loads(json.dumps(x)))
        fwd = build(code, spec, x, False)
        if fwd is None:
            res["skipped"] += 1
            continue
        rc, out = run(args["interp"], fwd, args["timeout"])
        if rc == 0 and agrees(out, want):
            res["forward"] += 1
        elif res["first_forward_fail"] is None:
            res["first_forward_fail"] = {"input": x, "expected": want, "output": out.strip()[:300]}
        rc, out = run(args["interp"], build(code, spec, x, True), args["timeout"])
        if rc == 0 and agrees(out, x):
            res["roundtrip"] += 1
        elif res["first_roundtrip_fail"] is None:
            res["first_roundtrip_fail"] = {"input": x, "output": out.strip()[:300]}
    return res


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--domain", action="store_true", help="定義域をすべて列挙する")
    g.add_argument("--random", type=int, metavar="N", help="範囲を広げた乱択入力を課題ごとに N 個")
    ap.add_argument("--interp", default="pyjanus")
    ap.add_argument("--thomsen", action="store_true", help="<suite>/thomsen/ に書き換え版があれば使う")
    ap.add_argument("--task", action="append", help="課題名（複数可。既定は 24 課題すべて）")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--json", type=Path, help="結果を JSON で保存する")
    a = ap.parse_args()
    names = a.task or list(SPECS)
    opts = {"interp": a.interp, "thomsen": a.thomsen, "random": a.random, "timeout": a.timeout}
    results = []
    with Pool(a.jobs) as pool:
        for r in pool.imap_unordered(check, [(n, opts) for n in names]):
            results.append(r)
            ran = r["inputs"] - r["skipped"]
            ok = r["forward"] == ran and r["roundtrip"] == ran
            skip = f"  (実行できない入力 {r['skipped']})" if r["skipped"] else ""
            print(f"{'PASS' if ok else 'FAIL'}  {r['task']:16s} 前向き {r['forward']}/{ran}  "
                  f"往復 {r['roundtrip']}/{ran}{skip}", flush=True)
    bad = [r for r in results if r["forward"] != r["inputs"] - r["skipped"]
           or r["roundtrip"] != r["inputs"] - r["skipped"]]
    print(f"{len(results) - len(bad)}/{len(results)} 課題が前向き・往復とも全件一致")
    if a.json:
        a.json.write_text(json.dumps(sorted(results, key=lambda r: names.index(r["task"])),
                                     indent=1, ensure_ascii=False))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
