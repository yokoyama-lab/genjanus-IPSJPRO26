import re
import sys
from collections import defaultdict, Counter, deque
from pathlib import Path

def normalize_lines(s: str):
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in s.split("\n")]
    # 末尾の空行は削る
    while lines and lines[-1] == "":
        lines.pop()
    return lines

def analyze_jana_log(log_path: str, answer_path: str = "p04cycle3_answer.txt"):
    """
    jana_check_results.log を解析し、
    成功・構文エラー・実行エラーに分類。
    さらに「成功」の中を、ログ中の連続する複数行 stripped を束ねて
    p04cycle3_answer.txt（正規化後の行列）と一致したかで
    正しい出力／誤った出力 に分類する。
    """

    answer_file = Path(answer_path)
    if not answer_file.exists():
        print(f"⚠️ 期待出力ファイルが見つからない: {answer_path}")
        sys.exit(1)

    answer_lines = normalize_lines(answer_file.read_text(encoding="utf-8"))
    if not answer_lines:
        print("⚠️ 期待出力が空である。判定不能になる。")
        sys.exit(1)

    current_file = None
    results = {}  # {filename: status}
    saw_correct_output = defaultdict(bool)  # {filename: True/False}

    # 判定パターン
    file_pattern = re.compile(r"^=== 検証: (.+\.janus) ===")
    runtime_err_pattern = re.compile(r"^\[ERROR \(line")
    syntax_err_pattern = re.compile(r"^File \"")

    # 連続行比較用のウィンドウ
    win = deque(maxlen=len(answer_lines))

    def reset_window():
        win.clear()

    with open(log_path, encoding="utf-8") as f:
        for raw in f:
            stripped = raw.rstrip()

            # 新しいファイル開始
            m = file_pattern.match(stripped)
            if m:
                current_file = m.group(1)
                results[current_file] = "成功"  # デフォルト成功
                reset_window()
                continue

            if current_file is None:
                continue

            # 構文エラー検出
            if syntax_err_pattern.match(stripped):
                results[current_file] = "構文エラー"
                reset_window()
                continue

            # 実行エラー検出
            if runtime_err_pattern.match(stripped):
                results[current_file] = "実行エラー"
                reset_window()
                continue

            # 成功扱いの間だけ出力判定に使う
            if results.get(current_file) != "成功":
                continue

            # ★ 連続する複数行を束ねて比較（スライディング）
            win.append(stripped)

            if len(win) == len(answer_lines):
                if list(win) == answer_lines:
                    saw_correct_output[current_file] = True
                    # 一度見つけたら、このファイルではもう探さなくてよいなら以下を有効化してもよい
                    # reset_window()

    # 結果分類
    categories = defaultdict(list)
    for fname, status in results.items():
        categories[status].append(fname)

    counter = Counter(results.values())
    total = sum(counter.values())

    # 成功の中をさらに分類
    success_files = sorted(categories.get("成功", []))
    success_correct = [f for f in success_files if saw_correct_output.get(f, False)]
    success_wrong = [f for f in success_files if not saw_correct_output.get(f, False)]

    # === 表示 ===
    print("=== Janus 構文検証 詳細結果 ===\n")
    print(f"総ファイル数: {total}")
    print(f"  ✅ 成功: {counter.get('成功', 0)}")
    print(f"  ⚠️ 構文エラー: {counter.get('構文エラー', 0)}")
    print(f"  ❌ 実行エラー: {counter.get('実行エラー', 0)}\n")

    def print_section(title, files, icon):
        print(f"{icon} {title} ({len(files)}件)")
        print("-" * 60)
        if not files:
            print("(なし)\n")
            return
        for f in files:
            print(f"  {f}")
        print()

    print_section("成功したファイル（正しい出力）", success_correct, "✅")
    print_section("成功したファイル（誤った出力）", success_wrong, "❌")
    print_section("構文エラーのあったファイル", sorted(categories.get("構文エラー", [])), "⚠️")
    print_section("実行エラーのあったファイル", sorted(categories.get("実行エラー", [])), "❌")

    # === CSV出力 ===
    csv_path = log_path.replace(".log", "_summary.csv")
    with open(csv_path, "w", encoding="utf-8") as out:
        out.write("ファイル名,結果,出力判定\n")
        for fname, status in sorted(results.items()):
            out_j = ""
            if status == "成功":
                out_j = "正しい出力" if saw_correct_output.get(fname, False) else "誤った出力"
            out.write(f"{fname},{status},{out_j}\n")

    print(f"📄 CSV出力: {csv_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python analyze_jana_results_detailed.py jana_check_results.log [p04cycle3_answer.txt]")
        sys.exit(1)

    log_path = sys.argv[1]
    answer_path = sys.argv[2] if len(sys.argv) >= 3 else "p04cycle3_answer.txt"
    analyze_jana_log(log_path, answer_path)
