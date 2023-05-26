#!/usr/bin/python
# -*- coding: utf-8 -*-


import codecs
import glob
import os
import re
import shutil
import stat
import sys
import sysconfig
from datetime import datetime

lib_paths = sysconfig.get_paths()
encoding = sys.getfilesystemencoding()
[sys.path.append(path) for key, path in lib_paths.items()]

pattern = re.compile(r'(?P<number>\b(Лист)\b\W*\b(\w+\S*\d*)\b)')

from natsort import natsorted
from PyPDF2 import PdfFileMerger


def getBasename(file_path):
    fullname = os.path.basename(file_path)
    filename, ext = os.path.splitext(fullname)
    return filename


def get_subdirectory(ipath, directory):
    folder = os.path.basename(os.path.dirname(ipath))
    drive, tail = os.path.splitdrive(ipath)
    ipath = os.path.realpath(ipath)
    while os.path.exists(ipath):
        if folder == '': return drive
        result = os.path.join(ipath, folder)
        ipath, folder = os.path.split(ipath)
        if folder.endswith(directory):
            return result


def determine_folder_structure(ipath, directory, folder=None):
    result = os.path.join(get_subdirectory(ipath, 'PROJECT'), directory)
    if bool(os.path.exists(result) and folder):
        result = os.path.join(result, folder)
    if not os.path.exists(result):
        os.makedirs(result)
    return result


def getSheetNumber(filepath):
    sheet_name = getBasename(filepath)
    name_match = pattern.search(sheet_name)
    if bool(name_match):
        sheet_number = name_match.group('number').strip()
        sheet_number = re.sub(r'(Лист\W*)', '', sheet_number, re.UNICODE).lower()
        return sheet_number
    return sheet_name


def sortPdfFiles(paths):
    title = re.compile(r'(Титул?)|(Обложка?)', re.UNICODE)
    paths = natsorted(paths, key=lambda x: getSheetNumber(x))
    titles = [paths.pop(idx) for idx, path in enumerate(paths) if title.match(getBasename(path))]
    paths = (titles.extend(paths) if len(titles) > 0 else paths)
    return paths


def removeDirectory(source):
    try:
        os.chmod(source, stat.S_IWRITE)
        [os.remove(os.path.join(source, entry)) for entry in os.listdir(source)]
        shutil.rmtree(source)
    except (OSError, WindowsError) as error:
        message = "Error remove: {}".format(str(error))
        print(message)
        return
    return


def copySeparatePdfFiles(source, destination):
    if os.path.exists(destination): removeDirectory(destination)
    if not os.path.exists(destination): os.makedirs(destination)
    files = glob.glob(os.path.join(source, '*.pdf'))
    files, result = sortPdfFiles(files), []
    for i, pdf in enumerate(files):
        filename = "{}.pdf".format(getBasename(pdf))
        target = os.path.join(destination, filename)
        shutil.copyfile(pdf, target)
        result.append(target)
    return result


def mergePdfFiles(source, outfile):
    merger, result = PdfFileMerger(), []
    files = glob.glob(os.path.join(source, '*.pdf'))
    if os.path.exists(outfile): os.remove(outfile)
    for i, pdf in enumerate(sortPdfFiles(files)):
        pdfName = getBasename(pdf)
        merger.append(pdf, pdfName)
        result.append(pdfName)
    with open(outfile, 'wb') as fileobject:
        merger.write(fileobject)
        merger.close()
    return result


########################################################################################################################
revit_file_path = ""
print("Run Merge PDF...")
revit_file_name = sys.argv[1]
temp_path = os.path.realpath(os.getenv("TEMP"))
save_time_date = format(datetime.now(), "%Y-%m-%d")
fileInput = os.path.join(temp_path, "PrintTempPath.txt")

if os.path.exists(fileInput):
    os.chmod(fileInput, stat.S_IWRITE)
    with codecs.open(fileInput, 'r', 'cp1251', 'ignore') as input:
        revit_file_path = os.path.normpath(os.path.abspath(input.read()))
        destination = determine_folder_structure(revit_file_path, '03_PDF', save_time_date)

########################################################################################################################
revitFileBool = os.path.exists(revit_file_path)
if not os.path.exists(destination): os.makedirs(destination)
if revitFileBool: print("\nRevit file name {}\n".format(revit_file_name))
if revitFileBool: print("\nDestination pdf files path {}".format(destination))
if revitFileBool: print("\nSource revit file path {}\n".format(revit_file_path))
if not revitFileBool: print("\nERROR: Revit file path not read {}\n".format(revit_file_path))
########################################################################################################################
separate, merged = None, None
os.chmod(destination, stat.S_IWRITE)
if os.path.exists(destination) and revitFileBool:
    for filename in os.listdir(temp_path):
        if filename.startswith(revit_file_name):
            os.chmod(destination, stat.S_IWRITE)
            source = os.path.join(temp_path, filename)
            output = os.path.join(destination, filename)
            separate = copySeparatePdfFiles(source, output)
            outfile = os.path.join(destination, filename + '.pdf')
            merged = mergePdfFiles(source, outfile)
            print("PDF file path: " + outfile)
            removeDirectory(source)
########################################################################################################################
if all([separate, merged]):
    print("\r\n\t ... Script Merge PDF successfully!")
    os.startfile(destination)
elif os.path.exists(destination):
    print("... Something went wrong!!!")
    os.startfile(destination)
########################################################################################################################
