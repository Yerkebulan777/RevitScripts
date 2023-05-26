# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts.
import os
import sys

sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

from Library_develop import transaction_script_util as Transactionstil

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import SharedParameterElement
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter, BuiltInCategory, WorksharingUtils
from Autodesk.Revit.DB import FilterNumericEquals, FilterNumericGreater, ParameterValueProvider, FilterDoubleRule
from Autodesk.Revit.DB import UnitUtils, ElementId, DisplayUnitType, ElementParameterFilter
from Autodesk.Revit.DB.Structure import Rebar


########################################################################################################################

def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def get_shared_parameter_guid_by_name(doc, parameter_name):
    definition = get_external_definition(doc, parameter_name)
    parameter = SharedParameterElement.Lookup(doc, definition.GUID)
    if bool(parameter): return parameter.GuidValue


def get_rebarIds_by_diameter(doc, diameter):
    provider_length = ParameterValueProvider(ElementId(BuiltInParameter.REBAR_ELEM_LENGTH))
    provider_diameter = ParameterValueProvider(ElementId(BuiltInParameter.REBAR_BAR_DIAMETER))
    length_rule = FilterDoubleRule(provider_length, FilterNumericGreater(), float(0), 0.005)
    diameter_rule = FilterDoubleRule(provider_diameter, FilterNumericEquals(), float(diameter / 304.8), 0.005)
    length_filter, diameter_filter = ElementParameterFilter(length_rule), ElementParameterFilter(diameter_rule)
    collector = FilteredElementCollector(doc).OfClass(Rebar).OfCategory(BuiltInCategory.OST_Rebar)
    collector = collector.WherePasses(length_filter).WherePasses(diameter_filter)
    ids = collector.WhereElementIsNotElementType().ToElementIds()
    ids = WorksharingUtils.CheckoutElements(doc, ids)
    return ids


def CalculateWeightOfReinforcement(doc):
    message = ''
    set_count, result_mass, result_length = 0, [], []
    section = os.path.basename(os.path.dirname(os.path.dirname(doc.PathName)))
    guid_length = get_shared_parameter_guid_by_name(doc, "BI_длина")
    guid_total_mass = get_shared_parameter_guid_by_name(doc, "BI_масса")
    guid_linear_mass = get_shared_parameter_guid_by_name(doc, "BI_масса_1_пм")
    if not any([(section.endswith("KJ")), (section.endswith("KG"))]): return "Is not KG section"
    if not all([guid_length, guid_total_mass, guid_linear_mass]): message = "Not defined any parameter"
    for diameter in range(2, 60, 2):
        rebarIds = get_rebarIds_by_diameter(doc, diameter)
        for idx, rid in enumerate(rebarIds):
            rebar = doc.GetElement(rid)
            if rebar.IsValidObject:
                # rebar_type = doc.GetElement(rebar.GetTypeId())
                length_dbl = rebar.get_Parameter(BuiltInParameter.REBAR_ELEM_LENGTH).AsDouble()
                length_met = UnitUtils.ConvertFromInternalUnits(length_dbl, DisplayUnitType.DUT_METERS)
                counts = rebar.get_Parameter(BuiltInParameter.REBAR_ELEM_QUANTITY_OF_BARS).AsInteger()
                total_length_meter = float(length_met * counts)
                total_length = float(length_dbl * counts)
                linear_mass_kilogram = float(0)
                if diameter == 6:
                    linear_mass_kilogram = 0.222

                elif diameter == 8:
                    linear_mass_kilogram = 0.395

                elif diameter == 10:
                    linear_mass_kilogram = 0.617

                elif diameter == 12:
                    linear_mass_kilogram = 0.888

                elif diameter == 14:
                    linear_mass_kilogram = 1.21

                elif diameter == 16:
                    linear_mass_kilogram = 1.58

                elif diameter == 18:
                    linear_mass_kilogram = 2.00

                elif diameter == 20:
                    linear_mass_kilogram = 2.47

                elif diameter == 22:
                    linear_mass_kilogram = 2.98

                elif diameter == 25:
                    linear_mass_kilogram = 3.85

                elif diameter == 28:
                    linear_mass_kilogram = 4.83

                elif diameter == 32:
                    linear_mass_kilogram = 6.31

                elif diameter == 36:
                    linear_mass_kilogram = 7.99

                elif diameter == 40:
                    linear_mass_kilogram = 9.87

                if linear_mass_kilogram:
                    unit_type = DisplayUnitType.DUT_KILOGRAMS_PER_CUBIC_METER
                    total_mass_meter = total_length_meter * linear_mass_kilogram
                    unit_linear_mass = UnitUtils.ConvertFromInternalUnits(linear_mass_kilogram, unit_type)
                    Transactionstil.set_value_by_guid(guid_linear_mass, rebar, unit_linear_mass)
                    Transactionstil.set_value_by_guid(guid_total_mass, rebar, total_mass_meter)
                    Transactionstil.set_value_by_guid(guid_length, rebar, total_length)
                    result_length.append(total_length_meter)
                    result_mass.append(total_mass_meter)
                    set_count += 1

    message_weight = "\nTotal weight of all reinforcement {} kilograms".format(str(round(sum(result_mass))))
    message_length = "\nTotal length of all reinforcement {} meters".format(str(round(sum(result_length))))
    message_result = "\nSet elements count /{}/ out of {} items ".format(str(set_count), str(len(result_mass)))
    message = message + message_length + message_weight + message_result
    return message

########################################################################################################################
