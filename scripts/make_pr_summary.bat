@echo off
chcp 65001

REM 現在のブランチ名を取得
FOR /F "delims=" %%b IN ('git rev-parse --abbrev-ref HEAD') DO set "feature_branch=%%b"

REM --- 出力開始 -----------------------------------------------------------
echo == Commit List == > pr_summary.txt
git log --oneline main..%feature_branch% >> pr_summary.txt

echo. >> pr_summary.txt
echo == Changed Files == >> pr_summary.txt
git diff --name-only main..%feature_branch% >> pr_summary.txt

REM 追加：行数ベースのサマリ
echo. >> pr_summary.txt
echo == Diff Summary (added / removed lines) == >> pr_summary.txt
git diff --stat --no-color main..%feature_branch% >> pr_summary.txt

REM 追加：実際の+/-行を含む詳細パッチ
echo. >> pr_summary.txt
echo == Detailed Diff == >> pr_summary.txt
git diff --no-color main..%feature_branch% >> pr_summary.txt
REM  ↑行数が多くなる場合は --unified=0 で前後コンテキストを省略可能

echo pr_summary.txt has been created for branch %feature_branch%
