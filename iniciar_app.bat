@echo off
echo "Configurando el entorno y ejecutando la aplicacion de Fase 4..."

REM Guarda el directorio actual
set CURRENT_DIR=%~dp0

REM Nombre del entorno virtual
set VENV_NAME=.venv

REM Comprueba si existe el entorno virtual
if not exist "%CURRENT_DIR%%VENV_NAME%" (
    echo "Creando entorno virtual..."
    python -m venv "%CURRENT_DIR%%VENV_NAME%"
    if %errorlevel% neq 0 (
        echo "Error: No se pudo crear el entorno virtual. Asegurate de tener Python instalado y en el PATH."
        goto :eof
    )
)

REM Activa el entorno virtual
echo "Activando entorno virtual..."
call "%CURRENT_DIR%%VENV_NAME%\Scripts\activate.bat"

REM Instala las dependencias
echo "Instalando dependencias desde requirements.txt..."
pip install -r "%CURRENT_DIR%requirements.txt"
if %errorlevel% neq 0 (
    echo "Error: No se pudieron instalar las dependencias."
    goto :eof
)


REM Establece la variable de entorno para Flask y ejecuta la app
echo "Iniciando la aplicacion Flask..."
set FLASK_APP=%CURRENT_DIR%app.py
set FLASK_ENV=development
flask run

echo "La aplicacion se ha detenido."
pause
:eof
