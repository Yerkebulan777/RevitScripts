#!/usr/bin/python
# -*- coding: utf-8 -*-

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
import Autodesk
clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.GeometryConversion)
#from Revit import GeometryConversion as gp

import math

curves = IN[0]
# Следующие 2 метода будут предполагать, что направления известны.
#The start point of a curve
def startPoint(curve):
    return curve.GetEndPoint(0)

#The end point of a curve
def endPoint(curve):
    return curve.GetEndPoint(1)
# Groups lines to be joined in sublists with the curves that have to be joined
def joinCurves(list):
  comp=[]
  re=[]
  unjoined = []
  for crv in curves:
    crv = crv.ToRevitType()
    match = False
    for co in comp:
      if startPoint(crv).IsAlmostEqualTo(startPoint(co)) and endPoint(crv).IsAlmostEqualTo(endPoint(co)):
        match = True
    if match:
      continue
    else:
      comp.append(crv)
      joined = []
      for c2 in curves:
        match = False
        c2 = c2.ToRevitType()
        for co in comp:
          if startPoint(c2).IsAlmostEqualTo(startPoint(co)) and endPoint(c2).IsAlmostEqualTo(endPoint(co)):
            match = True
        if match:
          continue
        else:
          if c2.Intersect(crv) == SetComparisonResult.Disjoint:
            continue
          elif c2.Intersect(crv) ==  SetComparisonResult.Equal:
            continue
          elif c2.Intersect(crv) == SetComparisonResult.Subset:
            comp.append(c2)
            joined.append(c2.ToProtoType())
    joined.append(crv.ToProtoType())
    re.append(joined)

  return re

result = joinCurves(curves)
OUT = result