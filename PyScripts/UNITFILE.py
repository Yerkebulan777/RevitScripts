import clr

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)

elements = IN[0]
elevations = IN[1]
lvlNumList = IN[2]
lvlElevList = IN[3]

output = []

offsetCategories = ['apple', 'banana', 'cherry']

for value, element in zip(elevations, elements):
    categoryName = UnwrapElement(element).Category.Name
    value = value + 250 if categoryName in offsetCategories else value

    if value < 0:
        output.append(-1)
        continue

    for lvlElevation, lvlNumber in zip(lvlElevList, lvlNumList):

        if value > lvlElevation:
            output.append(lvlNumber)
            break


levelElevations = IN[0]
basePointOffset = IN[1]

OUT = [round(val + basePointOffset) for val in levelElevations]
