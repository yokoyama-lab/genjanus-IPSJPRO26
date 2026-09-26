# モデルの呼び出し名と日付固定の有無（2026-09-26確認）

対象データのコミット：`5857ddf19b20bd72647619cc327e3531445c6156`。

同一のモデル名（エンドポイント）でも、提供側の更新により時期によって出力の性質が変わりうる。
再現性の観点からは日付固定のスナップショット（例：`gpt-4.1-2025-04-14`）を指定することが望ましい。
この文書は、各実験でモデルを**どの名前で呼び出したか**を収録ログから読み取り、
日付を含む名前（スナップショット）だったかを示す。

## 結論

- **V1・V2・予備調査・Rabin–Karp・カナリア実験の呼び出し名は、いずれも日付を含まない。**
  各 CLI（claude-cli・codex-cli・gemini-cli）と Gemini API に、下表の名前をそのまま渡した。
  Claude の `opus`・`haiku`・`sonnet` は CLI のエイリアスである。
- **どの版に解決されたかは、ログに記録されていない。** ただし Rabin–Karp の Sonnet run は、
  デバッグログで `claude-sonnet-4-6` に解決されたことを確認している（README §6）。
- **V0 当初分**も日付を含まない名前（`gpt-5.2`・`gpt-4.1`・`gpt-5-nano`）で OpenAI API を呼んだ
  （元ハーネスの生成スクリプトによる。この公開アーティファクトには V0 の呼び出し名の記録がない）。
- **V0 補充分（2026-07）** について、論文は日付固定のスナップショット
  （`gpt-4.1-2025-04-14`・`gpt-5-nano-2025-08-07`）を用いたと記している。
  この公開アーティファクトと元ハーネスには、その呼び出し名を示す記録が見つからなかった（未確認）。

## 実験別の呼び出し名

「呼び出し名」は `log.jsonl`（V1・カナリアは `experiment_log.jsonl`）の `model` 欄、
「経路」は `backend` 欄である。ハーネスはこの値を CLI の `--model`／`-m`、または API の `model` 引数に
そのまま渡す。期間は当該組合せのログ記録日の最初と最後で、補充・再実行を含む。

### V2（Basic19・Hard12・Extreme12）

| 論文の表記 | 経路 | 呼び出し名 | 日付固定 | ログ記録日 |
|---|---|---|---|---|
| Opus 4.8/high | claude-cli | `opus`（エイリアス） | なし | 2026-06-12〜07-04 |
| Haiku 4.5 | claude-cli | `haiku`（エイリアス） | なし | 2026-06-09〜07-05 |
| Sonnet 5/high | claude-cli | `claude-sonnet-5` | なし | 2026-07-02〜07-04 |
| Fable 5/low | claude-cli | `claude-fable-5` | なし | 2026-07-03〜07-04 |
| GPT-5.4/low | codex-cli | `gpt-5.4` | なし | 2026-06-10〜07-04 |
| GPT-5.4-mini/low | codex-cli | `gpt-5.4-mini` | なし | 2026-06-09〜07-04 |
| GPT-5.5/low | codex-cli | `gpt-5.5` | なし | 2026-06-10〜07-03 |
| Gemini-2.5-flash | gemini-cli, api | `gemini-2.5-flash` | なし | 2026-06-13〜07-04 |
| Gemini-3.1-flash-lite | gemini-cli, api | `gemini-3.1-flash-lite` | なし | 2026-06-10〜07-03 |
| Gemini-3-flash-preview | gemini-cli, api | `gemini-3-flash-preview` | なし | 2026-06-09〜07-05 |
| Gemini-3.5-flash | api | `gemini-3.5-flash` | なし | 2026-06-24〜07-04 |

Gemini の api 経路のログには `model_id` 欄もあるが、値は呼び出し名と同じである。

### V1・予備調査・Rabin–Karp・カナリア実験

| 実験 | 論文の表記 | 経路 | 呼び出し名 | 日付固定 | ログ記録日 |
|---|---|---|---|---|---|
| V1 | Opus 4.7 | Claude Code（論文 3.2 節） | `opus-4.7`（ログ上のラベル。元ハーネスのスクリプトに `--model claude-opus-4-7` の指定あり） | なし | 2026-05-22〜05-24 |
| カナリア | Opus 4.7 | （ログに記録なし） | `opus-4.7-canary`（ログ上のラベル） | なし | 2026-05-23 |
| h3 予備調査 | Opus 4.8 | claude-cli | `opus`（エイリアス） | なし | 2026-07-02 |
| h3 予備調査 | Fable 5 | claude-cli | `claude-fable-5` | なし | 2026-07-03 |
| Rabin–Karp | Opus 4.8 | claude-cli | `opus`（エイリアス） | なし | 2026-06-27〜06-29 |
| Rabin–Karp | Sonnet 4.6 | claude-cli | `sonnet`（エイリアス。`claude-sonnet-4-6` に解決） | なし | 2026-06-30 |
| Rabin–Karp | Fable 5 | claude-cli | `claude-fable-5` | なし | 2026-07-03〜07-04 |

### V0

| 区分 | 呼び出し名 | 日付固定 | 根拠 |
|---|---|---|---|
| 当初分（2025-12） | `gpt-5.2`・`gpt-4.1`・`gpt-5-nano` | なし | 元ハーネス `251226/gen_janus*.py` の `model=` 指定 |
| 補充分（2026-07） | 論文の記載は `gpt-4.1-2025-04-14`・`gpt-5-nano-2025-08-07` | あり（論文の記載） | 収録データに呼び出し名の記録なし（未確認） |

## 確認方法

```python
import json, glob, collections
c = collections.Counter()
for f in glob.glob('**/*log.jsonl', recursive=True):
    for line in open(f):
        d = json.loads(line)
        c[(f.split('/')[0], d.get('backend'), d.get('model'), d.get('model_id'))] += 1
for k, v in sorted(c.items(), key=str):
    print(k, v)
```

日付を含む呼び出し名（`-20YYMMDD` や `-20YY-MM-DD` の形）は、収録ログに1件もない。
