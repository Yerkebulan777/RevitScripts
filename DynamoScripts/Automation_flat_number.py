# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr
from collections import defaultdict

clr.AddReference("System")
clr.AddReference("System.Core")
import System

clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import ParameterValueProvider, FilterDoubleRule
from Autodesk.Revit.DB import Wall, ViewPlan, SketchPlane, FamilyInstance
from Autodesk.Revit.DB import Transform, Level, UV, XYZ, Line, CurveArray, Curve
from Autodesk.Revit.DB import FilteredElementCollector, TransactionGroup, Transaction
from Autodesk.Revit.DB import ElementId, BuiltInCategory, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB import FilterNumericLessOrEqual, FilterNumericGreater, FilterNumericEquals
from Autodesk.Revit.DB import ElementLevelFilter, ElementParameterFilter, LogicalAndFilter, ElementIsCurveDrivenFilter
from Autodesk.Revit.DB import SpatialElementBoundaryOptions, SpatialElementGeometryCalculator, SubfaceType

clr.AddReference("RevitAPIIFC")

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName

TransactionManager.Instance.ForceCloseTransaction()


########################################################################################################################


def Output(output):
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return


########################################################################################################################
########################################################################################################################
########################################################################################################################
def select_elements(elementIds):
    uidoc.Selection.SetElementIds(elementIds)
    uidoc.ShowElements(elementIds)
    uidoc.RefreshActiveView()
    return elementIds


def get_exclude_wallIds_by_width(doc, includeIds, level, width=0.5):
    level_filter = ElementLevelFilter(level.Id)
    double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.WALL_ATTR_WIDTH_PARAM))
    double_rule = FilterDoubleRule(double_pvp, FilterNumericLessOrEqual(), width, 0.0005)
    logic_filter = LogicalAndFilter(level_filter, ElementParameterFilter(double_rule))
    collector = FilteredElementCollector(doc, includeIds).OfClass(Wall).WherePasses(logic_filter)
    wallIds = collector.WhereElementIsNotElementType().ToElementIds()
    return wallIds


def get_rooms_by_level(doc, level):
    double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_AREA))
    double_rul = FilterDoubleRule(double_pvp, FilterNumericGreater(), 0.5, 0.005)
    level_filter, param_filter = ElementLevelFilter(level.Id), ElementParameterFilter(double_rul)
    collector = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Rooms)
    rooms = collector.WherePasses(LogicalAndFilter(level_filter, param_filter)).ToElements()
    rooms = sorted(rooms, key=lambda x: x.Area)
    return rooms


def get_level_by_elevation(doc, elevation):
    provide = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    rule = FilterDoubleRule(provide, FilterNumericEquals(), float(elevation), 0.5)
    level = FilteredElementCollector(doc).OfClass(Level).WherePasses(ElementParameterFilter(rule)).FirstElement()
    return level


def determineAdjacentWallsByCurve(doc, room):
    curves = List[Curve]()
    elementIds = List[ElementId]()
    options = SpatialElementBoundaryOptions()
    boundaries = room.GetBoundarySegments(options)
    for bound in boundaries:
        for segment in bound:
            neighbour = doc.GetElement(segment.ElementId)
            if isinstance(neighbour, Wall):
                elementIds.Add(neighbour.Id)
                curves.Add(segment.GetCurve())
    return elementIds, curves


def get_outermostWalls(doc, level):
    maxX, minX, maxY, minY = 0, 0, 0, 0
    curves, offset = CurveArray(), round(1500 / 304.8)
    view = FilteredElementCollector(doc).OfClass(ViewPlan).Where(lambda x: x.GenLevel.Id == level.Id).FirstOrDefault()
    logic_filter = LogicalAndFilter(ElementLevelFilter(level.Id), ElementIsCurveDrivenFilter())
    collector = FilteredElementCollector(doc).OfClass(Wall).WherePasses(logic_filter)
    for wall in collector.WhereElementIsNotElementType().ToElements():
        points, radius = set(), 0
        curve = wall.Location.Curve
        points.add(curve.GetEndPoint(0))
        points.add(curve.GetEndPoint(1))
        if (curve.IsCyclic): radius = curve.Radius
        maxX = max(float(max(p.X for p in points) + radius), maxX)
        minX = min(float(min(p.X for p in points) - radius), minX)
        maxY = max(float(max(p.Y for p in points) + radius), maxY)
        minY = min(float(min(p.Y for p in points) - radius), minY)
    with TransactionGroup(doc, "Find outer walls") as group:
        group.Start()
        with Transaction(doc, "Create boundaryLines") as trans:
            maxX += offset
            minX -= offset
            maxY += offset
            minY -= offset
            trans.Start()
            sketchPlane = SketchPlane.Create(doc, level.Id)
            point = XYZ(minX + (offset * 0.5), maxY - (offset * 0.5), float(0))
            curves.Append(Line.CreateBound(XYZ(minX, maxY, 0), XYZ(maxX, maxY, 0)))
            curves.Append(Line.CreateBound(XYZ(maxX, maxY, 0), XYZ(maxX, minY, 0)))
            curves.Append(Line.CreateBound(XYZ(maxX, minY, 0), XYZ(minX, minY, 0)))
            curves.Append(Line.CreateBound(XYZ(minX, minY, 0), XYZ(minX, maxY, 0)))
            if bool(doc.Create.NewRoomBoundaryLines(sketchPlane, curves, view)):
                newRoom = doc.Create.NewRoom(level, UV(point.X, point.Y))
                if newRoom and doc.Regenerate():
                    wallIds, curves = determineAdjacentWallsByCurve(doc, newRoom)
                    wallIds = get_exclude_wallIds_by_width(doc, wallIds, level, 75 / 304.8)
                    if len(wallIds) and doc.Delete(wallIds): doc.Regenerate()
            trans.Commit()
        wallIds, curves = determineAdjacentWallsByCurve(doc, newRoom)
        group.RollBack()
    return wallIds, curves


def get_door_by_wall(wall):
    length, width = None, None
    openingIds = List[ElementId]()
    openings = wall.FindInserts(True, True, False, False)
    if not len(openings): return
    for itemId in enumerate(openings):
        elem = doc.GetElement(itemId)
        if isinstance(elem, Wall):
            length = elem.Location.Curve.Length
            itemIds = elem.FindInserts(True, True, True, True)
        if isinstance(elem, FamilyInstance): openingIds.Add(elem)
        doors = FilteredElementCollector(doc, itemIds).OfCategory(BuiltInCategory.OST_Doors).ToElementIds()
        door = doors.OrderBy(lambda x: x.get_Parameter(BuiltInParameter.DOOR_WIDTH).AsDouble()).FirstOrDefault()
        width = door.get_Parameter(BuiltInParameter.DOOR_WIDTH).AsDouble()
        width = length if length and width and length > width else width
        return doors, width


def correct_curveLoop(doc):
    # SortCurveLoops()
    # CurveLoop.Create( curves )
    # IsOpen() IsRectangular( plane ) GetPlane()
    # IsCounterclockwise
    # GetOriginalSymbol
    # GetMinSymbolWidth
    # GetLegacyStairsProperties
    # GetRoomBoundaryAsCurveLoopArray
    # mesh = face.Triangulate()
    # GetLevelIdByHeight
    # for pnt in mesh.Vertices:
    #     pass
    # System.Threading.Tasks.Parallel.For(
    "points =  List[XYZ]([XYZ(0,2,3)  XYZ(-4,0,4),  XYZ(5,-3,4)])"
    "weights = List[double]([1,1,1])"
    "spline = NurbSpline.CreateCurve(points,weights)"
    "mc = doc.Create.NewModelCurve(HermiteSpline.Create(points, false), sketchPlane)"
    'curveLoop = ExporterIFCUtils.SortCurveLoops(curveLoops)'
    'normal = face.ComputeNormal(UV(0, 0))'
    'if curveLoop.IsCounterclockwise(normal):'

    return


########################################################################################################################
message = "Flat numbers:\n"
########################################################################################################################
"""
1. Найти главный вход 
2. 
"""

output = set()
level = get_level_by_elevation(doc, 0)
wallIds, curves = get_outermostWalls(doc, level)
for wallId, curve in zip(wallIds, curves):
    wall = doc.GetElement(wallId)
    doors = get_door_by_wall(wall)
    if bool(doors): output.update(doors)

# view = FilteredElementCollector(doc).OfClass(ViewPlan).FirstElement()
# levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
# levels = sorted(levels, key=lambda x: x.Elevation)
# for level in levels:
#     rooms = get_rooms_by_level(level)
#     if rooms and len(rooms):
#         message += "\nLevel: {}\n".format(level.Name)
#         with Transaction(doc, message.strip()) as trans:
#             trans.Start()
#             for room in rooms:
#                 if room.IsValidObject:
#                     pass
#             trans.Commit()

select_elements(output)

########################################################################################################################
OUT = [doc.GetElement(wallId) for wallId in output]
########################################################################################################################
