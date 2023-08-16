#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr

clr.AddReference('RevitAPI')

from Autodesk.Revit.DB import FilteredElementCollector, SpatialElement, Transform
from Autodesk.Revit.DB import BuiltInParameter, LogicalAndFilter, ElementIntersectsSolidFilter
from Autodesk.Revit.DB import Element, Solid, SolidUtils, Wall, Floor, Ceiling
from Autodesk.Revit.DB import ElementMulticategoryFilter, BuiltInCategory
from Autodesk.Revit.DB.Architecture import Room, RoomFilter

clr.AddReference("System")
clr.AddReference("System.Core")
from collections import OrderedDict
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

counter = int(0)
groupFinishName = IN[0]
roomNumberParamName = IN[1]

transform = Transform.Identity


def getRoomSolid(room):
    for geometry in room.ClosedShell:
        if isinstance(geometry, Solid):
            return geometry


########################################################################################################################

levelRoomsDict = OrderedDict()

builtInCats = [BuiltInCategory.OST_Walls, BuiltInCategory.OST_Floors, BuiltInCategory.OST_Ceilings]
multiCatFilter = ElementMulticategoryFilter(List[BuiltInCategory](builtInCats))

collector = FilteredElementCollector(doc).OfClass(SpatialElement).WherePasses(RoomFilter())
for room in collector.ToElements():
    if isinstance(room, Room) and room.Area > 0:
        levelName = room.Level.Name.strip()
        if levelName not in levelRoomsDict:
            levelRoomsDict[levelName] = []
        levelRoomsDict[levelName].append(room)

# Start a transaction
TransactionManager.Instance.EnsureInTransaction(doc)

for levelName, roomList in levelRoomsDict.items():

    wallFinishingData = {}
    floorFinishingData = {}
    ceilingFinishingData = {}

    levelFinishing = List[Element]()

    roomList = sorted(roomList, key=lambda r: r.Number)

    for room in roomList:
        solid = getRoomSolid(room)
        roomNumber = room.Number.strip()
        room.get_Parameter(BuiltInParameter.ROOM_FINISH_WALL).Set('')
        room.get_Parameter(BuiltInParameter.ROOM_FINISH_FLOOR).Set('')
        room.get_Parameter(BuiltInParameter.ROOM_FINISH_CEILING).Set('')
        if roomNumber and isinstance(solid, Solid):
            roomSolid = SolidUtils.CreateTransformed(solid, transform)
            logicFilter = LogicalAndFilter(ElementIntersectsSolidFilter(roomSolid), multiCatFilter)
            intersections = FilteredElementCollector(doc).WherePasses(logicFilter).ToElements()

            for element in intersections:

                if isinstance(element, Wall):
                    wallType = element.WallType
                    group = wallType.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL).AsString()
                    if group and groupFinishName.Equals(group):
                        levelFinishing.Add(element)
                        wallName = element.Name
                        if room.get_Parameter(BuiltInParameter.ROOM_FINISH_WALL).Set(wallName):
                            if wallName not in wallFinishingData:
                                wallFinishingData[wallName] = set()
                            wallFinishingData[wallName].add(roomNumber)

                elif isinstance(element, Floor):
                    floorType = element.FloorType
                    group = floorType.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL).AsString()
                    if group and groupFinishName.Equals(group):
                        levelFinishing.Add(element)
                        floorName = element.Name
                        if room.get_Parameter(BuiltInParameter.ROOM_FINISH_FLOOR).Set(floorName):
                            if floorName not in floorFinishingData:
                                floorFinishingData[floorName] = set()
                            floorFinishingData[floorName].add(roomNumber)

                elif isinstance(element, Ceiling):
                    levelFinishing.Add(element)
                    ceilingName = element.Name
                    if room.get_Parameter(BuiltInParameter.ROOM_FINISH_CEILING).Set(ceilingName):
                        if ceilingName not in ceilingFinishingData:
                            ceilingFinishingData[ceilingName] = set()
                        ceilingFinishingData[ceilingName].add(roomNumber)

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
