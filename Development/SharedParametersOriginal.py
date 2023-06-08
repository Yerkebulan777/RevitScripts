#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import difflib
import clr
import os

clr.AddReference("System")
import System
from System.Collections.Generic import *

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.DB import StorageType, SharedParameterElement
from Autodesk.Revit.DB import ExternalDefinitionCreationOptions
from Autodesk.Revit.DB import ParameterType, BuiltInParameterGroup

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
    bindingsMap = doc.ParameterBindings
    iterator = bindingsMap.ForwardIterator()
    while iterator.MoveNext():
        if doc.GetElement(iterator.Key.Id).ToString() == "Autodesk.Revit.DB.SharedParameterElement":
            definition = iterator.Key
            if definition.IsValidObject and parameter_name == definition.Name:
                shared_parameter = doc.GetElement(definition.Id)
                guids.append(shared_parameter.GuidValue)

    return guids


def tolist(obj1):
    if hasattr(obj1, "__iter__"):
        return obj1
    else:
        return [obj1]


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


def ParamBindingExists(_doc, _param_name, _param_type):
    map = doc.ParameterBindings
    iterator = map.ForwardIterator()
    iterator.Reset()
    while iterator.MoveNext():
        if iterator.Key != None and iterator.Key.Name == _param_name and iterator.Key.ParameterType == _param_type:
            paramExists = True
            return paramExists


def RemoveParamBinding(_doc, _param_name, _param_type):
    map = doc.ParameterBindings
    iterator = map.ForwardIterator()
    iterator.Reset()
    while iterator.MoveNext():
        if iterator.Key != None and iterator.Key.Name == _param_name and iterator.Key.ParameterType == _param_type:
            definition = iterator.Key
            map.Remove(definition)
            message = "Success"
            return message


def add_sparameter(doc, _param_name, _param_type, _group_name, _category, _param_group, _instance=True, _visible=True):
    message = None
    defile = app.OpenSharedParameterFile()
    if ParamBindingExists(doc, _param_name, _param_type):
        if not RemoveParamBinding(doc, _param_name, _param_type) == "Success":
            message = "Param Binding Not Removed Successfully"
            return message
    group = defile.Groups.get_Item(_group_name)
    if group == None: group = defile.Groups.Create(_group_name)
    if group.Definitions.Contains(group.Definitions.Item[_param_name]):
        _def = group.Definitions.Item[_param_name]
    else:
        _def = group.Definitions.Create(_param_name, _param_type, _visible)
    cats = app.Create.NewCategorySet()
    builtInCategory = System.Enum.ToObject(BuiltInCategory, _category.Id)
    cats.Insert(doc.Settings.Categories.get_Item(builtInCategory))
    if _instance:
        bind = app.Create.NewInstanceBinding(cats)
    else:
        bind = app.Create.NewTypeBinding(cats)

    param = doc.ParameterBindings.Insert(_def, bind, _param_group)
    return message


def get_parameter_type(value):
    tolerance, result = 0, None
    for pdt in System.Enum.GetValues(ParameterType):
        matcher = round(difflib.SequenceMatcher(None, pdt.ToString(), value).ratio(), 3)
        if tolerance < matcher:
            tolerance = matcher
            result = pdt

    return result


########################################################################################################################

groups = Dictionary[str, str]()
guids, names, datatypes, categories, groupnames = [], [], [], [], []
if os.path.exists(IN[0]):
    sp_path = os.path.realpath(IN[0])
    app.SharedParametersFilename = sp_path
    # with codecs.open(sp_path, 'r') as inf:
    #     for workset_name in inf.readlines():
    #         workset_name = re.split(r'\t', workset_name)
    #         if workset_name[0] == "GROUP": groups.Add(workset_name[1], workset_name[2])
    #         if workset_name[0] == "PARAM":
    #             guids.append(workset_name[1])
    #             names.append(workset_name[2])
    #             datatypes.append(workset_name[3])
    #             categories.append(workset_name[4])
    #             groupnames.append(dict(groups)[workset_name[5]])

########################################################################################################################
parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
# TransactionManager.Instance.EnsureInTransaction(doc)
# parameters = [doc.Delete(sprm.Id) for sprm in parameters]
# TransactionManager.Instance.TransactionTaskDone()
########################################################################################################################


outputs = []
result = None
binding_map = doc.ParameterBindings
iterator = binding_map.ForwardIterator()
spfile = app.OpenSharedParameterFile()
mygroups = spfile.Groups
iterator.Reset()
while iterator.MoveNext():
    definition = iterator.Key
    sbname = definition.Name
    binding = binding_map.Item[definition]
    shared_parameter = doc.GetElement(definition.Id)
    if isinstance(shared_parameter, SharedParameterElement):
        pgGroup = definition.ParameterGroup
        for guid, spname, dtname, groupname in zip(guids, names, datatypes, groupnames):
            if sbname == spname and shared_parameter.GuidValue != guid:
                pdtype = get_parameter_type(dtname.lower())
                TransactionManager.Instance.EnsureInTransaction(doc)
                group = spfile.Groups.get_Item(groupname)
                if group is None: group = spfile.Groups.Create(groupname)
                if group.Definitions.Contains(group.Definitions.Item[spname]):
                    defin = group.Definitions.Item[spname]
                else:
                    opt = ExternalDefinitionCreationOptions(spname, pdtype)
                    defin = group.Definitions.Create(opt)
                result = doc.ParameterBindings.Insert(defin, binding)
                binding_map.Remove(definition)
                TransactionManager.Instance.TransactionTaskDone()
                outputs.append(result)

newgroup = System.Enum.Parse(BuiltInParameterGroup, 'PG_GENERAL')
for prm in parameters:
    if prm.Name in ["Right Sidesplash Edge workset_name", "Left Sidesplash Edge workset_name"]:
        prm.ParameterGroup = newgroup

########################################################################################################################
OUT = outputs, newgroup
########################################################################################################################
