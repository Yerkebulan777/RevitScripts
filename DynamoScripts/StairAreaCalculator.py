#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import difflib
import clr

clr.AddReference("System")
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.DB import InstanceBinding, TypeBinding
from Autodesk.Revit.DB import StorageType, SharedParameterElement
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter
from Autodesk.Revit.DB import ElementId, Transaction, IntersectionResultArray, SetComparisonResult
from Autodesk.Revit.DB import HostObjectUtils, Transform, CurveLoop, Curve, Options, ViewDetailLevel
from Autodesk.Revit.DB import Line, XYZ, FilterNumericEquals, ParameterValueProvider, ElementParameterFilter
from Autodesk.Revit.DB import FilterStringRule, FilterStringContains, SolidCurveIntersectionOptions, FilterDoubleRule
from Autodesk.Revit.DB import ReferenceIntersector, FindReferenceTarget, ElementClassFilter, View3D, Floor
from Autodesk.Revit.DB import WorksetTable, Workset, FilteredWorksetCollector, WorksetId, WorksharingUtils
from Autodesk.Revit.DB.Architecture import Stairs

clr.AddReference("RevitAPIIFC")
from Autodesk.Revit.DB.IFC import ExporterIFCUtils

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import Selection

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


class CustomISelectionFilter(Selection.ISelectionFilter):
    def __init__(self, element_class):
        self.element_class = element_class

    def AllowElement(self, element):
        if isinstance(element, self.element_class):
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return True


########################################################################################################################
info = ""
selections = uidoc.Selection.PickObjects(Selection.ObjectType.Element.Element, CustomISelectionFilter(Stairs), "Select")
# Selection.Selection.GetElementIds()
for select in selections:
    stairs = doc.GetElement(select)
    landingIds = stairs.GetStairsLandings()
    stairsType = doc.GetElement(stairs.GetTypeId())
    info = "\nType:  {}".format(stairsType.GetType())
    info += "\nNumber of stories:(этажность)\t{}".format(stairs.NumberOfStories)
    info += "\nNumber of landings(колличество площадок):\t".format(landingIds.Count)
    info += "\nHeight of stairs(высота лестницы):\t{}".format(stairs.Height * 304.8)
    info += "\nNumber of treads(колличество ступеней):\t{}".format(stairs.ActualTreadsNumber)
    info += "\nNumber of riser(колличество подступенок):\t{}".format(stairs.ActualRisersNumber)
    info += "\nRiser Height:(высота подступенка):\t{}".format(stairsType.MaxRiserHeight * 304.8)
    info += "\nRiser Width:(ширина подступенка)\t{}".format(stairsType.MinRunWidth * 304.8)
    info += "\nTread Width:(глубина ступеней)\t{}".format(stairsType.MinTreadDepth * 304.8)
    for lid in landingIds:
        landing = doc.GetElement(lid)
        loop = CurveLoop()
        loop.Append(landing.GetFootprintBoundary())
        area = ExporterIFCUtils.ComputeAreaOfCurveLoops(List[CurveLoop]([loop]))
        info += "\n+{}".format(area)

########################################################################################################################
OUT = info
########################################################################################################################
