#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')
# encoding = sys.stdout.encoding

import os
import re
import clr
import time
from datetime import datetime
from datetime import timedelta

clr.AddReference("System")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from System.IO import *
from System.Collections.Generic import List

from Autodesk.Revit.DB import ElementId, FilteredElementCollector, Transaction, SubTransaction
from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, WorksetVisibility, WorksetId
from Autodesk.Revit.DB import NavisworksExportOptions, NavisworksCoordinates, NavisworksExportScope, LogicalOrFilter
from Autodesk.Revit.DB import FilterRule, ParameterFilterUtilities, ParameterFilterRuleFactory, ParameterFilterElement
from Autodesk.Revit.DB import WorksetDefaultVisibilitySettings, RevitLinkType, ImportInstance, CategoryType
from Autodesk.Revit.DB import ElementParameterFilter, FilteredWorksetCollector, WorksetKind
from Autodesk.Revit.DB import View3D, ViewFamily, ViewFamilyType, ElementCategoryFilter
from Autodesk.Revit.DB import ParameterValueProvider, FilterNumericLess, FilterDoubleRule
from Autodesk.Revit.DB import FamilySymbol, FamilyInstance
from Autodesk.Revit.DB.Electrical import Conduit
from Autodesk.Revit.DB.Plumbing import Pipe
########################################################################################################################
########################################################################################################################

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()
doc = revit_script_util.GetScriptDocument()
revitpath = revit_script_util.GetRevitFilePath()

filename = doc.Title
filename = filename.split(".rvt")[0]
filename = filename.split("_detached")[0].split("_отсоединено")[0]


########################################################################################################################
########################################################################################################################

def get_subdirectory(ipath, directory):
    folder = os.path.basename(os.path.dirname(ipath))
    drive, tail = os.path.splitdrive(ipath)
    ipath = os.path.realpath(ipath)
    while os.path.exists(ipath):
        if folder == '': return drive
        result = os.path.join(ipath, folder)
        ipath, folder = os.path.split(ipath)
        if folder.endswith(directory):
            return result


def determine_folder_structure(ipath, directory, folder=None):
    result = os.path.join(get_subdirectory(ipath, 'PROJECT'), directory)
    if bool(os.path.exists(result) and folder):
        result = os.path.join(result, folder)
    if not os.path.exists(result):
        os.makedirs(result)
    return result


def isUpdatedVersion(filepath, days=40, hours=0, minutes=0):
    isUpdated = False
    if os.path.isfile(filepath):
        Output("\nStart check export file time... ")
        span_modified_time = (datetime.now() - timedelta(days, hours, minutes))
        source_modified_time = datetime.fromtimestamp(os.path.getmtime(revitpath))
        export_modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        source_modified_time = (source_modified_time + timedelta(1, 6, 30))
        Output("Minimum span delta date: " + str(format(span_modified_time, '%Y-%m-%d')))
        Output("RVT file last modified date: " + str(format(source_modified_time, '%Y-%m-%d')))
        Output("NWC file last modified date: " + str(format(export_modified_time, '%Y-%m-%d')))
        isUpdated = bool(span_modified_time < source_modified_time < export_modified_time)
        if isUpdated:
            Output("\n ***  " + filename + " HAS BEEN EXPORTED " + "*** \n")
        else:
            try:
                os.remove(filepath)
            except OSError as exc:
                print("Error: {}".format(exc.message))

    return isUpdated


def deleted_families_by_name(doc, family_name, sensitive=False):
    family_rule, symbol_rule = List[FilterRule](), List[FilterRule]()
    symbol_param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)
    family_param_id = ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME)
    symbol_rule.Add(ParameterFilterRuleFactory.CreateContainsRule(symbol_param_id, family_name, sensitive))
    family_rule.Add(ParameterFilterRuleFactory.CreateContainsRule(family_param_id, family_name, sensitive))
    logic_filter = LogicalOrFilter(ElementParameterFilter(family_rule), ElementParameterFilter(symbol_rule))
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol)
    for symbol in collector.WherePasses(logic_filter).ToElements():
        Output("\nDeleted family: {}".format(symbol.Family.Name))
        doc.Delete(symbol.Id)
        doc.Regenerate()


def delete_imported_DWG(doc):
    DWG_to_deleteIList = List[ElementId]()
    for dwg in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        DWG_to_deleteIList.Add(dwg.Id)
    if any(DWG_to_deleteIList):
        doc.Delete(DWG_to_deleteIList)
        return Output("\nRemove imported CAD files")


def adjust_export_links(doc, file_name, result=False):
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks).OfClass(RevitLinkType)
    rvt_link_types = collector.ToElements()
    if any(rvt_link_types): Output('\nCheck and unload linked files...')
    for idx, link_type in enumerate(rvt_link_types):
        if RevitLinkType.IsLoaded(doc, link_type.Id):
            aTypeName = link_type.AttachmentType.ToString()
            if aTypeName == 'Attachment':
                link_name = link_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
                contains = any([segment for segment in re.findall(r'_(\w\w)_', file_name) if segment in link_name])
                Output("Attached linked file " + link_name + " unload")
                if contains == False:
                    link_type.Unload(None)
                elif (contains == True):
                    result = True
            if aTypeName == 'Overlay':
                try:
                    link_type.Unload(None)
                except Exception as error:
                    Output("Unload error: " + str(error))
                else:
                    Output("Unload linked file")
        else:
            Output("Not loaded linked file")

    return result


def create_3dView(doc):
    viewFamilyTypes = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    viewFamilyType3D = [vft for vft in viewFamilyTypes if vft.ViewFamily == ViewFamily.ThreeDimensional][0]
    with Transaction(doc, "3dView") as trans:
        trans.Start()
        view3D = View3D.CreateIsometric(doc, viewFamilyType3D.Id)
        Output("\nCreate3dView: " + view3D.Name)
        if view3D.IsLocked: view3D.Unlock()
        if view3D.ViewTemplateId != ElementId.InvalidElementId:
            view3D.ViewTemplateId = ElementId.InvalidElementId
        if view3D.CanModifyViewDiscipline():
            view3D.get_Parameter(BuiltInParameter.VIEW_DISCIPLINE).Set(4095)
        if view3D.CanModifyDetailLevel():
            view3D.get_Parameter(BuiltInParameter.VIEW_DETAIL_LEVEL).Set(1)
        if view3D.CanModifyDisplayStyle():
            view3D.get_Parameter(BuiltInParameter.MODEL_GRAPHICS_STYLE).Set(3)
        Output("\nSet View3D Orientation")
        trans.Commit()
    return view3D


def set_worksets_visibility(view):
    defaultVisibility = WorksetDefaultVisibilitySettings.GetWorksetDefaultVisibilitySettings(doc)
    with Transaction(doc, "Workset Visible modify") as trans:
        trans.Start()
        for workset in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets():
            with SubTransaction(doc) as subtrans:
                if not workset.IsValidObject: continue
                wid = WorksetId(workset.Id.IntegerValue)
                if not defaultVisibility.IsWorksetVisible(wid):
                    subtrans.Start()
                    defaultVisibility.SetWorksetVisibility(wid, True)
                    subtrans.Commit()
                visibility = view.GetWorksetVisibility(wid)
                if (visibility == WorksetVisibility.Hidden):
                    subtrans.Start()
                    view.SetWorksetVisibility(wid, WorksetVisibility.Visible)
                    subtrans.Commit()
        trans.Commit()
    Output("\nSet worksets visibility")
    return view


def hide_workset(doc, pattern):
    with Transaction(doc, "Hide workset") as trans:
        defaultVisibility = WorksetDefaultVisibilitySettings.GetWorksetDefaultVisibilitySettings(doc)
        worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()
        for workset in worksets:
            if not workset.IsValidObject: continue
            wid = WorksetId(workset.Id.IntegerValue)
            if defaultVisibility.IsWorksetVisible(wid):
                if bool(re.search(pattern, workset.Name, re.IGNORECASE)):
                    trans.Start()
                    Output("\nHide workset {0}".format(pattern))
                    defaultVisibility.SetWorksetVisibility(wid, False)
                    trans.Commit()
                    return


def set_model_category_visibility(doc, view):
    with Transaction(doc, "CategoriesVisibility") as trx:
        trx.Start()
        for cat in doc.Settings.Categories:
            if cat.CategoryType == CategoryType.Model:
                if view.CanCategoryBeHidden(cat.Id):
                    with SubTransaction(doc) as subtrx:
                        try:
                            subtrx.Start()
                            if cat.SubCategories.Size > 0:
                                view.SetCategoryHidden(cat.Id, False)
                            subtrx.Commit()
                        except Exception as exc:
                            Output("\nWarning: {} {}".format(exc.message, cat.Name))
        trx.Commit()
    return view


def adjusting_category_visibility(doc, view):
    with Transaction(doc, "AdjustingVisibility") as trx:
        try:
            trx.Start()
            view.SetCategoryHidden(ElementId(-2000051), False)
            view.SetCategoryHidden(ElementId(-2003400), False)
            view.SetCategoryHidden(ElementId(-2000240), True)
            trx.Commit()
        except Exception as ex:
            msg = "Error adjusting category visibility"
            Output("\n{}: {} ".format(msg, ex.message))
        else:
            Output("\nHide RoomSeparation lines")
            Output("\nHide MassForm category")
            Output("\nUnHide Level category")
    return view


def set_viewFilter(view, filter_name, pattern):
    rules = List[FilterRule]()
    wsparamId = ElementId(BuiltInParameter.ELEM_PARTITION_PARAM)
    categories = ParameterFilterUtilities.GetAllFilterableCategories()
    for workset in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets():
        if bool(re.search(pattern, workset.Name, re.IGNORECASE)):
            Output("\nHide " + workset.Name + " workset by view filter")
            with Transaction(doc, "ViewFilter") as trx:
                trx.Start()
                with SubTransaction(doc) as sut:
                    sut.Start()
                    rules.Add(ParameterFilterRuleFactory.CreateContainsRule(wsparamId, workset.Name, False))
                    sut.Commit()
                with SubTransaction(doc) as sut:
                    sut.Start()
                    filter = ParameterFilterElement.Create(doc, filter_name, categories, rules)
                    sut.Commit()
                with SubTransaction(doc) as sut:
                    sut.Start()
                    view.AddFilter(filter.Id)
                    sut.Commit()
                with SubTransaction(doc) as sut:
                    sut.Start()
                    view.SetFilterVisibility(filter.Id, False)
                    sut.Commit()
                trx.Commit()
            break
    return view


def GetLintelIdsInWindowsAndDoors(doc):
    lintelIds = List[ElementId]()
    framingCatIntId = int(2001320)
    doorCategory = ElementCategoryFilter(BuiltInCategory.OST_Doors)
    windCategory = ElementCategoryFilter(BuiltInCategory.OST_Windows)
    filter = LogicalOrFilter(doorCategory, windCategory)
    for famInst in FilteredElementCollector(doc).OfClass(FamilyInstance).WherePasses(filter):
        if isinstance(famInst, FamilyInstance):
            for subCompId in famInst.GetSubComponentIds():
                subComponent = doc.GetElement(subCompId)
                if (subComponent is None): continue
                if (framingCatIntId == abs(subComponent.Category.Id.IntegerValue)):
                    lintelIds.Add(subCompId)

    return lintelIds


def hide_pipes_by_diameter(doc, view, dimValue=30 / 304.8):
    with Transaction(doc, "ViewFilter") as trx:
        collector = FilteredElementCollector(doc).OfClass(Pipe)
        pvp = ParameterValueProvider(ElementId(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM))
        fRule = FilterDoubleRule(pvp, FilterNumericLess(), dimValue, 1E-3)
        collector = collector.WherePasses(ElementParameterFilter(fRule))
        pipeIds = collector.ToElementIds()
        if (pipeIds and view.IsValidObject):
            trx.Start()
            Output("\nHide pipes")
            view.HideElements(pipeIds)
            trx.Commit()


def hide_conduits_by_diameter(doc, view, dimValue=30 / 304.8):
    with Transaction(doc, "ViewFilter") as trx:
        collector = FilteredElementCollector(doc).OfClass(Conduit)
        pvp = ParameterValueProvider(ElementId(BuiltInParameter.RBS_CONDUIT_DIAMETER_PARAM))
        fRule = FilterDoubleRule(pvp, FilterNumericLess(), dimValue, 1E-3)
        collector = collector.WherePasses(ElementParameterFilter(fRule))
        conduitIds = collector.ToElementIds()
        if (conduitIds and view.IsValidObject):
            trx.Start()
            Output("\nHide conduits")
            view.HideElements(conduitIds)
            trx.Commit()


def get_option_to_export(linkBool, view3D):
    Output("\nStart set Export setting")
    options = NavisworksExportOptions()
    options.ExportUrls = False
    options.ViewId = view3D.Id
    options.ExportLinks = linkBool
    options.ExportRoomGeometry = False
    options.DivideFileIntoLevels = False
    options.FindMissingMaterials = False
    options.ExportRoomAsAttribute = False
    options.ConvertElementProperties = True
    options.Coordinates = NavisworksCoordinates.Shared
    options.ExportScope = NavisworksExportScope.View
    return options


def export_to_NWC(doc, option, directory, filename):
    Output("\n")
    start = time.clock()
    Output("\n" + "> * <" * 10 + "\n")
    Output("Start export: " + filename)
    doc.Export(directory, filename, option)
    Output("NWC export directory: " + directory)
    elapsed = time.strftime('%H:%M:%S', time.gmtime(time.clock() - start))
    Output("Successfully execution time: {0}".format(elapsed))
    Output("\n" + "> * <" * 10 + "\n")
    os.startfile(directory)
    time.sleep(3)
    Output("\n")


#################################################################################
export_directory = determine_folder_structure(revitpath, "05_NWC")
export_file_path = os.path.join(export_directory, "{0}.nwc".format(filename))
#################################################################################

Output("\n" + "> * <" * 10 + "\n")
if isUpdatedVersion(export_file_path) == False:
    Output("Start preparation for: {0}".format(filename))
    Output("Export directory: {0}".format(export_directory))
    with Transaction(doc, "Defined") as trx:
        trx.Start()
        delete_imported_DWG(doc)
        deleted_families_by_name(doc, "Задание")
        deleted_families_by_name(doc, "Приточный")
        deleted_families_by_name(doc, "BIM-Конфликт")
        deleted_families_by_name(doc, "Приточный_клапан")
        deleted_families_by_name(doc, "Задание на отверстие")
        trx.Commit()

    ###############################################################################

    view3D = create_3dView(doc)
    view3D = set_worksets_visibility(view3D)
    view3D = set_model_category_visibility(doc, view3D)
    view3D = adjusting_category_visibility(doc, view3D)

    view3D = set_viewFilter(view3D, "KR-filter", "KR")
    view3D = set_viewFilter(view3D, "AR-filter", "AR")
    view3D = set_viewFilter(view3D, "KG-filter", "KG")
    view3D = set_viewFilter(view3D, "VK-filter", "VK")
    view3D = set_viewFilter(view3D, "OV-filter", "OV")

    hide_conduits_by_diameter(doc, view3D)
    hide_pipes_by_diameter(doc, view3D)

    ###############################################################################

    hide_workset(doc, "Задание")
    hide_workset(doc, "Задание на отверстие")
    hide_workset(doc, "Отверстие")

    ###############################################################################

    boolExportLink = adjust_export_links(doc, filename)
    option = get_option_to_export(boolExportLink, view3D)
    export_to_NWC(doc, option, export_directory, filename)

    ###############################################################################
