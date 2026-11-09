# 参照実装との照合スクリプト

`programs/` の Janus プログラムを，Python の参照実装と広い入力で照合するためのものです。

## 正解データはどこから来ているか

論文の Hard12・Extreme12 では，**テストケースの期待値（`tasks.json`）は Python の参照実装から
作っています。** Janus のプログラムから作ったものではありません。参照実装は課題ごとの
単射な状態写像で，論文が「単射な参照関数」「参照実装」と呼んでいるものです。

`refs.py` は，実験ハーネス（非公開リポジトリ `tetsuo-jp/gen_janus` の
`260612/tools/hard_reference.py`，コミット de9d0fa7c）から，この 24 課題の参照実装と
検査用の定義域だけを書き換えずに抜き出したものです。`refs.py` から計算し直した期待値は，
`tasks.json` の 24 課題・全テストケースと一致します。

`programs/` の Janus プログラム（h2_heapify 以外）は，正解データとは別に手で書かれたもので，
論文には載っていません。

## 使い方

Python 3.8 以降と，Janus の処理系（PyJanus か Thomsen の jana）が要ります。外部の Python
パッケージは使いません。リポジトリの根で実行します。

```sh
python3 programs/checks/check.py --domain --interp pyjanus        # 定義域をすべて列挙
python3 programs/checks/check.py --random 150 --interp pyjanus    # 範囲を広げた乱択（課題ごとに 150 入力）
python3 programs/checks/check.py --domain --interp jana --thomsen # Thomsen の jana（thomsen/ 版を使う）
python3 programs/checks/check.py --domain --task h2_bwt           # 課題を絞る
```

各課題について，次の 2 つを数えて表示します。

- **前向き**：参照実装の出力と全変数が一致し，それ以外に非ゼロの変数が残らない
- **往復**：`call P(…)` の後に `uncall P(…)` して，全変数が入力値に戻る

`--json <file>` を付けると，課題ごとの件数と，最初に落ちた入力を保存します。

## 入力の選び方

- `--domain`：`refs.domains()` が課題ごとに決めている有界な入力をすべて試します（39〜6651 入力／課題）。
- `--random N`：定義域より大きな入力を課題ごとに N 個作ります。乱数の種は課題名から決まるので，
  何度実行しても同じ入力になります。配列は長さ 12 まで，数値は 10⁶ まで，h2_hilbert は k=6 まで，
  h2_mtf は記号 6 種・長さ 8 までです。前提を満たさない入力は参照実装の assert で除きます。
  h_cantor_pair は 1 歩ずつ数える作りで，x・y を大きくすると時間制限に当たるため，x・y ≤ 200 にしています。

長さ 0 の配列が要る入力（h2_heapify の n=1。`steps` の長さが 0 になる）は Janus で宣言できないので，
実行せずに「実行できない入力」として数えます。

## 結果（2026-11-09，PyJanus）

`result_domain_pyjanus.json` と `result_random150_pyjanus.json` に保存しています。

| 課題 | 定義域：前向き | 定義域：往復 | 乱択：前向き | 乱択：往復 |
|---|---|---|---|---|
| hard12 h_base3 | 400/400 | 400/400 | 150/150 | 150/150 |
| hard12 h_bingcd | 1200/1200 | 1200/1200 | 150/150 | 150/150 |
| hard12 h_bsort01 | 254/254 | 254/254 | 150/150 | 150/150 |
| hard12 h_cantor_pair | 1681/1681 | 1681/1681 | 150/150 | 150/150 |
| hard12 h_cantor_unpair | 401/401 | 401/401 | 150/150 | 150/150 |
| hard12 h_delta_decode | 780/780 | 780/780 | 150/150 | 150/150 |
| hard12 h_delta_encode | 780/780 | 780/780 | 150/150 | 150/150 |
| hard12 h_gray_decode | 512/512 | 512/512 | 150/150 | 150/150 |
| hard12 h_gray_encode | 513/513 | 513/513 | 150/150 | 150/150 |
| hard12 h_merge_halves | 3025/3025 | 3025/3025 | 150/150 | 150/150 |
| hard12 h_modexp | 75/75 | 75/75 | 150/150 | 150/150 |
| hard12 h_rotate_k | 306/306 | 306/306 | 150/150 | 150/150 |
| extreme12 h2_bitrev | 6651/6651 | 6651/6651 | 150/150 | 150/150 |
| extreme12 h2_bwt | 120/120 | **0/120** | 150/150 | **0/150** |
| extreme12 h2_cf_expand | 625/625 | 625/625 | 150/150 | 150/150 |
| extreme12 h2_heapify | 360/360（実行できない入力 3） | 360/360 | 150/150 | 150/150 |
| extreme12 h2_hilbert | 84/84 | 84/84 | 150/150 | 150/150 |
| extreme12 h2_kmp_failure | 126/126 | 126/126 | 150/150 | 150/150 |
| extreme12 h2_lehmer_rank | 153/153 | 153/153 | 150/150 | 150/150 |
| extreme12 h2_modinv | 199/199 | 199/199 | 150/150 | 150/150 |
| extreme12 h2_mtf | 39/39 | 39/39 | 150/150 | 150/150 |
| extreme12 h2_oesort | 340/340 | 340/340 | 150/150 | 150/150 |
| extreme12 h2_perm_inverse | 153/153 | **0/153** | 150/150 | **0/150** |
| extreme12 h2_zeckendorf | 300/300 | 300/300 | 150/150 | 150/150 |

前向きは 24/24 課題で全件一致。往復は h2_bwt と h2_perm_inverse だけが 0 件で，この 2 本は `delocal int x = x` で値を捨てているため可逆でない（`programs/README.md` 参照）。

**検査器の検出力**（変異注入）：h_gray_encode の式を `g ^= n / 4` に変えると前向きで 60 入力中 58 件が落ち（通った 2 件は n/2 と n/4 が等しい小さな n），入力 n を書き換える文を足すと 60 件すべてが落ちた。h_base3 の `delocal int d = trits % 10` を `delocal int d = d` に変えると，往復で 40 件すべてが落ちた。
