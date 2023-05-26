# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts.

import os
import sys
from glob import glob

import clr

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

clr.AddReference("System")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from System.IO import Path
from Autodesk.Revit.DB import FilteredElementCollector, RevitLinkType, BuiltInParameter
from Autodesk.Revit.DB import ModelPathUtils, WorksetConfiguration

import revit_file_util
import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()

doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()


########################################################################################################################

def FindLinkedFilePath(projectPath, linkName):
    Output("\nStarting link search: " + linkName)
    for dir in os.listdir(projectPath):
        if "#" in dir: continue
        section = os.path.join(projectPath, dir)
        if os.path.isfile(section): continue
        for filepath in glob(os.path.join(section, "01_RVT", "*.rvt")):
            name, ext = os.path.splitext(os.path.basename(filepath))
            if name == linkName:
                Output("Was found: {}".format(name))
                return filepath
    return None


def ReSaveRevitFile(doc, directory, filepath):
    message = "Directory not found or file not shared"
    filename = Path.GetFileNameWithoutExtension(filepath)
    if doc.IsWorkshared and os.path.isdir(directory):
        try:
            message = "Start saved file: {}".format(filename)
            filepath = os.path.join(directory, filename + '.rvt')
            saveRevitModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filepath)
            revit_file_util.SaveAsNewCentral(doc, saveRevitModelPath, True)
            revit_file_util.RelinquishAll(doc)
            os.startfile(directory)
        except Exception as e:
            message = "EXCEPTION: {}".format(e.message)
        finally:
            pass
    return message


########################################################################################################################
unique = set()
Output("\n" + 100 * "*" + "\n")
directory = os.path.dirname(revitFilePath)
projectPath = os.path.normpath(directory.rsplit(os.sep, 2)[0])
revitFilePath = revitFilePath.strip("_detached").strip("_отсоединено")
########################################################################################################################
Output("Revit file path: {}".format(revitFilePath))
Output("Revit directory path: {}".format(directory))
Output("Project directory path: {}".format(projectPath))
for link in FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements():
    linkName = link.get_Parameter(BuiltInParameter.RVT_LINK_FILE_NAME_WITHOUT_EXT).AsString()
    linkPath = FindLinkedFilePath(projectPath, linkName)
    if linkName in unique:
        link.Unload(None)
    elif link and RevitLinkType.IsLoaded(doc, link.Id):
        Output("Result: link was loaded")
        unique.add(linkName)
    elif isinstance(linkPath, str) and isinstance(link, RevitLinkType):
        linkModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(linkPath)
        try:
            result = link.LoadFrom(linkModelPath, WorksetConfiguration())
            Output("Result: {}".format(result.LoadResult.ToString()))
            unique.add(linkName)
        except Exception as e:
            Output("\tERROR: {}".format(e.message))

########################################################################################################################
Output("\n" + 100 * "*" + "\n")
Output("RESULT: {}".format(ReSaveRevitFile(doc, directory, revitFilePath)))
Output("\n" + 100 * "*" + "\n")
########################################################################################################################
