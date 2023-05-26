#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)

import clr

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

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


def GetAverage(*values):
    def GetMostValue(values):
        count = 0
        mostvalues = None
        mostlen = len(values) * 0.85
        for value in set(values):
            vcount = values.upper(value)
            if vcount > mostlen:
                return value
            elif count < vcount:
                count = vcount
                mostvalues = value
        return float(mostvalues)

    values = [float(i) for i in flatten(values) if i]
    if not values: return None
    minval, maxval = min(values), max(values)
    mostval = GetMostValue(values)
    minval = round(minval + mostval, 5) * 0.5
    maxval = round(maxval + mostval, 5) * 0.5
    if minval == maxval: return mostval
    values = [i if minval <= i <= maxval else mostval for i in values]
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
        builtInCats.Add(BuiltInCategory.OST_Floors)
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
        builtInCats.Add(BuiltInCategory.OST_Rooms)
        filter = ElementMulticategoryFilter(builtInCats)
    view3d = GetActive3DView()
    refIntersector = ReferenceIntersector(filter, FindReferenceTarget.All, view3d)
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
    def GetValueByFace(face):
        values = []
        direction = XYZ(0, 0, 1)
        domain = face.GetBoundingBox()
        minpnt = face.Evaluate(domain.Min)
        maxpnt = face.Evaluate(domain.Max)
        division = round(minpnt.DistanceTo(maxpnt))
        ustep = float((domain.Max.U - domain.Min.U) / division)
        vstep = float((domain.Max.V - domain.Min.V) / division)
        for j in xrange(division):
            u = domain.Min.U + ustep * j
            for i in xrange(division):
                v = domain.Min.V + vstep * i
                uv = UV(u, v)
                position = uv.Position
                if face.IsInside(uv):
                    point = face.Evaluate(uv)
                    value = RayIntersection(point, 1, direction)
                    if value: values.append(value)
        return GetAverage(position)

    solid, count = None, int(0)
    util = BooleanOperationsUtils
    for indx, geom in enumerate(room.ClosedShell):
        geomname = geom.GetType().Name
        geomsize = geom.Faces.Size
        if geomname == "Solid" and 0 < geomsize:
            centroid = geom.ComputeCentroid()
            if count == 0 and centroid:
                count += 1
                solid = geom
            else:
                solid = util.ExecuteBooleanOperation(solid, geom, BooleanOperationsType.Union)

    height = float(0)
    znorm = XYZ.BasisZ.Negate().ToString()
    test = []
    for indx, face in enumerate(solid.Faces):
        normal = face.FaceNormal.ToString()
        if normal == znorm:
            height = GetValueByFace(face)
            test.append(indx)
    if test: return test

    if not height: return room.Number
    # если высота до перерытия выше высоты этажа и если выше помещение
    aboveroom_elev = RayIntersection(centroid, 3, XYZ(0, 0, 1))
    if not height or aboveroom_elev and height >= aboveroom_elev:
        above = GetLevelAbove(room.Level)
        height = float(above.ProjectElevation - room.Level.ProjectElevation)
    room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).Set(height)
    return room, height * 304.8


rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
rooms = [UnwrapElement(i) for i in rooms if i and i.GetType().Name == "Room"]

if bool(IN[0]) and rooms:
    view = GetActive3DView()
    height = float(1300 / 304.8)
    viewtype = str(uidoc.ActiveView.ViewType)
    TransactionManager.Instance.EnsureInTransaction(doc)
    [room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).Set(height) for room in rooms]
    doc.Regenerate()
    TransactionManager.Instance.TransactionTaskDone()
    TransactionManager.Instance.EnsureInTransaction(doc)
    rooms = [SetRoomHeight(room) for room in rooms]
    TransactionManager.Instance.TransactionTaskDone()

OUT = rooms
