# CLAUDE.md — py2to3-agent

このリポジトリは「Python 2 のコードを等価な Python 3 へ移植する」エージェントと、その採点係（決定的 golden）です。
Python 2 を動かさずに、保存した期待出力（golden）と Python 3 の実行結果が一致するかで判定します。

## 確認のしかた

- `python eval/oracle.py --selftest` … 採点係が正しいか（正しい移植=PASS／壊した移植=FAIL）
- `python eval/oracle.py --candidate candidate` … 各ケースの candidate.py を採点
- `python eval/oracle.py` … お手本(reference.py)を採点

## いじるときの約束（評価駆動 / EDD）

- 先に eval（合否の基準）を満たすことを確認してから「完成」とする。雰囲気で done にしない。
- `eval/corpus/<ケース>/` の `reference.py`・`golden.txt` は採点の基準。むやみに変えない。
- Python 3 が必要。秘密情報・個人情報・客先コードを入れない。

## ファイルの役割

- `.claude/agents/py2to3-agent.md` … エージェント定義
- `eval/oracle.py` … 採点係（決定的 golden）／`design/design.md` … 設計／`README.md` … 説明
