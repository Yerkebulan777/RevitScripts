# -*- coding: utf-8 -*-
# !/usr/bin/python

import glob
import os
import shutil
import stat
import sys


def get_basename(file_path):
    fullname = os.path.basename(file_path)
    filename, ext = os.path.splitext(fullname)
    return filename


def replace_files(source, targets):
    results, errors = [], set()
    if os.path.isfile(source):
        for target in targets:
            if os.path.isfile(target):
                try:
                    # os.chmod(target, stat.S_IWRITE)
                    shutil.copyfile(source, target)
                except (IOError, WindowsError, OSError) as e:
                    errors.add("Error replace: {}".format(str(e)))
                else:
                    results.append(target)

    return results, errors


########################################################################################################################
########################################################################################################################
########################################################################################################################
isp, batch_path = r'\\Iaspserv\iasp', None
include_folders = ["AR", "AS", "KJ", "KR", "KG", "OV", "VK", "EM", "EOM", "PS", "SS"]
source = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))), 'BatFiles'))
batches = [os.path.join(source, batch) for batch in os.listdir(source) if batch.endswith('bat')]
directories = [root for root in glob.iglob(isp + os.sep + '*' + os.sep + '*') if os.path.isdir(root)]
directories = [root for root in directories if get_basename(root).endswith("PROJECT")]
print("Source directory: {}".format(str(source)))
for source_batch in batches:
    targets = []
    source_name = get_basename(source_batch) + '.bat'
    print("\nSource batch is: {}!".format(source_name))
    for root in directories:
        target_batch = os.path.join(root, source_name)
        if os.path.exists(target_batch): targets.append(target_batch)
        for dirname in os.listdir(root):
            if any(dirname.endswith(section) for section in include_folders):
                target_batch = os.path.join(root, dirname, "01_RVT", source_name)
                if os.path.exists(target_batch):
                    targets.append(target_batch)
                    # print(target_batch)

    results, errors = replace_files(source_batch, targets)
    print("...Target files count: {}".format(str(len(targets))))
    print("...Replace similar files count: {} ".format(str(len(results))))
    for error in errors: print(error)
