#!/usr/bin/python
# -*- coding: utf-8 -*-

import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

elements = IN[0]
paramName = IN[1]
filterValue = IN[2]


def compare_values(value1, value2):
    if isinstance(value1, str) and isinstance(value2, str):
        value1, value2 = value1.upper(), value2.upper()
        return (value1 == value2 or value1 in value2)

    if isinstance(value1, float) and isinstance(value2, float):
        value1, value2 = round(value1, 3), round(value2, 3)
        return bool(value1 == value2)

    if isinstance(value1, int) and isinstance(value2, bool):
        return bool(bool(value1) == value2)

    return bool(value1 == value2)


values = []
output = []

if bool(paramName):
    for elem in elements:
        prmValue = elem.GetParameterValueByName(paramName)
        if not prmValue:
            elemType = elem.ElementType
            prmValue = elemType.GetParameterValueByName(paramName)

        if prmValue is not None: values.append(prmValue)
        if compare_values(filterValue, prmValue):
            output.append(elem)

OUT = output, values
