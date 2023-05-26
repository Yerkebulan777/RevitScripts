# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import re
import os
import clr
import time
import codecs
import fnmatch
import datetime

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("System.Drawing")
clr.AddReference("System.Management")

import System
from System.IO import Path
from System.Threading import Mutex

clr.ImportExtensions(System.Linq)
from Microsoft.Win32 import Registry, RegistryValueKind

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import RevitLinkType
from Autodesk.Revit.DB import FamilyInstance
from Autodesk.Revit.DB import DisplayUnitType
from Autodesk.Revit.DB import BrowserOrganization
from Autodesk.Revit.DB import Transaction, FilteredElementCollector
from Autodesk.Revit.DB import ElementId, BuiltInCategory, BuiltInParameter, UnitUtils
from Autodesk.Revit.DB import PrintSetting, PrintRange, ViewSheet, ViewSheetSet, ViewSet
from Autodesk.Revit.DB import PageOrientationType, ZoomType, PaperPlacementType
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter
from Autodesk.Revit.DB import RasterQualityType, HiddenLineViewsType
from Autodesk.Revit.DB import FilterStringRule, FilterStringEquals
from Autodesk.Revit.DB import ColorDepthType

########################################################################################################################
########################################################################################################################
########################################################################################################################
import pinvoke_winAPI_util as winApiUtil

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()
doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()

Output("Create Mutex")
success = clr.Reference[bool]()
mutex = Mutex(False, r"Global\PrintMutex", success)
Output("Mutex is created => {0}\n".format(success))
########################################################################################################################
########################################################################################################################
########################################################################################################################
today = datetime.datetime.now()
matchSpace = re.compile(r"[ ]+")
matchLength = re.compile(r"^((.){,95}\b)")
matchPrefix = re.compile(r"^(\d\s)|(\.\w+)|(\s*)")
TempDirectory = os.path.normpath(os.getenv("TEMP"))
fileTempInput = os.path.join(TempDirectory, "PrintTempPath.txt")
IllegalCharacters = re.compile(r"([+*^#%!?@$&£{}/|;:<>`~\]\[\\]+)")


def unloadAllLinks():
    Output("\nStart unload links ...")
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks)
    for idx, linkType in enumerate(collector.OfClass(RevitLinkType)):
        if RevitLinkType.IsLoaded(doc, linkType.Id):
            try:
                linkType.Unload(None)
                Output("Unload link: {0}".format(idx + 1))
            except Exception as error:
                Output("Unload error: {0}".format(error))
    return


def stripIllegalCharacters(line, username=""):
    line = line.encode('cp1251', 'ignore').decode('cp1251') if isinstance(line, str) else 'unnamed'
    line = "{}{}".format(matchLength.match(line).group(0), '...') if len(line) > 100 else line
    line = IllegalCharacters.sub('', line, re.UNICODE).rstrip(username)
    line = line.replace('"', '').replace('/', '').rstrip('_').strip()
    line = "{:<100}".format(line).rstrip()
    line = matchSpace.sub(' ', line)
    return line


def getViewSheetByNumber(sheetNumber):
    pvp = ParameterValueProvider(ElementId(BuiltInParameter.SHEET_NUMBER))
    filter_rule = FilterStringRule(pvp, FilterStringEquals(), sheetNumber, True)
    collector = FilteredElementCollector(doc).OfClass(ViewSheet).OfCategory(BuiltInCategory.OST_Sheets)
    sheet = collector.WherePasses(ElementParameterFilter(filter_rule)).FirstElement()
    return sheet


def setRegistryValue(registryPath, keyName, newValue, user=True):
    registry = Registry.CurrentUser
    if user == False: registry = Registry.LocalMachine
    try:
        registryKey = registry.OpenSubKey(registryPath, True)
        oldValue = registryKey.GetValue(keyName)
        if bool(oldValue != newValue and newValue.isdigit() == False):
            registryKey.SetValue(keyName, newValue, RegistryValueKind.String)
        elif bool(oldValue != newValue and newValue.isdigit() == True):
            registryKey.SetValue(keyName, int(newValue), RegistryValueKind.DWord)
        registryKey.Close()
    except WindowsError as error:
        Output("Warning!: {}".format(error))
        return
    return bool(newValue)


def setPrintSettings(print_format, width_mm, height_mm, default):
    orientation = ""
    printManager = doc.PrintManager
    printSetup = printManager.PrintSetup
    printManager.PrintSetup.CurrentPrintSetting = printSetup.InSession
    parameters = printManager.PrintSetup.CurrentPrintSetting.PrintParameters

    if (default == True and width_mm > height_mm):
        orientation, parameters.PageOrientation = 'A', PageOrientationType.Landscape
    if (default == False and width_mm > height_mm):
        orientation, parameters.PageOrientation = 'K', PageOrientationType.Portrait
    if (default == True and height_mm > width_mm):
        orientation, parameters.PageOrientation = 'K', PageOrientationType.Portrait
    if (default == False and height_mm > width_mm):
        orientation, parameters.PageOrientation = 'A', PageOrientationType.Landscape

    format_name = "{}{}({}x{})".format(print_format, orientation, sheet_width, sheet_height)
    print_settings = FilteredElementCollector(doc).OfClass(PrintSetting).ToElements()
    if any([x for x in print_settings if x.Name == format_name]): return format_name

    parameters.ZoomType = ZoomType.Zoom
    parameters.PaperPlacement = PaperPlacementType.Center
    parameters.ColorDepth = ColorDepthType.Color
    parameters.RasterQuality = RasterQualityType.High
    parameters.HiddenLineViews = HiddenLineViewsType.VectorProcessing
    parameters.ViewLinksinBlue = False
    parameters.HideReforWorkPlanes = True
    parameters.HideUnreferencedViewTags = True
    parameters.HideCropBoundaries = True
    parameters.HideScopeBoxes = True
    parameters.ReplaceHalftoneWithThinLines = False
    parameters.MaskCoincidentLines = False
    parameters.Zoom = 99.95

    with Transaction(doc, "SavePrintSettings") as trx:
        trx.Start()
        doc.Regenerate()
        printManager.Apply()
        printManager = doc.PrintManager
        for pSize in printManager.PaperSizes:
            if bool(pSize.Name.Equals(print_format)):
                parameters.PaperSize = pSize
                printSetup.SaveAs(format_name)
                printManager.Apply()
                doc.Regenerate()
        trx.Commit()

    Output("\r\n\t" + format_name)
    return format_name


def get_python_path():
    environ_paths = os.environ.get("PATH", None)
    basePaths = [os.path.realpath(path) for path in environ_paths.split(';') if os.path.exists(path)]
    for basepath in basePaths:
        for entry in os.listdir(basepath):
            if fnmatch.fnmatch(entry, 'python.exe'):
                if 'Python' in os.path.basename(os.path.normpath(basepath)):
                    python_path = os.path.join(basepath, entry)
                    return python_path


def call_python_script(script_path, arg01=None, arg02=None, arg03=None, result=""):
    exists = os.path.exists(os.path.normpath(script_path))
    Output('\nRunning {0} => {1}'.format(exists, script_path))
    if exists:
        try:
            process = System.Diagnostics.Process()
            start = System.Diagnostics.ProcessStartInfo()
            start.Arguments = str.format("{0} {1} {2} {3}", script_path, arg01, arg02, arg03)
            start.RedirectStandardOutput = True
            start.RedirectStandardError = True
            start.FileName = get_python_path()
            start.UseShellExecute = False
            start.CreateNoWindow = True
            process.StartInfo = start
            process.Start()
            process.WaitForExit()
            result += process.StandardOutput.ReadToEnd()
            result += process.StandardError.ReadToEnd()
        except Exception as ex:
            result += ex.message
    return result


def get_sheet_format(width, height, format='Undefined', default=False, tolerance=5):
    settings = System.Drawing.Printing.PrinterSettings()
    print_document = System.Drawing.Printing.PrintDocument()
    print_document.PrinterSettings = settings
    printer_name = settings.PrinterName
    minval = min(width, height) + tolerance
    maxval = max(width, height) - tolerance
    for psz in settings.PaperSizes:
        if (tolerance < 1): break
        psw = round((psz.Width * 25.4) / 100)
        psh = round((psz.Height * 25.4) / 100)
        if minval > min(psw, psh) and maxval < max(psw, psh):
            diff = abs((psw - width) + (psh - height))
            if diff < tolerance:
                default = bool(psw < psh)
                format = psz.PaperName
                tolerance = diff

    return printer_name, format, default


def organizationGroupFilename(view_sheet, revit_file_name):
    organization = BrowserOrganization.GetCurrentBrowserOrganizationForSheets(doc)
    for info in organization.GetFolderItems(view_sheet.Id):
        if info.IsValidObject:
            try:
                reference = doc.GetElement(info.ElementId)
                parameter = view_sheet.get_Parameter(reference.GuidValue)
                prefix = matchPrefix.sub('', parameter.AsString())
                revit_file_name = revit_file_name + prefix.strip()
            except:
                pass
    return revit_file_name


def override_printer_settings(sheet_width, sheet_height, printer_name='PDF24'):
    result_name, format, default = get_sheet_format(sheet_width, sheet_height)
    if not bool(format != 'Undefined' and printer_name == result_name):
        if (printer_name != result_name): winApiUtil.setDefaultPrinter(printer_name)
        if (format == 'Undefined'):
            message = call_python_script(cps_script_path, sheet_width, sheet_height, printer_name)
            Output("\nUndefined format: ({}x{})".format(sheet_width, sheet_height))
            Output("\nResult override script settings: {}".format(message))
            return get_sheet_format(sheet_width, sheet_height)
    return result_name, format, default


########################################################################################################################
printer_name, pdf_directory_name, pdf24RegPath = 'PDF24', '03_PDF', r"Software\PDF24\Services\PDF"
########################################################################################################################

revitFileName = Path.GetFileNameWithoutExtension(revitFilePath)
revitFileName = revitFileName.strip("_detached").strip("_отсоединено")
revitFileName = stripIllegalCharacters(revitFileName)

script_directory = r"D:\YandexDisk\RevitExportConfig\PyScripts"
cps_script_path = os.path.join(script_directory, 'CustomPaperSize.py')
mpf_script_path = os.path.join(script_directory, 'MergePdfFiles.py')

########################################################################################################################
Output("\n" + "#" * 125 + "\n")
Output("Export to PDF script is running!")
Output('Revit file path: ' + revitFilePath)
Output('Revit file name: ' + revitFileName)
Output("\n" + "#" * 125 + "\n")
########################################################################################################################

unloadAllLinks()
printManager = doc.PrintManager
with Transaction(doc, "PrintSetUp") as transaction:
    printManager.Dispose()
    transaction.Start()
    printManager.SelectNewPrintDriver(printer_name)
    printManager.Apply()
    printManager.PrintRange = PrintRange.Select
    printManager.Apply()
    printManager.CombinedFile = False
    printManager.Apply()
    printManager.PrintToFile = True
    printManager.Apply()
    transaction.Commit()

########################################################################################################################

sheetDict = {}
unit_millimeters = DisplayUnitType.DUT_MILLIMETERS
collector = FilteredElementCollector(doc).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_TitleBlocks)
sheetBlocks = collector.WhereElementIsNotElementType().ToElements()
for title_block in sheetBlocks:
    title_name = stripIllegalCharacters(title_block.Name)
    sheetNumber = title_block.get_Parameter(BuiltInParameter.SHEET_NUMBER).AsString()
    sheet_width_dbl = title_block.get_Parameter(BuiltInParameter.SHEET_WIDTH).AsDouble()
    sheet_height_dbl = title_block.get_Parameter(BuiltInParameter.SHEET_HEIGHT).AsDouble()
    sheet_width = int(UnitUtils.ConvertFromInternalUnits(sheet_width_dbl, unit_millimeters))
    sheet_height = int(UnitUtils.ConvertFromInternalUnits(sheet_height_dbl, unit_millimeters))
    def_printer_name, format, default = override_printer_settings(sheet_width, sheet_height)
    formValid = bool(def_printer_name == printer_name and format != 'Undefined')
    if bool(formValid and mutex):
        viewSheet = getViewSheetByNumber(sheetNumber)
        if bool(viewSheet and viewSheet.CanBePrinted):
            sheet_format = setPrintSettings(format, sheet_width, sheet_height, default)
            if sheetDict.has_key(sheet_format):
                sheetDict[sheet_format].append(viewSheet)
            elif not sheetDict.has_key(sheet_format):
                sheetDict.update({sheet_format: [viewSheet]})

########################################################################################################################

with Transaction(doc, "DeleteAllViewSettings") as transaction:
    transaction.Start()
    viewSheetSetting = printManager.ViewSheetSetting
    for sheetSetting in FilteredElementCollector(doc).OfClass(ViewSheetSet).ToElements():
        if sheetSetting.IsValidObject:
            viewSheetSetting.CurrentViewSheetSet = printManager.ViewSheetSetting.InSession
            viewSheetSetting.CurrentViewSheetSet = sheetSetting
            printManager.ViewSheetSetting.Delete()
            printManager.Apply()
    viewSheetSetting.Dispose()
    transaction.Commit()

########################################################################################################################
countPrint = int(0)
countBlock = len(sheetBlocks)
countSheet = sum(len(sheetDict.get(x)) for x in sheetDict.iterkeys())
Output("\nAll valid sheets {} in {}".format(countSheet, countBlock))
printAllSettings = FilteredElementCollector(doc).OfClass(PrintSetting).ToElements()
########################################################################################################################

with Transaction(doc, "PrintViews") as transaction:
    transaction.Start()
    for settingName in sheetDict.iterkeys():
        printSheets = sheetDict.get(settingName)
        Output("\nStart {} printing {} sheets...\n".format(settingName, len(printSheets)))
        printSetting = [pst for pst in printAllSettings if pst.Name == settingName][0]
        printManager.PrintSetup.CurrentPrintSetting = printSetting
        printManager.Apply()  # Set print settings
        for idx, viewSheet in enumerate(printSheets):
            mutex.WaitOne()
            try:
                myViewSet = ViewSet()
                myViewSet.Insert(viewSheet)
                viewSheetSetting = printManager.ViewSheetSetting
                viewSheetSetting.CurrentViewSheetSet.Views = myViewSet
                outName = organizationGroupFilename(viewSheet, revitFileName)
                outPath = os.path.normpath(os.path.join(TempDirectory, outName.strip()))
                sheetName = viewSheet.get_Parameter(BuiltInParameter.SHEET_NAME).AsString()
                sheetNumber = viewSheet.get_Parameter(BuiltInParameter.SHEET_NUMBER).AsString()
                fileName = stripIllegalCharacters("Лист-{} - {}".format(sheetNumber, sheetName))
                viewSheetSetting.SaveAs("{}-{}.{}".format(settingName, countPrint, idx))
                filePath = os.path.normpath(os.path.join(outPath, fileName + '.pdf'))
                if not os.path.exists(outPath): os.makedirs(outPath)
                if os.path.exists(filePath): os.remove(filePath)
                printManager.PrintToFileName = filePath
                printManager.Apply()
                if setRegistryValue(pdf24RegPath, "AutoSaveDir", outPath):
                    if setRegistryValue(pdf24RegPath, "AutoSaveFilename", fileName):
                        if bool(printManager.SubmitPrint() and viewSheetSetting.Delete()):
                            sec = len([time.sleep(0.5) for _ in xrange(45) if not os.path.exists(filePath)])
                            if os.path.exists(filePath): countPrint += 1
                            if sec > 0: Output("\t{}".format(fileName))
            except Exception as exc:
                Output("\r\n\tEXCEPTION: {}!!!".format(exc.message))
                Output(fileName)
                Output(filePath)
                time.sleep(5)
            finally:
                mutex.ReleaseMutex()
                Output()
    transaction.Commit()

#######################################################################################################################
setRegistryValue(pdf24RegPath, "AutoSaveFilename", "$fileName")
Output("\nAll printed sheets {} in {}\n".format(countPrint, countSheet))
#######################################################################################################################

if bool(countPrint):
    mutex.WaitOne()
    Output('\n' + '><' * 100 + '\n')
    with codecs.open(fileTempInput, 'w', "cp1251") as fTemp: fTemp.write(revitFilePath)
    Output(call_python_script(mpf_script_path, revitFileName))
    Output('\n' + '><' * 100 + '\n')
    mutex.ReleaseMutex()

#######################################################################################################################
