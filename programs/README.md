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

実験の検証器は pyjanus（`--std jana2014_in_out`）です。上の表はテストケース（課題ごとに 4〜5 個）
についての結果です。

### 全域・乱択での検査（2026-11-09 実行）

テストケースだけでは模範解答として足りるか分からないので，実験ハーネスの Python 参照実装
（課題ごとの単射な状態写像。非公開の実験リポジトリ `gen_janus` の `tools/hard_reference.py`）を
正解として，pyjanus で次の 2 つを行いました。どちらも，前向き（期待値と一致し，期待外の非ゼロ変数が
残らない）と往復（`call` の後に `uncall` して全変数が入力に戻る）の両方を見ています。

1. **定義域の全列挙**：課題ごとに決めてある有界な入力をすべて試す（39〜6651 入力／課題）。
2. **範囲を広げた乱択**：定義域より大きな入力を課題ごとに 150 個（乱数の種は課題名から固定）。
   配列は長さ 12 まで，数値は 10⁶ まで，h2_hilbert は k=6，h2_mtf は記号 6 種・長さ 8 まで。
   前提を満たすかは参照実装の assert で判定し，満たさない入力は捨てた。
   h_cantor_pair は 1 歩ずつ数える作りで，x・y を大きくすると時間制限（20 秒）に当たるため，x・y ≤ 200 とした。

| 検査 | 前向き | 往復 |
|---|---|---|
| 定義域の全列挙 | 24/24 課題で全件一致 | 22/24（h2_bwt 0/120，h2_perm_inverse 0/153） |
| 範囲を広げた乱択（150 入力） | 24/24 課題で全件一致 | 22/24（h2_bwt 0/150，h2_perm_inverse 0/150） |

- 期待値と違う出力も，期待外の非ゼロ変数の残りも，1 件もありませんでした。
- 参照実装から計算し直した期待値は，`tasks.json` の 24 課題すべてと一致しました。
- h2_heapify の全列挙では n=1 の 3 入力を実行できていません。`steps` が長さ 0 の配列になり，
  Janus では宣言できないためです（プログラムの誤りではない）。

**模範解答としての扱い**

| 判断 | 課題 |
|---|---|
| 模範解答として使える | Hard12 の 12 本，Extreme12 の h2_bitrev・h2_cf_expand・h2_hilbert・h2_kmp_failure・h2_lehmer_rank・h2_modinv・h2_mtf・h2_oesort・h2_zeckendorf |
| 検査はすべて通るが，手書きでない | h2_heapify（モデル生成） |
| 模範解答に使えない | h2_bwt・h2_perm_inverse（可逆でない。下記） |

h2_bwt はさらに，値を `base = 1000003` で 1 つの整数に詰め込む書き方をしているため，
入力の値の大きさに上限があります。

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
