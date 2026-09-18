@echo off
title Compilation ADIF vers Cabrillo - F4GOP
echo ============================================
echo   Compilation ADIF -> Cabrillo (F4GOP)
echo ============================================
echo.

REM Verifier que Python est bien installe
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe ou pas dans le PATH.
    echo Installe Python depuis https://www.python.org/downloads/
    echo et coche bien "Add Python to PATH" pendant l'installation.
    pause
    exit /b 1
)

echo Installation / mise a jour de PyInstaller...
python -m pip install --upgrade pyinstaller

echo.
echo Compilation en cours, patience...
python -m PyInstaller --onefile --windowed --name "ADIF_to_Cabrillo_F4GOP" ADIF_to_Cabrillo_F4GOP.py

echo.
if exist "dist\ADIF_to_Cabrillo_F4GOP.exe" (
    echo ============================================
    echo   TERMINE !
    echo   Ton .exe se trouve dans : dist\ADIF_to_Cabrillo_F4GOP.exe
    echo ============================================
) else (
    echo Une erreur s'est produite pendant la compilation.
    echo Regarde les messages ci-dessus pour le detail.
)

pause
