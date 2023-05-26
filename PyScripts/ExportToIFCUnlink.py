# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import os
import clr
import time

# Import RevitAPI
clr.AddReference("System")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from System.IO import *

from Autodesk.Revit.DB import IFCExportOptions, IFCVersion
from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, WorksetVisibility, WorksetId
from Autodesk.Revit.DB import ElementId, FilteredElementCollector, Transaction, SubTransaction
from Autodesk.Revit.DB import WorksetDefaultVisibilitySettings, RevitLinkType, ImportInstance, CategoryType
from Autodesk.Revit.DB import FilteredWorksetCollector, WorksetKind
from Autodesk.Revit.DB import View3D, ViewFamily, ViewFamilyType

########################################################################################################################
########################################################################################################################

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()
doc = revit_script_util.GetScriptDocument()
revit_file_path = revit_script_util.GetRevitFilePath()

file_name = doc.Title
file_name = file_name.split(".rvt")[0]
file_name = file_name.split("_detached")[0].split("_отсоединено")[0]


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


def DeleteImportedDWG(doc):
    with Transaction(doc, "Remove imported files") as trx:
        trx.Start()
        Output("\nStart remove imported CAD files...")
        collector = FilteredElementCollector(doc).OfClass(ImportInstance)
        for elementId in collector.ToElementIds():
            try:
                doc.Delete(elementId)
            except Exception as error:
                Output("Delete error: {}".format(error))
        trx.Commit()


def DeleteAllElementsInCategory(doc, bic):
    with Transaction(doc, "Delete in Category") as trx:
        trx.Start()
        Output("\nStart remove elements in {} category...".format(bic))
        collector = FilteredElementCollector(doc).OfCategory(bic)
        for elementId in collector.ToElementIds():
            try:
                doc.Delete(elementId)
            except Exception as error:
                Output("Delete error: {}".format(error))
        trx.Commit()


def UnloadAllLinks(revitFilePath):
    Output("\nStart unload links ...")
    section = os.path.basename(os.path.dirname(os.path.dirname(revitFilePath)))
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks)
    Output("Is Revit file section: {}".format(section))
    rvtLinkTypes = collector.OfClass(RevitLinkType)
    for idx, linkType in enumerate(rvtLinkTypes):
        if RevitLinkType.IsLoaded(doc, linkType.Id):
            try:
                linkType.Unload(None)
            except Exception as error:
                Output("Unload error: {}".format(error))
    return


def getBasename(filePath):
    fullname = os.path.basename(filePath)
    filename, ext = os.path.splitext(fullname)
    return filename


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


def set_worksets_visibility(doc, view):
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


def output_text(message, directory, filename='Exception'):
    filepath = os.path.join(directory, filename + '.txt')
    if os.path.isfile(filepath): os.remove(filepath)
    with open(filepath, mode='a') as txf:
        txf.write(message)
        Output(message)


def export_to_IFC(doc, view, directory, filename):
    Output("\nStart export: {} ".format(filename))
    with Transaction(doc, "ExportToIFC") as trx:
        trx.Start()
        start = time.clock()
        try:
            options = IFCExportOptions()
            options.SpaceBoundaryLevel = 0
            options.FilterViewId = view.Id
            options.ExportBaseQuantities = True
            options.WallAndColumnSplitting = True
            options.FileVersion = IFCVersion.IFC2x3CV2
            # options.AddOption("ExportInternalRevitPropertySets", "true")
            # options.AddOption("ExportIFCCommonPropertySets", "true")
            # options.AddOption("ExportAnnotations ", "true")
            # options.AddOption("SpaceBoundaries ", "0")
            # options.AddOption("ExportRoomsInView", "false")
            # options.AddOption("Use2DRoomBoundaryForVolume ", "false")
            # options.AddOption("UseFamilyAndTypeNameForReference ", "true")
            # options.AddOption("ExportPartsAsBuildingElements", "false")
            # options.AddOption("ExportBoundingBox", "false")
            # options.AddOption("ExportSolidModelRep", "true")
            # options.AddOption("ExportSpecificSchedules", "false")
            # options.AddOption("ExportLinkedFiles", "false")
            # options.AddOption("IncludeSiteElevation", "true")
            # options.AddOption("UseActiveViewGeometry", "true")
            options.AddOption("TessellationLevelOfDetail", "1")
            doc.Export(directory, filename, options)
        except Exception as exc:
            message = "\nEXCEPTION: {0}".format(exc.message)
            output_text(message, directory, filename)
        finally:
            os.startfile(directory)
            time.sleep(3)
        elapsed = time.strftime('%H:%M:%S', time.gmtime((time.clock() - start)))
        Output("Successfully execution time: " + str(elapsed))
        Output("Revit file path: " + revit_file_path)
        Output("\n" + " < * > " * 15 + "\n")
        trx.Commit()
    return


###############################################################################
DeleteImportedDWG(doc)
DeleteAllElementsInCategory(doc, BuiltInCategory.OST_Mass)
###############################################################################
export_directory = determine_folder_structure(revit_file_path, "08_IFC")
export_file_path = os.path.join(export_directory, file_name)
export_file_path = os.path.abspath(export_file_path)
###############################################################################
UnloadAllLinks(revit_file_path)
###############################################################################
view3D = create_3dView(doc)
view3D = set_worksets_visibility(doc, view3D)
view3D = set_model_category_visibility(doc, view3D)
###############################################################################
export_to_IFC(doc, view3D, export_directory, file_name)
###############################################################################


