"""Hard12・Extreme12 の Python 参照実装と、検査に使う入力の定義域。

論文の実験ハーネス genjanus（非公開リポジトリ tetsuo-jp/gen_janus の
260612/tools/hard_reference.py、コミット de9d0fa7c）から、この 24 課題に関わる部分だけを
そのまま抜き出したもの（2026-11-09）。tasks.json の期待値は、この参照実装から作られている。

各参照関数は「全状態 → 全状態」の写像（dict → dict）で、単射である。
出力の dict は全パラメータを含む（期待値が全変数を決め、期待外の非ゼロ変数＝ゴミを許さない）。
前提を満たさない入力には assert で失敗する。
"""

import itertools
import math

# ============================================================
# 参照実装（単射な状態写像）
# ============================================================

def gray_encode(s):
    """g := n XOR floor(n/2)。n 不変。"""
    n, g = s["n"], s["g"]
    assert n >= 0 and g == 0
    return {"n": n, "g": n ^ (n >> 1)}


def gray_decode(s):
    """n := g ^ g/2 ^ g/4 ^ ...、steps = 項数。g 不変。"""
    g, n, steps = s["g"], s["n"], s["steps"]
    assert g >= 1 and n == 0 and steps == 0
    d = 1
    while g // d > 0:
        n ^= g // d
        d *= 2
        steps += 1
    return {"g": g, "n": n, "steps": steps}


def cantor_pair(s):
    """z := (x+y)(x+y+1)/2 + y。x, y は 0 に消費（全単射 N^2 -> N）。"""
    x, y, z = s["x"], s["y"], s["z"]
    assert x >= 0 and y >= 0 and z == 0
    return {"x": 0, "y": 0, "z": (x + y) * (x + y + 1) // 2 + y}


def cantor_unpair(s):
    """cantor_pair の逆: z から (x, y) を復元、z は 0 に。"""
    z, x, y = s["z"], s["x"], s["y"]
    assert z >= 0 and x == 0 and y == 0
    w = 0
    while (w + 1) * (w + 2) // 2 <= z:
        w += 1
    y = z - w * (w + 1) // 2
    x = w - y
    return {"z": 0, "x": x, "y": y}


def rotate_k(s):
    """先頭 n 要素を左に k 回転（置換。n, k 不変）。"""
    a, n, k = list(s["a"]), s["n"], s["k"]
    assert 0 < k < n and len(a) == n
    return {"a": a[k:] + a[:k], "n": n, "k": k}


def delta_encode(s):
    """a[i] := 元の a[i] - a[i-1] (1 <= i < n)。a[0], n 不変。"""
    a, n = list(s["a"]), s["n"]
    assert n >= 1 and len(a) == n
    out = [a[0]] + [a[i] - a[i - 1] for i in range(1, n)]
    return {"a": out, "n": n}


def delta_decode(s):
    """a[i] := 元の a[0..i] の前置和。delta_encode の逆。n 不変。"""
    a, n = list(s["a"]), s["n"]
    assert n >= 1 and len(a) == n
    out = []
    acc = 0
    for v in a:
        acc += v
        out.append(acc)
    return {"a": out, "n": n}


def bsort01(s):
    """0/1 配列を昇順整列 + 元のビット列を trace に LSB-first でパック。n 不変。"""
    a, n, trace = list(s["a"]), s["n"], s["trace"]
    assert trace == 0 and len(a) == n and all(v in (0, 1) for v in a)
    trace = sum(v << i for i, v in enumerate(a))
    return {"a": sorted(a), "n": n, "trace": trace}


def base3(s):
    """n を3進数に消費変換: trits = 3進桁を10進にパック、cnt = 桁数。n -> 0。"""
    n, trits, cnt = s["n"], s["trits"], s["cnt"]
    assert n >= 1 and trits == 0 and cnt == 0
    w = 1
    while n > 0:
        trits += (n % 3) * w
        n //= 3
        w *= 10
        cnt += 1
    return {"n": 0, "trits": trits, "cnt": cnt}


def bingcd(s):
    """二進(Stein)GCD + 分岐 trace。x=gcd, y=0、flags は4進分岐列、steps は反復数。"""
    x, y, steps, flags = s["x"], s["y"], s["steps"], s["flags"]
    assert x >= 1 and y >= 1 and not (x % 2 == 0 and y % 2 == 0)
    assert steps == 0 and flags == 0
    while x != y:
        if x % 2 == 0:
            x //= 2
            d = 0
        elif y % 2 == 0:
            y //= 2
            d = 1
        elif x > y:
            x -= y
            d = 2
        else:
            y -= x
            d = 3
        flags = flags * 4 + d
        steps += 1
    y -= x  # y = 0, x = gcd
    return {"x": x, "y": y, "steps": steps, "flags": flags}


def merge_halves(s):
    """a の2つの整列区間 (m個 + n個) を b にマージ消費。全移動の出所ビットを trace に記録。

    全 m+n ステップでビットを記録する（0=左区間、1=右区間。最初の移動が最上位）。
    m, n が保存されるためビット長 = m+n が確定し、先頭ゼロも復元可能 → 単射。
    （両側非空時のみ記録する版は先頭ゼロが潰れて非単射だった。--check-injective で検出済み）
    """
    a, b, m, n, trace = list(s["a"]), list(s["b"]), s["m"], s["n"], s["trace"]
    assert m >= 1 and n >= 1 and len(a) == m + n and len(b) == m + n
    assert trace == 0 and all(v == 0 for v in b)
    left, right = a[:m], a[m:]
    assert left == sorted(left) and right == sorted(right)
    i = j = 0
    out = []
    while i < m or j < n:
        take_left = j >= n or (i < m and left[i] <= right[j])  # 同値は左を優先
        if take_left:
            out.append(left[i])
            i += 1
            trace = trace * 2 + 0
        else:
            out.append(right[j])
            j += 1
            trace = trace * 2 + 1
    return {"a": [0] * (m + n), "b": out, "m": m, "n": n, "trace": trace}


def modexp(s):
    """r := base^e mod m を e 回の乗算で計算し、各 mod の商を q[i] に銀行。e -> 0。"""
    base, e, m, r, q = s["base"], s["e"], s["m"], s["r"], list(s["q"])
    assert base >= 1 and m >= 2 and e >= 1 and r == 1
    assert len(q) == e and all(v == 0 for v in q)
    for i in range(e):
        r *= base
        q[i] = r // m
        r -= q[i] * m
    return {"base": base, "e": 0, "m": m, "r": r, "q": q}


# ============================================================
# hard2 taskset（260612b_hard_tasks/README.md の12題）の参照実装
# ============================================================


def zeckendorf(s):
    """n を Zeckendorf 表現（Fibonacci 進法）に消費変換。z=10進パック、cnt=桁数。"""
    n, z, cnt = s["n"], s["z"], s["cnt"]
    assert n >= 1 and z == 0 and cnt == 0
    fibs = [1, 2]  # F2, F3, ...
    while fibs[-1] + fibs[-2] <= n:
        fibs.append(fibs[-1] + fibs[-2])
    while fibs and fibs[-1] > n:
        fibs.pop()
    cnt = len(fibs)
    rem = n
    for i in range(len(fibs) - 1, -1, -1):
        if fibs[i] <= rem:
            rem -= fibs[i]
            z += 10 ** i
    assert rem == 0
    return {"n": 0, "z": z, "cnt": cnt}


def cf_expand(s):
    """(a, b) の連分数展開（Euclid 商列）。a=gcd, b=0 に、q[] へ位置詰め、cnt=反復数。"""
    a, b, q, cnt = s["a"], s["b"], list(s["q"]), s["cnt"]
    assert a >= 1 and b >= 1 and cnt == 0 and all(v == 0 for v in q)
    i = 0
    while b != 0:
        q[i] = a // b
        a, b = b, a % b
        i += 1
    assert i <= len(q)
    return {"a": a, "b": 0, "q": q, "cnt": i}


def bitrev(s):
    """長さ 2^k の配列にビット反転置換（FFT 並べ替え）を適用。対合・ゴミゼロ。"""
    a, k = list(s["a"]), s["k"]
    n = 1 << k
    assert len(a) == n and k >= 1

    def rev(i):
        r = 0
        for _ in range(k):
            r = r * 2 + i % 2
            i //= 2
        return r

    out = [a[rev(i)] for i in range(n)]
    return {"a": out, "k": k}


def modinv(s):
    """inv = a^{-1} mod m（拡張 Euclid）。商列を q[] に、cnt=反復数。a, m 不変。"""
    import math
    a, m, inv, q, cnt = s["a"], s["m"], s["inv"], list(s["q"]), s["cnt"]
    assert 1 <= a < m and m >= 2 and math.gcd(a, m) == 1
    assert inv == 0 and cnt == 0 and all(v == 0 for v in q)
    r0, r1, i = m, a, 0
    while r1 != 0:
        q[i] = r0 // r1
        r0, r1 = r1, r0 % r1
        i += 1
    assert i <= len(q)
    return {"a": a, "m": m, "inv": pow(a, -1, m), "q": q, "cnt": i}


def mtf(s):
    """Move-to-Front 変換。a を in-place で MTF 符号列に、sym は最終アルファベット順列に。"""
    a, sym, n, k = list(s["a"]), list(s["sym"]), s["n"], s["k"]
    assert len(a) == n and sym == list(range(k)) and all(0 <= v < k for v in a)
    for t in range(n):
        c = sym.index(a[t])
        a[t] = c
        sym = [sym[c]] + sym[:c] + sym[c + 1:]
    return {"a": a, "sym": sym, "n": n, "k": k}


def oesort(s):
    """奇偶転置ソート。比較器スケジュールは n で確定し、全比較の swap bit を trace に。"""
    a, n, trace = list(s["a"]), s["n"], s["trace"]
    assert trace == 0 and len(a) == n and n >= 1
    for r in range(n):
        i = r % 2
        while i + 1 < n:
            if a[i] > a[i + 1]:
                a[i], a[i + 1] = a[i + 1], a[i]
                bit = 1
            else:
                bit = 0
            trace = trace * 2 + bit
            i += 2
    return {"a": a, "n": n, "trace": trace}


def heapify(s):
    """Floyd build-max-heap。比較ごとに（子選択bit, swap bit）を trace に 4進で積み、
    ノード i の比較回数を steps[i] に記録（可変長 trace の境界を確定させる）。"""
    a, n, steps, trace = list(s["a"]), s["n"], list(s["steps"]), s["trace"]
    assert len(a) == n and len(steps) == n // 2 and trace == 0
    assert all(v == 0 for v in steps)
    for i in range(n // 2 - 1, -1, -1):
        j = i
        while 2 * j + 1 < n:
            l, r = 2 * j + 1, 2 * j + 2
            if r < n and a[r] > a[l]:
                c, cb = r, 1
            else:
                c, cb = l, 0
            if a[c] > a[j]:
                a[c], a[j] = a[j], a[c]
                sb = 1
            else:
                sb = 0
            trace = trace * 4 + cb * 2 + sb
            steps[i] += 1
            if sb == 0:
                break
            j = c
    return {"a": a, "n": n, "steps": steps, "trace": trace}


def lehmer_rank(s):
    """順列 p を Lehmer ランク r（階乗進法）に全消費。S_n <-> [0, n!) の純全単射。"""
    import math
    p, n, r = list(s["p"]), s["n"], s["r"]
    assert sorted(p) == list(range(n)) and r == 0
    rank = 0
    for i in range(n):
        smaller = sum(1 for j in range(i + 1, n) if p[j] < p[i])
        rank += smaller * math.factorial(n - 1 - i)
    return {"p": [0] * n, "n": n, "r": rank}


def perm_inverse(s):
    """順列を in-place で逆順列に置換（p⁻¹[p[i]] = i）。S_n 上の対合・ゴミゼロ。"""
    p, n = list(s["p"]), s["n"]
    assert sorted(p) == list(range(n))
    q = [0] * n
    for i, v in enumerate(p):
        q[v] = i
    return {"p": q, "n": n}


def kmp_failure(st):
    """KMP 接頭辞関数 pi と、各位置での fallback 回数 fb（巻き戻し証書）。s 不変。"""
    s, pi, n, fb = list(st["s"]), list(st["pi"]), st["n"], list(st["fb"])
    assert len(s) == len(pi) == len(fb) == n and n >= 1
    assert all(v == 0 for v in pi) and all(v == 0 for v in fb)
    k = 0
    for i in range(1, n):
        c = 0
        while k > 0 and s[k] != s[i]:
            k = pi[k - 1]
            c += 1
        if s[k] == s[i]:
            k += 1
        pi[i] = k
        fb[i] = c
    return {"s": s, "pi": pi, "n": n, "fb": fb}


def hilbert(s):
    """Hilbert 曲線 d -> (x, y)（次数 k）。d を 0 に消費する純全単射。"""
    d, k, x, y = s["d"], s["k"], s["x"], s["y"]
    n = 1 << k
    assert 0 <= d < n * n and x == 0 and y == 0 and k >= 1
    t = d
    x = y = 0
    sz = 1
    while sz < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x = sz - 1 - x
                y = sz - 1 - y
            x, y = y, x
        x += sz * rx
        y += sz * ry
        t //= 4
        sz *= 2
    return {"d": 0, "k": k, "x": x, "y": y}


def bwt(st):
    """Burrows–Wheeler 変換。s を in-place で BWT(s) に置換し primary index を idx に。"""
    s, n, idx = list(st["s"]), st["n"], st["idx"]
    assert len(s) == n and idx == 0 and n >= 1
    rots = [s[i:] + s[:i] for i in range(n)]
    order = sorted(range(n), key=lambda i: rots[i])
    out = [rots[i][-1] for i in order]
    return {"s": out, "n": n, "idx": order.index(0)}


# ============================================================
# hard3（260618c のクリーン可逆化 旗艦5題。極力 trace を残さない純全単射）
# ============================================================


REFS = {
    "h_base3": base3,
    "h_bingcd": bingcd,
    "h_bsort01": bsort01,
    "h_cantor_pair": cantor_pair,
    "h_cantor_unpair": cantor_unpair,
    "h_delta_decode": delta_decode,
    "h_delta_encode": delta_encode,
    "h_gray_decode": gray_decode,
    "h_gray_encode": gray_encode,
    "h_merge_halves": merge_halves,
    "h_modexp": modexp,
    "h_rotate_k": rotate_k,
    "h2_bitrev": bitrev,
    "h2_bwt": bwt,
    "h2_cf_expand": cf_expand,
    "h2_heapify": heapify,
    "h2_hilbert": hilbert,
    "h2_kmp_failure": kmp_failure,
    "h2_lehmer_rank": lehmer_rank,
    "h2_modinv": modinv,
    "h2_mtf": mtf,
    "h2_oesort": oesort,
    "h2_perm_inverse": perm_inverse,
    "h2_zeckendorf": zeckendorf,
}


def _sorted_tuples(length, lo, hi):
    return [t for t in itertools.product(range(lo, hi + 1), repeat=length)
            if list(t) == sorted(t)]


def domains():
    """課題名 -> 入力状態のイテレータ。宣言した定義域の有界な部分をすべて列挙する。"""
    doms = {}
    doms["h_gray_encode"] = ({"n": n, "g": 0} for n in range(0, 513))
    doms["h_gray_decode"] = ({"g": g, "n": 0, "steps": 0} for g in range(1, 513))
    doms["h_cantor_pair"] = ({"x": x, "y": y, "z": 0}
                             for x in range(0, 41) for y in range(0, 41))
    doms["h_cantor_unpair"] = ({"z": z, "x": 0, "y": 0} for z in range(0, 401))
    doms["h_rotate_k"] = ({"a": list(t), "n": n, "k": k}
                          for n in range(2, 5) for k in range(1, n)
                          for t in itertools.product(range(0, 3), repeat=n))
    doms["h_delta_encode"] = ({"a": list(t), "n": n}
                              for n in range(1, 5)
                              for t in itertools.product(range(-2, 3), repeat=n))
    doms["h_delta_decode"] = ({"a": list(t), "n": n}
                              for n in range(1, 5)
                              for t in itertools.product(range(-2, 3), repeat=n))
    doms["h_bsort01"] = ({"a": list(t), "n": n, "trace": 0}
                         for n in range(1, 8)
                         for t in itertools.product((0, 1), repeat=n))
    doms["h_base3"] = ({"n": n, "trits": 0, "cnt": 0} for n in range(1, 401))
    doms["h_bingcd"] = ({"x": x, "y": y, "steps": 0, "flags": 0}
                        for x in range(1, 41) for y in range(1, 41)
                        if not (x % 2 == 0 and y % 2 == 0))
    doms["h_merge_halves"] = ({"a": list(lt) + list(rt), "b": [0] * (m + n),
                               "m": m, "n": n, "trace": 0}
                              for m in range(1, 4) for n in range(1, 4)
                              for lt in _sorted_tuples(m, 0, 4)
                              for rt in _sorted_tuples(n, 0, 4))
    doms["h_modexp"] = ({"base": b, "e": e, "m": m, "r": 1, "q": [0] * e}
                        for b in range(1, 6) for m in range(2, 7)
                        for e in range(1, 4))

    # ---- hard2（260612b の12題）----
    doms["h2_zeckendorf"] = ({"n": n, "z": 0, "cnt": 0} for n in range(1, 301))
    doms["h2_cf_expand"] = ({"a": a, "b": b, "q": [0] * 8, "cnt": 0}
                            for a in range(1, 26) for b in range(1, 26))
    doms["h2_bitrev"] = ({"a": list(t), "k": k}
                         for k in range(1, 4)
                         for t in itertools.product(range(0, 3), repeat=1 << k))
    doms["h2_modinv"] = ({"a": a, "m": m, "inv": 0, "q": [0] * 8, "cnt": 0}
                         for m in range(2, 26) for a in range(1, m)
                         if math.gcd(a, m) == 1)
    doms["h2_mtf"] = ({"a": list(t), "sym": list(range(3)), "n": n, "k": 3}
                      for n in range(1, 4)
                      for t in itertools.product(range(3), repeat=n))
    doms["h2_oesort"] = ({"a": list(t), "n": n, "trace": 0}
                         for n in range(1, 5)
                         for t in itertools.product(range(-1, 3), repeat=n))
    doms["h2_heapify"] = ({"a": list(t), "n": n, "steps": [0] * (n // 2),
                           "trace": 0}
                          for n in range(1, 6)
                          for t in itertools.product(range(0, 3), repeat=n))
    doms["h2_lehmer_rank"] = ({"p": list(t), "n": n, "r": 0}
                              for n in range(1, 6)
                              for t in itertools.permutations(range(n)))
    doms["h2_perm_inverse"] = ({"p": list(t), "n": n}
                               for n in range(1, 6)
                               for t in itertools.permutations(range(n)))
    doms["h2_kmp_failure"] = ({"s": list(t), "pi": [0] * n, "n": n,
                               "fb": [0] * n}
                              for n in range(1, 7)
                              for t in itertools.product((1, 2), repeat=n))
    doms["h2_hilbert"] = ({"d": d, "k": k, "x": 0, "y": 0}
                          for k in range(1, 4) for d in range(4 ** k))
    doms["h2_bwt"] = ({"s": list(t), "n": n, "idx": 0}
                      for n in range(1, 5)
                      for t in itertools.product(range(1, 4), repeat=n))
    return doms
