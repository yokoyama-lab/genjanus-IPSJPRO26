# 実験データアーティファクト / Research Artifact

- 実験データアーティファクト No. paper260703_evidence

本ディレクトリは，以下の論文に掲載した**すべての実験数値の根拠データ（一次データ）と集計スクリプト**を収めた研究アーティファクトである（2026-07-04 作成）。論文の読者が生成AIによる機械的なチェックを容易せしめることを目的として，冗長だが十分な情報を本README.mdでは提供する．

> 牧野 透也，横山 哲郎：可逆プログラミング課題における大規模言語モデルのコード生成能力の比較評価，
> 情報処理学会 プログラミング研究会（IPSJ SIGPRO）発表予稿，2026年8月．

**English overview.**
This directory is the research artifact for our IPSJ SIGPRO paper
*"Evaluating Large Language Models on Reversible Program Synthesis under Formal Constraints."*
It contains the primary data behind every number, table, and figure in the paper —
all generation trials (prompts, raw model outputs, extracted Janus programs, and verifier
results) for the V0/V1/V2 experiments over the Basic19, Hard12, and Extreme12 task sets,
the preliminary h3 probe, the reversible Rabin–Karp case study, and the canary
(data-contamination) check — together with the exact aggregation scripts and conventions
used to produce the reported results.

---

## 1. データ形式

### 1.1 run ディレクトリ（V1・V2 共通）

各 run は次の構成をとる。

```
<run_id>/
  log.jsonl       # 1行 = 1試行×1 self-refine ラウンドの検証結果
  trials/<task>/  # trial_XXX_round_YY.{prompt.txt, txt, jan, log, cases.json}
                  #   prompt.txt: モデルへの入力全文 / txt: モデル出力全文
                  #   jan: 抽出された Janus コード / cases.json: テストケースと実行結果
```

`log.jsonl` の主なフィールド：

| フィールド | 意味 |
|---|---|
| `run_id` / `backend` / `model` | run 識別子，実行経路（codex-cli / claude-cli / gemini-cli / api），モデル名（実行時の CLI/API 指定） |
| `prompt_id` / `task` | プロンプト（p01swap 等）／タスク（h_gray_encode，h2_bwt 等） |
| `trial`, `round` | 試行番号，self-refine ラウンド（0 = 初回生成） |
| `status` | SUCCESS / SYNTAX_ERROR / RUNTIME_ERROR / WRONG_OUTPUT / GENERATION_FAIL |
| `clean` | clean termination（補助変数の完全消去・delocal 成立）を満たしたか |
| `overfit` | 提示例のみ通過し隠しケースで不合格（成功に数えない） |
| `error` | 失敗理由（検証器メッセージ，CLI タイムアウト等） |

### 1.2 V0 データ（`v0_251226/`）

タスク×モデルごとのディレクトリに，生成コード（`*.janus`），モデル出力（`*.txt`），
採点結果（`stat_*.txt`・`*_summary.csv`）を含む。論文の V0 成功率は
`stat_*.txt` の「成功したファイル（正しい出力）」件数を分母（総試行数）で割った値である
（jana で実行できても出力が誤るものは成功に数えない）。
`*_topup_*` ディレクトリは 2026-07 に試行数を 100 へ揃えるため追加生成した分である。

## 2. 成功判定と集計規約（論文の全数値はこの規約による）

1. **クリーン成功**：全テストケース通過（`status=SUCCESS`）かつ `clean=true` かつ
   `overfit=false`。self-refine を用いる設定では，ラウンド上限（Basic19 は5回，
   Hard12・Extreme12 は3回）までに一度でもクリーン成功すればその試行は成功。
2. **バックエンド失敗の除外**：レート制限・認証失効・サンドボックス不具合など，
   モデル能力に起因しない失敗（全ラウンド `GENERATION_FAIL` の試行）は分母から除外する。
   ただし **claude-cli の生成タイムアウト（拡張思考が制限時間内に停止しないもの）は
   有効試行・失敗として分母に算入**する。
3. **試行数の均一化**：各（モデル, タスク）で (run_id, trial) 順の**先頭N有効試行**を採り，
   N本に満たない分はタイムアウト＝失敗として補填して分母を固定する。
   N は Hard12 が 5（分母60＝5×12），Extreme12 が 10（分母120＝10×12。
   2026-07-04 の n=10 化以降。Gemini-3-flash-preview のみ API クレジット制約により
   7有効試行＝84），Basic19 が 10，self-refine 分析（図3）が 20 である。
4. **タスク等加重（マクロ平均）**：Extreme12 の総合値はタスクごとの成功率の単純平均。
   本規約では全タスクの分母が揃うため成功数／総試行数と一致する。
   表8の95%信頼区間は Wilson 法による（試行はタスク内で相関するため目安）。

## 3. 論文の図表 → データ → スクリプト 対応表

| 論文の図表・節 | データ | 集計/生成スクリプト |
|---|---|---|
| 図2 上段 V0（19プロンプト×3モデル, n=100） | `v0_251226/`（stat_*.txt。2026-07 の topup 分を含む。集計 xlsx 同梱） | `scripts/make_figs.py`（V0 の採点は jana [kirkedal, mult_eq ブランチ, ID 1ac57e5]＋`analyze_jana_results_detailed2.py`） |
| 図2 下段・図4 Basic19 ブロック（n=10） | `v2_basic19/`（モデル別プールは §4 参照） | `scripts/make_figs.py` の `BASIC19_N10` |
| 図3 self-refine（GPT-5.4-mini, ラウンド別累積, n=20） | `v2_basic19/20260609_gpt-5.4-mini_low_paper19/`（先頭20試行） | `scripts/make_figs.py` `fig_selfrefine` |
| 表7・図4 Hard12 ブロック（8モデル，X/120，n=10） | `v2_hard12/`（2026-07-05 に n=10 化。20260704_topup10h_{opus,g3fp,gpt54mini,g25f(+b),haiku}_hard12 を含む 16 run。Gemini 2 モデルは公式 API run＋topup） | `scripts/table7_hard12.py`（CAP=10。CAP=5 で旧 X/60 を再現） |
| 表8・図5 失敗内訳・図4 Extreme12 ブロック（10モデル，n=10） | `v2_extreme12/`（2026-07-04/05 に n=10 化。20260704_topup10_{opus,fable5,sonnet5,g35flash,gpt54,g3fp}_hard2 を含む 21 run のプール。全モデル各タスク先頭10有効試行） | `scripts/table89.py`（CAP=10。タスク等加重・失敗内訳・Wilson CI を完全再現。CAP=5 で旧 n=5 表を再現） |
| §4.3 V1（16タスク×100試行；完了1220=全成功・未完了380=CLIタイムアウト） | `v1_260308/experiment_log.jsonl` | (task, trial) ごとに SUCCESS の有無を数える単純集計 |
| §4.9 h3 予備調査（ntt / edit_distance / ackermann / suffix_array） | `h3_probe/`（Opus 4.8 = 20260702，Fable 5 = 20260703） | log.jsonl の per-task 単純集計（ntt の生成タイムアウト1件は失敗算入） |
| §5.3 生成失敗パターン1〜3のコード例 | `v2_hard12/20260612_codex_gpt-5.4_hard12`（h_cantor_pair trial 24），`v2_hard12/20260612_claude_opus_hard12`（h_modexp trial 5 round 0/1） | 本文掲載コードと逐語一致 |
| §5.5 Rabin–Karp（Opus 4.8 / Sonnet 4.6 / Fable 5） | `rabin_karp/`（hashgate＝設計調査，repro＝forward-only 各次元5試行，sonnet_rk_repro＝全試行生成不能，fable5_rk＝1D/2D 5/5・3D 4/4）＋`oracle/`（正準解）＋`rk1d_fable5.jan`（実行可能例） | 設計分類は classify_design.py（RK 実験一式に付属） |
| §6.7 カナリア実験（データ汚染の予備確認） | `canary_opus47/`（Opus 4.7×9課題：(a)識別子難読化 (b)新規合成・逆方向 (c)イディオム禁止。ログ＋raw/extracted/verified 一式＋課題定義抜粋） | log の status 集計＋raw 出力の逐語照合（汚染の明確な兆候なし） |

## 4. 各サブフォルダ

- `v0_251226/` — V0（2025-12〜2026-01 実施，2026-07 に n=100 へ補充）。
  gpt-5.2 / gpt-4.1 / gpt-5-nano，修復なし単一生成，検証器 jana（-std=janus）。
- `v1_260308/` — V1 Claude Opus 4.7（2026-05 実施）。16タスク×100試行，self-refine 最大5回。
- `v2_basic19/` — V2 Basic19 の採用 run（15 run）。モデル別プール：
  GPT-5.4-mini = 20260609；GPT-5.4 = 20260610b；GPT-5.5 = 20260610b＋topup10；
  Haiku 4.5 = 20260609＋topup 3本（2026-07-04 に全19プロンプト n=10 到達）；
  Gemini-3-flash-preview = 20260609/0610b/0612＋API topup10；
  Gemini-3.1-flash-lite = 20260610b＋API topup10；Opus 4.8/high = 20260703_opus_high_basic19。
- `v2_hard12/` — 表7の8モデル分（n=10 化の topup10h 5 run を含む 16 run）。Gemini 2 モデルは公式 API run（20260702）＋topup を採用し，gemini-cli 版 2 run は参考として収載（本文の「素朴集計12%」の根拠は `20260612_gemini_gemini-3-flash-preview_hard12`）。
- `v2_extreme12/` — 表8・図5の10モデル分（n=10 化の topup10 6 run を含む 21 run）。
- `h3_probe/` — Extreme12 を越える課題の予備調査（2 run）。
- `rabin_karp/` — 可逆 Rabin–Karp 実験一式（4 run のログと生成 .jan，オラクル，実行可能例）。
- `canary_opus47/` — §6.7 のカナリア実験一式（2026-03，Opus 4.7）。raw/ に生成原文を保存。
- `scripts/` — 集計・図生成スクリプトの正本：
  - `table89.py` — 表8（タスク等加重）・図5（失敗内訳）の集計（論文値を完全再現）
  - `table7_hard12.py` — 表7の集計（table89 と同一規約）
  - `make_figs.py` — 全図の生成（`BASIC19_N10` / `HARD12_RATES` / `EXT12_RATES` を内蔵）
  - `dump.py` / `agg_data.json` — 旧・図用集計（参考）

## 5. 再現方法

スクリプトは原本リポジトリのディレクトリ配置（`260612/runs/<run_id>` 等）を参照する。
本フォルダ単体で実行する場合は，参照先を本フォルダのサブディレクトリへ張り替えればよい：

```bash
mkdir -p shim/260612/runs shim/260607/runs
for d in v2_extreme12/*/ v2_hard12/*/; do ln -s "$(pwd)/$d" shim/260612/runs/; done
for d in v2_basic19/*/;               do ln -s "$(pwd)/$d" shim/260607/runs/; done
sed -i 's|^BASE=.*|BASE="'"$(pwd)"'/shim"|' scripts/table89.py scripts/table7_hard12.py
python3 scripts/table89.py        # 表8・図5の全数値を再現
python3 scripts/table7_hard12.py  # 表7の全数値を再現
```

（2026-07-04 に第三者環境で上記手順により表7・表8・図5の論文値の完全再現を確認済み。）

## 6. 注意事項

- モデル・バックエンド（API/CLI）の内部設定は非公開であり，同名モデルでも提供経路・
  実施時期により挙動が変わりうる。各試行の実行条件は log.jsonl の
  `backend`・`model` フィールドおよび `prompt.txt` に記録されている。
- モデル名は実行時の CLI/API 指定に基づく。Rabin–Karp の Sonnet run は
  `--model sonnet` エイリアス（デバッグログで claude-sonnet-4-6 と確認）。
- 検証器は V0 が jana（-std=janus），V1/V2 が PyJanus（jana2014 / jana2014_in_out）であり，
  世代間の数値は直接比較できない（論文 §6.1）。
- 図3（self-refine）の分母20は「先頭20**有効**試行」である。p16sqrt では試行
  33・34・36・37・39 が全ラウンド GENERATION_FAIL（バックエンド起因）のため除外され，
  対象は試行 17--32, 35, 38, 40, 41 の20本となる（この規約でログから全9系列を完全再現できる）。
- 本フォルダ内のモデル出力（`*.txt`・`*.jan` 等）は各 LLM が生成したものをそのまま保存している。

## 7. 連絡先・謝辞

- 連絡先：牧野 透也（南山大学）／横山 哲郎（南山大学）
- 本研究は JSPS 科研費 22K11983 の助成を受けたものである。
