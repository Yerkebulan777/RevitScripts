# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import time

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import re
import clr
import difflib
from functools import wraps
from collections import defaultdict

clr.AddReference("System")
clr.AddReference("System.Core")
import System

clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector, Level, XYZ
from Autodesk.Revit.DB import ElementId, BuiltInCategory, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB import ViewFamilyType, ViewFamily, ViewPlan, ViewDiscipline, ViewDetailLevel, DisplayStyle
from Autodesk.Revit.DB import ParameterValueProvider, FilterDoubleRule, FilterNumericGreater
from Autodesk.Revit.DB import ElementLevelFilter, ElementParameterFilter, LogicalAndFilter
from Autodesk.Revit.DB.Architecture import Room

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog

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
DICTIONARY = defaultdict(dict)
########################################################################################################################
DICTIONARY["МОП"].update({'Холл': '0'})
DICTIONARY["МОП"].update({'Лифт': '0'})
DICTIONARY["МОП"].update({'Тамбур': '0'})
DICTIONARY["МОП"].update({'Коридор': '0'})
DICTIONARY["МОП"].update({'Веранда': '0'})
DICTIONARY["МОП"].update({'Терраса': '0'})
DICTIONARY["МОП"].update({'Кладовая': '0'})
DICTIONARY["МОП"].update({'Приемная': '0'})
DICTIONARY["МОП"].update({'Ресепшен': '0'})
DICTIONARY["МОП"].update({'Вестибюль': '0'})
DICTIONARY["МОП"].update({'Ко-воркинг': '0'})
DICTIONARY["МОП"].update({'Колясочная': '0'})
DICTIONARY["МОП"].update({'Зона отдыха': '0'})
DICTIONARY["МОП"].update({'Грузовой Лифт': '0'})
DICTIONARY["МОП"].update({'Лифтовой холл': '0'})
DICTIONARY["МОП"].update({'Общий коридор': '0'})
DICTIONARY["МОП"].update({'Комната отдыха': '0'})
DICTIONARY["МОП"].update({'Воздушная Зона': '0'})
DICTIONARY["МОП"].update({'Пассажирский лифт': '0'})
DICTIONARY["МОП"].update({'Лестничная клетка': '0'})
DICTIONARY["МОП"].update({'Лестничная площадка': '0'})
DICTIONARY["МОП"].update({'Встроенное помещение': '0'})
DICTIONARY["МОП"].update({'Межквартирный коридор': '0'})
DICTIONARY["МОП"].update({'Внеквартирный коридор': '0'})
DICTIONARY["МОП"].update({'Грузо-пассажирский лифт': '0'})
DICTIONARY["МОП"].update({'Лестнично-лифтовой холл': '0'})
########################################################################################################################
DICTIONARY["Офис"].update({'ПУИ': '3'})
DICTIONARY["Офис"].update({'С/y': '3'})
DICTIONARY["Офис"].update({'Офис': '3'})
DICTIONARY["Офис"].update({'Холл': '3'})
DICTIONARY["Офис"].update({'Шлюз': '3'})
DICTIONARY["Офис"].update({'Тамбур': '3'})
DICTIONARY["Офис"].update({'Кабинет': '3'})
DICTIONARY["Офис"].update({'Приемная': '3'})
DICTIONARY["Офис"].update({'Ресепшен': '3'})
DICTIONARY["Офис"].update({'Кладовая': '3'})
DICTIONARY["Офис"].update({'Кинотеатр': '3'})
DICTIONARY["Офис"].update({'Конференц зал': '3'})
DICTIONARY["Офис"].update({'Помещения коммерческой зоны': '3'})
########################################################################################################################
DICTIONARY["Пракинг"].update({'ПУИ': '4'})
DICTIONARY["Пракинг"].update({'Бокс': '4'})
DICTIONARY["Пракинг"].update({'Пракинг': '4'})
DICTIONARY["Пракинг"].update({'Насосная': '4'})
DICTIONARY["Пракинг"].update({'Пост охраны': '4'})
DICTIONARY["Пракинг"].update({'Комната охраны': '4'})
DICTIONARY["Пракинг"].update({'Место для велосипедов': '4'})
########################################################################################################################
DICTIONARY["Квартира"].update({'С/y': '1'})
DICTIONARY["Квартира"].update({'Холл': '1'})
DICTIONARY["Квартира"].update({'Ниша': '1'})
DICTIONARY["Квартира"].update({'Кухня': '1'})
DICTIONARY["Квартира"].update({'Ванная': '1'})
DICTIONARY["Квартира"].update({'Балкон': '1'})
DICTIONARY["Квартира"].update({'Лоджия': '1'})
DICTIONARY["Квартира"].update({'Спальня': '1'})
DICTIONARY["Квартира"].update({'Кабинет': '1'})
DICTIONARY["Квартира"].update({'Коридор': '1'})
DICTIONARY["Квартира"].update({'Веранда': '1'})
DICTIONARY["Квартира"].update({'Терраса': '1'})
DICTIONARY["Квартира"].update({'Столовая': '1'})
DICTIONARY["Квартира"].update({'Гардероб': '1'})
DICTIONARY["Квартира"].update({'Гостиная': '1'})
DICTIONARY["Квартира"].update({'Прихожая': '1'})
DICTIONARY["Квартира"].update({'Гостевая': '1'})
DICTIONARY["Квартира"].update({'Гостиная': '1'})
DICTIONARY["Квартира"].update({'Библиотека': '1'})
DICTIONARY["Квартира"].update({'Кухня ниша': '1'})
DICTIONARY["Квартира"].update({'Постирочная': '1'})
DICTIONARY["Квартира"].update({'Ниша гардероб': '1'})
DICTIONARY["Квартира"].update({'Кухонная зона': '1'})
DICTIONARY["Квартира"].update({'Лоджия балкон': '1'})
DICTIONARY["Квартира"].update({'Мастер спальня': '1'})
DICTIONARY["Квартира"].update({'Кухня столовая': '1'})
DICTIONARY["Квартира"].update({'Детская спальня': '1'})
DICTIONARY["Квартира"].update({'Гостевая спальня': '1'})
DICTIONARY["Квартира"].update({'Зона приема пищи': '1'})
DICTIONARY["Квартира"].update({'Гостиная столовая': '1'})
########################################################################################################################
DICTIONARY["Кладовка"].update({'Кладовая': '5'})
DICTIONARY["Кладовка"].update({'Хранение': '5'})
DICTIONARY["Кладовка"].update({'Экспидиция': '5'})
########################################################################################################################
DICTIONARY["Тех.помещение"].update({'ПУИ': '00'})
DICTIONARY["Тех.помещение"].update({'ИТП': '00'})
DICTIONARY["Тех.помещение"].update({'Душевая': '00'})
DICTIONARY["Тех.помещение"].update({'Насосная': '00'})
DICTIONARY["Тех.помещение"].update({'Мастерская': '00'})
DICTIONARY["Тех.помещение"].update({'Вент.Камера': '00'})
DICTIONARY["Тех.помещение"].update({'Тамбур-Шлюз': '00'})
DICTIONARY["Тех.помещение"].update({'Тех.коридор': '00'})
DICTIONARY["Тех.помещение"].update({'Операторская': '00'})
DICTIONARY["Тех.помещение"].update({'Тех.подполье': '00'})
DICTIONARY["Тех.помещение"].update({'Насосная АТП': '00'})
DICTIONARY["Тех.помещение"].update({'Тех.помещение': '00'})
DICTIONARY["Тех.помещение"].update({'Тепловой Пункт': '00'})
DICTIONARY["Тех.помещение"].update({'Электрощитовая': '00'})
DICTIONARY["Тех.помещение"].update({'Комната Охраны': '00'})
DICTIONARY["Тех.помещение"].update({'Помещение сервиса': '00'})
DICTIONARY["Тех.помещение"].update({'Насосная хоз. пит.': '00'})
DICTIONARY["Тех.помещение"].update({'Воздухозаборная камера': '00'})
DICTIONARY["Тех.помещение"].update({'Помещение тех.персонала': '00'})
DICTIONARY["Тех.помещение"].update({'Инвентарная для клининга': '00'})
DICTIONARY["Тех.помещение"].update({'Помещение JET вентиляции': '00'})
########################################################################################################################

########################################################################################################################
regex = re.compile(r"([+*^#%!?@$&£\\\[\]{}|/;:<>`~]|\d*)")


########################################################################################################################
def get_rooms_by_level(level):
    double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_AREA))
    double_rul = FilterDoubleRule(double_pvp, FilterNumericGreater(), 0.5, 0.005)
    level_filter, param_filter = ElementLevelFilter(level.Id), ElementParameterFilter(double_rul)
    collector = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Rooms)
    rooms = collector.WherePasses(LogicalAndFilter(level_filter, param_filter)).ToElements()
    rooms = sorted(rooms, key=lambda x: x.Area)
    return rooms


def get_doorIds_by_room(room, view):
    result, roomIdInt = [], room.Id.IntegerValue
    level_filter = ElementLevelFilter(room.Level.Id)
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors)
    phase = doc.GetElement(view.get_Parameter(BuiltInParameter.VIEW_PHASE).AsElementId())
    for door in collector.WherePasses(level_filter).WhereElementIsNotElementType().ToElements():
        rmn = door.ToRoom[phase]
        if isinstance(rmn, Room):
            if rmn.Id.IntegerValue == roomIdInt:
                result.append(door.Id)
        rmn = door.FromRoom[phase]
        if isinstance(rmn, Room):
            if rmn.Id.IntegerValue == roomIdInt:
                result.append(door.Id)
    return result


# def get_room_groups(departments, rooms):
#     groups, setIds = [], set()
#     dictionary = dict(sorted(zip(departments, rooms), key=lambda x: x[0]))
#     for department, room in dictionary.iteritems():
#         roomId = room.Id
#         if room.Id in setIds: continue
#         doorIds = get_doorIds_by_room(room)
#         intersects = [rmn for dep, rmn in dictionary.items() if department == dep and roomId != rmn.Id]
#         intersects = [rmn for rmn in intersects for door in get_doorIds_by_room(rmn) if door.Id in doorIds]
#         groups.append(intersects)
#         count = len(intersects)
#         setIds.add(roomId)
#         for rmn in intersects:
#             param = get_element_shared_parameter(doc, rmn, "BI_количество_комнат")
#             if param and not param.IsReadOnly: param.Set(count)
#     return groups


def get_center_point(elements):
    elements = (elements if isinstance(elements, list) else [elements])
    boxes = (elem.get_BoundBox(None) for elem in elements if elem)
    center = [XYZ((box.Min + box.Max) * 0.5) for box in boxes]
    return center


def defined_rooms(rooms, view):
    groupDictIds = defaultdict(dict)
    intersectDoorIds = defaultdict(set)
    if isinstance(rooms, list) and len(rooms):
        elevation = rooms[0].Level.ProjectElevation
        for room in rooms:
            roomId = room.Id
            area = float(room.Area / 304.8)
            doorIds = get_doorIds_by_room(room, view)
            intersectDoorIds[roomId].add(doorIds)
            """ определить высоту этажа и установить """
            """ найти лестничную клетку по дверям и лестнице или объему и окну """
            """ https://codemg.ru/geometry/storona_pryamougolnika.php (соотношение / сторон) """
            """ определить по боксу диагональ больших помещений - коридор - вывести длину по периметру """
            """ найти ближайшие маленькие комнаты по дверям и расстоянию """
            """ определить назнечение по площади и по этажу помещения """
            """ определить тамбуры и лифты по площади двери и нет окон """
            """ если дверей больше 3x тогда коридор, если больше 5-ти тогда МОП коридор"""
            """ для квартиры  определить по площади (гостиннная, прихожая, кухня, санузел, спальня, балкон) """
            """ для квартиры  определить жилые комнаты по площади окон """
            """ найденные данные вывести в словарь """
        return groupDictIds


########################################################################################################################
message = "Undefined rooms:\n"
########################################################################################################################
view = FilteredElementCollector(doc).OfClass(ViewPlan).FirstElement()
levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
levels = sorted(levels, key=lambda x: x.Elevation)
for level in levels:
    rooms = get_rooms_by_level(level)
    if rooms and len(rooms):
        message += "\n\n\nLevel: {}\n".format(level.Name)
        for room in rooms:
            if room.IsValidObject:
                pass
########################################################################################################################
OUT = message
########################################################################################################################
