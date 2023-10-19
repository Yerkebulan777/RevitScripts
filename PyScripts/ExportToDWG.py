#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import zipfile

sys.path.append(r"C:\Program Files\IronPython 2.7\Lib")
sys.path.append(r"C:\Program Files\IronPython 2.7\Lib\site-packages")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\DLLs")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

from datetime import datetime, timedelta

import clr

clr.AddReference("System")
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import WorksetKind
from Autodesk.Revit.DB import BuiltInCategory
from Autodesk.Revit.DB import ViewSheet, ElementId
from Autodesk.Revit.DB import Family, RevitLinkType
from Autodesk.Revit.DB import WorksetDefaultVisibilitySettings
from Autodesk.Revit.DB import Transaction, SolidGeometry, LineScaling
from Autodesk.Revit.DB import FilteredElementCollector, FilteredWorksetCollector
from Autodesk.Revit.DB import DWGExportOptions, ACADVersion, ACAObjectPreference
from Autodesk.Revit.DB import PropOverrideMode, ExportColorMode, TextTreatment, ExportUnit

from System.Collections.Generic import List
from System.IO import Path

import revit_script_util
from revit_script_util import Output

########################################################################################################################

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()
doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()

########################################################################################################################
exportOptions = DWGExportOptions()
version = doc.Application.VersionNumber
exportOptions.LineScaling = LineScaling.PaperSpace
exportOptions.Colors = ExportColorMode.TrueColorPerView
exportOptions.ExportOfSolids = SolidGeometry.ACIS
exportOptions.FileVersion = ACADVersion.R2007
exportOptions.HatchPatternsFileName = r"C:\Program Files\Autodesk\Revit " + version + "\\" + r"ACADInterop\acdbiso.pat"
exportOptions.LinetypesFileName = r"C:\Program Files\Autodesk\Revit " + version + "\\" + r"ACADInterop\acdbiso.lin"
exportOptions.HideScopeBox = True
exportOptions.HideUnreferenceViewTags = True
exportOptions.HideReferencePlane = True
exportOptions.LayerMapping = "AIA"
exportOptions.PropOverrides = PropOverrideMode.ByEntity
exportOptions.ACAPreference = ACAObjectPreference.Object
exportOptions.TextTreatment = TextTreatment.Exact
exportOptions.TargetUnit = ExportUnit.Millimeter
exportOptions.NonplotSuffix = "NPLT"
exportOptions.MergedViews = True
exportOptions.SharedCoords = False
exportOptions.MarkNonplotLayers = False
exportOptions.PreserveCoincidentLines = False

########################################################################################################################

matchSpace = re.compile(r"\s+")
matchLength = re.compile(r"^((.){,115}\b)")
matchDigits = re.compile(r'(\d+\.\d+|\d+)')
IllegalCharacters = re.compile(r"([+*^#%!?@$&£{}/|;:<>`~\]\[\\]+)")


########################################################################################################################
def stripIllegalCharacters(message, username=""):
    message = message.encode('cp1251', 'ignore').decode('cp1251') if isinstance(message, str) else 'unnamed'
    message = "{}{}".format(matchLength.match(message).group(0), '...') if len(message) > 100 else message
    message = IllegalCharacters.sub('', message, re.UNICODE).rstrip(username)
    message = message.replace('"', '').replace('/', '').rstrip('_').strip()
    message = matchSpace.sub(' ', message)
    return message


def getSessionTime(sessionId):
    session_time = sessionId
    session_time = session_time.replace("<", "")
    session_time = session_time.replace(">", "")
    session_time = session_time.replace("T", ".")
    session_time = session_time.replace(":", ".")
    session_time = session_time.split(".")
    session_time = session_time[:-2]
    year = int(session_time[0].split("-")[0])
    month = int(session_time[0].split("-")[1])
    day = int(session_time[0].split("-")[2])
    hour = int(session_time[1])
    mins = int(session_time[2])
    current_time = datetime(year, month, day, hour, mins, 0) + timedelta(hours=6, minutes=30)
    session_time = format(current_time.replace(minute=30), '%Y-%m-%d_%H-%M')
    return session_time


def get_subdirectory(ipath, directory):
    folder = os.path.basename(os.path.dirname(ipath))
    drive, tail = os.path.splitdrive(ipath)
    ipath = os.path.realpath(ipath)
    while os.path.exists(ipath):
        if folder == '': return drive
        result = os.path.join(ipath, folder)
        ipath, folder = os.path.split(ipath)
        if folder.endswith(directory):
            return result


def determine_folder_structure(ipath, directory, folder=None):
    result = os.path.join(get_subdirectory(ipath, 'PROJECT'), directory)
    if bool(os.path.exists(result) and folder):
        result = os.path.join(result, folder)
    if not os.path.exists(result):
        os.makedirs(result)
    return result


def unloadAllLinks(revit_file_path):
    Output("\nStart unload links ...")
    section = os.path.basename(os.path.dirname(os.path.dirname(revit_file_path)))
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks)
    Output("Is Revit file section: {}".format(section))
    rvtLinkTypes = collector.OfClass(RevitLinkType)
    for idx, linkType in enumerate(rvtLinkTypes):
        if RevitLinkType.IsLoaded(doc, linkType.Id):
            try:
                linkType.Unload(None)
            except Exception as error:
                Output("Unload error: {}".format(error))
    return


def setWorksetVisibility(doc):
    Output("\nStart check worksets visibility...")
    wsDefaultSet = WorksetDefaultVisibilitySettings.GetWorksetDefaultVisibilitySettings(doc)
    workSets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()
    Output("Worksets count {}".format(len(workSets)))
    with Transaction(doc, "WorksetVisibility") as trx:
        trx.Start()
        for workset in workSets:
            worksetName = "{}".format(workset.Name).strip()
            Output("Workset name: {}".format(worksetName))
            if (worksetName.startswith('#')):
                if workset.IsOpen and wsDefaultSet.IsValidObject:
                    try:
                        wsDefaultSet.SetWorksetVisibility(workset.Id, False)
                        Output("Workset {} not visible".format(worksetName))
                    except Exception as error:
                        Output("Workset error: {} {}".format(worksetName, error))
        trx.Commit()
    return wsDefaultSet.Dispose()


def deleteFamilyByName(family_name):
    for family in FilteredElementCollector(doc).OfClass(Family).ToElements():
        if family.IsValidObject and family.Name.Equals(family_name):
            Output("\nDeleting the {0} family".format(family_name))
            doc.Delete(family.Id)
            return


def output_text(message, directory, filename='Exception'):
    filepath = os.path.join(directory, filename + '.txt')
    if os.path.isfile(filepath): os.remove(filepath)
    with open(filepath, mode='a') as txf:
        txf.write(message)
        Output(message)


def exportToDWG(directory, sheetName, viewSheet):
    collection = List[ElementId]([viewSheet.Id])
    sheetName = stripIllegalCharacters(sheetName)
    filePath = os.path.join(directory, sheetName + ".dwg")
    try:
        if (doc.Export(directory, sheetName, collection, exportOptions)):
            [time.sleep(0.5) for _ in xrange(60) if not os.path.exists(filePath)]
            fileSize = str(round(float(os.stat(filePath).st_size / 1024)))
            message = "{0} \t {1}(Kb)".format(sheetName, fileSize)
            return Output(message)
    except Exception as ex:
        output_text(ex.message, directory, sheetName)
        return


def zipTheFolderWithSubfolders(exportDirectory, fileName):
    output = os.path.join(os.path.dirname(exportDirectory), fileName + '.zip')
    zipObject = zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED)
    rootLength = int(len(exportDirectory) + 1)
    os.startfile(os.path.dirname(exportDirectory))
    for base, dirs, files in os.walk(exportDirectory):
        for file in files:
            filename = os.path.join(base, file)
            zipObject.write(filename, filename[rootLength:])
    zipObject.close()
    return fileName


def getSheetNumber(sequenceSheet):
    stringNumber = sequenceSheet.SheetNumber
    stringNumber = stringNumber.encode('ascii', 'ignore')
    stringNumber = IllegalCharacters.sub('.', stringNumber.strip())
    stringNumber = "".join(matchDigits.findall(stringNumber))
    return stringNumber


########################################################################################################################

sessionTime = getSessionTime(sessionId)
revitFileName = Path.GetFileNameWithoutExtension(doc.PathName)
revitFileName = revitFileName.rstrip("_detached").rstrip("_отсоединено")
revitFileName = revitFileName.encode('ascii', 'ignore').decode('ascii').rstrip('_').strip()
exportDirectory = determine_folder_structure(revitFilePath, '02_DWG', sessionTime)
exportDirectory = os.path.join(exportDirectory, revitFileName)
if not os.path.isdir(exportDirectory):
    os.makedirs(exportDirectory)

########################################################################################################################

setWorksetVisibility(doc)
# unloadAllLinks(revitFileName)
with Transaction(doc, "Hide families") as trx:
    trx.Start()
    deleteFamilyByName("BIM-Конфликт")
    deleteFamilyByName("BIM1-Clash Sphere")
    deleteFamilyByName("Задание на отверстие")
    deleteFamilyByName("Задание на проем")
    deleteFamilyByName("InternalOrigin")
    doc.Regenerate()
    trx.Commit()

########################################################################################################################

Output("\n\n\n")
Output("*Export to DWG processing script is running!")
Output("*Export name: " + revitFileName)
Output("*Directory: " + sessionTime)
Output("\n\n\n")

########################################################################################################################
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
sheets = sorted(sheets, key=lambda x: (len(x.SheetNumber), x.SheetNumber))
Output("\r\n\tStart export sheets...")
########################################################################################################################

lengthName = int(0)
printCount = int(0)
sheetCount = len(sheets)
for sequenceSheet in sheets:
    if sequenceSheet.CanBePrinted:
        sheetName = sequenceSheet.Name
        sheetNumber = getSheetNumber(sequenceSheet)
        sequenceName = "{} - Лист - {} - {}".format(revitFileName, sheetNumber, sheetName)
        exportToDWG(exportDirectory, sequenceName, sequenceSheet)
        lengthName += len(sequenceName)
        printCount += 1

########################################################################################################################
Output("\r\n\tAll printed sheets: {} in {}".format(printCount, sheetCount))
Output("\r\n\tMiddle sheet name length: {}".format((lengthName / printCount)))
########################################################################################################################
Output('\n\n\n')
Output('><' * 100)
message = zipTheFolderWithSubfolders(exportDirectory, revitFileName)
Output("\r\t\tCreating a zip archive... {}".format(message))
Output('><' * 100)
Output(
    '\n\n\n')  ########################################################################################################################
