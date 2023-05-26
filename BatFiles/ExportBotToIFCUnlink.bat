@echo off

python "D:\YandexDisk\RevitExportConfig\PyScripts\TempCleaner.py"
%LOCALAPPDATA%\RevitBatchProcessor\BatchRvt.exe --settings_file "D:\YandexDisk\RevitExportConfig\Settings\ExportBotToIFCUnlink.json"
"C:\Program Files\RevitBatchProcessor\BatchRvt.exe" --settings_file "D:\YandexDisk\RevitExportConfig\Settings\ExportBotToIFCUnlink.json"

exit
