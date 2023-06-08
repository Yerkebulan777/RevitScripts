#!/usr/bin/python
# -*- coding: utf-8 -*-

import clr

clr.AddReference("System")
from System.Collections.Generic import Dictionary, List

clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import \
    ElementId, XYZ, Line, WallType, Wall, Transaction, FilteredElementCollector, \
    BuiltInCategory, BuiltInParameter, FilterStringContains, FilterNumericLessOrEqual, FilterNumericGreater, \
    FilterDoubleRule, FilterStringRule, LogicalAndFilter, ParameterValueProvider, ExclusionFilter, \
    ElementMulticategoryFilter, ElementParameterFilter, ElementLevelFilter, BoundingBoxIntersectsFilter, \
    Outline, ViewType, SpatialElement

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
    double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.WALL_ATTR_WIDTH_PARAM))
    double_rule = FilterDoubleRule(double_pvp, FilterNumericLessOrEqual(), 0.5, 0.05)
    double_filter = ElementParameterFilter(double_rule)
    string_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_MODEL))
    string_rule = FilterStringRule(string_pvp, FilterStringContains(), model_mark, False)
    string_filter = ElementParameterFilter(string_rule)
    logic_filter = LogicalAndFilter(double_filter, string_filter)
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
            weight += round(difflib.SequenceMatcher(None, apartment, comment).ratio(), 3)
            weight += round(difflib.SequenceMatcher(None, department, comment).ratio(), 3)
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


def wallfinish_generator(room, walltypes, defaultype, elevation):
    options = DB.SpatialElementBoundaryOptions()
    options.StoreFreeBoundaryFaces = False
    options.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Finish
    boundsegmentgen = (_ for segmentlist in room.GetBoundarySegments(options) for _ in segmentlist)
    for segment in boundsegmentgen:
        curve = segment.GetCurve()
        if curve is None: continue
        if curve.ApproximateLength < 0.05: continue
        point, qoint, center = curve.GetEndPoint(0), curve.GetEndPoint(1), curve.Evaluate(0.5, True)
        point, qoint = XYZ(point.X, point.Y, elevation), XYZ(qoint.X, qoint.Y, elevation)
        center, direction = XYZ(center.X, center.Y, elevation), (qoint - point).Normalize()
        crossvector = direction.CrossProduct(XYZ.BasisZ).Normalize()
        basic_name, basic_mat_int = None, None
        element = doc.GetElement(segment.ElementId)
        if element is None: element = get_element_by_point(center, elevation)
        if element is None: element = get_element_by_point(center, elevation, curve.ApproximateLength)
        if isinstance(element, DB.RevitLinkInstance): basic_name = 'монолитные бетонные стены и колонны'
        if isinstance(element, DB.ModelLine) and curve.ApproximateLength < 2.5:
            separation, element = element, get_element_by_point(center, elevation)
            if element is None: element = get_element_by_point(center, elevation, 0.5 * curve.ApproximateLength)
            if element is None: element = separation
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
        if isinstance(element, DB.FamilyInstance):
            basic_type = element.Document.GetElement(element.GetTypeId())
            basic_name = basic_type.get_Parameter(BuiltInParameter.ALL_MODEL_FAMILY_NAME).AsString()
            basic_name = strip_stringline(basic_name, "Прямоугольная")
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
        if room.IsPointInRoom(center - delta): curve = Line.CreateBound(qoint - delta, point - delta)
        if room.IsPointInRoom(center + delta): curve = Line.CreateBound(point + delta, qoint + delta)
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
            for idx, dictionary in enumerate(boundiclist):
                curve = dictionary['workset_name']
                if tolerance > curve.GetEndPoint(0).DistanceTo(endpt):
                    curve = Line.CreateBound(curve.GetEndPoint(0), curve.GetEndPoint(1))
                    dictionary['workset_name'] = curve
                    queue.add(dictionary)
                    count = idx
                    break
                if tolerance > curve.GetEndPoint(1).DistanceTo(endpt):
                    curve = Line.CreateBound(curve.GetEndPoint(1), curve.GetEndPoint(0))
                    dictionary['workset_name'] = curve
                    queue.add(dictionary)
                    count = idx
                    break
            boundiclist = [dic for idx, dic in enumerate(boundiclist) if idx != count]
        grouped_curves.append(group)
    return grouped_curves


class warning_dismiss(DB.IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        fail_accessor = failuresAccessor.GetFailureMessages()
        for failure in fail_accessor.GetEnumerator():
            fail_severity = failure.GetSeverity()
            if (fail_severity == DB.FailureSeverity.Warning):
                failuresAccessor.DeleteWarning(failure)
        return DB.FailureProcessingResult.Continue


def reduce_line(point, qoint, view3d, check=True):
    if check:
        center = (point + qoint) * 0.5
        lenght = point.DistanceTo(qoint) * 0.5
        builtInCats = List[BuiltInCategory]()
        builtInCats.Add(BuiltInCategory.OST_Walls)
        builtInCats.Add(BuiltInCategory.OST_Floors)
        builtInCats.Add(BuiltInCategory.OST_StructuralColumns)
        builtInCats.Add(BuiltInCategory.OST_MechanicalEquipment)
        builtInCats.Add(BuiltInCategory.OST_CurtainWallMullions)
        cat_filter = DB.ElementMulticategoryFilter(builtInCats)
        intersector = DB.ReferenceIntersector(cat_filter, DB.FindReferenceTarget.Face, view3d)
        intersector.FindReferencesInRevitLinks = False
        # start point
        direction = point.Subtract(qoint).Normalize()
        context = intersector.FindNearest(center, direction)
        if context != None and context.Proximity < lenght:
            point = center + context.Proximity * direction
        # end point
        direction = qoint.Subtract(point).Normalize()
        context = intersector.FindNearest(center, direction)
        if context != None and context.Proximity < lenght:
            qoint = center + context.Proximity * direction
    if point.DistanceTo(qoint) > 0.05:
        return Line.CreateBound(point, qoint)


########################################################################################################################
view3d = list(i for i in FilteredElementCollector(doc).OfClass(DB.View3D).ToElements() if i.IsTemplate != True)[0]
uidoc.RequestViewChange(view3d)
########################################################################################################################

undefined = list()
actiview, informs = doc.ActiveView, set()
if actiview.ViewType == ViewType.FloorPlan:
    level = doc.ActiveView.GenLevel
    walltypes = get_walltypes('Отделка')
    elevation = level.Elevation
    with Transaction(doc, "CreateWallFinishing") as trx:
        trx.Start()
        fail_options = trx.GetFailureHandlingOptions()
        fail_options.SetFailuresPreprocessor(warning_dismiss())
        trx.SetFailureHandlingOptions(fail_options)
        collector = FilteredElementCollector(doc).OfClass(SpatialElement)
        double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_AREA))
        double_rul = FilterDoubleRule(double_pvp, FilterNumericGreater(), 3.0, 0.5)
        string_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_NAME))
        string_rul = FilterStringRule(string_pvp, FilterStringContains(), 'Лестничная', True)
        level_filter, param_filter = ElementLevelFilter(level.Id), ElementParameterFilter(double_rul)
        logic_filter, string_filter = LogicalAndFilter(level_filter, param_filter), ElementParameterFilter(string_rul)
        excluding = collector.OfCategory(BuiltInCategory.OST_Rooms).WherePasses(string_filter).ToElementIds()
        collector = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Rooms)
        if any(excluding): collector = collector.WherePasses(ExclusionFilter(List[ElementId](excluding)))
        rooms = FilteredElementCollector(doc).OfClass(SpatialElement).WherePasses(logic_filter).ToElements()
        defaultype = underdeterminable_walltype('underdeterminable', walltypes)
        for room in rooms:
            tolerance = float(0)
            info = deleted_wall_by_group_model(room, "Отделка")
            apartment = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
            department = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT).AsString()
            if not bool(department): informs.add("Укажите назначение помещению: " + apartment)
            if bool(department) and len(department) < 3: informs.add("Укажите назначение помещению: " + apartment)
            if IN[0] and bool(department):
                area_param = room.get_Parameter(BuiltInParameter.ROOM_AREA)
                area = round(DB.UnitUtils.ConvertFromInternalUnits(area_param.AsDouble(), area_param.DisplayUnitType))
                height = room.get_Parameter(BuiltInParameter.ROOM_HEIGHT).AsDouble()
                height = float(round(height * 304.8) / 150 * 150) / 304.8
                boundgenerator = wallfinish_generator(room, walltypes, defaultype, elevation)
                boundictionaries = list(dic for dic in boundgenerator if dic is not None)
                if area > 15.0:
                    check = True
                else:
                    check = False
                for group in group_closed_borderlines(boundictionaries):
                    points = []
                    for idx, sequence in enumerate(group):
                        lengthen = True
                        previous = group[idx - 1]
                        element = previous['element0']
                        if isinstance(element, DB.Wall):
                            if (element.WallType.Kind == DB.WallKind.Curtain): lengthen = False
                        if lengthen and previous['type'].Id.IntegerValue == sequence['type'].Id.IntegerValue:
                            v1 = previous['workset_name'].Direction.Normalize()
                            v2 = sequence['workset_name'].Direction.Normalize()
                            if v1.CrossProduct(v2).IsAlmostEqualTo(XYZ.Zero, 0.005): continue

                        point, qoint = previous['workset_name'].GetEndPoint(0), previous['workset_name'].GetEndPoint(1)
                        delta = 0.5 * previous['workset_name'].Direction.Normalize()
                        line = Line.CreateBound(qoint - delta, qoint + delta)
                        intersection = line.Project(sequence['workset_name'].GetEndPoint(0)).XYZPoint
                        points.append(intersection)

                    for idx, qoint in enumerate(points):
                        joineds = []
                        point = points[idx - 1]
                        line = reduce_line(point, qoint, view3d, check)
                        if line is None: continue
                        # newline = doc.Create.NewDetailCurve(doc.ActiveView, workset_name)
                        # newline.LineStyle.GraphicsStyleCategory.LineColor = DB.Color(50, 125, 0)
                        group = [sequence for sequence in group if sequence is not None]
                        if any(group): group.reverse()
                        for sequence in group:
                            curve = sequence['workset_name']
                            center = curve.Evaluate(0.5, True)
                            if line.Project(center).Distance < 0.05:
                                fintype = sequence['type']
                                element = sequence['element0']
                                joineds.append(element)
                                sequence = None

                        if element is None: continue
                        catname = element.Category.Id.ToString()
                        if catname == "-2000066": continue
                        if catname == "-2000011" and (element.WallType.Kind == DB.WallKind.Curtain): continue
                        wall = Wall.Create(doc, line, fintype.Id, level.Id, height, 0, True, False)
                        wall.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(room.Number)
                        wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(0)
                        if fintype.Id.IntegerValue == defaultype.Id.IntegerValue:
                            undefined.append(wall), informs.add('walls in room ' + room.Number + ' undefined')
                        if catname == "-2000011":
                            for element in joineds:
                                try:
                                    DB.JoinGeometryUtils.JoinGeometry(doc, wall, element)
                                except:
                                    pass
                                else:
                                    DB.JoinGeometryUtils.SwitchJoinOrder(doc, wall, element)

        trx.Commit()

#######################################################################################################################

if IN[0] and any(undefined):
    undefids = List[ElementId](element.Id for element in undefined if element.IsValidObject)
    try:
        uidoc.Selection.SetElementIds(undefids)
        uidoc.RequestViewChange(actiview)
        uidoc.ShowElements(undefids)
        uidoc.RefreshActiveView()
    except:
        pass

#######################################################################################################################
OUT = sorted(list(informs))
#######################################################################################################################
