# !/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

from cleaning_parameters_util import cleaning_parameters
from set_navisworks_view_util import set_navisworks_view
from set_floor_number_util import set_floor_number

import os
import clr
import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
from System.IO import Path
from System import EventHandler
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import BuiltInCategory, GroupType
from Autodesk.Revit.DB import IFailuresPreprocessor, BuiltInFailures
from Autodesk.Revit.DB import FailureSeverity, FailureProcessingResult, FailureResolutionType
from Autodesk.Revit.DB import ModelPathUtils, PerformanceAdviser, PerformanceAdviserRuleId
from Autodesk.Revit.DB import ElementId, Transaction, FilteredElementCollector, ImportInstance
from Autodesk.Revit.DB.Events import FailuresProcessingEventArgs

########################################################################################################################

import revit_file_util
import revit_script_util
from revit_script_util import Output

revit_file_path = revit_script_util.GetRevitFilePath()
sessionId = revit_script_util.GetSessionId()
doc = revit_script_util.GetScriptDocument()
uiapp = revit_script_util.GetUIApplication()


########################################################################################################################


class OnFailuresProcessing(IFailuresPreprocessor):
    def PreprocessFailures(self, args):
        failuresAccessor = args.GetFailuresAccessor()
        messages = failuresAccessor.GetFailureMessages()
        if (0 == messages.Count):
            failuresAccessor.SetProcessingResult(FailureProcessingResult.Continue)
            return
        for msgAccessor in messages:
            fas = msgAccessor.GetSeverity()
            if (fas == FailureSeverity.Warning):
                if (fas.GetDefaultResolutionCaption() == "Remove Constraints"):
                    if (fas.IsFailureResolutionPermitted(msgAccessor, FailureResolutionType.UnlockConstraints)):
                        msgAccessor.SetCurrentResolutionType(FailureResolutionType.UnlockConstraints)
                        fas.ResolveFailure(msgAccessor)
                    else:
                        msgAccessor.SetCurrentResolutionType(FailureResolutionType.DeleteElements)
                        fas.ResolveFailure(msgAccessor)
                failuresAccessor.DeleteWarning(msgAccessor)
                failuresAccessor.SetProcessingResult(FailureProcessingResult.Continue)
        failuresAccessor.SetProcessingResult(FailureProcessingResult.ProceedWithCommit)
        return


doc.Application.FailuresProcessing += EventHandler[FailuresProcessingEventArgs](OnFailuresProcessing)


########################################################################################################################
def ungroup_all_elements(doc):
    with Transaction(doc, "Ungroup elements") as trans:
        trans.Start()
        count = int(0)
        collector = FilteredElementCollector(doc).OfClass(GroupType)
        for group_type in collector.OfCategory(BuiltInCategory.OST_IOSModelGroups):
            if isinstance(group_type, GroupType):
                count += len([group.UngroupMembers() for group in group_type.Groups])
        trans.Commit()
    message = "\nUngroup {} elements".format(count)
    return message


PURGE_GUID = "e8c63650-70b7-435a-9010-ec97660c1bda"
rule_id_list = List[PerformanceAdviserRuleId]()
for rule_id in PerformanceAdviser.GetPerformanceAdviser().GetAllRuleIds():
    if str(rule_id.Guid) == PURGE_GUID:
        rule_id_list.Add(rule_id)
        break


def purge_elements(doc):
    deleteIds = List[ElementId]()
    failure_messages = PerformanceAdviser.GetPerformanceAdviser().ExecuteRules(doc, rule_id_list)
    if failure_messages.Count: [deleteIds.AddRange(fls.GetFailingElements()) for fls in failure_messages]
    deleteIds.AddRange(FilteredElementCollector(doc).OfClass(ImportInstance).ToElementIds())
    if deleteIds is None: return
    if deleteIds and len(deleteIds):
        with Transaction(doc, "Purge elements") as trans:
            trans.Start()
            for idx, elementId in enumerate(deleteIds):
                try:
                    doc.Delete(deleteIds)
                except:
                    pass
            message = "\nCleared of unused {} elements".format(idx)
            trans.Commit()
        return message


def determine_folder_structure(export_name_directory):
    project_directory = os.path.dirname(os.path.dirname(revit_file_path))
    export_directory = os.path.join(project_directory, export_name_directory)
    if not os.path.exists(export_directory): os.makedirs(export_directory)
    return export_directory


def saveAsRevitOutFile(doc, originalRevitFilePath, saveFolderPath):
    revitFileName = Path.GetFileName(originalRevitFilePath)
    saveRevitFilePath = Path.Combine(saveFolderPath, revitFileName)
    if doc.IsWorkshared:
        saveRevitModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(saveRevitFilePath)
        revit_file_util.SaveAsNewCentral(doc, saveRevitModelPath, True)
        revit_file_util.RelinquishAll(doc)
    else:
        revit_file_util.SaveAs(doc, saveRevitFilePath, True)
    return saveRevitFilePath


def saveRevitFile(doc, originalRevitFilePath, saveFolderPath):
    revitFileName = Path.GetFileName(originalRevitFilePath)
    saveRevitFilePath = Path.Combine(saveFolderPath, revitFileName)
    if doc.IsWorkshared:
        revit_file_util.Save(doc)
        revit_file_util.RelinquishAll(doc)
    return saveRevitFilePath


########################################################################################################################
revit_file_name = Path.GetFileNameWithoutExtension(revit_file_path)
########################################################################################################################
Output("\n\n\n Start Export to BIM script ... \n\n\n")
########################################################################################################################
Output(ungroup_all_elements(doc))
Output("\nStart purge elements...")
message = purge_elements(doc)
if message: Output("\t{}".format(message))
message = purge_elements(doc)
if message: Output("\t{}".format(message))
message = purge_elements(doc)
if message: Output("\t{}".format(message))
########################################################################################################################
Output("\nStart set floor number...")
message = set_floor_number(doc)
if message: Output("\t{}".format(message))
########################################################################################################################
Output("\nStart cleaning parameters...")
message = cleaning_parameters(doc)
if message: Output("\t{}".format(message))
########################################################################################################################
Output("\nStart set navisworks view...")
view3D = set_navisworks_view(doc)
if view3D: Output("\t{} completed!".format(view3D.Name))
########################################################################################################################
export_directory = determine_folder_structure("07_BIM")
export_file_path = saveAsRevitOutFile(doc, revit_file_path, export_directory)
Output("\nExport directory path: {}".format(export_file_path))
########################################################################################################################
Output("\n\n\n ... Export to BIM script completed \n\n\n")
########################################################################################################################
