import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate("serviceAccountKey.json")
#firebase is of json format
firebase_admin.initialize_app(cred,{
    "databaseURL":"https://faceattendancerealtime-bec6e-default-rtdb.firebaseio.com/"
})
#We begin by creating a reference for the database i.e we are going to create a student directory here
ref = db.reference('Students')

data = {
    "123456":
        {
            "name": "George Varughese",
            "major": "Comp Science",
            "starting_year": 2021,
            "total_attendance": 6,
            "standing": "G",
            "year":1,
            "last_attendance_time": "2022-12-11 00:54:34"
        },

    "852741":
        {
            "name": "Jeff Bezos",
            "major": "Robotics",
            "starting_year": 2019,
            "total_attendance": 5,
            "standing": "B",
            "year": 3,
            "last_attendance_time": "2022-12-11 00:54:34"
        },

    "963852":
        {
            "name": "Elon Musk",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 12,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        }
}

#in python it is a dictionary but it is a json format
for key,value in data.items():
    #To send the data to a specific directory then we have to use child
    ref.child(key).set(value)