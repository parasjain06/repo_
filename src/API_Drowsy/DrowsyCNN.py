# importing the necessary packages
from scipy.spatial import distance as dist
from imutils import face_utils
import numpy as np
import dlib
import cv2
import os
import uvicorn
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from fastapi import Body, File
from PIL import Image
from io import BytesIO
from keras.models import load_model

# CurrentFolder path
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

##Loading DrowsyRule
predictor_path ='../../model/shape_predictor_68_face_landmarks.dat'
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

##Loading DrowsyCNN models
model = load_model('../../model/DrowsyCNN_model.h5')

##Initialise params
COUNTER = 0
yawn = 0
prev_yawn_status = False
yawnStatus = False


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


def crop_eye(img, eye_points):
    IMG_SIZE = (34, 26)
    x1, y1 = np.amin(eye_points, axis=0)
    x2, y2 = np.amax(eye_points, axis=0)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

    w = (x2 - x1) * 1.2
    h = w * IMG_SIZE[1] / IMG_SIZE[0]

    margin_x, margin_y = w / 2, h / 2

    min_x, min_y = int(cx - margin_x), int(cy - margin_y)
    max_x, max_y = int(cx + margin_x), int(cy + margin_y)

    eye_rect = np.rint([min_x, min_y, max_x, max_y]).astype(np.int)

    eye_img = img[eye_rect[1]:eye_rect[3], eye_rect[0]:eye_rect[2]]

    return eye_img, eye_rect


app = FastAPI()


@app.post("/drow/", response_class=JSONResponse)
async def drowRule(file: bytes = File(...)):
    # convert file to image
    image = np.array(Image.open(BytesIO(file)))
    # Convert PIL image to cv2 image
    imcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(imcv, cv2.COLOR_BGR2GRAY)
    text = ""

    # define constants for aspect ratios
    EYE_AR_THRESH = 0.25
    EYE_AR_CONSEC_FRAMES = 48
    MOU_AR_THRESH = 0.80

    # grab the indexes of the facial landmarks for the left and right eye
    # also for the mouth
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    (mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

    # detect faces in the grayscale frame
    rects = detector(gray, 0)
    faces = []
    # loop over the face detections
    for rect in rects:
        # determine the facial landmarks for the face region, then
        # convert the facial landmark (x, y)-coordinates to a NumPy
        # array
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        faces.append(shape)

    shape = faces[0]

    # Predicted params
    leftEye = shape[lStart:lEnd]
    rightEye = shape[rStart:rEnd]
    mouth = shape[mStart:mEnd]

    # Aspect ratios
    leftEAR = eye_aspect_ratio(leftEye)
    rightEAR = eye_aspect_ratio(rightEye)
    mouEAR = mouth_aspect_ratio(mouth)
    ear = (leftEAR + rightEAR) / 2.0

    return {'ear': ear, 'mouEAR': mouEAR}


# DrowsyCNN FastAPI
@app.post("/drowCNN/", response_class=JSONResponse)
async def drowCNN(file: bytes = File(...)):
    # convert file to image
    image = np.array(Image.open(BytesIO(file)))
    # Convert PIL image to cv2 image
    imcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    IMG_SIZE = (34, 26)
    img_ori = cv2.resize(imcv, dsize=(0, 0), fx=0.5, fy=0.5)
    img = img_ori.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    print("inside drowCNN")
    for face in faces:
        shapes = predictor(gray, face)
        shapes = face_utils.shape_to_np(shapes)

        eye_img_l, eye_rect_l = crop_eye(gray, eye_points=shapes[36:42])
        eye_img_r, eye_rect_r = crop_eye(gray, eye_points=shapes[42:48])
        print("inside for")
        eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE)
        eye_img_r = cv2.resize(eye_img_r, dsize=IMG_SIZE)
        eye_img_r = cv2.flip(eye_img_r, flipCode=1)

        eye_input_l = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
        eye_input_r = eye_img_r.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
        print("inside for 2")
        pred_l = model.predict(eye_input_l)
        pred_r = model.predict(eye_input_r)
    print("outside for")
    return {'pred_l': float(pred_l[0][0]), 'pred_r': float(pred_r[0][0])}



if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8080)
