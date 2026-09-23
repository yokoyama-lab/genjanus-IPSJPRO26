#!/usr/bin/env python3
"""LLM 生成 Janus プログラムの「可逆化設計」を分類し，設計空間の分布表を作る。

`rabin_karp/classify_design.py`（Rabin–Karp 専用の 3 類分類：forward-only /
modinv-roll / recompute）を，コーパス全体（RK・canary・Basic19）に一般化したもの。

設計分類（primary label）とその判定条件
----------------------------------------
可逆プログラムでは中間値（ガーベジ）を最後に 0 に戻す必要がある。その「戻し方」で分類する。

  history            履歴保存。局所配列（`local int h[n]`）に反復ごとの値を前進的に書き込み，
                     後で逆順に引き戻す（forward-only）。または局所スタックへの push で履歴を保持。
                     判定: has_history_array（要素代入のある局所配列）or has_local_stack_history
  algebraic-inverse  代数的逆。履歴も再計算も使わず，数学的な逆演算で更新を打ち消す。
                     判定: has_modinv（法逆元 modinv/dinv の使用，`... % q = 1` を終了条件とする
                     ループ）or has_linear_swap（`tmp += f(x); x <=> tmp; tmp -= g(x)` 型の
                     「一時変数へ新値を計算→交換→逆式で一時変数を消す」更新イディオム）
  recompute          再計算（Bennett）。compute–copy–uncompute。
                     判定: has_uncall_pair（同じ手続きを call と uncall の両方で使う）
                     or has_recursion（自己再帰。呼び出しスタックが暗黙の履歴になる）
  direct             上記いずれも不要。可逆更新（`+=`, `<=>` 等）と局所変数の入れ子だけで
                     ガーベジが生じない単一パス（swap, cycle3, rev など）。
  other              構文解析も正規表現でも特徴が取れない（空ファイル・非 Janus 出力等）。

優先規則（複数戦略が共存する場合の primary label）
  algebraic-inverse > history > recompute > direct     （parse 成否に関係なく同じ）
これは元の classify_design.py の優先順（modinv > 局所配列 > それ以外=recompute）を含む。
RK 互換ラベル `rk_label` は元スクリプトの意味論をそのまま再現する:
  has_modinv → modinv-roll ／ 主手続き内に局所配列 → forward-only ／ それ以外 → recompute

特徴ベクトル（CSV に全て出力）
  parse_ok, n_procs, n_call, n_uncall, n_uncall_pair, has_uncall_pair, has_recursion,
  n_local_arrays, has_history_array, n_local_stacks, has_local_stack_history,
  n_push, n_pop, n_swap, has_linear_swap, has_modinv, has_inline_uncompute,
  local_arr_in_entry, n_loops, n_if, loc

解析器
  PyJanus（`jana_py.parser_jana2014_in_out`）が import できれば AST から特徴を取る。
  PYTHONPATH か `--pyjanus DIR` で指定。無い場合・構文エラーの場合は正規表現に退避し，
  parse_ok=0 として記録する。標準ライブラリ以外の依存なし。

使い方
  python3 scripts/classify_design_general.py [--csv OUT.csv] [--pyjanus DIR] [--md]
         [--rk-check rabin_karp/classify_design.py] PATH...
  PATH は run ディレクトリ（log.jsonl または experiment_log.jsonl を持つ），.jan ファイル，
  または glob。run ディレクトリ配下の .jan は再帰的に集め，log からメタデータ
  （model, task, round, status, clean）を結合する。`--ext rplpp` で gen_roopl の ROOPL++
  生成物（.rplpp）を正規表現のみで分類する（参考値。class/method 構文に読み替え）。
"""
from __future__ import annotations

import argparse
import collections
import csv
import dataclasses
import glob
import importlib
import json
import os
import re
import sys

# --------------------------------------------------------------------------- PyJanus
_PARSER = None


def load_pyjanus(path: str | None = None):
    """PyJanus のパーサを読み込む。失敗したら None（正規表現退避）。"""
    global _PARSER
    if _PARSER is not None:
        return _PARSER
    if path:
        sys.path.insert(0, path)
    try:
        _PARSER = importlib.import_module("jana_py.parser_jana2014_in_out")
    except Exception:  # noqa: BLE001
        _PARSER = False
    return _PARSER


RE_LOCAL_LINE = re.compile(r"^(\s*(?:de)?local\s+)(int|stack|bool|char)(\s+.*)$")
_TYPES = ("int", "stack", "bool", "char")


def fixup_multi_decl(text: str) -> str:
    """`local int a = 0, b = 1` → `local int a = 0, int b = 1`。

    旧版 PyJanus（実験当時の検証器）が受理していた型省略の複数宣言を，現行パーサ向けに
    正規化する。括弧深さ 0 のコンマだけを区切りとみなす。"""
    out = []
    for line in text.splitlines(keepends=True):
        m = RE_LOCAL_LINE.match(line)
        if not m or "," not in line:
            out.append(line)
            continue
        head, typ, rest = m.groups()
        segs, depth, cur = [], 0, ""
        for ch in rest:
            depth += ch in "([" ; depth -= ch in ")]"
            if ch == "," and depth == 0:
                segs.append(cur); cur = ""
            else:
                cur += ch
        segs.append(cur)
        fixed = [segs[0]] + [(" " + seg.strip()) if seg.strip().split(" ", 1)[0] in _TYPES
                             else (" " + typ + " " + seg.strip()) for seg in segs[1:]]
        out.append(head + typ + ",".join(fixed) + ("\n" if line.endswith("\n") else ""))
    return "".join(out)


_LAST_FIXUP = False


def parse_janus(text: str, filename: str = "<mem>"):
    """PyJanus で構文解析。失敗したら複数宣言の正規化（fixup）を試し，それでも駄目なら None。"""
    global _LAST_FIXUP
    _LAST_FIXUP = False
    mod = load_pyjanus()
    if not mod:
        return None
    try:
        return mod.parse_program(filename, text)
    except Exception:  # noqa: BLE001  構文エラー等は全て退避
        pass
    fixed = fixup_multi_decl(text)
    if fixed != text:
        try:
            prog = mod.parse_program(filename, fixed)
            _LAST_FIXUP = True
            return prog
        except Exception:  # noqa: BLE001
            pass
    return None


# --------------------------------------------------------------------------- AST utils
def _children(node):
    """dataclass ノードの子ノード（dataclass または list）を列挙。"""
    if dataclasses.is_dataclass(node):
        for f in dataclasses.fields(node):
            if f.name == "pos":
                continue
            yield getattr(node, f.name)
    elif isinstance(node, list):
        yield from node


def walk(node):
    """全ノードを前順で列挙。"""
    stack = [node]
    while stack:
        n = stack.pop()
        if dataclasses.is_dataclass(n):
            yield n
            stack.extend(list(_children(n)))
        elif isinstance(n, list):
            stack.extend(n)


def key(node):
    """位置情報を除いた構造キー（式の同一性比較に使う）。"""
    if dataclasses.is_dataclass(node):
        return (type(node).__name__,) + tuple(key(c) for c in _children(node))
    if isinstance(node, list):
        return tuple(key(c) for c in node)
    if hasattr(node, "value") and hasattr(node, "name"):  # Enum
        return node.value
    return node


def stmt_lists(node):
    """手続き本体を含む全ての文リスト（list[Stmt]）を列挙。"""
    for n in walk(node):
        for f in dataclasses.fields(n):
            v = getattr(n, f.name)
            if isinstance(v, list) and v and type(v[0]).__name__.endswith("Stmt"):
                yield v


def _t(n):
    return type(n).__name__


def _lval_name(lv):
    return lv.ident.name


def _idents_in(node):
    return {n.name for n in walk(node) if _t(n) == "Ident"}


# --------------------------------------------------------------------------- features
FEATURE_NAMES = [
    "parse_ok", "n_procs", "n_call", "n_uncall", "n_uncall_pair", "has_uncall_pair",
    "has_recursion", "n_local_arrays", "has_history_array", "n_local_stacks",
    "has_local_stack_history", "n_push", "n_pop", "n_swap", "has_linear_swap",
    "has_modinv", "has_inline_uncompute", "local_arr_in_entry", "n_loops", "n_if", "loc", "parse_fixup",
]

RE_MODINV_CALL = re.compile(r"(un)?call\s+\w*modinv\w*")
RE_MODINV_LOOP = re.compile(r"%\s*q\s*=\s*1")
RE_DINV = re.compile(r"\bdinv\b")


def modinv_regex(code: str) -> bool:
    """classify_design.py と同一の modinv 判定（後方互換のため式をそのまま保持）。"""
    return bool(RE_MODINV_CALL.search(code) or RE_MODINV_LOOP.search(code) or RE_DINV.search(code))


def _entry_proc_names(proc_names, called):
    """他から呼ばれない手続き＝入口候補。無ければ最後に定義された手続き。"""
    entry = [p for p in proc_names if p not in called]
    return entry or proc_names[-1:]


def features_ast(prog, code: str) -> dict:
    f = dict.fromkeys(FEATURE_NAMES, 0)
    f["parse_ok"] = 1
    f["loc"] = sum(1 for l in code.splitlines() if l.strip())
    procs = list(prog.procs)
    if prog.main is not None:
        procs.append(prog.main)
    proc_names = [p.procname.name for p in prog.procs]
    f["n_procs"] = len(procs)

    calls = collections.defaultdict(set)    # proc -> set of callee names (call+uncall)
    call_names, uncall_names = collections.Counter(), collections.Counter()
    for p in procs:
        pname = getattr(getattr(p, "procname", None), "name", "<main>")
        for n in walk(p.body if hasattr(p, "body") else p.stmts):
            t = _t(n)
            if t == "CallStmt":
                call_names[n.ident.name] += 1
                calls[pname].add(n.ident.name)
            elif t == "UncallStmt":
                uncall_names[n.ident.name] += 1
                calls[pname].add(n.ident.name)
            elif t == "PushStmt":
                f["n_push"] += 1
            elif t == "PopStmt":
                f["n_pop"] += 1
            elif t == "SwapStmt":
                f["n_swap"] += 1
            elif t in ("FromStmt", "IterateStmt", "ForeachStmt"):
                f["n_loops"] += 1
            elif t == "IfStmt":
                f["n_if"] += 1
    f["n_call"] = sum(call_names.values())
    f["n_uncall"] = sum(uncall_names.values())
    pair = set(call_names) & set(uncall_names)
    f["n_uncall_pair"] = len(pair)
    f["has_uncall_pair"] = int(bool(pair))

    # 再帰（直接 or 相互）: 呼び出しグラフの自身への到達可能性
    def reaches(src, dst, seen):
        for c in calls.get(src, ()):
            if c == dst or (c not in seen and (seen.add(c) or reaches(c, dst, seen))):
                return True
        return False
    f["has_recursion"] = int(any(reaches(p, p, set()) for p in proc_names))

    called = set(call_names) | set(uncall_names)
    entry = set(_entry_proc_names(proc_names, called))

    # 局所配列・局所スタック・履歴
    for p in procs:
        pname = getattr(getattr(p, "procname", None), "name", "<main>")
        body = p.body if hasattr(p, "body") else p.stmts
        local_arrays, local_stacks = set(), set()
        for n in walk(body):
            if _t(n) in ("LocalStmt", "BareLocalStmt"):
                d = n.enter_decl if _t(n) == "LocalStmt" else n.decl
                if d.dimensions:
                    local_arrays.add(d.ident.name)
                elif d.typ.kind == "stack":
                    local_stacks.add(d.ident.name)
        f["n_local_arrays"] += len(local_arrays)
        f["n_local_stacks"] += len(local_stacks)
        if local_arrays and pname in entry:
            f["local_arr_in_entry"] = 1
        for n in walk(body):
            t = _t(n)
            if t == "AssignStmt" and n.lval.selectors and _lval_name(n.lval) in local_arrays:
                f["has_history_array"] = 1
            if t == "SwapStmt" and (
                (n.lval1.selectors and _lval_name(n.lval1) in local_arrays)
                if hasattr(n, "lval1") else False
            ):
                f["has_history_array"] = 1
            if t == "PushStmt" and n.ident.name in local_stacks:
                f["has_local_stack_history"] = 1

        # 同一手続き内の inline uncompute: `x += E` の後に同じ `x -= E`（*=/= も同様）
        assigns = [n for n in walk(body) if _t(n) == "AssignStmt"]
        seen = {}
        inv = {"+=": "-=", "*=": "/=", "^=": "^="}
        for a in assigns:
            k = (key(a.lval), key(a.expr))
            op = a.mod_op.value
            seen.setdefault(k, set()).add(op)
        for k, ops in seen.items():
            if any(op in ops and inv[op] in ops for op in inv):
                f["has_inline_uncompute"] = 1
                break

        # 線形交換更新: 同一文リスト内で tmp += E1 ; ... ; tmp <=> x ; ... ; tmp -= E2
        for sl in stmt_lists(body):
            plus, swapped = set(), set()
            for s in sl:
                t = _t(s)
                if t == "AssignStmt" and not s.lval.selectors:
                    nm = _lval_name(s.lval)
                    if s.mod_op.value == "+=" and nm not in swapped:
                        plus.add(nm)
                    elif s.mod_op.value == "-=" and nm in swapped:
                        f["has_linear_swap"] = 1
                elif t == "SwapStmt":
                    for lv in _swap_lvals(s):
                        if not lv.selectors and _lval_name(lv) in plus:
                            swapped.add(_lval_name(lv))

    # 法逆元: 正規表現（元スクリプト互換）＋ AST（`... % ... = 1` を終了条件とするループ）
    modinv = modinv_regex(code)
    if not modinv:
        for n in walk(prog):
            if _t(n) == "FromStmt":
                c = n.exit_cond
                if (_t(c) == "BinExpr" and c.op.value == "==" and _t(c.left) == "BinExpr"
                        and c.left.op.value == "%" and _t(c.right) == "Number" and c.right.value == 1):
                    modinv = True
    f["has_modinv"] = int(modinv)
    return f


def _swap_lvals(s):
    out = []
    for fld in dataclasses.fields(s):
        v = getattr(s, fld.name)
        if _t(v) == "Lval":
            out.append(v)
    return out


RE_PROC = re.compile(r"^\s*procedure\s+(\w+)", re.M)
RE_METHOD = re.compile(r"^\s*method\s+(\w+)", re.M)          # ROOPL++
RE_CALL = re.compile(r"\bcall\s+(?:\w+\s*::\s*)?(\w+)")     # ROOPL++ の obj::m も末尾名で扱う
RE_UNCALL = re.compile(r"\buncall\s+(?:\w+\s*::\s*)?(\w+)")
RE_LOCAL_ARR = re.compile(r"\blocal\s+\w+\s+(\w+)\s*\[")
RE_RPP_ARR = re.compile(r"\bnew\s+\w+\s*\[[^\]]*\]\s+(\w+)|\blocal\s+\w+\s*\[\s*\]\s+(\w+)")  # ROOPL++
RE_LOCAL_STACK = re.compile(r"\blocal\s+stack\s+(\w+)")


def features_regex(code: str, lang: str = "janus") -> dict:
    """正規表現による特徴抽出（粗い近似）。

    Janus では構文解析できないファイルの退避経路。ROOPL++（lang="rooplpp"）では唯一の経路で，
    procedure→method，局所配列→`new int[n] a` / `local int[] a` と読み替える。"""
    f = dict.fromkeys(FEATURE_NAMES, 0)
    f["loc"] = sum(1 for l in code.splitlines() if l.strip())
    re_proc = RE_METHOD if lang == "rooplpp" else RE_PROC
    kw = "method" if lang == "rooplpp" else "procedure"
    procs = re_proc.findall(code)
    f["n_procs"] = len(procs)
    calls, uncalls = RE_CALL.findall(code), RE_UNCALL.findall(code)
    f["n_call"], f["n_uncall"] = len(calls), len(uncalls)
    pair = set(calls) & set(uncalls)
    f["n_uncall_pair"], f["has_uncall_pair"] = len(pair), int(bool(pair))
    blocks = re.split(rf"(?=^\s*{kw}\s)", code, flags=re.M)
    for b in blocks:
        m = re_proc.match(b)
        if m and re.search(rf"\b(un)?call\s+(?:\w+\s*::\s*)?{re.escape(m.group(1))}\b", b):
            f["has_recursion"] = 1
    if lang == "janus":
        arrs = RE_LOCAL_ARR.findall(code)
    else:  # ROOPL++: main メソッドでの入力配列確保（new int[n]）は履歴ではないので除外
        arrs = [a or b for blk in blocks
                if not re.match(r"\s*method\s+main\b", blk)
                for a, b in RE_RPP_ARR.findall(blk)]
    f["n_local_arrays"] = len(arrs)
    f["has_history_array"] = int(any(re.search(rf"\b{re.escape(a)}\s*\[[^\]]*\]\s*[-+^*/]=", code) for a in arrs))
    stacks = RE_LOCAL_STACK.findall(code)
    f["n_local_stacks"] = len(stacks)
    f["has_local_stack_history"] = int(any(re.search(rf"\bpush\s*\([^)]*,\s*{re.escape(s)}\s*\)", code) for s in stacks))
    f["n_push"] = len(re.findall(r"\bpush\s*\(", code))
    f["n_pop"] = len(re.findall(r"\bpop\s*\(", code))
    f["n_swap"] = code.count("<=>")
    f["has_linear_swap"] = int(bool(re.search(r"(\w+)\s*\+=.*\n(?:.*\n)*?.*\b\1\s*<=>.*\n(?:.*\n)*?.*\b\1\s*-=", code)))
    f["has_modinv"] = int(modinv_regex(code))
    f["n_loops"] = len(re.findall(r"\b(from|iterate)\b", code))
    f["n_if"] = len(re.findall(r"\bif\b", code))
    called = set(calls) | set(uncalls)
    entry = set(_entry_proc_names(procs, called))
    for b in blocks:
        m = re_proc.match(b)
        if m and m.group(1) in entry and m.group(1) != "main" and (RE_LOCAL_ARR if lang == "janus" else RE_RPP_ARR).search(b):
            f["local_arr_in_entry"] = 1
    return f


def label_of(f: dict) -> str:
    """優先規則: algebraic-inverse > history > recompute > direct（/other）。"""
    if f["has_modinv"] or f["has_linear_swap"]:
        return "algebraic-inverse"
    if f["has_history_array"] or f["has_local_stack_history"]:
        return "history"
    if f["has_uncall_pair"] or f["has_recursion"]:
        return "recompute"
    if f["parse_ok"] or f["n_procs"]:
        return "direct"
    return "other"


def sublabel_of(f: dict) -> str:
    """primary label の内訳（どの特徴で判定されたか）。"""
    lab = label_of(f)
    if lab == "algebraic-inverse":
        return "algebraic/modinv" if f["has_modinv"] else "algebraic/linear-swap"
    if lab == "history":
        return "history/array" if f["has_history_array"] else "history/stack"
    if lab == "recompute":
        return "recompute/uncall" if f["has_uncall_pair"] else "recompute/recursion"
    return lab


def rk_label_of(f: dict) -> str:
    """classify_design.py の 3 類ラベルを特徴から再現（RK 後方互換）。"""
    if f["has_modinv"]:
        return "modinv-roll"
    if f["local_arr_in_entry"]:
        return "forward-only"
    return "recompute"


def classify_code(code: str, filename: str = "<mem>", lang: str = "janus") -> dict:
    """1 ファイルを分類。lang="rooplpp" は正規表現のみ（parse_ok=0）。"""
    prog = parse_janus(code, filename) if lang == "janus" else None
    f = features_ast(prog, code) if prog is not None else features_regex(code, lang)
    f["parse_fixup"] = int(_LAST_FIXUP)
    f["label"] = label_of(f)
    f["sublabel"] = sublabel_of(f)
    f["rk_label"] = rk_label_of(f)
    return f


# --------------------------------------------------------------------------- corpus / metadata
RE_TRIAL = re.compile(r"trial_(\d+)_round_(\d+)\.(jan|rplpp)$")


def _rows(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [json.loads(l) for l in fh if l.strip()]


_LOG_CACHE: dict[str, dict] = {}


def _log_index(run_dir: str):
    """run_dir の log.jsonl / experiment_log.jsonl を (task_dir, trial, round) で索引。"""
    if run_dir in _LOG_CACHE:
        return _LOG_CACHE[run_dir]
    idx = {}
    for name in ("log.jsonl", "experiment_log.jsonl"):
        p = os.path.join(run_dir, name)
        if os.path.exists(p):
            for r in _rows(p):
                k = (r.get("prompt_id") or r.get("task"), int(r.get("trial", -1)), int(r.get("round", -1)))
                idx[k] = r  # 重複時は最後の行を採用
            break
    _LOG_CACHE[run_dir] = idx
    return idx


def find_run_dir(path: str):
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(6):
        if os.path.exists(os.path.join(d, "log.jsonl")) or os.path.exists(os.path.join(d, "experiment_log.jsonl")):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    return None


def family_of(task: str, model: str, lang: str = "janus") -> str:
    pre = "rooplpp-" if lang == "rooplpp" else ""
    if model == "reference":
        return pre + "reference"
    if task in ("rk1d", "rk2d", "rk3"):
        return "rk"
    if task.startswith("canary"):
        return "canary"
    return pre + "basic19"


def metadata(path: str) -> dict:
    m = RE_TRIAL.search(path)
    task_dir = os.path.basename(os.path.dirname(path))
    run_dir = find_run_dir(path)
    meta = dict(run=os.path.basename(run_dir) if run_dir else "", model="", task=task_dir,
                trial=int(m.group(1)) if m else -1, round=int(m.group(2)) if m else -1,
                status="", clean="", overfit="")
    if run_dir and m:
        r = _log_index(run_dir).get((task_dir, meta["trial"], meta["round"]))
        if r:
            meta.update(model=r.get("model", ""), task=r.get("task", task_dir), status=r.get("status", ""),
                        clean="" if r.get("clean") is None else int(bool(r.get("clean"))),
                        overfit="" if r.get("overfit") is None else int(bool(r.get("overfit"))))
    meta["family"] = family_of(meta["task"], meta["model"], lang_of(path))
    return meta


def lang_of(path: str) -> str:
    return "rooplpp" if path.endswith(".rplpp") else "janus"


def collect_files(paths, ext="jan"):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(glob.glob(os.path.join(p, "**", "*." + ext), recursive=True))
        elif os.path.isfile(p):
            if p.endswith("." + ext):
                out.append(p)
        else:
            out += sorted(glob.glob(p, recursive=True))
    return list(dict.fromkeys(out))


META_COLS = ["file", "run", "family", "model", "task", "trial", "round", "status", "clean", "overfit",
             "label", "sublabel", "rk_label"]
LABELS = ["history", "algebraic-inverse", "recompute", "direct", "other"]


def classify_files(files, base=None):
    rows = []
    for fp in files:
        with open(fp, encoding="utf-8", errors="replace") as fh:
            code = fh.read()
        f = classify_code(code, fp, lang_of(fp))
        meta = metadata(fp)
        rel = os.path.relpath(fp, base) if base else fp
        rows.append({"file": rel, **meta, **{k: f[k] for k in ("label", "sublabel", "rk_label")}, **{k: f[k] for k in FEATURE_NAMES}})
    return rows


# --------------------------------------------------------------------------- tables
def crosstab(rows, rowkey, colkeys=LABELS, md=False, title=""):
    tab = collections.defaultdict(collections.Counter)
    for r in rows:
        tab[rowkey(r)][r["label"]] += 1
    lines = []
    if title:
        lines.append(("### " if md else "== ") + title)
    hdr = ["", *colkeys, "n"]
    body = []
    for k in sorted(tab, key=lambda x: str(x)):
        c = tab[k]
        n = sum(c.values())
        body.append([str(k)] + [f"{c[l]} ({100*c[l]/n:.0f}%)" if c[l] else "0" for l in colkeys] + [str(n)])
    tot = collections.Counter()
    for c in tab.values():
        tot.update(c)
    n = sum(tot.values())
    if n:
        body.append(["ALL"] + [f"{tot[l]} ({100*tot[l]/n:.0f}%)" if tot[l] else "0" for l in colkeys] + [str(n)])
    if md:
        lines.append("| " + " | ".join(hdr) + " |")
        lines.append("|" + "---|" * len(hdr))
        lines += ["| " + " | ".join(b) + " |" for b in body]
    else:
        w = [max(len(x) for x in col) for col in zip(hdr, *body)]
        for b in [hdr, *body]:
            lines.append("  ".join(x.ljust(wi) for x, wi in zip(b, w)))
    return "\n".join(lines)


def _sublabel_table(rows, md=False):
    c = collections.Counter(r["sublabel"] for r in rows)
    lines = [("### " if md else "== ") + "sublabel counts (LLM files)"]
    for k, v in sorted(c.items(), key=lambda x: -x[1]):
        lines.append(f"  {k:24s} {v}")
    return "\n".join(lines)


def round_transitions(rows):
    """試行ごとに round 0 と最終 round のラベルを比べる（両方のファイルがある試行のみ）。"""
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["run"], r["task"], r["trial"])][r["round"]] = r["label"]
    trans = collections.Counter()
    for k, d in by.items():
        if len(d) < 2 or 0 not in d:
            continue
        trans[(d[0], d[max(d)])] += 1
    return trans


def print_tables(rows, md=False):
    llm = [r for r in rows if not r["family"].endswith("reference")]
    out = [crosstab(rows, lambda r: r["family"], md=md, title="label x task-family (all files)")]
    out.append(crosstab(llm, lambda r: f'{r["family"]}/{r["model"] or "?"}', md=md, title="label x model (LLM files)"))
    out.append(crosstab(llm, lambda r: f'{r["family"]}/{r["task"]}', md=md, title="label x task (LLM files)"))
    refs = [r for r in rows if r["family"].endswith("reference")]
    if refs:
        ref = collections.defaultdict(collections.Counter)
        for r in refs:
            ref[r["task"]][r["label"]] += 1
        out.append(("### " if md else "== ") + "reference-solution label by task\n" +
                   "\n".join(f"  {t:18s} {dict(ref[t])}" for t in sorted(ref)))
    out.append(crosstab(llm, lambda r: "SUCCESS" if r["status"] == "SUCCESS" else (r["status"] or "no-log"),
                        md=md, title="label x status (LLM files)"))
    for fam in sorted({r["family"] for r in llm}):
        sub = [r for r in llm if r["family"] == fam]
        tab = collections.defaultdict(collections.Counter)
        for r in sub:
            tab[r["label"]]["SUCCESS" if r["status"] == "SUCCESS" else "fail"] += 1
        blk = [("### " if md else "== ") + f"success rate by label ({fam})"]
        for l in LABELS:
            if tab[l]:
                n = sum(tab[l].values())
                blk.append(f"  {l:18s} SUCCESS {tab[l]['SUCCESS']:4d} / {n:4d}  ({100*tab[l]['SUCCESS']/n:.0f}%)")
        out.append("\n".join(blk))
    trans = round_transitions(llm)
    blk = [("### " if md else "== ") + "round 0 -> final round label transitions (trials with >=2 rounds)"]
    same = sum(v for (a, b), v in trans.items() if a == b)
    tot = sum(trans.values())
    for (a, b), v in sorted(trans.items(), key=lambda x: -x[1]):
        blk.append(f"  {a:18s} -> {b:18s} {v}")
    if tot:
        blk.append(f"  unchanged {same}/{tot} ({100*same/tot:.0f}%)")
    out.append("\n".join(blk))
    out.append(crosstab(llm, lambda r: r["sublabel"], colkeys=["n"], md=md, title="sublabel counts (LLM files)")
               if False else _sublabel_table(llm, md))
    unparsed = [r for r in rows if not r["parse_ok"]]
    fixed = sum(r["parse_fixup"] for r in rows)
    out.append(f"\nfiles: {len(rows)}   parsed by PyJanus: {len(rows)-len(unparsed)} (of which after multi-decl fixup: {fixed})"
               f"   regex fallback: {len(unparsed)}   pyjanus available: {bool(load_pyjanus())}")
    print("\n\n".join(out))


# --------------------------------------------------------------------------- RK validation
def rk_check(rows, orig_script: str, base: str):
    """元の classify_design.py を import し，RK の SUCCESS・clean・非 overfit ファイルで比較。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("classify_design", orig_script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    agree = disagree = 0
    detail = []
    for r in rows:
        if r["family"] != "rk" or r["status"] != "SUCCESS" or r["clean"] != 1 or r["overfit"] == 1:
            continue
        fp = os.path.join(base, r["file"]) if base else r["file"]
        with open(fp, encoding="utf-8", errors="replace") as fh:
            orig, _sig = mod.classify(fh.read())
        if orig == r["rk_label"]:
            agree += 1
        else:
            disagree += 1
            detail.append(f"  {r['file']}: orig={orig} new={r['rk_label']} (general={r['label']})")
    print(f"\n== RK validation vs {orig_script}: agree {agree} / {agree+disagree}, disagree {disagree}")
    print("\n".join(detail))
    return agree, disagree, detail


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="run dirs, .jan files or globs")
    ap.add_argument("--csv", help="write per-file CSV here")
    ap.add_argument("--pyjanus", help="PyJanus checkout dir (else PYTHONPATH)")
    ap.add_argument("--no-ast", action="store_true", help="force regex-only features")
    ap.add_argument("--md", action="store_true", help="Markdown tables")
    ap.add_argument("--base", default=None, help="make CSV paths relative to this dir")
    ap.add_argument("--ext", default="jan", help="file extension collected from dirs: jan (default) or rplpp (ROOPL++, regex only)")
    ap.add_argument("--rk-check", metavar="CLASSIFY_DESIGN_PY", help="compare with original RK classifier")
    a = ap.parse_args(argv)
    global _PARSER
    if a.no_ast:
        _PARSER = False
    else:
        load_pyjanus(a.pyjanus)
    files = collect_files(a.paths, a.ext)
    if not files:
        sys.exit("no .jan files found")
    rows = classify_files(files, a.base)
    if a.csv:
        os.makedirs(os.path.dirname(os.path.abspath(a.csv)), exist_ok=True)
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=META_COLS + FEATURE_NAMES)
            w.writeheader()
            w.writerows(rows)
    print_tables(rows, md=a.md)
    if a.rk_check:
        rk_check(rows, a.rk_check, a.base)


if __name__ == "__main__":
    main()
