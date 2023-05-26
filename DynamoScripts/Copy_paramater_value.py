#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import difflib
import clr

clr.AddReference("System")
from System.Collections.Generic import *

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.DB import StorageType, SharedParameterElement
from Autodesk.Revit.DB import InstanceBinding, TypeBinding

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


def tolist(obj1):
    if hasattr(obj1, "__iter__"):
        return obj1
    else:
        return [obj1]


def transaction(action):
    def wrapped(*args, **kwargs):
        TransactionManager.Instance.EnsureInTransaction(doc)
        result = action(*args, **kwargs)
        TransactionManager.Instance.TransactionTaskDone()
        return result

    return wrapped


@transaction
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


@transaction
def set_value_by_guid(guid, element, value):
    param, result = None, None
    if element.IsValidObject: param = element.get_Parameter(guid)
    if bool(param):
        if param.StorageType == StorageType.String:
            if isinstance(value, str):
                result = param.Set(value)
            else:
                result = param.Set(str(value))
        elif param.StorageType == StorageType.Double:
            if isinstance(value, float):
                result = param.Set(value)
            else:
                result = param.Set(int(float(value)))
        elif param.StorageType == StorageType.Integer:
            if isinstance(value, int):
                result = param.Set(value)
            else:
                result = param.Set(int(value))
        return result


def reinsert_shared_parameter(parameter_name, category_set):
    binding_map = doc.ParameterBindings
    iterator = binding_map.ForwardIterator()
    spfile = app.OpenSharedParameterFile()
    iterator.Reset()
    result = None
    while iterator.MoveNext():
        definition = iterator.Key
        element_bind = iterator.Current
        if definition.IsValidObject:
            sip_name = definition.Name
            sip_type = definition.ParameterType
            sip_group = definition.ParameterGroup
            binding = binding_map.Item[definition]
            shared_parameter = doc.GetElement(definition.Id)
            if isinstance(shared_parameter, SharedParameterElement) and sip_name == parameter_name:
                if isinstance(element_bind, InstanceBinding):
                    bind = doc.Application.Create.NewInstanceBinding(category_set)
                if isinstance(element_bind, TypeBinding):
                    bind = app.Create.NewTypeBinding(category_set)
                group = spfile.Groups.get_Item(sip_group.ToString())
                if group is None: group = spfile.Groups.Create(sip_group.ToString())
                if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
                    # setCat = doc.ParameterBindings.ReInsert(definition, instanceBinding, sip_group)
                    # binding_map.Remove(definition)
                    definition = group.Definitions.Item[parameter_name]
                    # TransactionManager.Instance.EnsureInTransaction(doc)
                    # TransactionManager.Instance.TransactionTaskDone()
                    result = dir(definition)
                    result.append(sip_group)
                    result.append(sip_type)
                    result.append(binding)

    return result


def get_guid_by_parameter_name(parameter_names):
    tolerance, result = 0, None
    spf = app.OpenSharedParameterFile()
    shared_params = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
    for sp_name in tolist(parameter_names):
        definition = [dfn for group in spf.Groups for dfn in group.Definitions if spf and dfn.Name == sp_name][0]
        for sparam in shared_params:
            guid_value = sparam.GuidValue
            if definition and guid_value == definition.GUID: return guid_value
            matcher = difflib.SequenceMatcher(None, sparam.Name, sp_name).ratio()
            if tolerance < matcher:
                tolerance = matcher
                result = guid_value

    return result


def get_parameter_value(element, parameter_name):
    value = None
    for param in element.GetParameters(parameter_name):
        if "Double" in str(param.StorageType):
            value = (param.AsDouble() * 304.8)
        elif "Integer" in str(param.StorageType):
            value = (param.AsInteger())
        elif "String" in str(param.StorageType):
            value = (param.AsString())
        else:
            elemId = param.AsElementId()
            value = (doc.GetElement(elemId))

    return value


########################################################################################################################
target_parameter_name, source_parameter_name, elements = IN[1], IN[2], IN[0]
########################################################################################################################

output = []
guid = get_guid_by_parameter_name(target_parameter_name)
for element in elements:
    element = UnwrapElement(element)
    val = get_parameter_value(element, source_parameter_name)
    if val: output.append(set_value_by_guid(guid, element, val))

########################################################################################################################
OUT = guid, output
########################################################################################################################
