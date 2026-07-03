@echo off
chcp 65001 >nul
echo ========================================
echo    ???????GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] ??Git??...
git status --short images/

echo.
echo [2/4] ??images???Git...
git add images/

echo.
echo [3/4] ????...
git commit -m "??????"

echo.
echo [4/4] ???GitHub...
git push origin main

echo.
echo ========================================
echo    ?????
echo    ??1-2?????dashboard??
echo ========================================
echo.
pause
