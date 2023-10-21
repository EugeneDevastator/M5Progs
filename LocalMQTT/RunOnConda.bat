set SCRIPT_DIR=%~dp0
if not exist "%SCRIPT_DIR%\mqenv" (
    call conda create --prefix ./mqenv python=3.7.9 --yes
)
call conda activate "%SCRIPT_DIR%\mqenv"
pip install -r requirements.txt > NUL 2>&1
python mqtt.py
