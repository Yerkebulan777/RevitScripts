import clr

clr.AddReference("DynamoUnits")
from DynamoUnits import *

roomsAreaCoeff = []
roomsAreaMultipliedByCoeff = []
roomsArea = []
# Переменная списка комнат

apt_rooms = IN[0]  # Помещения
apt_numbers = IN[1]  # Номер квартиры
apt_types = IN[2]  # Тип помещения
roundCount = IN[3]  # Округление площади

apartments = []  # Массив квартир
apart_nums = []  # Массив номеров квартир

for i, room in enumerate(apt_rooms):
    uroom, apt_num = UnwrapElement(room), apt_numbers[i]
    area = round(uroom.Area * 0.09290304, roundCount)  #
    karea = area  # Area multiplied by coefficient
    if area > 0:
        contains = apart_nums.IndexOf(apt_num)
        koeff = 1
        if apt_types[i] == 3:
            # elif uroom.get_Parameter(parAptTip).AsInteger()==3: #Тип помещения 3
            koeff = 0.5
        elif apt_types[i] == 4:
            # elif uroom.get_Parameter(parAptTip).AsInteger()==4:#Тип помещения 4
            koeff = 0.3
        elif apt_types[i] == 5:
            # if uroom.get_Parameter(parAptTip).AsInteger()==5: #Тип помещения 5
            koeff = 0
        elif apt_types[i] == 7:
            # elif uroom.get_Parameter(parAptTip).AsInteger()==4:#Тип помещения 7
            koeff = 0.4
        if contains > -1:
            if apt_types[i] == 1:
                # if uroom.get_Parameter(parAptTip).AsInteger()==1: #Тип помещения 1
                apartments[contains][0] += 1  # По индексу квартиры добавляем еще одну комнату
                apartments[contains][2] += area  # Прибавляем площадь к Жилой площади квартиры
                apartments[contains][3] += area
            elif apt_types[i] == 2:
                # elif uroom.get_Parameter(parAptTip).AsInteger()==2: #Тип помещения 1
                apartments[contains][3] += area
            karea = round(koeff * area, roundCount)
            apartments[contains][1] += karea  # Прибавляем площадь к Общей площади квартиры
        else:
            apart_nums.append(apt_num)
            aptRoomsCount = 0
            uarea = 0
            apartarea = 0
            if apt_types[i] == 1:
                # if uroom.get_Parameter(parAptTip).AsInteger() == 1:
                aptRoomsCount = 1
                uarea = area
                apartarea = area
            elif apt_types[i] == 2:
                # elif uroom.get_Parameter(parAptTip).AsInteger()==2:
                apartarea = area
            karea = round(koeff * area, roundCount)
            apartments.append([aptRoomsCount, karea, uarea, apartarea])
    roomsAreaCoeff.append(koeff)
    roomsAreaMultipliedByCoeff.append(karea)
    roomsArea.append(area)

i = 0
outRooms = []  # Массив списка комнат на выход
for room in apt_rooms:
    uroom = UnwrapElement(room)
    apt_num = apt_numbers[i]
    # aptNum = uroom.get_Parameter(parAptNumber).AsString()
    aptPos = apart_nums.IndexOf(apt_num)
    indx = apt_rooms.IndexOf(room)
    if aptPos > -1 and uroom.Area:
        apt = apartments[aptPos]
        outRooms.append([room, apt_num + "_" + str(apt_types[i]),
                         apt[0],
                         apt[1],
                         apt[2],
                         apt[3],
                         roomsAreaCoeff[indx],
                         roomsAreaMultipliedByCoeff[indx],
                         roomsArea[indx]])
    i = i + 1
OUT = outRooms

# На выходе 8 списков
# l[0] - комнаты
# l[1] - Категория
# l[2] - Номер квартиры
# l[3] - Общая площадь квартиры
# l[4] - Жилая площадь квартиры
# l[5] - Площадь квартиры
# l[6] - Коэффициент площади комнаты
# l[7] - Площадь комнаты, умноженная на коэффициент
