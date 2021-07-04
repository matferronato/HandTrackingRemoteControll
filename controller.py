from handDetector import HandDetector
import cv2
import math
import numpy as np

handDetector = HandDetector(min_detection_confidence=0.7)
webcamFeed = cv2.VideoCapture(0)
cv2.namedWindow('win1')

expected = 80
offset = 20
offsetButtonY = 100
offsetButtonX = 200

class RemoteControll():
    def __init__(self, offsetButtonX = 200, offsetButtonY = 100, expected=80, offset=20, timer=50, volumeUpMin = 20, volumeUpMax = 90, volumeDownMin = 20, volumeDownMax = 90):
        self.counter = 0
        self.expected = expected
        self.offset = offset
        self.timer = timer
        #Text
        self.textDelay = 33
        self.textCounter = 0
        self.textDots = 3
        self.textString = ""
        #Calibrated
        self.calibratedCenterX = 0
        self.calibratedCenterY = 0
        self.calibratedMaxRadius = 0
        #Thresholds
        self.volumeDownMin = volumeDownMin
        self.volumeDownMax = volumeDownMax
        self.volumeUpMin = volumeUpMin
        self.volumeUpMax = volumeUpMax
        self.downPressed = False
        self.upPressed = False
        #Actions
        self.trigger = False
        self.runningText = ""
        self.runningDelay = 20
        self.runningCounter = 0
        #States
        self.remoteControllMode = False
        self.state = "Calibrate"
        self.transitions = {"Calibrate" : "Running"}
        self.draw = False

    def checkAction(self):
        if self.state == "Calibrate":
            self.calibrationRoutine()
            i = 0
        elif self.state == "Running":
            self.runningRoutine()
    
    def runningRoutine(self):
        triangle, dummy = self.getTrianglePoints()
        lengthVolumeUp, lengthVolumeDown = self.getVolumeDistances(triangle)
        self.senseButtonPressed(lengthVolumeUp, lengthVolumeDown)
        if(self.draw):
            self.drawnControllLines(triangle)
        self.runAction()
            
    def runAction(self):
        if(self.trigger):
            self.runningCounter += 1
            cv2.putText(image, self.runningText, (250,40), cv2.FONT_HERSHEY_COMPLEX, 1, (0,0,0), 2)
            if self.runningCounter > self.runningDelay:
                self.trigger = False
                self.runningCounter = 0
            
    def senseButtonPressed(self, lengthVolumeUp, lengthVolumeDown):
        if(self.upPressed):
            if lengthVolumeUp > self.volumeUpMax:
                self.upPressed = False
        else:
            if lengthVolumeUp < self.volumeUpMin:
                self.upPressed = True
                self.pressButton("apertou volume +")
        if(self.downPressed):
            if lengthVolumeDown > self.volumeDownMax:
                self.downPressed = False
        else:
            if lengthVolumeDown < self.volumeDownMax:
                self.downPressed = True
                self.pressButton("apertou volume -")
                

    def pressButton(self, action):
        self.runningText = action
        self.trigger = True


    def getVolumeDistances(self, triangle):
        volumeUp = triangle[0]
        volumeDown = triangle[1]
        endPoint = triangle[2]        
        lengthVolumeUp = math.hypot(endPoint[0]-volumeUp[0], endPoint[1]-volumeUp[1])
        lengthVolumeDown = math.hypot(endPoint[0]-volumeDown[0], endPoint[1]-volumeDown[1])
        return lengthVolumeUp, lengthVolumeDown

    def drawnControllLines(self, triangle):
        cv2.putText(image, "Calibrated!", (30,40), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
        volumeUp = triangle[0]
        volumeDown = triangle[1]
        endPoint = triangle[2]
        cv2.line(image, endPoint, volumeUp, (0, 255, 255), 3)
        cv2.line(image, endPoint, volumeDown, (255, 255, 0), 3)

 
    def calibrationRoutine(self):
        centerX, centerY, maxRadius = self.getCenter()
        triangle, length = self.getTrianglePoints()
        self.calibrate(length)
        #if(self.draw):
        self.drawnCalibration(centerX, centerY, maxRadius)
        self.changeStateCalibrate()

    def changeStateCalibrate(self):
        if self.counter == self.timer:
            self.state = self.transitions[self.state]
            self.findCalibratedCenter()

    def findCalibratedCenter(self):
        self.calibratedCenterY =  (handLandmarks[0][2] + handLandmarks[12][2]) / 2
        self.calibratedCenterX =  (handLandmarks[4][1] + handLandmarks[20][1]) / 2
        self.calibratedMaxRadius = (handLandmarks[0][2] - handLandmarks[12][2])/2        

    def getCenter(self):
        centerY =  (handLandmarks[0][2] + handLandmarks[12][2]) / 2
        centerX =  (handLandmarks[4][1] + handLandmarks[20][1]) / 2
        maxRadius = (handLandmarks[0][2] - handLandmarks[12][2])/2
        maxRadius = maxRadius if maxRadius > 0 else 0
        return centerX, centerY, maxRadius

    def getTrianglePoints(self):
        x1, y1 = handLandmarks[8][1], handLandmarks[8][2]
        x2, y2 = handLandmarks[12][1], handLandmarks[12][2]    
        x3, y3 = handLandmarks[4][1], handLandmarks[4][2]    
        p0 = (x1, y1)
        p1 = (x2, y2)
        p2 = (x3, y3)
        triangle = [p0, p1, p2]     
        length = math.hypot(p1[0]-p0[0], p1[1]-p0[1])
        return triangle, length
 
    def getExtraDots(self):
        self.textCounter  = self.textCounter+1
        if self.textCounter > self.textDelay:
            self.textCounter = 0
            if len(self.textString) > self.textDots-1:
                self.textString = ""
            else:
                self.textString += "."
 
    def calibrate(self, length):
        self.getExtraDots()
        cv2.putText(image, "Calibrando"+self.textString, (30,40), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 2)
        if(length < (self.expected+self.offset) and length > (self.expected-self.offset)):
            self.counter = self.timer if self.counter > self.timer else (self.counter + 1)
        else:
            self.counter = 0
 
    def drawnCalibration(self, centerX, centerY, maxRadius):
        currentSize = int(maxRadius*(self.counter/self.timer))
        if currentSize < maxRadius-1:
            color = (0, 0, 255)
            cv2.circle(image, (int(centerX), int(centerY)), currentSize, (255, 0, 255), int(currentSize/10))
        else:
            color = (0, 255, 0)
        cv2.circle(image, (int(centerX), int(centerY)), int(maxRadius), color, int(maxRadius/10))
         
        



rc = RemoteControll()
while True:
    status, image = webcamFeed.read()
    handLandmarks = handDetector.findHandLandMarks(image=image, draw=False)
    if(len(handLandmarks) != 0):    
        rc.checkAction()

        

    cv2.waitKey(1)    
    cv2.imshow('win1', image)

