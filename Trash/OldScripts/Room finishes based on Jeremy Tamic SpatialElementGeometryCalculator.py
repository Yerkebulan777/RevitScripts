# -*- coding: utf-8 -*-
# -----------------------Импоорт библиотек----------------------
import clr
from clr import StrongBox

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIIFC')
from Autodesk.Revit.DB.IFC import ExporterIFCUtils

"""
clr.AddReference("RevitNodes") 
import Revit
from Revit.Elements import *

clr.ImportExtensions(Revit.Elements) #ToDSType не работает без
clr.ImportExtensions(Revit.GeometryConversion)
"""

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

clr.AddReference('System')
from System.Collections.Generic import List

# -----------------------Классы и Функции----------------------
test3 = []


class SolidHandler:
    def __init__(self):
        _offset = 0

    def GetLargestFaceArea(self, intersectSolid):
        faceArray = intersectSolid.Faces
        maxFaceArea = 0
        for face in faceArray:
            a = face.Area
            if a > maxFaceArea:
                maxFaceArea = a
            else:
                pass
        return maxFaceArea

    def GetWallAsOpeningArea(self, elemOpening, elemHost, solidRoom):
        doc = elemOpening.Document
        wallAsOpening = elemOpening
        options = doc.Application.Create.NewGeometryOptions()
        options.ComputeReferences = True
        options.IncludeNonVisibleObjects = True
        solidProfile = self.GetWallProfil(wallAsOpening)
        solidOpening = GeometryCreationUtilities.CreateExtrusionGeometry(solidProfile, wallAsOpening.Orientation, 1)
        intersectSolid = BooleanOperationsUtils.ExecuteBooleanOperation(solidOpening, solidRoom,
                                                                        BooleanOperationsType.Intersect)

        if intersectSolid.Faces.Size.Equals(0):
            solidOpening = GeometryCreationUtilities.CreateExtrusionGeometry(solidProfile,
                                                                             wallAsOpening.Orientation.Negate(), 1)
            intersectSolid = BooleanOperationsUtils.ExecuteBooleanOperation(solidOpening, solidRoom,
                                                                            BooleanOperationsType.Intersect)
        openingArea = self.GetLargestFaceArea(intersectSolid)
        # test3.append(intersectSolid.ToProtoType())
        return openingArea

    def CreateSolidFromBoundingBox(self, lcs, boundingBoxXYZ, solidOptions):
        retrn = None
        if boundingBoxXYZ == None or not boundingBoxXYZ.Enabled:
            retrn = None
        else:
            pass

        if lcs == None:
            bboxTransform = boundingBoxXYZ.Transform
        else:
            bboxTransform = lcs.Multiply(boundingBoxXYZ.Transform)
        profilePts = [XYZ()] * 4

        profilePts[0] = bboxTransform.OfPoint(boundingBoxXYZ.Min)
        profilePts[1] = bboxTransform.OfPoint(XYZ(boundingBoxXYZ.Max.X, boundingBoxXYZ.Min.Y, boundingBoxXYZ.Min.Z))
        profilePts[2] = bboxTransform.OfPoint(XYZ(boundingBoxXYZ.Max.X, boundingBoxXYZ.Max.Y, boundingBoxXYZ.Min.Z))
        profilePts[3] = bboxTransform.OfPoint(XYZ(boundingBoxXYZ.Min.X, boundingBoxXYZ.Max.Y, boundingBoxXYZ.Min.Z))
        upperRightXYZ = bboxTransform.OfPoint(boundingBoxXYZ.Max)

        # // If we assumed that the transforms had no scaling,
        # // then we could simply take boundingBoxXYZ.Max.Z - boundingBoxXYZ.Min.Z.
        # // This code removes that assumption.

        origExtrusionVector = XYZ(boundingBoxXYZ.Min.X, boundingBoxXYZ.Min.Y, boundingBoxXYZ.Max.Z) - boundingBoxXYZ.Min
        extrusionVector = bboxTransform.OfVector(origExtrusionVector)

        extrusionDistance = extrusionVector.GetLength()
        extrusionDirection = extrusionVector.Normalize()

        line_list_for_loop = []
        baseLoop = CurveLoop()
        i = 0

        while i < 4:
            baseLoop.Append(Line.CreateBound(profilePts[i], profilePts[(i + 1) % 4]))
            i += 1

        baseLoops = List[CurveLoop]([baseLoop])

        if solidOptions == None:
            retrn = GeometryCreationUtilities.CreateExtrusionGeometry(baseLoops, extrusionDirection, extrusionDistance)
        else:
            retrn = GeometryCreationUtilities.CreateExtrusionGeometry(baseLoops, extrusionDirection, extrusionDistance,
                                                                      solidOptions)

        return retrn

    def GetWallProfil(self, insert_wall):
        g_curve_list = self.GetW_P_curve(insert_wall)
        if g_curve_list != None:
            icurve = List[Autodesk.Revit.DB.Curve](g_curve_list)
            # --- Расположение точек в линиях должно быть последовательным для курвелооп ExporterIFCUtils.ValidateCurveLoops()
            i_crv_loop = CurveLoop.Create(icurve)
            i_list_crv_loop = List[CurveLoop]([i_crv_loop])
            return i_list_crv_loop

    def GetW_P_curve(self, u_wall):
        if u_wall.GetType().Name == "Wall":
            loc = u_wall.Location
            crv = loc.Curve
            bo = u_wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
            wh = u_wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
            move_bo = Transform.translation(XYZ(0, 0, bo))
            move_wh = Transform.translation(XYZ(0, 0, wh))
            crv1 = crv.CreateTransformed(move_bo)
            crv2 = crv1.CreateTransformed(move_wh)

            crv11 = Autodesk.Revit.DB.Line.CreateBound(crv1.GetEndPoint(0), crv2.GetEndPoint(0))
            crv22 = Autodesk.Revit.DB.Line.CreateBound(crv2.GetEndPoint(0), crv2.GetEndPoint(1))
            crv33 = Autodesk.Revit.DB.Line.CreateBound(crv2.GetEndPoint(1), crv1.GetEndPoint(1))
            crv44 = Autodesk.Revit.DB.Line.CreateBound(crv1.GetEndPoint(1), crv1.GetEndPoint(0))

            g_crv_list = [crv11, crv22, crv33, crv44]
            return g_crv_list
        else:
            return None


# -----------------------Класс OpeningHandler----------------------
class OpeningHandler:
    def __init__(self):
        pass

    """
    def IsInRoom(self,room,f):
        id = room.Id
        if f.Room != None and f.Room.Id == id:
            return True
        elif f.ToRoom != None and f.ToRoom.Id == id:
            return True
        elif f.FromRoom != None and f.FromRoom.Id == id:
            return True
        else:
            return False
    """

    def IsInRoom2(self, face, f):
        multpl = f.Host.Width / 2
        bbox_z = XYZ(0, 0, (f.get_BoundingBox(doc.ActiveView).Max.Z - f.get_BoundingBox(doc.ActiveView).Min.Z) / 2)
        x = Autodesk.Revit.DB.Line.CreateBound((f.Location.Point - f.FacingOrientation.Multiply(multpl)).Add(bbox_z),
                                               (f.Location.Point + f.FacingOrientation.Multiply(multpl)).Add(
                                                   bbox_z))  # Создаётся проверочная линия в центре семейства
        # test3.append([bbox_z,x.ToProtoType()])#([x.ToProtoType(),face.ToProtoType()])
        if face.Intersect(x) == SetComparisonResult.Disjoint:
            # test3.append(False)
            return False
        else:
            # test3.append(True)
            return True

    """	
    def GetLargestSolid(self,geomElem):
        lstHostSolids = List[Solid]
        solidMax = None
        lstVolumes = List[double]
        for geomObj in geomElem:
            geomSolid = geomObj
            if None != geomSolid:
                lstHostSolids.append(geomSolid)
                lstVolumes.append(geomSolid.Volume)
            else:
                pass
            maxVolVal = lstVolumes.Max()
            for sol in lstHostSolids:
                if sol.Volume == maxVolVal:
                    solidMax = sol
                else:
                    pass
        return solidMax
    """

    def GetOpeningArea(self, elemHost, elemInsert, room, roomSolid, face):
        doc = room.Document
        openingArea = 0
        if elemInsert.GetType().Name == "FamilyInstance":
            if self.IsInRoom2(face, elemInsert) and elemHost.GetType().Name == "Wall":
                wall = elemHost
                openingArea = self.GetWallCutArea(elemInsert, wall)
        elif elemInsert.GetType().Name == "Wall":
            solidHandler = SolidHandler()
            openingArea = solidHandler.GetWallAsOpeningArea(elemInsert, elemHost,
                                                            roomSolid)  # elemInsert.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED).AsDouble()*0.09290304#solidHandler.GetWallAsOpeningArea(elemInsert,roomSolid)
        return openingArea

    def GetWallCutArea(self, elemInsert, wall):
        doc = elemInsert.Document
        cutDir = StrongBox[XYZ](wall.Orientation)
        # family_doc = doc.EditFamily(elemInsert.Symbol.Family)
        # fam_elem = FilteredElementCollector(family_doc).OfCategory(BuiltInCategory.OST_IOSOpening) #ищим в семействе вырез под проём линиями
        try:
            curveLoop = ExporterIFCUtils.GetInstanceCutoutFromWall(doc, wall, elemInsert, cutDir)
            loops = []
            loops.append(curveLoop)
            return ExporterIFCUtils.ComputeAreaOfCurveLoops(loops)
        # """
        # if not wall.IsStackedWallMember:
        # 	return ExporterIFCUtils.ComputeAreaOfCurveLoops(loops)
        # else:
        # 	solHandler = SolidHandler()
        # 	optCompRef = doc.Application.Create.NewGeometryOptions()
        # 	if None != optCompRef:
        # 		optCompRef.ComputeReferences = True
        # 		optCompRef.DetailLevel = ViewDetailLevel.Medium
        # 		geomElemHost = wall.get_Geometry(optCompRef)
        # 		solidOpening = GeometryCreationUtilities.CreateExtrusionGeometry(loops,cutDir.Negate(),.1)
        # 		solidHost = solHandler.CreateSolidFromBoundingBox(None,geomElemHost.GetBoundingBox(),None)
        # 	if solidHost == None:
        # 		return 0
        # 	intersectSolid = BooleanOperationsUtils.ExecuteBooleanOperation(solidOpening, solidHost, BooleanOperationsType.Intersect)
        # 	if intersectSolid.Faces.Size.Equals(0):
        # 		solidOpening = GeometryCreationUtilities.CreateExtrusionGeometry(loops,cutDir,.1)
        # 		intersectSolid = BooleanOperationsUtils.ExecuteBooleanOperation( solidOpening, solidHost, BooleanOperationsType.Intersect )
        # return solHandler.GetLargestFaceArea(intersectSolid)
        # """
        except:
            solHandler = SolidHandler()
            opt = Options()
            opt.ComputeReferences = False
            opt.DetailLevel = ViewDetailLevel.Coarse
            opt.IncludeNonVisibleObjects = True
            fi_geom = elemInsert.GetOriginalGeometry(opt)
            uni_geom = None
            for g in fi_geom:
                if g.GetType() == Autodesk.Revit.DB.Solid:
                    if uni_geom == None:
                        uni_geom = g
                    else:
                        uni_geom = BooleanOperationsUtils.ExecuteBooleanOperation(uni_geom, g,
                                                                                  BooleanOperationsType.Union)
            if uni_geom.SurfaceArea == 0 or uni_geom == None:
                f_box = solHandler.CreateSolidFromBoundingBox(None, elemInsert.get_BoundingBox(doc.ActiveView), None)
            # test3.append(uni_geom.Volume)
            else:
                f_box = solHandler.CreateSolidFromBoundingBox(None, uni_geom.GetBoundingBox(), None)
            f_box_face_area = solHandler.GetLargestFaceArea(f_box)
            # test3.append(uni_geom.Volume)#([e.AsCurve().ToProtoType() for e in uni_geom.Edges])#([uni_geom.ToProtoType(),f_box.ToProtoType(),f_box_face_area])
            return f_box_face_area


# -----------------------АПИ параметры----------------------
doc = DocumentManager.Instance.CurrentDBDocument

sebOptions = SpatialElementBoundaryOptions()
sebOptions.StoreFreeBoundaryFaces = True
sebOptions.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
calculator = SpatialElementGeometryCalculator(doc, sebOptions)

# -----------------------Рабочие параметры----------------------
rooms = UnwrapElement(IN[0])
openingHandler = OpeningHandler()
compareWallAndRoom = []
list_of_opened_areas_by_room = []
# --------------------------Начало Скрипта----------------------


for room in rooms:
    list_of_cut_areas = []
    results = calculator.CalculateSpatialElementGeometry(room)
    roomSolid = results.GetGeometry()
    for face in roomSolid.Faces:
        boundaryFaceInfo = results.GetBoundaryFaceInfo(face)
        for spatialSubFace in boundaryFaceInfo:
            if spatialSubFace.SubfaceType != SubfaceType.Side:
                pass
            wall = doc.GetElement(spatialSubFace.SpatialBoundaryElement.HostElementId)
            if wall == None:
                pass
            elif wall.GetType() == Autodesk.Revit.DB.Wall:
                if wall.WallType.Kind == WallKind.Curtain:
                    pass
                else:
                    hostObject = wall
                    insertsThisHost = hostObject.FindInserts(True, False, True, True)
                    for idInsert in insertsThisHost:
                        countOnce = room.Id.ToString() + wall.Id.ToString() + idInsert.ToString()
                        if not compareWallAndRoom.Contains(countOnce):
                            elemOpening = doc.GetElement(idInsert)
                            if type(openingHandler.GetOpeningArea(wall, elemOpening, room, roomSolid, face)) == float:
                                # test3.append([wall.GetType().Name,elemOpening.GetType().Name,room.GetType().Name,roomSolid])
                                list_of_cut_areas.append(
                                    openingHandler.GetOpeningArea(wall, elemOpening, room, roomSolid, face) * 0.092903)
                                compareWallAndRoom.append(countOnce)
    list_of_opened_areas_by_room.append(list_of_cut_areas)

OUT = list_of_opened_areas_by_room, test3
