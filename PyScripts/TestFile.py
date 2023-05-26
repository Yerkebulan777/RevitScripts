#!/usr/bin/env python
# -*- coding: utf-8 -*-

import difflib
import glob
import os
import re

from natsort import natsorted

pattern = re.compile(r'(?P<number>\b(Лист)\b\W*\b(\w+\S*\d*)\b)')


def getBasename(file_path):
    fullname = os.path.basename(file_path)
    filename, ext = os.path.splitext(fullname)
    return filename


def getSheetNumber(filepath):
    sheet_name = getBasename(filepath)
    name_match = pattern.search(sheet_name)
    print(sheet_name)
    if bool(name_match):
        sheet_number = name_match.group('number').strip()
        sheet_number = re.sub(r'(Лист\W*)', '', sheet_number, re.UNICODE)
        return sheet_number
    return sheet_name


def getSubdirectory(ipath, directory):
    folder = os.path.basename(os.path.dirname(ipath))
    drive, tail = os.path.splitdrive(ipath)
    ipath = os.path.realpath(ipath)
    while os.path.exists(ipath):
        if folder == '': return drive
        result = os.path.join(ipath, folder)
        ipath, folder = os.path.split(ipath)
        if folder.endswith(directory):
            return result


def determineDirectory(ipath, directory, folder=None):
    result = os.path.join(getSubdirectory(ipath, 'PROJECT'), directory)
    if bool(os.path.exists(result) and folder):
        result = os.path.join(result, folder)
    if not os.path.exists(result):
        os.makedirs(result)
    return result


def retrieveArchModelPath(filepath, tolerance=0.75, result=None):
    regex = re.compile(r'#')
    filename = os.path.basename(filepath)
    filename, extension = os.path.splitext(filename)
    directory = getSubdirectory(filepath, 'PROJECT')
    directory = os.path.dirname(directory)
    print("FileName: {}".format(filename))
    for folder in os.listdir(directory):
        if (folder.endswith('AR') or folder.endswith('AS')):
            path = os.path.join(directory, folder)
            if os.path.isdir(path):
                paths = glob.glob(path + '/*' + extension)
                paths.extend(glob.glob(path + '/**/*' + extension))
                paths.extend(glob.glob(path + '/***/**/*' + extension))
                for idx, path in enumerate(paths):
                    if regex.search(path): continue
                    name, extension = os.path.splitext(os.path.basename(path))
                    matchValue = difflib.SequenceMatcher(None, filename, name).ratio()
                    if matchValue > tolerance:
                        tolerance = matchValue
                        result = path
    return result



extension = '.pdf'
path = r"I:\112_AKBULAK_URBAN\01_PROJECT\III_6-1_SS\03_PDF\2023-04-14\AKB-RVS_SS_URBN_villa_XL_6.3"
paths = glob.glob(path + '/*' + extension)
paths.extend(glob.glob(path + '/**/*' + extension))
paths.extend(glob.glob(path + '/***/**/*' + extension))
for current in paths:
    getSheetNumber(current)

