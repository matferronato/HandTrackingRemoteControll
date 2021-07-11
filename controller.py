from handDetector import HandDetector
import cv2
import math
import numpy as np
import serial



from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import math

handDetector = HandDetector(min_detection_confidence=0.7)
webcamFeed = cv2.VideoCapture(0)
cv2.namedWindow('win1')
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

class ControllerSerial():
    def __init__(self, defaultPort = "COM9", baudrate = 9600):
        self.thisSerial = serial.Serial(defaultPort, baudrate)
        self.dictCommands = {"volumeUp" : "aa", "volumeDown" : "bb", "confirmation" : "cc", "menu" : "dd", "arrowUp" : "ee", "arrowDown" : "ff", "arrowLeft" : "gg", "arrowRight" : "hh",}

    def writeUart(self, message):
        characteres = self.dictCommands [message]
        characteres = bytes(characteres, 'ascii')
        self.thisSerial.write(characteres)

class RemoteControll():
    def __init__(self, 
        buttonModeThresholdeMin = 30,
        buttonModeThresholdeMax = 50, 
        expected=50, 
        offset=20, 
        timer=50, 
        volumeUpMin = 10, 
        volumeUpMax = 90, 
        volumeDownMin = 20, 
        volumeDownMax = 90,
        menuMin = 10, 
        menuMax = 90,
        confirmationMin = 20, 
        confirmationMax = 90,        
        ):
        self.controller = ControllerSerial()
        self.counter = 0
        self.expected = expected
        self.offset = offset
        self.timer = timer
        self.buttonModeThresholdeMin = buttonModeThresholdeMin        
        self.buttonModeThresholdeMax = buttonModeThresholdeMax        
        self.buttonMode = "Volume"        
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
        self.menuMin = menuMin 
        self.menuMax = menuMax
        self.confirmationMin = confirmationMin 
        self.confirmationMax = confirmationMax 
        self.menuPressed = False
        self.confirmationPressed = False
        self.downPressed = False
        self.upPressed = False
        self.arrowPressed = False
        #Actions
        self.trigger = False
        self.runningText = ""
        self.runningDelay = 12
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
        cv2.putText(image, "Calibrated! "+self.buttonMode, (30,40), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
        triangle, dummy = self.getTrianglePoints()
        lenghtMenu, lenghtConfirmation = self.getMenuDistances()
        print(lenghtMenu, lenghtConfirmation)
        lengthVolumeUp, lengthVolumeDown, lengthInBetween = self.getVolumeDistances(triangle)
        self.checkMode(lengthVolumeUp, lengthVolumeDown, lengthInBetween, lenghtConfirmation)
        if (self.buttonMode == "Volume"):
            self.senseButtonPressed(lengthVolumeUp, lengthVolumeDown, lenghtMenu, lenghtConfirmation)
            if(self.draw):
                self.drawnControllLines(triangle)
        else:
            centerX, centerY, maxRadius = self.findSwipeCenter(triangle)
            cv2.circle(image, (int(self.calibratedCenterX), int(self.calibratedCenterY)), int(self.calibratedMaxRadius),(0,255,0),  int(self.calibratedMaxRadius/10))
            self.senseSwipe(centerX, centerY, maxRadius)
            if(self.draw):
                self.drawnControllCircle(centerX, centerY, maxRadius)
        self.runAction()

    def checkMode(self, lengthVolumeUp, lengthVolumeDown, lengthInBetween, lenghtMenu):
        if (self.buttonMode == "Volume"):
            if lengthInBetween < self.buttonModeThresholdeMin and lengthVolumeUp < self.buttonModeThresholdeMin and lengthVolumeDown < self.buttonModeThresholdeMin and lenghtMenu < self.buttonModeThresholdeMin:
                self.findCalibratedCenter()
                self.buttonMode = "Arrows"
        else:
            if lengthInBetween > self.buttonModeThresholdeMax and lengthVolumeUp > self.buttonModeThresholdeMax and lengthVolumeDown > self.buttonModeThresholdeMax and lenghtMenu > self.buttonModeThresholdeMax:
                self.buttonMode = "Volume"            

    def findSwipeCenter(self, triangle):
        p0 = triangle[0]
        p1 = triangle[1]
        p2 = triangle[2]
        centerX = int((p0[0] + p1[0] + p2[0])/3)
        centerY = int((p0[1] + p1[1] + p2[1])/3)
        maxRadius = max(p0[0]-p1[0],p0[0]-p2[0])
        maxRadius = maxRadius if maxRadius > 0 else 0
        return centerX, centerY, maxRadius
                
    def senseSwipe(self, centerX, centerY, maxRadius):
        if(self.arrowPressed):
            if centerX > self.calibratedCenterX-self.calibratedMaxRadius and centerX < self.calibratedCenterX+self.calibratedMaxRadius:
                if centerY > self.calibratedCenterY-self.calibratedMaxRadius and centerY < self.calibratedCenterY+self.calibratedMaxRadius:
                    self.arrowPressed  = False        
        else:
            if centerX < self.calibratedCenterX-self.calibratedMaxRadius:
                self.pressButton("right arrow ")
                self.controller.writeUart("arrowRight")

                self.arrowPressed  = True
            elif centerX > self.calibratedCenterX+self.calibratedMaxRadius:
                self.pressButton("left arrow ")
                self.controller.writeUart("arrowLeft") 
                self.arrowPressed  = True
            elif centerY < self.calibratedCenterY-self.calibratedMaxRadius:
                self.pressButton("up arrow ")
                self.controller.writeUart("arrowUp")
                self.arrowPressed  = True
            elif centerY > self.calibratedCenterY+self.calibratedMaxRadius:
                self.pressButton("down arrow")
                self.controller.writeUart("arrowDown")
                self.arrowPressed  = True


    def runAction(self):
        if(self.trigger):
            self.runningCounter += 1
            cv2.putText(image, self.runningText, (30,80), cv2.FONT_HERSHEY_COMPLEX, 1, (0,0,0), 2)
            if self.runningCounter > self.runningDelay:
                self.trigger = False
                self.runningCounter = 0
            
    def senseButtonPressed(self, lengthVolumeUp, lengthVolumeDown, lenghtMenu, lenghtConfirmation):
        if(self.upPressed):
            if lengthVolumeUp > self.volumeUpMax:
                self.upPressed = False
        else:
            if lengthVolumeUp < self.volumeUpMin:
                print("up ", lengthVolumeUp, lengthVolumeDown, self.volumeUpMin)
                self.upPressed = True
                self.pressButton("volume +")
                self.controller.writeUart("volumeUp")                
        
        if(self.downPressed):
            if lengthVolumeDown > self.volumeDownMax:
                self.downPressed = False
        else:
            if lengthVolumeDown < self.volumeDownMin:
                print("down ", lengthVolumeUp, lengthVolumeDown, self.volumeDownMin)
                self.downPressed = True
                self.pressButton("volume -")
                self.controller.writeUart("volumeDown") 
        
        if(self.menuPressed):
            if lenghtMenu > self.menuMax:
                self.menuPressed = False
        else:
            if lenghtMenu < self.menuMin:
                self.menuPressed = True
                self.pressButton("Menu")  
                self.controller.writeUart("menu")                
        
        if(self.confirmationPressed):
            if lenghtConfirmation > self.confirmationMax:
                self.confirmationPressed = False
        else:
            if lenghtConfirmation < self.confirmationMin:
                self.confirmationPressed = True
                self.pressButton("Confirm")
                self.controller.writeUart("confirmation")
                
    def pressButton(self, action):
        self.runningText = action
        self.trigger = True
        currentVolumeDb = volume.GetMasterVolumeLevel()
        #if("-" in action):
        #    volume.SetMasterVolumeLevel(currentVolumeDb - 1.0, None)
        #else:
        #    volume.SetMasterVolumeLevel(currentVolumeDb + 1.0, None)
            

    def getMenuDistances(self):
        x1, y1 = handLandmarks[16][1], handLandmarks[16][2]
        x2, y2 = handLandmarks[20][1], handLandmarks[20][2]         
        x3, y3 = handLandmarks[4][1], handLandmarks[4][2]    
        lenghtMenu = math.hypot(x3-x1, y3-y1)
        lenghtConfirmation = math.hypot(x3-x2, y3-y2)
        return lenghtMenu, lenghtConfirmation

    def getVolumeDistances(self, triangle):
        volumeUp = triangle[0]
        volumeDown = triangle[1]
        endPoint = triangle[2]        
        lengthInBetween = math.hypot(volumeDown[0]-volumeUp[0], volumeDown[1]-volumeUp[1])
        lengthVolumeUp = math.hypot(endPoint[0]-volumeUp[0], endPoint[1]-volumeUp[1])
        lengthVolumeDown = math.hypot(endPoint[0]-volumeDown[0], endPoint[1]-volumeDown[1])
        return lengthVolumeUp, lengthVolumeDown, lengthInBetween

    def drawnControllLines(self, triangle):
        volumeUp = triangle[0]
        volumeDown = triangle[1]
        endPoint = triangle[2]
        cv2.line(image, endPoint, volumeUp, (0, 255, 255), 3)
        cv2.line(image, endPoint, volumeDown, (255, 255, 0), 3)
        cv2.line(image, volumeUp, volumeDown, (255, 255, 255), 3)

    def drawnControllCircle(self, centerX, centerY, maxRadius):
        cv2.circle(image, (int(centerX), int(centerY)), int(maxRadius), (255,255,255), cv2.FILLED)
        
 
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
            #self.findCalibratedCenter()

    def findCalibratedCenter(self):
        self.calibratedCenterY =  (handLandmarks[4][2] + handLandmarks[12][2]) / 2
        self.calibratedCenterX =  (handLandmarks[8][1] + handLandmarks[20][1]) / 2
        self.calibratedMaxRadius = ((handLandmarks[0][2] - handLandmarks[12][2])/2)      
        self.calibratedMaxRadius = self.calibratedMaxRadius  if self.calibratedMaxRadius > 0 else 0
        #self.calibratedCenterY =  (handLandmarks[0][2] + handLandmarks[12][2]) / 2
        #self.calibratedCenterX =  (handLandmarks[4][1] + handLandmarks[20][1]) / 2
        #self.calibratedMaxRadius = ((handLandmarks[0][2] - handLandmarks[12][2])/2)        
        #self.calibratedMaxRadius = self.calibratedMaxRadius  if self.calibratedMaxRadius > 0 else 0

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
        cv2.putText(image, "Calibrating"+self.textString, (30,40), cv2.FONT_HERSHEY_COMPLEX, 1, (255,0,0), 2)
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
    handLandmarks = handDetector.findHandLandMarks(image=image, draw=True)
    if(len(handLandmarks) != 0):    
        rc.checkAction()

        
    cv2.waitKey(1)    
    cv2.imshow('win1', image)

