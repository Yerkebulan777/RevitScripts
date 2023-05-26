import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager	
doc = DocumentManager.Instance.CurrentDBDocument
rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().ToElements()
floor = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floor).WhereElementIsNotElementType().ToElements()
#-----------ВХОДНЫЕ ДАННЫЕ------------------
par1=IN[1]
setpar=IN[2]
tire = IN[3]
zap = IN[4]
#----------ФУНКЦИИ------------------
def get3p(room):
	try:
		val1 = floor.LookupParameter(par1).AsValueString()
	except:
		val1=""		
	if val1 is None:
		val1=""
	valob=val1
	return valob
	
#----------СОРТИРОВКА ПОМЕЩЕНИЙ ПО НОМЕРУ--------------
r1=[]
list1=[]
for room in rooms:
	if room.Area>0:
		r1.append(room)
		num1=room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
		num2=""
		num3=""
		num4=""
		num5=""
		num6=""
		if "." in num1:
			c1=num1.find(".")
			num2=num1[c1+1:]
			num1=num1[:c1]
			if "." in num2:
				c2=num2.find(".")
				num3=num2[c2+1:]
				num2=num2[:c2]
				if "." in num3:
					c3=num3.find(".")
					num4=num3[c3+1:]
					num3=num3[:c3]
					if "." in num4:
						c4=num4.find(".")
						num5=num4[c4+1:]
						num4=num4[:c4]
						if "." in num5:
							c5=num5.find(".")
							num6=num5[c5+1:]
							num5=num5[:c5]
		if num1!="":
			num1=int(float(num1))
		if num2!="":
			num2=int(float(num2))
		if num3!="":
			num3=int(float(num3))
		if num4!="":
			num4=int(float(num4))
		if num5!="":
			num5=int(float(num5))
		if num6!="":
			num6=int(float(num6))		
		list1.append([room,num1,num2,num3,num4,num5,num6])
		#list1.append(UnwrapElement(room).get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString())

from operator import itemgetter
b = sorted(list1,key = itemgetter(1,2,3,4,5,6))
list2=[]
for b1 in b:
	nm1 = str(b1[1])
	if b1[2]!="":
		nm1=nm1+"."+str(b1[2])
	if b1[3]!="":
		nm1=nm1+"."+str(b1[3])		
	if b1[4]!="":
		nm1=nm1+"."+str(b1[4])
	if b1[5]!="":
		nm1=nm1+"."+str(b1[5])
	if b1[6]!="":
		nm1=nm1+"."+str(b1[6])		
	list2.append([b1[0],nm1])	
	
#---------------БЕРЕМ ПАРАМЕТРЫ-----------------------
uniq=[]
for room1 in list2:
	room = room1[0]
	valob = get3p(room)
	if valob not in uniq:
		uniq.append(valob)
numlist=[]
roomlist=[]
roomtxt=[]
for val in uniq:
	list=[]
	text=[]
	txt=""
	for room1 in list2:
		room=room1[0]
		num = room1[1]
		valob = get3p(room)
		if valob==val:
			list.append(room)
			text.append(num)
			txt=txt+num+zap
	roomtxt.append(txt[:len(txt)-1])		
	numlist.append(text)
	roomlist.append(list)
	
TransactionManager.Instance.EnsureInTransaction(doc)
i=0
for rooms in roomlist:
	for room in rooms:
		room.LookupParameter(setpar).Set(roomtxt[i])
	i=i+1
TransactionManager.Instance.TransactionTaskDone()
	
OUT = roomlist