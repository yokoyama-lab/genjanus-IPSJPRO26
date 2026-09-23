# LLM 生成可逆プログラムの設計空間分類（Rabin–Karp → 全コーパス）

`rabin_karp/classify_design.py`（可逆 Rabin–Karp の成功解を forward-only / modinv-roll /
recompute の 3 類に分ける正規表現分類器）を，手元にある LLM 生成 Janus プログラム全体に一般化し，
「ガーベジをどう消すか」という設計戦略の分布を集計した。

- 分類器: `scripts/classify_design_general.py`（標準ライブラリのみ。PyJanus が `PYTHONPATH` に
  あれば AST で特徴抽出，無ければ正規表現に退避）
- 結果: `labels.csv`（Janus，1 行 = 1 ファイル，メタデータ＋ラベル＋特徴ベクトル），
  `labels_rooplpp.csv`（ROOPL++，参考・正規表現のみ）

再現:
```bash
PYTHONPATH=/path/to/pyjanus python3 scripts/classify_design_general.py --base .. --md \
  --csv analysis/design_space/labels.csv --rk-check rabin_karp/classify_design.py \
  rabin_karp/20260627_claude_opus_rk_hashgate rabin_karp/20260629_claude_opus_rk_repro \
  rabin_karp/20260703_claude_fable5_rk canary_opus47 ../gen_roopl/runs/*_janus_basic19 \
  ../gen_roopl/runs/regress_janus_reference ../gen_roopl/runs/regress_janus_reference_m3 \
  ../gen_roopl/runs/selftest_20260729_janus ../gen_roopl/runs/selftest_20260729_paper_L0_janus
python3 scripts/classify_design_general.py --ext rplpp --base .. --md \
  --csv analysis/design_space/labels_rooplpp.csv ../gen_roopl/runs/*rooplpp* \
  ../gen_roopl/runs/selftest_rooplpp_reference ../gen_roopl/runs/smoke_rooplpp_switch
```

## 1. 分類（taxonomy）と優先規則

可逆プログラムでは中間値を最後に 0 に戻す必要がある。その戻し方で分類する。

| label | 意味 | 判定に使う特徴 |
|---|---|---|
| **history** | 履歴保存（RK の forward-only）。局所配列に反復ごとの値を前進的に書き込み，後で逆順に引き戻す。局所スタックへの push も含む | `has_history_array`（要素代入 `h[i] op= ...` のある `local int h[n]`），`has_local_stack_history` |
| **algebraic-inverse** | 代数的逆（RK の modinv-roll）。履歴も再計算も使わず，数学的逆演算で更新を打ち消す | `has_modinv`（`modinv`/`dinv` の使用，`... % q = 1` を終了条件とするループ），`has_linear_swap`（`tmp += f(x); x <=> tmp; tmp -= g(x)` 型の「一時変数に新値→交換→逆式で消去」イディオム） |
| **recompute** | 再計算（Bennett）。compute–copy–uncompute | `has_uncall_pair`（同じ手続きを `call` と `uncall` の両方で使用），`has_recursion`（自己／相互再帰：呼び出しスタックが暗黙の履歴） |
| **direct** | 上記いずれも不要。可逆更新（`+=`, `<=>`, …）と局所変数の入れ子だけで書ける単一パス（swap, cycle3, rev, srch など） | 他の特徴が全て 0 |
| **other** | 構文解析も正規表現でも手続きが見つからない（空・非 Janus 出力） | — |

**優先規則（複数戦略が共存する場合の primary label）**: algebraic-inverse > history > recompute > direct。
元スクリプトの優先順（modinv > 主手続き内局所配列 > それ以外）を包含する。
`sublabel` 列に内訳（`recompute/uncall`, `recompute/recursion`, `history/array`, `history/stack`,
`algebraic/modinv`, `algebraic/linear-swap`）を残す。
`rk_label` 列は元スクリプトの 3 類をそのまま再現する（`has_modinv`→modinv-roll，
`local_arr_in_entry`→forward-only，それ以外→recompute）。

特徴ベクトル（CSV 全列）: `parse_ok, n_procs, n_call, n_uncall, n_uncall_pair, has_uncall_pair,
has_recursion, n_local_arrays, has_history_array, n_local_stacks, has_local_stack_history, n_push, n_pop,
n_swap, has_linear_swap, has_modinv, has_inline_uncompute, local_arr_in_entry, n_loops, n_if, loc, parse_fixup`。
`has_inline_uncompute`（同一手続き内で同じ `x += E` と `x -= E` が両方ある）は特徴として記録するが，
局所変数の通常の後片付けと区別できないためラベルには使わない。

### 対象コーパス（既存ファイルのみ，新規生成なし）

| family | 出所 | .jan 数 | メタデータ |
|---|---|---|---|
| rk | `rabin_karp/{opus_rk_hashgate, opus_rk_repro, fable5_rk}/trials/` | 95 | 各 run の `log.jsonl` |
| canary | `canary_opus47/extracted/` | 146 | `canary_opus47/experiment_log.jsonl` |
| basic19 | gen_roopl `runs/*_janus_basic19/trials/`（8 モデル） | 1074 | 各 run の `log.jsonl` |
| reference | gen_roopl `runs/{regress_janus_reference*, selftest_*_janus}`（人手参照解） | 72 | 同上（model=reference） |

Janus-examples リポジトリは `.j2/.j1`（別方言）のみで `.jan` を含まないため対象外。
V0/V1/V2 の生成コードは本リポジトリに含まれない（ログのみ）ため対象外。

## 2. RK 後方互換の検証

RK 3 run の SUCCESS・clean・非 overfit の最終 .jan（重複行を除いた **27 ファイル**）について，
`rk_label` と元 `classify_design.py` の `classify()` 出力を比較した結果 **一致 27 / 27，不一致 0**
（`--rk-check` で再現）。元スクリプトの出力が 43 件になるのは `fable5_rk/log.jsonl` に同一
(task, trial, round) の重複行が 13 組あるため（ファイル単位では 27）。

一般ラベルとの対応: modinv-roll ⇔ algebraic-inverse（3），forward-only ⇔ history（9），
recompute ⇔ recompute（15）。RK 全 95 ファイル（失敗含む）では `direct` が 2 件現れる
（局所配列も uncall も無い単一パスの誤答）。

## 3. 分布表（Janus）

以下「LLM files」は reference（人手解）72 件を除いた 1315 件。件数（行内 %）。

### (a) label × task-family

| family | history | algebraic-inverse | recompute | direct | n |
|---|---|---|---|---|---|
| rk | 17 (18%) | 8 (8%) | 68 (72%) | 2 (2%) | 95 |
| canary | 0 | 0 | 5 (3%) | 141 (97%) | 146 |
| basic19 | 0 | 8 (1%) | 255 (24%) | 811 (76%) | 1074 |
| reference（人手） | 0 | 0 | 24 (33%) | 48 (67%) | 72 |

- RK のみ history / algebraic-inverse が現れる。Basic19・canary では「戦略が要る」課題でも
  recompute（uncall か再帰）が実質唯一の戦略で，履歴配列は 0 件。
- 課題別（LLM vs 人手解）: fact / fib / fibp / gcd / sqrt / srchB は人手解が recompute だが，
  LLM は gcd 52%，fibp 45%，sqrt 87%，srchB 85% を direct で書く（多くは失敗解，§(c) 参照）。
  逆に perm2code / rle / srchA / rev は人手解 direct，LLM も 79–90% direct。
  swap / cycle3 / flipsign / even / max2 は全件 direct。

### (b) label × model（LLM files）

| family/model | history | algebraic-inverse | recompute | direct | n |
|---|---|---|---|---|---|
| basic19/fable | 0 | 0 | 14 (23%) | 46 (77%) | 60 |
| basic19/gpt-5.4 | 0 | 1 (1%) | 68 (58%) | 48 (41%) | 117 |
| basic19/gpt-5.4-mini | 0 | 3 (2%) | 54 (29%) | 128 (69%) | 185 |
| basic19/gpt-5.5 | 0 | 1 (0%) | 41 (18%) | 180 (81%) | 222 |
| basic19/gpt-5.6-luna | 0 | 0 | 33 (19%) | 141 (81%) | 174 |
| basic19/haiku | 0 | 3 (2%) | 22 (13%) | 144 (85%) | 169 |
| basic19/opus | 0 | 0 | 18 (29%) | 44 (71%) | 62 |
| basic19/sonnet | 0 | 0 | 5 (6%) | 80 (94%) | 85 |
| canary/opus-4.7-canary | 0 | 0 | 5 (3%) | 141 (97%) | 146 |
| rk/opus | 9 (12%) | 8 (11%) | 54 (74%) | 2 (3%) | 73 |
| rk/claude-fable-5 | 6 (33%) | 0 | 12 (67%) | 0 | 18 |
| rk/?（log 行なし） | 2 | 0 | 2 | 0 | 4 |

gpt-5.4 は Basic19 でも recompute が 58% と突出（自己再帰型が多い）。RK では opus のみが
modinv 型を選び，fable5 は history か recompute のみ。ファイル数は self-refine ラウンド分を含む
（失敗が多いモデルほど行数が多い）。

### (c) label × status — 戦略は成功を予測するか

| status（LLM files） | history | algebraic-inverse | recompute | direct | n |
|---|---|---|---|---|---|
| SUCCESS | 9 (2%) | 3 (1%) | 96 (18%) | 440 (80%) | 548 |
| IRREVERSIBLE | 0 | 4 (1%) | 83 (28%) | 213 (71%) | 300 |
| RUNTIME_ERROR | 1 (0%) | 6 (2%) | 95 (28%) | 241 (70%) | 343 |
| WRONG_OUTPUT | 1 (2%) | 1 (2%) | 17 (27%) | 43 (69%) | 62 |
| NO_HASH（RK 専用） | 4 (10%) | 2 (5%) | 35 (83%) | 1 (2%) | 42 |
| SYNTAX_ERROR | 0 | 0 | 0 | 16 (100%) | 16 |

ラベル別成功率（SUCCESS / 件数）:

| family | history | algebraic-inverse | recompute | direct |
|---|---|---|---|---|
| rk | 9/17 (53%) | 3/8 (38%) | 15/68 (22%) | 0/2 |
| canary | — | — | 0/5 (0%) | 81/141 (57%) |
| basic19 | — | 0/8 (0%) | 81/255 (32%) | 359/811 (44%) |

- RK では **history（履歴配列）が最も成功率が高く（53%），recompute は 22%**。RK の失敗の主因
  NO_HASH（ハッシュを使わず総当たり）は 83% が recompute 型で，「uncall で消す」書き方の
  プログラムほどハッシュ更新を諦める傾向がある。
- Basic19 では direct（44%）> recompute（32%）だが，これは課題難度の混在による
  （direct は swap/cycle3 等の易課題を含む）。人手解が recompute の課題で同一課題内比較すると，
  gcd は recompute 15/39（38%）に対し direct 5/43（12%），fibp は recompute 16/40（40%）vs
  direct 6/34（18%），srchB は 7/13 vs 16/76。一方 sqrt は direct 24/52 vs recompute 1/8 と逆
  （`labels.csv` から集計可）。「戦略が要る課題で戦略を持たない解」は概ね失敗しやすい。
- algebraic-inverse（linear-swap 型）は Basic19 で 8 件全て失敗（fib で `a <=> d; d -= b - a`
  のような逆式を誤る）。RK の modinv 型は 3/8。

### (d) label × round — self-refine は戦略を変えるか

round 0 と最終 round の両方に .jan がある試行 **223 件**（RK 19，canary 37，basic19 167）の遷移:

| round 0 → 最終 | 件数 |
|---|---|
| direct → direct | 138 |
| recompute → recompute | 38 |
| direct → recompute | 26 |
| recompute → direct | 7 |
| recompute → history | 5 |
| recompute → algebraic-inverse | 3 |
| algebraic-inverse → recompute | 2 |
| その他（各 1） | 4 |
| **不変** | **178 / 223 (80%)** |

修復ラウンドの 80% は戦略を変えず局所修正に留まる。変える場合は direct→recompute
（uncall を導入して後片付けを追加）が最多。RK に限ると不変 9/19（47%）で，recompute→history 5，
recompute→algebraic 3 と「再計算から履歴・逆元へ」の移行が見られる（元 `classify_design.py`
が成功解で forward-only を多く数えたのは，この修復後の姿である）。

## 4. 参考: ROOPL++（gen_roopl，正規表現のみ）

同じ規則を `.rplpp`（3024 LLM 件 + 38 参照解）に適用（`--ext rplpp`。`method` を手続き，
`new int[n] a` / `local int[] a`（main 以外）を局所配列と読み替え。PyJanus は使わないため精度は
Janus より低い）。LLM: history 125 (4%) / algebraic 40 (1%) / recompute 779 (26%) / direct 2080 (69%)。
成功率は history 17%，algebraic 12%，recompute 30%，direct 44%。perm2code で history が 49%
（符号配列を別途確保）と Janus 版（0%）と対照的。round 遷移不変 459/535（86%）。

## 5. 限界・注記

- **解析経路**: Janus 1387 件のうち PyJanus（現行 main，`jana2014_in_out`）で 1336 件が解析成功。
  うち 45 件は `local int a = 0, b = 1`（型省略の複数宣言。実験当時の PyJanus は受理）を
  `local int a = 0, int b = 1` に正規化して解析（`parse_fixup=1`）。**51 件（3.7%）が正規表現退避**
  （`parse_ok=0`）：`end`, `{}`，`;`，自然言語の混入など非 Janus 出力がほとんどで，全て失敗解。
- **ラベルなし**: `fable5_rk/trials/rk3/trial_005_round_0{0..3}.jan` の 4 件は log.jsonl に対応行が無く
  status 空（表では `no-log`）。gen_roopl の GENERATION_FAIL 行（230）は .jan が無く対象外。
- **ヒューリスティックの限界**: `has_recursion` は再帰全般を recompute に含める（fact の自然再帰も
  含む；`sublabel` で `recompute/recursion` として分離可）。`has_linear_swap` は文リスト内の
  `+=`→`<=>`→`-=` の順序のみ見るため，偶然の並びを拾う可能性がある。パラメタ配列を履歴に流用する
  設計や，inline の手作業 uncompute（`x += E … x -= E`）は history / recompute に数えない（`direct`）。
- 反復回数の違い（失敗試行ほど round 数が多い）により，ファイル単位の集計は失敗解に重みが付く。
  試行単位の集計は `labels.csv` の (run, task, trial, round) から行える。
- 元スクリプトのデータファイル・`classify_design.py` は変更していない。
