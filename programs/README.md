# Hard12 / Extreme12 の Janus プログラム

論文の Hard12・Extreme12 の 24 課題について，参照用の Janus プログラム，課題仕様，
テストケース，実験で使ったプロンプト（L4_full）をまとめたものです（2026-11-08 追加）。

## 構成

```
programs/
  tasks.json                 24 課題の仕様（手続き名・引数・説明・テストケース・解答の出所）
  verify.py                  全テストを jana / pyjanus で実行して判定するスクリプト
  hard12/<task>.jan          Hard12 の参照プログラム（12 本）
  extreme12/<task>.jan       Extreme12 の参照プログラム（12 本）
  */tests/<task>/caseK.jan   参照プログラム＋main の実行可能なテストプログラム
  */prompts_L4_full/<task>.txt  実験で LLM に与えたプロンプト（L4_full 条件）
  extreme12/thomsen/         Thomsen の jana で動くように書き換えた版（3 本）とそのテスト
```

`tests/<task>/case0.jan` がプロンプトに載せた例で，case1 以降は LLM に見せていない
テストケースです。

## ⚠ h2_heapify は模範解答ではない

**h2_heapify には手書きの模範解答がありません。** `extreme12/h2_heapify.jan` は
**モデルが生成し，検証器に通ったプログラム**です（Claude Opus，run
`20260613_claude_opus_hard2`，trial 11，round 0。初回生成で 4 ケースすべてに成功し，
後始末も完全）。ほかの 23 本は手書きの参照プログラムです。`tasks.json` の
`reference` 欄にも同じことを書いてあります。

## 検証結果（2026-11-08 実行）

```
python3 programs/verify.py --interp pyjanus             # 前向き実行
python3 programs/verify.py --interp jana                # Thomsen の jana
python3 programs/verify.py --interp jana --thomsen      # thomsen/ 版を使う
python3 programs/verify.py --interp pyjanus --roundtrip # call → uncall で入力に戻るか
```

| 検査 | pyjanus | Thomsen の jana |
|---|---|---|
| 前向き実行（そのまま） | 24/24 | 19/24 |
| 前向き実行（`--thomsen`） | 24/24 | 22/24 |
| 往復（`--roundtrip`，`--thomsen`） | 22/24 | 17/24 |

実験の検証器は pyjanus（`--std jana2014_in_out`）です。テストケースは課題ごとに 4〜5 個
しかないので，ここで「通った」と言えるのはそのケースについてだけです。

### Thomsen の jana との方言差

次の 3 本は pyjanus の拡張を使っているので，Thomsen の jana ではそのまま動きません。
`extreme12/thomsen/` に，意味を変えずに書き換えた版を置きました（jana・pyjanus の
両方でテストに通ることを確認済み）。

| 課題 | pyjanus の拡張 | 書き換え |
|---|---|---|
| h2_bitrev | `uncall` される手続きの中の `*=`・`/=` | `local t … += t … delocal` で書き直した |
| h2_zeckendorf | 比較式を整数として足す（`d += (a <= n)`） | `if … fi` に直した |
| h2_heapify | `==` と，真偽値を整数として使う `delocal` | `=` と `if … fi` に直した |

Thomsen の jana は `*=`・`/=` を逆向きに実行できません。そのため，それらを含む
プログラム（h_base3，h_bingcd，h_gray_decode，h2_heapify の一部ケース，h2_hilbert）は，
前向き実行は通りますが `--roundtrip`（`uncall`）は jana では失敗します。pyjanus では通ります。

### ⚠ h2_bwt と h2_perm_inverse の参照プログラムは可逆ではない

この 2 本は `delocal int lo = lo`（h2_bwt 102 行目），`delocal int first = first`・
`delocal int m = m`（h2_perm_inverse 22・41 行目）のように，局所変数を**自分自身と比べて
捨てて**います。この比較は常に真なので，前向き実行では値が黙って捨てられます。
逆向きにはその値を復元できません。

- pyjanus は前向き実行を通しますが，`uncall` は失敗します（`Variable 'lo' has not been declared`）。
- Thomsen の jana は前向き実行の時点でエラーにします（`Identifiers 'lo' and 'lo' are aliases`）。

つまりこの 2 本は，入出力のテストケースには合いますが，**Janus の可逆プログラムとしては
成り立っていません**。課題そのもの（BWT と置換の逆）は全単射なので，正しい可逆
プログラムは存在するはずですが，ここには含まれていません。穴埋めなどの教材に使う場合は
この 2 課題を除くか，注意して扱ってください。
