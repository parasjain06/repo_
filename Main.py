import cv2
import json
import imutils
from src.postProcessing.PostProcessorPosture import processPosture
from src.postProcessing.PostProcessDrowsy import processDrowy,detect
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from PIL import Image
import uuid
from src.postProcessing.PostProcessorPosture import notifyPosture
from src.postProcessing.PostProcessDrowsy import notifyDrowsy
from src.postProcessing.PostProcessGaze import notifyGaze
import time

host_name = "127.0.0.1"
port = "8080"
host_name2 ="127.0.0.1"
port2 = "8090"

drow_url_body = "/drow/"
drow_url = "http://" + host_name + ":" + port + drow_url_body

drowCNN_url_body = "/drowCNN/"
drowCNN_url = "http://" + host_name + ":" + port + drowCNN_url_body

pos_url_body = "/posture/"
pos_url = "http://" + host_name2 + ":" + port2 + pos_url_body

img_path = "./frames/"
gaze_url_body = "/gaze/"
gaze_url = "http://" + host_name2 + ":" + port2 + gaze_url_body

def request(url, files,data):
    if files is None:
        return requests.request("POST", url, json=data)
    else:
        return requests.request("POST", url,json=data, files=files)


def img(frame):
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # return gray
    cv2.imwrite("im1.png",frame)
    cnt = open("im1.png","rb").read()
    return cnt

#Initialise Counters for Drowsiness
drowsyParamsJson = '{ "COUNTER":0,"yawnStatus":"False", "yawn":0, "prev_yawn_status":"False"}'
drowsyParamsDict = json.loads(drowsyParamsJson)

#Initialise Counters for posture
postureParamsJson = '{ "wrongPosFrame":0,"shoulderNotVisible":0, "neckStrainCounter":0, "handSupportCounter":0}'
postureParamsDict = json.loads(postureParamsJson)

video = cv2.VideoCapture(0)

DrowsyRule = False
PartialDrowsyRule = False
DrowsyCNN = False
PartialDrowsyCNN =False

text = ""
textDrowsy= ""
textPos= ""
textGaze=""
partialSleep_Counter =0
sleepy_counter = 0

totalFrames =0
unAttentiveFrame = 0

##Calculate the start time
start = time.time()
elapsed = 0

while video.isOpened():
    # Calculate the current time and
    # Elapsed time since start
    current_time = time.time()
    elapsed = current_time - start

    totalFrames =totalFrames +1
    imageRead, frame = video.read()
    if imageRead:
        frame1 = imutils.resize(frame, width=640)
        fid = uuid.uuid4()

        i_name = str(fid) + '.jpg'
        img = Image.fromarray(frame1, 'RGB')
        img.save(img_path + i_name)

        file = [
            ('file', open(img_path + i_name, 'rb'))
        ]
        fileDrow = [
            ('file', open(img_path + i_name, 'rb'))
        ]
        filePos = [
            ('file', open(img_path + i_name, 'rb'))
        ]
        fileGaze = [
            ('file1', open(img_path + i_name, 'rb'))
        ]

        #data = {'arr' : frame.tolist()}
        #data_gaze = {'arr' : frame.tolist()}

        cv2.rectangle(frame, (1, 1), (900, 100), (0, 0, 0), -1)
        cv2.putText(frame, "........................Detecting Posture, Fatigue and Attention........................", (20, 15), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 235, 0), 1, cv2.LINE_AA)
        with ThreadPoolExecutor(max_workers=4) as executor:
            posture_detect = executor.submit(request, pos_url , filePos, {})
            gaze_detect = executor.submit(request, gaze_url, fileGaze, {})
            drowsy_detectRule = executor.submit(request, drow_url ,file,{})
            drowsy_detectCNN = executor.submit(request, drowCNN_url, fileDrow, {})


        # Posture
        textPos ="Algo1 : You are in a Good posture"
        if as_completed(posture_detect):
            if posture_detect.result().status_code == 200:
                posture_detect_json = json.loads(posture_detect.result().content.decode('utf8'))
                postureParamsDict, textPos = processPosture(posture_detect_json, postureParamsDict, textPos)
                if (str(textPos) == "Algo1 : You are in a Good posture"):
                    cv2.putText(frame, textPos, (20, 35), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 235, 0), 1, cv2.LINE_AA)
                else :
                    cv2.putText(frame, textPos, (20, 35), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 0, 230), 1, cv2.LINE_AA)


        #Rule based drowsy
        textDrow = "Algo2 : No Drowsyness observed"
        drowsyParamsDict['prev_yawn_status'] = drowsyParamsDict['yawnStatus']
        if as_completed(drowsy_detectRule):
            if drowsy_detectRule.result().status_code == 200:
                drowRule_json = json.loads(drowsy_detectRule.result().content.decode('utf8'))
                ear=drowRule_json['ear']
                mouEAR = drowRule_json['mouEAR']
                textDrow,drowsyParamsDict = detect(ear, mouEAR,drowsyParamsDict,textDrow)
                if  drowsyParamsDict["yawn"] > 0:
                    DrowsyRule = True
                if drowsyParamsDict["COUNTER"] > 4:
                    PartialDrowsyRule = True
                if str(textDrow) == "Algo2 : No Drowsyness observed" :
                    cv2.putText(frame, textDrow, (20, 55), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 235, 0), 1, cv2.LINE_AA)
                else:
                    cv2.putText(frame, textDrow,(20, 55), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 0, 230), 1, cv2.LINE_AA)


        #CNN based drowsy
        if as_completed(drowsy_detectCNN):
            if drowsy_detectCNN.result().status_code == 200:
                textDrowsy= "Algo 3 : No Drowsiness Observed"
                drowCNN_json = json.loads(drowsy_detectCNN.result().content.decode('utf8'))
                pred_l = drowCNN_json["pred_l"]
                pred_r = drowCNN_json["pred_r"]

                if 0.1 < pred_l < 0.7 and 0.1 < pred_r < 0.7:
                    partialSleep_Counter = partialSleep_Counter + 1
                    textDrowsy= "Algo3 : Some Signs of Drowsiness"
                elif pred_l < 0.1 and pred_r < 0.1:
                    sleepy_counter = sleepy_counter + 1
                    textDrowsy = "Algo3 : Drowsyness"

                if sleepy_counter > 4:
                    DrowsyCNN = True
                elif partialSleep_Counter > 4:
                    PartialDrowsyCNN = True
                if str(textDrowsy) == "Algo 3 : No Drowsiness Observed":
                    cv2.putText(frame, "Algo3 : No Drowsyness observed", (20, 75), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 235, 0), 1, cv2.LINE_AA)
                else:
                    cv2.putText(frame, textDrowsy, (20, 75), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 0, 230), 1, cv2.LINE_AA)


        # Gaze
        # Gaze detection
        if as_completed(gaze_detect):
            if gaze_detect.result().status_code == 200:
                gaze_detect_json = json.loads(gaze_detect.result().content.decode('utf8'))
                print("gaze_detect_json is " + str(gaze_detect_json["text"]))
                textGaze = gaze_detect_json["text"]
                if (str(textGaze) != "Looking center"):
                    unAttentiveFrame =unAttentiveFrame +1
                    cv2.putText(frame, "Algo4 : Inattentive", (20, 95), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 0, 230), 1, cv2.LINE_AA)
                else:
                    cv2.putText(frame, "Algo4 : Attentive", (20, 95), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 235 , 0), 1, cv2.LINE_AA)

        cv2.putText(frame, "Seconds : %s"% elapsed, (120, 100), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 235, 0), 1, cv2.LINE_AA)
        cv2.imshow("Frames",frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

# do a bit of cleanup
cv2.destroyAllWindows()
video.release()

#Notification
print("Actual duration %s" % (elapsed/60))
#Initialise posture details for webex
notifyPosture(postureParamsDict,totalFrames)

# Initialise drowsiness details for webex
notifyDrowsy(DrowsyRule, DrowsyCNN,PartialDrowsyRule,PartialDrowsyCNN,drowsyParamsDict)

notifyGaze(totalFrames,unAttentiveFrame)
