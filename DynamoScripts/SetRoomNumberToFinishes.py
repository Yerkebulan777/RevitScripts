#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr

clr.AddReference('RevitAPI')

from Autodesk.Revit.DB import Element, Wall, Floor, Ceiling
from Autodesk.Revit.DB import SpatialElement, SpatialElementGeometryCalculator
from Autodesk.Revit.DB import FilteredElementCollector, ElementId, IntersectionResult
from Autodesk.Revit.DB import SpatialElementBoundaryOptions, SpatialElementBoundaryLocation
from Autodesk.Revit.DB import BuiltInParameter, ElementIntersectsSolidFilter
from Autodesk.Revit.DB import ParameterValueProvider, FilterStringRule
from Autodesk.Revit.DB import ElementParameterFilter, FilterStringContains
from Autodesk.Revit.DB import BoundingBoxContainsPointFilter
from Autodesk.Revit.DB.Architecture import Room, RoomFilter

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List
from System.IO import Path

from collections import OrderedDict
from collections import defaultdict

########################################################################################################################

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

########################################################################################################################

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName
revit_file_name = Path.GetFileNameWithoutExtension(revit_file_path)
revit_file_name = revit_file_name.split("_detached")[0].split("_отсоединено")[0].strip()
revit_file_name = revit_file_name.encode('cp1251', 'ignore').decode('cp1251').strip()
TransactionManager.Instance.ForceCloseTransaction()


def get_room_data(doc):
    output = defaultdict(list)
    collector = FilteredElementCollector(doc).OfClass(SpatialElement).WherePasses(RoomFilter())
    for room in collector.ToElements():
        if isinstance(room, Room) and room.Volume > 0:
            elevation = room.Level.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsDouble()
            output[int(round(elevation * 0.3048))].append(room)

    return output


def get_finished_by_room(doc, room, model_group_name, options, offset=0.05):
    calculator = SpatialElementGeometryCalculator(doc, options)
    results = calculator.CalculateSpatialElementGeometry(room)
    result = []
    solid = results.GetGeometry()
    centroid = solid.ComputeCentroid()
    provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_MODEL))
    rule = FilterStringRule(provider, FilterStringContains(), model_group_name)
    group_filter, solid_filter = ElementParameterFilter(rule), ElementIntersectsSolidFilter(solid)
    elements = FilteredElementCollector(doc).WherePasses(solid_filter).WherePasses(group_filter).ToElements()
    if elements and len(elements) > 0: result.extend(elements)
    for face in solid.Faces:
        for subface in results.GetBoundaryFaceInfo(face):
            face = subface.GetSpatialElementFace()
            intersection = face.Project(centroid)
            if isinstance(intersection, IntersectionResult):
                pnt_filter = BoundingBoxContainsPointFilter(intersection.XYZPoint, offset)
                element = FilteredElementCollector(doc).WherePasses(pnt_filter).WherePasses(group_filter).FirstElement()
                if element: result.append(element)

    return result


########################################################################################################################

counter = int(0)
groupModelName = IN[0]
roomNumberParamName = IN[1]

options = SpatialElementBoundaryOptions()
options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish

levelRoomsData = OrderedDict(get_room_data(doc).items())

# Start a transaction
TransactionManager.Instance.EnsureInTransaction(doc)

for elevationInt, roomList in levelRoomsData.items():

    wallFinishingData = {}
    floorFinishingData = {}
    ceilingFinishingData = {}

    levelFinishing = List[Element]()

    for room in sorted(roomList, key=lambda r: r.Number):

        roomNumber = room.Number.strip()

        room.get_Parameter(BuiltInParameter.ROOM_FINISH_WALL).Set('')
        room.get_Parameter(BuiltInParameter.ROOM_FINISH_FLOOR).Set('')
        room.get_Parameter(BuiltInParameter.ROOM_FINISH_CEILING).Set('')

        for element in get_finished_by_room(doc, room, groupModelName, options):

            if isinstance(element, Wall):
                levelFinishing.Add(element)
                wallName = element.Name
                if room.get_Parameter(BuiltInParameter.ROOM_FINISH_WALL).Set(wallName):
                    if wallName not in wallFinishingData: wallFinishingData[wallName] = set()
                    wallFinishingData[wallName].add(roomNumber)
                    continue

            if isinstance(element, Floor):
                levelFinishing.Add(element)
                floorName = element.Name
                if room.get_Parameter(BuiltInParameter.ROOM_FINISH_FLOOR).Set(floorName):
                    if floorName not in floorFinishingData: floorFinishingData[floorName] = set()
                    floorFinishingData[floorName].add(roomNumber)
                    continue

            if isinstance(element, Ceiling):
                levelFinishing.Add(element)
                ceilingName = element.Name
                if room.get_Parameter(BuiltInParameter.ROOM_FINISH_CEILING).Set(ceilingName):
                    if ceilingName not in ceilingFinishingData: ceilingFinishingData[ceilingName] = set()
                    ceilingFinishingData[ceilingName].add(roomNumber)
                    continue

    for element in levelFinishing:
        elementName = element.Name
        if isinstance(element, Wall):
            roomNumbers = wallFinishingData.get(elementName)
            isValidSet = element.LookupParameter(roomNumberParamName).Set(", ".join(roomNumbers))
            counter += 1
            continue

        if isinstance(element, Floor):
            roomNumbers = floorFinishingData.get(elementName)
            isValidSet = element.LookupParameter(roomNumberParamName).Set(", ".join(roomNumbers))
            counter += 1
            continue

        if isinstance(element, Ceiling):
            roomNumbers = ceilingFinishingData.get(elementName)
            isValidSet = element.LookupParameter(roomNumberParamName).Set(", ".join(roomNumbers))
            counter += 1
            continue

# Commit the transaction
TransactionManager.Instance.TransactionTaskDone()

OUT = counter
