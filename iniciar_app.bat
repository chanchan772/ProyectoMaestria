@echo off
echo ============================================
echo   Monitoreo de Calidad del Aire
echo   Universidad Central - Maestria en Analitica de Datos
echo ============================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.11 o superior
    pause
    exit /b 1
)

echo Verificando instalacion de Python: OK
echo.

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ADVERTENCIA: No se encontro entorno virtual
    echo Ejecutando con Python global...
)

echo.
echo Iniciando aplicacion Flask...
echo La aplicacion se abrira en: http://localhost:5000
echo.
echo Presiona Ctrl+C para detener el servidor
echo ============================================
echo.

REM Ejecutar aplicacion Flask
python app.py

pause
