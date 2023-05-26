#!/usr/bin/python
# -*- coding: utf-8 -*-

import clr
import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

from itertools import groupby, product


def Manhattan(tup1, tup2):
    return abs(tup1[0] - tup2[0]) + abs(tup1[1] - tup2[1])


# initializing list
test_list = [(4, 4), (6, 4), (7, 8), (11, 11), (7, 7), (11, 12), (5, 4)]

# printing original list
print("The original list is : " + str(test_list))

# Group Adjacent Coordinates
# Using product() + groupby() + list comprehension
man_tups = [sorted(sub) for sub in product(test_list, repeat=2) if Manhattan(*sub) == 1]

res_dict = {ele: {ele} for ele in test_list}
for tup1, tup2 in man_tups:
    res_dict[tup1] |= res_dict[tup2]
    res_dict[tup2] = res_dict[tup1]

res = [[next(val)] for key, val in groupby(sorted(res_dict.values(), key=id), id)]

# printing result
print("The grouped elemets : " + str(res))
