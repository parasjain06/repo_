from scipy.spatial import distance as dist
from src.Notifier.Notifier import notify
import _pickle as cPickle
# calculating eye aspect ratio
import numpy as np
def eye_aspect_ratio(eye):
    # compute the euclidean distances between the vertical
    print("inside eye_aspect_ration")
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    print("inside 2eye_aspect_ration")
    # compute the euclidean distance between the horizontal
    C = dist.euclidean(eye[0], eye[3])
    # compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)
    return ear


# calculating mouth aspect ratio
def mouth_aspect_ratio(mou):
    # compute the euclidean distances between the horizontal
    X = dist.euclidean(mou[0], mou[6])
    # compute the euclidean distances between the vertical
    Y1 = dist.euclidean(mou[2], mou[10])
    Y2 = dist.euclidean(mou[4], mou[8])
    # taking average
    Y = (Y1 + Y2) / 2.0
    # compute mouth aspect ratio
    mar = Y / X
    return mar

def processDrowy(leftEye,rightEye,mouth,drowsyPredictDict,drowsyParamsDict):
    # Text values
    drowsyText = "\nHi, I can see drowsiness in you \nPlease follow below : \n1)Drink water regularly\n2)Take break and walk around at regular intervals\n" \
                 "3)Coffe intake can help if too sleepy\n"
    partialDrowsyText = "\nHi, Some signs of drowsiness is observed,\n1)Drink water regularly\n2)Do some desk exercises"

    #Threshold values
    EYE_AR_THRESH = 0.25
    EYE_AR_CONSEC_FRAMES = 48
    MOU_AR_THRESH = 0.80

    #Predicted params
    lStart = drowsyPredictDict["lStart"]
    lEnd = drowsyPredictDict["lEnd"]
    rStart = drowsyPredictDict["rStart"]
    rEnd = drowsyPredictDict["rEnd"]
    mStart = drowsyPredictDict["mStart"]
    mEnd = drowsyPredictDict["mEnd"]
    print("After Predicted params")
    #Drowsy Params
    COUNTER = drowsyParamsDict["COUNTER"]
    yawnStatus = drowsyParamsDict["yawnStatus"]
    yawns = drowsyParamsDict["yawns"]
    prev_yawn_status = drowsyParamsDict["prev_yawn_status"]

    print("After Drowsy params")

    # extract the left and right eye coordinates, then use the
    # coordinates to compute the eye aspect ratio for both eyes
    # shape = faces[0]
    # leftEye = shape[lStart:lEnd]
    # print(leftEye)
    # rightEye = shape[rStart:rEnd]
    # mouth = shape[mStart:mEnd]
    #leftEye = np.fromstring((leftEye), dtype=int).reshape(6,2)
    #leftEye = cPickle.loads(s)
    leftEAR = eye_aspect_ratio(leftEye)
    rightEAR = eye_aspect_ratio(rightEye)
    mouEAR = mouth_aspect_ratio(mouth)
    formatted_float = "{:.2f}".format(mouEAR)
    # average the eye aspect ratio together for both eyes
    ear = (leftEAR + rightEAR) / 2.0
    # check to see if the eye aspect ratio is below the blink
    # threshold, and if so, increment the blink frame counter
    if ear < EYE_AR_THRESH:
        COUNTER += 1
    # otherwise, the eye aspect ratio is not below the blink
    # threshold, so reset the counter and alarm
    else:
        COUNTER = 0

    # yawning detections
    if mouEAR > MOU_AR_THRESH:
        yawnStatus = True
        output_text = "Yawn Count: " + str(yawns + 1)
    else:
        yawnStatus = False

    if prev_yawn_status == True and yawnStatus == False:
        yawns += 1

    drowsyParamsDict["COUNTER"] = COUNTER
    drowsyParamsDict["yawnStatus"] = yawnStatus
    drowsyParamsDict["yawns"] = yawns
    drowsyParamsDict["prev_yawn_status"] = prev_yawn_status
    return drowsyParamsDict

def notifyDrowsyWeb(drowsyRuleParamsDict,drowsyCNNParamsDict):
    NotDrowsyText = "No drowsiness observed"
    drowsyText = "\nHi, I can see drowsiness in you \nPlease follow below : \n1)Drink water regularly\n2)Take break and walk around at regular intervals\n" \
                 "3)Coffe intake can help if too sleepy\n"
    partialDrowsyText = "\nHi, Some signs of drowsiness is observed,\n1)Drink water regularly\n2)Do some desk exercises"
    partialSleepCounter = drowsyCNNParamsDict["partialSleepCounter"]
    Counter = drowsyRuleParamsDict["COUNTER"]
    yawn = drowsyRuleParamsDict["yawn"]

    if Counter > 4:
        notifytext = drowsyText
    elif yawn > 2:
        notifytext =drowsyText
    elif partialSleepCounter > 4:
        notifytext = partialDrowsyText
    else :
        notifytext = NotDrowsyText

    notify(notifytext)
#


def detect(ear,mouEAR,drowsyParamsDict,text):
    COUNTER = drowsyParamsDict["COUNTER"]
    yawn = drowsyParamsDict["yawn"]
    prev_yawn_status =drowsyParamsDict["prev_yawn_status"]
    # Threshold values
    EYE_AR_THRESH = 0.23
    EYE_AR_CONSEC_FRAMES = 48
    MOU_AR_THRESH = 0.70

    # check to see if the eye aspect ratio is below the blink
    # threshold, and if so, increment the blink frame counter
    if ear < EYE_AR_THRESH:
        text = "Algo2 : Drowsy"
        COUNTER += 1
    # otherwise, the eye aspect ratio is not below the blink
    # threshold, so reset the counter and alarm
    else:
        COUNTER = 0

    # yawning detections
    if mouEAR > MOU_AR_THRESH:
        text = "Algo2  :Yawning"
        yawnStatus = True
        output_text = "Yawn Count: " + str(yawn + 1)
    else:
        yawnStatus = False

    if prev_yawn_status == True and yawnStatus == False:
        yawn += 1

   # prev_yawn_status = yawnStatus

    drowsyParamsDict["COUNTER"] = COUNTER
    drowsyParamsDict["yawn"] = yawn
    drowsyParamsDict["prev_yawn_status"] = prev_yawn_status

    return text,drowsyParamsDict
