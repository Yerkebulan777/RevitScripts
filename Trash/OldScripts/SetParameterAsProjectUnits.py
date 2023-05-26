def checkParameter(param):
    for p in param:
        internal = p.Definition
        if internal.BuiltInParameter != BuiltInParameter.INVALID:
            return p
    return param[0]


parameters = []

for e in element:
    param = e.GetParameters(name)
    p = checkParameter(param)
    parameters.append(p)

TransactionManager.Instance.EnsureInTransaction(doc)
for i, p in enumerate(parameters):
    if p is None:
        listout.append(None)
    elif p.StorageType == StorageType.Double:
        ProjectUnits = p.DisplayUnitType
        newval = UnitUtils.ConvertToInternalUnits(values, ProjectUnits)
        p.Set(newval)
        listout.append(element[i])
    elif p.StorageType == StorageType.ElementId:
        newval = UnwrapElement(values)
        p.Set(newval.Id)
        listout.append(element[i])
    else:
        p.Set(values)
        listout.append(element[i])
TransactionManager.Instance.TransactionTaskDone()
