#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
import math
import random as rnd

import clr

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('System')
import System
from System.Collections.Generic import *

clr.AddReference('RevitNodes')
import Revit

clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument


def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def GetSortedLevels():
    levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    return sorted(levels, key=lambda x: x.Elevation)


def GetLevelAbove(level, tolerance):
    sorted_lvls = GetSortedLevels()
    sorted_nams = [ i.Name for i in sorted_lvls ]
    index = sorted_nams.index(level.Name)
    if index + 1 >= len(sorted_lvls): return level
    result = sorted_lvls[index + 1]
    if result.Elevation - level.Elevation < tolerance:
        return GetLevelAbove(result, tolerance)
    return result


def GetLevelByElevation(value, tolerance):
    seach_val = value // (tolerance/2) * (tolerance/2)
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    filterrule = FilterDoubleRule(provider, FilterNumericEquals(), seach_val, tolerance/3 )
    collector = FilteredElementCollector(DocumentManager.Instance.CurrentDBDocument).OfClass(Level)
    level = collector.WherePasses(ElementParameterFilter(filterrule)).FirstElement()
    if level == None:
        tolerance = tolerance + (300/304.8)
        try: return GetLevelByElevation(value, tolerance)
        except: pass
    return level


def GetCollumns():
    result = []
    for level in GetSortedLevels():
        levelfilter = ElementLevelFilter(level.Id)
        collector = FilteredElementCollector(doc).WherePasses(levelfilter).WhereElementIsNotElementType()
        elements = collector.OfCategory(BuiltInCategory.OST_StructuralColumns).ToElements()
        result.extend(elements)
    return result


def GetWallsByWidht(value, evaluator):
    result = []
    for level in GetSortedLevels():
        level_filter = ElementLevelFilter(level.Id)
        provider = ParameterValueProvider(ElementId(BuiltInParameter.WALL_ATTR_WIDTH_PARAM))
        filterrule = FilterDoubleRule(provider, evaluator, value, 0.0005)
        prm_filter = ElementParameterFilter(filterrule)
        collector = FilteredElementCollector(doc).WherePasses(level_filter).OfClass(Wall)
        elements = collector.WherePasses(prm_filter).WhereElementIsNotElementType().ToElements()
        result.extend(elements)
    return result


def GetElementSolid(item):
    geo_elem = item.get_Geometry(Autodesk.Revit.DB.Options()).GetTransformed(Transform.Identity)
    solids = [ geo for geo in geo_elem if 'Solid' in geo.ToString() and geo.Volume > 0 ]
    util = BooleanOperationsUtils
    type = BooleanOperationsType.Union
    for i, solid in enumerate(solids):
        if i == 0: usolid = solid
        elif i != 0: usolid = util.ExecuteBooleanOperation(usolid, solid[i], type)
    return usolid


def GetCentroid(item):
    solid = GetElementSolid(item)
    centroid = solid.ComputeCentroid()
    return centroid


def GetRayIntersection(point, filter_class, direction):
    collector = FilteredElementCollector(doc).OfClass(View3D)
    actiview = uidoc.ActiveView
    if actiview.Id in collector.ToElementIds(): view = actiview
    else: view = [v for v in collector.ToElements() if v.IsTemplate != True][0]
    filter = ElementClassFilter(filter_class)
    refIntersector = ReferenceIntersector(filter, FindReferenceTarget.All, view)
    refIntersector.FindReferencesInRevitLinks = True
    refwc = refIntersector.Find(point, direction)
    if refwc:
        for ref in sorted(refwc, key=lambda x: x.Proximity):
            reference = ref.GetReference()
            endpoint = reference.GlobalPoint
            if point.DistanceTo(endpoint) >= 600/304.8:
                represent = reference.ConvertToStableRepresentation(doc)
                element = doc.GetElement(represent)
                return endpoint.Z


def SetCorrectCollumnTopLevel(item, recursion):
    tolerance = 1800/304.8
    base_level_prm = item.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
    top_level_prm = item.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
    base_level = doc.GetElement(base_level_prm.AsElementId())
    top_level = doc.GetElement(top_level_prm.AsElementId())
    base_elev = base_level.Elevation
    center = GetCentroid(item)
    point = XYZ(center.X, center.Y, base_elev + (base_elev - center.Z)*0.5)
    height = GetRayIntersection(point, Floor, XYZ(0, 0, 1))
    if not height or height <= base_elev and recursion != True:
        return SetCorrectCollumnTopLevel(item, True)
    elif height and height > base_elev:
        new_top_level = GetLevelByElevation(height, tolerance/3)
        if top_level.Id != new_top_level.Id:
            return top_level_prm.Set(new_top_level.Id)
    else:
        new_top_level = GetLevelAbove(base_level, tolerance)
        if top_level.Id != new_top_level.Id:
            return top_level_prm.Set(new_top_level.Id)


def SetCorrectCollumnTopOffset(item):
    if not item: return
    point = GetCentroid(item)
    height = GetRayIntersection(point, Floor, XYZ(0, 0, 1))
    if not height: return
    top_offset_prm = item.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)
    top_level_prm = item.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
    top_level = doc.GetElement(top_level_prm.AsElementId())
    top_elev = top_level.Elevation
    top_offset = height - top_elev
    return top_offset_prm.Set(top_offset)


def GetAverageValue(values):
    result = [float(i) for i in flatten(values) if i]
    if len(result) == 1: return result[0]
    if len(result) >= 2:
        maxfilter = round(max(result) + sum(result) / len(result) + 0.005, 3) * 0.5
        minfilter = round(min(result) + sum(result) / len(result) - 0.005, 3) * 0.5
        result = [i for i in result if i <= maxfilter and i >= minfilter]
        try: return sum(result) / len(result)
        except: pass


def SetWallHeight(wall):
    try: curve = wall.Location.Curve
    except: return False
    tolerance = 1800 / 304.8
    level = wall.Document.GetElement(wall.LevelId)
    above_level = GetLevelAbove(level, tolerance)
    if above_level == None or level.Id == above_level.Id: return
    samples = int(round(curve.Length // (tolerance / 2)) + 1)
    if samples > 10 or samples < 3: samples = 3
    points = [curve.Evaluate(round(0.5 / samples + float(i) / samples, 3), True) for i in range(samples)]
    values = [GetRayIntersection(p, Floor, XYZ(0, 0, 1)) for p in points]
    height = GetAverageValue(values)
    if height:
        calc_height = height - level.Elevation
        wall_height = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
        if calc_height and calc_height >= tolerance and wall_height > tolerance and wall_height != calc_height:
            wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(ElementId.InvalidElementId)
            wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).Set(calc_height)
            return True


def DeleteDuplicate(item):
    solid = GetElementSolid(item)
    solidfilter = ElementIntersectsSolidFilter(solid)
    collector = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(solidfilter)
    intersect = collector.OfCategory(BuiltInCategory.OST_StructuralColumns).FirstElement()
    centroid = GetCentroid(item)
    if intersect and GetCentroid(intersect).AlmostEqual(centroid):
        return doc.Delete(item.Id)


def SelectElement( items ):
    collection =  List[ElementId](i.Id for i in items if i)
    selection = uidoc.Selection.SetElementIds(collection)
    return selection


def CreateModelCurve(startpoint, endpoint):
    geomplane = Plane.CreateByNormalAndOrigin(XYZ.BasisX, startpoint)
    sketch = SketchPlane.Create(uidoc.Document, geomplane)
    uidoc.Document.ActiveView.SketchPlane = sketch
    uidoc.Document.ActiveView.ShowActiveWorkPlane()
    line = Line.CreateBound(startpoint, endpoint)
    modelcurve = doc.Create.NewModelCurve(line, sketch)
    return modelcurve


# Element.Name.GetValue(item)
###################################################################################################
items = GetCollumns()
TransactionManager.Instance.EnsureInTransaction(doc)
result = [SetCorrectCollumnTopLevel(item, False) for item in items if item]
doc.Regenerate()
TransactionManager.Instance.TransactionTaskDone()

###################################################################################################
items = GetWallsByWidht((100/304.8), FilterNumericGreaterOrEqual())
TransactionManager.Instance.EnsureInTransaction(doc)
result = [SetWallHeight(item) for item in items if item]
doc.Regenerate()
select = SelectElement( items )
TransactionManager.Instance.TransactionTaskDone()

###################################################################################################
items = GetCollumns()
TransactionManager.Instance.EnsureInTransaction(doc)
result = [SetCorrectCollumnTopOffset(item) for item in items if item]
doc.Regenerate()
TransactionManager.Instance.TransactionTaskDone()

#result = len(set([ i for i in result if i ]))

OUT = result
