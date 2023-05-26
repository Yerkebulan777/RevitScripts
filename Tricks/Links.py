import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager


def parseLinkedReference(doc, linkedRef):
    reps = linkedRef.ConvertToStableRepresentation(doc).split(':')
    res = ''
    first = True
    for i, s in enumerate(reps):
        t = s
        if "RVTLINK" in s:
            if (i < len(reps) - 1):
                if reps[i + 1] == "0":
                    t = "RVTLINK"
                else:
                    t = "0:RVTLINK"
            else:
                t = "0:RVTLINK"
        if not first:
            res = res + ":" + t
        else:
            res = t
            first = False
    ref = Reference.ParseFromStableRepresentation(doc, res)
    return ref


doc = DocumentManager.Instance.CurrentDBDocument
family_type = UnwrapElement(IN[0])
hosts = UnwrapElement(IN[1])
linked_instance = UnwrapElement(IN[2])

output = []
TransactionManager.Instance.EnsureInTransaction(doc)

for h in hosts:
    reference = HostObjectUtils.GetBottomFaces(h)[0]
    linked_reference = reference.CreateLinkReference(linked_instance)

    parsed_ref = parseLinkedReference(doc, linked_reference)
    face = h.GetGeometryObjectFromReference(reference)
    bb = face.GetBoundingBox()
    centerUV = bb.Min + (bb.Max - bb.Min) / 2
    p = face.Evaluate(centerUV)
    inst = doc.Create.NewFamilyInstance(parsed_ref, p, XYZ(0, 0, 0), family_type)
    output.append(inst)

TransactionManager.Instance.TransactionTaskDone()
