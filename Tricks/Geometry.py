# -*- coding: UTF-8 -*-


def get_geometry(element):
    opt = Options()
    opt.ComputeReferences = True
    opt.IncludeNonVisibleObjects = True
    opt.DetailLevel = Autodesk.Revit.DB.ViewDetailLevel.Medium
    for geom in element.get_Geometry(opt):
        if geom.GetType() == Autodesk.Revit.DB.Solid and geom.Faces.Size > 0:
            return geom
        elif geom.GetType() == Autodesk.Revit.DB.GeometryInstance:
            for obj in geom.SymbolGeometry:
                if obj.GetType() == Autodesk.Revit.DB.Solid and obj.Faces.Size > 0:
                    return obj


def get_element_intersection(centre, radius=0.5):
    frame = Autodesk.Revit.DB.Frame(centre, XYZ.BasisX, XYZ.BasisY, XYZ.BasisZ)
    p1, p2, p3 = centre - radius * XYZ.BasisZ, centre + radius * XYZ.BasisX, centre + radius * XYZ.BasisZ
    l1, l2, l3 = Line.CreateBound(p1, p2), Line.CreateBound(p2, p3), Line.CreateBound(p3, p1)
    half_circle = CurveLoop.Create(List[Curve]([l1, l2, l3]))
    loops = List[CurveLoop]()
    loops.Add(half_circle)
    sphere = GeometryCreationUtilities.CreateRevolvedGeometry(frame, loops, 0, 2 * math.pi)
    solidfilter = ElementIntersectsSolidFilter(sphere)
    builtInCats = List[BuiltInCategory]()
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_StructuralFraming)
    builtInCats.Add(BuiltInCategory.OST_StructuralColumns)
    categfilter = ElementMulticategoryFilter(builtInCats)
    logicfilter = LogicalAndFilter(solidfilter, categfilter)
    collector = FilteredElementCollector(doc).WhereElementIsViewIndependent()
    intersection = collector.WherePasses(logicfilter).FirstElement()
    return intersection


def Is_rebarIntersections(solid, elevation, point, qoint):
    normal = (qoint - point)
    mid_point = (point + qoint) * 0.5
    mid_point = mid_point + elevation * XYZ.BasisZ
    options = SolidCurveIntersectionOptions()
    intersection = solid.IntersectWithCurve(curve, options)
    for segment in intersection.SegmentCount():
        if intersection.GetCurveSegment(segment):
            return True


def rayByVector(point, direction, filter_class):
    filter = ElementClassFilter(filter_class)
    view3d = [view for view in FilteredElementCollector(doc).OfClass(View3D) if not view.IsTemplate][0]
    refInt = ReferenceIntersector(filter, FindReferenceTarget.Element, view3d)
    result = refInt.FindNearest(point, direction)
    if result is not None:
        refel = result.GetReference()
        refId = refel.ElementId
        instance = doc.GetElement(refId)
        pt = refel.GlobalPoint
        return


def IsCollinear(line1, line2):
    direction01 = line1.Direction.Normalize()
    direction02 = line2.Direction.Normalize()
    direction03 = (line1.Origin - line2.Origin).Normalize()
    if direction01.CrossProduct(direction02).IsZeroLength():
        if direction01.CrossProduct(direction03).IsZeroLength():
            return True


def get_intersection(current, match, reverse=False):
    results = clr.Reference[IntersectionResultArray]()
    result = current.Intersect(match, results)
    if result == SetComparisonResult.Overlap:
        intersection = results.Item[0]
        return intersection.XYZPoint
    p1 = current.GetEndPoint(0)
    q1 = current.GetEndPoint(1)
    p2 = match.GetEndPoint(0)
    q2 = match.GetEndPoint(1)
    v1, v2, v3 = q1 - p1, q2 - p2, p2 - p1
    if not v1.CrossProduct(v2).IsZeroLength():
        try:
            c = round((v2.X * v3.Y - v2.Y * v3.X), 9) / round((v2.X * v1.Y - v2.Y * v1.X), 9)
            x = round((p1.X + c * v1.X), 9)
            y = round((p1.Y + c * v1.Y), 9)
            z = round((p1.Z + c * v1.Z), 9)
        except:
            pass
        else:
            return XYZ(x, y, z)
    if reverse != True:
        current = Line.CreateBound(p1, q1 + 0.5 * v1)
        result = current.Project(p2)
        return result.XYZPoint
    elif reverse == True:
        current = Line.CreateBound(p1, q1 + 0.5 * v1)
        result = current.Project(q2)
        return result.XYZPoint


def get_wall_by_point(point, elevation, offset=0.5):
    point = XYZ(point.X, point.Y, elevation + offset)
    bboxfilter = BoundingBoxContainsPointFilter(point, False)
    collector = FilteredElementCollector(doc).WhereElementIsViewIndependent()
    return collector.OfClass(Wall).WherePasses(bboxfilter).FirstElement()


def get_room_boundary(room):
    curveloop, tolerance = None, float(0)
    options = SpatialElementBoundaryOptions()
    options.StoreFreeBoundaryFaces = True
    options.SpatialElementBoundaryLocation = Autodesk.Revit.DB.SpatialElementBoundaryLocation.Finish
    calculator = SpatialElementGeometryCalculator(doc, options)
    results = calculator.CalculateSpatialElementGeometry(room)
    room_solid = results.GetGeometry()
    for boundface in room_solid.Faces:
        for subface in results.GetBoundaryFaceInfo(boundface):
            subtype = subface.SubfaceType
            if (subtype == SubfaceType.Top):
                room_face = subface.GetSpatialElementFace()
                for loop in room_face.GetEdgesAsCurveLoops():
                    if not loop.IsOpen():
                        length = loop.GetExactLength()
                        if tolerance < length:
                            tolerance = length
                            curveloop = loop
    return curveloop


def get_ray_intersection(point, direction, view3d):
    builtInCats = List[BuiltInCategory]()
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_Floors)
    builtInCats.Add(BuiltInCategory.OST_StructuralColumns)
    builtInCats.Add(BuiltInCategory.OST_MechanicalEquipment)
    builtInCats.Add(BuiltInCategory.OST_CurtainWallMullions)
    cat_filter = DB.ElementMulticategoryFilter(builtInCats)
    intersector = DB.ReferenceIntersector(cat_filter, DB.FindReferenceTarget.Face, view3d)
    intersector.FindReferencesInRevitLinks = True
    context = intersector.FindNearest(point, direction)
    if context != None:
        proximity = context.Proximity
        reference = context.GetReference()
        ids = reference.ConvertToStableRepresentation(doc)
        reference = DB.Reference.ParseFromStableRepresentation(doc, ids)
        element = doc.GetElement(reference)
        intersection = point + proximity * direction
        if isinstance(element, DB.RevitLinkInstance):
            element = element.GetLinkDocument().GetElement(reference.LinkedElementId)
        geometry = element.GetGeometryObjectFromReference(reference)
        return element, proximity, intersection, geometry


sortedElements = sorted(columns, key=lambda ele: (round(ele.GetLocation().Y), round(ele.GetLocation().X)))



def get_element_intersection_by_radius(centre, radius=0.5):
    frame = Autodesk.Revit.DB.Frame(centre, XYZ.BasisX, XYZ.BasisY, XYZ.BasisZ)
    p1, p2, p3 = centre - radius * XYZ.BasisZ, centre + radius * XYZ.BasisX, centre + radius * XYZ.BasisZ
    l1, l2, l3 = Line.CreateBound(p1, p2), Line.CreateBound(p2, p3), Line.CreateBound(p3, p1)
    half_circle = CurveLoop.Create(List[Curve]([l1, l2, l3]))
    loops = List[CurveLoop]()
    loops.Add(half_circle)
    sphere = GeometryCreationUtilities.CreateRevolvedGeometry(frame, loops, 0, 2 * math.pi)
    solidfilter = ElementIntersectsSolidFilter(sphere)
    builtInCats = List[BuiltInCategory]()
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_StructuralFraming)
    builtInCats.Add(BuiltInCategory.OST_StructuralColumns)
    categfilter = ElementMulticategoryFilter(builtInCats)
    logicfilter = LogicalAndFilter(solidfilter, categfilter)
    collector = FilteredElementCollector(doc).WhereElementIsViewIndependent()
    intersection = collector.WherePasses(logicfilter).FirstElement()
    return intersection


min_x = round(min(p.X for p in points) - 5)
max_x = round(max(p.X for p in points) + 5)
min_y = round(min(p.Y for p in points) - 5)
max_y = round(max(p.Y for p in points) + 5)


def get_element_intersection_by_rectangle(min_x, max_x, min_y, max_y, elevation, height):
    profile = List[Curve]()
    profile00 = XYZ(min_x, min_y, elevation)
    profile01 = XYZ(min_x, max_y, elevation)
    profile11 = XYZ(max_x, max_y, elevation)
    profile10 = XYZ(max_x, min_x, elevation)
    profile.Add(Line.CreateBound(profile00, profile01))
    profile.Add(Line.CreateBound(profile01, profile11))
    profile.Add(Line.CreateBound(profile11, profile10))
    profile.Add(Line.CreateBound(profile10, profile00))
    curveLoop = CurveLoop.Create(profile)
    result = GeometryCreationUtilities.CreateExtrusionGeometry(curveLoop, XYZ.BasisZ, height)
    return result


def getInstancesByClass(doc, revitClass):
    collector = FilteredElementCollector(doc).OfClass(revitClass)
    return collector.WhereElementIsNotElementType().ToElements()


def getSolid(instance, transform, tolerance=0):
    result = None
    geometry = instance.get_Geometry(options)
    for solid in geometry.GetTransformed(transform):
        if isinstance(solid, Autodesk.Revit.DB.Solid):
            if solid.Faces.Size:
                volume = solid.Volume
                if (volume > tolerance):
                    tolerance = volume
                    result = solid
    return result


def getIntersection(doc, element):
    intersectionFilter = Autodesk.Revit.DB.ElementIntersectsElementFilter(element)
    return FilteredElementCollector(doc).WherePasses(intersectionFilter).ToElements()