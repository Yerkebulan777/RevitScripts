#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import clr
from System.Collections.Generic import List

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import difflib

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference('RevitAPIIFC')

from Autodesk.Revit.DB \
    import FilteredElementCollector, BuiltInCategory, BuiltInParameter, \
    ElementId, Transaction, IntersectionResultArray, SetComparisonResult, \
    HostObjectUtils, Transform, CurveLoop, Curve, Options, ViewDetailLevel, \
    Line, XYZ, FilterNumericEquals, ParameterValueProvider, ElementParameterFilter, FilterDoubleRule, \
    FilterStringRule, FilterStringContains, SolidCurveIntersectionOptions, \
    ReferenceIntersector, FindReferenceTarget, ElementClassFilter, View3D, Floor, \
    WorksetTable, Workset, FilteredWorksetCollector, WorksetId, WorksharingUtils

from Autodesk.Revit.DB.Structure \
    import RebarBarType, Rebar, RebarHookOrientation, RebarStyle, RebarHostData
# from Autodesk.Revit.DB.IFC import ExporterIFCUtils
# from Autodesk.Revit.UI.Selection import ObjectType
# from Autodesk.Revit.ApplicationServices import *
# from Autodesk.Revit.Attributes import *
from Autodesk.Revit.UI import Selection

"""
import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()

doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()
"""

clr.AddReference('RevitNodes')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


def grids_main_direction(grids):
    direction = None
    max_len, dig_len, let_len, dig_num, let_num = float(0), float(0), float(0), int(0), int(0)
    for indx, grid in enumerate(grids):
        if not (grid.IsCurved):
            curve = grid.Curve
            vector = curve.Direction.Normalize()
            length = round(curve.ApproximateLength, 3)
            name = grid.get_Parameter(BuiltInParameter.DATUM_TEXT).AsString()
            if all(char.isdigit() for char in name if char):
                dig_num += 1
                dig_len += length / dig_num
                if max_len < dig_len:
                    max_len = dig_len
                    direction = vector
            else:
                let_num += 1
                let_len += length / let_num
                if max_len < let_len:
                    max_len = let_len
                    direction = vector
    return direction


def IsCollinear(line1, line2):
    direction01 = line1.Direction.Normalize()
    direction02 = line2.Direction.Normalize()
    direction03 = (line1.Origin - line2.Origin).Normalize()
    if direction01.CrossProduct(direction02).IsZeroLength():
        if direction01.CrossProduct(direction03).IsZeroLength():
            return True


def simpfly_curveloop(curveloop, clearance=0.5):
    simpfly_lines = []
    curves = [i for i in curveloop.GetEnumerator()]
    idx, current = 0, curves[0]
    qoint = current.GetEndPoint(1)
    while curves:
        reverse = None
        point = XYZ(0, 0, 0)
        tolerance = clearance
        for count, line in enumerate(curves):
            p = line.GetEndPoint(0)
            q = line.GetEndPoint(1)

            distance = p.DistanceTo(qoint)
            if tolerance > distance:
                tolerance = distance
                reverse = False
                idx = count
            distance = q.DistanceTo(qoint)
            if tolerance > distance:
                tolerance = distance
                reverse = True
                idx = count

        match = curves.pop(idx)
        if reverse == True:
            q = match.GetEndPoint(1)
            point = (qoint + q) * 0.5
            qoint = match.GetEndPoint(0)
        if reverse == False:
            p = match.GetEndPoint(0)
            point = (qoint + p) * 0.5
            qoint = match.GetEndPoint(1)
        if IsCollinear(current, match):
            try:
                current = simpfly_lines.pop()
                point = current.GetEndPoint(0)
            except:
                pass
        p = XYZ(point.X, point.Y, float(0))
        q = XYZ(qoint.X, qoint.Y, float(0))
        current = Line.CreateBound(p, q)
        simpfly_lines.append(current)
    return simpfly_lines


def offset_curveloop(curveloop, rebar_cover, inside=True):
    normal = XYZ.BasisZ
    rebar_cover = abs(rebar_cover)
    if curveloop.HasPlane():
        normal = curveloop.GetPlane().Normal
    if inside and curveloop.IsCounterclockwise(normal):
        curveloop.Flip()
    if not inside and not curveloop.IsCounterclockwise(normal):
        curveloop.Flip()
    try:
        curveloop = CurveLoop.CreateViaOffset(curveloop, rebar_cover, normal)
        return curveloop
    except:
        return curveloop


def get_floor_curveloop(floor, rebar_cover, profile=False):
    tolerance, bot_face = float(0), None
    for face in HostObjectUtils.GetBottomFaces(floor):
        planar_face = floor.GetGeometryObjectFromReference(face)
        if tolerance < planar_face.Area:
            bot_face = planar_face

    tolerance, zidx = float(0), 0
    boundary_loops, profile_loop = [], None
    for idx, loop in enumerate(bot_face.GetEdgesAsCurveLoops()):
        if loop and not loop.IsOpen():
            boundary_lines = simpfly_curveloop(loop)
            loop = CurveLoop.Create(List[Curve](boundary_lines))
            loop = offset_curveloop(loop, rebar_cover, False)
            length = loop.GetExactLength()
            boundary_loops.append(loop)
            if tolerance < length:
                boundary_lines = simpfly_curveloop(loop)
                profile_loop = CurveLoop.Create(List[Curve](boundary_lines))
                profile_loop = offset_curveloop(profile_loop, rebar_cover * 2, True)
                tolerance = length
                zidx = idx

    if profile == True:
        return profile_loop
    if profile == False:
        return [profile_loop if idx == zidx else loop for idx, loop in enumerate(boundary_loops)]


def get_cross_grids(grids, direction):
    grid_curves = []
    for grid in grids:
        if not (grid.IsCurved):
            curve = grid.Curve
            vector = curve.Direction.Normalize()
            if direction.CrossProduct(vector).IsUnitLength():
                grid_curves.append(curve)
    return grid_curves


def get_module_length(grids, start_point, end_point, diameter):
    num, points = int(0), set()
    results = clr.Reference[IntersectionResultArray]()
    start_point = XYZ(start_point.X, start_point.Y, 0)
    end_point = XYZ(end_point.X, end_point.Y, 0)
    newline = Line.CreateBound(start_point, end_point)
    direction = newline.Direction.Normalize()
    cross_grid_lines = get_cross_grids(grids, direction)
    for num, line in enumerate(cross_grid_lines):
        line.MakeUnbound()
        result = newline.Intersect(line, results)
        if result == SetComparisonResult.Overlap:
            intersection = results.Item[0]
            point = intersection.XYZPoint
            points.add(point)
    lengths = [p.DistanceTo(q) for i, p in enumerate(points) for j, q in enumerate(points) if i != j]
    span_length = float(min(lengths) * num + max(lengths)) / 2 / num
    module_length = float((span_length + float(diameter * 150)) * 0.5)
    return module_length


def get_intersection(line1, line2):
    results = clr.Reference[IntersectionResultArray]()
    result = line1.Intersect(line2, results)
    if result == SetComparisonResult.Overlap:
        intersection = results.Item[0]
        return intersection.XYZPoint


def intersection_by_direction(mid_point, boundary_lines, distance, direction):
    intersections = []
    p = mid_point - distance * direction
    q = mid_point + distance * direction
    newline = Line.CreateBound(p, q)
    for line in boundary_lines:
        if not IsCollinear(newline, line):
            point = get_intersection(newline, line)
            if point:
                intersections.append(point)
    if bool(i for i in intersections if i):
        return intersections


def points_by_interval(start_point, end_point, interval):
    points = []
    interval = interval
    mid_point = (start_point + end_point) * 0.5
    direction = (end_point - start_point).Normalize()
    distance = round(start_point.DistanceTo(end_point), 3) + interval
    division = int(round(distance / interval))
    half_length = (division * interval) / 2
    start_point = mid_point + half_length * direction
    end_point = mid_point - half_length * direction
    newline = Line.CreateBound(start_point, end_point)
    divide = 1 / float(division)
    for i in range(1, division):
        parameter = divide * float(i)
        point = newline.Evaluate(parameter, True)
        points.append(point)
    return points


def get_break_points(cross_grid_curves, start_point, end_point, module_length, top_layout):
    result_points = []
    start_point = XYZ(start_point.X, start_point.Y, 0)
    end_point = XYZ(end_point.X, end_point.Y, 0)
    newline = Line.CreateBound(start_point, end_point)
    direction = newline.Direction.Normalize()
    length = newline.ApproximateLength
    prv_point = start_point
    if round(length * 0.5) > round(module_length):
        division = int(length // module_length)
        divide = 1 / float(division)
        result_points.append(start_point)
        for count in range(division):
            irp1 = irp2 = None
            parameter = divide * float(count)
            break_point = newline.Evaluate(parameter, True)
            interval1 = interval2 = float("inf")
            for line in cross_grid_curves:
                line.MakeUnbound()
                ir_point = get_intersection(newline, line)
                if bool(ir_point):
                    vector = ir_point - break_point
                    distance = vector.DotProduct(direction)
                    if 0 <= distance < interval1:
                        interval1 = distance
                        irp1 = ir_point
                    vector = break_point - ir_point
                    distance = vector.DotProduct(direction)
                    if 0 <= distance < interval2:
                        interval2 = distance
                        irp2 = ir_point
            if bool(irp1 and irp2):
                mid_point = (irp1 + irp2) * 0.5
                if mid_point.DistanceTo(prv_point) > module_length:
                    prv_point = mid_point
                    if top_layout:
                        result_points.append(prv_point)
                    else:
                        result_points.append(irp1)
        result_points.append(end_point)
    return result_points


def sort_points(points):
    zipped = zip([round(p.X, 7) for p in points], [round(p.Y, 7) for p in points])
    zipped = sorted(zipped, key=lambda x: x[0])
    zipped = sorted(zipped, key=lambda x: x[1])
    points = [XYZ(x, y, float(0)) for x, y in zipped]
    return points


def get_optimal_points(points, diameter, max_length):
    def points_by_index(sorted_points, diameter, max_length):
        idx = 0
        result = []
        balance = float(0)
        overlap = round(float(diameter * 50), 5)
        half_overlap = round(float(diameter * 25), 5)
        while idx < len(sorted_points):
            pnt = sorted_points.pop(idx)
            result.append(pnt)
            tolerance = float('inf')
            sorted_points = [qnt for i, qnt in enumerate(sorted_points) if i >= idx]
            for count, qnt in enumerate(sorted_points):
                len_limit = round(float(max_length), 5)
                interspace = round(qnt.DistanceTo(pnt), 5)
                if interspace > len_limit:
                    break

                num = int(len(sorted_points) - 1)
                if idx == 0 or count == num:
                    length = interspace + half_overlap
                else:
                    length = interspace + overlap
                remainder = (len_limit // length) * (overlap + (len_limit % length) * (1 - (length / len_limit)))
                if length <= len_limit and tolerance > remainder:
                    tolerance = remainder
                    balance += remainder
                    idx = count
        return result, balance

    sorted_points = sort_points(points)
    revers_points = list(reversed(sorted_points))
    sorted = points_by_index(sorted_points, diameter, max_length)
    revers = points_by_index(revers_points, diameter, max_length)
    if sorted[1] > revers[1]:
        points = list(reversed(revers[0]))
        return points
    else:
        points = sorted[0]
        return points


def get_overlap_lines(points, direction, diameter, step_count):
    lines = []
    num = int(len(points) - 1)
    offset = float(diameter * 0.5)  # смещение в бок
    setback = float(diameter * 25)  # длина нахлеста
    rearrange = float(setback * 1.5)  # перекомпановка
    direction = XYZ(abs(direction.X), abs(direction.Y), 0)
    crossline = direction.CrossProduct(XYZ.BasisZ)
    for icount, p in enumerate(points):
        for jcount, q in enumerate(points):
            if (icount + 1) == jcount:
                if icount % 2 == 0:
                    p = p + offset * crossline
                    q = q + offset * crossline
                if icount % 2 != 0:
                    p = p - offset * crossline
                    q = q - offset * crossline
                if step_count % 2 == 0:
                    if 0 < icount:
                        p = p - setback * direction
                        p = p + rearrange * direction
                    if num > jcount:
                        q = q + setback * direction
                        q = q + rearrange * direction
                if step_count % 2 != 0:
                    if icount != 0:
                        p = p - setback * direction
                        p = p - rearrange * direction
                    if jcount != num:
                        q = q + setback * direction
                        q = q - rearrange * direction
                newline = Line.CreateBound(p, q)
                lines.append(newline)
                break
    return lines


def is_hostPoint(hostId, start_point, end_point, elevation, ray_direction, recheck=False):
    def ray_inspector(ray_point, ray_direction):
        filter = ElementClassFilter(Floor)
        view3d = [view for view in FilteredElementCollector(doc).OfClass(View3D) if not view.IsTemplate][0]
        refInt = ReferenceIntersector(filter, FindReferenceTarget.Element, view3d)
        refinResult = refInt.FindNearest(ray_point, ray_direction)
        if bool(refinResult):
            refel = refinResult.GetReference()
            return refel.ElementId

    ray_point = (start_point + end_point) * 0.5
    ray_point = ray_point + elevation * ray_direction
    ##### ray_point need to verify #####
    if recheck == True:
        ray_points = list()
        ray_points.append(XYZ(ray_point.X + 0.1, ray_point.Y + 0.1, ray_point.Z))
        ray_points.append(XYZ(ray_point.X - 0.1, ray_point.Y - 0.1, ray_point.Z))
        for rpt in ray_points:
            if hostId != ray_inspector(rpt, ray_direction):
                return False
        return True
    if recheck == False:
        if hostId == ray_inspector(ray_point, ray_direction):
            return True


def parameter_by_name(element, mark_name):
    mark_name = mark_name.lower()
    parameter = tolerance = None
    for param in element.Parameters:
        param_name = param.Definition.Name
        param_name = param_name.lower()
        matcher = difflib.SequenceMatcher(None, mark_name, param_name).ratio()
        if tolerance < matcher:
            tolerance = matcher
            parameter = param
    return parameter


def get_geometry(element):
    opt = Options()
    opt.ComputeReferences = True
    opt.IncludeNonVisibleObjects = True
    opt.DetailLevel = ViewDetailLevel.Medium
    for solid in element.get_Geometry(opt):
        if solid.Faces.Size != 0:
            return solid


def Is_intersect(solid, elevation, point, qoint):
    mid_point = (point + qoint) * 0.5
    end_point = mid_point + elevation * XYZ.BasisZ
    curve = Line.CreateBound(mid_point, end_point)
    options = SolidCurveIntersectionOptions()
    intersection = solid.IntersectWithCurve(curve, options)
    try:
        return bool(intersection.GetCurveSegment(0))
    except:
        pass


def calculation(rebar_host, diameter, boundary_lines, grids, direction, top):
    bound_points = []
    mid_point = XYZ(0, 0, 0)
    for idx, line in enumerate(boundary_lines):
        bound_points.append(line.GetEndPoint(0))
        point = line.Evaluate(0.5, True)
        mid_point += point
    mid_point = mid_point / len(boundary_lines)
    mid_point = XYZ(mid_point.X, mid_point.Y, 0)
    ###############################################################################################
    max_length, interval = round(float(11700 / 304.8), 5), round(float(200 / 304.8), 5)
    ###############################################################################################
    actiview = doc.ActiveView
    trf = Transform.Identity
    solid = get_geometry(rebar_host)
    centroid = solid.ComputeCentroid()
    elevation = trf.OfPoint(centroid).Z
    direction = XYZ(abs(direction.X), abs(direction.Y), 0)
    cross_direction = direction.CrossProduct(XYZ.BasisZ)
    distance = float(max(p.DistanceTo(mid_point) for p in bound_points))
    point = mid_point + distance * direction
    qoint = mid_point - distance * direction
    step_points = points_by_interval(point, qoint, interval)
    mod_length = get_module_length(grids, point, qoint, diameter)
    crossgrid_lines = get_cross_grids(grids, cross_direction)
    ###############################################################################################
    result_lines = []
    for step_count, point in enumerate(step_points):
        intersections = intersection_by_direction(point, boundary_lines, distance, cross_direction)
        intersections = list(p for p in intersections if p)
        if intersections and isinstance(intersections, list):
            sorted_points = sort_points(intersections)
            for idx, q in enumerate(sorted_points):
                if idx > 0:
                    p = sorted_points[idx - 1]
                    if Is_intersect(solid, elevation, p, q):
                        if p.DistanceTo(q) <= max_length:
                            line = Line.CreateBound(p, q)
                            result_lines.append(line)
                        else:
                            points = get_break_points(crossgrid_lines, p, q, mod_length, top)
                            points = get_optimal_points(points, diameter, max_length)
                            lines = get_overlap_lines(points, cross_direction, diameter, step_count)
                            result_lines.extend(lines)
    # if actiview.ViewType == ViewType.FloorPlan or actiview.ViewType == ViewType.EngineeringPlan:
    #     for line in result_lines:
    #         doc.Create.NewDetailCurve(actiview, line)
    return result_lines


def get_RebarType(diameter, filter_mark, is_rm=0):
    evaluator = FilterNumericEquals()
    bip = BuiltInParameter.REBAR_BAR_DIAMETER
    provider = ParameterValueProvider(ElementId(bip))
    filter_rule = FilterDoubleRule(provider, evaluator, float(diameter), 0.0001)
    filter = ElementParameterFilter(filter_rule)
    collector = FilteredElementCollector(doc).OfClass(RebarBarType).WherePasses(filter)
    rebar_type, rebar_types = collector.FirstElement(), collector.ToElements()
    filter_parameter = parameter_by_name(rebar_type, 'фильтр_арматуры')
    lineal_parameter = parameter_by_name(rebar_type, 'в_погонных_метрах')
    tolerance = float(0)
    for rtype in rebar_types:
        filter_value = rtype.get_Parameter(filter_parameter.GUID).AsString()
        if filter_value:
            lineal_value = rtype.get_Parameter(lineal_parameter.GUID).AsInteger()
            matcher = difflib.SequenceMatcher(None, filter_value.lower(), filter_mark.lower()).ratio()
            if matcher > tolerance and (lineal_value == is_rm):
                tolerance = matcher
                rebar_type = rtype
    return rebar_type


def reinforcing(doc, host, normal, result_lines, diameter, direction, top):
    elevation = rb_type = None
    if top == True:
        rb_type = get_RebarType(diameter, "Перекрытие_Фоновая_Верхняя")
        elevation = host.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_TOP).AsDouble()
        elevation = elevation - rebar_cover - diameter
    if top == False:
        rb_type = get_RebarType(diameter, "Перекрытие_Фоновая_Нижняя")
        elevation = host.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_BOTTOM).AsDouble()
        elevation = elevation + rebar_cover + diameter
    if XYZ(abs(direction.X), abs(direction.Y), 0).IsAlmostEqualTo(XYZ.BasisX):
        elevation = float(elevation - diameter * 0.5)
    if XYZ(abs(direction.X), abs(direction.Y), 0).IsAlmostEqualTo(XYZ.BasisY):
        elevation = float(elevation + diameter * 0.5)
    rebars = []
    vector = XYZ(0, 0, elevation)
    style = RebarStyle.Standard
    left = RebarHookOrientation.Left
    right = RebarHookOrientation.Right
    for line in result_lines:
        tf = Transform.CreateTranslation(vector)
        curve = line.CreateTransformed(tf)
        crvlst = List[Curve]()
        crvlst.Add(curve)
        rebar = Rebar.CreateFromCurves(doc, style, rb_type, None, None, host, normal, crvlst, right, left, True, True)
        rebars.append(rebar)
    doc.Regenerate()
    return rebars


def deleted_rebars(rebar_host):
    rebar_hostdata = RebarHostData.GetRebarHostData(rebar_host)
    if rebar_hostdata.IsValidHost():
        rebar_elements = rebar_hostdata.GetRebarsInHost()
        if bool(rebar_elements):
            workset_name = "#_КЖ_Арм_плит_фоновая"
            ids = [elem.Id for elem in rebar_elements]
            elementIds = List[ElementId](ids)
            bip = BuiltInParameter.ELEM_PARTITION_PARAM
            pvp = ParameterValueProvider(ElementId(bip))
            rule = FilterStringRule(pvp, FilterStringContains(), workset_name, False)
            collector = FilteredElementCollector(doc, elementIds)
            elementIds = collector.WherePasses(ElementParameterFilter(rule)).ToElementIds()
            doc.Delete(elementIds)
            doc.Regenerate()


def set_workset(elements, direction, top):
    workset_name = "#_КЖ_Арм_плит_фоновая"
    if top == True:
        if XYZ(abs(direction.X), abs(direction.Y), 0).IsAlmostEqualTo(XYZ.BasisX):
            workset_name = "#_КЖ_Арм_плит_фоновая_верх_X"
        if XYZ(abs(direction.X), abs(direction.Y), 0).IsAlmostEqualTo(XYZ.BasisY):
            workset_name = "#_КЖ_Арм_плит_фоновая_верх_Y"
    elif top == False:
        if XYZ(abs(direction.X), abs(direction.Y), 0).IsAlmostEqualTo(XYZ.BasisX):
            workset_name = "#_КЖ_Арм_плит_фоновая_низ_X"
        if XYZ(abs(direction.X), abs(direction.Y), 0).IsAlmostEqualTo(XYZ.BasisY):
            workset_name = "#_КЖ_Арм_плит_фоновая_низ_Y"
    wstable = doc.GetWorksetTable()
    if wstable.IsWorksetNameUnique(doc, workset_name):
        Workset.Create(doc, workset_name)
        doc.Regenerate()
    worksets = FilteredWorksetCollector(doc).ToWorksets()
    wids = List[WorksetId]([ws.Id for ws in worksets])
    try:
        WorksharingUtils.CheckoutWorksets(doc, wids)
    except:
        pass
    for workset in worksets:
        if workset_name == workset.Name:
            try:
                WorksetTable.SetActiveWorksetId(wstable, workset.Id)
            except:
                pass
            for element in elements:
                element.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM).Set(workset.Id.IntegerValue)
            return workset_name, len(elements)


class CustomISelectionFilter(Selection.ISelectionFilter):
    def __init__(self, element_class):
        self.element_class = element_class

    def AllowElement(self, element):
        if isinstance(element, self.element_class):
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return True


########################################################################################################################
diameter = float(12 / 304.8)
rebar_cover = float(25 / 304.8)
########################################################################################################################
collector = FilteredElementCollector(doc)
grids = collector.OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType().ToElements()
direction = grids_main_direction(grids)
cross_direction = direction.CrossProduct(XYZ.BasisZ)
select = uidoc.Selection.PickObject(Selection.ObjectType.Element.Element, CustomISelectionFilter(Floor), "Select")
rebar_host = doc.GetElement(select)
# collector = FilteredElementCollector(doc, doc.ActiveView.Id)
# rebar_host = collector.OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType().FirstElement()
########################################################################################################################
wstable = doc.GetWorksetTable()
activewsid = wstable.GetActiveWorksetId()
trf = Transform.Identity
profile_loop = get_floor_curveloop(rebar_host, rebar_cover, True)
normal = profile_loop.GetPlane().Normal
boundary_loops = get_floor_curveloop(rebar_host, rebar_cover)
boundary_lines = [line.CreateTransformed(trf) for loops in boundary_loops for line in loops.GetEnumerator() if line]

results = []
if bool(rebar_host):
    with Transaction(doc, "CreateRebar") as tra:
        tra.Start()
        # Deleted rebars
        deleted_rebars(rebar_host)
        ### Reinforcing by TOP direction
        rebar_lines = calculation(rebar_host, diameter, boundary_lines, grids, direction, True)
        rebar_elements = reinforcing(doc, rebar_host, normal, rebar_lines, diameter, direction, True)
        workset_name = set_workset(rebar_elements, direction, True)
        results.append(workset_name)
        ## Reinforcing by TOP cross_direction
        rebar_lines = calculation(rebar_host, diameter, boundary_lines, grids, cross_direction, True)
        rebar_elements = reinforcing(doc, rebar_host, normal, rebar_lines, diameter, cross_direction, True)
        workset_name = set_workset(rebar_elements, cross_direction, True)
        results.append(workset_name)
        ### Reinforcing by BOTTOM direction
        rebar_lines = calculation(rebar_host, diameter, boundary_lines, grids, direction, False)
        rebar_elements = reinforcing(doc, rebar_host, normal, rebar_lines, diameter, direction, False)
        workset_name = set_workset(rebar_elements, direction, False)
        results.append(workset_name)
        ## Reinforcing by BOTTOM cross_direction
        rebar_lines = calculation(rebar_host, diameter, boundary_lines, grids, cross_direction, False)
        rebar_elements = reinforcing(doc, rebar_host, normal, rebar_lines, diameter, cross_direction, False)
        workset_name = set_workset(rebar_elements, cross_direction, False)
        results.append(workset_name)
        tra.Commit()

OUT = results
