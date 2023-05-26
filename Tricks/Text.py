#!/usr/bin/python
# coding: utf-8

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
# reload(sys)
# sys.setdefaultencoding("utf-8")

# import clr
# clr.AddReference("System")
# clr.AddReference("System.Core")
# clr.AddReference("RevitAPI")
# clr.AddReference("RevitAPIUI")
# clr.AddReference('RevitAPIIFC')
# clr.AddReference('RevitNodes')
# clr.AddReference('RevitServices')
# import Autodesk
# import Revit
# from Autodesk.Revit.DB import *
# from Autodesk.Revit.DB.Structure import *
# from Autodesk.Revit.DB.IFC import ExporterIFCUtils
# from Autodesk.Revit.UI.Selection import ObjectType
# from Autodesk.Revit.ApplicationServices import *
# from Autodesk.Revit.Attributes import *
# from Autodesk.Revit.UI import *
# from RevitServices.Persistence import DocumentManager
# from RevitServices.Transactions import TransactionManager
# import System
# from System.Collections.Generic import List

# clr.ImportExtensions(Revit.Elements)
# clr.ImportExtensions(Revit.GeometryConversion)

# doc = DocumentManager.Instance.CurrentDBDocument
# app = DocumentManager.Instance.CurrentUIApplication.Application
# uiapp = DocumentManager.Instance.CurrentUIApplication
# uidoc = uiapp.ActiveUIDocument

# TransactionManager.Instance.ForceCloseTransaction()
# import random
# from collections import defaultdict, namedtuple


encoding = sys.getdefaultencoding()
string_line = u""" 'привет', 'мама', 'папа', 'сиськи', 'хахаха', 'котен', 'пример' 'паралалелоограмм' 'english' """


def EncodeWinText(string, encoding='ascii'):
    rus_symbols = u"абвгдеёзийклмнопрстуфхъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЪЫЬЭ"
    eng_symbols = u"abvgdeezijklmnoprstufh'y'eABVGDEEZIJKLMNOPRSTUFH'Y'E"
    if isinstance(string, basestring):
        string = string.replace("&", 'aas').replace(u"&", 'aus')
        tr = {ord(a): ord(b) for a, b in zip(rus_symbols, eng_symbols)}
        string = string.translate(tr)
        string = string.encode('cp1251', 'ignore').decode('cp1251')
        return string.encode(encoding, 'replace').decode(encoding)
    result = 'error' + str(type(string)) + ' '
    return result.join(str(dir(string)))


print encoding
print EncodeWinText(string_line, encoding)

import re  ##Import for re or Regular Expressions

strlist = IN[0]  ##Simple list of items to match
regexExp = IN[1]  ##Regexp string to match

outlist = []
regex = re.compile(regexExp, re.IGNORECASE)
for item in strlist:  ## For each item in the list run a match
    outlist.append(regex.match(item) is not None)
    ### If match is not NONE then it is a match (true) - else (false)- append that to the list for each item

OUT = outlist  ##Set output to results
