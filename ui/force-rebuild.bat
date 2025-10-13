@echo off
echo ========================================
echo FORCE REBUILD - Developer Assistant UI
echo ========================================
echo.

echo Step 1: Stopping any running processes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Clearing Vite cache...
if exist node_modules\.vite (
    rmdir /s /q node_modules\.vite
    echo Vite cache cleared!
) else (
    echo No Vite cache found.
)

echo Step 3: Clearing dist folder...
if exist dist (
    rmdir /s /q dist
    echo Dist folder cleared!
) else (
    echo No dist folder found.
)

echo.
echo ========================================
echo Cache cleared successfully!
echo ========================================
echo.
echo Now starting development server...
echo.

npm run dev

pause
