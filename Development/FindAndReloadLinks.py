# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts

import os

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *
from Autodesk.Revit.ApplicationServices import *
from Autodesk.Revit.Attributes import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import *
from Autodesk.Revit.Exceptions import *

from System.IO import *
from System.Linq import *

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()

doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()


# The code above is boilerplate, everything below is all yours.
# You can use almost any part of the Revit API here!
#########################################################################################
def FindLinkedFilePath(project_path, linkName):
    file_path = None
    for dirpath, dirnames, filenames in os.walk(project_path):
        for name in filenames:
            if name == linkName and "#" not in dirpath:
                file_path = dirpath + "\\" + name

    return file_path


def UnloadAllLoadedLinks(links_collector):
    Output(75 * "!")
    for li in links_collector:
        try:
            linkStatus = li.GetExternalFileReference().GetLinkedFileStatus().ToString()
            if linkStatus == "Loaded":
                li.Unload(None)
        except Exception as e:
            Output("\t!UNLOAD_EXCEPTION: " + str(e))
    Output(75 * "!")


def SyncWithRelinquishing(doc):
    # Set options for accessing central model
    transOpts = TransactWithCentralOptions()

    # Set options for synchronizing with central
    syncOpts = SynchronizeWithCentralOptions()

    # Sync with relinquishing any checked out elements or worksets
    relinquishOpts = RelinquishOptions(True)
    syncOpts.SetRelinquishOptions(relinquishOpts)

    # Do not automatically save local model after sync
    syncOpts.SaveLocalAfter = False
    syncOpts.Comment = "Исправление Путей Связанных Файлов"

    doc.SynchronizeWithCentral(transOpts, syncOpts)


def SaveByOverwriting(doc, doc_path):
    SAoptions = SaveAsOptions()
    SAoptions.OverwriteExistingFile = True

    if doc.IsWorkshared == True:
        WSAoptions = WorksharingSaveAsOptions()
        WSAoptions.SaveAsCentral = True
        SAoptions.SetWorksharingOptions(WSAoptions)

    doc.SaveAs(doc_path, SAoptions)

    if doc.IsWorkshared == True:
        Output("Synchronizing...")
        objTransactWithCentralOptions = TransactWithCentralOptions()
        objSynchronizeWithCentralOptions = SynchronizeWithCentralOptions()
        objRelinquishOptions = RelinquishOptions(True)

        objSynchronizeWithCentralOptions.SetRelinquishOptions(objRelinquishOptions)
        doc.SynchronizeWithCentral(objTransactWithCentralOptions, objSynchronizeWithCentralOptions)


#########################################################################################
doc_path = revitFilePath.replace("_detached", "").replace("_отсоединено", "")
project_path = doc_path.split("01_PROJECT")[0] + "01_PROJECT"

links_collector = FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements()

i = 1
Output("\nLinks in this document:")
for li in links_collector:
    Output(50 * "*")
    try:
        linkName = li.get_Parameter(BuiltInParameter.RVT_LINK_FILE_NAME_WITHOUT_EXT).AsString() + ".rvt"
        linkStatus = li.GetExternalFileReference().GetLinkedFileStatus().ToString()
        Output(" (" + str(i) + ") " + linkName + ": " + linkStatus)
    except Exception as e:
        Output(" ERROR: " + str(e))

    i += 1
    if linkStatus == "NotFound" or linkStatus == "Loaded":
        linkPath = FindLinkedFilePath(project_path, linkName)
        if linkPath is not None and "#" not in linkPath:
            Output("   ->Reloading Link...")
            try:
                linkModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(linkPath)
                result = li.LoadFrom(linkModelPath, WorksetConfiguration())
                Output("   ->Result: " + result.LoadResult.ToString())
            except Exception as e:
                Output("    !LOAD_EXCEPTION: " + str(e))
        else:
            Output("   ->File does not exist!")
            continue

#########################################################################################
Output(75 * "#")
Output("Resaving the document...")

if doc.IsWorkshared == True:
    Output(" ->Syncronzing with the central model.....")
    try:
        SyncWithRelinquishing(doc)
    except Exception as e:
        Output("    !SYNC_EXCEPTION: " + str(e))
        doc.Save()
        # SaveByOverwriting(doc, doc_path)
else:
    Output(" ->This document is not workshared, saving normally.....")
    doc.Save()
