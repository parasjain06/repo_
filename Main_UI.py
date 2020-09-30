import base64

import cv2
import json
import imutils
from uvicorn.middleware.debug import HTMLResponse

from PostProcessorPosture import processPosture
from PostProcessDrowsy import processDrowy,detect
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.middleware.cors import CORSMiddleware
import requests
from PIL import Image
import uuid
from PostProcessorPosture import notifyPosture
from PostProcessDrowsy import notifyDrowsyWeb
from PostProcessGaze import notifyGaze
import time
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from fastapi import Body, File
import uvicorn
from io import BytesIO
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

def requestDetect(url, files,data):
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



video = cv2.VideoCapture(0)

DrowsyRule = False
PartialDrowsyRule = False
DrowsyCNN = False
PartialDrowsyCNN =False


##Calculate the start time
start = time.time()
elapsed = 0
# Gaze FastAPI
app = FastAPI()


#Adding CORS policy
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:4200",
    "http://localhost:4200/recorded"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Total Frames
app.state.totalFrames = 0

#Drowsy vars
app.state.Counter = 0
app.state.yawnStatus = "False"
app.state.yawn = 0
app.state.prevYawnStatus = "False"

#Posture vars
app.state.wrongPosFrame = 0
app.state.shoulderNotVisible = 0
app.state.neckStrainCounter = 0
app.state.handSupportCounter = 0

#Attentiveness vars
app.state.unAttentiveFrame = 0

#Drowsy CNN
app.state.partialSleepCounter= 0
app.state.sleepyCounter = 0

#Dicts
app.state.postureParamsDict = ""
app.state.drowsyParamsDict = ""

app.state.counter_1 = 0


@app.post("/wellness", response_class=JSONResponse)
async def wellness(request : Request,body: str = Body(...), notify: bool = None):
    print("Notify value is " +str(notify))
    request.app.state.totalFrames = app.state.totalFrames + 1
    #request.app.state.counter_1 = app.state.counter_1 +  1
    totalFrames = request.app.state.totalFrames
    #print (request.app.state.counter_1)

    app.state.Counter = request.app.state.Counter
    image = Image.open(BytesIO(base64.b64decode(body[23:])))
    postureParamsDict = {"wrongPosFrame":request.app.state.wrongPosFrame,"shoulderNotVisible":request.app.state.shoulderNotVisible,
                         "neckStrainCounter":request.app.state.neckStrainCounter, "handSupportCounter":request.app.state.handSupportCounter }
    drowsyRuleParamsDict= {"COUNTER":request.app.state.Counter, "yawnStatus":request.app.state.yawnStatus, "yawn":request.app.state.yawn, "prev_yawn_status":request.app.state.prevYawnStatus}
    drowsyCNNParamsDict = {"partialSleepCounter": request.app.state.partialSleepCounter, "sleepyCounter" : request.app.state.sleepyCounter}
    unAttentiveFrame = request.app.state.unAttentiveFrame

    # Calculate the current time and
    # Elapsed time since start
    current_time = time.time()
    elapsed = current_time - start

    fid = uuid.uuid4()
    i_name = str(fid) + '.jpg'
    image.save(img_path + i_name)

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

    with ThreadPoolExecutor(max_workers=3) as executor:
        posture_detect = executor.submit(requestDetect, pos_url , filePos, {})
        gaze_detect = executor.submit(requestDetect, gaze_url, fileGaze, {})
        drowsy_detectRule = executor.submit(requestDetect, drow_url ,file,{})
        drowsy_detectCNN = executor.submit(requestDetect, drowCNN_url, fileDrow, {})
    # Posture
    textPosReason ="You are in a Good posture"
    correctPos = "YES"
    if as_completed(posture_detect):
        if posture_detect.result().status_code == 200:
            posture_detect_json = json.loads(posture_detect.result().content.decode('utf8'))
            postureParamsDict, textPosReason = processPosture(posture_detect_json, postureParamsDict, textPosReason)
            if textPosReason != "You are in a Good posture" and textPosReason != "Are you there? I cant see you!":
                correctPos="NO"
    # Rule based drowsy
    drowTextRuleReason = "No Drowsyness observed"
    drowRule="NO"
    frameDrowRule =False
    drowsyRuleParamsDict['prev_yawn_status'] = drowsyRuleParamsDict['yawnStatus']
    if as_completed(drowsy_detectRule):
        if drowsy_detectRule.result().status_code == 200:
            drowRule_json = json.loads(drowsy_detectRule.result().content.decode('utf8'))
            ear = drowRule_json['ear']
            mouEAR = drowRule_json['mouEAR']
            drowTextRuleReason, drowsyRuleParamsDict,frameDrowRule = detect(ear, mouEAR, drowsyRuleParamsDict, drowTextRuleReason)

            if drowsyRuleParamsDict["yawn"] > 0:
                DrowsyRule = True
                drowRule = "YES"
            if drowsyRuleParamsDict["COUNTER"] > 4:
                PartialDrowsyRule = True
                drowRule = "YES"

    # CNN based drowsy
    drowTextCNNReason = "No Drowsiness Observed"
    drowCNN = "NO"
    frameDrowCNN = False
    framePartialCNN = False

    if as_completed(drowsy_detectCNN):
        if drowsy_detectCNN.result().status_code == 200:
            drowCNN_json = json.loads(drowsy_detectCNN.result().content.decode('utf8'))
            pred_l = drowCNN_json["pred_l"]
            pred_r = drowCNN_json["pred_r"]
            print("pred_l : %s" % pred_l)
            print("pred_r : %s" % pred_r)

            if 0.1 < pred_l < 0.7 and 0.1 < pred_r < 0.7:
                drowsyCNNParamsDict["partialSleepCounter"] = drowsyCNNParamsDict["partialSleepCounter"] + 1
                print("Some Signs of Drowsiness")
                drowTextCNNReason = "Some Signs of Drowsiness"
                drowCNN = "YES"
                framePartialCNN =True

            elif pred_l < 0.1 and pred_r < 0.1:
                drowsyCNNParamsDict["sleepyCounter"] = drowsyCNNParamsDict["sleepyCounter"] + 1
                print("Drowsyness ")
                drowTextCNNReason = "Drowsyness observed"
                drowCNN = "YES"
                frameDrowCNN = True

    drowText ="NO"
    drowTextReason="No Drowsiness Observed"
    if framePartialCNN == True:
        drowText = "YES"
        drowTextReason = "Some Signs of Drowsiness"
    elif frameDrowRule == True or frameDrowCNN == True:
        drowText = "YES"
        drowTextReason = "Drowsiness Observed"

    # Gaze
    # Gaze detection
    AttentiveGaze = "YES"
    textGazeReason="Gaze not detected"
    if as_completed(gaze_detect):
        if gaze_detect.result().status_code == 200:
            gaze_detect_json = json.loads(gaze_detect.result().content.decode('utf8'))
            print("gaze_detect_json is " + str(gaze_detect_json["text"]))
            textGazeReason = gaze_detect_json["text"]
            if (str(textGazeReason) != "Looking center"):
                unAttentiveFrame = unAttentiveFrame + 1
                AttentiveGaze = "NO"
            else:
                AttentiveGaze = "YES"

    print("Actual duration %s" % (elapsed/60))
    app.state.wrongPosFrame = postureParamsDict["wrongPosFrame"]
    app.state.shoulderNotVisible = postureParamsDict["shoulderNotVisible"]
    app.state.neckStrainCounter = postureParamsDict["neckStrainCounter"]
    app.state.handSupportCounter = postureParamsDict["handSupportCounter"]
    print(postureParamsDict)
    app.state.Counter = drowsyRuleParamsDict["COUNTER"]
    app.state.yawnStatus = drowsyRuleParamsDict["yawnStatus"]
    app.state.yawn = drowsyRuleParamsDict["yawn"]
    app.state.prevYawnStatus = drowsyRuleParamsDict["prev_yawn_status"]
    print(drowsyRuleParamsDict)
    app.state.partialSleepCounter = drowsyCNNParamsDict["partialSleepCounter"]
    app.state.sleepyCounter = drowsyCNNParamsDict["partialSleepCounter"]
    print(drowsyCNNParamsDict)

    app.state.postureParamsDict = postureParamsDict
    app.state.drowsyRuleParamsDict =drowsyRuleParamsDict
    app.state.unAttentiveFrame = unAttentiveFrame

    #Notification

    if(notify == True):
        #Initialise posture details for webex
        notifyPosture(postureParamsDict,totalFrames)
        # Initialise drowsiness details for webex
        notifyDrowsyWeb(drowsyRuleParamsDict,drowsyCNNParamsDict )
        notifyGaze(totalFrames,unAttentiveFrame)

    return {"correctPos" : correctPos,"textPosReason": textPosReason,"drowText":drowText ,"drowTextReason" : drowTextReason ,"yawnCount" : drowsyRuleParamsDict["yawn"],
            "AttentiveGaze" : AttentiveGaze,"textGazeReason" : textGazeReason , "wrongPosFrame" :postureParamsDict["wrongPosFrame"] , "totalFrames" : totalFrames }



if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8092)