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

def tolist(x):
    if hasattr(x, '__iter__'):
        return x
    else:
        return [x]


def flatten(x):
    result = []
    for el in tolist(x):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def LevelByElevation(value):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    filterrule = FilterDoubleRule(provider, FilterNumericEquals(), value, 0.5)
    levelfilter = ElementParameterFilter(filterrule)
    return FilteredElementCollector(DocumentManager.Instance.CurrentDBDocument).OfClass(Level).WherePasses(
        levelfilter).FirstElement()


def GetFilterDoubleParameter(bip, value, evaluator):
    provider = ParameterValueProvider(ElementId(bip))
    filterrule = FilterDoubleRule(provider, evaluator, value, 0.005)
    ParameterFilter = ElementParameterFilter(filterrule)
    return ParameterFilter


def GetFilterStringParameter(bip, value):
    provider = ParameterValueProvider(ElementId(bip))
    ParameterFilter = FilterStringRule(provider, FilterStringContains(), value, False)
    return ElementParameterFilter(ParameterFilter)


def GetBoundingBoxesByRooms(rooms):
    BoundingBoxes = [i.get_BoundingBox(None) for i in rooms if i.get_BoundingBox(None)]
    Transforms = [box.Transform for box in BoundingBoxes]
    BBoxMinX = min([t.OfPoint(box.Min).X for box, t in zip(BoundingBoxes, Transforms)])
    BBoxMinY = min([t.OfPoint(box.Min).Y for box, t in zip(BoundingBoxes, Transforms)])
    BBoxMinZ = min([t.OfPoint(box.Min).Z for box, t in zip(BoundingBoxes, Transforms)])
    BBoxMaxX = max([t.OfPoint(box.Max).X for box, t in zip(BoundingBoxes, Transforms)])
    BBoxMaxY = max([t.OfPoint(box.Max).Y for box, t in zip(BoundingBoxes, Transforms)])
    BBoxMaxZ = max([t.OfPoint(box.Max).Z for box, t in zip(BoundingBoxes, Transforms)])
    BBoxMin = XYZ(BBoxMinX, BBoxMinY, BBoxMinZ) + XYZ(0, 0, -5.0)
    BBoxMax = XYZ(BBoxMaxX, BBoxMaxY, BBoxMaxZ) + XYZ(0, 0, 15.0)
    return BBoxMin, BBoxMax


def GetWallfinishing(level, BBoxMin, BBoxMax):
    LevelFilter = ElementLevelFilter(level.Id)
    BBoxFilter = BoundingBoxIntersectsFilter(Outline(BBoxMin, BBoxMax))
    LocationFilter = LogicalAndFilter(LevelFilter, BBoxFilter)
    WallWidhtFilter = GetFilterDoubleParameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM, value=0.15,
                                               evaluator=FilterNumericLessOrEqual())
    StringFilter = GetFilterStringParameter(BuiltInParameter.FUNCTION_PARAM, "Внутренние слои")
    WallFilter = LogicalAndFilter(WallWidhtFilter, StringFilter)
    collector = FilteredElementCollector(doc).WherePasses(LocationFilter)
    walls = collector.OfClass(Wall).WherePasses(WallFilter).WhereElementIsNotElementType().ToElements()
    return walls


def GetMultiCategoryElements(level, BBoxMin, BBoxMax):
    LevelFilter = ElementLevelFilter(level.Id)
    BBoxFilter = BoundingBoxIntersectsFilter(Outline(BBoxMin, BBoxMax))
    LocationFilter = LogicalAndFilter(LevelFilter, BBoxFilter)
    builtInCats = List[BuiltInCategory]()
    builtInCats.Add(BuiltInCategory.OST_Roofs)
    builtInCats.Add(BuiltInCategory.OST_Floors)
    builtInCats.Add(BuiltInCategory.OST_Ceilings)
    builtInCats.Add(BuiltInCategory.OST_GenericModel)
    CategoryFilter = ElementMulticategoryFilter(builtInCats)
    collector = FilteredElementCollector(doc).WherePasses(LocationFilter)
    elements = collector.WherePasses(CategoryFilter).WhereElementIsNotElementType().ToElements()
    # wall.Orientation
    return elements


def FilterByWorksetUserAndGroup(items):
    usworkset = doc.Application.Username
    groups = FilteredElementCollector(doc).OfClass(Group)
    group_elems = flatten([i.GetMemberIds() for i in tolist(groups) if i])
    items = [i for i in items if i.Id not in group_elems]
    worksets = [i.get_Parameter(BuiltInParameter.EDITED_BY).AsString() for i in items if i]
    results = [i for i, w in zip(items, worksets) if i and w == "" or i and w == usworkset]
    return results


def GetFibonachiCirclePoints(point, samples):
    points = []
    increment = math.pi * (3.0 - math.sqrt(5.0))
    rds = 0.1
    for i in range(samples):
        phi = ((i + 0.1) % samples) * increment
        x = math.cos(phi) * rds
        y = math.sin(phi) * rds
        rds += 0.1
        p = XYZ(point.X + x, point.Y + y, point.Z)
        points.append(p)
    return points


def GetMostValue(values):
    set_common = set(values)
    tolerance = round(len(values) * 0.85)
    most_val = None
    count_val = 0
    for val in set_common:
        if val == None and values.upper(val) <= tolerance:
            pass
        elif val == None:
            continue
        count = values.upper(val)
        if count > count_val:
            count_val = count
            most_val = val
    result = most_val
    return result


def IntersectPoint(point, item):
    result = None
    vector = XYZ(0.5, 0.5, 0.5).Normalize()
    pntMin = point - vector * 0.05
    pntMax = point + vector * 0.05
    filter = BoundingBoxIntersectsFilter(Outline(pntMin, pntMax))
    itemId = FilteredElementCollector(item.Document).WherePasses(filter).FirstElementId()
    if itemId == item.Id: result = True
    return result


def GetRoomByElementBBox(room_doc, elevation, item):
    BBox = item.get_BoundingBox(None)
    bbmin = BBox.Transform.OfPoint(BBox.Min)
    bbmax = BBox.Transform.OfPoint(BBox.Max)
    center = (bbmin + bbmax) * 0.5
    phi = (math.sqrt(5) - 1) / 2
    bbmin = XYZ(bbmin.X + (center.X - bbmin.X) / phi, bbmin.Y + (center.Y - bbmin.Y) / phi,
                bbmin.Z + (center.Z - bbmin.Z) / phi)
    bbmax = XYZ(bbmax.X + (center.X - bbmax.X) / phi, bbmax.Y + (center.Y - bbmax.Y) / phi,
                bbmax.Z + (center.Z - bbmax.Z) / phi)
    min_distance = (bbmin.DistanceTo(bbmax)) * 0.3
    points = [XYZ(rnd.uniform(bbmin.X, bbmax.X), rnd.uniform(bbmin.Y, bbmax.Y), rnd.uniform(bbmin.Z, bbmax.Z)) for i in
              range(7)]
    points = [p for p in points if min_distance <= p.DistanceTo(center) and IntersectPoint(p, item)]
    pntZ = round((elevation + 5.0), 3)
    rooms = [room_doc.GetRoomAtPoint(XYZ(p.X, p.Y, pntZ)) for p in points]
    if len({r.Id for r in rooms if r}) >= 3: return None
    if rooms: return GetMostValue(rooms)
    center = XYZ(center.X, center.Y, pntZ)
    points = GetFibonachiCirclePoints(center, 30)
    rooms = [room_doc.GetRoomAtPoint(p) for p in points]
    room = GetMostValue(rooms)
    return room


def GetRoomByCurve(room_doc, elevation, item):
    samples = 3
    room = None
    if "Curve" in item.Location.GetType().Name:
        curve = item.Location.Curve
        points = [curve.Evaluate(round(0.5 / samples + float(i) / samples, 3), True) for i in range(samples)]
        fibpts = flatten([GetFibonachiCirclePoints(p, 9) for p in points])
        pntZ = round((elevation + 5.0), 3)
        rooms = [room_doc.GetRoomAtPoint(XYZ(p.X, p.Y, pntZ)) for p in fibpts]
        rooms = [room for room in rooms if room]
        if rooms and len(set(rooms)) == 1: return rooms[0]
        if rooms and len(set(rooms)) != 1:
            room = GetMostValue(rooms)
        else:
            fibpts = flatten([GetFibonachiCirclePoints(p, 30) for p in points])
        rooms = [room_doc.GetRoomAtPoint(XYZ(p.X, p.Y, pntZ)) for p in fibpts]
        rooms = [room for room in rooms if room]
        if rooms and len(set(rooms)) == 1: return rooms[0]
        if rooms and len(set(rooms)) != 1: room = GetMostValue(rooms)
    return room


def SetValue(item, prm_name, value):
    if item == None: pass
    try:
        item.LookupParameter(prm_name).Set(value); return
    except:
        pass


def GetSetRoomNumber(rooms, items, prm_name):
    if not items: pass
    room_doc = rooms[0].Document
    elevation = rooms[0].Level.Elevation
    numbers = [room.Number for room in rooms]
    defined = []
    for item in items:
        number = None
        room = GetRoomByCurve(room_doc, elevation, item)
        if not room: room = GetRoomByElementBBox(room_doc, elevation, item)
        if room and room.Number in numbers:
            defined.append(item)
            SetValue(item, prm_name, number)
        else:
            SetValue(item, prm_name, "")
    return defined


def SelectElement(items):
    collection = List[ElementId](i.Id for i in items if i)
    selection = uidoc.Selection.SetElementIds(collection)
    return selection


def ShowElementName(items):
    typeIds = set([i.GetTypeId() for i in flatten(items) if i])
    result = []
    for i in tolist(typeIds):
        etype = doc.GetElement(i)
        typename = etype.get_Parameter(BuiltInParameter.SYMBOL_FAMILY_AND_TYPE_NAMES_PARAM).AsString()
        typemark = etype.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK).AsString()
        if typename and typemark: result.Add(typename + " " + typemark)
        if typename and not typemark: result.Add(typename)
    return result


########################################################################################
rooms = [UnwrapElement(i) for i in flatten(IN[0]) if i and i.GetType().Name == "Room"]
prm_name = IN[1]
########################################################################################

TransactionManager.Instance.EnsureInTransaction(doc)

defined = []
undefined = []
if rooms:
    level = LevelByElevation(rooms[0].Level.Elevation)
    bbox = GetBoundingBoxesByRooms(rooms)
    numbers = [room.Number for room in rooms]
    items = GetWallfinishing(level, bbox[0], bbox[1])
    items = FilterByWorksetUserAndGroup(items)
    elems = GetSetRoomNumber(rooms, items, prm_name)
    defined.extend(elems)
    items = (i for i in items if i not in elems)
    undefined.extend(items)
    items = GetMultiCategoryElements(level, bbox[0], bbox[1])
    items = FilterByWorksetUserAndGroup(items)
    elems = GetSetRoomNumber(rooms, items, prm_name)
    defined.extend(elems)
    items = (i for i in items if i not in elems)
    undefined.extend(items)
    items = elems = None

doc.Regenerate()
TransactionManager.Instance.TransactionTaskDone()

########################################################################################
result_quantity = len(defined)
undefd_quantity = len(undefined)
if undefd_quantity == 0:
    elems_name = ShowElementName(defined)
else:
    elems_name = ShowElementName(undefined); SelectElement(undefined)
########################################################################################

OUT = result_quantity, undefd_quantity, undefined