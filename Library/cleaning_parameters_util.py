# -*- coding: utf-8 -*-
# !/usr/bin/python
import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import os
import clr
import difflib
import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import ParameterElement
from Autodesk.Revit.DB import SharedParameterElement
from Autodesk.Revit.DB import ViewSchedule, Family
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.DB import InstanceBinding, TypeBinding
from Autodesk.Revit.DB import TransactionGroup, Transaction
from Autodesk.Revit.DB import ExternalDefinition, InternalDefinition
from Autodesk.Revit.DB import BuiltInCategory, ViewSheet, View, ScheduleSheetInstance
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity
from Autodesk.Revit.DB import FailureResolutionType
from Autodesk.Revit.DB import IFamilyLoadOptions
from Autodesk.Revit.DB import FamilySource


########################################################################################################################
class warning_dismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        for failure in failuresAccessor.GetFailureMessages():
            # fId = failure.GetFailureDefinitionId
            # if fId == BuiltInFailures.GroupFailures.AtomViolationWhenOnePlaceInstance:
            #     failuresAccessor.DeleteWarning(failure)
            fas = failure.GetSeverity()
            if (fas == FailureSeverity.Warning):
                if (fas.GetDefaultResolutionCaption() == "Remove Constraints"):
                    if (fas.IsFailureResolutionPermitted(failure, FailureResolutionType.UnlockConstraints)):
                        failure.SetCurrentResolutionType(FailureResolutionType.UnlockConstraints)
                        fas.ResolveFailure(failure)
                    else:
                        failure.SetCurrentResolutionType(FailureResolutionType.DeleteElements)
                        fas.ResolveFailure(failure)
                failuresAccessor.DeleteWarning(failure)
                return FailureProcessingResult.Continue
        return FailureProcessingResult.ProceedWithCommit


class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source = FamilySource.Family
        overwriteParameterValues = False
        return True


def load_shared_parameter_file(doc, filepath):
    if os.path.exists(filepath):
        doc.Application.SharedParametersFilename = filepath
        filepath = doc.Application.SharedParametersFilename
        return filepath


def get_external_by_definition(doc, definition):
    parameter = doc.GetElement(definition.Id)
    defile = doc.Application.OpenSharedParameterFile()
    if isinstance(parameter, SharedParameterElement):
        for group in defile.Groups:
            external = group.Definitions.Item[parameter.Name]
            if external and parameter.GuidValue == external.GUID:
                return external


def get_placed_viewIds(doc):
    placedIdList = set()
    collector = FilteredElementCollector(doc).OfClass(ViewSheet)
    for sheet in collector.OfCategory(BuiltInCategory.OST_Sheets).ToElements():
        placedIds = sheet.GetAllPlacedViews()
        if len(placedIds):
            placedIdList.update(placedIds)
            placedIdList.add(sheet.Id)
    return placedIdList


def deleted_unused_views(doc):
    viewIds = [view.Id for view in FilteredElementCollector(doc).OfClass(View) if view.IsTemplate != True]
    viewIds.extend(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Sheets).ToElementIds())
    viewIds.extend(FilteredElementCollector(doc).OfClass(ScheduleSheetInstance).ToElementIds())
    viewIds = set(viewIds).difference(get_placed_viewIds(doc))
    with Transaction(doc, "Delete unused schedules") as trans:
        trans.Start()
        for idx, vid in enumerate(viewIds):
            try:
                message = "\nDeleted {} views".format(idx)
                doc.Delete(vid)
            except:
                pass
        trans.Commit()
    return message


def get_schedule_field(doc, schedule, parameter_name):
    definition = schedule.Definition
    for i in range(definition.GetFieldCount()):
        field = definition.GetField(i)
        param = doc.GetElement(field.ParameterId)
        if param and parameter_name == param.Name:
            return field


def get_schedules_by_definition(doc, definition):
    output, parameter_name = set(), definition.Name
    for schedule in FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements():
        if get_schedule_field(doc, schedule, parameter_name): output.add(schedule)
    return output


def reset_shared_family_parameter(doc, parameter_name, external, category_set, parameter_group):
    for family in FilteredElementCollector(doc).OfClass(Family).ToElements():
        if family.IsValidObject and family.IsEditable:
            if category_set.Contains(family.FamilyCategory):
                with doc.EditFamily(family) as family_doc:
                    manager = family_doc.FamilyManager
                    param = manager.get_Parameter(parameter_name)
                    if (param and not external.Equals(param.Definition)):
                        with Transaction(family_doc) as trans:
                            trans.Start()
                            manager.ReplaceParameter(param, external, parameter_group, param.IsInstance)
                            trans.Commit()
                    family_doc.LoadFamily(doc, FamilyOption())
                    family_doc.Close(False)
                    yield family


def remove_parameter(doc, definition, parameter_name):
    with Transaction(doc, "Remove Parameter") as trans:
        if definition.IsValidObject:
            trans.Start()
            message = "\n\t{}: deleted successfully".format(parameter_name)
            if not doc.ParameterBindings.Remove(definition):
                if definition and definition.IsValidObject:
                    parameter = doc.GetElement(definition.Id)
                    doc.Delete(parameter.Id)
            trans.Commit()
            return message
    return "Invalid definition {}".format(parameter_name)


def get_similar_external_definition(doc, parameter_name):
    definition, filepath, tolerance = None, None, 0.75
    if parameter_name.startswith("BI"): filepath = r"D:\YandexDisk\RevitExportConfig\DataBase\BI_FOP.txt"
    if parameter_name.startswith("TMS"): filepath = r"D:\YandexDisk\RevitExportConfig\DataBase\TMS_FOP.txt"
    if filepath and load_shared_parameter_file(doc, filepath):
        spf = doc.Application.OpenSharedParameterFile()
        for dfn in (dfn for group in spf.Groups for dfn in group.Definitions):
            weight = difflib.SequenceMatcher(None, parameter_name, dfn.Name).ratio()
            if (weight > tolerance):
                tolerance = weight
                definition = dfn
    return definition


def reinsert_shared_parameter(doc, definition, category_set, parameter_group, is_instance=True):
    binding_cats = doc.Application.Create.NewInstanceBinding(category_set)
    if not is_instance: binding_cats = doc.Application.Create.NewTypeBinding(category_set)
    with Transaction(doc, "Reinsert Parameter") as trans:
        parameter_name = definition.Name
        map = doc.ParameterBindings
        try:
            trans.Start()
            fail_options = trans.GetFailureHandlingOptions()
            fail_options.SetFailuresPreprocessor(warning_dismiss())
            trans.SetFailureHandlingOptions(fail_options)
            if map.Contains(definition):
                if map.ReInsert(definition, binding_cats, parameter_group):
                    message = "\n\t{}: successfully reinsert".format(parameter_name)
            if not map.Contains(definition):
                if map.Insert(definition, binding_cats, parameter_group):
                    message = "\n\t{}: successfully insert".format(parameter_name)
            trans.Commit()
        except Exception as e:
            message = "\n\t{}: failed to bind {}".format(parameter_name, e)
            trans.RollBack()
    return message


########################################################################################################################
def cleaning_parameters(doc):
    iterator = doc.ParameterBindings.ForwardIterator()
    with TransactionGroup(doc, "Cleaning parameters") as transGroup:
        iterator.Reset()
        transGroup.Start()
        message = deleted_unused_views(doc)
        while iterator.MoveNext():
            if not iterator.IsReadOnly:
                try:
                    definition = iterator.Key
                except:
                    continue
                if definition.IsValidObject:
                    if isinstance(definition, InternalDefinition):
                        binding, prm_name = iterator.Current, definition.Name
                        schedules = get_schedules_by_definition(doc, definition)
                        external = get_similar_external_definition(doc, prm_name)
                        if external and isinstance(external, ExternalDefinition):
                            flag = bool(len(schedules))
                            cat_set = binding.Categories
                            prm_group = definition.ParameterGroup
                            parameter = doc.GetElement(definition.Id)
                            if isinstance(binding, TypeBinding): instance = False
                            if isinstance(binding, InstanceBinding): instance = True
                            if flag: message += "\nParameter used in schedule: ".join(sch.Name for sch in schedules)
                            families = reset_shared_family_parameter(doc, prm_name, external, cat_set, prm_group)
                            messageList = ["\nReset parameter in: ".format(fam.Name) for fam in families if fam]
                            message += reinsert_shared_parameter(doc, external, cat_set, prm_group, instance)
                            message = (message.join(messageList) if len(messageList) else message)
                            if isinstance(parameter, ParameterElement):
                                if not flag: message += remove_parameter(doc, definition, prm_name)
                            if isinstance(parameter, SharedParameterElement):
                                if parameter.GuidValue != external.GUID:
                                    message += remove_parameter(doc, definition, prm_name)
        transGroup.Assimilate()
    return message
########################################################################################################################
