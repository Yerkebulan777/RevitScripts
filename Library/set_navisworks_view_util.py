# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import os
import clr

clr.AddReference("System")
clr.AddReference("System.Core")

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk
from Autodesk.Revit.DB import WorksharingUtils, ElementParameterFilter
from Autodesk.Revit.DB import FilterNumericEquals, FilterNumericGreater, ParameterValueProvider, FilterDoubleRule
from Autodesk.Revit.DB import ElementId, FilteredElementCollector, TransactionGroup, Transaction, SubTransaction
from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, WorksetVisibility, WorksetId
from Autodesk.Revit.DB import WorksetDefaultVisibilitySettings, RevitLinkType, CategoryType
from Autodesk.Revit.DB import FilteredWorksetCollector, WorksetKind, ImportInstance
from Autodesk.Revit.DB import View3D, ViewFamily, ViewFamilyType


########################################################################################################################
########################################################################################################################


def create_3dView(doc, view_name="3D_Navisworks"):
    # uidoc = doc.Application.ActiveUIDocument
    view3D, views = None, FilteredElementCollector(doc).OfClass(View3D).ToElements()
    viewFamilyTypes = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    viewFamilyType3D = [vft for vft in viewFamilyTypes if vft.ViewFamily == ViewFamily.ThreeDimensional][0]
    views = [view for view in views if not view.IsTemplate and 5 < len(view.Name)]
    navisworks = [view for view in views if view and view.Name == view_name]
    with Transaction(doc, "Create3dView") as trans:
        trans.Start()
        for view in views:
            if view.Name.startswith("{") and view.Name.endswith("}"):
                try:
                    doc.Delete(view.Id)
                except:
                    pass
        view3D = navisworks[0] if len(navisworks) else View3D.CreateIsometric(doc, viewFamilyType3D.Id)
        view3D.get_Parameter(BuiltInParameter.VIEW_NAME).Set(view_name)
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
        trans.Commit()
    # uidoc.RequestViewChange(view3D)
    return view3D


def hide_links_visibility(doc, view):
    collector = FilteredElementCollector(doc).OfClass(RevitLinkType)
    elementIdSet = collector.OfCategory(BuiltInCategory.OST_RvtLinks).ToElementIds()
    imports = FilteredElementCollector(doc, view.Id).OfClass(ImportInstance).ToElementIds()
    with Transaction(doc, "Links Hide Visibility") as trans:
        try:
            trans.Start()
            for linkedFileId in elementIdSet:
                if (linkedFileId and not doc.GetElement(linkedFileId).IsHidden(view)):
                    if (doc.GetElement(linkedFileId).CanBeHidden(view)):
                        view.HideElements(elementIdSet)
            [doc.Delete(dwgId) for dwgId in imports]
            trans.Commit()
        except:
            trans.RollBack()
    return


def set_worksets_visibility(doc, view):
    defaultVisibility = WorksetDefaultVisibilitySettings.GetWorksetDefaultVisibilitySettings(doc)
    with Transaction(doc, "Workset Visible modify") as trans:
        trans.Start()
        for workset in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets():
            if not workset.IsValidObject: continue
            wid = WorksetId(workset.Id.IntegerValue)
            if not defaultVisibility.IsWorksetVisible(wid):
                defaultVisibility.SetWorksetVisibility(wid, True)
            visibility = view.GetWorksetVisibility(wid)
            if (visibility == WorksetVisibility.Hidden):
                view.SetWorksetVisibility(wid, WorksetVisibility.Visible)
        trans.Commit()
    return view


def set_category_visibility(doc, view):
    model = CategoryType.Model
    annotation = CategoryType.Annotation
    analytic = CategoryType.AnalyticalModel
    with Transaction(doc, "CategoriesVisibility") as trans:
        trans.Start()
        for category in doc.Settings.Categories:
            catType = category.CategoryType
            if (catType == annotation or catType == analytic):
                with SubTransaction(doc) as sub:
                    try:
                        sub.Start()
                        view.SetCategoryHidden(ElementId(category.Id.IntegerValue), True)
                        sub.Commit()
                    except:
                        sub.RollBack()
            if catType == model:
                if category.SubCategories.Size == 0: continue
                if view.CanCategoryBeHidden(category.Id):
                    with SubTransaction(doc) as sub:
                        try:
                            sub.Start()
                            view.SetCategoryHidden(ElementId(category.Id.IntegerValue), False)
                            sub.Commit()
                        except Exception as e:
                            sub.RollBack()
        with SubTransaction(doc) as sub:
            try:
                sub.Start()
                view.SetCategoryHidden(ElementId(-2003400), True)
                sub.Commit()
            except Exception as e:
                sub.RollBack()
        with SubTransaction(doc) as sub:
            try:
                sub.Start()
                view.SetCategoryHidden(ElementId(-2000240), True)
                sub.Commit()
            except Exception as e:
                sub.RollBack()
        trans.Commit()
    return view


def get_rebar_ids_by_diameter(doc, diameter):
    provider_length = ParameterValueProvider(ElementId(BuiltInParameter.REBAR_ELEM_LENGTH))
    provider_diameter = ParameterValueProvider(ElementId(BuiltInParameter.REBAR_BAR_DIAMETER))
    length_rule = FilterDoubleRule(provider_length, FilterNumericGreater(), float(0), 0.005)
    diameter_rule = FilterDoubleRule(provider_diameter, FilterNumericEquals(), float(diameter / 304.8), 0.005)
    length_filter, diameter_filter = ElementParameterFilter(length_rule), ElementParameterFilter(diameter_rule)
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rebar)
    collector = collector.WherePasses(length_filter).WherePasses(diameter_filter)
    rebarIds = collector.WhereElementIsNotElementType().ToElementIds()
    rebarIds = WorksharingUtils.CheckoutElements(doc, rebarIds)
    return rebarIds


def create_view_template(doc, uiapp):
    with Transaction(doc, "Create view template") as trans:
        try:
            trans.Start()
            postCommand = Autodesk.Revit.UI.PostableCommand.CreateTemplateFromCurrentView
            commandId = Autodesk.Revit.UI.RevitCommandId.LookupPostableCommandId(postCommand)
            uiapp.PostCommand(commandId)
            trans.Commit()
        except:
            trans.RollBack()
    return


########################################################################################################################
def set_navisworks_view(doc):
    with TransactionGroup(doc, "set_navisworks_view") as transGroup:
        transGroup.Start()
        view3D = create_3dView(doc)
        if View3D:
            set_worksets_visibility(doc, view3D)
            set_category_visibility(doc, view3D)
            hide_links_visibility(doc, view3D)
            section = os.path.basename(os.path.dirname(os.path.dirname(doc.PathName)))
            with Transaction(doc, "SetSolidInView") as trans:
                if any([(section.endswith("KJ")), (section.endswith("KG"))]):
                    for diameter in range(2, 60, 2):
                        rebarIds = get_rebar_ids_by_diameter(doc, diameter)
                        if view3D and len(rebarIds):
                            try:
                                trans.Start()
                                [doc.GetElement(rid).SetSolidInView(view3D, True) for rid in rebarIds]
                                trans.Commit()
                            except:
                                trans.RollBack()
        transGroup.Assimilate()
        return view3D
########################################################################################################################
