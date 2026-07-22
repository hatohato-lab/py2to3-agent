#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oracle.py — Python 2 → Python 3 移植エージェントの決定的オラクル（外部オラクル＝合否判定）。

EDD（評価駆動開発）の中核。候補となる移植コードが、各 corpus ケースについて
  (a) python3 -m py_compile で構文が通り、かつ
  (b) python3 で実行すると golden（期待 stdout）を再現する
ときだけ PASS とする。LLM 審査なし・乱数なし・完全に決定的。
比較は前後の空白・改行を除いた完全一致（strip 後の一致）。
コンパイル・実行とも 10 秒のタイムアウト付き（無限ループする候補は FAIL になる）。
Python 2 ランタイムは不要（期待出力を golden.txt に保存して比較する）。

使い方:
  python oracle.py                  # 各ケースの reference.py（正例＝陽性対照）を採点
  python oracle.py --candidate NAME # 各ケースの NAME.py（エージェントの出力）を採点
  python oracle.py --selftest       # オラクル自身を検証（正しい移植→PASS / 壊れた移植→FAIL）

終了コード: 全ケース PASS（または selftest が期待どおり）で 0、それ以外 1。
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows コンソール(cp932)でも日本語・記号を出せるよう出力を UTF-8 に統一。
# Linux/Mac は元から UTF-8 なので無害。これが無いと Windows で print が落ちる。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

# ── 言語ごとの設定（repo 間の差分はここだけ＝「共通の型」） ──
LANG = "Python 2 → Python 3"
EXT = ".py"
CORPUS = Path(__file__).resolve().parent / "corpus"
TIMEOUT_SEC = 10  # コンパイル・実行それぞれの上限秒。無限ループ候補で固まらないため
# selftest 用の汎用ミューテーション（ファイル非依存で壊す）
OUTPUT_BREAK = '\nprint("__ORACLE_SELFTEST_EXTRA__")\n'
COMPILE_BREAK = '\ndef __oracle_selftest_broken__(:\n'


def compile_and_run(src: Path, workdir: Path):
    """(ok, stdout, detail) を返す。ok=False はコンパイルか実行の失敗。"""
    cfile = str(workdir / "out.pyc")  # __pycache__ を corpus に作らないよう一時へ
    try:
        cp = subprocess.run(
            [sys.executable, "-c",
             "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)",
             str(src), cfile],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return (False, "", f"timeout: py_compile が {TIMEOUT_SEC} 秒以内に終わらない")
    if cp.returncode != 0:
        msg = (cp.stdout + cp.stderr).strip().replace("\n", " ")
        return (False, "", "py_compile: " + msg[:160])
    try:
        rp = subprocess.run([sys.executable, str(src)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        return (False, "", f"timeout: 実行が {TIMEOUT_SEC} 秒以内に終わらない（無限ループの疑い）")
    if rp.returncode != 0:
        return (False, "", "実行時エラー: " + rp.stderr.strip().replace("\n", " ")[:160])
    return (True, rp.stdout, "ok")


def grade(src: Path, golden: str):
    if not src.exists():
        return ("FAIL", f"{src.name} が無い")
    with tempfile.TemporaryDirectory() as td:
        ok, out, detail = compile_and_run(src, Path(td))
    if not ok:
        return ("FAIL", detail)
    if out.strip() == golden.strip():
        return ("PASS", "ok")
    return ("FAIL", f"出力不一致: got={out.strip()!r} want={golden.strip()!r}"[:160])


def cases():
    """corpus のケース一覧。0 件なら空合格（0/0 PASS）を防ぐため明示エラーで異常終了する。"""
    found = sorted(p for p in CORPUS.iterdir() if p.is_dir()) if CORPUS.is_dir() else []
    if not found:
        print(f"エラー: corpus にケースが 1 件もありません（{CORPUS}）。"
              "0 件のまま PASS とはしないため、exit 1 で終了します。", file=sys.stderr)
        sys.exit(1)
    return found


def grade_all(candidate: str):
    rows, allpass = [], True
    for c in cases():
        golden = (c / "golden.txt").read_text(encoding="utf-8")
        verdict, detail = grade(c / f"{candidate}{EXT}", golden)
        rows.append((c.name, verdict, detail))
        allpass = allpass and verdict == "PASS"
    return rows, allpass


def print_table(rows, title):
    print(f"\n### {title}")
    print("| ケース | 判定 | 詳細 |")
    print("|---|---|---|")
    for name, verdict, detail in rows:
        print(f"| {name} | {verdict} | {detail} |")
    npass = sum(1 for _, v, _ in rows if v == "PASS")
    print(f"\n小計: {npass}/{len(rows)} PASS")
    return npass == len(rows)


def selftest():
    print(f"# オラクル自己検証 — {LANG}")
    rows, good_ok = grade_all("reference")
    print_table(rows, "① 正しい移植 reference（PASS であるべき）")
    # 破壊試験は全ケースに適用（先頭だけでは弁別力の証明にならない）
    brk_rows, breaks_ok = [], True
    for c in cases():
        ref = (c / f"reference{EXT}").read_text(encoding="utf-8")
        golden = (c / "golden.txt").read_text(encoding="utf-8")
        for label, mut in [("出力破壊", OUTPUT_BREAK), ("構文破壊", COMPILE_BREAK)]:
            with tempfile.TemporaryDirectory() as td:
                p = Path(td) / f"broken{EXT}"
                p.write_text(ref + mut, encoding="utf-8")
                verdict, _ = grade(p, golden)
            ok = verdict == "FAIL"
            breaks_ok = breaks_ok and ok
            brk_rows.append((f"{label}({c.name})", verdict, "期待=FAIL " + ("OK" if ok else "NG オラクル不良")))
    print_table(brk_rows, "② 壊れた移植（FAIL であるべき）")
    valid = good_ok and breaks_ok
    print(f"\n## オラクル判定: {'PASS（信頼できる外部オラクル）' if valid else 'FAIL（オラクル自体に欠陥）'}")
    return valid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="reference",
                    help="採点する候補ファイル名（拡張子なし）。既定=reference")
    ap.add_argument("--selftest", action="store_true", help="オラクル自身を検証")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    rows, allpass = grade_all(a.candidate)
    ok = print_table(rows, f"採点: {a.candidate}{EXT}（{LANG}）")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
