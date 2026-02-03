@echo off
REM Forex Trader Bot - Windows Setup Script
REM Extract this zip file and run setup.bat

echo.
echo ========================================
echo   FOREX TRADER BOT - SETUP
echo ========================================
echo.

REM Create folders
if not exist "charts" mkdir charts
if not exist "data" mkdir data

echo ✅ Folders created!
echo.
echo Now you need to:
echo.
echo 1. Get Telegram Bot Token:
echo    - Open Telegram
echo    - Search for @BotFather
echo    - Send /newbot
echo    - Follow instructions
echo    - Copy the token
echo.
echo 2. Get Chat ID:
echo    - Search for @userinfobot
echo    - Send /start
echo    - Copy your Chat ID
echo.
echo 3. Set environment variables:
echo    - Right-click This PC > Properties
echo    - Advanced System Settings
echo    - Environment Variables
echo    - Add User variables:
echo      TELEGRAM_BOT_TOKEN=your_token_here
echo      TELEGRAM_CHAT_ID=your_chat_id_here
echo.
echo 4. Install Python dependencies:
echo    pip install flask pandas numpy matplotlib requests
echo.
echo 5. Run the bot:
echo    python app.py
echo.
echo Files will be saved to:
echo %CD%
echo.
pause
