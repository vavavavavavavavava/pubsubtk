@echo off
chcp 65001
REM Get the current branch name
FOR /F "delims=" %%b IN ('git rev-parse --abbrev-ref HEAD') DO set "feature_branch=%%b"

REM Output commit list to summary.txt
echo == Commit List == > summary.txt
git log --oneline main..%feature_branch% >> summary.txt

REM Output changed files list
echo. >> summary.txt
echo == Changed Files == >> summary.txt
git diff --name-only main..%feature_branch% >> summary.txt

REM Optional: show a message
echo summary.txt has been created for branch %feature_branch%
