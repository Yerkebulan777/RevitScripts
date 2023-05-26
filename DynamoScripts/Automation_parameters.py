# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')

import os
import clr
import difflib

clr.AddReference("System")
clr.AddReference("System.Core")
import System
from System import EventHandler
from System.Collections.Generic import List

clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FailureResolutionType
from Autodesk.Revit.DB.Events import FailuresProcessingEventArgs
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import ParameterFilterUtilities
from Autodesk.Revit.DB import BuiltInParameterGroup, Family
from Autodesk.Revit.DB import Category, CategoryType, Transaction
from Autodesk.Revit.DB import FilteredElementCollector, SharedParameterElement
from Autodesk.Revit.DB import Element, ElementId, BuiltInCategory, ExternalDefinition

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


def Output(output):
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return


########################################################################################################################

class warning_dismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        for failure in failuresAccessor.GetFailureMessages():
            fail_severity = failure.GetSeverity()
            if (fail_severity == FailureSeverity.Warning):
                failuresAccessor.DeleteWarning(failure)
        return FailureProcessingResult.Continue


class OnFailuresProcessing(IFailuresPreprocessor):
    def PreprocessFailures(self, args):
        failuresAccessor = args.GetFailuresAccessor()
        fail_messages = failuresAccessor.GetFailureMessages()
        if (0 == fail_messages.Count):
            failuresAccessor.SetProcessingResult(FailureProcessingResult.Continue)
            return
        for msgAccessor in fail_messages:
            fas = msgAccessor.GetSeverity()
            if (fas == FailureSeverity.Warning):
                if (fas.GetDefaultResolutionCaption() == "Remove Constraints"):
                    if (fas.IsFailureResolutionPermitted(msgAccessor, FailureResolutionType.UnlockConstraints)):
                        msgAccessor.SetCurrentResolutionType(FailureResolutionType.UnlockConstraints)
                        fas.ResolveFailure(msgAccessor)
                    else:
                        msgAccessor.SetCurrentResolutionType(FailureResolutionType.DeleteElements)
                        fas.ResolveFailure(msgAccessor)
                failuresAccessor.DeleteWarning(msgAccessor)
                failuresAccessor.SetProcessingResult(FailureProcessingResult.Continue)
        failuresAccessor.SetProcessingResult(FailureProcessingResult.ProceedWithCommit)
        return


def load_shared_parameter_file(doc, filepath):
    if os.path.exists(filepath):
        doc.Application.SharedParametersFilename = filepath
        filepath = doc.Application.SharedParametersFilename
        return filepath


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        definition = group.Definitions.Item[parameter_name]
        if group.Definitions.Contains(definition):
            return definition


def remove_parameter(doc, definition):
    with Transaction(doc, "Remove Parameter") as trans:
        try:
            trans.Start()
            parameter_name = definition.Name
            message = "\n\t{}: deleted successfully".format(parameter_name)
            if not doc.ParameterBindings.Remove(definition):
                if definition and definition.IsValidObject:
                    param = doc.GetElement(definition.Id)
                    doc.Delete(param.Id)
            trans.Commit()
        except Exception as e:
            message = "\n\t{}: failed delete {}".format(parameter_name, e)
            trans.RollBack()
        return message


def remove_similar_shared_parameters(doc, parameter_name):
    result, parameter_name, tolerance = None, parameter_name.rstrip(), 0.85
    parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
    definition = get_external_definition(doc, parameter_name)
    guid = definition.GUID if definition else None
    for param in sorted(parameters, key=lambda param: param.Name):
        param_name = param.Name.rstrip() if guid and param.IsValidObject else None
        weight = difflib.SequenceMatcher(None, parameter_name, param_name).ratio()
        if bool(weight > tolerance) and guid != param.GuidValue:
            result, tolerance = param.GetDefinition(), weight
    message = (remove_parameter(doc, result) if result else '')
    return message


def get_shared_parameter(doc, parameter_name):
    external = get_external_definition(doc, parameter_name)
    if external and external.IsValidObject:
        parameter = SharedParameterElement.Lookup(doc, external.GUID)
        return parameter


def get_parameter_group(parameter_group='PG_GENERAL'):
    group = System.Enum.Parse(BuiltInParameterGroup, parameter_group)
    return group


def create_category_set(doc, categoryIds=None, family_set=None):
    categorySet = doc.Application.Create.NewCategorySet()
    families = List[Element](FilteredElementCollector(doc).OfClass(Family))
    for cid in ParameterFilterUtilities.GetAllFilterableCategories():
        category = Category.GetCategory(doc, ElementId(cid.IntegerValue))
        if category and category.AllowsBoundParameters:
            categoryIdint = int(category.Id.IntegerValue)
            if categoryIds and not category.IsReadOnly:
                if any(True for cid in categoryIds if int(cid) == categoryIdint):
                    builtInCategory = System.Enum.ToObject(BuiltInCategory, categoryIdint)
                    categorySet.Insert(doc.Settings.Categories.get_Item(builtInCategory))
            if not categoryIds and category.CategoryType == CategoryType.Model:
                if any([category.HasMaterialQuantities, category.IsCuttable]):
                    filterId = System.Predicate[System.Object](lambda x: x.FamilyCategoryId == category.Id)
                    filterUsed = System.Predicate[System.Object](lambda x: x.IsEditable and x.IsUserCreated)
                    flag = (bool(families.FindAll(filterId).FindAll(filterUsed)) if family_set else False)
                    if not family_set: categorySet.Insert(category)
                    if flag: categorySet.Insert(category)
    return categorySet


def reinsert_shared_parameter(doc, definition, parameter_group, category_set, is_instance=True):
    binding = None
    if is_instance:
        binding = doc.Application.Create.NewInstanceBinding(category_set)
    elif not is_instance:
        binding = doc.Application.Create.NewTypeBinding(category_set)
    with Transaction(doc, "Reset Parameter") as trans:
        parameter_name = definition.Name
        map = doc.ParameterBindings
        try:
            trans.Start()
            fail_options = trans.GetFailureHandlingOptions()
            fail_options.SetFailuresPreprocessor(warning_dismiss())
            trans.SetFailureHandlingOptions(fail_options)
            message = "\n\t{}: successfully insert".format(parameter_name)
            if not map.Insert(definition, binding, parameter_group):
                message = "\n\t{}: contains".format(parameter_name)
                if definition.Equals(map.Item[definition].Categories):
                    message = "\n\t{}: successfully reinsert".format(parameter_name)
                    if not map.ReInsert(definition, binding, parameter_group):
                        message = "\n\t{}: something is wrong".format(parameter_name)
            trans.Commit()
        except Exception as e:
            message = "\n\t{}: failed to bind {}".format(parameter_name, e)
            trans.RollBack()
    return message


def reset_shared_parameter(doc, filepath, parameter_name, param_group='PG_GENERAL', categoryIds=None, instance=True):
    message = "Not defined {} ExternalDefinition".format(parameter_name)
    if load_shared_parameter_file(doc, filepath):
        external = get_external_definition(doc, parameter_name)
        if isinstance(external, ExternalDefinition):
            bip_group = get_parameter_group(param_group)
            category_set = create_category_set(doc, categoryIds)
            message = reinsert_shared_parameter(doc, external, bip_group, category_set, instance)
    return message


def shared_parameter(doc, filepath, parameter_name, param_group='PG_GENERAL', categoryIds=None, instance=True):
    message = reset_shared_parameter(doc, filepath, parameter_name, param_group, categoryIds, instance)
    message += remove_similar_shared_parameters(doc, parameter_name)
    parameter = get_shared_parameter(doc, parameter_name)
    return parameter, message


########################################################################################################################
filepath, shareId, roomId, rebarId = IN[0], None, ['-2000160'], ['-2009000']
familyIds = [str(cst.Id) for cst in create_category_set(doc, None, True)]
doc.Application.FailuresProcessing += EventHandler[FailuresProcessingEventArgs](OnFailuresProcessing)
########################################################################################################################
# prm_floor = shared_parameter(doc, filepath, "BI_этаж", 'PG_DATA', shareId, True)
# prm_mark = shared_parameter(doc, filepath, "BI_марка_конструкции", 'PG_DATA', familyIds, True)
# prm_design = shared_parameter(doc, filepath, "BI_обозначение", 'PG_IDENTITY_DATA', shareId, False)
# prm_naming = shared_parameter(doc, filepath, "BI_наименование", 'PG_IDENTITY_DATA', shareId, False)
########################################################################################################################
# prm_wight = shared_parameter(doc, filepath, "BI_ширина", 'PG_DATA', familyIds, True)
# prm_lenght = shared_parameter(doc, filepath, "BI_длина", 'PG_DATA', familyIds, True)
# prm_height = shared_parameter(doc, filepath, "BI_высота", 'PG_DATA', familyIds, True)
# prm_thick = shared_parameter(doc, filepath, "BI_толщина", 'PG_DATA', familyIds, True)
# prm_thick_shelf = shared_parameter(doc, filepath, "BI_толщина_стенки", 'PG_DATA', familyIds, True)
# prm_rebar_diameter = shared_parameter(doc, filepath, "BI_диаметр_арматуры", 'PG_DATA', rebarId, True)
########################################################################################################################
prm_entrance = shared_parameter(doc, filepath, "BI_подъезд", 'PG_DATA', roomId, True)
prm_flat_num = shared_parameter(doc, filepath, "BI_квартира", 'PG_DATA', roomId, True)
prm_room_type = shared_parameter(doc, filepath, "BI_тип_помещения", 'PG_DATA', roomId, True)
prm_flat_area = shared_parameter(doc, filepath, "BI_площадь_квартиры", 'PG_DATA', roomId, True)
prm_room_index = shared_parameter(doc, filepath, "BI_индекс_помещения", 'PG_DATA', roomId, True)
prm_room_height = shared_parameter(doc, filepath, "BI_высота_помещения", 'PG_DATA', roomId, True)
prm_flat_capacity = shared_parameter(doc, filepath, "BI_количество_комнат", 'PG_DATA', roomId, True)
prm_room_quotient = shared_parameter(doc, filepath, "BI_коэффициент_площади", 'PG_DATA', roomId, True)
prm_room_shared_area = shared_parameter(doc, filepath, "BI_площадь_квартиры_общая", 'PG_DATA', roomId, True)
prm_room_quotient_area = shared_parameter(doc, filepath, "BI_площадь_с_коэффициентом", 'PG_DATA', roomId, True)
########################################################################################################################
OUT = prm_flat_num, prm_room_type, prm_room_quotient, prm_room_quotient_area
########################################################################################################################
