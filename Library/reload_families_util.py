#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import os
import clr
import glob

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FailureResolutionType, BuiltInFailures, Transaction
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity
from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource
from Autodesk.Revit.DB import FilteredElementCollector, Family
from Autodesk.Revit.DB import SharedParameterElement
from Autodesk.Revit.DB import ExternalDefinitions


########################################################################################################################
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


class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source = FamilySource.Family
        overwriteParameterValues = False
        return True


########################################################################################################################
def get_basename(filepath):
    fullname = os.path.basename(filepath)
    filename, ext = os.path.splitext(fullname)
    return filename


def get_family_names(doc):
    families = FilteredElementCollector(doc).OfClass(Family).ToElements()
    result = [family.Name for family in families if family.IsEditable]
    return result


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def get_family_paths(doc, directory):
    result, filenames = [], []
    family_names = get_family_names(doc)
    section = os.path.basename(os.path.dirname(os.path.dirname(doc.PathName)))
    includes = ["AR", "AS", "KJ", "KR", "KG", "OV", "VK", "EOM", "EM", "EL", "PS", "SS"]
    includes = ["VK"] if bool(section.endswith("VK")) else includes
    includes = ["OV"] if bool(section.endswith("OV")) else includes
    includes = ["EL"] if any([section.endswith("PS"), section.endswith("SS")]) else includes
    includes = ["EL"] if any([section.endswith("EOM"), section.endswith("EM")]) else includes
    includes = ["AR"] if any([section.endswith("AR"), section.endswith("AS")]) else includes
    includes = ["KR"] if any([section.endswith("KJ"), section.endswith("KG"), section.endswith("KR")]) else includes
    for folder in os.listdir(directory):
        if folder in includes:
            root = os.path.abspath(os.path.join(directory, folder))
            filenames.extend(glob.iglob(os.path.join(root, '*.rfa')))
            filenames.extend(glob.iglob(os.path.join(root, '*', '*.rfa')))
            filenames.extend(glob.iglob(os.path.join(root, '*', '*', '*.rfa')))
            result.extend([path for path in filenames if get_basename(path) in family_names])
    return result


def load_family(doc, filepath):
    family_doc = doc.Application.OpenDocumentFile(filepath)
    manager = family_doc.FamilyManager
    for family_param in manager.GetParameters():
        if not family_param.IsShared: continue
        definition = family_param.Definition
        param = SharedParameterElement.Lookup(doc, family_param.GUID)
        if isinstance(param, SharedParameterElement):
            param_name = param.Name
            internal = param.GetDefinition()
            external = get_external_definition(doc, param_name)
            if external and not external.Equals(internal):
                with Transaction(doc, param_name) as trans:
                    trans.Start()
                    doc.Delete(param.Id)
                    trans.Commit()
            if internal and not internal.Equals(definition):
                with Transaction(family_doc, param_name) as trans:
                    trans.Start()
                    if not external: manager.RemoveParameter(family_param)
                    if isinstance(external, ExternalDefinitions):
                        inst_bool = family_param.IsInstance
                        bip_group = definition.ParameterGroup
                        manager.ReplaceParameter(family_param, external, bip_group, inst_bool)
                    trans.Commit()
    family = family_doc.LoadFamily(doc, FamilyOption())
    family_doc.Close(False)
    family_doc.Dispose()
    return family


########################################################################################################################
def reload_families(doc, directory):
    message = ''  # core data processing
    family_paths = get_family_paths(doc, directory)
    for filepath in family_paths:
        family = load_family(doc, filepath)
        if family: message += "\nReloaded: {}".format(family.Name)
        with Transaction(doc, "Activate") as trans:
            try:
                trans.Start()
                for symbolId in family.GetFamilySymbolIds():
                    symbol = doc.GetElement(symbolId)
                    if symbol.IsValidObject:
                        symbol.Activate()
                trans.Commit()
            except:
                trans.RollBack()
    return message
########################################################################################################################
