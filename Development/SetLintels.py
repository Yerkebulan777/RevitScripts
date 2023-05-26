#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')
reload(sys)
import re
import clr
import difflib

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import Dictionary, List

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import UnitUtils, ElementId, Wall, FamilySymbol
from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource, Transaction, StorageType
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity, BuiltInFailures
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, ElementMulticategoryFilter
from Autodesk.Revit.DB import LogicalOrFilter, FilterStringContains, FilterStringRule
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.GeometryReferences)

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


########################################################################################################################

class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source = FamilySource.Family
        overwriteParameterValues = True
        return True


class warning_dismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        for failure in failuresAccessor.GetFailureMessages():
            fId = failure.GetFailureDefinitionId
            if fId == BuiltInFailures.GroupFailures.AtomViolationWhenOnePlaceInstance:
                failuresAccessor.DeleteWarning(failure)
            fail_severity = failure.GetSeverity()
            if (fail_severity == FailureSeverity.Warning):
                failuresAccessor.DeleteWarning(failure)
        return FailureProcessingResult.Continue


def transaction(action):
    def wrapped(*args, **kwargs):
        with Transaction(doc, 'Automation') as trans:
            trans.Start()
            fail_options = trans.GetFailureHandlingOptions()
            fail_options.SetFailuresPreprocessor(warning_dismiss())
            trans.SetFailureHandlingOptions(fail_options)
            try:
                result = action(*args, **kwargs)
            except:
                result = None
                trans.RollBack()
            else:
                trans.Commit()
        return result

    return wrapped


########################################################################################################################
def get_wall_width(doc, element):
    host_ids = List[ElementId]()
    host_ids.Add(element.get_Parameter(BuiltInParameter.HOST_ID_PARAM).AsElementId())
    provider = ParameterValueProvider(ElementId(BuiltInParameter.SYMBOL_NAME_PARAM))
    rule_01 = FilterStringRule(provider, FilterStringContains(), "кирпич", False)
    rule_02 = FilterStringRule(provider, FilterStringContains(), "газоблок", False)
    str_filter = LogicalOrFilter(ElementParameterFilter(rule_01), ElementParameterFilter(rule_02))
    host = FilteredElementCollector(doc, host_ids).OfClass(Wall).WherePasses(str_filter).FirstElement()
    if host: return host.WallType.Width


def get_subelement(instance):
    subelements = instance.GetSubComponentIds()
    if (subelements.Count > 0):
        for sid in subelements:
            inst = doc.GetElement(sid)
            family = inst.Symbol.Family
            catId = family.FamilyCategoryId.IntegerValue
            if catId == -2001320: return inst


def sort_dictionary(dictionary):
    sort_keys = []
    pydict = dict(dictionary)
    for key, value in pydict.iteritems():
        sizes = [int(i) for i in key.strip().split('x')]
        sort_keys.append(int((sizes[0] * 0.25) + (sizes[1] * 0.5) + (sizes[2] * 25)) // 5)
    output = [data[1] for data in sorted(zip(sort_keys, pydict.items()))]
    return reversed(output)


def create_family_type(doc, family, new_type_name):
    if (family and new_type_name):
        family_doc = doc.EditFamily(family)
        if not family_doc.IsFamilyDocument: return
        family_manager = family_doc.FamilyManager
        for fid in family.GetFamilySymbolIds():
            symbol = family.Document.GetElement(fid)
            name = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            if (new_type_name == name): return family
        with Transaction(family_doc, "CreateNewType") as trans:
            trans.Start()
            family_manager.NewType(new_type_name)
            trans.Commit()
        return family


def get_hole_size(doc):
    maximum = float(3000 / 304.8)
    categories = List[BuiltInCategory]()
    categories.Add(BuiltInCategory.OST_Doors)
    categories.Add(BuiltInCategory.OST_Windows)
    dictionary = Dictionary[str, str]()
    hole_filter = ElementMulticategoryFilter(categories)
    hole_collector = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(hole_filter)
    for instance in hole_collector.ToElements():
        if instance.IsValidObject:
            sill = instance.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM).AsDouble()
            WVStr = instance.Symbol.get_Parameter(BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM).AsValueString()
            HVStr = instance.Symbol.get_Parameter(BuiltInParameter.FAMILY_ROUGH_HEIGHT_PARAM).AsValueString()
            WVDbl = instance.Symbol.get_Parameter(BuiltInParameter.GENERIC_HEIGHT).AsDouble()
            HVDbl = instance.Symbol.get_Parameter(BuiltInParameter.GENERIC_WIDTH).AsDouble()
            HVStr = str((round(((sill + int(HVStr)) * 304.8) / 300) * 300) / 304.8)
            HVDbl = float((round(((sill + HVDbl) * 304.8) / 300) * 300) / 304.8)
            HVDbl = float(HVDbl if (HVDbl < maximum) else maximum)
            thick = get_wall_width(doc, instance)
            if all([HVDbl, WVDbl, thick]):
                elementId = str(instance.Id.IntegerValue)
                height_mm, width_mm = round(HVDbl * 304.8), round(WVDbl * 304.8)
                int_height = int(height_mm if height_mm > int(HVStr) else HVStr)
                int_width = int(width_mm if width_mm > int(WVStr) else WVStr)
                int_thick = int(round((thick * 304.8) / 10) * 10)
                size_key = "{}x{}x{}".format(str(int_height), str(int_width), str(int_thick))
                if (dict(dictionary).has_key(size_key)):
                    result = dict(dictionary).get(size_key)
                    dictionary[size_key] = "{},{}".format(result, elementId)
                else:
                    dictionary[size_key] = elementId

    return sort_dictionary(dictionary)


def get_family_by_name(doc, family_name):
    pvp = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME))
    flt = ElementParameterFilter(FilterStringRule(pvp, FilterStringContains(), family_name, False))
    family = FilteredElementCollector(doc).OfClass(FamilySymbol).WherePasses(flt).FirstElement().Family
    return family


def get_family_parameter(family, param_name):
    tolerance, family_param = int(0), None
    family_manager = family.Document.FamilyManager
    for param in family_manager.GetParameters:
        weight = difflib.SequenceMatcher(None, param_name, param.Definition.Name).ratio()
        if (weight > tolerance): tolerance, family_param = weight, param
    return family_param


@transaction
def set_family_parameter_value(family, param_name, value):
    family_manager = family.Document.FamilyManager
    family_param = family_manager.get_Parameter(param_name)
    if not family_param: family_param = get_family_parameter(family, param_name)
    if family_param and family_param.StorageType == StorageType.String:
        value = (value if isinstance(value, basestring) else str(value))
        family_param = family_manager.Set(family_param, value)
    if family_param and family_param.StorageType == StorageType.Double:
        if isinstance(value, float): family_manager.Set(family_param, UnitUtils.Convert.ToDouble(value))
        if isinstance(value, basestring): family_param.SetValueString(value)
    if family_param and family_param.StorageType == StorageType.Integer:
        value = (value if isinstance(value, int) else int(value))
        family_manager.Set(family_param, value)
    if family_param and family_param.StorageType == StorageType.ElementId:
        value = (value if isinstance(value, int) else int(value))
        family_manager.Set(family_param, ElementId(value))
    return family_param


def load_family(doc, family):
    family = doc.EditFamily(family).LoadFamily(doc, FamilyOption())
    return family


def get_valid_holes(doc, data_list):
    instances, marks = [], []
    for idx, line in enumerate(data_list):
        size, lineIds = line
        size = re.sub(r"^(\d*x)", '', size).strip()
        stringIds = [line for line in lineIds.split(',')]
        mark = "(элемент_перемычки)ПР-{}-{}".format(str(idx + 1), size)
        for jdx, line in enumerate(stringIds):
            instance = doc.GetElement(ElementId(int(line.strip())))
            if not instance.IsValidObject: continue
            marks.append(mark)
    return marks


########################################################################################################################
family = get_family_by_name(doc, "Металлическая перемычка")
family = create_family_type(doc, family, "NewTest")
set_family_parameter_value(family, "BI_марка", "NewTest")
set_family_parameter_value(family, "Несущая стена", 1)
set_family_parameter_value(family, "Высота этажа", 3000)
set_family_parameter_value(family, "Назначить опирание", 0)
set_family_parameter_value(family, "Глубина опирания", 300)
set_family_parameter_value(family, "Типовой размер", 1)
set_family_parameter_value(family, "Ширина проема", 1200)
set_family_parameter_value(family, "Толщина стены", 1200)
family = load_family(doc, family)
# data_list = get_hole_size_by_instances(doc)
# result = get_valid_holes(doc, data_list)
########################################################################################################################
OUT = family
########################################################################################################################
