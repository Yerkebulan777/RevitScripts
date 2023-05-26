#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
from collections import defaultdict

import clr

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference('System')
import System
from System.Collections.Generic import *

clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument


def GetStyleName(geobject):
    gstyle = doc.GetElement(geobject.GraphicsStyleId)
    if gstyle is not None:
        gstyle_name = gstyle.GraphicsStyleCategory.Name
        return gstyle_name


def LineIdByPoLyLine(geobj, view):
    geotype = geobj.GetType().Name
    if geotype == "PolyLine":
        next, strpt = int(0), XYZ(0, 0, 0)
        num = geobj.NumberOfCoordinates
        idx = None
        for idx in range(num):
            if int(idx + 1) == int(num): break
            strpt = geobj.GetCoordinate(idx)
            endpt = geobj.GetCoordinate(int(idx + 1))
            length = strpt.DistanceTo(endpt)
            if length < 0.5: continue
            crv = Line.CreateBound(strpt, endpt)
            crv = doc.Create.NewDetailCurve(view, crv)
        return num, idx


def DetailLinesIds(geobjts, view):
    layerdict = defaultdict(list)
    test = []
    for geobj in geobjts:
        if not geobj: continue
        geotype = geobj.GetType().Name
        if geotype == "GeometryInstance":
            geobj = geobj.GetInstanceGeometry()
            for geo in geobj:
                if geotype == "Line":
                    if geo.Length < 0.05: continue
                    style = GetStyleName(geobj)
                    #crv = doc.Create.NewDetailCurve(view, geo)
                    #layerdict[style].append(strId)
                if geotype == "PolyLine":
                    style = GetStyleName(geobj)
                    strids = LineIdByPoLyLine(geobj, view)
                    test.append(strids)
                    #layerdict[style].extend(strids)
        if geotype == "Line":
            if geobj.Length < 0.05: continue
            style = GetStyleName(geobj)
            #crv = doc.Create.NewDetailCurve(view, geobj)
            #layerdict[style].append(strId)
        if geotype == "PolyLine":
            style = GetStyleName(geobj)
            strids = LineIdByPoLyLine(geobj, view)
            test.append(strids)
            #layerdict[style].extend(strids)
    return test


def GetCadLinesDict():
    view = List[ElementId]()
    view.Add(doc.ActiveView.Id)
    view = FilteredElementCollector(doc, view).OfClass(Autodesk.Revit.DB.ViewPlan).FirstElement()
    for cadlink in FilteredElementCollector(doc).OfClass(Autodesk.Revit.DB.CADLinkType):
        if cadlink.IsExternalFileReference() and bool(view):
            ref = Reference(cadlink)
            sref = ref.ConvertToStableRepresentation(doc)
            pref = Reference.ParseFromStableRepresentation(doc, sref)
            geobjts = cadlink.GetGeometryObjectFromReference(pref)
            if not bool(geobjts): continue
            geobjts = [geo for geo in geobjts if geo.GraphicsStyleId]
            layerdict = DetailLinesIds(geobjts, view)
            return layerdict


def SortedKey(layerdict):
    keys, lenvals = [], []
    for k in layerdict.iterkeys():
        lenvals.append(len(layerdict.get(k)))
        keys.append(k)
    ignored = sum(lenvals) * 0.05
    sortkey = [k for i, k in sorted(zip(lenvals, keys)) if i > ignored]
    return sortkey


def GroupLinesByJoin(lineIds):
    def flatten(listOfLists):
        import itertools
        return itertools.chain.from_iterable(listOfLists)

    test = []
    key = int(0)
    groupdict = defaultdict(set)
    lineIds = flatten(lineIds)
    for strid in lineIds:
        if not strid: continue
        test.append(strid)
        """
        pnt01, pnt02 = crv.GetEndPoint(0), crv.GetEndPoint(1)
        
        
        id01 = {crv.Id for crv, duple in zip(lines, lines) if crv.Distance(pnt01) < 0.05}
        id02 = {crv.Id for crv, duple in zip(lines, lines) if crv.Distance(pnt02) < 0.05}
        ids = id01.union(id02)
        if len(ids) <= 1: continue
        dicids = flatten(groupdict.viewvalues())
        if ids and bool(set(dicids).intersection(ids)):
            count = len(groupdict.viewkeys())
            for key, val in list(groupdict.iteritems()):
                if bool(set(val).intersection(ids)):
                    val = groupdict.pop(key)
                    ids.union(val)
                    if count > key:
                        count = key
                groupdict.update({key: ids})
        else:
            key += 1
            groupdict.update({key: ids})

    setids = set(groupdict.values())
    for ids in lines:
        if bool(setids.intersection(ids)):
            doc.Delete(ids)
            doc.Regenerate()
            """
    return test


###########################################################################
TransactionManager.Instance.EnsureInTransaction(doc)
layerdict = GetCadLinesDict()
#sortedkey = SortedKey(layerdict)[-1]
#linelst = layerdict.get(sortedkey)
#test = GroupLinesByJoin(linelst)
TransactionManager.Instance.TransactionTaskDone()
###########################################################################


OUT = layerdict
