@echo off
chcp 65001
REM Get the current branch name
FOR /F "delims=" %%b IN ('git rev-parse --abbrev-ref HEAD') DO set "feature_branch=%%b"

REM Output commit list to pr_summary.txt
echo == Commit List == > pr_summary.txt
git log --oneline main..%feature_branch% >> pr_summary.txt

REM Output changed files list
echo. >> pr_summary.txt
echo == Changed Files == >> pr_summary.txt
git diff --name-only main..%feature_branch% >> pr_summary.txt

REM Optional: show a message
echo pr_summary.txt has been created for branch %feature_branch%
