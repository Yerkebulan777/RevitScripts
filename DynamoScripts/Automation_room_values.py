# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import time

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import re
import clr
import difflib
from collections import defaultdict

clr.AddReference("System")
clr.AddReference("System.Core")
import System

clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector, Level, XYZ
from Autodesk.Revit.DB import SharedParameterElement, ExternalDefinition
from Autodesk.Revit.DB import ElementId, BuiltInCategory, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB import ViewFamilyType, ViewFamily, ViewPlan, ViewDiscipline, ViewDetailLevel, DisplayStyle
from Autodesk.Revit.DB import ParameterValueProvider, FilterDoubleRule, FilterNumericGreater
from Autodesk.Revit.DB import ElementLevelFilter, ElementParameterFilter, LogicalAndFilter
from Autodesk.Revit.DB import Transaction, UnitUtils, DisplayUnitType
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
"points =  List[XYZ]([XYZ(0,2,3)  XYZ(-4,0,4),  XYZ(5,-3,4)])"
"weights = List[double]([1,1,1])"
"spline = NurbSpline.CreateCurve(points,weights)"
"mc = doc.Create.NewModelCurve(HermiteSpline.Create(points, false), sketchPlane)"
########################################################################################################################
regex = re.compile(r"([+*^#%!?@$&£\\\[\]{}|/;:<>`~]|\d*)")


########################################################################################################################
def select_elements(elementIds):
    uidoc.Selection.SetElementIds(elementIds)
    uidoc.ShowElements(elementIds)
    uidoc.RefreshActiveView()
    return elementIds


def get_rooms_by_level(level):
    double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_AREA))
    double_rul = FilterDoubleRule(double_pvp, FilterNumericGreater(), 0.5, 0.005)
    level_filter, param_filter = ElementLevelFilter(level.Id), ElementParameterFilter(double_rul)
    collector = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Rooms)
    rooms = collector.WherePasses(LogicalAndFilter(level_filter, param_filter)).ToElements()
    rooms = sorted(rooms, key=lambda x: x.Area)
    return rooms


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        definition = group.Definitions.Item[parameter_name]
        if group.Definitions.Contains(definition):
            return definition


def get_element_shared_parameter(doc, element, parameter_name):
    external = get_external_definition(doc, parameter_name)
    if external and isinstance(external, ExternalDefinition):
        parameter = SharedParameterElement.Lookup(doc, external.GUID)
        if isinstance(parameter, SharedParameterElement):
            param = element.get_Parameter(parameter.GuidValue)
            return param


def get_similar_value(target, source, tolerance=0.5, result=None):
    if isinstance(target, basestring):
        target = regex.sub('', target, re.IGNORECASE)
        target = target.encode('cp1251', 'ignore').decode('cp1251')
        length, target = len(target), target.strip()
        pattern = re.compile(target.lower())
        for idx, text in enumerate(source):
            search = regex.sub('', text, re.IGNORECASE)
            search = search.encode('cp1251', 'ignore').decode('cp1251').strip()
            weight = difflib.SequenceMatcher(None, target, search).ratio()
            if 7 < length and target.startswith(search[:7]): weight += 0.3
            if 5 < length and target.startswith(search[:5]): weight += 0.2
            if 3 < length and target.startswith(search[:3]): weight += 0.1
            if pattern.findall(text, re.IGNORECASE): weight += 0.5
            if target == search: return text
            if (weight > tolerance):
                tolerance = weight
                result = text
        return result


def get_valid_apartment(apartment):
    matches = set()
    for dictionary in DICTIONARY.itervalues():
        if dictionary.has_key(apartment): return apartment
        matches.add(get_similar_value(apartment, dictionary.keys()))
    return get_similar_value(apartment, matches)


def get_valid_departament(apartment):
    for department, dictionary in DICTIONARY.iteritems():
        if dictionary.has_key(apartment):
            return department


def get_departament(room):
    department = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT).AsString()
    department = department if isinstance(department, basestring) else ""
    department = regex.sub('', department, re.IGNORECASE).strip()
    department = department.capitalize()
    if department and len(department):
        if DICTIONARY.get(department): return department
        result = get_similar_value(department, DICTIONARY.keys())
        return result


def get_apartment(room, department):
    apartment = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
    apartment = apartment if isinstance(apartment, basestring) else ""
    apartment = regex.sub('', apartment, re.IGNORECASE).strip()
    apartment = apartment.capitalize()
    dictionary = DICTIONARY.get(department)
    if isinstance(dictionary, dict):
        if (dictionary.has_key(apartment)):
            return apartment
    apartment = get_valid_apartment(apartment)
    return apartment


def get_room_definition(room):
    department = get_departament(room)
    apartment = get_apartment(room, department)
    if apartment and department is None:
        department = get_valid_departament(apartment)
    if department and isinstance(department, basestring):
        dictionary = DICTIONARY.get(department)
        if isinstance(dictionary, dict):
            if (dictionary.has_key(apartment)):
                return department, apartment
    return department, apartment


def set_defined_values(room, department, apartment):
    if DICTIONARY.get(department) and room.IsValidObject:
        millimeter = DisplayUnitType.DUT_MILLIMETERS
        square_meter = DisplayUnitType.DUT_SQUARE_METERS
        code_value = DICTIONARY.get(department).get(apartment)
        flat_param = get_element_shared_parameter(doc, room, "BI_квартира")
        type_param = get_element_shared_parameter(doc, room, "BI_тип_помещения")
        index_param = get_element_shared_parameter(doc, room, "BI_индекс_помещения")
        height_param = get_element_shared_parameter(doc, room, "BI_высота_помещения")
        quot_param = get_element_shared_parameter(doc, room, "BI_коэффициент_площади")
        area_param = get_element_shared_parameter(doc, room, "BI_площадь_с_коэффициентом")
        flat_number = int(flat_param.AsInteger() if flat_param and not flat_param.IsReadOnly else 0)
        index_value = '{0}.{1}'.format(code_value, flat_number) if bool(flat_number) else code_value
        if code_value and flat_param and type_param and index_param and quot_param and area_param:
            height = UnitUtils.ConvertFromInternalUnits(room.UnboundedHeight, millimeter)
            double = room.get_Parameter(BuiltInParameter.ROOM_AREA).AsDouble()
            room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT).Set(department)
            room.get_Parameter(BuiltInParameter.ROOM_NAME).Set(apartment)
            if not index_param.IsReadOnly: index_param.Set(index_value)
            if not height_param.IsReadOnly: height_param.Set(height)
            if not type_param.IsReadOnly: type_param.Set(department)
            area = UnitUtils.Convert(double, square_meter, square_meter)
            if not area_param.IsReadOnly: area_param.Set(area)
            if not quot_param.IsReadOnly: quot_param.Set(1)
            if code_value and "Квартира" == department:
                if apartment == "Лоджия балкон":
                    area_param.Set(area * 0.4)
                    quot_param.Set(0.4)
                elif apartment == "Лоджия":
                    area_param.Set(area * 0.5)
                    quot_param.Set(0.5)
                elif apartment == "Веранда":
                    area_param.Set(area * 0.8)
                    quot_param.Set(0.8)
                elif apartment == "Балкон":
                    area_param.Set(area * 0.3)
                    quot_param.Set(0.3)
                elif apartment == "Терраса":
                    area_param.Set(area * 0.3)
                    quot_param.Set(0.3)
            return True


########################################################################################################################
message = "Defined rooms:\n"
########################################################################################################################
view = FilteredElementCollector(doc).OfClass(ViewPlan).FirstElement()
levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
levels = sorted(levels, key=lambda x: x.Elevation)
for level in levels:
    rooms = get_rooms_by_level(level)
    if rooms and len(rooms):
        message += "\nLevel: {}\n".format(level.Name)
        with Transaction(doc, message.strip()) as trans:
            trans.Start()
            for room in rooms:
                if room.IsValidObject:
                    department, apartment = get_room_definition(room)
                    if department and isinstance(apartment, basestring):
                        if set_defined_values(room, department, apartment):
                            message += "\nFind: {} {}".format(department, apartment)
                    else:
                        select_elements(List[ElementId]([room.Id]))
                        break
            trans.Commit()
########################################################################################################################
OUT = message
########################################################################################################################
