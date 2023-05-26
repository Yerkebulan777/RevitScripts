# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')

import os
import clr
import System
import fnmatch

clr.AddReference('System')

python_path = sys.executable
script_path = r'D:\TEMP\CustomPaperSize.py'
form_name, width_mm, height_mm = 'CustomSize', 369, 689


def get_python_path(python_path):
    environ_paths = os.environ.get("PATH", None)
    basepaths = [os.path.realpath(path) for path in environ_paths.split(';') if os.path.exists(path)]
    for basepath in basepaths:
        for entry in os.listdir(basepath):
            if fnmatch.fnmatch(entry, 'python.exe'):
                if 'Python' in os.path.basename(os.path.normpath(basepath)):
                    python_path = os.path.join(basepath, entry)
                    print python_path
    return python_path


def call_python_script(python_path, script_path, form_name, width_mm, height_mm):
    try:
        process = System.Diagnostics.Process()
        start = System.Diagnostics.ProcessStartInfo()
        start.FileName = python_path
        start.Arguments = str.format("{0} {1} {2} {3}", script_path, form_name, width_mm, height_mm)
        # arg[0] = Path to your python script (example : C:\\python_script.py)
        start.RedirectStandardOutput = True
        start.UseShellExecute = False
        process.StartInfo = start
        process.Start()
        output = process.StandardOutput.ReadToEnd()
        process.WaitForExit()
    except Exception as output:
        raise output
    return output


python_path = get_python_path(python_path)
result = call_python_script(python_path, script_path, form_name, width_mm, height_mm)
print result
