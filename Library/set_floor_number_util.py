#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
from shared_parameter_util import get_shared_parameter
import re
import clr

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import WorksharingUtils
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import XYZ, Grid, UnitUtils, DisplayUnitType, Transform
from Autodesk.Revit.DB import SharedParameterElement, StorageType
from Autodesk.Revit.DB import FilterNumericLessOrEqual, FilterNumericGreaterOrEqual
from Autodesk.Revit.DB import ExclusionFilter, Outline
from Autodesk.Revit.DB import BoundingBoxXYZ, BoundingBoxIntersectsFilter, LogicalOrFilter
from Autodesk.Revit.DB import ElementId, Level, FamilyInstance, Structure, Floor
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter
from Autodesk.Revit.DB import LogicalAndFilter, ElementMulticategoryFilter, ElementLevelFilter
from Autodesk.Revit.DB import SharedParameterApplicableRule, FilterNumericEquals
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter
from Autodesk.Revit.DB import FilterDoubleRule, FilterIntegerRule, FilterStringRule
from Autodesk.Revit.DB import FilterStringContains
from Autodesk.Revit.DB import FilterElementIdRule


########################################################################################################################
########################################################################################################################
def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def get_internal_guid_by_name(doc, parameter_name):
    external = get_external_definition(doc, parameter_name)
    if bool(external and SharedParameterElement.Lookup(doc, external.GUID)):
        return external.GUID


def get_unique_listId(elemnetIdlist):
    mmap, uniques = {}, List[ElementId]()
    for elementId in elemnetIdlist:
        if elementId not in mmap:
            mmap[elementId] = 1
            uniques.Add(elementId)
    return uniques


def get_levelId_by_name(doc, level_name):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.DATUM_TEXT))
    name_filter = ElementParameterFilter(FilterStringRule(provider, FilterStringContains(), level_name, False))
    levelId = FilteredElementCollector(doc).OfClass(Level).WherePasses(name_filter).FirstElementId()
    return levelId


def get_valid_levels(doc):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    floor_rule = FilterDoubleRule(provider, FilterNumericLessOrEqual(), float(300), 0.0005)
    levels = FilteredElementCollector(doc).OfClass(Level).WherePasses(ElementParameterFilter(floor_rule)).ToElements()
    levels = sorted(levels, key=lambda x: x.Elevation)
    return levels


def get_average_level_height(levels):
    elevations = [x.Elevation for x in levels]
    height = (max(elevations) - min(elevations)) / len(levels)
    height = (round(height * 304.8 / 300) * 300 / 304.8)
    min_height, max_height = (2500 / 304.8), (4500 / 304.8)
    height = (min_height if height < min_height else height)
    height = (max_height if height > max_height else height)
    return height


def get_above_level_and_height(doc, level, levels):
    elevation, average = level.Elevation, get_average_level_height(levels)
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    rule_min = FilterDoubleRule(provider, FilterNumericGreaterOrEqual(), float(elevation), 0.005)
    rule_max = FilterDoubleRule(provider, FilterNumericLessOrEqual(), float(elevation + average * 3), 0.005)
    logic_filter = LogicalAndFilter(ElementParameterFilter(rule_min), ElementParameterFilter(rule_max))
    levels = FilteredElementCollector(doc).OfClass(Level).WherePasses(logic_filter).ToElements()
    levels = list(level for level in levels if elevation <= level.Elevation)
    levels = sorted(levels, key=lambda x: x.ProjectElevation)
    above = (level if len(levels) == 1 else levels[1])
    height = float(above.Elevation - level.Elevation)
    return above, height


def get_level_number(level, levels):
    elevator, top = float(0), int(len(levels) - 3)
    levelId, number = level.Id.IntegerValue, int(0)
    value = level.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsDouble()
    datum_name = level.Name.encode('cp1251', 'ignore').decode('cp1251').strip()
    datum_name = ''.join(filter(lambda i: i.isalpha() or i.isspace(), datum_name))
    elevation = round(UnitUtils.ConvertFromInternalUnits(value, DisplayUnitType.DUT_METERS))
    if elevation > 5 and re.search(r"\b(Будка)\b", datum_name, re.UNICODE | re.IGNORECASE): return int(101)
    if elevation > 5 and re.search(r"\b(Кровля)\b", datum_name, re.UNICODE | re.IGNORECASE): return int(100)
    if elevation > 5 and re.search(r"\b(Чердак)\b", datum_name, re.UNICODE | re.IGNORECASE): return int(99)
    levels = sorted(levels, key=lambda x: x.Elevation)
    undeground = bool(elevation < 0)
    if undeground: reversed(levels)
    for current in levels:
        currentId = current.Id.IntegerValue
        currentName = current.Name.encode('ascii', 'ignore')
        dumber = ''.join(filter(lambda i: i.isdigit(), currentName))
        value = level.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsDouble()
        dumber = int(dumber if (not undeground and dumber and int(dumber) < top) else number)
        elevation = round(UnitUtils.ConvertFromInternalUnits(value, DisplayUnitType.DUT_METERS))
        calculate = (True if not dumber and abs(elevation - elevator) > 1.8 else False)
        number = int(dumber if (not undeground and not calculate) else number)
        if (calculate and elevation > 0): number += 1
        if (calculate and elevation < 0): number -= 1
        if (elevation == 0): number = 1
        if currentId == levelId: break
        elevator = elevation
    return number


def get_level_by_elevation(doc, elevation, average):
    provide = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    rule_min = FilterDoubleRule(provide, FilterNumericGreaterOrEqual(), float(elevation), 0.05)
    rule_max = FilterDoubleRule(provide, FilterNumericLessOrEqual(), float(elevation + average), 0.05)
    logic_filter = LogicalAndFilter(ElementParameterFilter(rule_min), ElementParameterFilter(rule_max))
    level = FilteredElementCollector(doc).OfClass(Level).WherePasses(logic_filter).FirstElement()
    return level


def get_system_elementIds_by_level(doc, level):
    builtInCats = List[BuiltInCategory]()
    level_filter = ElementLevelFilter(level.Id)
    builtInCats.Add(BuiltInCategory.OST_Roofs)
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_Ramps)
    category_filter = ElementMulticategoryFilter(builtInCats)
    logic_filter = LogicalAndFilter(level_filter, category_filter)
    collector = FilteredElementCollector(doc).WherePasses(logic_filter)
    result = collector.WhereElementIsNotElementType().ToElementIds()
    return result


def get_floorIds_by_level(doc, above, level):
    level00, level01 = ElementLevelFilter(above.Id), ElementLevelFilter(level.Id)
    provider = ParameterValueProvider(ElementId(BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL))
    filter00 = ElementParameterFilter(FilterIntegerRule(provider, FilterNumericEquals(), 1))
    filter01 = ElementParameterFilter(FilterIntegerRule(provider, FilterNumericEquals(), 0))
    floor_filter = LogicalOrFilter(LogicalAndFilter(level00, filter00), LogicalAndFilter(level01, filter01))
    collector = FilteredElementCollector(doc).OfClass(Floor).WherePasses(floor_filter)
    result = collector.WhereElementIsNotElementType().ToElementIds()
    return result


def get_host_rebar_familyIds_by_level(doc, level):
    lvl_filter = ElementLevelFilter(level.Id)
    rht_provider = ParameterValueProvider(ElementId(BuiltInParameter.FAMILY_CAN_HOST_REBAR))
    filter_host = ElementParameterFilter(FilterIntegerRule(rht_provider, FilterNumericEquals(), 1))
    collector = FilteredElementCollector(doc).OfClass(FamilyInstance).WherePasses(lvl_filter)
    collector = collector.WherePasses(filter_host).WhereElementIsViewIndependent()
    result = collector.WhereElementIsNotElementType().ToElementIds()
    return result


def get_rebarIds_by_structural(doc, element_ids):
    rebarIds = set()
    hostData = Structure.RebarHostData
    provider = ParameterValueProvider(ElementId(int(BuiltInParameter.HOST_ID_PARAM)))
    for elemId in get_unique_listId(element_ids):
        element = doc.GetElement(elemId)
        if element.IsValidObject:
            host = hostData.GetRebarHostData(element)
            rule = FilterElementIdRule(provider, FilterNumericEquals(), elemId)
            if host: rebarIds.update([rbr.Id for rbr in host.GetRebarsInHost()])
            collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_AreaRein)
            reins = collector.WherePasses(ElementParameterFilter(rule)).ToElements()
            if reins: [rebarIds.update(arn.GetRebarInSystemIds()) for arn in reins]
    return rebarIds


def get_level_by_element(doc, element, levels, average=7):
    bbox = element.get_BoundingBox(None)
    if isinstance(bbox, BoundingBoxXYZ):
        center = (bbox.Min + bbox.Max) * 0.5
        result, value = None, center.Z
        level = get_level_by_elevation(doc, value, average)
        if level: return level
        for current in levels:
            elevation = current.ProjectElevation
            if (elevation > value): break
            result = current
        return result


def set_value_to_elements(doc, guid, element_ids, value):
    length, counts = int(0), int(0)
    element_ids = WorksharingUtils.CheckoutElements(doc, element_ids)
    if len(element_ids):
        for elementId in element_ids:
            element = doc.GetElement(elementId)
            if element.IsValidObject:
                result, param = None, element.get_Parameter(guid)
                ungroup = element.GroupId.Equals(ElementId.InvalidElementId)
                if ungroup and param:
                    length += 1
                    if param.StorageType == StorageType.String:
                        value = (value if isinstance(value, basestring) else str(value))
                        if param.IsReadOnly and param.HasValue: continue
                        try:
                            param.Set(value)
                            counts += 1
                        except:
                            pass
                    if param.StorageType == StorageType.Integer:
                        value = (value if isinstance(value, int) else int(value))
                        if param.IsReadOnly and param.HasValue: continue
                        try:
                            param.Set(value)
                            counts += 1
                        except:
                            pass
        message = "Set values in {} out of {} items\n".format(counts, length)
        return message


def check_floor_number(doc, parameter_name):
    guid = get_internal_guid_by_name(doc, parameter_name)
    parameter = SharedParameterElement.Lookup(doc, guid)
    message, provide = "", ParameterValueProvider(parameter.Id)
    parameter_filter = ElementParameterFilter(SharedParameterApplicableRule(parameter_name))
    value_filter = ElementParameterFilter(FilterIntegerRule(provide, FilterNumericEquals(), 0))
    collector = FilteredElementCollector(doc).WherePasses(parameter_filter).WherePasses(value_filter)
    undefinedIds = collector.WhereElementIsViewIndependent().WhereElementIsNotElementType().ToElementIds()
    if len(undefinedIds): set_value_to_elements(doc, guid, undefinedIds, 689)
    message = "\nNot defined {} elements count\n".format(len(undefinedIds))
    return message


def set_num_generator(doc, parameter_name, transform, levels, average, min_x, max_x, min_y, max_y):
    gridsIds = FilteredElementCollector(doc).OfClass(Grid).WhereElementIsNotElementType().ToElementIds()
    filter = ElementParameterFilter(SharedParameterApplicableRule(parameter_name))
    guid = get_internal_guid_by_name(doc, parameter_name)
    includeIds = List[ElementId]()
    includeIds.AddRange(gridsIds)
    for idx, level in enumerate(levels):
        setIds = set()
        number = get_level_number(level, levels)
        above, height = get_above_level_and_height(doc, level, levels)
        height = float(average if (height < average * 0.5) else height)
        height_in_meter = float(round(height * 304.8) / 1000)
        level_name = level.Name.encode('cp1251', 'ignore').decode('cp1251').strip()
        message = "\n{}) {} defined as {} number (H={}m)\n".format(idx, level_name, number, height_in_meter)
        #####################################################
        setIds.update(get_system_elementIds_by_level(doc, level))
        setIds.update(get_floorIds_by_level(doc, above, level))
        setIds.update(get_host_rebar_familyIds_by_level(doc, level))
        setIds.update(get_rebarIds_by_structural(doc, setIds))
        ######################################################
        offset = float(average if number < 0 else 0.5)
        min_elev = float(level.ProjectElevation - offset)
        max_elev = float(level.ProjectElevation + height - 0.5)
        min_point = transform.OfPoint(XYZ((min_x), (min_y), (min_elev)))
        max_point = transform.OfPoint(XYZ((max_x), (max_y), (max_elev)))
        bbox_filter = BoundingBoxIntersectsFilter(Outline(min_point, max_point))
        collector = FilteredElementCollector(doc).WherePasses(bbox_filter).WherePasses(filter)
        if len(includeIds): collector = collector.WherePasses(ExclusionFilter(includeIds))
        setIds.update(collector.WhereElementIsViewIndependent().ToElementIds())
        collectionIds = get_unique_listId(setIds)
        if len(collectionIds):
            message += set_value_to_elements(doc, guid, collectionIds, number)
            includeIds.AddRange(collectionIds)
            doc.Regenerate()
        yield message


########################################################################################################################
########################################################################################################################
########################################################################################################################
def set_floor_number(doc, parameter_name="BI_этаж"):
    levels = get_valid_levels(doc)
    average = get_average_level_height(levels)
    points, transform = set(), Transform.Identity
    message = "\nAverage height: {}\n".format(round(average * 304.8))
    filepath = r"D:\YandexDisk\RevitExportConfig\DataBase\BI_FOP.txt"
    get_shared_parameter(doc, filepath, parameter_name, 'PG_GENERAL')
    grids = FilteredElementCollector(doc).OfClass(Grid).WhereElementIsNotElementType().ToElements()
    if len(grids): points.update(grid.Curve.GetEndPoint(0) for grid in grids)
    if len(grids): points.update(grid.Curve.GetEndPoint(1) for grid in grids)
    min_x = round(min(p.X for p in points) - 30) if len(grids) else float(-500)
    max_x = round(max(p.X for p in points) + 30) if len(grids) else float(1000)
    min_y = round(min(p.Y for p in points) - 30) if len(grids) else float(-500)
    max_y = round(max(p.Y for p in points) + 30) if len(grids) else float(1000)
    with Transaction(doc, "Set floor number") as trans:
        if len(levels):
            trans.Start()
            msgs = set_num_generator(doc, parameter_name, transform, levels, average, min_x, max_x, min_y, max_y)
            message += "\r\n\t".join(sms for key, sms in enumerate(msgs))
            message += check_floor_number(doc, parameter_name)
            trans.Commit()
    return message
########################################################################################################################
########################################################################################################################
########################################################################################################################
