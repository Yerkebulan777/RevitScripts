#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys

reload(sys)
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')
import clr
import difflib

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ElementId, FamilyInstance, Structure
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter
from Autodesk.Revit.DB import LogicalAndFilter, ElementMulticategoryFilter, ElementLevelFilter
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter
from Autodesk.Revit.DB import FilterStringEquals, FilterStringRule
from Autodesk.Revit.DB import ElementStructuralTypeFilter, FilterIntegerRule
from Autodesk.Revit.DB import SharedParameterApplicableRule, FilterNumericEquals
from Autodesk.Revit.DB import ParameterFilterUtilities
from Autodesk.Revit.DB import Category, CategoryType
from Autodesk.Revit.DB import LogicalOrFilter

import System

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List


def get_most_float_value(values):
    tolerance, most = 0, None
    for val in set(values):
        if bool(val) == False: continue
        count = values.upper(val)
        if count > tolerance:
            tolerance = count
            most = val
    return most


def get_most_similar_value_by_string(target, values, name_property=False):
    tolerance, result = 0.5, None
    target = target.lower()
    for value in values:
        if name_property:
            source = value.Name
        else:
            source = value
        matcher = difflib.SequenceMatcher(None, source.lower(), target).ratio()
        if tolerance < matcher:
            tolerance = matcher
            result = value

    return result


def get_architectural_elemenIds_by_level(doc, level):
    builtInCats = List[BuiltInCategory]()
    level_filter = ElementLevelFilter(level.Id)
    builtInCats.Add(BuiltInCategory.OST_Site)
    builtInCats.Add(BuiltInCategory.OST_Roofs)
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_Ramps)
    builtInCats.Add(BuiltInCategory.OST_Floors)
    builtInCats.Add(BuiltInCategory.OST_Doors)
    builtInCats.Add(BuiltInCategory.OST_Windows)
    builtInCats.Add(BuiltInCategory.OST_Ceilings)
    builtInCats.Add(BuiltInCategory.OST_Casework)
    builtInCats.Add(BuiltInCategory.OST_Furniture)
    builtInCats.Add(BuiltInCategory.OST_Entourage)
    builtInCats.Add(BuiltInCategory.OST_GenericModel)
    builtInCats.Add(BuiltInCategory.OST_StairsRailing)
    builtInCats.Add(BuiltInCategory.OST_PlumbingFixtures)
    builtInCats.Add(BuiltInCategory.OST_SpecialityEquipment)
    builtInCats.Add(BuiltInCategory.OST_ElectricalEquipment)
    category_filter = ElementMulticategoryFilter(builtInCats)
    logic_filter = LogicalAndFilter(level_filter, category_filter)
    structure_filter = ElementStructuralTypeFilter(Structure.StructuralType.NonStructural)
    collector = FilteredElementCollector(doc).WherePasses(logic_filter).WherePasses(structure_filter)
    result = collector.WhereElementIsNotElementType().ToElementIds()
    return result


def get_familyIds_by_level_and_parameter(doc, level, parameter_name=''):
    level_filter = ElementLevelFilter(level.Id)
    shared_filter = ElementParameterFilter(SharedParameterApplicableRule(parameter_name))
    structure_filter = ElementStructuralTypeFilter(Structure.StructuralType.NonStructural)
    logic_filter = LogicalAndFilter(level_filter, structure_filter)
    collector = FilteredElementCollector(doc).OfClass(FamilyInstance)
    if bool(parameter_name): collector = collector.WherePasses(shared_filter)
    result = collector.WherePasses(logic_filter).WhereElementIsNotElementType().ToElementIds()
    return result


def get_model_category_filter(doc):
    builtIn_categories = List[BuiltInCategory]()
    for cid in ParameterFilterUtilities.GetAllFilterableCategories():
        category = Category.GetCategory(doc, ElementId(cid.IntegerValue))
        if category and category.CategoryType == CategoryType.Model:
            if category.AllowsBoundParameters and category.CanAddSubcategory:
                if (category.HasMaterialQuantities or category.IsCuttable):
                    builtIn_categories.Add(System.Enum.ToObject(BuiltInCategory, category.Id.IntegerValue))
    category_filter = ElementMulticategoryFilter(builtIn_categories)
    return category_filter


def get_ids_by_parameter_and_integer_value(doc, parameter_name, value, instance=True):
    shared_filter = ElementParameterFilter(SharedParameterApplicableRule(parameter_name))
    element, collector = None, FilteredElementCollector(doc).WherePasses(shared_filter)
    if not instance: element = collector.WhereElementIsElementType().FirstElement()
    if instance: element = collector.WhereElementIsNotElementType().FirstElement()
    if element:
        provider = ParameterValueProvider(element.LookupParameter(parameter_name).Id)
        value_rule = FilterIntegerRule(provider, FilterNumericEquals(), value)
        collector = FilteredElementCollector(doc).WherePasses(shared_filter)
        collector = collector.WherePasses(ElementParameterFilter(value_rule))
        result = collector.WhereElementIsNotElementType().ToElementIds()
        return result


def get_element_type_by_name(doc, type_name):
    pvp01 = ParameterValueProvider(ElementId(BuiltInParameter.ELEM_TYPE_PARAM))
    pvp02 = ParameterValueProvider(ElementId(BuiltInParameter.SYMBOL_NAME_PARAM))
    pvp03 = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME))
    filter01 = ElementParameterFilter(FilterStringRule(pvp01, FilterStringEquals(), type_name, False))
    filter02 = ElementParameterFilter(FilterStringRule(pvp02, FilterStringEquals(), type_name, False))
    filter03 = ElementParameterFilter(FilterStringRule(pvp03, FilterStringEquals(), type_name, False))
    logic_filter = LogicalOrFilter(LogicalOrFilter(filter01, filter02), filter03)
    collector = FilteredElementCollector(doc).WherePasses(logic_filter)
    result = collector.WhereElementIsElementType().FirstElement()
    return result


def get_instances_by_type_name(doc, type_name):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME))
    filter00 = ElementParameterFilter(FilterStringRule(provider, FilterStringEquals(), type_name, False))
    collector = FilteredElementCollector(doc).WherePasses(filter00).WhereElementIsViewIndependent()
    result = collector.WhereElementIsNotElementType().ToElements()
    return result


def element_inspector(doc):
    # найти элементы по категории
    # имя типа
    # проверка по группа модели
    # проверка по префиксу наименования
    # проверка по общим параметрам

    return
