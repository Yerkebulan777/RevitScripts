import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import LocationCurve
from System.Windows import Clipboard

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

# Get selected elements
elements = [doc.GetElement(e) for e in uidoc.Selection.GetElementIds()]

# Check if elements are valid
if all(e.IsValidObject for e in elements):
    # Calculate total length of curved elements
    totalLength = sum(
        location.Curve.Length
        for element in elements
        if isinstance((location := element.Location), LocationCurve)
    )

    # Convert total length to millimeters and round to nearest integer
    totalLengthInMM = int(round(totalLength * 304.8))

    # Copy result to clipboard
    Clipboard.SetText(str(totalLengthInMM))

    # Output result
    OUT = totalLengthInMM
else:
    # Output error message if elements are not valid
    OUT = "Error: Invalid input elements provided"

