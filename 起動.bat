@echo off
rem ダブルクリックで株シミュレータを起動する（この黒い画面を閉じるとアプリも終了する）
rem ※ cmd が正しく読めるよう、このファイルは Shift-JIS で保存している
cd /d "%~dp0"

if not exist ".venv\Scripts\streamlit.exe" (
    echo 初回のセットアップをしています。数分かかります...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo 株シミュレータを起動しています。ブラウザが自動で開きます。
echo この黒い画面を閉じると、アプリも終了します。
".venv\Scripts\streamlit.exe" run app.py
pause
