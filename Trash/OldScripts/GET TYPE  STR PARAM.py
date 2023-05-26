elist = IN[0]
paramname = str(IN[1])

elements = []
out_list = []

for i in range(0, len(elist)):
	elements.append(UnwrapElements(elist[i]))
for i in elements:
	elemsym = i.Symbol
	fml = elemsym.Family
	fmlparam = elemsym.get_Parameter(paramname)
	value = fmlparam.AsValueString()
	out_list.append(value)
	
OUT = out_list