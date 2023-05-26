#!/usr/bin/python
# -*- coding: utf-8 -*-
import math
import sys
import clr

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

clr.AddReference("System")
clr.AddReference("System.Core")
from System.IO import Path

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import GroupType
from Autodesk.Revit.DB import ModelPathUtils
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import XYZ, Floor
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.DB import BuiltInCategory, BuiltInParameter
from Autodesk.Revit.DB import RevitLinkType, RevitLinkInstance, ElementCategoryFilter

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName

TransactionManager.Instance.ForceCloseTransaction()


########################################################################################################################
def ungroup_all_elements(doc, deleted=False):
    with Transaction(doc, "Ungroup elements") as transact:
        count = int(0)
        transact.Start()
        collector = FilteredElementCollector(doc).OfClass(GroupType)
        groupTypes = collector.OfCategory(BuiltInCategory.OST_IOSModelGroups).ToElements()
        for groupType in groupTypes:
            if isinstance(groupType, GroupType):
                count += len([group.UngroupMembers() for group in groupType.Groups])
                if deleted: doc.Delete(groupType.Id)
        transact.Commit()
    message = "\nUngroup {} elements".format(count)
    return message


transform = None
revitLinkInstance = None
docCommunications = doc

linkType = (UnwrapElement(IN[0]) if bool(IN[0]) else None)
if linkType and RevitLinkType.IsLoaded(doc, linkType.Id):
    extFile = linkType.GetExternalFileReference()
    linkPath = ModelPathUtils.ConvertModelPathToUserVisiblePath(extFile.GetPath())
    linkName = Path.GetFileNameWithoutExtension(linkPath)
    for linkInst in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
        if linkInst and linkInst.GetLinkDocument():
            temp_doc = linkInst.GetLinkDocument()
            temp_name = Path.GetFileNameWithoutExtension(temp_doc.PathName)
            if linkName == temp_name:
                doc = uiapp.ActiveUIDocument.Document
                revitLinkInstance = linkInst
                docCommunications = temp_doc

########################################################################################################################
basePointFilter = ElementCategoryFilter(BuiltInCategory.OST_ProjectBasePoint)
projectBasePoint = FilteredElementCollector(doc).WherePasses(basePointFilter).FirstElement()
surveyBasePoint =  FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_SharedBasePoint).FirstElement()

origin = XYZ(0, 0, 0)
if revitLinkInstance:
    transform = revitLinkInstance.GetTotalTransform()
    resultTransformPoint = transform.OfPoint(origin)

    localLocation = doc.ActiveProjectLocation
    linkLocation = docCommunications.ActiveProjectLocation

    localTransform = localLocation.GetTotalTransform().Inverse

    localPosition = localLocation.GetProjectPosition(origin)
    prompt = "\n\n\nCurrent project location information:"
    prompt += "\n\t" + "Origin point position:"
    prompt += "\n\t\t" + "Angle: {}".format(localPosition.Angle)
    prompt += "\n\t\t" + "Elevation: {}".format(localPosition.Elevation * 304.8)
    prompt += "\n\t\t" + "East to West offset: {}".format(localPosition.EastWest * 304.8)
    prompt += "\n\t\t" + "North to South offset: {}".format(localPosition.NorthSouth * 304.8)

    linkPosition = linkLocation.GetProjectPosition(origin)
    prompt += "\n\n\nCurrent link location information:"
    prompt += "\n\t" + "Origin point position:"
    prompt += "\n\t\t" + "Angle: {}".format(linkPosition.Angle)
    prompt += "\n\t\t" + "Elevation: {}".format(linkPosition.Elevation * 304.8)
    prompt += "\n\t\t" + "East to West offset: {}".format(linkPosition.EastWest * 304.8)
    prompt += "\n\t\t" + "North to South offset: {}".format(linkPosition.NorthSouth * 304.8)

    surveyPoint = localTransform.OfPoint(origin)

    x = projectBasePoint.get_Parameter(BuiltInParameter.BASEPOINT_EASTWEST_PARAM).AsDouble()
    y = projectBasePoint.get_Parameter(BuiltInParameter.BASEPOINT_NORTHSOUTH_PARAM).AsDouble()
    z = projectBasePoint.get_Parameter(BuiltInParameter.BASEPOINT_ELEVATION_PARAM).AsDouble()
    r = projectBasePoint.get_Parameter(BuiltInParameter.BASEPOINT_ANGLETON_PARAM).AsDouble()

    result = XYZ(origin.X * math.cos(r) - origin.Y * math.sin(r), origin.X * math.sin(r) + origin.Y * math.cos(r), z)
    resultPoint =  round(x * 304.8, 3), round(y * 304.8, 3), round(z * 304.8, 3)

    OUT = dir(surveyPoint)

else:
    OUT = origin
########################################################################################################################
