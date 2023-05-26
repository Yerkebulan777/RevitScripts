# -*- coding: UTF-8 -*-
import random


def points_by_lenght(points, diameter, max_length):
    idx = 0
    result = []
    overlap = float(diameter * 50)
    mid_length = round(float(max_length - overlap), 5)
    while idx < len(points):
        tolerance = float(0)
        point = points.pop(idx)
        result.append(point)
        points = [q for i, q in enumerate(points) if i >= idx]
        for count, q in enumerate(points):
            distance = round(float(point.DistanceTo(q)), 5)
            if tolerance < distance <= mid_length:
                tolerance = distance
                idx = count
    return result


def get_optimal_lenth(data_list, max_length):
    queue = set()
    result = None
    balance = float("inf")
    for idx, value in enumerate(data_list):
        longness = []
        residuary = []
        if sum(residuary) < balance:
            balance = sum(residuary)
            result = longness
        if idx != 0:
            if idx < min(queue):
                longness.append(data_list[0])
            else:
                break
        while idx < len(data_list):
            find = None
            current = data_list[idx]
            longness.append(current)
            tolerance = remainder = float(0)
            for count, value in enumerate(data_list):
                distance = float(value - current)
                if tolerance < distance <= max_length:
                    remainder = max_length - distance
                    tolerance = distance
                    idx = count
                    find = True
            if find:
                residuary.append(remainder)
                queue.add(idx)
            else:
                break
    return result


########################################################################################################################
division = 15  # На сколько частей делится линия
max_length = 6000  # Максимальная длина элемента
path_length = 25000  # Общая длина линии расположения
########################################################################################################################

data_list = []
divide = 1 / float(division)
data_list.append(float(0))
for count in range(division):
    parameter = divide * float(count)
    minval = round(parameter * path_length)
    maxval = round((parameter + divide) * path_length)
    length = round(random.randint(int(minval), int(maxval)), 5)
    data_list.append(length)
data_list.append(path_length)

result = get_optimal_lenth(data_list, max_length)
print data_list
print result, len(data_list)
