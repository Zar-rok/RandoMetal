@echo off
setlocal enabledelayedexpansion

for /f "tokens=2 delims= " %%i in ('python -V') do (

	set version=%%i
	set version=!version: =!
	set version=!version:.=!	
	
	if version LSS 279 (
		python get-pip.py
	)
	
	if version LSS 340 (
		python get-pip.py
	)
)

python -m pip install -U pip

pip install requests
pip install beautifulsoup4
pip install selenium
