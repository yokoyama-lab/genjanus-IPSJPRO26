# V0（2025-12-26，jana 採点）の PyJanus 再採点と世代間比較表

論文の表4（V0：gpt-5.2 / gpt-4.1 / gpt-5-nano，19 課題 × 100 生成，Haskell 版 `jana -std=janus` で採点）を，
V1・V2 と同じ検証器 PyJanus（`--std jana2014`）で再採点し，V0〜V2 を Basic19 の課題 id で揃えた
世代間比較表を再構築した。生成（LLM 呼び出し）は一切行っていない。既存の .janus をそのまま採点し直しただけである。

- 結果（CSV）: `v0_rescore_by_prompt_model.csv`（§4 の表(d)），`cross_generation_table.csv`（§5 の表(e)）
- 採点器: PyJanus commit `e0cd78ff0ace`（2026-07-17，yokoyama-lab/pyjanus main）
- スクリプト: `scripts/`（`build_manifest.py` / `score.py` / `v2_agg.py` / `final_agg.py`，§7 参照）
- 注意: 採点・集計は，V0 の .janus コーパス本体を持つ tetsuo-jp/gen_janus 上の別コンテナで行った。
  本アーティファクト・リポジトリの `v0_251226/` には `stat_*.txt`（jana の採点結果）しか収載していないため，
  1 ファイル 1 行の全件 CSV（8,325 プログラム × 2 std = 16,650 行，`final_agg.py` が出力する
  `v0_pyjanus_rescore.csv`）はここには含めず，集計表（上記 2 CSV）とスクリプトのみを収める。

## 1. 対象コーパスの棚卸し

- gen_janus/251226/: 130 ディレクトリ，8,857 .janus。論文の正本集合（= paper260703_evidence/v0_251226
  にミラーされたディレクトリ ＝ 本リポジトリの `v0_251226/`）は 118 ディレクトリ，8,325 プログラム
  （誤命名の `stat_*.janus` 1 件を除外。この 1 件は論文の p16sqrt gpt-5.2 の分母 101 に数えられていた）。
  ファイル名トークンによるモデル別件数: gpt5_2 3,609 / gpt4_1 2,635 / gpt5-nano 2,081。
- 「正本 run（canonical）」= jana の判定が表4を正確に再現する run 群（規則: すべての `*topup*` ディレクトリ
  ＋ n を 100 に揃える最新の非 topup ディレクトリ）。この選択規則で表4の jana 成功率が全 57 セルで一致した。
  正本 n = 5,696（19 × 3 × 100。ただし p10fact gpt-5-nano n=97，p14srchA gpt-5-nano n=99 — 論文の分母と同一）。
  V0 の p18fib（300 件，Basic19 に対応枠なし）は正本集合から除外。非正本ディレクトリ（差し替え前の初回 run，
  `_botsu`，`_mid`，`_todelete`，claude_opus4_5）も採点したが，全件 CSV にのみ含める。
- jana の 1 ファイルごとの判定: 各ディレクトリの `stat_*.txt` から読み取り（7,905 件）。stat ファイルが壊れていた
  4 ディレクトリはディレクトリ内の jana_check_results ログから元の集計器と同じアルゴリズムで再導出（299 件）。
  122 件は jana 判定が得られない。
- V0 → Basic19 の id 対応（表4を再現することで検証済み）: p01swap→p01，p02swap→p02，p03–p06cycle3→p03–p06，
  p08flipsign→p07flipsign，p07max→p08max2，p09even→p09，p11factorial→p10fact，p12gcd→p11gcd，
  p15fibpair→p12fibp，p10arrayreverse→p13rev，p13linearsearch→p14srchA，p14linearsearch→p15srchB，
  p19sqrt→p16sqrt，p16rle→p17rle，p20perm2code→p18perm2code，p17fib→p19fib。V0 の p18fib（英語 fib プロンプト）
  は Basic19 に対応枠がない。
- V1: `v1_260308/experiment_log.jsonl`（Opus 4.7，16 課題 × 100 試行。1,343 行が GENERATION_FAIL = claude CLI の
  タイムアウト）。V2: README §4 に列挙した paper19 の 15 run のプール（＋ 20260702_gemini_api_…_p17rle）。
  「有効 10 件先取り」規則での再計算は `make_figs.BASIC19_N10` と 133 セル中 132 セルで一致（Haiku p11gcd: 2 対 論文 3）。

## 2. 方言対応の決定

- V0 のプログラムは古典 Jana そのものである: `procedure main()`，型付き引数，`local/delocal`，
  `from/do/loop/until`，`if/then/else/fi`，配列 `int a[] = {…}`。read/write は使わない。
  PyJanus の DIALECTS.md によれば，`jana2014` は上流 Haskell 版 `Jana.Parser` の移植（全文法。出力は `-s` による
  最終ストアのダンプで，jana と同じ形式），`jana2014_in_out` は jana2014 ＋ 厳格な read/write。
  したがって jana `-std=janus` ≙ PyJanus `--std jana2014`。
- PyJanus の jana2014 と jana2014_in_out は正本ファイル全件で判定が一致。正本ファイルにおける jana と
  PyJanus(jana2014) の一致率: 5321/5696 = 93.4%。

## 3. 混同行列（正本 V0 ファイル。行 = jana 判定，列 = PyJanus jana2014）

| | SUCCESS | WRONG_OUTPUT | SYNTAX_ERROR | RUNTIME_ERROR | TIMEOUT | total |
|---|---|---|---|---|---|---|
| SUCCESS | 1140 | 0 | 3 | 0 | 0 | 1143 |
| WRONG_OUTPUT | 0 | 322 | 17 | 3 | 7 | 349 |
| SYNTAX_ERROR | 43 | 1 | 1709 | 242 | 1 | 1996 |
| RUNTIME_ERROR | 37 | 12 | 9 | 2150 | 0 | 2208 |
| total | 1220 | 335 | 1738 | 2395 | 8 | 5696 |

不一致の内訳:

| jana 判定 → PyJanus(jana2014) | n | PyJanus の主なメッセージ |
|---|---|---|
| SYNTAX_ERROR → RUNTIME_ERROR | 242 | Assertion failed: should be false (151); Expected value to be `X' for local variable `X' (36); Assertion failed: should be true (29) |
| SYNTAX_ERROR → SUCCESS | 43 | (ran to completion) |
| RUNTIME_ERROR → SUCCESS | 37 | (ran to completion) |
| WRONG_OUTPUT → SYNTAX_ERROR | 17 | Unexpected end of input (17) |
| RUNTIME_ERROR → WRONG_OUTPUT | 12 | (ran to completion) |
| RUNTIME_ERROR → SYNTAX_ERROR | 9 | Unexpected "~" (7); Variable name `X' is already bound (2) |
| WRONG_OUTPUT → TIMEOUT | 7 | |
| SUCCESS → SYNTAX_ERROR | 3 | Unexpected "~" (3) |
| WRONG_OUTPUT → RUNTIME_ERROR | 3 | Couldn't match expected type `X' (2); Assertion failed: should be false (1) |
| SYNTAX_ERROR → TIMEOUT / WRONG_OUTPUT | 1 / 1 | |

## 4. 表(d): V0 の課題 × モデル別 — jana（論文）対 PyJanus

Py_in_out（jana2014_in_out）は全セルで Py2014 と同一のため列を省く。W/SY/RT/TO = WRONG_OUTPUT / SYNTAX_ERROR /
RUNTIME_ERROR / TIMEOUT の件数。CSV 版: `v0_rescore_by_prompt_model.csv`。

| Basic19 | V0 prompt | model | n | jana ✓ | jana % | paper % | Py2014 ✓ | Py2014 % | Py2014: W/SY/RT/TO |
|---|---|---|---|---|---|---|---|---|---|
| p01swap | p01swap | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 0/100/0/0 |
| p01swap | p01swap | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/100/0/0 |
| p01swap | p01swap | gpt-5-nano | 100 | 0 | 0 | 0 | 0 | 0 | 0/100/0/0 |
| p02swap | p02swap | gpt-5.2 | 100 | 95 | 95 | 95 | 95 | 95 | 0/3/2/0 |
| p02swap | p02swap | gpt-4.1 | 100 | 81 | 81 | 81 | 81 | 81 | 2/16/1/0 |
| p02swap | p02swap | gpt-5-nano | 100 | 94 | 94 | 94 | 94 | 94 | 0/5/1/0 |
| p03cycle3 | p03cycle3 | gpt-5.2 | 100 | 9 | 9 | 9 | 9 | 9 | 11/22/58/0 |
| p03cycle3 | p03cycle3 | gpt-4.1 | 100 | 26 | 26 | 26 | 26 | 26 | 56/13/5/0 |
| p03cycle3 | p03cycle3 | gpt-5-nano | 100 | 72 | 72 | 72 | 73 | 73 | 2/18/7/0 |
| p04cycle3 | p04cycle3 | gpt-5.2 | 100 | 8 | 8 | 8 | 8 | 8 | 11/8/73/0 |
| p04cycle3 | p04cycle3 | gpt-4.1 | 100 | 33 | 33 | 33 | 33 | 33 | 47/12/8/0 |
| p04cycle3 | p04cycle3 | gpt-5-nano | 100 | 76 | 76 | 76 | 77 | 77 | 1/16/6/0 |
| p05cycle3 | p05cycle3 | gpt-5.2 | 100 | 36 | 36 | 36 | 36 | 36 | 4/8/52/0 |
| p05cycle3 | p05cycle3 | gpt-4.1 | 100 | 17 | 17 | 17 | 17 | 17 | 50/16/17/0 |
| p05cycle3 | p05cycle3 | gpt-5-nano | 100 | 67 | 67 | 67 | 67 | 67 | 2/29/2/0 |
| p06cycle3 | p06cycle3 | gpt-5.2 | 100 | 36 | 36 | 36 | 36 | 36 | 24/4/36/0 |
| p06cycle3 | p06cycle3 | gpt-4.1 | 100 | 21 | 21 | 21 | 21 | 21 | 11/19/49/0 |
| p06cycle3 | p06cycle3 | gpt-5-nano | 100 | 69 | 69 | 69 | 73 | 73 | 2/25/0/0 |
| p07flipsign | p08flipsign | gpt-5.2 | 100 | 5 | 5 | 5 | 6 | 6 | 11/7/76/0 |
| p07flipsign | p08flipsign | gpt-4.1 | 100 | 7 | 7 | 7 | 9 | 9 | 4/15/72/0 |
| p07flipsign | p08flipsign | gpt-5-nano | 100 | 12 | 12 | 12 | 19 | 19 | 0/42/39/0 |
| p08max2 | p07max | gpt-5.2 | 100 | 32 | 32 | 32 | 35 | 35 | 1/24/40/0 |
| p08max2 | p07max | gpt-4.1 | 100 | 23 | 23 | 23 | 24 | 24 | 4/15/57/0 |
| p08max2 | p07max | gpt-5-nano | 100 | 35 | 35 | 35 | 41 | 41 | 10/17/32/0 |
| p09even | p09even | gpt-5.2 | 100 | 94 | 94 | 94 | 94 | 94 | 1/0/5/0 |
| p09even | p09even | gpt-4.1 | 100 | 78 | 78 | 78 | 86 | 86 | 6/2/6/0 |
| p09even | p09even | gpt-5-nano | 100 | 61 | 61 | 61 | 98 | 98 | 0/2/0/0 |
| p10fact | p11factorial | gpt-5.2 | 100 | 16 | 16 | 16 | 16 | 16 | 6/6/71/1 |
| p10fact | p11factorial | gpt-4.1 | 100 | 13 | 13 | 13 | 15 | 15 | 33/13/39/0 |
| p10fact | p11factorial | gpt-5-nano | 97 | 6 | 6 | 6 | 6 | 6 | 1/69/21/0 |
| p11gcd | p12gcd | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 0/19/81/0 |
| p11gcd | p12gcd | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/29/71/0 |
| p11gcd | p12gcd | gpt-5-nano | 100 | 0 | 0 | 0 | 0 | 0 | 0/64/35/1 |
| p12fibp | p15fibpair | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 0/26/74/0 |
| p12fibp | p15fibpair | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/10/90/0 |
| p12fibp | p15fibpair | gpt-5-nano | 100 | 2 | 2 | 2 | 3 | 3 | 0/63/34/0 |
| p13rev | p10arrayreverse | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 1/2/97/0 |
| p13rev | p10arrayreverse | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/18/82/0 |
| p13rev | p10arrayreverse | gpt-5-nano | 100 | 6 | 6 | 6 | 6 | 6 | 0/55/39/0 |
| p14srchA | p13linearsearch | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 1/29/70/0 |
| p14srchA | p13linearsearch | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/11/89/0 |
| p14srchA | p13linearsearch | gpt-5-nano | 99 | 0 | 0 | 0 | 0 | 0 | 0/84/15/0 |
| p15srchB | p14linearsearch | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 5/17/78/0 |
| p15srchB | p14linearsearch | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/9/91/0 |
| p15srchB | p14linearsearch | gpt-5-nano | 100 | 0 | 0 | 0 | 0 | 0 | 0/81/19/0 |
| p16sqrt | p19sqrt | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 0/93/7/0 |
| p16sqrt | p19sqrt | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 1/6/93/0 |
| p16sqrt | p19sqrt | gpt-5-nano | 100 | 0 | 0 | 0 | 0 | 0 | 15/57/28/0 |
| p17rle | p16rle | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 0/16/83/1 |
| p17rle | p16rle | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/36/64/0 |
| p17rle | p16rle | gpt-5-nano | 100 | 0 | 0 | 0 | 0 | 0 | 2/98/0/0 |
| p18perm2code | p20perm2code | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 0/8/88/4 |
| p18perm2code | p20perm2code | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/10/89/1 |
| p18perm2code | p20perm2code | gpt-5-nano | 100 | 13 | 13 | 13 | 16 | 16 | 9/65/10/0 |
| p19fib | p17fib | gpt-5.2 | 100 | 0 | 0 | 0 | 0 | 0 | 0/23/77/0 |
| p19fib | p17fib | gpt-4.1 | 100 | 0 | 0 | 0 | 0 | 0 | 0/11/89/0 |
| p19fib | p17fib | gpt-5-nano | 100 | 0 | 0 | 0 | 0 | 0 | 1/72/27/0 |

モデル別（19 課題プール）:

| V0 model (19 prompts pooled) | n | jana ✓ | PyJanus jana2014 ✓ | PyJanus in_out ✓ |
|---|---|---|---|---|
| gpt-5.2 | 1900 | 331 (17.4%) | 335 (17.6%) | 335 (17.6%) |
| gpt-4.1 | 1900 | 299 (15.7%) | 312 (16.4%) | 312 (16.4%) |
| gpt-5-nano | 1896 | 513 (27.1%) | 573 (30.2%) | 573 (30.2%) |

## 5. 表(e): 世代間比較表（Basic19 id，clean success の %）

V0 = PyJanus(jana2014) 再採点，単発生成（pass@1，n≈100）。V1 = Opus 4.7，self-refine ≤5
（round-0 % / final %。分母はバックエンドが有効だった試行。括弧内は CLI タイムアウトを含む全 100 試行に対する値）。
V2 = paper19 run のプール，self-refine ≤5，SUCCESS∧clean∧¬overfit，round-0 % / final %
（n = 有効試行数。全プールであり，論文の「先頭 10 件」規則ではない）。CSV 版: `cross_generation_table.csv`。

| Basic19 | V0 gpt-5.2 | V0 gpt-4.1 | V0 gpt-5-nano | V1 task | V1 r0 / final % (valid n; all-100) | V2 Opus 4.8/high | V2 Gemini-3-flash-prev | V2 GPT-5.4/low | V2 GPT-5.5/low | V2 GPT-5.4-mini/low | V2 Gemini-3.1-flash-lite | V2 Haiku 4.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p01swap | 0 | 0 | 0 | swap | 100 / 100 (n=90; 90 / 90) | 17/100 (12) | 100/100 (12) | 65/100 (20) | 76/97 (38) | 8/88 (48) | 0/17 (12) | 80/90 (10) |
| p02swap | 95 | 81 | 94 | swap | 100 / 100 (n=90; 90 / 90) | 100/100 (12) | 100/100 (12) | 100/100 (18) | 100/100 (24) | 98/100 (48) | 55/100 (11) | 100/100 (10) |
| p03cycle3 | 9 | 26 | 73 | cycle3 | 100 / 100 (n=87; 87 / 87) | 100/100 (12) | 92/100 (12) | 100/100 (18) | 100/100 (24) | 90/100 (48) | 55/64 (11) | 100/100 (10) |
| p04cycle3 | 8 | 33 | 77 | cycle3 | 100 / 100 (n=87; 87 / 87) | 100/100 (12) | 100/100 (12) | 100/100 (18) | 100/100 (24) | 100/100 (48) | 55/82 (11) | 100/100 (10) |
| p05cycle3 | 36 | 17 | 67 | cycle3 | 100 / 100 (n=87; 87 / 87) | 100/100 (12) | 100/100 (12) | 100/100 (18) | 100/100 (18) | 100/100 (48) | 55/73 (11) | 100/100 (10) |
| p06cycle3 | 36 | 21 | 73 | cycle3 | 100 / 100 (n=87; 87 / 87) | 100/100 (12) | 100/100 (12) | 100/100 (18) | 100/100 (18) | 94/100 (48) | 55/91 (11) | 100/100 (10) |
| p07flipsign | 6 | 9 | 19 | negate | 68 / 100 (n=68; 46 / 68) | 100/100 (12) | 92/100 (12) | 89/100 (18) | 100/100 (18) | 100/100 (48) | 91/100 (11) | 100/100 (10) |
| p08max2 | 35 | 24 | 41 | max_min* | 100 / 100 (n=85; 85 / 85) | 100/100 (12) | 92/100 (12) | 100/100 (18) | 100/100 (18) | 100/100 (48) | 91/100 (11) | 100/100 (10) |
| p09even | 94 | 86 | 98 | — | — | 100/100 (12) | 92/100 (12) | 94/100 (18) | 100/100 (18) | 100/100 (48) | 100/100 (11) | 100/100 (10) |
| p10fact | 16 | 15 | 6 | factorial | 95 / 100 (n=38; 36 / 38) | 100/100 (12) | 100/100 (12) | 100/100 (18) | 100/100 (18) | 79/100 (48) | 64/82 (11) | 90/90 (10) |
| p11gcd | 0 | 0 | 0 | gcd | 100 / 100 (n=30; 30 / 30) | 83/100 (12) | 75/100 (12) | 83/100 (18) | 22/89 (18) | 6/48 (33) | 18/36 (11) | 8/25 (12) |
| p12fibp | 0 | 0 | 3 | — | — | 100/100 (12) | 92/100 (12) | 83/100 (18) | 22/83 (18) | 3/41 (32) | 0/27 (11) | 0/10 (10) |
| p13rev | 0 | 0 | 6 | — | — | 83/100 (12) | 100/100 (12) | 72/100 (18) | 50/100 (14) | 9/91 (32) | 27/55 (11) | 10/40 (10) |
| p14srchA | 0 | 0 | 0 | — | — | 75/100 (12) | 75/100 (12) | 94/100 (18) | 33/100 (12) | 0/28 (32) | 9/18 (11) | 0/0 (10) |
| p15srchB | 0 | 0 | 0 | — | — | 83/100 (12) | 92/100 (12) | 67/94 (18) | 25/100 (12) | 10/60 (20) | 18/55 (11) | 20/30 (10) |
| p16sqrt | 0 | 0 | 0 | isqrt | 98 / 100 (n=43; 42 / 43) | 100/100 (12) | 100/100 (12) | 56/94 (18) | 67/100 (12) | 23/36 (22) | 27/82 (11) | 10/70 (10) |
| p17rle | 0 | 0 | 0 | — | — | 100/100 (12) | 50/100 (12) | 0/22 (18) | 0/8 (12) | 0/0 (20) | 0/0 (11) | 0/0 (10) |
| p18perm2code | 0 | 0 | 16 | — | — | 91/100 (11) | 83/100 (12) | 50/94 (18) | 0/67 (12) | 0/4 (24) | 0/9 (11) | 0/0 (10) |
| p19fib | 0 | 0 | 0 | fibonacci* | 86 / 100 (n=14; 12 / 14) | 0/100 (4) | 17/42 (12) | 8/17 (12) | 0/0 (12) | 0/0 (21) | 0/36 (11) | 0/0 (10) |

対応付けの注意: V1 は 16 課題で，Basic19 に対応するのは 8 課題のみ，しかも近似的である。
`max_min*`（x←max，y←min ＋ swapped フラグ）≠ p08max2；`fibonacci*` ≠ p19fib の仕様；`swap` は p01/p02 の両方に対応
（p01 の V0 解答ファイルは文字列 "dummy" そのもの ⇒ V0 p01 は構成上 0%）；`cycle3` は p03–p06 に対応。
Basic19 に対応枠のない V1 課題: collatz，digit_sum，div_mod，gcd_nohint，is_prime，power，reverse_num，sort3。
V1 の難課題で分母が極端に小さいのは，1,600 試行のうち 1,343 が claude CLI 内で死んだためである。

## 6. 注意事項

- PyJanus の「preprocessing error」（`#` コメント行）と「validation error」（procedure の重複 / main なし /
  local の再束縛）は SYNTAX_ERROR に畳み込んだ。jana はこれらを `File "…"` 接頭辞付きで報告し，元の集計器は
  それを構文エラーとして数えている。
- PyJanus は jana より寛容: jana が構文解析で拒否した正本ファイル 287 件が PyJanus では実行される。
  jana が `fi t == (x >= y)`，`until i >= len / 2`，`delocal int max = m` のような式の後で "Expecting statement"
  を出すもの（145 件），条件中の `==`（92），識別子への単項マイナス（43），`;` 区切り（7）。
  うち 242 件は PyJanus の実行時アサーションで失敗し，43 件が SUCCESS，1 件が WRONG_OUTPUT，1 件が TIMEOUT になる。
  また jana の実行時エラー 49 件が PyJanus では走る（37 SUCCESS，12 WRONG_OUTPUT）: jana の
  "Couldn't match expected type"（27）と，`delocal int t = t` に対する jana のエイリアス検査（22。PyJanus は
  `x -= x` や `call f(t,t)` は拒否するが，自己参照 delocal は通す）。
  差し引きで PyJanus の成功数は jana より多い（5,696 件中 1,220 対 1,143）。gpt-5.2 / gpt-4.1 / gpt-5-nano で
  それぞれ +0.2 / +0.7 / +3.1 ポイント。動きの大きいセル: p09even gpt-5-nano 61→98，gpt-4.1 78→86；
  p07flipsign nano 12→19；p08max2 nano 35→41。
- PyJanus が厳格な点: ビット反転 `~` は jana2014 文法にない。正本の flipsign 10 件が該当し，うち jana-SUCCESS
  3 件が SYNTAX_ERROR になる（jana の成功が失われる唯一のケース）。非正本では，最初の procedure より前の
  トップレベル文を PyJanus は拒否するが jana は読み飛ばす（2 件）。
- 元の採点の副産物: jana が "More than one main procedure defined" でクラッシュした正本 17 件を，元の集計器は
  成功/誤った出力として数えていた。PyJanus では SYNTAX_ERROR。成功率には影響しない。
- タイムアウト: 1 プログラム `-t 10`（外側で `timeout 20`）。jana は `timeout 100s` を使っていた。
  正本 8 件が PyJanus でタイムアウトし，`-t 100` で再実行しても依然タイムアウト。いずれも両検証器で失敗。
- p01swap はどの検証器でも 0（解答ファイルが "dummy"。300 プログラムすべてが両検証器で構文エラーでもある）。
  jana2014 と jana2014_in_out は全ファイルで同一。
- LLM 生成は行っていない。8,325 プログラム × 2 std をすべて採点（16,650 行。8 ワーカー，9 分）。

## 7. 再現手順

スクリプトは `scripts/` にある。前提となる配置は次のとおり（パスはスクリプト内にハードコードされている）:

- gen_janus のチェックアウト（V0 コーパス `251226/`，`paper260703_evidence/`，V2 の `260607/runs/`）が `/home/claude/gen_janus`
- PyJanus のチェックアウトが `/home/claude/pyjanus`（`score.py` が `PYTHONPATH` に設定）
- 作業ディレクトリ S: `final_agg.py` 冒頭の `S=` にハードコードされたパスを自分の作業ディレクトリに書き換える。
  `final_agg.py` は S から `manifest.csv`，`scores_raw.csv`，`v2_basic19_agg.json` を読み，
  `OUT`（既定 `/home/claude`）に `v0_pyjanus_rescore.csv`・`v0_rescore_by_prompt_model.csv`・`cross_generation_table.csv` を書く。

実行順序: (1) `build_manifest.py > manifest.csv`；(2) `jobs.txt`（各行 `<file> <std>`）を作り
`xargs -P 8 -L 1 python3 score.py < jobs.txt > scores_raw.csv`；(3) `v2_agg.py v2_basic19_agg.csv`
（cwd = gen_janus。同名の `.json` も出力）；(4) `final_agg.py`。

```
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/yokoyama-lab/pyjanus /home/claude/pyjanus   # e0cd78f
python3 build_manifest.py > manifest.csv          # 118 artifact dirs -> file,dir,prompt,model,jana_status (stat_*.txt / log fallback)
tail -n +2 manifest.csv | cut -d, -f1 | awk '{print $0" jana2014"; print $0" jana2014_in_out"}' > jobs.txt
xargs -P 8 -L 1 python3 score.py < jobs.txt > scores_raw.csv
#   score.py: cd gen_janus; timeout 20 env PYTHONPATH=/home/claude/pyjanus python3 -m jana_py.cli --std $STD -s -t 10 $FILE </dev/null 2>&1
#   status: rc==124 -> TIMEOUT; 'PyJanus parsing error' -> SYNTAX_ERROR; 'PyJanus execution error' -> RUNTIME_ERROR; other rc!=0 -> OTHER_ERROR
#   else SUCCESS iff 251226/<v0prompt>_answer.txt lines occur as consecutive rstripped output lines (sliding window, as analyze_jana_results_detailed2.py), else WRONG_OUTPUT
python3 v2_agg.py v2_basic19_agg.csv               # V2 pool, valid-trial + first-10 cross-check vs make_figs.BASIC19_N10
python3 final_agg.py                               # canonical selection, matrices, tables, cross-gen
```
