import clr

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

from System.Collections.Generic import *

doc = DocumentManager.Instance.CurrentDBDocument


def tolist(input):
    if not isinstance(input, list):
        return [input]
    else:
        return input


def flatten(x):
    result = []
    for el in tolist(x):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def FilterElementsByWorksetUser(items):
    usworkset == doc.Application.Username
    worksets = [i.get_Parameter(BuiltInParameter.EDITED_BY).AsString() for i in items if i]
    results = [i for i, w in zip(items, worksets) if i and w == "" or i and w == usworkset]
    return results


def FilterElementsInGroup(items):
    collector = FilteredElementCollector(doc)
    groups = collector.OfClass(Group)
    if not groups: return items
    elemsInGroup = flatten([i.GetMemberIds() for i in groups if i])
    items = [i for i in items if i.Id not in elemsInGroup]
    return items


def GetParameter(item, sechname):
    params = item.Parameters
    paramsName = [prm.Definition.Name for prm in params]
    for prmname, prm in sorted(zip(paramsName, params)):
        if prm.Definition.Name.Equals(sechname):
            return prm
        elif prm.Definition.Name.Contains(sechname):
            return prm
        else:
            lowername = prmname.ToLower()
            sechname = sechname.ToLower()
            if lowername == sechname: return prm


def FilterElementsByParameter(items, parameter_name, filter_string_value):
    item = items[0]
    doc = item.Document
    ids = [i.Id for i in items if i]
    icollection = List[ElementId](ids)
    parameter = GetParameter(item, parameter_name)
    FilterRule = FilterStringRule(ParameterValueProvider(parameter.Id), FilterStringContains(), filter_string_value,
                                  False)
    ParameterFilter = ElementParameterFilter(FilterRule)
    items = FilteredElementCollector(doc, icollection).WherePasses(
        ParameterFilter).WhereElementIsNotElementType().ToElements()
    return items


dataEnteringNode = IN
################################################
items = None
items = [UnwrapElement(i) for i in flatten(IN[1]) if i]
items = FilterElementsByWorksetUser(items)
items = FilterElementsInGroup(items)
parameter_name = IN[2]
filter_string_value = IN[3]
################################################

if IN[0] == True and items:
    items = FilterElementsByParameter(items, parameter_name, filter_string_value)
else:
    items = items

OUT = items
