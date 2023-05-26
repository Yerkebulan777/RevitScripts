#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
reload(sys)
import difflib
import glob
import clr
import os

clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
import System

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.DB import StorageType, SharedParameterElement, ExternalDefinition
from Autodesk.Revit.DB import ParameterType, BuiltInParameterGroup, CategoryType
from Autodesk.Revit.DB import Family, IFamilyLoadOptions, ViewSchedule

# from Autodesk.Revit.DB import ExternalDefinitionCreationOptions

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.GeometryReferences)

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


def get_guids_by_parameter_name(parameter_name):
    guids = []
    bindings = doc.ParameterBindings
    iterator = bindings.ForwardIterator()
    while iterator.MoveNext():
        if doc.GetElement(iterator.Key.Id).ToString() == "Autodesk.Revit.DB.SharedParameterElement":
            definition = iterator.Key
            if definition.IsValidObject and parameter_name == definition.Name:
                shared_parameter = doc.GetElement(definition.Id)
                guids.append(shared_parameter.GuidValue)
    return guids


def get_guid_by_parameter_name(parameter_names):
    tolerance, result = 0, None
    spf = app.OpenSharedParameterFile()
    shared_params = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
    if not isinstance(parameter_names, list): parameter_names = [parameter_names]
    for sp_name in parameter_names:
        definition = [dfn for group in spf.Groups for dfn in group.Definitions if spf and dfn.Name == sp_name][0]
        for sparam in shared_params:
            guid_value = sparam.GuidValue
            if definition and guid_value == definition.GUID: return guid_value
            matcher = difflib.SequenceMatcher(None, sparam.Name, sp_name).ratio()
            if tolerance < matcher:
                tolerance = matcher
                result = guid_value
    return result


def get_value_by_guid(guid, element):
    param, value = None, None
    if element.IsValidObject: param = element.get_Parameter(guid)
    if bool(param):
        if param.StorageType == StorageType.String:
            value = param.AsString()
        elif param.StorageType == StorageType.Double:
            value = param.AsDouble()
        elif param.StorageType == StorageType.Integer:
            value = param.AsInteger()
        return value


def get_parameter_type(value):
    tolerance, result = 0, None
    for pdt in System.Enum.GetValues(ParameterType):
        matcher = round(difflib.SequenceMatcher(None, pdt.ToString(), value).ratio(), 3)
        if tolerance < matcher:
            tolerance = matcher
            result = pdt

    return result


def get_field(schedule, name):
    field = None
    definition = schedule.Definition
    count = definition.GetFieldCount()
    for i in range(0, count, 1):
        if definition.GetField(i).GetName() == name:
            field = definition.GetField(i)
    return field


def get_shared_parameters_in_schedules():
    results, sids = set(), set()
    for schedule in FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements():
        for field in schedule.Definition.GetSchedulableFields():
            if (field.ParameterId.IntegerValue > 0):
                parameter = doc.GetElement(field.ParameterId)
                if isinstance(parameter, SharedParameterElement):
                    if get_field(schedule, parameter.Name):
                        if parameter.Id not in sids:
                            results.add(parameter.Name)
                            sids.add(parameter.Id)
    return results


def get_families(source=r"K:\\"):
    families = []
    drive = os.path.realpath(os.path.abspath(source))
    include_folders = ["AR", "AS", "KJ", "KR", "KG", "OV", "VK", "EOM", "PS", "SS"]
    directory = [os.path.join(drive, entry) for entry in os.listdir(drive) if entry.endswith('Библиотека')][0]
    roots = [os.path.normpath(os.path.join(directory, fld)) for fld in os.listdir(directory) if fld in include_folders]
    for root in roots:
        families.extend(glob.iglob(os.path.join(root, '*.rfa')))
        families.extend(glob.iglob(os.path.join(root, '*', '*.rfa')))
        families.extend(glob.iglob(os.path.join(root, '*', '*', '*.rfa')))

    return families


class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        return True


def add_parameter_to_family(family_doc, external_parameter, group='INVALID', instance=True):
    """ 'PG_GEOMETRY' 'PG_GENERAL' 'INVALID' """
    bpg = System.Enum.Parse(BuiltInParameterGroup, group)
    param = family_doc.FamilyManager.get_Parameter(external_parameter.Name)
    if param and param.IsShared and param.GUID == external_parameter.GUID:
        return
    elif param:
        family_doc.RemoveParameter(param)
    return doc.FamilyManager.AddParameter(external_parameter, bpg, instance)


########################################################################################################################
if os.path.exists(IN[0]): app.SharedParametersFilename = os.path.realpath(IN[0])
########################################################################################################################

output = []
binding_map = doc.ParameterBindings
spfile = app.OpenSharedParameterFile()
iterator = binding_map.ForwardIterator()
iterator.Reset()
while iterator.MoveNext():
    if isinstance(iterator.Key, ExternalDefinition): continue
    infinition = iterator.Key
    parameter = doc.GetElement(infinition.Id)
    if isinstance(parameter, SharedParameterElement):
        internal_name = infinition.Name
        internal_guid = parameter.GuidValue
        internal_binding = binding_map.Item[infinition]
        for group in spfile.Groups:
            for definition in group.Definitions:
                name, guid = definition.Name, definition.GUID
                mach_name = bool(True if name == internal_name else False)
                mach_guid = bool(True if guid == internal_guid else False)
                if mach_name and mach_guid: continue
                TransactionManager.Instance.EnsureInTransaction(doc)
                binding_map.Insert(definition, internal_binding)
                doc.Delete(parameter.Id)
                doc.Regenerate()
                TransactionManager.Instance.TransactionTaskDone()

########################################################################################################################

# family_files = all_family_pahts_in_library()
# family_names = [os.path.basename(os.path.abspath(flp)) for flp in family_files]
directory = os.path.normpath(os.path.dirname(os.path.abspath(doc.PathName)))
parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
for family in FilteredElementCollector(doc).OfClass(Family).ToElements():
    TransactionManager.Instance.ForceCloseTransaction()
    if family.IsEditable and not family.IsInPlace:
        family_doc = doc.EditFamily(family)
        category = family_doc.OwnerFamily.FamilyCategory
        if category.CategoryType.Equals(CategoryType.Model):
            add_parameter_to_family(family_doc, parameter)
            family_doc.LoadFamily(doc, FamilyOption())
            output.append(family.Name)
            family_doc.Close(False)

########################################################################################################################
# parameters = get_shared_parameters_in_schedules()
OUT = output
########################################################################################################################
