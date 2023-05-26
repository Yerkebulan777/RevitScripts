# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts.

import os
import time
from datetime import datetime, timedelta

import clr

clr.AddReference("System")
clr.AddReference("System.Core")
from System.IO import *

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import FilteredElementCollector, Transaction
from Autodesk.Revit.DB import ViewSet, Family, ViewSheet, View, FilterElement, ViewType
from Autodesk.Revit.DB import DWFExportOptions, DWFImageFormat, DWFImageQuality, ExportPaperFormat

# from Autodesk.Revit.DB import *
# from Autodesk.Revit.UI import *
# from Autodesk.Revit.Attributes import *
# from Autodesk.Revit.UI.Selection import *
# from Autodesk.Revit.ApplicationServices import *

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()

doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()


# The code above is boilerplate, everything below is all yours.
# You can use almost any part of the Revit API here!
def ExportDWFwithCustomOptions(document, full_export_path):
    options = DWFExportOptions()
    options.CropBoxVisible = False
    options.ExportingAreas = True
    options.ExportObjectData = True
    options.ExportTexture = True
    options.ImageFormat = DWFImageFormat.Lossless
    options.ImageQuality = DWFImageQuality.High
    options.MergedViews = True
    options.PaperFormat = ExportPaperFormat.Default
    options.PortraitLayout = False
    options.StopOnError = False

    views = ViewSet()
    # find the sheets
    coll = FilteredElementCollector(doc)
    allSheets = coll.OfClass(ViewSheet).ToElements()

    for sheet in allSheets:
        if sheet.CanBePrinted == True:
            views.Insert(sheet)
        else:
            Output("  This view, <" + sheet.SheetNumber + "-" + sheet.Name + "> is not printable!")
            continue

    saveName = doc.Title.split("_detached")[0]
    saveName = saveName.split("_отсоединено")[0]
    saveName = saveName.split(".rvt")[0]

    try:
        document.Export(full_export_path, saveName, views, options)
    except Exception as ex:
        Output(ex.message)


def GetSaveTime(current_sessionId):
    saveTime = current_sessionId
    saveTime = saveTime.replace("<", "")
    saveTime = saveTime.replace(">", "")
    saveTime = saveTime.replace("T", ".")
    saveTime = saveTime.replace(":", ".")
    saveTime = saveTime.split(".")
    saveTime = saveTime[:-2]

    year = int(saveTime[0].split("-")[0])
    month = int(saveTime[0].split("-")[1])
    day = int(saveTime[0].split("-")[2])
    hour = int(saveTime[1])
    mins = int(saveTime[2])
    current_time = datetime(year, month, day, hour, mins, 0)
    six_hours_from_now = current_time + timedelta(hours=6)

    saveTime = format(six_hours_from_now, '%Y-%m-%d_%H.%M')

    return saveTime


def DeleteFamily(family_name):
    for family in FilteredElementCollector(doc).OfClass(Family).ToElements():
        if family and family.Name.Contains(family_name):
            with Transaction(doc, "Delete Family") as trans:
                trans.Start()
                doc.Delete(family.Id)
                Output("Delete Family " + family_name)
                trans.Commit()
                break
    return


# Determine the filesystem for saving the exported files
def DetermineFolderStructure(path, file_type_folder):
    full_export_path = path
    working_directory = path
    rvt_folder_name = ""
    # Determine which file system we are working with:
    if "1_Design" in path:
        working_directory = working_directory.split(r"\1_Design")[0]
        rvt_folder_name = path.split(r"\1_Design")[1]
        rvt_folder_name = rvt_folder_name[1:]
        rvt_folder_name = rvt_folder_name.partition("\\")[0]
    elif "1_V RABOTE" in path and "RVT" in path:
        working_directory = working_directory.split(r"\RVT")[0]
    elif "2_NA VIDACHU" in path and "RVT" in path:
        working_directory = working_directory.split(r"\RVT")[0]
    elif "01_PROJECT" in path and "01_RVT" in path:
        working_directory = working_directory.split(r"\01_RVT")[0]
        rvt_folder_name = path.split(r"\01_PROJECT")[1]
        rvt_folder_name = rvt_folder_name[1:]
        rvt_folder_name = rvt_folder_name.partition("\\")[0]
    else:
        working_directory = working_directory.rsplit('\\', 1)[0]

    # Create/Check the appropriate folders for determined file system:
    if not rvt_folder_name:
        pre_export_path = working_directory + "\\" + file_type_folder
        if not os.path.exists(pre_export_path):
            os.makedirs(pre_export_path)

        full_export_path = pre_export_path + "\\" + GetSaveTime(sessionId)
        if not os.path.exists(full_export_path):
            os.makedirs(full_export_path)
    else:
        if "1_Design" in path:
            pre_export_path = working_directory + r"\4_Publication" + "\\" + rvt_folder_name
            if not os.path.exists(pre_export_path):
                os.makedirs(pre_export_path)

            export_path = working_directory + r"\4_Publication" + "\\" + rvt_folder_name + "\\" + file_type_folder
            if not os.path.exists(export_path):
                os.makedirs(export_path)

            full_export_path = export_path + "\\" + GetSaveTime(sessionId)
            if not os.path.exists(full_export_path):
                os.makedirs(full_export_path)
        elif "01_PROJECT" in path and "01_RVT" in path:
            pre_export_path = working_directory + r"\04_DWF"
            if not os.path.exists(pre_export_path):
                os.makedirs(pre_export_path)

            full_export_path = pre_export_path + "\\" + GetSaveTime(sessionId)
            if not os.path.exists(full_export_path):
                os.makedirs(full_export_path)

    return (working_directory, rvt_folder_name, full_export_path)


file_type = "DWF"
working_directory = DetermineFolderStructure(revitFilePath, file_type)[0]
rvt_folder_name = DetermineFolderStructure(revitFilePath, file_type)[1]
the_export_path = DetermineFolderStructure(revitFilePath, file_type)[2]

Output(" Session ID : " + sessionId + "\n")
Output(" The working directory is: " + working_directory + "\n")
Output(" The revit folder name: " + rvt_folder_name + "\n")
#########################################################################################
Output(" Deleting the Clash Spheres....\n")
DeleteFamily("BIM-Конфликт")
DeleteFamily("BIM1-Clash Sphere")
DeleteFamily("InternalOrigin")

Output(" Turning the <BIM-Конфликт> filter off in all views....")
views_collector = FilteredElementCollector(doc).OfClass(View).ToElements()
filters_collector = FilteredElementCollector(doc).OfClass(FilterElement).ToElements()
filter_to_turn_off = None

for viewfilter in filters_collector:
    if viewfilter.Name == "BIM-Конфликт" or viewfilter.Name == "BIM-Конфликт (Все)":
        filter_to_turn_off = viewfilter

if filter_to_turn_off is not None:
    with Transaction(doc, "Turn off Filter") as trans:
        trans.Start()
        # Cycle through views
        for view in views_collector:
            if view.ViewType is not ViewType.Schedule:
                try:
                    view.SetFilterVisibility(filter_to_turn_off.Id, False)
                except Exception as e:
                    pass
                    # Output( " ->[1] " + str(e).replace("\n","") )
        trans.Commit()

Output(" Export path: " + the_export_path)
time.sleep(60)

with Transaction(doc, "DWF Export") as trans:
    trans.Start()
    ExportDWFwithCustomOptions(doc, the_export_path)
    trans.RollBack()
