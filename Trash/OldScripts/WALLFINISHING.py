#!/usr/bin/python
# -*- coding: utf-8 -*-

import clr

clr.AddReference("System")
from System.Collections.Generic import Dictionary, List

clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import \
    ElementId, XYZ, Line, WallType, Wall, View3D, FilteredElementCollector, BuiltInCategory, BuiltInParameter, \
    Transaction, \
    FilterStringContains, FilterNumericLessOrEqual, FilterNumericGreater, \
    FilterDoubleRule, FilterStringRule, LogicalAndFilter, ParameterValueProvider, ExclusionFilter, \
    ElementMulticategoryFilter, ElementParameterFilter, ElementLevelFilter, BoundingBoxIntersectsFilter, \
    Outline, SetComparisonResult, IntersectionResultArray, ViewType, SpatialElement

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.GeometryReferences)

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

# clr.AddReference("RevitAPIUI")
# clr.AddReference('RevitAPIIFC')
# from Autodesk.Revit.DB.Structure import *
# from Autodesk.Revit.DB.IFC import ExporterIFCUtils
# from Autodesk.Revit.UI.Selection import ObjectType
# from Autodesk.Revit.ApplicationServices import *
# from Autodesk.Revit.Attributes import *
# from Autodesk.Revit.UI import *

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import re, difflib

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


def GetFilterDoubleParameter(bip, value):
    provider = ParameterValueProvider(ElementId(bip))
    filterrule = FilterDoubleRule(provider, FilterNumericLessOrEqual(), value, 0.05)
    ParameterFilter = ElementParameterFilter(filterrule)
    return ParameterFilter


def GetFilterStringParameter(bip, value):
    provider = ParameterValueProvider(ElementId(bip))
    filterrule = FilterStringRule(provider, FilterStringContains(), value, False)
    ParameterFilter = ElementParameterFilter(filterrule)
    return ParameterFilter


def deleted_wall_by_group_model(room, model_mark):
    deleted = None
    bbox = room.get_BoundingBox(None)
    min_bbox = bbox.Transform.OfPoint(bbox.Min)
    max_bbox = bbox.Transform.OfPoint(bbox.Max)
    bbox_filter = BoundingBoxIntersectsFilter(Outline(min_bbox, max_bbox))
    provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_MODEL))
    filterrule = FilterStringRule(provider, FilterStringContains(), model_mark, False)
    string_filter = ElementParameterFilter(filterrule)
    logic_filter = LogicalAndFilter(bbox_filter, string_filter)
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls)
    for delid in collector.WherePasses(logic_filter).WhereElementIsNotElementType().ToElementIds():
        try:
            doc.Delete(delid)
            doc.Regenerate()
        except:
            pass
        else:
            deleted = 'Deleted finishes in room ' + str(room.Number)
    return deleted


def get_walltypes(model_mark='Отделка'):
    collector = FilteredElementCollector(doc).OfClass(WallType)
    widht_filter = GetFilterDoubleParameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM, 0.5)
    string_filter = GetFilterStringParameter(BuiltInParameter.ALL_MODEL_MODEL, model_mark)
    logic_filter = LogicalAndFilter(widht_filter, string_filter)
    return collector.WherePasses(logic_filter).WhereElementIsElementType().ToElements()


def underdeterminable_walltype(walltypeName, walltypes):
    for walltype in walltypes:
        if (walltype.Kind == DB.WallKind.Basic):
            name = walltype.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            if name == walltypeName: return walltype
    function1, function2 = None, None
    newtype = walltypes[0].Duplicate(walltypeName)
    layers = List[DB.CompoundStructureLayer]()
    for material in FilteredElementCollector(doc).OfClass(DB.Material).ToElements():
        if not function1 and "окраска" in material.Name.lower():
            function1 = DB.MaterialFunctionAssignment.Finish1
            layers.Add(DB.CompoundStructureLayer(5.0 / 304.8, function1, material.Id))
        if not function2 and "штукатур" in material.Name.lower():
            function2 = DB.MaterialFunctionAssignment.Finish2
            layers.Add(DB.CompoundStructureLayer(15.0 / 304.8, function2, material.Id))
        if bool(function1) and bool(function2):
            cstruct = DB.CompoundStructure.CreateSimpleCompoundStructure(layers)
            cstruct.StructuralMaterialIndex = 0
            cstruct.SetNumberOfShellLayers(DB.ShellLayerType.Interior, 0)
            cstruct.SetNumberOfShellLayers(DB.ShellLayerType.Exterior, 0)
            newtype.SetCompoundStructure(cstruct)
            doc.Regenerate()
            return newtype


def get_finishtype(walltypes, base_integer, apartment, department, undefined_type):
    result, tolerance = undefined_type, 0.5
    if not apartment: apartment = 'undefined'
    apartment, department = apartment.lower(), department.lower()
    if base_integer == None: return None
    for walltype in walltypes:
        weight = float(0)
        walltype = doc.GetElement(walltype.Id)
        if bool(walltype) and base_integer == walltype.LookupParameter('Тип поверхности отделки').AsInteger():
            comment = strip_stringline(walltype.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS).AsString())
            if apartment in comment: return walltype
            weight += round(max(difflib.SequenceMatcher(None, apartment, word).ratio() for word in comment), 3)
            weight += round(max(difflib.SequenceMatcher(None, department, word).ratio() for word in comment), 3)
            if (weight > tolerance):
                tolerance = weight
                result = walltype
    return result


def get_element_by_point(center, elevation, radius=0.5):
    builtInCats = List[BuiltInCategory]()
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_StructuralFraming)
    builtInCats.Add(BuiltInCategory.OST_StructuralColumns)
    builtInCats.Add(BuiltInCategory.OST_MechanicalEquipment)
    categfilter = ElementMulticategoryFilter(builtInCats)
    center = XYZ(center.X, center.Y, elevation + radius * 0.5)
    pmin = center - radius * XYZ(0.5, 0.5, 0.5).Normalize()
    pmax = center + radius * XYZ(0.5, 0.5, 0.5).Normalize()
    bboxfilter = BoundingBoxIntersectsFilter(Outline(pmin, pmax))
    logicfilter = LogicalAndFilter(bboxfilter, categfilter)
    collector = FilteredElementCollector(doc).WhereElementIsViewIndependent()
    return collector.WherePasses(logicfilter).FirstElement()


def strip_stringline(string_line, chars=""):
    string_line = re.sub(r"[_#%!?@$;.,()]+", ' ', string_line)
    string_line = re.sub(r"(\b|\s+\-?|^\-?)(\d+|\d*\.\d+)\b", "", string_line)
    string_line = string_line.strip(chars)
    return string_line.lower()


def get_intersection(previous, following, tolerance=0.5):
    results = clr.Reference[IntersectionResultArray]()
    result = previous.Intersect(following, results)
    if result == SetComparisonResult.Overlap:
        intersection = results.Item[0]
        return intersection.XYZPoint
    p1 = previous.GetEndPoint(0)
    q1 = previous.GetEndPoint(1)
    p2 = following.GetEndPoint(0)
    q2 = following.GetEndPoint(1)
    v1, v2, v3 = q1 - p1, q2 - p2, p2 - p1
    if not v1.CrossProduct(v2).IsZeroLength():
        try:
            c = round((v2.X * v3.Y - v2.Y * v3.X), 9) / round((v2.X * v1.Y - v2.Y * v1.X), 9)
            x = round((p1.X + c * v1.X), 9)
            y = round((p1.Y + c * v1.Y), 9)
            z = round((p1.Z + c * v1.Z), 9)
        except:
            delta = tolerance * v1.Normalize()
            previous = Line.CreateBound(p1, q1 + delta)
            return previous.Project(p2).XYZPoint
        else:
            return XYZ(x, y, z)


def wallfinish_generator(room, walltypes, defaultype, elevation):
    options = DB.SpatialElementBoundaryOptions()
    options.StoreFreeBoundaryFaces = True
    options.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Finish
    boundsegmentgen = (_ for segmentlist in room.GetBoundarySegments(options) for _ in segmentlist)
    for segment in boundsegmentgen:
        curve = segment.GetCurve()
        if curve.ApproximateLength < 0.05: continue
        point, qoint, center = curve.GetEndPoint(0), curve.GetEndPoint(1), curve.Evaluate(0.5, True)
        point, qoint = XYZ(point.X, point.Y, elevation), XYZ(qoint.X, qoint.Y, elevation)
        direction = (qoint - point).Normalize()
        crossvector = direction.CrossProduct(XYZ.BasisZ).Normalize()
        element = doc.GetElement(segment.ElementId)
        if element is None: element = get_element_by_point(center, elevation)
        if element is None: element = get_element_by_point(center, elevation, curve.ApproximateLength)
        if isinstance(element, DB.RevitLinkInstance): element = element.Document.GetElement(segment.LinkElementId)
        basic_name, basic_mat_int = None, None
        if isinstance(element, DB.Wall):
            basic_type = element.Document.GetElement(element.GetTypeId())
            basic_name = basic_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            basic_name = strip_stringline(basic_name, "t=")
            com_struct = basic_type.GetCompoundStructure()
            if bool(com_struct):
                for layer in com_struct.GetLayers():
                    if layer.Function == DB.MaterialFunctionAssignment.Finish1:
                        material = doc.GetElement(layer.MaterialId)
                        basic_name = basic_name + ' ' + strip_stringline(material.Name)
                    if layer.Function == DB.MaterialFunctionAssignment.Finish2:
                        material = doc.GetElement(layer.MaterialId)
                        basic_name = basic_name + ' ' + strip_stringline(material.Name)
        elif isinstance(element, DB.FamilyInstance):
            basic_type = element.Document.GetElement(element.GetTypeId())
            basic_name = basic_type.get_Parameter(BuiltInParameter.ALL_MODEL_FAMILY_NAME).AsString()
            basic_name = strip_stringline(basic_name, "Прямоугольная")
        elif isinstance(element, DB.ModelLine) and curve.ApproximateLength < 2.5:
            element = get_element_by_point(center, elevation)
            if bool(element):
                basic_type = element.Document.GetElement(element.GetTypeId())
                basic_name = basic_type.get_Parameter(BuiltInParameter.ALL_MODEL_FAMILY_NAME).AsString()
                basic_name = strip_stringline(basic_name, "сборный")

        if bool(basic_name):
            if 'газоблок' in basic_name:
                basic_mat_int = 1
            elif 'кирпич' in basic_name:
                basic_mat_int = 2
            elif 'бетон' in basic_name:
                basic_mat_int = 3
            elif 'монолит' in basic_name:
                basic_mat_int = 3
            elif 'венткороб' in basic_name:
                basic_mat_int = 3
            elif 'ГКЛ' in basic_name:
                basic_mat_int = 4
            elif 'гипс' in basic_name:
                basic_mat_int = 4
            elif 'картон' in basic_name:
                basic_mat_int = 4

        finishtype = get_finishtype(walltypes, basic_mat_int, apartment, department, defaultype)
        if finishtype is None: finishtype = defaultype
        half_value = 0.5 * finishtype.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM).AsDouble()
        if isinstance(element, DB.Wall) and element.WallType.Kind != DB.WallKind.Curtain:
            if not DB.WallUtils.IsWallJoinAllowedAtEnd(element, 0): DB.WallUtils.DisallowWallJoinAtEnd(element, 0)
            if not DB.WallUtils.IsWallJoinAllowedAtEnd(element, 1): DB.WallUtils.DisallowWallJoinAtEnd(element, 1)
            # half_width = 0.5 * element.WallType.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM).AsDouble()
            delta = half_value * crossvector
            if room.IsPointInRoom(center - delta):
                curve = Line.CreateBound(qoint - delta, point - delta)
            if room.IsPointInRoom(center + delta):
                curve = Line.CreateBound(point + delta, qoint + delta)
        if isinstance(element, DB.FamilyInstance):
            delta = half_value * crossvector
            if room.IsPointInRoom(center - 0.5 * crossvector):
                curve = Line.CreateBound(qoint - delta, point - delta)
            elif room.IsPointInRoom(center + 0.5 * crossvector):
                curve = Line.CreateBound(point + delta, qoint + delta)

        yield Dictionary[str, object]({'workset_name': curve, 'type': finishtype, 'element0': element})


def group_closed_borderlines(boundiclist, tolerance=0.5):
    grouped_curves, queue = [], set()
    boundiclist = boundiclist[::-1]
    while boundiclist:
        group = []
        queue.add(boundiclist.pop())
        while queue:
            count = len(boundiclist)
            current = queue.pop()
            group.append(current)
            endpt = current['workset_name'].GetEndPoint(1)
            for idx, boundictionary in enumerate(boundiclist):
                curve = boundictionary['workset_name']
                if tolerance > curve.GetEndPoint(0).DistanceTo(endpt):
                    curve = Line.CreateBound(curve.GetEndPoint(0), curve.GetEndPoint(1))
                    boundictionary['workset_name'] = curve
                    queue.add(boundictionary)
                    count = idx
                    break
                if tolerance > curve.GetEndPoint(1).DistanceTo(endpt):
                    curve = Line.CreateBound(curve.GetEndPoint(1), curve.GetEndPoint(0))
                    boundictionary['workset_name'] = curve
                    queue.add(boundictionary)
                    count = idx
                    break
            boundiclist = [dic for idx, dic in enumerate(boundiclist) if idx != count]
        grouped_curves.append(group)
    return grouped_curves


def reduced_closed_borderlines(boundiclist):
    for idx, current in enumerate(boundiclist):
        if current is None: continue
        previous = group[idx - 1]
        v1 = previous['workset_name'].Direction.Normalize()
        v2 = current['workset_name'].Direction.Normalize()
        crossProduct = v1.CrossProduct(v2).Normalize()
        if crossProduct.IsAlmostEqualTo(XYZ.Zero, 0.005):
            previous_element, current_element = previous['element0'], current['element0']
            if previous_element.Category.Id.ToString() == "-2000011" == current_element.Category.Id.ToString():
                if current_element.WallType.Kind == DB.WallKind.Curtain: continue
                if previous['type'].Id.IntegerValue == current['type'].Id.IntegerValue:
                    point, qoint = previous['workset_name'].GetEndPoint(0), current['workset_name'].GetEndPoint(1)
                    count, dictionary, pydict = 0, Dictionary[str, object](), dict(previous)
                    for key in pydict.iterkeys():
                        if 'element' in key:
                            dictionary[key] = pydict.get(key)
                            count += 1
                    dictionary.Add('workset_name', Line.CreateBound(point, qoint))
                    dictionary.Add('element' + str(count), current_element)
                    dictionary.Add('type', current['type'])
                    group[idx], group[idx - 1] = dictionary, None
        elif crossProduct.IsAlmostEqualTo(XYZ.BasisZ, 0.05):
            point = get_intersection(previous['workset_name'], current['workset_name'])
            p1, q2 = previous['workset_name'].GetEndPoint(0), current['workset_name'].GetEndPoint(1)
            if p1.DistanceTo(point) > 0.5: previous['workset_name'] = Line.CreateBound(p1, point)
            if q2.DistanceTo(point) > 0.5: current['workset_name'] = Line.CreateBound(point, q2)

    return [current for current in boundiclist if current is not None]


def get_rayIntersection(point, direction, view3D, element):
    filter = DB.ElementClassFilter(Wall)
    refIntersector = DB.ReferenceIntersector(filter, DB.FindReferenceTarget.Face, view3D)
    referenceWithContext = refIntersector.FindNearest(point, direction)
    reference = referenceWithContext.GetReference()
    if bool(reference) and reference.ElementId == element.Id: return reference.GlobalPoint


class warning_dismiss(DB.IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        fail_accessor = failuresAccessor.GetFailureMessages()
        for failure in fail_accessor.GetEnumerator():
            fail_severity = failure.GetSeverity()
            if (fail_severity == DB.FailureSeverity.Warning):
                failuresAccessor.DeleteWarning(failure)
        return DB.FailureProcessingResult.Continue


########################################################################################################################
actiview, informs = doc.ActiveView, set()
if actiview.ViewType == ViewType.FloorPlan:
    level = doc.ActiveView.GenLevel
    walltypes = get_walltypes('Отделка')
    elevation = level.Elevation
    with Transaction(doc, "CreateWallFinishing") as trax:
        trax.Start()
        fail_options = trax.GetFailureHandlingOptions()
        fail_options.SetFailuresPreprocessor(warning_dismiss())
        trax.SetFailureHandlingOptions(fail_options)
        collector = FilteredElementCollector(doc).OfClass(SpatialElement)
        double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_AREA))
        double_rule = FilterDoubleRule(double_pvp, FilterNumericGreater(), 5.0, 0.5)
        string_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_NAME))
        string_rule = FilterStringRule(string_pvp, FilterStringContains(), 'Лестничная', True)
        level_filter, param_filter = ElementLevelFilter(level.Id), ElementParameterFilter(double_rule)
        logic_filter, string_filter = LogicalAndFilter(level_filter, param_filter), ElementParameterFilter(string_rule)
        excluding = collector.OfCategory(BuiltInCategory.OST_Rooms).WherePasses(string_filter).ToElementIds()
        collector = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Rooms)
        if any(excluding): collector = collector.WherePasses(ExclusionFilter(List[ElementId](excluding)))
        rooms = collector.WherePasses(logic_filter).ToElements()
        defaultype = underdeterminable_walltype('underdeterminable', walltypes)
        finishes = list()
        for room in rooms:
            tolerance = float(0)
            apartment = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
            department = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT).AsString()
            info = deleted_wall_by_group_model(room, "Отделка")
            if bool(info) and not IN[0]: informs.add(info)
            if IN[0] and bool(department):
                height = room.get_Parameter(BuiltInParameter.ROOM_HEIGHT).AsDouble()
                height = float(round(height * 304.8) / 150 * 150) / 304.8
                boundgenerator = wallfinish_generator(room, walltypes, defaultype, elevation)
                boundictionaries = list(dic for dic in boundgenerator if dic is not None)
                for group in group_closed_borderlines(boundictionaries):
                    for boundic in reduced_closed_borderlines(group):
                        curve, element = boundic['workset_name'], boundic['element0']
                        catname = element.Category.Id.ToString()
                        if catname == "-2000066": continue
                        if catname == "-2000011" and (element.WallType.Kind == DB.WallKind.Curtain): continue
                        wall = Wall.Create(doc, curve, boundic['type'].Id, level.Id, height, 0, True, False)
                        wall.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(room.Number)
                        wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(0)
                        finishes.append(wall.Id)
                        if catname == "-2000011":
                            for key in dict(boundic).iterkeys():
                                if 'element' in key:
                                    element = boundic[key]
                                    if wall.Id not in DB.JoinGeometryUtils.GetJoinedElements(doc, element):
                                        try:
                                            DB.JoinGeometryUtils.JoinGeometry(doc, wall, element)
                                        except:
                                            pass
                                        else:
                                            DB.JoinGeometryUtils.SwitchJoinOrder(doc, wall, element)

        doc.Regenerate()
        if any(finishes) and IN[0]:
            opt = DB.Options()
            opt.ComputeReferences = True
            opt.IncludeNonVisibleObjects = True
            opt.DetailLevel = DB.ViewDetailLevel.Medium
            exclusion_filter = ExclusionFilter(List[ElementId](finishes))
            view3D = [view for view in FilteredElementCollector(doc).OfClass(View3D) if not (view.IsTemplate)][0]
            for wid in finishes:
                wall = doc.GetElement(wid)
                if wall is None: continue
                solid = [geom for geom in wall.get_Geometry(opt) if isinstance(geom, DB.Solid)][0]
                filter = DB.ElementIntersectsSolidFilter(solid)
                collector = FilteredElementCollector(doc).OfClass(Wall).WherePasses(filter)
                element = collector.WherePasses(exclusion_filter).FirstElement()
                if bool(element):
                    curve = wall.Location.Curve
                    point = curve.Evaluate(0.5, True)
                    direction = curve.Direction.Normalize()
                    height = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
                    intersection = get_rayIntersection(point, direction.Negate(), view3D, element)
                    if bool(intersection):
                        try:
                            line = Line.CreateBound(intersection, curve.GetEndPoint(1))
                            iwall = Wall.Create(doc, line, wall.GetTypeId(), level.Id, height, 0, True, False)
                            iwall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(0)
                            DB.WallUtils.DisallowWallJoinAtEnd(iwall, 0)
                            doc.Delete(wall.Id)
                        except:
                            pass
                    intersection = get_rayIntersection(point, direction, view3D, element)
                    if bool(intersection):
                        try:
                            line = Line.CreateBound(curve.GetEndPoint(0), intersection)
                            iwall = Wall.Create(doc, line, wall.GetTypeId(), level.Id, height, 0, True, False)
                            iwall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(0)
                            DB.WallUtils.DisallowWallJoinAtEnd(iwall, 1)
                            doc.Delete(wall.Id)
                        except:
                            pass

        trax.Commit()

#######################################################################################################################
# selids = List[ElementId]()
# for i in informs:
#     selids.Add(i)
# uidoc.Selection.SetElementIds(selids)
#######################################################################################################################

OUT = informs
