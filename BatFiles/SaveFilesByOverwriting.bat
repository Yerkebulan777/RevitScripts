@echo off
SET mypath=%~dp0
echo %mypath:~0,-1%
echo *******
echo.

python "D:\YandexDisk\RevitExportConfig\PyScripts\TempCleaner.py" "%mypath:~0,-1%"
python "D:\YandexDisk\RevitExportConfig\PyScripts\ScanFoldersForRevitFiles.py" "%mypath:~0,-1%"

%LOCALAPPDATA%\RevitBatchProcessor\BatchRvt.exe --settings_file "D:\YandexDisk\RevitExportConfig\Settings\SaveFilesByOverwriting.json"
"C:\Program Files\RevitBatchProcessor\BatchRvt.exe" --settings_file "D:\YandexDisk\RevitExportConfig\Settings\SaveFilesByOverwriting.json"

pause
