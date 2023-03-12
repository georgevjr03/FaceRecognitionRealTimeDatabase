import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
#firebase is of json format
firebase_admin.initialize_app(cred,{
    "databaseURL":"https://faceattendancerealtime-bec6e-default-rtdb.firebaseio.com/",
    "storageBucket": "faceattendancerealtime-bec6e.appspot.com"
})
bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)


imgBackground = cv2.imread('Resources/background.png')
#Importing The Mode Images
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
#['.DS_Store', '4.png', '2.png', '3.png', '1.png']
for path in modePathList:
    if path!='.DS_Store':
        imgModeList.append(cv2.imread(os.path.join(folderModePath,path)))

#print(len(imgModeList))


#Load the encoding file
print("Loading Encode File ....")
file = open("EncodeFile.p","rb")
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
#print(studentIds) ['963852', '852741', '123456']
print("Encode File Loaded ....")

modeType = 0
counter = 0
id = -1
imgStudent = []
while True:
    success, img = cap.read()

    #We will have to scale down our image since lot of computation  power takes place
    #To 1/4 th of the size
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    # openCv uses RGB and face_recognition library uses RGB hence we have to convert it
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    #Now we have to feed in the value to our face recognition system and it will detect
    #and give us some o/p
    faceCurFrame = face_recognition.face_locations(imgS)
    #Don't need to find the encoding of the whole Image only the encoding of the face
    #So we are giving the loc of the face and we are telling to extract it and find the img
    encodeCurFrame = face_recognition.face_encodings(imgS,faceCurFrame)


    imgBackground[162:162+480,55:55+640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    if faceCurFrame:
        #Now we are going to loop thru all the encodings and one by one we're going to compare
        #it with the generated encodings i.e whether their matching
        for encodeFace, faceLoc in zip(encodeCurFrame,faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown,encodeFace)
            #The lower the face dist the better the match
            faceDis = face_recognition.face_distance(encodeListKnown,encodeFace)
            #print("matches", matches)
            #print("faceDis", faceDis)
            #matches[False, False, True]
            #aceDis[0.76043034 0.79221649 0.43829038]

            matchIndex = np.argmin(faceDis)
            #print("Match Index", matchIndex)
            #With this match Index we will chk inside matches list and if it is true then
            #correct face detected
            if matches[matchIndex]:
                #print("Known Face Detected")
                #print(studentIds[matchIndex])
                #Drawing a rectangle
                y1, x2, y2, x1 = faceLoc
                #we intially reduced the size of img by 1/4 th now back to org size
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                #our img is not starting frm 0,we have to add an x and y value then only our imgs start
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                #rt-rectangle thickness,bbox-bounding box
                imgBackground = cvzone.cornerRect(imgBackground,bbox,rt=0)
                id = studentIds[matchIndex]
                if counter == 0:
                    #To partially remove the lag of loading the image:
                    cvzone.putTextRect(imgBackground, "Loading" , (275, 400))
                    cv2.imshow("Face Attendance", imgBackground)
                    # adding a delay of 1 ms
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

        if counter!=0:
            #We will only download the datas from the database during the 1st frame only
            if counter == 1:
                # Get the data
                studentInfo = db.reference(f'Students/{id}').get()
                print(studentInfo)
                #Get the image from the storage
                blob = bucket.get_blob(f'Images/{id}.png')
                #uint8-Unsigned int 8
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgStudent = cv2.imdecode(array,cv2.COLOR_BGRA2BGR)
                #Update data of attendance
                #Since the date is in str we will need to convert it into the actual format
                dateTimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                                                   "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now()-dateTimeObject).total_seconds()
                print(secondsElapsed)
                if secondsElapsed>30:
                    ref = db.reference(f'Students/{id}')
                    studentInfo['total_attendance']+=1
                    ref.child('total_attendance').set(studentInfo['total_attendance'])
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    modeType = 0
                    counter = 0
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

            if 10<counter<20:
                modeType = 2
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
            if modeType != 0:
                if counter<=10:
                    #Here this is used for putting text on images i.e in the first case we are referencing the total_attendance just like a dictionary
                    cv2.putText(imgBackground,str(studentInfo['total_attendance']),(861,125),
                                cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1)
                    cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(id), (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                    #Since we want to center align our name so basically we will calculate the empty space and place the text there as well
                    (w, h), _ = cv2.getTextSize(studentInfo['name'],cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414-w)//2
                    cv2.putText(imgBackground, str(studentInfo['name']), (808+offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                    imgBackground[175:175+216,909:909+216] = imgStudent


                counter+=1

                if counter>=20:
                    #basically Reset all values back to default
                    counter = 0
                    modeType = 3
                    studentInfo = []
                    imgStudent = []
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    else:
        modeType = 3
        counter = 0
    #cv2.imshow("Webcam", img)
    cv2.imshow("Face Attendance", imgBackground)
    #adding a delay of 1 ms
    cv2.waitKey(1)