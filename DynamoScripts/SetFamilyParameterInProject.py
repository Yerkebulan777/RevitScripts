#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')

import difflib
import clr
import os

import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource, Family
from Autodesk.Revit.DB import TransactionGroup, Transaction
from Autodesk.Revit.DB import FailureResolutionType, BuiltInFailures, SaveAsOptions
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity
from Autodesk.Revit.DB import FilteredElementCollector, SharedParameterElement

# clr.AddReference('RevitAPIIFC')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName


########################################################################################################################
def Output(output):
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return


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
    app = doc.Application
    defile = app.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def check_parameter(doc, definition, isInstance):
    map = doc.ParameterBindings
    iterator = map.ForwardIterator()
    parameter_name = definition.Name
    parameter_type = definition.ParameterType
    message = "CheckParameter {0}".format(parameter_name)
    external = get_external_definition(doc, parameter_name)
    guid = (external.GUID if external else None)
    with Transaction(doc, message) as trans:
        trans.Start()
        iterator.Reset()
        if not guid: return
        while iterator.MoveNext():
            binding = None
            definition = iterator.Key
            parameter = doc.GetElement(definition.Id)
            if isinstance(parameter, SharedParameterElement):
                definition_name = definition.Name
                if parameter.GuidValue == guid:
                    flagBolean = (True if definition_name != parameter_name else False)
                    flagBolean = (True if definition.ParameterType != parameter_type else flagBolean)
                    if flagBolean and doc.Delete(parameter.Id):
                        parameter_group = definition.ParameterGroup
                        categories = map.Item[definition].Categories
                        if (isInstance): binding = doc.Application.Create.NewInstanceBinding(categories)
                        if not (isInstance): binding = doc.Application.Create.NewTypeBinding(categories)
                        doc.ParameterBindings.Insert(external, binding, parameter_group)
                        Output("Reset parameter: {}".format(definition_name))
                elif parameter.GuidValue != guid:
                    prm_name, def_name = parameter_name.lower(), definition_name.lower()
                    weight = difflib.SequenceMatcher(None, prm_name, def_name).ratio()
                    if (weight > 0.85): doc.Delete(parameter.Id)
        trans.Commit()
    parameter = SharedParameterElement.Lookup(doc, external.GUID)
    return parameter


def get_families_by_shared_parameter(doc, parameter):
    result, bindings = set(), doc.ParameterBindings.Item[parameter.GetDefinition()]
    categoryIds = [cat.Id.IntegerValue for cat in bindings.Categories]
    for family in FilteredElementCollector(doc).OfClass(Family).ToElements():
        if family.FamilyCategory.Id.IntegerValue in categoryIds:
            result.add(family)
    return result


def reset_family_parameter(path, definition, prm_guid, prm_group, isInstance=True):
    doc = app.OpenDocumentFile(path)
    name = "IsTemp{}".format(prm_name)
    params = [prm for prm in doc.FamilyManager.GetParameters() if prm.IsShared and prm_guid == prm.GUID]
    with Transaction(doc, "Reset Parameter {}".format(name)) as trans:
        trans.Start()
        param = (params[0] if len(params) else None)
        if (param and not definition.Equals(param.Definition)):
            if param.IsShared: param = doc.FamilyManager.ReplaceParameter(param, name, prm_group, isInstance)
            param = doc.FamilyManager.ReplaceParameter(param, definition, prm_group, isInstance)
        if (param is None):
            param = doc.FamilyManager.AddParameter(name, prm_group, definition.ParameterType, isInstance)
            param = doc.FamilyManager.ReplaceParameter(param, definition, prm_group, isInstance)
    trans.Commit()
    doc.Dispose()
    return param


########################################################################################################################
########################################################################################################################
result = []
isInstance = bool(IN[1])
options = SaveAsOptions()
options.OverwriteExistingFile = True
temp = os.path.normpath(os.getenv("TEMP"))
definition = UnwrapElement(IN[0]).GetDefinition()
param = check_parameter(doc, definition, isInstance)
prm_name = param.Name
prm_guid = param.GuidValue
prm_group = definition.ParameterGroup
external = get_external_definition(doc, prm_name)
families = get_families_by_shared_parameter(doc, param)
with TransactionGroup(doc, prm_name) as transGroup:
    transGroup.Start()
    for family in families:
        if not external: break
        if family.IsValidObject:
            family_name = family.Name
            if family.Pinned: continue
            if family.IsInPlace: continue
            if not family.IsEditable: continue
            family_doc = doc.EditFamily(family)
            if not family_doc.IsFamilyDocument:
                family_doc.Close(False)
                family_doc.Dispose()
            if family_doc and family_doc.IsFamilyDocument:
                path = os.path.join(temp, family_name + '.rfa')
                try:
                    family_doc.SaveAs(path, options)
                    family_doc.Close(False)
                    family_doc.Dispose()
                    param = reset_family_parameter(path, external, prm_guid, prm_group, isInstance)
                    if param and param.IsShared: result.append("Set {} complete!".format(param.Definition.Name))
                except Exception as e:
                    result.append("Save error: {} ".format(e))
                with Transaction(doc, "Load Family") as trans:
                    try:
                        trans.Start()
                        fail_options = trans.GetFailureHandlingOptions()
                        fail_options.SetFailuresPreprocessor(warning_dismiss())
                        trans.SetFailureHandlingOptions(fail_options)
                        if doc.LoadFamily(path, FamilyOption()):
                            result.append("Load {} complete!\n".format(family_name))
                        trans.Commit()
                    except Exception as e:
                        result.append("Activate error: {} ".format(e))
                        trans.RollBack()
    transGroup.Assimilate()
    doc.Save()

########################################################################################################################
OUT = prm_name, result
########################################################################################################################
