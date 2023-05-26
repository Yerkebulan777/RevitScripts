#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
import math

import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('System')
from System.Collections.Generic import List

clr.AddReference('RevitNodes')
import Revit

clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
uiapp = DocumentManager.Instance.CurrentUIApplication


def flatten(items):
    if hasattr(items, '__iter__'):
        itemlst = items
    else:
        itemlst = [items]
    result = []
    for el in itemlst:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def GetLevelByElev(value):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    filterrule = FilterDoubleRule(provider, FilterNumericEquals(), value, 0.5)
    levelfilter = ElementParameterFilter(filterrule)
    level = FilteredElementCollector(doc).OfClass(Level).WherePasses(levelfilter).FirstElement()
    return level


def GetLevelAbove(level):
    tolerance = float(1800 / 304.8)
    levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    sortedLvls = sorted(levels, key=lambda x: (x.ProjectElevation))
    sortedLvlNames = [i.Name for i in sortedLvls]
    index = sortedLvlNames.index(level.Name)
    if index < len(sortedLvls):
        result = sortedLvls[index + 1]
        if result.ProjectElevation - level.ProjectElevation >= tolerance:
            return result
        else:
            return GetLevelAbove(result)


def GetAverage(values):
    def GetMostValue(values):
        mostvalues = None
        vcount, count = int(0)
        mostlen = len(values) * 0.85
        for value in set(values):
            if values.upper(value) <= mostlen:
                return value
            elif value:
                vcount = values.upper(value)
            if count > vcount:
                count = vcount
                mostvalues = value
        return float(mostvalues)

    values = [float(i) for i in flatten(values) if i]
    if len(set(values)) == 1:
        return values[0]
    elif len(set(values)) >= 2:
        minval, maxval = min(values), max(values)
        if minval == maxval: return maxval
        mostval = GetMostValue(values)
        minval = round(minval + mostval) * 0.5
        maxval = round(maxval + mostval) * 0.5
        values = [i for i in values if i <= maxval and i >= minval]
        result = float(sum(values) / len(values))
        return result


def GetActive3DView():
    actiview = uidoc.ActiveView
    collector = FilteredElementCollector(doc).OfClass(View3D)
    if actiview.Id in collector.ToElementIds(): return actiview
    TransactionManager.Instance.EnsureInTransaction(doc)
    TransactionManager.Instance.ForceCloseTransaction()
    cmdname = PostableCommand.CloseHiddenWindows
    cmdid = RevitCommandId.LookupPostableCommandId(cmdname)
    for view in collector.ToElements():
        if view and not view.IsTemplate:
            try:
                uidoc.ActiveView.Dispose()
                uidoc.RequestViewChange(view)
                uidoc.RefreshActiveView()
                uiapp.PostCommand(cmdid)
                collector.Dispose()
                return view
            except:
                pass


def RayIntersection(point, filter_class, direction):
    filter, tolerance = None, float(1500 / 304.8)
    point = XYZ(point.X, point.Y, point.Z)
    if filter_class == 1:
        builtInCats = List[BuiltInCategory]()
        builtInCats.Add(BuiltInCategory.OST_Ceilings)
        builtInCats.Add(BuiltInCategory.OST_GenericModel)
        builtInCats.Add(BuiltInCategory.OST_StructuralFraming)
        filter = ElementMulticategoryFilter(builtInCats)
    if filter_class == 2:
        builtInCats = List[BuiltInCategory]()
        builtInCats.Add(BuiltInCategory.OST_Floors)
        builtInCats.Add(BuiltInCategory.OST_StructuralFraming)
        builtInCats.Add(BuiltInCategory.OST_Roofs)
        filter = ElementMulticategoryFilter(builtInCats)
    if filter_class == 3:
        builtInCats = List[BuiltInCategory]()
        builtInCats.Add(BuiltInCategory.OST_Walls)
        filter = ElementMulticategoryFilter(builtInCats)
    view = uidoc.ActiveView  # 3DView
    refIntersector = ReferenceIntersector(filter, FindReferenceTarget.Element, view)
    refIntersector.FindReferencesInRevitLinks = True
    startpoint = point + direction * tolerance
    nrefwc = refIntersector.FindNearest(startpoint, direction)
    if not nrefwc: return
    reference = nrefwc.GetReference()
    endpoint = reference.GlobalPoint
    value = float(point.DistanceTo(endpoint))
    # represent = reference.ConvertToStableRepresentation(doc)
    # element = doc.GetElement(represent)
    return value


def SetRoomHeight(room):
    def PointsByFace(face):
        domain = face.GetBoundingBox()
        minpnt = face.Evaluate(domain.Min)
        maxpnt = face.Evaluate(domain.Max)
        division = int((float(minpnt.DistanceTo(maxpnt)) // 0.5) + 1)
        ustep = float((domain.Max.U - domain.Min.U) / division)
        vstep = float((domain.Max.V - domain.Min.V) / division)
        pnts = []
        for j in xrange(division):
            u = domain.Min.U + ustep * j
            for i in xrange(division):
                v = domain.Min.V + vstep * i
                uv = UV(u, v)
                if face.IsInside(uv):
                    pnt = face.Evaluate(uv)
                    pnts.append(pnt)
        return pnts

    calculator = SpatialElementGeometryCalculator(room.Document)
    calc_geom = calculator.CalculateSpatialElementGeometry(room)
    roomsolid = calc_geom.GetGeometry()
    faces = []
    for face in roomsolid.Faces:
        for subface in calc_geom.GetBoundaryFaceInfo(face):
            if subface.SubfaceType == SubfaceType.Bottom:
                subface = subface.GetSubface()
                faces.extend(subface)
    pts = flatten([PointsByFace(face) for face in faces if face.Area > 0])
    return pts
    floor_height = GetAverage([RayIntersection(pt, 2, XYZ(0, 0, 1)) for pt in pts])
    if floor_height: return floor_height
    level = GetLevelByElev(room.Level.Elevation)
    above_lvl = GetLevelAbove(level)
    if floor_height and above_lvl:
        countpts = len(pts)
        centroid = XYZ(sum([pt.X for pt in pts]), sum([pt.Y for pt in pts]), sum([pt.Z for pt in pts]))
        centroid = XYZ(centroid.X / countpts, centroid.Y / countpts, centroid.Z / countpts)
        centroid = XYZ(centroid.X, centroid.Y, above_lvl.ProjectElevation)
        lvl_height = float(above_lvl.ProjectElevation - level.ProjectElevation)
        above_room = room.Document.GetRoomAtPoint(centroid)
        # если высота до перерытия выше высоты этажа и если выше помещение
        if floor_height > lvl_height and above_room and room.Id != above_room.Id:
            room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).Set(lvl_height)
        else:
            room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).Set(floor_height)
        return room


def WallByGroupInRoom(room, level, group_model):
    bbox = room.get_BoundingBox(None)
    bbmin = bbox.Transform.OfPoint(bbox.Min) - XYZ(0.5, 0.5, 0.5)
    bbmax = bbox.Transform.OfPoint(bbox.Max) + XYZ(0.5, 0.5, 0.5)
    lvlfilter = ElementLevelFilter(level.Id)
    bbxfilter = BoundingBoxIntersectsFilter(Outline(bbmin, bbmax))
    locfilter = LogicalAndFilter(lvlfilter, bbxfilter)
    provider = ParameterValueProvider(ElementId(BuiltInParameter.WALL_ATTR_WIDTH_PARAM))
    filter = ElementParameterFilter(FilterDoubleRule(provider, FilterNumericLessOrEqual(), round(50 / 304.8, 5), 0.05))
    collector = FilteredElementCollector(doc).OfClass(Wall).WherePasses(locfilter)
    ids = collector.WherePasses(filter).WhereElementIsNotElementType().ToElementIds()
    if bool(ids):
        provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_MODEL))
        filter = ElementParameterFilter(FilterStringRule(provider, FilterStringContains(), group_model, False))
        result = FilteredElementCollector(doc, ids).WherePasses(filter).ToElements()
        return result


def IsWallInRoom(wall, room, isFinishing):
    location = wall.Location
    if "Curve" in location.GetType().Name:
        calc_wh = None
        curve = location.Curve
        normal = wall.Orientation
        wthick = float(wall.WallType.Width) * 5
        samles, crvlen = 5, float(curve.Length)
        mintol, maxtol = round(1800 / 304.8, 3), round(4500 / 304.8, 3)
        if crvlen < mintol: samles = 3
        points = [curve.Evaluate(round(float(i + 0.5) / samles, 5), True) for i in xrange(samles)]
        offset = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
        roomht = room.get_Parameter(BuiltInParameter.ROOM_HEIGHT).AsDouble()
        height = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
        if isFinishing == True and mintol < height < maxtol:
            calc_wh = [RayIntersection(point, 1, XYZ(0, 0, 1)) for point in points]
            calc_wh = [val if val and round(val) <= round(roomht) else roomht for val in calc_wh]
            calc_wh = float(sum(calc_wh) / len(calc_wh) - offset)
        elif isFinishing != True and mintol < height < maxtol:
            calc_wh = [RayIntersection(point, 2, XYZ(0, 0, 1)) for point in points]
            calc_wh = [val if val and round(val) >= round(roomht) else roomht for val in calc_wh]
            calc_wh = float(sum(calc_wh) / len(calc_wh) - offset)
        extpoints = [point + normal * wthick for point in points]
        if any({room.IsPointInRoom(point) for point in extpoints}):
            if calc_wh and calc_wh != height: height = calc_wh
            wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(ElementId.InvalidElementId)
            wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).Set(height)
            wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(3)
            return wall
        intpoints = [point - normal * wthick for point in points]
        if any({room.IsPointInRoom(point) for point in intpoints}):
            level = GetLevelByElev(room.Level.Elevation)
            inserts = bool(wall.FindInserts(True, True, True, True))
            boolean = bool(height != None and height < maxtol and not inserts)
            if boolean and not wall.Flipped:
                newall = Wall.Create(doc, curve, wall.WallType.Id, level.Id, height, float(0), True, False)
                newall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).Set(offset)
                newall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(3)
                doc.Delete(wall.Id)
                return newall
            elif boolean and wall.Flipped:
                newall = Wall.Create(doc, curve, wall.WallType.Id, level.Id, height, float(0), False, False)
                newall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).Set(offset)
                newall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(3)
                doc.Delete(wall.Id)
                return newall
            else:
                return wall


def SetValue(item, value):
    prm = item.LookupParameter(IN[1])
    if prm != None and not prm.IsReadOnly:
        prm.Set(value)
        return item


def SelectElement(items):
    collection = List[ElementId](i.Id for i in items if i)
    selection = uidoc.Selection.SetElementIds(collection)
    return selection


rooms = [UnwrapElement(i) for i in flatten(IN[0]) if i and i.GetType().Name == "Room"]

TransactionManager.Instance.EnsureInTransaction(doc)

view = GetActive3DView()
viewtype = str(uidoc.ActiveView.ViewType)
newrooms, finishes = [], []
if viewtype == "ThreeD":
    for room in rooms:
        room = SetRoomHeight(room)
        newrooms.append(room)
        doc.Regenerate()
        continue
        level = GetLevel(room.Level.Elevation)
        walls = WallByGroupInRoom(room, level, "Отделка")
        if walls:
            value = room.Number
            walls = [IsWallInRoom(wall, room, True) for wall in walls]
            walls = [SetValue(wall, value) for wall in walls if wall]
            finishes.extend(walls)

TransactionManager.Instance.TransactionTaskDone()

OUT = newrooms
