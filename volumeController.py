from handDetector import HandDetector
import cv2
import math
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import slowclap as sc




handDetector = HandDetector(min_detection_confidence=0.7)
webcamFeed = cv2.VideoCapture(0)
feed = sc.MicrophoneFeed()


devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

resetState = 12


while True:
    status, image = webcamFeed.read()
    handLandmarks = handDetector.findHandLandMarks(image=image, draw=True)

    #if(len(handLandmarks) != 0):
    #    x1, y1 = handLandmarks[4][1], handLandmarks[4][2]
    #    x2, y2 = handLandmarks[8][1], handLandmarks[8][2]
    #    length = math.hypot(x2-x1, y2-y1)
    #    print(length)

    #    cv2.circle(image, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
    #    cv2.circle(image, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
    #    cv2.line(image, (x1, y1), (x2, y2), (255, 0, 255), 3)

    if(len(handLandmarks) != 0):
        centerY =  (handLandmarks[0][2] + handLandmarks[12][2]) / 2
        centerX =  (handLandmarks[4][1] + handLandmarks[20][1]) / 2
        size = (handLandmarks[0][2] - handLandmarks[12][2])/2
        size = size if size > 0 else 0
        cv2.circle(image, (int(centerX), int(centerY)), int(size), (255, 0, 255), int(size/10))
        #print(int(size))
    #detector = sc.AmplitudeDetector(feed, threshold=1700000)    
    #print(detector)
  
    cv2.imshow("Volume", image)
    cv2.waitKey(1)