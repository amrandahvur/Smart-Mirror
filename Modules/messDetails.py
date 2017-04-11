import json
from pyexcel_odsr import get_data
data = get_data("mess_details.ods")["Sheet1"]
import time
import datetime
import eventing

t = datetime.time

meal_times = [
	"Breakfast": (t(7, 30), t(9, 30)),
	"Lunch": (t(11, 45), t(2, 15)), 
	"Evening Tea": (t(17, 00), t(16, 00)), 
	"Dinner": (t(20, 00), t(23, 30))
]

odsIndex = {
	"Breakfast": 1,
	"Lunch": 2,
	"Evening Tea": 3,
	"Dinner": 4
}

def getMeal():
	now = datetime.datetime.now()
	for k in meal_times:
		start = datetime.datetime.combine(datetime.datetime.today(), meal_times[k][0])
		end = datetime.datetime.combine(datetime.datetime.today(), meal_times[k][1])

		weekday_index = datetime.datetime.today().weekday() + 1

		if(start < now < end):
			eventing.send(0, {
				"type": "mess-meal",
				"meal": data[odsIndex[k]][weekday_index]
			})

if __name__ == "__main__":
	print(json.dumps(data, indent=4, sort_keys=True))