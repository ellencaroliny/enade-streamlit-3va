@echo off
cd /d "%~dp0"
echo ========================================
echo  Cubo ENADE - Streamlit Dashboard
echo ========================================
echo.
echo Preparando banco de dados...
python prepare_data.py
if errorlevel 1 (
    echo Erro ao preparar banco de dados.
    pause
    exit /b 1
)
echo.
echo Iniciando Streamlit...
echo Acesse: http://localhost:8501
echo.
streamlit run app.py
pause
