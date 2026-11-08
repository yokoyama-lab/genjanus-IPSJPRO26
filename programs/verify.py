#!/usr/bin/env python3
"""Run every test program under programs/*/tests/ and compare with tasks.json.

Usage:
    python3 programs/verify.py --interp jana            # Thomsen's jana
    python3 programs/verify.py --interp pyjanus         # pyjanus (--std jana2014_in_out -s)
    python3 programs/verify.py --interp jana --thomsen  # Thomsen-compatible variants
    python3 programs/verify.py --interp jana --task h2_bwt

A case passes when the interpreter exits with 0, every expected variable has
the expected value, and no other variable is left non-zero unless it kept its
input value (the "clean" condition used in the paper).
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def parse_output(stdout):
    result = {}
    for line in stdout.splitlines():
        if "=" not in line:
            continue
        var, value = (s.strip() for s in line.split("=", 1))
        m = re.match(r"(\w+)\[\d+\]$", var)
        if m and value.startswith("{") and value.endswith("}"):
            result[m.group(1)] = [int(v) for v in value[1:-1].split(",") if v.strip()]
            continue
        try:
            result[var] = int(value)
        except ValueError:
            pass
    return result


def nonzero(v):
    return any(x != 0 for x in v) if isinstance(v, list) else v != 0


def run(interp, path, timeout):
    if interp == "pyjanus":
        cmd = ["pyjanus", "--std", "jana2014_in_out", "-s", "-t", str(timeout), str(path)]
    else:
        cmd = [interp, f"-t{timeout}", str(path)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    return p.returncode, p.stdout + p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interp", default="jana", help="jana (Thomsen) or pyjanus, or a path to jana")
    ap.add_argument("--task", action="append")
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--roundtrip", action="store_true",
                    help="run `call P(...)` followed by `uncall P(...)`; every variable must return to its input")
    ap.add_argument("--thomsen", action="store_true",
                    help="use <suite>/thomsen/tests/ variants where they exist")
    args = ap.parse_args()
    specs = json.loads((HERE / "tasks.json").read_text())
    n_ok = n_all = 0
    for name, spec in specs.items():
        if args.task and name not in args.task:
            continue
        verdicts = []
        for i, tc in enumerate(spec["test_cases"]):
            path = HERE / spec["suite"] / "tests" / name / f"case{i}.jan"
            alt = HERE / spec["suite"] / "thomsen" / "tests" / name / f"case{i}.jan"
            if args.thomsen and alt.exists():
                path = alt
            expected = tc["expected"]
            if args.roundtrip:
                src = path.read_text()
                head, main_part = src.split("procedure main()", 1)
                calls = re.findall(r"^\s*call (.*)$", main_part, re.M)
                main_part += "".join(f"    uncall {c}\n" for c in reversed(calls))
                with tempfile.NamedTemporaryFile("w", suffix=".jan", delete=False) as f:
                    f.write(head + "procedure main()" + main_part)
                path = Path(f.name)
                expected = tc["inputs"]
            rc, out = run(args.interp, path, args.timeout)
            if args.roundtrip:
                path.unlink()
            got = parse_output(out) if rc == 0 else {}
            if rc != 0:
                verdicts.append(("ERROR", out.strip().splitlines()[:2]))
                continue
            wrong = {k: got.get(k) for k, v in expected.items()
                     if got.get(k, [0] * len(v) if isinstance(v, list) else 0) != v}
            garbage = [k for k, v in got.items()
                       if k not in expected and v != tc["inputs"].get(k, 0) and nonzero(v)]
            verdicts.append(("OK", None) if not wrong and not garbage
                            else ("WRONG", {"wrong": wrong, "garbage": garbage}))
        ok = all(v == "OK" for v, _ in verdicts)
        n_all += 1
        n_ok += ok
        print(f"{'PASS' if ok else 'FAIL'}  {spec['suite']:9s} {name:16s} "
              f"{sum(v == 'OK' for v, _ in verdicts)}/{len(verdicts)}")
        for i, (v, d) in enumerate(verdicts):
            if v != "OK":
                print(f"      case{i}: {v} {d}")
    print(f"{n_ok}/{n_all} tasks pass with {args.interp}")
    return 0 if n_ok == n_all else 1


if __name__ == "__main__":
    sys.exit(main())
