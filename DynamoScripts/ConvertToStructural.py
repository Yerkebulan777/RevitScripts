#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import Structure
from Autodesk.Revit.DB import IFailuresPreprocessor
from Autodesk.Revit.DB import ElementStructuralTypeFilter
from Autodesk.Revit.DB import Group, GroupType, WallType, CategoryType
from Autodesk.Revit.DB import FailureSeverity, FailureProcessingResult
from Autodesk.Revit.DB import Transaction, BuiltInParameter, BuiltInCategory
from Autodesk.Revit.DB import ElementId, Floor, FilteredElementCollector, SpatialElement
from Autodesk.Revit.DB import FilterStringContains, FilterNumericLessOrEqual, FilterNumericGreaterOrEqual
from Autodesk.Revit.DB import FilterDoubleRule, FilterStringRule, LogicalAndFilter, LogicalOrFilter
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter, ElementFilter

clr.AddReference('RevitNodes')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


class warning_dismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        for failure in failuresAccessor.GetFailureMessages():
            fail_severity = failure.GetSeverity()
            if (fail_severity == FailureSeverity.Error):
                failuresAccessor.DeleteWarning(failure)
        return FailureProcessingResult.Continue


def ungroup_group_elements(doc):
    with Transaction(doc, "Ungroup elements") as trans:
        trans.Start()
        count = int(0)
        collector = FilteredElementCollector(doc).OfClass(GroupType)
        for group_type in collector.OfCategory(BuiltInCategory.OST_IOSModelGroups):
            if isinstance(group_type, GroupType):
                count += len([group.UngroupMembers() for group in group_type.Groups])
        trans.Commit()
    message = "\nUngroup {} elements".format(count)
    return message


def get_architect_wallIds(doc, width=float(120 / 304.8)):
    filter_list = List[ElementFilter]()

    structure_filter = ElementStructuralTypeFilter(Structure.StructuralType.NonStructural)

    model_group_provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_MODEL))
    part_group_rule = FilterStringRule(model_group_provider, FilterStringContains(), "Перегородки", False)
    finish_group_rule = FilterStringRule(model_group_provider, FilterStringContains(), "Отделка", False)
    glass_group_rule = FilterStringRule(model_group_provider, FilterStringContains(), "Витраж", False)

    type_provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME))
    type_rule_00 = FilterStringRule(type_provider, FilterStringContains(), "перегородки", False)
    type_rule_01 = FilterStringRule(type_provider, FilterStringContains(), "утеплитель", False)
    type_rule_02 = FilterStringRule(type_provider, FilterStringContains(), "газоблок", False)
    type_rule_03 = FilterStringRule(type_provider, FilterStringContains(), "отделка", False)
    type_rule_04 = FilterStringRule(type_provider, FilterStringContains(), "кирпич", False)
    type_rule_05 = FilterStringRule(type_provider, FilterStringContains(), "картон", False)
    type_rule_06 = FilterStringRule(type_provider, FilterStringContains(), "гипс", False)

    provider = ParameterValueProvider(ElementId(BuiltInParameter.WALL_ATTR_WIDTH_PARAM))
    width_rule = FilterDoubleRule(provider, FilterNumericLessOrEqual(), width, 0.0005)

    filter_list.Add(ElementParameterFilter(finish_group_rule))
    filter_list.Add(ElementParameterFilter(glass_group_rule))
    filter_list.Add(ElementParameterFilter(part_group_rule))
    filter_list.Add(ElementParameterFilter(type_rule_00))
    filter_list.Add(ElementParameterFilter(type_rule_01))
    filter_list.Add(ElementParameterFilter(type_rule_02))
    filter_list.Add(ElementParameterFilter(type_rule_03))
    filter_list.Add(ElementParameterFilter(type_rule_04))
    filter_list.Add(ElementParameterFilter(type_rule_05))
    filter_list.Add(ElementParameterFilter(type_rule_06))
    filter_list.Add(ElementParameterFilter(width_rule))

    collector = FilteredElementCollector(doc).OfClass(WallType).WherePasses(structure_filter)
    wallIds = collector.WherePasses(LogicalOrFilter(filter_list)).ToElementIds()
    return wallIds


def get_architect_floor_ids(doc):
    offset_provider = ParameterValueProvider(ElementId(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM))
    thick_provider = ParameterValueProvider(ElementId(BuiltInParameter.STRUCTURAL_FLOOR_CORE_THICKNESS))
    offset_rule = FilterDoubleRule(offset_provider, FilterNumericGreaterOrEqual(), float(0), 0.005)
    thick_rule = FilterDoubleRule(thick_provider, FilterNumericLessOrEqual(), float(0.5), 0.005)
    logic_filter = LogicalAndFilter(ElementParameterFilter(offset_rule), ElementParameterFilter(thick_rule))
    collector = FilteredElementCollector(doc).OfClass(Floor).WherePasses(logic_filter)
    floorIds = collector.WhereElementIsNotElementType().ToElementIds()
    return floorIds


def remove_elements(doc, elementIds):
    with Transaction(doc, "Remove") as trans:
        if isinstance(elementIds, List):
            trans.Start()
            fail_options = trans.GetFailureHandlingOptions()
            fail_options.SetFailuresPreprocessor(warning_dismiss())
            trans.SetFailureHandlingOptions(fail_options)
            try:
                doc.Delete(elementIds)
                doc.Regenerate()
            except:
                [doc.Delete(elemId) for elemId in elementIds if elemId and not elemId.InvalidElementId]
            trans.Commit()
    return


excluded = []
result = set()
excluded.append(-2000095)  # Группы
excluded.append(-2000011)  # Стены
excluded.append(-2000100)  # Колонны
excluded.append(-2000170)  # Панели витража
excluded.append(-2000120)  # Лестницы
excluded.append(-2000023)  # Двери
excluded.append(-2000014)  # Окна
excluded.append(-2000032)  # Перекрытия
excluded.append(-2001330)  # Несущие колонны
excluded.append(-2001320)  # Каркас несущий
excluded.append(-2000996)  # Проемы для шахты
excluded.append(-2001300)  # Фундамент
excluded.append(-2001336)  # Фермы
excluded.append(-2000240)  # Уровни
message = ungroup_group_elements(doc)
collector = FilteredElementCollector(doc).OfClass(Group)
groupInstances = collector.OfCategory(BuiltInCategory.OST_IOSModelGroups)
for cat in doc.Settings.Categories:
    flag = None
    cat_type = cat.CategoryType
    if cat_type.Equals(CategoryType.Annotation): flag = True
    if cat_type.Equals(CategoryType.AnalyticalModel): flag = True
    if cat.Id.IntegerValue not in excluded: flag = True
    if flag and not cat.IsReadOnly:
        collector = FilteredElementCollector(doc).OfCategoryId(cat.Id)
        elementIds = collector.WhereElementIsNotElementType().ToElementIds()
        if elementIds and len(elementIds):
            remove_elements(doc, elementIds)
            result.add(cat.Name)

elementIds = List[ElementId]()
roomIds = FilteredElementCollector(doc).OfClass(SpatialElement).ToElementIds()
lineIds = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RoomSeparationLines).ToElementIds()
floorIds = get_architect_floor_ids(doc)
wallIds = get_architect_wallIds(doc)
elementIds.AddRange(floorIds)
elementIds.AddRange(wallIds)
elementIds.AddRange(roomIds)
elementIds.AddRange(lineIds)
remove_elements(doc, elementIds)
OUT = result
