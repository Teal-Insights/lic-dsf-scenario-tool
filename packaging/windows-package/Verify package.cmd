@echo off
setlocal DisableDelayedExpansion
set "ERRORLEVEL="
if not exist "%~dp0runtime\python.exe" goto no_runtime
cd /d "%~dp0"
"%~dp0runtime\python.exe" -X utf8 -B "%~dp0start_local.py" --verify-only
set "status=%ERRORLEVEL%"
if not "%status%"=="0" echo This check finished with status %status%.
pause
goto finished

:no_runtime
echo.
echo The program files are missing from this folder.
echo.
echo Verify package.cmd could not find runtime\python.exe beside it, so the
echo application cannot start. Two things usually cause this:
echo.
echo   - The launcher was opened from inside the ZIP. Windows shows the
echo     inside of a ZIP as though it were an ordinary folder, but nothing
echo     in this package runs from that view.
echo   - The ZIP was only partly extracted, or files were moved or deleted
echo     after it was extracted.
echo.
echo Extracting a fresh, complete copy fixes both:
echo.
echo   1. Close this window.
echo   2. Find the ZIP file you downloaded, usually in your Downloads folder.
echo   3. Right-click the ZIP file and choose Extract All.
echo   4. Choose Extract and wait for Windows to finish.
echo   5. Open the folder that Windows created.
echo   6. Double-click Verify package.cmd inside that folder.
echo.
echo Keep every extracted file together in one folder.
echo.
pause
exit /b 1

:finished
endlocal
