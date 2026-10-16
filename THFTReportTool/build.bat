@echo off
setlocal
echo ========================================================
echo   BUILD CONG CU TAO BAO CAO THFT (THFTReportTool)
echo ========================================================

cd /d "%~dp0"

echo [1/3] Don dep thu muc build cu...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist dist_installer rmdir /s /q dist_installer

echo [2/3] Dong goi ung dung voi PyInstaller...
pyinstaller --clean --noconfirm THFTReportTool.spec

if not exist "dist\THFTReportTool\THFTReportTool.exe" (
    echo [LOI] Dong goi PyInstaller that bai!
    pause
    exit /b 1
)

echo [OK] Da tao thanh cong: dist\THFTReportTool\THFTReportTool.exe

echo [3/3] Bien dich bo cai dat Inno Setup...
set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if exist "%ISCC_PATH%" (
    "%ISCC_PATH%" "installer\THFTReportTool.iss"
    if exist "dist_installer\THFTReportTool_Setup.exe" (
        echo [OK] Da tao thanh cong: dist_installer\THFTReportTool_Setup.exe
        copy /y "dist_installer\THFTReportTool_Setup.exe" "..\THFTReportTool_Setup.exe" >nul
        echo [OK] Da cap nhat ra thu muc goc: ..\THFTReportTool_Setup.exe
    ) else (
        echo [CANH BAO] Khong tim thay file Setup sau khi bien dich!
    )
) else (
    echo [CANH BAO] Khong tim thay ISCC.exe cua Inno Setup.
)

echo [4/4] Tao file nen Portable ZIP tai thu muc goc...
python -c "import shutil, zipfile, os; zip_p = r'..\THFTReportTool_Portable.zip'; os.path.exists(zip_p) and os.remove(zip_p); zf = zipfile.ZipFile(zip_p, 'w', zipfile.ZIP_DEFLATED); [zf.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), r'dist')) for r, d, fs in os.walk(r'dist\THFTReportTool') for f in fs]; zf.close()"
if exist "..\THFTReportTool_Portable.zip" (
    echo [OK] Da tao thanh cong: ..\THFTReportTool_Portable.zip
)

echo ========================================================
echo   HOAN THANH QUA TRINH BUILD!
echo ========================================================
endlocal
