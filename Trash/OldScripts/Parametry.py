# -*- coding: UTF-8 -*-
from Autodesk.Revit.DB import BuiltInCategory
from Autodesk.Revit.DB import Wall, BuiltInParameter, Transaction, FilteredElementCollector

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
active_view = doc.ActiveView

sel = uidoc.Selection  # Объект отвечающий за все выбранные элементы. Отсюда мы их сможем получить
els = [doc.GetElement(i) for i in sel.GetElementIds()]

walls = FilteredElementCollector(doc).OfClass(Wall).ToElements()
rooms = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_Rooms).ToElements()

room = rooms[0]  # Возьмем первую комнату

par = room.GetParameters("Отделка стен")[0]
par_str = par.AsString()

# Вычислим площадь стен
summ_area = 0
for wall in walls:
    summ_area += wall.LookupParameter("Площадь").AsDouble() * 0.3048 ** 2  # переводим в квадратные метры
summ_area = round(summ_area, 2)

with Transaction(doc, "Запись параметра в стены") as t:
    t.Start()
    for i in walls:
        i.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(par_str)
    room.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(str(summ_area))
    t.Commit()
