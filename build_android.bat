@echo off
echo ========================================
echo FADAKKA INDEX - Android Build Script
echo ========================================
echo.
echo Make sure you have:
echo 1. Linux or WSL (Windows Subsystem for Linux)
echo 2. Buildozer installed (pip install buildozer)
echo 3. Java JDK 17+ installed
echo.
echo Starting build...
echo.

buildozer android debug

echo.
echo If build successful, find APK in: bin/
echo Install on your phone and enjoy!
pause