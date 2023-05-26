import clr

# Import RevitAPI
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# Import RevitAPIUI
clr.AddReference('RevitAPIUI')
# Import DocumentManager and TransactionManager
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager

# Import Dynamo Python References
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

# Import RevitNodes
clr.AddReference('RevitNodes')

# Assign Labels to Revit Document and Application
doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application

ele = IN[0]
param = IN[1]

# val = IN[2]
outTC = []
famType = []
for i in UnwrapElement(IN[0]):
    id = i.GetTypeId()
    if id == ElementId.InvalidElementId:
        famType.append(None)
    else:
        famType.append(doc.GetElement(id))

builtInParmTM = BuiltInParameter.ALL_MODEL_TYPE_MARK
builtInParmComm = BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
# TransactionManager.Instance.EnsureInTransaction(doc)

# Cycle through all Family Element Types
for i in UnwrapElement(famType):
    # Cycle through All Type Parameters from Family Type
    # Get BuiltInParameter Values
    comments = i.get_Parameter(builtInParmComm)
    typeMark = i.get_Parameter(builtInParmTM)
    outTC.append(typeMark.AsString())
for i in UnwrapElement(ele):
    for j in i.Parameters:
        if j.IsShared and j.Definition.Name == param:
            paramVal = i.get_Parameter(j.GUID)
            outTC.append(paramVal.AsString())
# Set BuiltInParameter Values
# typeMark = c.Set(val)


OUT = outTC
