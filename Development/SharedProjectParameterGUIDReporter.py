#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
reload(sys)
import difflib
import clr
import os

clr.AddReference("System")
# clr.AddReference("System.Windows.Forms")

import System
from System import *
from System.Collections.Generic import *

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.DB import StorageType, SharedParameterElement, ExternalDefinition, InternalDefinition
from Autodesk.Revit.DB import ParameterType, BuiltInParameterGroup, BuiltInCategory

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
    guids = None
    bindings = doc.ParameterBindings
    iterator = bindings.ForwardIterator()
    while iterator.MoveNext():
        if doc.GetElement(iterator.Key.Id).ToString() == "Autodesk.Revit.DB.SharedParameterElement":
            definition = iterator.Key
            if definition.IsValidObject and parameter_name == definition.Name:
                shared_parameter = doc.GetElement(definition.Id)
                guids = shared_parameter.GuidValue

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


class ProjectParameterData(object):
    def __init__(self):
        self.Definition = None
        self.Binding = None
        self.Name = None  # Needed because accessing the Definition later may produce an error.
        self.IsSharedStatusKnown = False  # Will probably always be true when the data is gathered
        self.IsShared = False
        self.GUID = None


########################################################################################################################
if os.path.exists(IN[0]): app.SharedParametersFilename = os.path.realpath(IN[0])
########################################################################################################################

result = get_guids_by_parameter_name("BI_тип_помещения")

# output = []
# binding_map = doc.ParameterBindings
# iterator = binding_map.ForwardIterator()
# iterator.Reset()
# while iterator.MoveNext():
#     ppd = ProjectParameterData()
#     if isinstance(iterator.Key, InternalDefinition):
#         ppd.definition = iterator.Key
#         prm_name = ppd.definition.Name
#         prm_guid = ppd.definition.GUID
#         prm_type = ppd.definition.ParameterType
#         prm_group = ppd.definition.ParameterGroup
#         output.append(prm_name)
#         if ppd.definition.IsValidObject:
#             for cat in iterator.Current.Categories:
#                 bic = System.Enum.ToObject(BuiltInCategory, cat.Id.IntegerValue)
#                 output.append(bic)


spfile = app.OpenSharedParameterFile()
gr = spfile.Groups
defp = [g.Definitions for g in gr]
defflat = [x for l in defp for x in l]
defflatname = [x.Name for x in defflat]

# parameter = doc.GetElement(infinition.Id)
# if isinstance(parameter, SharedParameterElement):
#     internal_name = infinition.Name
#     internal_guid = parameter.GuidValue
#     internal_binding = binding_map.Item[infinition]
#
# for group in spfile.Groups:
#     for definition in group.Definitions:
#         name, guid = definition.Name, definition.GUID
#         mach_name = bool(True if name == internal_name else False)
#         mach_guid = bool(True if guid == internal_guid else False)
#         if mach_name and mach_guid: continue
#         TransactionManager.Instance.EnsureInTransaction(doc)
#         binding_map.Insert(definition, internal_binding)
#         try:
#             doc.Delete(parameter.Id)
#         except Exception as error:
#             output.append("Warning: parameter name {} error {}".format(name, str(error)))
#             doc.Regenerate()
#         TransactionManager.Instance.TransactionTaskDone()

########################################################################################################################

# family_files = all_family_pahts_in_library()
# family_names = [os.path.basename(os.path.abspath(flp)) for flp in family_files]

########################################################################################################################
# parameters = get_shared_parameters_in_schedules()
OUT = result, spfile, defflat, defflatname
########################################################################################################################
