#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import re
import clr
import difflib

clr.AddReference('RevitAPI')

from Autodesk.Revit.DB import SubTransaction
from Autodesk.Revit.DB import WorksetVisibility, WorksetId
from Autodesk.Revit.DB import WorksetDefaultVisibilitySettings, RevitLinkType
from Autodesk.Revit.DB import ImportInstance
from Autodesk.Revit.DB import View3D, ViewFamily, ViewFamilyType
from Autodesk.Revit.DB import ParameterFilterUtilities
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import Category, CategoryType, BuiltInParameterGroup
from Autodesk.Revit.DB import XYZ, Grid, UnitUtils, DisplayUnitType, Transform
from Autodesk.Revit.DB import Curve, CurveLoop, GeometryCreationUtilities
from Autodesk.Revit.DB import SharedParameterElement, StorageType
from Autodesk.Revit.DB import WorksharingUtils, FilteredWorksetCollector, WorksetKind
from Autodesk.Revit.DB import FilterNumericLessOrEqual, FilterNumericGreaterOrEqual
from Autodesk.Revit.DB import ExclusionFilter, Outline, ElementIntersectsSolidFilter
from Autodesk.Revit.DB import BoundingBoxXYZ, BoundingBoxIntersectsFilter, LogicalOrFilter
from Autodesk.Revit.DB import Options, Solid, GeometryInstance, ViewDetailLevel
from Autodesk.Revit.DB import ElementId, Level, FamilyInstance, Structure, Floor
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter
from Autodesk.Revit.DB import LogicalAndFilter, ElementMulticategoryFilter, ElementLevelFilter
from Autodesk.Revit.DB import SharedParameterApplicableRule, FilterNumericEquals
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter
from Autodesk.Revit.DB import FilterDoubleRule, FilterIntegerRule, FilterStringRule
from Autodesk.Revit.DB import FilterNumericGreater, FilterNumericLess
from Autodesk.Revit.DB import FilterStringContains, FilterStringEquals
from Autodesk.Revit.DB import ViewSchedule

clr.AddReference("System")
clr.AddReference("System.Core")
import System
from System.Collections.Generic import List
from System.IO import Path

########################################################################################################################

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitNodes")
import Revit
import Autodesk

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

########################################################################################################################

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName
revit_file_name = Path.GetFileNameWithoutExtension(revit_file_path)
revit_file_name = revit_file_name.split("_detached")[0].split("_отсоединено")[0].strip()
revit_file_name = revit_file_name.encode('cp1251', 'ignore').decode('cp1251').strip()
TransactionManager.Instance.ForceCloseTransaction()


def Output(output):
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return


########################################################################################################################
########################################################################################################################
def delete_imported_DWG(doc):
    DWG_to_deleteIList = List[ElementId]()
    for dwg in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        DWG_to_deleteIList.Add(dwg.Id)
    if any(DWG_to_deleteIList):
        doc.Delete(DWG_to_deleteIList)
        return


def create_3dView(doc, view_name="3D_Navisworks"):
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
    uidoc.RequestViewChange(view3D)
    uidoc.RefreshActiveView()
    return view3D


def hide_links_visibility(doc, view):
    imports = FilteredElementCollector(doc, view.Id).OfClass(ImportInstance).ToElementIds()
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RvtLinks).OfClass(RevitLinkType)
    with Transaction(doc, "Links Hide Visibility") as trans:
        trans.Start()
        [doc.Delete(dwgId) for dwgId in imports if isinstance(dwgId, ElementId)]
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


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        definition = group.Definitions.Item[parameter_name]
        if definition and group.Definitions.Contains(definition):
            return definition


def get_internal_guid_by_name(doc, parameter_name):
    external = get_external_definition(doc, parameter_name)
    if bool(external and SharedParameterElement.Lookup(doc, external.GUID)):
        return external.GUID


def get_schedule_by_parameter(doc, parameter):
    paramId, parameter_name = parameter.Id, parameter.Name
    for schedule in FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements():
        for param in schedule.GetParameters(parameter_name):
            if param.Id == paramId:
                return schedule


def set_parameter_to_schedule(schedule, parameter):
    definition, paramId = schedule.Definition, parameter.Id
    for field in definition.GetSchedulableFields():
        if field.ParameterId == paramId:
            definition.AddField(field)
            return schedule


def create_category_set(doc, categoryIds=None):
    categorySet = doc.Application.Create.NewCategorySet()
    for cid in ParameterFilterUtilities.GetAllFilterableCategories():
        category = Category.GetCategory(doc, ElementId(cid.IntegerValue))
        if category and category.CategoryType == CategoryType.Model:
            if category.AllowsBoundParameters and category.CanAddSubcategory:
                categoryIdint = category.Id.IntegerValue
                if categoryIds and str(categoryIdint) in categoryIds:
                    builtInCategory = System.Enum.ToObject(BuiltInCategory, categoryIdint)
                    categorySet.Insert(doc.Settings.Categories.get_Item(builtInCategory))
                if not categoryIds and bool(category.HasMaterialQuantities or category.IsCuttable):
                    builtInCategory = System.Enum.ToObject(BuiltInCategory, categoryIdint)
                    categorySet.Insert(doc.Settings.Categories.get_Item(builtInCategory))
    return categorySet


def reset_shared_parameter(doc, parameter_name, categoryIds=None, parameter_group="PG_DATA"):
    message = "Not exist parameter <{}>".format(parameter_name)
    external = get_external_definition(doc, parameter_name)
    if not external: return Output(message)
    binding = doc.Application.Create.NewInstanceBinding(create_category_set(doc, categoryIds))
    message, guid, group = "", external.GUID, System.Enum.Parse(BuiltInParameterGroup, parameter_group)
    shared_parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
    if not any([param for param in shared_parameters if param.GuidValue == guid]):
        with Transaction(doc, "Try set {}".format(parameter_name)) as trans:
            try:
                trans.Start()
                message = "Set parameter {}".format(parameter_name)
                if doc.ParameterBindings.Insert(external, binding, group): Output(message)
                message = ""
                trans.Commit()
            except:
                trans.RollBack()
    for param in shared_parameters:
        weight = difflib.SequenceMatcher(None, param.Name.lower(), parameter_name.lower())
        if bool(weight.ratio() > 0.85):
            with Transaction(doc, "Reset {}".format(parameter_name)) as trans:
                try:
                    trans.Start()
                    map = doc.ParameterBindings
                    guid_value = param.GuidValue
                    if guid_value == guid:
                        definition = param.GetDefinition()
                        if not map.ReInsert(definition, binding, group):
                            if map.Remove(definition): map.Insert(definition, binding, group)
                    elif guid_value != guid:
                        schedule = get_schedule_by_parameter(doc, param)
                        parameter = SharedParameterElement.Lookup(doc, guid)
                        if schedule and parameter:
                            set_parameter_to_schedule(schedule, parameter)
                            view_name = schedule.get_Parameter(BuiltInParameter.VIEW_NAME).AsString()
                            message += "\nPlease reset parameter {} in {}!".format(param.Name, view_name)
                        else:
                            doc.Delete(param.Id)
                    trans.Commit()
                except Exception as e:
                    Output("Exception: {}".format(e))
                    trans.RollBack()
    if len(message): Output(message)
    return


def get_levelId_by_name(name):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.DATUM_TEXT))
    name_filter = ElementParameterFilter(FilterStringRule(provider, FilterStringContains(), name, False))
    levelId = FilteredElementCollector(doc).OfClass(Level).WherePasses(name_filter).FirstElementId()
    return levelId


def get_valid_levels(doc):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    floor_rule = FilterDoubleRule(provider, FilterNumericLessOrEqual(), float(300), 0.0005)
    levels = FilteredElementCollector(doc).OfClass(Level).WherePasses(ElementParameterFilter(floor_rule)).ToElements()
    levels = sorted(levels, key=lambda x: x.Elevation)
    return levels


def get_average_level_height(levels):
    elevations = [x.Elevation for x in levels]
    height = (max(elevations) - min(elevations)) / len(levels)
    height = (round(height * 304.8 / 300) * 300 / 304.8)
    min_height, max_height = (2500 / 304.8), (4500 / 304.8)
    height = (min_height if height < min_height else height)
    height = (max_height if height > max_height else height)
    return height


def get_above_level_and_height(level, levels):
    elevation, average = level.Elevation, get_average_level_height(levels)
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    rule_min = FilterDoubleRule(provider, FilterNumericGreaterOrEqual(), float(elevation), 0.005)
    rule_max = FilterDoubleRule(provider, FilterNumericLessOrEqual(), float(elevation + average * 3), 0.005)
    logic_filter = LogicalAndFilter(ElementParameterFilter(rule_min), ElementParameterFilter(rule_max))
    levels = FilteredElementCollector(doc).OfClass(Level).WherePasses(logic_filter).ToElements()
    levels = list(level for level in levels if elevation <= level.Elevation)
    levels = sorted(levels, key=lambda x: x.ProjectElevation)
    above = (level if len(levels) == 1 else levels[1])
    height = float(above.Elevation - level.Elevation)
    return above, height


def get_level_number(level, levels):
    elevator, top = float(0), int(len(levels) - 3)
    levelId, number = level.Id.IntegerValue, int(0)
    value = level.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsDouble()
    datum_name = level.Name.encode('cp1251', 'ignore').decode('cp1251').strip()
    datum_name = ''.join(filter(lambda i: i.isalpha() or i.isspace(), datum_name))
    elevation = round(UnitUtils.ConvertFromInternalUnits(value, DisplayUnitType.DUT_METERS))
    if elevation > 5 and re.search(r"\b(Будка)\b", datum_name, re.UNICODE | re.IGNORECASE): return int(101)
    if elevation > 5 and re.search(r"\b(Кровля)\b", datum_name, re.UNICODE | re.IGNORECASE): return int(100)
    if elevation > 5 and re.search(r"\b(Чердак)\b", datum_name, re.UNICODE | re.IGNORECASE): return int(99)
    levels = sorted(levels, key=lambda x: x.Elevation)
    undeground = bool(elevation < 0)
    if undeground: reversed(levels)
    for idx, current in enumerate(levels):
        currentId = current.Id.IntegerValue
        currentName = current.Name.encode('ascii', 'ignore')
        dumber = ''.join(filter(lambda i: i.isdigit(), currentName))
        value = level.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsDouble()
        dumber = int(dumber if (not undeground and dumber and int(dumber) < top) else number)
        elevation = round(UnitUtils.ConvertFromInternalUnits(value, DisplayUnitType.DUT_METERS))
        calculate = (True if not dumber and abs(elevation - elevator) > 1.8 else False)
        number = int(dumber if (not undeground and not calculate) else number)
        if (calculate and elevation > 0): number += 1
        if (calculate and elevation < 0): number -= 1
        if (elevation == 0): number = 1
        if currentId == levelId: break
        elevator = elevation
    return number


def get_level_by_elevation(elevation, average):
    provide = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    rule_min = FilterDoubleRule(provide, FilterNumericGreaterOrEqual(), float(elevation), 0.05)
    rule_max = FilterDoubleRule(provide, FilterNumericLessOrEqual(), float(elevation + average), 0.05)
    logic_filter = LogicalAndFilter(ElementParameterFilter(rule_min), ElementParameterFilter(rule_max))
    level = FilteredElementCollector(doc).OfClass(Level).WherePasses(logic_filter).FirstElement()
    return level


def get_elementIds_by_level(doc, level):
    builtInCats = List[BuiltInCategory]()
    level_filter = ElementLevelFilter(level.Id)
    builtInCats.Add(BuiltInCategory.OST_Roofs)
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_Ramps)
    category_filter = ElementMulticategoryFilter(builtInCats)
    logic_filter = LogicalAndFilter(level_filter, category_filter)
    collector = FilteredElementCollector(doc).WherePasses(logic_filter)
    result = collector.WhereElementIsNotElementType().ToElementIds()
    return result


def get_floorIds_by_level(doc, above, level):
    level00, level01 = ElementLevelFilter(above.Id), ElementLevelFilter(level.Id)
    provider = ParameterValueProvider(ElementId(BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL))
    filter00 = ElementParameterFilter(FilterIntegerRule(provider, FilterNumericEquals(), 1))
    filter01 = ElementParameterFilter(FilterIntegerRule(provider, FilterNumericEquals(), 0))
    floor_filter = LogicalOrFilter(LogicalAndFilter(level00, filter00), LogicalAndFilter(level01, filter01))
    collector = FilteredElementCollector(doc).OfClass(Floor).WherePasses(floor_filter)
    result = collector.WhereElementIsNotElementType().ToElementIds()
    return result


def get_familyIds_by_level(doc, level, number, parameter):
    lvl_filter = ElementLevelFilter(level.Id)
    prm_provider = ParameterValueProvider(parameter.Id)
    rht_provider = ParameterValueProvider(ElementId(BuiltInParameter.FAMILY_CAN_HOST_REBAR))
    filter01 = ElementParameterFilter(FilterIntegerRule(rht_provider, FilterNumericEquals(), 1))
    filter02 = ElementParameterFilter(FilterIntegerRule(prm_provider, FilterNumericEquals(), 0))
    filter03 = ElementParameterFilter(FilterIntegerRule(prm_provider, FilterNumericGreater(), number))
    collector = FilteredElementCollector(doc).OfClass(FamilyInstance).WherePasses(lvl_filter)
    collector = collector.WherePasses(filter01).WherePasses(LogicalOrFilter(filter02, filter03))
    result = collector.WhereElementIsViewIndependent().WhereElementIsNotElementType().ToElementIds()
    return result


def get_solid_geometry(element):
    opt = Options()
    opt.ComputeReferences = True
    opt.IncludeNonVisibleObjects = True
    opt.DetailLevel = ViewDetailLevel.Medium
    for geom in element.get_Geometry(opt):
        if geom.GetType() == Solid and geom.Faces.Size > 0: return geom
        if geom.GetType() == GeometryInstance:
            for obj in geom.SymbolGeometry:
                if obj.GetType() == Solid and obj.Faces.Size > 0:
                    return obj


def get_rebarIds_by_structural(doc, element_ids):
    result = set()
    hostData = Structure.RebarHostData
    bmk = BuiltInParameter.ALL_MODEL_MARK
    bip = BuiltInParameter.REBAR_ELEM_HOST_MARK
    provider = ParameterValueProvider(ElementId(bip))
    guid = get_internal_guid_by_name(doc, "BI_марка_конструкции")
    for elemId in element_ids:
        element = doc.GetElement(elemId)
        solid = get_solid_geometry(element)
        if bool(solid):
            rebars = set()
            builtInCats = List[BuiltInCategory]()
            builtInCats.Add(BuiltInCategory.OST_Rebar)
            builtInCats.Add(BuiltInCategory.OST_AreaRein)
            host = hostData.GetRebarHostData(element)
            mark = element.get_Parameter(bmk).AsString()
            if host: rebars.update(host.GetRebarsInHost())
            intersectionFilter = ElementIntersectsSolidFilter(solid)
            category_filter = ElementMulticategoryFilter(builtInCats)
            mark = (mark if isinstance(mark, basestring) else "indefinable")
            rule = FilterStringRule(provider, FilterStringEquals(), mark, True)
            filter = LogicalOrFilter(ElementParameterFilter(rule), intersectionFilter)
            collector = FilteredElementCollector(doc).WherePasses(category_filter)
            rebars.update(collector.WherePasses(filter).ToElementIds())
            collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_AreaRein)
            reins = collector.WherePasses(ElementParameterFilter(rule)).WhereElementIsNotElementType().ToElements()
            [rebars.update(rein.GetRebarInSystemIds()) for rein in reins]
            for rebar in rebars:
                try:
                    result.add(rebar.Id)
                    rebar.get_Parameter(guid).Set(mark)
                except:
                    pass
    return result


def get_level_by_element(element, levels, average=7):
    bbox = element.get_BoundingBox(None)
    if isinstance(bbox, BoundingBoxXYZ):
        center = (bbox.Min + bbox.Max) * 0.5
        result, value = None, center.Z
        level = get_level_by_elevation(value, average)
        if level: return level
        for current in levels:
            elevation = current.ProjectElevation
            if (elevation > value): break
            result = current
        return result


def get_solid_box(min_x, max_x, min_y, max_y, min_elevation, max_elevation):
    profile00 = XYZ(min_x, min_y, min_elevation)
    profile01 = XYZ(min_x, max_y, min_elevation)
    profile11 = XYZ(max_x, max_y, min_elevation)
    profile10 = XYZ(max_x, min_y, min_elevation)
    height = float(abs(max_elevation - min_elevation))
    line01 = Autodesk.Revit.DB.Line.CreateBound(profile00, profile01)
    line02 = Autodesk.Revit.DB.Line.CreateBound(profile01, profile11)
    line03 = Autodesk.Revit.DB.Line.CreateBound(profile11, profile10)
    line04 = Autodesk.Revit.DB.Line.CreateBound(profile10, profile00)
    profile = List[Curve]([line01, line02, line03, line04])
    loops = List[CurveLoop]([CurveLoop.Create(profile)])
    solid = GeometryCreationUtilities.CreateExtrusionGeometry(loops, XYZ.BasisZ, height)
    return solid


def set_value_to_elements(guid, element_ids, value):
    length, counts = int(0), int(0)
    definition = SharedParameterElement.Lookup(doc, guid)
    element_ids = WorksharingUtils.CheckoutElements(doc, element_ids)
    if definition and len(element_ids):
        for elementId in element_ids:
            element = doc.GetElement(elementId)
            if element.IsValidObject:
                result, param = None, element.get_Parameter(guid)
                ungroup = element.GroupId.Equals(ElementId.InvalidElementId)
                if ungroup and param:
                    length += 1
                    if param.StorageType == StorageType.String:
                        value = (value if isinstance(value, basestring) else str(value))
                        if param.IsReadOnly and param.HasValue: continue
                        try:
                            param.Set(value)
                            counts += 1
                        except:
                            pass
                    if param.StorageType == StorageType.Double:
                        value = (value if isinstance(value, float) else float(value))
                        if param.IsReadOnly and param.HasValue: continue
                        try:
                            param.Set(value)
                            counts += 1
                        except:
                            pass
                    if param.StorageType == StorageType.Integer:
                        value = (value if isinstance(value, int) else int(value))
                        if param.IsReadOnly and param.HasValue: continue
                        try:
                            param.Set(value)
                            counts += 1
                        except:
                            pass
        message = "Set values in {} out of {} items\n".format(counts, length)
        return message


def select_elements(elementIds):
    uidoc.Selection.SetElementIds(elementIds)
    uidoc.RefreshActiveView()
    return elementIds


########################################################################################################################
########################################################################################################################
stop = True
if doc.IsWorkshared:
    try:
        all_worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksetIds()
        edt_worksets = WorksharingUtils.CheckoutWorksets(doc, all_worksets)
        stop, borrow = False, len(set(all_worksets).difference(edt_worksets))
        if not (borrow < round(len(all_worksets) * 0.3)):
            Output("Need to synchronize project")
            stop = True
    except Exception as e:
        Output("Error: {}".format(e))
########################################################################################################################
view3D = create_3dView(doc)
if view3D:
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
########################################################################################################################
########################################################################################################################
message = ""
points = set()
parameter_name = "BI_этаж"
includeIds = List[ElementId]()
transform = Transform.Identity
reset_shared_parameter(doc, parameter_name)
guid = get_internal_guid_by_name(doc, parameter_name)
if not guid: Output("\nWARNING: Not parameter BI_этаж!!!\n")
grIds = FilteredElementCollector(doc).OfClass(Grid).WhereElementIsNotElementType().ToElementIds()
grids = FilteredElementCollector(doc).OfClass(Grid).WhereElementIsNotElementType().ToElements()
if len(grids): includeIds.AddRange(grIds)
if len(grids): points.update(grid.Curve.GetEndPoint(0) for grid in grids)
if len(grids): points.update(grid.Curve.GetEndPoint(1) for grid in grids)
min_x = round(min(p.X for p in points) - 5) if len(grids) else float(-500)
max_x = round(max(p.X for p in points) + 5) if len(grids) else float(1000)
min_y = round(min(p.Y for p in points) - 5) if len(grids) else float(-500)
max_y = round(max(p.Y for p in points) + 5) if len(grids) else float(1000)
with Transaction(doc, "defined elements") as trans:
    if not stop and guid:
        trans.Start()
        levels = get_valid_levels(doc)
        average = get_average_level_height(levels)
        parameter = SharedParameterElement.Lookup(doc, guid)
        parameter_filter = ElementParameterFilter(SharedParameterApplicableRule(parameter_name))
        for idx, level in enumerate(levels):
            setIds = set()
            # if idx < 20: continue
            number = get_level_number(level, levels)
            above, height = get_above_level_and_height(level, levels)
            height = average if idx > 5 and (height < average) else height
            inf_name, inf_number, inf_height = level.Name, number, float(round(height * 304.8) / 1000)
            message += "\n{}. {} defined as {} number (height {} m)\n".format(idx, inf_name, inf_number, inf_height)
            #############################################################################################
            setIds.update(get_elementIds_by_level(doc, level))
            setIds.update(get_floorIds_by_level(doc, above, level))
            setIds.update(get_familyIds_by_level(doc, level, number, parameter))
            setIds.update(get_rebarIds_by_structural(doc, setIds))
            #############################################################################################
            tolerance = float(average if number < 0 else 0.5)
            min_elev = float(level.ProjectElevation - tolerance)
            max_elev = float(level.ProjectElevation + height - 0.5)
            exclude_filter = ExclusionFilter(includeIds)
            if (round(max_elev - min_elev) > 5):
                min_point = transform.OfPoint(XYZ((min_x), (min_y), (min_elev)))
                max_point = transform.OfPoint(XYZ((max_x), (max_y), (max_elev)))
                bbox_filter = BoundingBoxIntersectsFilter(Outline(min_point, max_point))
                solid_box = get_solid_box(min_x, max_x, min_y, max_y, min_elev, max_elev)
                solid_filter = ElementIntersectsSolidFilter(solid_box)
                collector = FilteredElementCollector(doc).WhereElementIsViewIndependent()
                collector = collector.WherePasses(LogicalOrFilter(solid_filter, bbox_filter))
                collector = collector.WherePasses(parameter_filter)
                collector = collector.WherePasses(exclude_filter)
                setIds.update(collector.ToElementIds())
            collectionIds = List[ElementId](list(setIds))
            collectionIds = select_elements(collectionIds)
            counts = len(collectionIds)
            if bool(counts):
                message += set_value_to_elements(guid, collectionIds, number)
                includeIds.AddRange(collectionIds)
                if counts > 1000: doc.Regenerate()
        trans.Commit()

if len(message):
    Output(message)
    provide = ParameterValueProvider(parameter.Id)
    flt1 = ElementParameterFilter(FilterIntegerRule(provide, FilterNumericGreater(), 0))
    flt2 = ElementParameterFilter(FilterIntegerRule(provide, FilterNumericLess(), 0))
    collector = FilteredElementCollector(doc).WherePasses(parameter_filter).WhereElementIsViewIndependent()
    includeIds = collector.WherePasses(LogicalOrFilter(flt1, flt2)).WhereElementIsNotElementType().ToElementIds()
    with Transaction(doc, "Check elements") as trans:
        if len(includeIds):
            trans.Start()
            exclusion_filter = ExclusionFilter(includeIds)
            collector = FilteredElementCollector(doc).WherePasses(parameter_filter).WhereElementIsViewIndependent()
            undefinedIds = collector.WherePasses(exclusion_filter).WhereElementIsNotElementType().ToElementIds()
            undefinedIds = WorksharingUtils.CheckoutElements(doc, undefinedIds)
            set_value_to_elements(guid, undefinedIds, 000)
            trans.Commit()

########################################################################################################################
commandId = Autodesk.Revit.UI.RevitCommandId.LookupPostableCommandId(Autodesk.Revit.UI.PostableCommand.PurgeUnused)
message = "<{}> completed!!!\n".format(revit_file_name)
uiapp.PostCommand(commandId)
OUT = message
########################################################################################################################
