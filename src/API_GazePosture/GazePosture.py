from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from src.gaze.gazeUtility.gaze_tracking import GazeTracking
import numpy as np
from src.posture.postureUtility.utility import padRightDownCorner
from scipy.ndimage.filters import gaussian_filter
from src.posture.config.config_reader import config_reader
from model.model import get_testing_model
import cv2
import os
import uvicorn
import dlib
from fastapi import Body, File
from PIL import Image
from io import BytesIO

##Loading posture model
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
modelpos = get_testing_model()
print(THIS_FOLDER)
modelpos.load_weights('../../model/model.h5' )

##Loading DrowsyRule
predictor_path = '../../model/shape_predictor_68_face_landmarks.dat'
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)


colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0],
          [0, 255, 0], \
          [0, 255, 85], [0, 255, 170], [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255],
          [85, 0, 255], \
          [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]]

def process(input_image, params, model_params,model):
    ''' Start of finding the Key points of full body using Open Pose.'''
    #print("inside process")
    oriImg = input_image  # B,G,R order
    print(oriImg.dtype)
    print(oriImg.ndim)
    #print("Image read")
    multiplier = [x * model_params['boxsize'] / oriImg.shape[0] for x in params['scale_search']]
    heatmap_avg = np.zeros((oriImg.shape[0], oriImg.shape[1], 19))
    paf_avg = np.zeros((oriImg.shape[0], oriImg.shape[1], 38))
    #print("Image heatmap")
    for m in range(1):
        scale = multiplier[m]
        #print(scale)
        #img = cv2.imread(oriImg,cv2.IMREAD_COLOR)
        #print(img.size)
        #if img is not None and
        imageToTest = cv2.resize(oriImg, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        imageToTest_padded, pad = padRightDownCorner(imageToTest, model_params['stride'],
                                                          model_params['padValue'])
        input_img = np.transpose(np.float32(imageToTest_padded[:, :, :, np.newaxis]),
                                 (3, 0, 1, 2))  # required shape (1, width, height, channels)
        output_blobs = model.predict(input_img)
        heatmap = np.squeeze(output_blobs[1])  # output 1 is heatmaps
        heatmap = cv2.resize(heatmap, (0, 0), fx=model_params['stride'], fy=model_params['stride'],
                             interpolation=cv2.INTER_CUBIC)
        heatmap = heatmap[:imageToTest_padded.shape[0] - pad[2], :imageToTest_padded.shape[1] - pad[3],
                  :]
        heatmap = cv2.resize(heatmap, (oriImg.shape[1], oriImg.shape[0]), interpolation=cv2.INTER_CUBIC)
        paf = np.squeeze(output_blobs[0])  # output 0 is PAFs
        paf = cv2.resize(paf, (0, 0), fx=model_params['stride'], fy=model_params['stride'],
                         interpolation=cv2.INTER_CUBIC)
        paf = paf[:imageToTest_padded.shape[0] - pad[2], :imageToTest_padded.shape[1] - pad[3], :]
        paf = cv2.resize(paf, (oriImg.shape[1], oriImg.shape[0]), interpolation=cv2.INTER_CUBIC)
        heatmap_avg = heatmap_avg + heatmap / len(multiplier)
        try :
            paf_avg = paf_avg + paf / len(multiplier)
        except Exception as e:
            print("Exception on a frame")

    all_peaks = []  # To store all the key points which a re detected.
    peak_counter = 0
    #print("process 1")
    canvas = input_image  # B,G,R order
    for part in range(18):
        map_ori = heatmap_avg[:, :, part]
        map = gaussian_filter(map_ori, sigma=3)
        map_left = np.zeros(map.shape)
        map_left[1:, :] = map[:-1, :]
        map_right = np.zeros(map.shape)
        map_right[:-1, :] = map[1:, :]
        map_up = np.zeros(map.shape)
        map_up[:, 1:] = map[:, :-1]
        map_down = np.zeros(map.shape)
        map_down[:, :-1] = map[:, 1:]
        peaks_binary = np.logical_and.reduce(
            (map >= map_left, map >= map_right, map >= map_up, map >= map_down, map > params['thre1']))
        peaks = list(zip(np.nonzero(peaks_binary)[1], np.nonzero(peaks_binary)[0]))  # note reverse
        peaks_with_score = [x + (map_ori[x[1], x[0]],) for x in peaks]
        id = range(peak_counter, peak_counter + len(peaks))
        peaks_with_score_and_id = [peaks_with_score[i] + (id[i],) for i in range(len(id))]

        all_peaks.append(peaks_with_score_and_id)
        peak_counter += len(peaks)

    for i in range(18): #drawing all the detected key points.
        for j in range(len(all_peaks[i])):
            cv2.circle(canvas, all_peaks[i][j][0:2], 4, colors[i], thickness=-1)
    #print("process 2")
    return canvas,all_peaks




app = FastAPI()
# Gaze FastAPI
@app.post("/gaze/", response_class=JSONResponse)
async def gaze(file1: bytes = File(...)):
    frame = np.array(Image.open(BytesIO(file1)))
    #json_param = await request.json()
    #print("inside gaze")
    #nmpyarr = np.array(json_param['arr'])
    #print(nmpyarr.shape)
    #frame = np.uint8(nmpyarr)
    # print(nmpyarray)
    gaze = GazeTracking(predictor,detector)
    gaze.refresh(frame)
    frame = gaze.annotated_frame()
    text = ""

    # if gaze.is_blinking():
    #    text = "Blinking"
    if gaze.is_right():
        text = "Looking right"
    elif gaze.is_left():
        text = "Looking left"
    elif gaze.is_center():
        text = "Looking center"

    print(text)
    #    cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)

    left_pupil = gaze.pupil_left_coords()
    right_pupil = gaze.pupil_right_coords()
    print(left_pupil)
    print(right_pupil)

    return {'text': text}


# Posture FastAPI
@app.post("/posture/", response_class=JSONResponse)
async def posture(file: bytes = File(...)):
    rightEar = None
    leftEar = None
    rightShoulder = None
    leftShoulder = None
    nose = None
    neckJoint = None
    rightKnee = None
    leftKnee = None
    rightFoot = None
    leftFoot = None
    leftHand = None
    rightHand = None

    nmpyarray = np.array(Image.open(BytesIO(file)))
    #nmpyarray = np.uint8(image)
    #json_param = await request.json()
    #print("inside posture")
    #nmpyarr = np.array(json_param['arr'])
    #print(nmpyarr.shape)
    params, model_params = config_reader()
    # print(nmpyarr)
    #nmpyarray = np.uint8(nmpyarr)
    canvas, all_peaks = process(nmpyarray, params, model_params, modelpos)

    try:
        if (all_peaks[16][0][0:2]):
            rightEar = str(all_peaks[16][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[17][0][0:2]):
            leftEar = str(all_peaks[17][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[2][0][0:2]):
            rightShoulder = str(all_peaks[2][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[5][0][0:2]):
            leftShoulder = str(all_peaks[5][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[0][0][0:2]):
            nose = str(all_peaks[0][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[1][0][0:2]):
            neckJoint = str(all_peaks[1][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[9][0][0:2]):
            rightKnee = str(all_peaks[9][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[10][0][0:2]):
            rightFoot = str(all_peaks[10][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[12][0][0:2]):
            leftKnee = str(all_peaks[12][0][0:2])
    except Exception as e:
        pass

    try:
        if (all_peaks[13][0][0:2]):
            leftFoot = str(all_peaks[13][0][0:2])
    except Exception as e:
        pass
    try:
        if (all_peaks[7][0][0:2]):
            leftHand = str(all_peaks[7][0][0:2])
    except Exception as e:
        pass
    try:
        if (all_peaks[4][0][0:2]):
            rightHand = str(all_peaks[4][0][0:2])
    except Exception as e:
        pass

    print(rightEar)
    print(leftEar)
    print(rightShoulder)
    print(leftShoulder)
    print(nose)
    print(neckJoint)

    return {'rightEar': rightEar, 'leftEar': leftEar, 'rightShoulder': rightShoulder, 'leftShoulder': leftShoulder,
            'nose': nose, 'neckJoint': neckJoint, 'leftKnee': leftKnee, 'leftFoot': leftFoot, 'rightKnee': rightKnee,
            'rightFoot': rightFoot, 'leftHand': leftHand, 'rightHand': rightHand}


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8090)