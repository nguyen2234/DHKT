@echo off
chcp 65001 >nul
echo ========================================================
echo   BAT DAU BUILD UNG DUNG: CONG CU TAO BAO CAO WO
echo ========================================================
cd /d "%~dp0\.."

echo [1/3] Kiem tra moi truong Python va thu vien...
python -m pip install -r requirements.txt

echo [2/3] Dang dong goi bang PyInstaller...
pyinstaller --clean -y "build_scripts\wo_report_tool.spec"

if %ERRORLEVEL% NEQ 0 (
    echo [LOI] Dong goi PyInstaller that bai!
    pause
    exit /b %ERRORLEVEL%
)

echo [3/3] Kiem tra Inno Setup Compiler de tao file Setup.exe...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if exist %ISCC% (
    echo Dang tao bo cai dat WOReportTool_Setup.exe...
    %ISCC% "build_scripts\setup_installer.iss"
    echo [HOAN TAT] Da tao xong file setup tai: dist\WOReportTool_Setup.exe
) else (
    echo [THONG BAO] Khong tim thay Inno Setup trong may.
    echo Thu muc ung dung standalone da duoc tao thanh cong tai:
    echo   dist\WOReportTool\WOReportTool.exe
    echo Nguoi dung co the su dung truc tiep ma khong can cai dat gi!
)

echo ========================================================
echo   BUILD HOAN TAT THANH CONG!
echo ========================================================
pause
