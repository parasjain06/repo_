import math
from src.Notifier.Notifier import notify

def convertTupple(x):
    x = res = tuple(int(num) for num in x.replace('(', '').replace(')', '').replace('...', '').split(', '))
    return x

# Calculate distance between two points A(x,y), B(x,y)
def calcDistance(a, b):  # calculate distance between two points.
    a = convertTupple(a)
    b = convertTupple(b)
    try:
        x1, y1 = a
        x2, y2 = b
        return math.hypot(x2 - x1, y2 - y1)
    except Exception as e:
        print("unable to calculate distance")

# Calculate angle between 3 points() A(x,y), B(x,y), C(x,y)
def angle3pt(a, b, c):
    a = convertTupple(a)
    b = convertTupple(b)
    c = convertTupple(c)
    """Counterclockwise angle in degrees by turning from a to c around b
        Returns a float between 0.0 and 360.0"""
    ang = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
    return ang + 360 if ang < 0 else ang

# Analyse Posture params
def processPosture(posture_detect_json, postureParamsDict, displayText):
    # parse dictionary of posture:
    print("inside processPosture")
    wrongFrameCounted =False
    wrongPosFrame = postureParamsDict["wrongPosFrame"]
    shoulderNotVisible = postureParamsDict["shoulderNotVisible"]
    neckStrainCounter = postureParamsDict["neckStrainCounter"]
    handSupportCounter = postureParamsDict["handSupportCounter"]

    #Extract all joints
    rightEar =posture_detect_json["rightEar"]
    leftEar = posture_detect_json["leftEar"]
    rightShoulder = posture_detect_json["rightShoulder"]
    leftShoulder = posture_detect_json["leftShoulder"]
    nose = posture_detect_json["nose"]
    neckJoint = posture_detect_json["neckJoint"]
    leftKnee = posture_detect_json["leftKnee"]
    leftFoot = posture_detect_json["leftFoot"]
    rightKnee = posture_detect_json["rightKnee"]
    rightFoot = posture_detect_json["rightFoot"]
    rightHand = posture_detect_json["rightHand"]
    leftHand = posture_detect_json["leftHand"]
    print(rightShoulder)
    print(leftShoulder)

    # Check if right shoulder and left shoulder exists,else Incorrect posture
    try :
        if not rightShoulder and not leftShoulder and not nose and not neckJoint:
            displayText =  "Algo1 : Are you there? I cant see you!"
        elif rightShoulder and leftShoulder:
            print("Right and left shoulder are visible")
        else:
            displayText =  "Algo1 : Your shoulders are not visible, please sit straight!"
    except IndexError:
        print("Index error shoulder not visible")
        shoulderNotVisible = shoulderNotVisible + 1
        if wrongFrameCounted ==False:
            wrongPosFrame = wrongPosFrame + 1
            wrongFrameCounted= True


    # Check if legs or knees are visible , If visible then Posture is incorrect
    try:
        if leftKnee or leftFoot or rightKnee or rightFoot:
            if wrongFrameCounted == False:
                wrongPosFrame = wrongPosFrame + 1
                wrongFrameCounted = True
            print("Leg detected")
            displayText= "Algo1 : leg detected incorrect posture!"
    except IndexError:
            pass

    # Check if the neck is bend too much (up/down/left/right)
    try:
        # Check Neck is bend left/right
        if (rightEar and leftEar and rightShoulder and leftShoulder and nose):

            rightdistance = calcDistance(rightEar, rightShoulder)
            # print("distance between right ear and right shoulder is %d" % rightdistance)
            leftdistance = calcDistance(leftEar, leftShoulder)
            #print("distance between left ear and left shoulder is %d" % leftdistance)

            # Neck Bend right
            if ((leftdistance > rightdistance) and (leftdistance - rightdistance) > 50):
                neckStrainCounter = neckStrainCounter + 1
                print("please dont bend your neck to the right")
                displayText =  "Algo1 : please dont bend your neck to the right!"
                if wrongFrameCounted == False:
                    wrongPosFrame = wrongPosFrame + 1
                    wrongFrameCounted = True

            # Neck Bend left
            elif ((rightdistance > leftdistance) and (rightdistance - leftdistance) > 50):
                neckStrainCounter = neckStrainCounter + 1
                print("please dont bend your neck to the left")
                displayText =  "Algo1 : please dont bend your neck to the left!"
                if wrongFrameCounted == False:
                    wrongPosFrame = wrongPosFrame + 1
                    wrongFrameCounted = True
            # Neck too up or Down
            if (angle3pt(leftEar, nose, rightEar) < 145 or angle3pt(leftEar, nose, rightEar) > 215):
                neckStrainCounter = neckStrainCounter + 1
                print("please keep ur head straight it is either too up or too down")
                displayText =  "Algo1 : keep ur head straight: It is either too up or too down!"
                if wrongFrameCounted == False:
                    wrongPosFrame = wrongPosFrame + 1
                    wrongFrameCounted = True
            # Check Hand support to neck
            # Left Hand
            if (leftHand):
                distanceNeckJointLeftHand = calcDistance(neckJoint, leftHand)
                print("distance is %s" % distanceNeckJointLeftHand)
                if (distanceNeckJointLeftHand < 80):
                    handSupportCounter = handSupportCounter + 1
                    print("please dont rest ur neck on hand for too long")
                    displayText = "Algo1 : Do not rest ur neck on hand for too long!"
                    if wrongFrameCounted == False:
                        wrongPosFrame = wrongPosFrame + 1
                        wrongFrameCounted = True
            #Right Hand
            elif (rightHand):
                distanceNeckJointRightHand = calcDistance(neckJoint, rightHand)
                if (distanceNeckJointRightHand < 80):
                    handSupportCounter = handSupportCounter + 1
                    print("please dont rest ur neck on hand for too long")
                    displayText =  "Algo1 : Do not rest ur neck on hand for too long!"
                    if wrongFrameCounted == False:
                        wrongPosFrame = wrongPosFrame + 1
                        wrongFrameCounted = True
    except Exception as e:
        pass

    # update dictionary of posture params
    postureParamsDict["wrongPosFrame"] = wrongPosFrame
    postureParamsDict["shoulderNotVisible"] = shoulderNotVisible
    postureParamsDict["neckStrainCounter"] = neckStrainCounter
    postureParamsDict["handSupportCounter"] = handSupportCounter

    return postureParamsDict, displayText

#Assuming:- Average time taken to process one frame is 2 seconds
def calculateMin(frameCount):
    return (frameCount*2)/60


#Notify user
def notifyPosture(postureParamsDict, totalFrames):
    # parse dictionary of posture:
    wrongPosFrame = postureParamsDict["wrongPosFrame"]
    shoulderNotVisible = postureParamsDict["shoulderNotVisible"]
    neckStrainCounter = postureParamsDict["neckStrainCounter"]
    handSupportCounter = postureParamsDict["handSupportCounter"]
    displayText = ""

    # Find averages of all the params
    avg = wrongPosFrame / totalFrames * 100
    avg_neckBends = neckStrainCounter / totalFrames * 100
    avg_HandSupport = handSupportCounter / totalFrames * 100
    avg_shoulderNotVisible = (shoulderNotVisible / totalFrames) * 100
    print("avg_neckBends is %s:" % avg_neckBends)
    print("avg_HandSupport is %s:" % avg_HandSupport)
    print("avg_shldrNtVsble is %s" % avg_shoulderNotVisible)
    print("totalFrames is %s" % totalFrames)
    print("Wrong frames %s " % wrongPosFrame)
    print("val is %s" % avg)


    totalMin = calculateMin(totalFrames)
    wrongMin = calculateMin(wrongPosFrame)
    handSuportMin = calculateMin(handSupportCounter)
    neckStrainMins = calculateMin(neckStrainCounter)

    if avg_shoulderNotVisible > 40:
        webexText = "Hi,\nI cannot see your Shoulders\nPossible scenarios are:- \n 1)You were not sitting in front of " \
                    "laptop\n 2)you are not sitting on table/chair \n " \
                    "3) Please maintain the camera level so that it captures your shoulders also "

    elif avg > 30:
        webexText = "Hi,Your posture is not correct\nPlease make sure to not bend your neck, and Dont put your hand " \
                    "on the face for long time\nFollowing are the consequences\n 1) NeckPain\n 2) Spondilitis\n 3) " \
                    "Face touching can spread virus" \
                    "\nResult :\n1) Total Duration %.2f min \n2) Durations for Incorrect posture: %.2f min\n3) Duration for neck Strain: %.2f min" \
                    "\n4) Duration for HandSupport: %.2f min" % (
                        totalMin, wrongMin,neckStrainMins, handSuportMin)
    else:
        webexText = "Hi,\nLast footage shows ur posture was correct\nPlease be sure to follow below: \n 1) Always use " \
                    "chair and table while working \n 2) Dont touch your face regularly as it may spread virus" \
                    "\n 3) Sit properly else i may loose to capture you \n 4) If you are sitting for long time please " \
                    "take a break \n 5) Please do some desk exercises:  link "
        # # Going to post on webex
    notify(webexText)