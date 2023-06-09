import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

#Load Dynamo wrappers
clr.AddReference("RevitNodes")
import Revit
from Revit.Elements import *
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

#Load Revit API
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
import Autodesk

#Load document reference
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application

def toList(input):
	if not isinstance(input, list):
		return [input]
	else:
		return input

def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

def vecSimilarity(v1,v2):
	tolerance = 0.000001
	if abs(v1.X - v2.X) <= tolerance and abs(v1.Y - v2.Y) <= tolerance and abs(v1.Z - v2.Z) <= tolerance:
		return True
	else:
		return False
	
rooms = flatten(toList(IN[0]))
wfParam = IN[1]
whParam = IN[2]

#Get room boundaries, elements and disjoined curves
roomElems = []
disjoinedCurves = []
options = Autodesk.Revit.DB.SpatialElementBoundaryOptions()
roomBounds = []
for r in rooms:
	roomBounds.append(UnwrapElement(r).GetBoundarySegments(options))

for rb in roomBounds:
	tempCrvList = []
	for closedCrv in rb:
		tempCCCrvList = []
		for elem in closedCrv:
			if doc.GetElement(elem.ElementId) is None:
				roomElems.append(None)
				tempCCCrvList.append(elem.GetCurve().ToProtoType())
			else:
				roomElems.append(doc.GetElement(elem.ElementId))
				tempCCCrvList.append(elem.GetCurve().ToProtoType())
		tempCrvList.append(tempCCCrvList)
	disjoinedCurves.append(tempCrvList)

#Join curves in polycurves
joinedCurves = []
for d in disjoinedCurves:
	tempList = []
	for item in d:
		tempList.append(PolyCurve.ByJoinedCurves(item))
	joinedCurves.append(tempList)

#Check the sense of the polycurve
for j in joinedCurves:
	for crv in j:
		if crv.BasePlane().Normal.Z > 0:
			crv = crv
		else:
			crv = crv.Reverse()

repeatedRooms = []
count = 0
for j in joinedCurves:
	tempList = []
	for crv in j:
		tempList.append(rooms[count])
	repeatedRooms.append(tempList)
	count += 1

joinedCurves = flatten(joinedCurves)
repeatedRooms = flatten(repeatedRooms)


#Retrieve wallTypes and heights
wTypes = []
wHeights = []

allWallTypes = FilteredElementCollector(doc).OfClass(WallType)
for r in repeatedRooms:
	wHeights.append(r.GetParameterValueByName(whParam))
	for wt in allWallTypes:
		if Element.Name.__get__(wt) == r.GetParameterValueByName(wfParam):
			wTypes.append(wt.ToDSType(True))

#Retrieve the level of each room
levels = []
for r in repeatedRooms:
	levels.append(UnwrapElement(r).Level)

#Create an offseted curve to place finishes. Wall by curve are modeled by Wall Centerline
offsetedCurves = []
count = 0
for j in joinedCurves:
	if UnwrapElement(repeatedRooms[count]).IsPointInRoom(
            j.Offset(wTypes[count].GetParameterValueByName("Ширина") * 0.5, False).StartPoint.ToXyz()):
		offsetedCurves.append(j.Offset(wTypes[count].GetParameterValueByName("Ширина")*0.5,False))
	else:
		offsetedCurves.append(j.Offset(wTypes[count].GetParameterValueByName("Ширина")*-0.5,False))
	count +=1

explodedCurves = []
for oc in offsetedCurves:
	explodedCurves.append(oc.Explode())

#Create walls on topValue of the curves with fixed height
wHeightsList = [] #List of height for each wall
distances = [] #distance to move a probe point to check the paralel wall
walls = []
TransactionManager.Instance.EnsureInTransaction(doc)
count = 0
for group in explodedCurves:
	for crv in group:
		if vecSimilarity(crv.TangentAtParameter(0),crv.TangentAtParameter(1)):
			rbldCrv = Autodesk.DesignScript.Geometry.Line.ByStartPointEndPoint(crv.StartPoint, crv.EndPoint)
		else:
			rbldCrv = Autodesk.DesignScript.Geometry.Arc.ByThreePoints(crv.PointAtParameter(0), crv.PointAtParameter(0.5), crv.PointAtParameter(1))
		w = Wall.Create(doc, rbldCrv.ToRevitType(), UnwrapElement(wTypes[count]).Id, UnwrapElement(levels[count]).Id, 5, 0, True, False);
		wHeightsList.append(wHeights[count])
		walls.append(w.ToDSType(False))
	count +=1
TransactionManager.Instance.TransactionTaskDone()

#Change the height of the walls to meet requirements, change Location workset_name to Finish Face Exterior and turn off Room Bounding
count = 0
for w in walls:
	w.SetParameterByName("Неприсоединенная высота", wHeightsList[count])
	w.SetParameterByName("Линия привязки", 2)
	w.SetParameterByName("Граница помещения", 0)
	#Here is the best location to add any room parameter to the walls p.e. Room Number
	#w.SetParameterByName("RoomNumber", UnwrapElement(repeatedRooms[count]).GetParameterValueByName(Number))
	count +=1

#If the suport wall has inserts, this will join it to the finish wall.
#If the suport wall is a curtain wall, this will delete the finish associated to it.
TransactionManager.Instance.EnsureInTransaction(doc)
count = 0
for r in roomElems:
	if r is not None and UnwrapElement(r).Category.Name.ToString() == "Walls" and len(UnwrapElement(r).FindInserts(True, True, True, True)) != 0:
		JoinGeometryUtils.JoinGeometry(doc, UnwrapElement(walls[count]), UnwrapElement(r))
	if r is not None and UnwrapElement(r).Category.Name.ToString() == "Walls" and UnwrapElement(r).WallType.Kind == WallKind.Curtain:
		doc.Delete(UnwrapElement(walls[count]).Id)
	count += 1
TransactionManager.Instance.TransactionTaskDone()

OUT = walls