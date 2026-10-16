@echo off
chcp 65001 >nul
echo ============================================================
echo   WO OPERATIONS CENTER — ONE-CLICK PRODUCTION BUILD SCRIPT
echo ============================================================
echo.

set PROJECT_DIR=%~dp0..
cd /d "%PROJECT_DIR%"

echo [1/3] Biên dịch React Frontend (Vite + Tailwind v4)...
cd frontend
where.exe bun >nul 2>nul && (call bun run build) || (call npm run build)
if %errorlevel% neq 0 (
    echo [LỖI] Không thể build React frontend. Vui lòng kiểm tra lại lỗi trên.
    pause
    exit /b %errorlevel%
)
cd /d "%PROJECT_DIR%"
echo [OK] Đã hoàn thành build frontend vào frontend\dist.
echo.

echo [2/3] Đóng gói ứng dụng desktop bằng PyInstaller...
pyinstaller --clean -y packaging\WOOperationsCenter.spec
if %errorlevel% neq 0 (
    echo [LỖI] Quá trình PyInstaller gặp sự cố.
    pause
    exit /b %errorlevel%
)
echo [OK] Đã tạo thư mục thực thi tại dist\WOOperationsCenter\WOOperationsCenter.exe.
echo.

echo [3/3] Tạo bộ cài đặt Inno Setup Installer...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if exist %ISCC% (
    echo Tìm thấy Inno Setup tại: %ISCC%
    %ISCC% packaging\setup_installer.iss
    echo [OK] Đã tạo bộ cài đặt tại: dist_installer\WOOperationsCenter_Setup.exe
) else (
    echo [THÔNG BÁO] Không tìm thấy Inno Setup 6 trên máy.
    echo Bạn có thể chạy trực tiếp ứng dụng tại:
    echo   dist\WOOperationsCenter\WOOperationsCenter.exe
)

echo.
echo ============================================================
echo   HOÀN TẤT ĐÓNG GÓI ỨNG DỤNG WO OPERATIONS CENTER!
echo ============================================================
pause
