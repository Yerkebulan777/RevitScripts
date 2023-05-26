#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import clr

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

clr.AddReference("System")
clr.AddReference("System.Core")

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference('RevitNodes')
clr.AddReference('RevitServices')

import Revit
import Autodesk

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)
from Autodesk.Revit.DB import Transaction, FilteredElementCollector, ElementId
from Autodesk.Revit.DB import FailureSeverity, FailureProcessingResult
from Autodesk.Revit.DB import IFailuresPreprocessor, BuiltInFailures
from Autodesk.Revit.DB import BuiltInCategory

from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

from System.Collections.Generic import List

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


class warning_dismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        for failure in failuresAccessor.GetFailureMessages():
            fail_severity = failure.GetSeverity()
            if (fail_severity == FailureSeverity.Warning):
                failuresAccessor.DeleteWarning(failure)
        return FailureProcessingResult.Continue


result = set()
categories = doc.Settings.Categories
with Transaction(doc, "AutoDelete") as trans:
    excluded = []
    excluded.append(-2000011)  # Стены
    excluded.append(-2000100)  # Колонны
    excluded.append(-2000170)  # Панели витража
    excluded.append(-2000180)  # Пандус
    excluded.append(-2000120)  # Лестницы
    excluded.append(-2000126)  # Ограждения
    excluded.append(-2000023)  # Двери
    excluded.append(-2000014)  # Окна
    excluded.append(-2000032)  # Перекрытия
    excluded.append(-2000038)  # Потолки
    excluded.append(-2000171)  # Импосты витража
    excluded.append(-2000340)  # Витражные системы
    excluded.append(-2001330)  # Несущие колонны
    excluded.append(-2001320)  # Каркас несущий
    excluded.append(-2000035)  # Крыши
    excluded.append(-2000095)  # Группы
    excluded.append(-2000996)  # Проемы для шахты
    excluded.append(-2001300)  # Фундамент
    excluded.append(-2001336)  # Фермы
    excluded.append(-2001340)  # Топография
    excluded.append(-2001370)  # Антураж
    trans.Start()
    fail_options = trans.GetFailureHandlingOptions()
    fail_options.SetFailuresPreprocessor(warning_dismiss())
    trans.SetFailureHandlingOptions(fail_options)
    for cat in categories:
        flag = None
        cat_type = cat.CategoryType
        cat_database = Autodesk.Revit.DB.CategoryType
        if cat_type.Equals(cat_database.Annotation): flag = True
        if cat_type.Equals(cat_database.AnalyticalModel): flag = True
        if cat.Id.IntegerValue not in excluded: flag = True
        if flag:
            try:
                collector = FilteredElementCollector(doc).OfCategoryId(cat.Id)
                ids = collector.WhereElementIsElementType().ToElementIds()
                doc.Delete(List[ElementId](ids))
                if ids: result.add(cat.Name)
            except:
                doc.Regenerate()
                for i in ids:
                    try:
                        doc.Delete(i.Id)
                    except Exception:
                        pass
    trans.Commit()

ids = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElementIds()
with Transaction(doc, "ReDelete") as trans:
    try:
        trans.Start()
        doc.Delete(List[ElementId](ids))
        trans.Commit()
    except:
        trans.RollBack()

OUT = result
