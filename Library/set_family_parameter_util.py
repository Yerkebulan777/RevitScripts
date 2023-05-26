#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import clr
import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import TransactionGroup, Transaction
from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource, Family
from Autodesk.Revit.DB import FailureResolutionType, BuiltInFailures, BuiltInParameterGroup
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity
from Autodesk.Revit.DB import FilteredElementCollector, SharedParameterElement, ExternalDefinition


########################################################################################################################
class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source = FamilySource.Family
        overwriteParameterValues = False
        return True


class warning_dismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        for failure in failuresAccessor.GetFailureMessages():
            fId = failure.GetFailureDefinitionId
            if fId == BuiltInFailures.GroupFailures.AtomViolationWhenOnePlaceInstance:
                failuresAccessor.DeleteWarning(failure)
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
        return FailureProcessingResult.ProceedWithCommit


########################################################################################################################
def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def get_internal_parameter(doc, parameter_name):
    external = get_external_definition(doc, parameter_name)
    parameter = SharedParameterElement.Lookup(doc, external.GUID)
    return parameter


def get_families_by_definition(doc, definition):
    result, bindings = set(), doc.ParameterBindings.Item[definition]
    categoryIds = [cat.Id.IntegerValue for cat in bindings.Categories]
    for family in FilteredElementCollector(doc).OfClass(Family).ToElements():
        if family.FamilyCategory.Id.IntegerValue in categoryIds:
            result.add(family)
    return result


def set_family_shared_parameters(doc, family, parameter_names, parameter_group, isInstance=True):
    param, family_doc = None, doc.EditFamily(family)
    with Transaction(family_doc) as trans:
        if family_doc.IsFamilyDocument:
            trans.Start()
            manager = family_doc.FamilyManager
            fail_options = trans.GetFailureHandlingOptions()
            fail_options.SetFailuresPreprocessor(warning_dismiss())
            trans.SetFailureHandlingOptions(fail_options)
            for prm_name in parameter_names:
                temp = "Temp{}".format(prm_name)
                param = manager.get_Parameter(prm_name)
                external = get_external_definition(doc, prm_name)
                if isinstance(external, ExternalDefinition):
                    if (param and not external.Equals(param.Definition)):
                        param = manager.ReplaceParameter(param, external, parameter_group, isInstance)
                    if bool(param) == False:
                        param = manager.AddParameter(temp, parameter_group, external.ParameterType, isInstance)
                        param = manager.ReplaceParameter(param, external, parameter_group, isInstance)
            family_doc.LoadFamily(doc, FamilyOption())
            trans.Commit()
    family_doc.Close(False)
    family_doc.Dispose()
    return param


########################################################################################################################
def set_parameters_in_families(doc, families, parameter_names, parameter_group, isInstance):
    """ 'PG_DATA' 'PG_GEOMETRY' 'PG_GENERAL' 'INVALID' """
    group = System.Enum.Parse(BuiltInParameterGroup, parameter_group)
    parameter_names = parameter_names if isinstance(parameter_names, list) else list(parameter_names)
    with TransactionGroup(doc, "Set family parameter") as transGroup:
        message = "\n"
        transGroup.Start()
        for family in families:
            if family.IsValidObject:
                family_name = family.Name
                if bool(family.IsEditable and not family.IsInPlace):
                    param = set_family_shared_parameters(doc, family, parameter_names, group, isInstance)
                    if param: message += "\nSet family parameters in {} complete!".format(family_name)
        transGroup.Assimilate()
    return message
########################################################################################################################
