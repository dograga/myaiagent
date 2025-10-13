@echo off
echo Clearing Vite cache and rebuilding...
echo.

REM Clear Vite cache
if exist node_modules\.vite (
    echo Removing node_modules\.vite...
    rmdir /s /q node_modules\.vite
)

REM Clear dist folder if exists
if exist dist (
    echo Removing dist folder...
    rmdir /s /q dist
)

echo.
echo Cache cleared!
echo.
echo Now run: npm run dev
echo Then open browser and press Ctrl+Shift+R to hard refresh
pause
