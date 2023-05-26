import sys
import clr
import System

sys.path.append(r"C:\Windows\System32")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("System.Drawing")
clr.AddReference("System.Management")
clr.AddReference("System.Runtime.InteropServices")
clr.AddReference("Microsoft.Office.Interop.Excel")
clr.ImportExtensions(System.Linq)

# from System.Runtime.InteropServices import *
# import Microsoft.Office.Interop.Excel as Excel

# from Microsoft.Win32 import *
# from System.Collections import *

import System.Reflection as Refl
from System.Reflection import Emit
import System.Runtime.InteropServices as Interop

assemblyBuilder = (Emit.AssemblyBuilder.DefineDynamicAssembly(Refl.AssemblyName("WIN_API_ASSEMBLY"),
                                                              Emit.AssemblyBuilderAccess.Run))

WIN_API_CALLING_CONVENTION = Interop.CallingConvention.StdCall

PINVOKE_METHOD_ATTRIBUTES = (
        Refl.MethodAttributes.Public |
        Refl.MethodAttributes.Static |
        Refl.MethodAttributes.HideBySig |
        Refl.MethodAttributes.PinvokeImpl
)

PUBLIC_STATIC_BINDING_FLAGS = Refl.BindingFlags.Static | Refl.BindingFlags.Public


def GetWinApiFunctionImpl(functionName, moduleName, charSet, returnType, *parameterTypes):
    MODULE_BUILDER = assemblyBuilder.DefineDynamicModule("WIN_API_MODULE_" + System.Guid.NewGuid().ToString())
    tbuilder = MODULE_BUILDER.DefineType("WIN_API_TYPE" + "_" + moduleName + "_" + functionName)
    mbuilder = tbuilder.DefinePInvokeMethod(functionName, moduleName, PINVOKE_METHOD_ATTRIBUTES,
                                            Refl.CallingConventions.Standard,
                                            clr.GetClrType(returnType),
                                            [clr.GetClrType(t) for t in parameterTypes].ToArray[System.Type](),
                                            WIN_API_CALLING_CONVENTION,
                                            charSet)
    mbuilder.SetImplementationFlags(mbuilder.MethodImplementationFlags | Refl.MethodImplAttributes.PreserveSig)
    winApiType = tbuilder.CreateType()
    methodInfo = winApiType.GetMethod(functionName, PUBLIC_STATIC_BINDING_FLAGS)

    def WinApiFunction(*parameters):
        return methodInfo.Invoke(None, parameters.ToArray[System.Object]())

    return WinApiFunction


def GetWinApiFunction(functionName, moduleName, returnType, *parameterTypes):
    return GetWinApiFunctionImpl(functionName, moduleName, Interop.CharSet.Auto, returnType, *parameterTypes)


FUNCTION_NAME = "SetDefaultPrinter"
MODULE_NAME = "winspool.drv"
RETURN_VALUE = System.IntPtr
PARAM_TYPES = System.String

setDefaultPrinterApiFunc = GetWinApiFunction(FUNCTION_NAME, MODULE_NAME, RETURN_VALUE, PARAM_TYPES)


def setDefaultPrinter(printerName):
    result = setDefaultPrinterApiFunc(printerName)
    return result

