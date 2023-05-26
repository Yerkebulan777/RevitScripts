#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import clr
import System

clr.AddReference("System")
clr.AddReference("System")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

from System.IO import *

from Autodesk.Revit.DB import ElementId, FilteredElementCollector, Transaction, SubTransaction
from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, WorksetVisibility, WorksetId
from Autodesk.Revit.DB import WorksetDefaultVisibilitySettings, RevitLinkType, CategoryType
from Autodesk.Revit.DB import FilteredWorksetCollector, WorksetKind, ImportInstance
from Autodesk.Revit.DB import View3D, ViewOrientation3D, ViewFamily, ViewFamilyType

########################################################################################################################
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName


########################################################################################################################

def Output(output):
    clr.AddReference("RevitAPIUI")
    from Autodesk.Revit.UI import TaskDialog
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return


########################################################################################################################
def delete_imported_DWG(doc):
    DWG_to_deleteIList = List[ElementId]()
    for dwg in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        DWG_to_deleteIList.Add(dwg.Id)
    if any(DWG_to_deleteIList):
        doc.Delete(DWG_to_deleteIList)
        return


def create_3dView(doc):
    view3D, name = None, "3D_Navisworks"
    views = FilteredElementCollector(doc).OfClass(View3D).ToElements()
    viewFamilyTypes = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    viewFamilyType3D = [vft for vft in viewFamilyTypes if vft.ViewFamily == ViewFamily.ThreeDimensional][0]
    naviswork_views = [vw for vw in views if vw and vw.Name == name]
    if len(naviswork_views): view3D = naviswork_views[0]
    with Transaction(doc, "3dView") as trans:
        trans.Start()
        [doc.Delete(vw.Id) for vw in views if vw and vw.Name.startswith("{")]
        if not view3D: view3D = View3D.CreateIsometric(doc, viewFamilyType3D.Id)
        view3D.get_Parameter(BuiltInParameter.VIEW_NAME).Set(name)
        if view3D.IsLocked: view3D.Unlock()
        if view3D.ViewTemplateId != ElementId.InvalidElementId:
            view3D.ViewTemplateId = ElementId.InvalidElementId
        if view3D.CanModifyViewDiscipline():
            view3D.get_Parameter(BuiltInParameter.VIEW_DISCIPLINE).Set(4095)
        if view3D.CanModifyDetailLevel():
            view3D.get_Parameter(BuiltInParameter.VIEW_DETAIL_LEVEL).Set(3)
        if view3D.CanModifyDisplayStyle():
            view3D.get_Parameter(BuiltInParameter.MODEL_GRAPHICS_STYLE).Set(6)
        view3D.IsSectionBoxActive = False
        doc.Regenerate()
        trans.Commit()
        trans.Dispose()
    uidoc.RequestViewChange(view3D)
    return view3D


def hide_links_visibility(doc, view):
    imports = FilteredElementCollector(doc, view.Id).OfClass(ImportInstance).ToElementIds()
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks).OfClass(RevitLinkType)
    with Transaction(doc, "Links Hide Visibility") as trans:
        trans.Start()
        [doc.Delete(dwg.Id) for dwg in imports]
        elementIdSet = collector.ToElementIds()
        for linkedFileId in elementIdSet:
            if (linkedFileId and not doc.GetElement(linkedFileId).IsHidden(view)):
                if (doc.GetElement(linkedFileId).CanBeHidden(view)):
                    view.HideElements(elementIdSet)
        trans.Commit()
        trans.Dispose()
    return


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
        trans.Dispose()
    return view


def set_category_visibility(view):
    with Transaction(doc, "CategoriesVisibility") as trans:
        trans.Start()
        for category in doc.Settings.Categories:
            if category.CategoryType == CategoryType.Model and category.SubCategories.Size > 0:
                if not view.CanCategoryBeHidden(category.Id): continue
                with SubTransaction(doc) as sub:
                    try:
                        sub.Start()
                        view.SetCategoryHidden(ElementId(category.Id.IntegerValue), False)
                        sub.Commit()
                    except Exception as e:
                        Output("Error unhidden category: {}".format(e))
        with SubTransaction(doc) as sub:
            try:
                sub.Start()
                view.SetCategoryHidden(ElementId(-2003400), True)
                sub.Commit()
            except Exception as e:
                Output("\nHide MassForm category error: " + str(e))
        with SubTransaction(doc) as sub:
            try:
                sub.Start()
                view.SetCategoryHidden(ElementId(-2000240), True)
                sub.Commit()
            except Exception as e:
                Output("\nHide Level category error: " + str(e))
        trans.Commit()
        trans.Dispose()
    return view


########################################################################################################################
view3D = create_3dView(doc)
set_worksets_visibility(view3D)
set_category_visibility(view3D)
hide_links_visibility(doc, view3D)
rebars = FilteredElementCollector(doc, view3D.Id).OfCategory(BuiltInCategory.OST_Rebar).ToElements()
with Transaction(doc, "CategoriesVisibility") as trans:
    trans.Start()
    for rebar in rebars:
        try:
            rebar.SetSolidInView(view3D, True)
        except:
            pass
    trans.Commit()
    trans.Dispose()
########################################################################################################################
OUT = view3D
########################################################################################################################
