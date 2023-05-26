@echo off
SET mypath=%~dp0
echo %mypath:~0,-1%
echo *******
echo.

wmic printer where name="PDF24" call setdefaultprinter
python "D:\YandexDisk\RevitExportConfig\PyScripts\TempCleaner.py" "%mypath:~0,-1%"
python "D:\YandexDisk\RevitExportConfig\PyScripts\SetVirtualPrinterDriver.py" "%mypath:~0,-1%"
python "D:\YandexDisk\RevitExportConfig\PyScripts\ScanFoldersForRevitFiles.py" "%mypath:~0,-1%"
wmic printer where default=TRUE get name

%LOCALAPPDATA%\RevitBatchProcessor\BatchRvt.exe --settings_file "D:\YandexDisk\RevitExportConfig\Settings\ExportToPDF.json"
"C:\Program Files\RevitBatchProcessor\BatchRvt.exe" --settings_file "D:\YandexDisk\RevitExportConfig\Settings\ExportToPDF.json"

pause
