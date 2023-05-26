#!/usr/bin/python
# -*- coding: cp1251 -*-


import os
import time
import shutil


########################################################################################################################
days = 3  # specify the days
delay = (days * 24 * 60 * 60)
seconds = time.time() - delay
temp = os.path.realpath(os.getenv("TEMP"))
for filename in os.listdir(temp):
    source = os.path.join(temp, filename)
    if seconds > os.stat(source).st_ctime:
        if os.path.isfile(source):
            try:
                os.remove(source)
            except OSError as e:
                print("Error delete file: %s" % (e.message))
        if os.path.isdir(source):
            try:
                shutil.rmtree(source)
            except OSError as e:
                print("Error delete directory: %s" % (e.message))

print("\r\n\tClear temp directory  completed!!!\r\n\t")
########################################################################################################################
