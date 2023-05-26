import clr

clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument

def tolist(input):
	if not isinstance(input, list):
		return [input]
	else:
		return input

def GetValidRooms( doc, level ):
	levelFilter = ElementLevelFilter( level.Id )
	TransactionManager.Instance.EnsureInTransaction(doc)
	rooms = FilteredElementCollector(doc).OfClass(Autodesk.Revit.DB.SpatialElement).WherePasses(levelFilter).ToElements()
	check = [ doc.Delete(room) for room in rooms if room.Level is None ]
	rooms = [ room for room in rooms if room.Area ]
	TransactionManager.Instance.TransactionTaskDone()
	if len(rooms) >= 5: return rooms
	collector = FilteredElementCollector(doc)
	LinkInstance = collector.OfClass(RevitLinkInstance).WhereElementIsNotElementType().ToElements()
	if LinkInstance == None: pass
	for link in LinkInstance:
		try:
			doc = link.GetLinkDocument()
			if doc == None: continue
			collector = FilteredElementCollector(doc)
			rooms = collector.OfClass(Autodesk.Revit.DB.SpatialElement).WherePasses(levelFilter).ToElements()
			if rooms: rooms = [ room for room in rooms if room.Area ]
			if rooms and len(rooms) >= 5: return rooms
		except: continue

def LevelIdByElevation( value ):
	provider = ParameterValueProvider( ElementId(BuiltInParameter.LEVEL_ELEV) )
	filterrule = FilterDoubleRule( provider, FilterNumericEquals(), value, 1.5 )
	levelfilter = ElementParameterFilter( filterrule )
	return FilteredElementCollector(DocumentManager.Instance.CurrentDBDocument).OfClass(Level).WherePasses(levelfilter).FirstElement()

############################################### INPUT ############################################
if IN[0]: levelInput = UnwrapElement(IN[0])
else: levelInput = DocumentManager.Instance.CurrentDBDocument.ActiveView.GenLevel
if levelInput: levelElevation =  levelInput.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsDouble()
else: levelElevation = 0.000
level = LevelIdByElevation( levelElevation )
##################################################################################################
rooms = GetValidRooms( doc, level )

OUT = rooms 