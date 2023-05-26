#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import os
import math
import difflib
from datetime import datetime

import clr

clr.AddReference("System")
clr.AddReference("System.Core")
import System
from System.IO import Path

clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
clr.AddReference("RevitAPIUI")
import Autodesk
from Autodesk.Revit.DB import SolidUtils
from Autodesk.Revit.DB import ModelPathUtils
from Autodesk.Revit.DB import ViewDetailLevel
from Autodesk.Revit.DB import SharedParameterElement
from Autodesk.Revit.DB import UnitUtils, DisplayUnitType
from Autodesk.Revit.DB import Transaction, SubTransaction
from Autodesk.Revit.DB import RevitLinkType, RevitLinkInstance
from Autodesk.Revit.DB import UV, XYZ, Line, Solid, Level, Wall, Floor
from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter, Transform
from Autodesk.Revit.DB import ElementId, Family, FamilyInstance, FamilySymbol
from Autodesk.Revit.DB import FamilyInstanceReferenceType, Reference, SketchPlane, Outline
from Autodesk.Revit.DB import Options, SolidCurveIntersectionOptions, ElementIntersectsSolidFilter
from Autodesk.Revit.DB import FilteredElementCollector, ElementMulticategoryFilter, FamilyInstanceFilter
from Autodesk.Revit.DB import ElementParameterFilter, ParameterValueProvider, LogicalAndFilter, LogicalOrFilter
from Autodesk.Revit.DB import FilterNumericGreaterOrEqual, FilterNumericLessOrEqual
from Autodesk.Revit.DB import FilterStringRule, FilterStringContains
from Autodesk.Revit.DB import FilterDoubleRule, FilterNumericGreater
from Autodesk.Revit.DB import LocationPoint, LocationCurve
from Autodesk.Revit.DB import BoundingBoxIntersectsFilter

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()
########################################################################################################################
options = Options()
options.IncludeNonVisibleObjects = True
options.DetailLevel = ViewDetailLevel.Medium
intersectionOptions = SolidCurveIntersectionOptions()
linkType = (UnwrapElement(IN[0]) if bool(IN[0]) else None)
########################################################################################################################
pipeCategory = BuiltInCategory.OST_PipeCurves
ductCategory = BuiltInCategory.OST_DuctCurves
conduitCategory = BuiltInCategory.OST_Conduit
cableTrayCategory = BuiltInCategory.OST_CableTray
equipmentCategory = BuiltInCategory.OST_MechanicalEquipment
nonStruct = Autodesk.Revit.DB.Structure.StructuralType.NonStructural
########################################################################################################################
openingReserve = float(50 / 304.8)  # запас для проёма в мм
openingMinSize = int(100)  # минимальный диаметр для отверстия
openingMaxSize = int(500)  # максимальный диаметр для отверстия
openingMaxRatio = 3  # максимальное отношение сторон коммуникации для отверстия
########################################################################################################################
commentDataTime = datetime.now().strftime('%d.%b.%Y')
hostDoc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
identityTransform = Transform.Identity
uidoc = uiapp.ActiveUIDocument
revitLinkInstance = None
invertTransform = None
linkDoc = hostDoc

if linkType and RevitLinkType.IsLoaded(hostDoc, linkType.Id):
    extFile = linkType.GetExternalFileReference()
    linkPath = ModelPathUtils.ConvertModelPathToUserVisiblePath(extFile.GetPath())
    linkName = Path.GetFileNameWithoutExtension(linkPath)
    for linkInst in FilteredElementCollector(hostDoc).OfClass(RevitLinkInstance).ToElements():
        tempDocument = linkInst.GetLinkDocument()
        tempDocumentName = Path.GetFileNameWithoutExtension(tempDocument.PathName)
        if linkName == tempDocumentName:
            totalTransform = linkInst.GetTotalTransform()
            invertTransform = totalTransform.Inverse
            linkDoc = tempDocument
            revitLinkInstance = linkInst


########################################################################################################################
def getExternalDefinition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        definition = group.Definitions.Item[parameter_name]
        if definition and group.Definitions.Contains(definition):
            return definition


def getGuidByParameterName(doc, parameter_name):
    external = getExternalDefinition(doc, parameter_name)
    parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToList()
    parameter = parameters.FirstOrDefault(lambda x: external.GUID == x.GuidValue)
    if parameter: return parameter.GuidValue


def getFamilySymbolByName(doc, family_name):
    provider00 = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME))
    provider01 = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME))
    filter00 = ElementParameterFilter(FilterStringRule(provider00, FilterStringContains(), family_name, False))
    filter01 = ElementParameterFilter(FilterStringRule(provider01, FilterStringContains(), family_name, False))
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).WherePasses(LogicalOrFilter(filter00, filter01))
    result = collector.WhereElementIsElementType().FirstElement()
    return result


def getOpeningsByFamilySymbol(doc, familySymbol):
    family_filter = FamilyInstanceFilter(doc, familySymbol.Id)
    instances = FilteredElementCollector(doc).OfClass(FamilyInstance).WherePasses(family_filter).ToElements()
    return instances


def getValueByParameterName(element, param_name, tolerance=0, result=None):
    for param in element.GetParameters(param_name):
        weight = difflib.SequenceMatcher(None, param_name, param.Definition.Name).ratio()
        if (weight > tolerance): tolerance, result = weight, param.AsDouble()
    return result


########################################################################################################################
wallOpeningName = (IN[1] if isinstance(IN[1], basestring) else "")
floorOpeningName = (IN[2] if isinstance(IN[2], basestring) else "")
########################################################################################################################
instanceOpenings = []
wallOpening = getFamilySymbolByName(hostDoc, wallOpeningName)
floorOpening = getFamilySymbolByName(hostDoc, floorOpeningName)
if wallOpening: instanceOpenings.extend(getOpeningsByFamilySymbol(hostDoc, wallOpening))
if floorOpening: instanceOpenings.extend(getOpeningsByFamilySymbol(hostDoc, floorOpening))
########################################################################################################################
builtInCats = List[BuiltInCategory]()
# builtInCats.Add(pipeCategory)
# builtInCats.Add(ductCategory)
# builtInCats.Add(conduitCategory)
# builtInCats.Add(cableTrayCategory)
builtInCats.Add(equipmentCategory)
catFilter = ElementMulticategoryFilter(builtInCats)
########################################################################################################################
unit = DisplayUnitType.DUT_MILLIMETERS
widthParameterName = "TMS_Отверстие_Ширина"
heightParameterName = "TMS_Отверстие_Высота"
widthParamGuid = getGuidByParameterName(hostDoc, "TMS_Отверстие_Ширина")
heightParamGuid = getGuidByParameterName(hostDoc, "TMS_Отверстие_Высота")
elevationLevelGuid = getGuidByParameterName(hostDoc, "TMS_Отверстие_Отметка от этажа")
elevationElementGuid = getGuidByParameterName(hostDoc, "TMS_Отверстие_Отметка этажа")
commentParameterName = "Комментарии"


########################################################################################################################
class ConstructObject:
    def __init__(self, categoryId, instance, normal, solid, level):
        self.categoryId = categoryId
        self.instance = instance
        self.normal = normal
        self.solid = solid
        self.level = level


def getInstances(doc, revitClass, condition=0.5):
    paramId = ElementId.InvalidElementId
    selectIds = uidoc.Selection.GetElementIds()
    collector = FilteredElementCollector(doc).OfClass(revitClass)
    # HOST_AREA_COMPUTED
    if (revitClass is Wall): paramId = ElementId(BuiltInParameter.WALL_ATTR_WIDTH_PARAM)
    if (revitClass is Floor): paramId = ElementId(BuiltInParameter.STRUCTURAL_FLOOR_CORE_THICKNESS)
    if 0 != selectIds.Count: collector = FilteredElementCollector(doc, selectIds).OfClass(revitClass)
    rule = FilterDoubleRule(ParameterValueProvider(paramId), FilterNumericGreater(), condition, 0.0005)
    instances = collector.WherePasses(ElementParameterFilter(rule)).WhereElementIsNotElementType().ToElements()
    return instances


def validBaseLevel(instance):
    if instance.IsValidObject:
        return not bool(instance.LevelId.Equals(ElementId.InvalidElementId))


def getCentroid(instance, transform):
    bbox = instance.get_BoundingBox(None)
    centroid = (bbox.Min + bbox.Max) * 0.5
    centroid = transform.OfPoint(centroid)
    return centroid


def getSolid(instance, transform):
    tolerance, result = 0, None
    geometry = instance.get_Geometry(options)
    for solid in geometry.GetTransformed(transform):
        if isinstance(solid, Solid):
            if solid.Faces.Size:
                volume = solid.Volume
                if (volume > tolerance):
                    tolerance = volume
                    result = solid
    return result


def getInstanceNormal(instance):
    direction = XYZ.BasisZ
    location = instance.Location
    if isinstance(location, LocationCurve):
        direction = location.Curve.Direction
    elif revitLinkInstance and isinstance(instance, FamilyInstance):
        centerType = FamilyInstanceReferenceType.CenterLeftRight
        reference = instance.GetReferences(centerType).FirstOrDefault()
        ids = Reference.ConvertToStableRepresentation(reference, linkDoc)
        reference = Reference.ParseFromStableRepresentation(linkDoc, ids)
        reference = reference.CreateLinkReference(revitLinkInstance)
        with Transaction(hostDoc, "GetPlan") as trans:
            trans.Start()
            sketch = SketchPlane.Create(hostDoc, reference)
            plan = sketch.GetPlane()
            normal = plan.Normal
            trans.RollBack()
        direction = normal.CrossProduct(XYZ.BasisZ)
    return direction


def createLineByNormal(centroid, normal, lenght=5):
    lenght = float(lenght * 0.5)
    point00 = centroid - (normal * lenght)
    point01 = centroid + (normal * lenght)
    return Autodesk.Revit.DB.Line.CreateBound(point00, point01)


def deleteElementId(doc, itemId, flag=True):
    with Transaction(doc, "Delete elements") as trans:
        if isinstance(itemId, ElementId):
            trans.Start()
            doc.Delete(itemId)
            doc.Regenerate()
            trans.Commit()
            return flag


def getOpeningIdByPoint(intersectPoint, tolerance=5, result=None):
    for instance in instanceOpenings:
        if instance.IsValidObject:
            point = instance.Location.Point
            distance = intersectPoint.DistanceTo(point)
            if tolerance < distance:
                result = instance.Id
                tolerance = distance
    return result


def getCommunicationSize(instance, width_double=None, height_double=None):
    categoryIdint = instance.Category.Id.IntegerValue
    builtInCategory = System.Enum.ToObject(BuiltInCategory, categoryIdint)
    if builtInCategory == pipeCategory:
        diameter = instance.get_Parameter(BuiltInParameter.RBS_PIPE_OUTER_DIAMETER).AsDouble()
        width_double, height_double = diameter, diameter
    elif builtInCategory == ductCategory:
        try:
            diameter = instance.get_Parameter(BuiltInParameter.RBS_CURVE_DIAMETER_PARAM).AsDouble()
            width_double, height_double = diameter, diameter
        except:
            width_double = instance.get_Parameter(BuiltInParameter.RBS_CURVE_WIDTH_PARAM).AsDouble()
            height_double = instance.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM).AsDouble()
    elif builtInCategory == conduitCategory:
        diameter = instance.get_Parameter(BuiltInParameter.RBS_CONDUIT_DIAMETER_PARAM).AsDouble()
        width_double, height_double = diameter, diameter
    elif builtInCategory == cableTrayCategory:
        width_double = instance.get_Parameter(BuiltInParameter.RBS_CABLETRAY_WIDTH_PARAM).AsDouble()
        height_double = instance.get_Parameter(BuiltInParameter.RBS_CABLETRAY_HEIGHT_PARAM).AsDouble()
    height_double = (height_double + openingReserve if height_double is not None else None)
    width_double = (width_double + openingReserve if width_double is not None else None)
    if any([(width_double is None), (height_double is None)]):
        width_double = getValueByParameterName(instance, widthParameterName)
        height_double = getValueByParameterName(instance, heightParameterName)
    return width_double, height_double


def calculateSize(angleSide, hostDepth, sideSizeDouble, base=50):
    side_size_mm = UnitUtils.ConvertFromInternalUnits(sideSizeDouble, unit)
    flag = bool(hostDepth != 0 and round(angleSide) != 0 and round(angleSide) < 60)
    offset = int(math.tan(math.radians(angleSide)) * (hostDepth + base) if flag else 0)
    side_size_mm = int(round((offset + side_size_mm) / base) * base)
    return side_size_mm


def defineOpeningSize(widthDouble, heightDouble, hostNormal, line):
    if isinstance(line, Line):
        point0 = line.GetEndPoint(0)
        point1 = line.GetEndPoint(1)
        vectorLine = (point1 - point0)
        centrePoint = ((point0 + point1) * 0.5)
        radianVectorZ = vectorLine.AngleTo(XYZ.BasisZ)
        radianNormalZ = hostNormal.AngleTo(XYZ.BasisZ)
        radianHight = abs(radianVectorZ - radianNormalZ)
        radianWidht = abs(vectorLine.AngleTo(hostNormal))
        angleWidht = int(round(math.degrees(radianWidht)))
        angleHight = int(round(math.degrees(radianHight)))
        hostDepth = int(abs(round(hostNormal.DotProduct(vectorLine) * 304.8)))
        openingWidth = int(calculateSize(angleWidht, hostDepth, widthDouble))
        openingHeight = int(calculateSize(angleHight, hostDepth, heightDouble))
        angleWidht = int(abs(180 - angleWidht if round(angleWidht) > 90 else angleWidht))
        angleHight = int(abs(180 - angleHight if round(angleHight) > 90 else angleHight))
        return centrePoint, openingWidth, openingHeight, hostDepth, angleWidht, angleHight


def defineElevationDifference(element, locationPoint):
    centerPoint = getCentroid(element, identityTransform)
    vector = (locationPoint - centerPoint)
    distance = vector.DotProduct(XYZ.BasisZ)
    return distance


def createInstanceOpening(centrePoint, hostInstance, hostLevel, openingWidth, openingHeight, direction, opening=None):
    openingWidth = float(openingWidth / 304.8)
    openingHeight = float(openingHeight / 304.8)
    centrePoint = totalTransform.OfPoint(centrePoint)
    categoryIdInt = construct.categoryId.IntegerValue
    elevationLevel = float(round(hostInstance.Elevation * 304.8) / 304.8)
    elevationPoint = float((centrePoint - XYZ.Zero).DotProduct(XYZ.BasisZ) - elevationLevel)
    centrePoint = XYZ(centrePoint.X, centrePoint.Y, elevationPoint)
    with Transaction(hostDoc, "Create opening") as transact:
        transact.Start()
        if wallOpening and categoryIdInt == -2000011:  # Wall category
            opening = hostDoc.Create.NewFamilyInstance(centrePoint, wallOpening, hostInstance, hostLevel, nonStruct)
            if opening and opening.IsValidObject:
                opening.get_Parameter(widthParamGuid).Set(openingWidth)
                opening.get_Parameter(heightParamGuid).Set(openingHeight)
                if bool(opening.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM).Set(0)):
                    opening.get_Parameter(elevationElementGuid).Set(elevationPoint)
                    opening.get_Parameter(elevationLevelGuid).Set(elevationLevel)
        elif floorOpening and categoryIdInt == -2000032:  # Floor category
            opening = hostDoc.Create.NewFamilyInstance(centrePoint, floorOpening, direction, hostInstance, nonStruct)
            if opening and opening.IsValidObject:
                opening.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM).Set(hostLevel.Id)
                opening.get_Parameter(heightParamGuid).Set(openingHeight)
                opening.get_Parameter(widthParamGuid).Set(openingWidth)
        transact.Commit()
    return opening


def createOpeningsByIntersection(construct):
    result = []
    hostLevel = construct.level
    hostSolid = construct.solid
    hostNormal = construct.normal
    hostInstance = construct.instance
    bbox = hostInstance.get_BoundingBox(None)
    minPoint = invertTransform.OfPoint(bbox.Min)
    maxPoint = invertTransform.OfPoint(bbox.Max)
    collector = FilteredElementCollector(linkDoc).WherePasses(catFilter)
    bboxFilter = BoundingBoxIntersectsFilter(Outline(minPoint, maxPoint))
    intersectionFilter = LogicalAndFilter(bboxFilter, ElementIntersectsSolidFilter(hostSolid))
    intersecting = collector.WherePasses(intersectionFilter).ToElements()
    categoryIdInt = construct.categoryId.IntegerValue
    for idx, communication in enumerate(intersecting):
        intersectDirection = getInstanceNormal(communication)
        centrePoint = getCentroid(communication, identityTransform)
        widthDouble, heightDouble = getCommunicationSize(communication)
        intersectLine = createLineByNormal(centrePoint, intersectDirection)
        middleSize = int(round(sum([widthDouble, heightDouble]) * 0.5 * 304.8))
        isParallel = hostNormal.CrossProduct(intersectDirection).IsAlmostEqualTo(XYZ.Zero)
        intersectLine = hostSolid.IntersectWithCurve(intersectLine, intersectionOptions).GetCurveSegment(0)
        openingSize = defineOpeningSize(widthDouble, heightDouble, hostNormal, intersectLine)
        centrePoint, openingWidth, openingHeight, hostDepth, angleWidht, angleHight = openingSize
        isValidIntersection = bool(isParallel and (openingMinSize < middleSize < openingMaxSize))
        if isValidIntersection:
            centrePoint = totalTransform.OfPoint(centrePoint)
            elevationLevel = float(round(hostLevel.Elevation * 304.8) / 304.8)
            elevationPoint = float((centrePoint - XYZ.Zero).DotProduct(XYZ.BasisZ) - elevationLevel)
            centrePoint = XYZ(centrePoint.X, centrePoint.Y, elevationPoint)
            opening = createInstanceOpening(construct, openingWidth, openingHeight, centrePoint)
            if opening: result.append(opening)
        return result
    return hostInstance


########################################################################################################################
origin = XYZ(0, 0, 0)
hostLocation = hostDoc.ActiveProjectLocation
linkLocation = linkDoc.ActiveProjectLocation
newPosition = hostLocation.GetProjectPosition(origin)
########################################################################################################################
output = []
count = int(0)
wallInstances = getInstances(hostDoc, Wall)
instance = wallInstances.FirstOrDefault()
if revitLinkInstance and instance:
    output.append(linkDoc.Title)
    categoryWallId = instance.Category.Id
    if wallOpening: wallOpening.Activate()
    output.append(wallOpening.Family.Name)
    for idx, instance in enumerate(wallInstances):
        if validBaseLevel(instance):
            normal = instance.Orientation
            solid = getSolid(instance, invertTransform)
            level = hostDoc.GetElement(instance.LevelId)
            construct = ConstructObject(categoryWallId, instance, normal, solid, level)
            openingResult = createOpeningsByIntersection(construct)
            if openingResult: output.append(openingResult)
            if idx == 100: break

########################################################################################################################
# isVertical = normal.CrossProduct(XYZ.BasisZ).IsAlmostEqualTo(XYZ.Zero)
# exteriorRef = HostObjectUtils.GetSideFaces(instance, ShellLayerType.Exterior).FirstOrDefault()
# exteriorFace = instance.GetGeometryObjectFromReference(exteriorRef)
# normal = exteriorFace.ComputeNormal(UV(0, 0)).Normalize()
########################################################################################################################
OUT = output
########################################################################################################################
