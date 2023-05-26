# -*- coding: UTF-8 -*-
#  This file will be run on startup and when a remote Python engine
#  gets initialized

import System
from System.Collections.Generic import List

import clr
from operator import itemgetter

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
import Autodesk

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('RevitNodes')
import Revit
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
UIunit = Document.GetUnits(doc).GetFormatOptions(UnitType.UT_Length).DisplayUnits

viewcollector = FilteredElementCollector(doc).OfClass(View3D).ToElements()

def tolist(x):
	if hasattr(x,'__iter__'): return x
	else : return [x]

def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

def WallFromRoom(room):
	LevelFilter = ElementLevelFilter(room.Level.Id)
	BBox = room.get_BoundingBox(None)
	IntersectsFilter = BoundingBoxIntersectsFilter( Outline( BBox.Min, BBox.Max ))
	logicalFilter = LogicalAndFilter(LevelFilter, IntersectsFilter)
	return FilteredElementCollector(doc).WhereElementIsNotElementType().WhereElementIsViewIndependent().WherePasses(logicalFilter).OfClass(Wall).ToElements()

def GetLevelAbove(level):
	allLevels = FilteredElementCollector(doc).OfClass(Level).ToElements()
	elevations = [i.Elevation for i in allLevels]
	sortedLevels = [x for (y,x) in sorted(zip(elevations,allLevels))]
	sortedLevelNames = [i.Name for i in sortedLevels]
	index = sortedLevelNames.index(level.Name)
	if index + 1 >= len(sortedLevels):
		return None
	else:
		return sortedLevels[index+1]

def GetExteriorWallDirection(item):
	if type(item) == Autodesk.Revit.DB.Wall:
		locationCurve = item.Location
		if locationCurve != None:
			curve = locationCurve.Curve
			direction = XYZ.BasisX
			if type(curve) == Autodesk.Revit.DB.Line:
				direction = curve.ComputeDerivatives(0, True).BasisX.Normalize()
			else:
				direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
			exteriorDirection = XYZ.BasisZ.CrossProduct(direction)
			if item.Flipped:
				exteriorDirection = -exteriorDirection
			return exteriorDirection

def GetWallLoctionPoints(item):
	curve = wall.Location.Curve
	halfthickness = 0.5 * wall.WallType.Width
	extvector = GetExteriorWallDirection(wall)
	startPoint = curve.GetEndPoint( 0 )
	endPoint = curve.GetEndPoint( 1 )
	vdirect = (endPoint - startPoint).Normalize()
	pstr = startPoint - vdirect + halfthickness * extvector
	pend = endPoint + vdirect + halfthickness * extvector
	pmidl = (pstr + pend)/2
	points = [pstr, pmidl, pend]
	return points

def View3D():
	viewlist = filter(lambda x: x, viewcollector)
	result = []
	for view in viewlist:
		if view.ViewType == ViewType.ThreeD:
			if not(view.IsTemplate):
				if view.Name in "{3D}":
					result = view
	return result

def GetHeightPoint(RayStartPoints):
    builtInCats = [BuiltInCategory.OST_Ceilings, BuiltInCategory.OST_Floors, BuiltInCategory.OST_Roofs]
    filter = ElementMulticategoryFilter(List[BuiltInCategory](builtInCats))
    ri = ReferenceIntersector(filter, FindReferenceTarget.All, View3D())
    ri.FindReferencesInRevitLinks = False
    direction = XYZ(0,0,1)
    Hpoint = []
    TopElements = []
    for p in RayStartPoints:
        ref = ri.FindNearest(p, direction)
        if ref != None:
			refp = ref.GetReference().GlobalPoint
			refp = refp - p
			pts = refp
			Hpoint.append(pts.Z)
			TopElements.append(doc.GetElement(ref.GetReference().ElementId))
	if TopElements:
		return min(tolist(Hpoint))

def SetParameterToNone(parameter, items):
    inv = ElementId.InvalidElementId
    for i in tolist(items):
    	itm = None
    	par = i.LookupParameter(parameter)
    	if par is not None:
			par.Set(inv)
			itm = i
	return

########################## INPUT ##################################
rooms = test = None
rooms = flatten(tolist(UnwrapElement(IN[0])))
###################################################################

finishingwalls = []
for indx, rm in enumerate(rooms):
	wall = WallFromRoom(rm)
	finishingwalls.append(wall)

flattenwall = flatten(finishingwalls)

TransactionManager.Instance.EnsureInTransaction(doc)

raypoints = []
result = []
test = []
for wall in flattenwall:
	points = GetWallLoctionPoints(wall)
	toppoint = GetHeightPoint(points)
	raypoints.append(toppoint)
	wallheight = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
	if toppoint != wallheight:
		baselvlId = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT).AsElementId()
		blevel = doc.GetElement(baselvlId)
		alevel = GetLevelAbove(blevel)
		levelheight = alevel.Elevation - blevel.Elevation
		WallHeightPrm = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)
		if alevel and toppoint and  toppoint < levelheight:
			resultval = levelheight - toppoint
			if WallHeightPrm is not None:
				WallHeightPrm.Set(alevel.Id)
                test.append("Тест прошел условие Зависимый сверху")
                result.append(resultval * 304.8)
        else:
            resultval = toppoint
            if WallHeightPrm is not None:
            	inv = ElementId.InvalidElementId
            	WallHeightPrm.Set(inv)
            	test.append("Тест прошел условие Неприсоединенный")
            	result.append(toppoint * 304.8)

TransactionManager.Instance.TransactionTaskDone()