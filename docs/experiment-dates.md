# 実験実施時期の根拠（2026-09-25確認）

対象データのコミット：`d55cf01ac2a3112281caf3144994367afc5d7a9a`。
対象はこの公開アーティファクトに収録された実験ログであり、元ハーネスでの後続実験全体ではない。

## 概要

| 実験 | 収録ログから確認できる記録日 | 根拠・範囲 |
|---|---|---|
| V0 当初分 | 2025-12-26〜28（run名の日付） | `v0_251226/` の当初分ディレクトリ。各試行の開始・終了時刻ではない |
| V0 補充分 | 2026-07-03（run名の日付） | `v0_251226/*topup*`。READMEの従来表記は2026-07 |
| V1 本文掲載の Opus 4.7 | 2026-05-22〜24 | `v1_260308/experiment_log.jsonl`。探索環境全体の期間とは別 |
| V2 Basic19 | 2026-06-09〜2026-07-04 | `v2_basic19/` の15ログ。補充・再実行を含む |
| V2 Hard12 | 2026-06-12〜2026-07-05 | `v2_hard12/` の16ログ。参考CLI run・再実行も含む |
| V2 Extreme12 | 2026-06-13〜2026-07-05 | `v2_extreme12/` の21ログ。集計対象外の予備runも含む |
| h3 予備調査 | 2026-07-02〜03 | Opusのログは07-02、Fableのログは07-03 |
| Rabin–Karp | 2026-06-27〜2026-07-04 | hashgate、forward-only、Sonnet、Fableの4ログ |
| カナリア実験 | 2026-05-23 | `canary_opus47/experiment_log.jsonl` |

日付は各ログの `timestamp` を読み取り、記録されている暦日をそのまま示した。
これらのフィールドにはタイムゾーン指定がないため、UTC/JSTへの変換は行っていない。
範囲の両端は最初・最後の**ログ記録時刻**であり、実験開始・終了時刻や、その間の連続実行を保証しない。
失敗、self-refine の各ラウンド、後日の補充・再実行も含む。採用試行だけの実施期間ではない。
run名・ディレクトリ名、アーティファクトの作成日、Gitコミット日、ファイル更新日は実験日時と区別する。
V0 は同じ形式の試行別 `timestamp` がないため、run名から分かる日付に限定した。
従来の「2025-12〜2026-01」というV0の説明に対し、この収録データのrun名だけでは2026-01の実施日は特定できない。

## ディレクトリ名と実施日の相違

- `v1_260308/` の本文掲載ログは2026-05-22〜24。`260308` を実施日とは解釈しない。
- カナリアの旧READMEにあった「2026-03」は、収録ログの2026-05-23と一致しないため、ログに基づいて訂正した。
- `rabin_karp/20260629_claude_sonnet_rk_repro/` の記録日は2026-06-30。
- Fable の Rabin–Karp は2026-07-03〜04。run名の07-03だけでは再開分を表せない。
- Hard12の一部の `20260612_*` runには2026-07-02の再実行が含まれる。採用規約はREADME §2の3bに従う。
- 2026-07の推論エフォート追試など、このアーティファクトに対応ログがない実験については、本一覧から実施日を断定しない。

## 各ログの記録日

「行数」はJSONLレコード数であり、独立試行数や有効試行数ではない。

| ログ | 最初の記録 | 最後の記録 | 行数 | 記録のある日（不連続日を含む） |
|---|---|---|---:|---|
| [v1_260308/experiment_log.jsonl](../v1_260308/experiment_log.jsonl) | 2026-05-22T22:43:13.310176 | 2026-05-24T01:13:06.976293 | 2623 | 2026-05-22, 2026-05-23, 2026-05-24 |
| [v2_basic19/20260609_gemini_gemini-3-flash-preview_paper19/log.jsonl](../v2_basic19/20260609_gemini_gemini-3-flash-preview_paper19/log.jsonl) | 2026-06-09T23:41:27.989394 | 2026-06-10T01:59:17.732148 | 114 | 2026-06-09, 2026-06-10 |
| [v2_basic19/20260609_gpt-5.4-mini_low_paper19/log.jsonl](../v2_basic19/20260609_gpt-5.4-mini_low_paper19/log.jsonl) | 2026-06-09T20:12:57.868717 | 2026-07-03T01:44:25.324979 | 2746 | 2026-06-09, 2026-06-10, 2026-07-03 |
| [v2_basic19/20260609_haiku_paper19/log.jsonl](../v2_basic19/20260609_haiku_paper19/log.jsonl) | 2026-06-09T09:48:08.659364 | 2026-06-09T11:22:46.090508 | 105 | 2026-06-09 |
| [v2_basic19/20260610b_codex_gpt-5.4_paper19/log.jsonl](../v2_basic19/20260610b_codex_gpt-5.4_paper19/log.jsonl) | 2026-06-10T18:46:58.504001 | 2026-06-11T07:15:05.921595 | 555 | 2026-06-10, 2026-06-11 |
| [v2_basic19/20260610b_codex_gpt-5.5_paper19/log.jsonl](../v2_basic19/20260610b_codex_gpt-5.5_paper19/log.jsonl) | 2026-06-10T23:28:50.743503 | 2026-06-11T07:44:37.220453 | 562 | 2026-06-10, 2026-06-11 |
| [v2_basic19/20260610b_gemini_gemini-3-flash-preview_paper19/log.jsonl](../v2_basic19/20260610b_gemini_gemini-3-flash-preview_paper19/log.jsonl) | 2026-06-11T00:15:41.051412 | 2026-06-11T08:45:20.636811 | 131 | 2026-06-11 |
| [v2_basic19/20260610b_gemini_gemini-3.1-flash-lite_paper19/log.jsonl](../v2_basic19/20260610b_gemini_gemini-3.1-flash-lite_paper19/log.jsonl) | 2026-06-10T23:14:40.433782 | 2026-06-11T10:21:33.880236 | 314 | 2026-06-10, 2026-06-11 |
| [v2_basic19/20260612_gemini_gemini-3-flash-preview_paper19/log.jsonl](../v2_basic19/20260612_gemini_gemini-3-flash-preview_paper19/log.jsonl) | 2026-06-12T19:22:34.200523 | 2026-06-12T20:18:49.979993 | 104 | 2026-06-12 |
| [v2_basic19/20260703_codex_gpt-5.5_paper19_topup10/log.jsonl](../v2_basic19/20260703_codex_gpt-5.5_paper19_topup10/log.jsonl) | 2026-07-03T06:49:13.111863 | 2026-07-03T06:55:51.225738 | 62 | 2026-07-03 |
| [v2_basic19/20260703_gemini_api_gemini-3-flash-preview_paper19_topup10/log.jsonl](../v2_basic19/20260703_gemini_api_gemini-3-flash-preview_paper19_topup10/log.jsonl) | 2026-07-03T06:50:25.412068 | 2026-07-03T07:29:08.921333 | 54 | 2026-07-03 |
| [v2_basic19/20260703_gemini_api_gemini-3.1-flash-lite_paper19_topup10/log.jsonl](../v2_basic19/20260703_gemini_api_gemini-3.1-flash-lite_paper19_topup10/log.jsonl) | 2026-07-03T17:05:27.013925 | 2026-07-03T17:15:03.238934 | 442 | 2026-07-03 |
| [v2_basic19/20260703_haiku_paper19_topup/log.jsonl](../v2_basic19/20260703_haiku_paper19_topup/log.jsonl) | 2026-07-03T00:52:38.155745 | 2026-07-03T03:21:23.034500 | 71 | 2026-07-03 |
| [v2_basic19/20260703_haiku_paper19_topup10/log.jsonl](../v2_basic19/20260703_haiku_paper19_topup10/log.jsonl) | 2026-07-03T06:52:10.455190 | 2026-07-03T07:16:23.388264 | 59 | 2026-07-03 |
| [v2_basic19/20260703_haiku_paper19_topup10b/log.jsonl](../v2_basic19/20260703_haiku_paper19_topup10b/log.jsonl) | 2026-07-03T22:50:12.739401 | 2026-07-04T01:43:43.937193 | 146 | 2026-07-03, 2026-07-04 |
| [v2_basic19/20260703_opus_high_basic19/log.jsonl](../v2_basic19/20260703_opus_high_basic19/log.jsonl) | 2026-07-03T08:26:28.536920 | 2026-07-03T10:31:09.325776 | 247 | 2026-07-03 |
| [v2_hard12/20260612_claude_haiku_hard12/log.jsonl](../v2_hard12/20260612_claude_haiku_hard12/log.jsonl) | 2026-06-12T21:24:45.885169 | 2026-07-02T04:33:46.975883 | 266 | 2026-06-12, 2026-07-02 |
| [v2_hard12/20260612_claude_opus_hard12/log.jsonl](../v2_hard12/20260612_claude_opus_hard12/log.jsonl) | 2026-06-12T21:24:37.752957 | 2026-07-02T06:33:32.081049 | 83 | 2026-06-12, 2026-07-02 |
| [v2_hard12/20260612_codex_gpt-5.4_hard12/log.jsonl](../v2_hard12/20260612_codex_gpt-5.4_hard12/log.jsonl) | 2026-06-12T21:25:12.742076 | 2026-06-13T13:34:59.951032 | 443 | 2026-06-12, 2026-06-13 |
| [v2_hard12/20260612_codex_gpt-5.5_hard12/log.jsonl](../v2_hard12/20260612_codex_gpt-5.5_hard12/log.jsonl) | 2026-06-13T02:56:28.413578 | 2026-06-13T13:55:51.293982 | 602 | 2026-06-13 |
| [v2_hard12/20260612_gemini_gemini-2.5-flash_hard12/log.jsonl](../v2_hard12/20260612_gemini_gemini-2.5-flash_hard12/log.jsonl) | 2026-06-13T22:04:29.875449 | 2026-07-02T10:08:46.832863 | 347 | 2026-06-13, 2026-06-14, 2026-07-02 |
| [v2_hard12/20260612_gemini_gemini-3-flash-preview_hard12/log.jsonl](../v2_hard12/20260612_gemini_gemini-3-flash-preview_hard12/log.jsonl) | 2026-06-13T00:54:39.112664 | 2026-07-02T09:08:20.571516 | 428 | 2026-06-13, 2026-06-14, 2026-07-02 |
| [v2_hard12/20260612_gemini_gemini-3.1-flash-lite_hard12/log.jsonl](../v2_hard12/20260612_gemini_gemini-3.1-flash-lite_hard12/log.jsonl) | 2026-06-12T22:31:18.901678 | 2026-06-14T06:18:39.804321 | 1052 | 2026-06-12, 2026-06-13, 2026-06-14 |
| [v2_hard12/20260612_gpt-5.4-mini_low_hard12/log.jsonl](../v2_hard12/20260612_gpt-5.4-mini_low_hard12/log.jsonl) | 2026-06-12T21:25:10.859939 | 2026-07-02T01:37:38.408087 | 545 | 2026-06-12, 2026-07-02 |
| [v2_hard12/20260702_api_gemini-2.5-flash_hard12/log.jsonl](../v2_hard12/20260702_api_gemini-2.5-flash_hard12/log.jsonl) | 2026-07-02T14:11:43.378466 | 2026-07-02T15:12:38.146080 | 190 | 2026-07-02 |
| [v2_hard12/20260702_api_gemini-3-flash-preview_hard12/log.jsonl](../v2_hard12/20260702_api_gemini-3-flash-preview_hard12/log.jsonl) | 2026-07-02T14:11:43.518410 | 2026-07-02T14:39:15.631907 | 79 | 2026-07-02 |
| [v2_hard12/20260704_topup10h_g25f_hard12/log.jsonl](../v2_hard12/20260704_topup10h_g25f_hard12/log.jsonl) | 2026-07-04T13:16:49.899701 | 2026-07-04T14:29:05.103028 | 187 | 2026-07-04 |
| [v2_hard12/20260704_topup10h_g25f_hard12b/log.jsonl](../v2_hard12/20260704_topup10h_g25f_hard12b/log.jsonl) | 2026-07-04T22:56:43.313698 | 2026-07-04T23:04:40.949591 | 19 | 2026-07-04 |
| [v2_hard12/20260704_topup10h_g3fp_hard12/log.jsonl](../v2_hard12/20260704_topup10h_g3fp_hard12/log.jsonl) | 2026-07-04T12:39:56.569289 | 2026-07-04T13:16:41.607491 | 77 | 2026-07-04 |
| [v2_hard12/20260704_topup10h_gpt54mini_hard12/log.jsonl](../v2_hard12/20260704_topup10h_gpt54mini_hard12/log.jsonl) | 2026-07-04T12:43:42.060950 | 2026-07-04T13:26:34.028173 | 99 | 2026-07-04 |
| [v2_hard12/20260704_topup10h_haiku_hard12/log.jsonl](../v2_hard12/20260704_topup10h_haiku_hard12/log.jsonl) | 2026-07-04T19:55:54.171355 | 2026-07-05T11:12:24.238740 | 201 | 2026-07-04, 2026-07-05 |
| [v2_hard12/20260704_topup10h_opus_hard12/log.jsonl](../v2_hard12/20260704_topup10h_opus_hard12/log.jsonl) | 2026-07-04T18:38:56.700498 | 2026-07-04T19:55:42.840719 | 51 | 2026-07-04 |
| [v2_extreme12/20260613_claude_haiku_hard2/log.jsonl](../v2_extreme12/20260613_claude_haiku_hard2/log.jsonl) | 2026-06-13T01:30:49.564599 | 2026-06-18T10:52:57.866509 | 1458 | 2026-06-13, 2026-06-17, 2026-06-18 |
| [v2_extreme12/20260613_claude_opus_hard2/log.jsonl](../v2_extreme12/20260613_claude_opus_hard2/log.jsonl) | 2026-06-13T07:27:07.329972 | 2026-06-22T08:19:21.331491 | 74 | 2026-06-13, 2026-06-18, 2026-06-21, 2026-06-22 |
| [v2_extreme12/20260613_codex_gpt-5.5_hard2/log.jsonl](../v2_extreme12/20260613_codex_gpt-5.5_hard2/log.jsonl) | 2026-06-13T21:33:37.321299 | 2026-06-18T19:03:56.844566 | 1405 | 2026-06-13, 2026-06-14, 2026-06-16, 2026-06-17, 2026-06-18 |
| [v2_extreme12/20260616_gemini_gemini-3.1-flash-lite_hard2/log.jsonl](../v2_extreme12/20260616_gemini_gemini-3.1-flash-lite_hard2/log.jsonl) | 2026-06-16T23:58:54.533879 | 2026-06-18T07:40:15.365636 | 1164 | 2026-06-16, 2026-06-17, 2026-06-18 |
| [v2_extreme12/20260618_codex_gpt-5.4-mini_hard2/log.jsonl](../v2_extreme12/20260618_codex_gpt-5.4-mini_hard2/log.jsonl) | 2026-06-18T18:04:49.321900 | 2026-06-19T08:12:45.425630 | 1375 | 2026-06-18, 2026-06-19 |
| [v2_extreme12/20260618_codex_gpt-5.4_hard2/log.jsonl](../v2_extreme12/20260618_codex_gpt-5.4_hard2/log.jsonl) | 2026-06-18T18:04:49.487861 | 2026-06-19T17:57:21.409739 | 587 | 2026-06-18, 2026-06-19 |
| [v2_extreme12/20260624_api_gemini-3.5-flash_hard2/log.jsonl](../v2_extreme12/20260624_api_gemini-3.5-flash_hard2/log.jsonl) | 2026-06-24T00:58:58.677536 | 2026-06-24T09:33:09.578589 | 211 | 2026-06-24 |
| [v2_extreme12/20260702_claude_sonnet5_hard2/log.jsonl](../v2_extreme12/20260702_claude_sonnet5_hard2/log.jsonl) | 2026-07-02T13:37:37.586980 | 2026-07-02T17:55:12.664911 | 74 | 2026-07-02 |
| [v2_extreme12/20260702_codex_gpt-5.4_extreme3fill/log.jsonl](../v2_extreme12/20260702_codex_gpt-5.4_extreme3fill/log.jsonl) | 2026-07-02T14:12:43.624135 | 2026-07-02T14:36:18.093829 | 55 | 2026-07-02 |
| [v2_extreme12/20260703_api_g3fp_hard2/log.jsonl](../v2_extreme12/20260703_api_g3fp_hard2/log.jsonl) | 2026-07-03T08:30:22.188656 | 2026-07-03T10:08:50.611842 | 185 | 2026-07-03 |
| [v2_extreme12/20260703_claude_fable5_low_hard2/log.jsonl](../v2_extreme12/20260703_claude_fable5_low_hard2/log.jsonl) | 2026-07-03T01:38:16.810025 | 2026-07-03T02:18:36.112826 | 62 | 2026-07-03 |
| [v2_extreme12/20260703_topup_gpt54_hard2/log.jsonl](../v2_extreme12/20260703_topup_gpt54_hard2/log.jsonl) | 2026-07-03T07:31:49.538874 | 2026-07-03T08:26:26.740044 | 92 | 2026-07-03 |
| [v2_extreme12/20260703_topup_opus_hard2/log.jsonl](../v2_extreme12/20260703_topup_opus_hard2/log.jsonl) | 2026-07-03T07:33:00.292829 | 2026-07-03T08:32:35.963715 | 39 | 2026-07-03 |
| [v2_extreme12/20260703_topup_opus_hard2b/log.jsonl](../v2_extreme12/20260703_topup_opus_hard2b/log.jsonl) | 2026-07-03T15:48:10.590613 | 2026-07-03T15:48:10.658612 | 3 | 2026-07-03 |
| [v2_extreme12/20260703_topup_sonnet5_hard2/log.jsonl](../v2_extreme12/20260703_topup_sonnet5_hard2/log.jsonl) | 2026-07-03T15:46:27.090609 | 2026-07-03T15:56:27.228874 | 5 | 2026-07-03 |
| [v2_extreme12/20260704_topup10_fable5_hard2/log.jsonl](../v2_extreme12/20260704_topup10_fable5_hard2/log.jsonl) | 2026-07-04T17:47:06.306389 | 2026-07-04T18:36:15.095947 | 72 | 2026-07-04 |
| [v2_extreme12/20260704_topup10_g35flash_hard2/log.jsonl](../v2_extreme12/20260704_topup10_g35flash_hard2/log.jsonl) | 2026-07-04T01:31:53.682444 | 2026-07-04T01:51:05.685074 | 16 | 2026-07-04 |
| [v2_extreme12/20260704_topup10_g3fp_hard2/log.jsonl](../v2_extreme12/20260704_topup10_g3fp_hard2/log.jsonl) | 2026-07-04T22:53:25.912178 | 2026-07-05T00:10:05.744800 | 79 | 2026-07-04, 2026-07-05 |
| [v2_extreme12/20260704_topup10_gpt54_hard2/log.jsonl](../v2_extreme12/20260704_topup10_gpt54_hard2/log.jsonl) | 2026-07-04T01:23:13.100740 | 2026-07-04T01:59:20.832729 | 59 | 2026-07-04 |
| [v2_extreme12/20260704_topup10_opus_hard2/log.jsonl](../v2_extreme12/20260704_topup10_opus_hard2/log.jsonl) | 2026-07-04T02:02:22.148675 | 2026-07-04T11:39:56.150632 | 29 | 2026-07-04 |
| [v2_extreme12/20260704_topup10_sonnet5_hard2/log.jsonl](../v2_extreme12/20260704_topup10_sonnet5_hard2/log.jsonl) | 2026-07-04T12:12:57.197749 | 2026-07-04T17:46:27.779133 | 68 | 2026-07-04 |
| [h3_probe/20260702_claude_opus_hard3ext/log.jsonl](../h3_probe/20260702_claude_opus_hard3ext/log.jsonl) | 2026-07-02T13:52:35.143421 | 2026-07-02T15:39:26.624029 | 35 | 2026-07-02 |
| [h3_probe/20260703_claude_fable5_low_hard3ext/log.jsonl](../h3_probe/20260703_claude_fable5_low_hard3ext/log.jsonl) | 2026-07-03T16:31:13.328575 | 2026-07-03T16:45:52.042838 | 33 | 2026-07-03 |
| [rabin_karp/20260627_claude_opus_rk_hashgate/log.jsonl](../rabin_karp/20260627_claude_opus_rk_hashgate/log.jsonl) | 2026-06-27T10:34:45.216231 | 2026-06-27T10:51:52.854190 | 8 | 2026-06-27 |
| [rabin_karp/20260629_claude_opus_rk_repro/log.jsonl](../rabin_karp/20260629_claude_opus_rk_repro/log.jsonl) | 2026-06-29T15:33:25.131771 | 2026-06-29T20:51:09.666022 | 65 | 2026-06-29 |
| [rabin_karp/20260629_claude_sonnet_rk_repro/log.jsonl](../rabin_karp/20260629_claude_sonnet_rk_repro/log.jsonl) | 2026-06-30T00:11:48.063611 | 2026-06-30T06:41:49.836187 | 14 | 2026-06-30 |
| [rabin_karp/20260703_claude_fable5_rk/log.jsonl](../rabin_karp/20260703_claude_fable5_rk/log.jsonl) | 2026-07-03T16:41:28.001212 | 2026-07-04T13:51:30.789919 | 31 | 2026-07-03, 2026-07-04 |
| [canary_opus47/experiment_log.jsonl](../canary_opus47/experiment_log.jsonl) | 2026-05-23T11:34:07.626666 | 2026-05-23T21:48:00.272658 | 155 | 2026-05-23 |

## 再確認方法

リポジトリのルートで以下を実行する。一次データは変更しない。

```python
from datetime import datetime
from pathlib import Path
import json

groups = ("v1_260308", "v2_basic19", "v2_hard12", "v2_extreme12",
          "h3_probe", "rabin_karp", "canary_opus47")
for group in groups:
    for path in sorted(Path(group).rglob("*log.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        times = [datetime.fromisoformat(row["timestamp"]) for row in rows]
        print(path, min(times), max(times), len(times),
              sorted({time.date().isoformat() for time in times}))
```
