#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr

clr.AddReference('RevitAPI')

from Autodesk.Revit.DB import SpatialElement
from Autodesk.Revit.DB import FilteredElementCollector, ElementId
from Autodesk.Revit.DB import XYZ, Element, Wall, Floor, Ceiling, ViewType
from Autodesk.Revit.DB import SpatialElementBoundaryOptions, SpatialElementBoundaryLocation
from Autodesk.Revit.DB import BuiltInParameter, LogicalAndFilter
from Autodesk.Revit.DB import ParameterValueProvider, FilterStringRule
from Autodesk.Revit.DB import ElementParameterFilter, FilterStringContains
from Autodesk.Revit.DB import BoundingBoxIntersectsFilter, Outline
from Autodesk.Revit.DB.Architecture import Room, RoomFilter

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List
from System.IO import Path

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


def get_rooms_by_view(doc):
    output = list()
    active = doc.ActiveView
    if active.ViewType == ViewType.FloorPlan:
        collector = FilteredElementCollector(doc, active.Id).OfClass(SpatialElement).WherePasses(RoomFilter())
        for room in collector.ToElements():
            if isinstance(room, Room):
                if room.Volume > 0:
                    output.append(room)
    return output


def get_finished_by_room(doc, room, model_group_name):
    output = []
    bbox = room.get_BoundingBox(None)
    min_bbox = bbox.Transform.OfPoint(bbox.Min)
    max_bbox = bbox.Transform.OfPoint(bbox.Max)
    box_filter = BoundingBoxIntersectsFilter(Outline(min_bbox, max_bbox))
    provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_MODEL))
    rule = FilterStringRule(provider, FilterStringContains(), model_group_name, False)
    logic_filter = LogicalAndFilter(box_filter, ElementParameterFilter(rule))
    collector = FilteredElementCollector(doc).WherePasses(logic_filter).WhereElementIsNotElementType()
    output.extend(collector.ToElements())

    # for face in solid.Faces:
    #     for subface in results.GetBoundaryFaceInfo(face):
    #         face = subface.GetSubface()
    #         box = face.GetBoundingBox()
    #         center = (box.Max + box.Min) * 0.5
    #         point = get_center_point_of_face(face)
    #         normal = face.ComputeNormal(center).Normalize()
    #         point = point + normal * offset
    #         if isinstance(point, XYZ):
    #             pnt_filter = BoundingBoxContainsPointFilter(point, offset * 3)
    #             element = FilteredElementCollector(doc).WherePasses(pnt_filter).WherePasses(logic_filter).FirstElement()
    #             if element: output.append(element)

    return output


def get_center_point_of_face(face):
    mesh = face.Triangulate()
    count, x, y, z = 0, 0, 0, 0
    for num in range(mesh.NumTriangles):
        triangle = mesh.get_Triangle(num)
        for idx in range(3):
            vertex = triangle.get_Vertex(idx)
            x += vertex.X
            y += vertex.Y
            z += vertex.Z
            count += 1

    point = XYZ(x / count, y / count, z / count)
    return point


########################################################################################################################

counter = 0
groupModelName = IN[0]
roomNumberParamName = IN[1]

options = SpatialElementBoundaryOptions()
options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish

# Start a transaction
TransactionManager.Instance.EnsureInTransaction(doc)

wallFinishingData = {}
floorFinishingData = {}
ceilingFinishingData = {}

levelFinishing = List[Element]()

roomList = get_rooms_by_view(doc)
roomList = sorted(roomList, key=lambda r: r.Number)

for room in roomList:
    if isinstance(room, Room):

        room.get_Parameter(BuiltInParameter.ROOM_FINISH_WALL).Set('')
        room.get_Parameter(BuiltInParameter.ROOM_FINISH_FLOOR).Set('')
        room.get_Parameter(BuiltInParameter.ROOM_FINISH_CEILING).Set('')

        roomName = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()

        for element in get_finished_by_room(doc, room, groupModelName):

            if isinstance(element, Wall):
                levelFinishing.Add(element)
                wallName = element.Name
                if room.get_Parameter(BuiltInParameter.ROOM_FINISH_WALL).Set(wallName):
                    if wallName not in wallFinishingData: wallFinishingData[wallName] = set()
                    wallFinishingData[wallName].add(roomName)
                    continue

            if isinstance(element, Floor):
                levelFinishing.Add(element)
                floorName = element.Name
                if room.get_Parameter(BuiltInParameter.ROOM_FINISH_FLOOR).Set(floorName):
                    if floorName not in floorFinishingData: floorFinishingData[floorName] = set()
                    floorFinishingData[floorName].add(roomName)
                    continue

            if isinstance(element, Ceiling):
                levelFinishing.Add(element)
                ceilingName = element.Name
                if room.get_Parameter(BuiltInParameter.ROOM_FINISH_CEILING).Set(ceilingName):
                    if ceilingName not in ceilingFinishingData: ceilingFinishingData[ceilingName] = set()
                    ceilingFinishingData[ceilingName].add(roomName)
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
