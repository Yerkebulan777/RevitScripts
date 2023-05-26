@echo off

wmic printer where name="PDF24" call setdefaultprinter
python "D:\YandexDisk\RevitExportConfig\PyScripts\TempCleaner.py"
python "D:\YandexDisk\RevitExportConfig\PyScripts\SetVirtualPrinterDriver.py"
wmic printer where default=TRUE get name

%LOCALAPPDATA%\RevitBatchProcessor\BatchRvt.exe --settings_file "D:\YandexDisk\RevitExportConfig\Settings\ExportBotToPDFUnlink.json"
"C:\Program Files\RevitBatchProcessor\BatchRvt.exe" --settings_file "D:\YandexDisk\RevitExportConfig\Settings\ExportBotToPDFUnlink.json"

exit




