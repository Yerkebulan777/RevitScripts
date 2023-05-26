# -*- coding: utf-8 -*-
rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
rooms = [i for i in rooms if i.Area > 0]

gen_mod = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_GenericModel).WhereElementIsElementType()
walls = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsElementType()
floors = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsElementType()
ceils = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Ceilings).WhereElementIsElementType()

objects = gen_mod.UnionWith(walls).UnionWith(floors).UnionWith(ceils).ToElements()


# https://www.revitapidocs.com/2020/aa41fc13-9f81-836c-4271-82568ba5d7e8.htm
def get_solids(elements, option):
    all_element_dict = {}
    for element in elements:
        all_element_dict.setdefault(element.Id.IntegerValue, [])
        geom = element.Geometry[option]
        for i in geom:
            if isinstance(i, Solid):
                all_element_dict[element.Id.IntegerValue].append(i)
            elif isinstance(i, GeometryInstance):
                all_element_dict[element.Id.IntegerValue] += [j for j in list(i.GetInstanceGeometry()) if
                                                              isinstance(j, Solid)]
    return all_element_dict


opt = Options()
opt.DetailLevel = ViewDetailLevel.Medium

objects = get_solids(objects, opt)
rooms = get_solids(rooms, opt)
with Transaction(doc, "Склейка") as t:
    t.Start()
    for room_key, room_solids in rooms.items():
        for room_solid in room_solids:
            for obj_key, obj_solids in objects.items():
                for obj_solid in obj_solids:
                    new_solid = BooleanOperationsUtils.ExecuteBooleanOperation(room_solid, obj_solid,
                                                                               BooleanOperationsType.Union)
                    is_intersect = round((new_solid.SurfaceArea - room_solid.SurfaceArea - obj_solid.SurfaceArea) + (
                                new_solid.Volume - room_solid.Volume - obj_solid.Volume), 10) != 0
                    if is_intersect:
                        r_obj = doc.GetElement(ElementId(obj_key))
                        r_room = doc.GetElement(ElementId(room_key))
                        room_number = r_room.LookupParameter("Номер").AsString()
                        room_name = r_room.LookupParameter("Имя").AsString()
                        res_string = "{} {}".format(room_number, room_name)
                        r_obj.LookupParameter("Комментарии").Set(res_string)
                        break
                else:
                    r_obj = doc.GetElement(ElementId(obj_key))
                    r_obj.LookupParameter("Комментарии").Set("Не заполнено")
    t.Commit()
