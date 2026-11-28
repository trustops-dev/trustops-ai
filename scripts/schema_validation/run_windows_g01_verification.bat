@echo off
setlocal
cd /d "%~dp0"
echo ========================================================================
echo TrustOps AI v1.18.0 - Native Windows Offline Verification (Double-Click)
echo ========================================================================
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 run_native_verification.py
) else (
    python run_native_verification.py
)
echo.
echo Finished! Report saved to native_host_verification_report.json
pause