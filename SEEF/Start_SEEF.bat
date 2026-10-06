@echo off
cd /d "%~dp0"
python launch_browser.py
if errorlevel 1 pause
