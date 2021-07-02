from handDetector import HandDetector
import cv2
import math
import numpy as np

#import slowclap as sc




handDetector = HandDetector(min_detection_confidence=0.7)
webcamFeed = cv2.VideoCapture(0)
cv2.namedWindow('win1')

expected = 80
offset = 20
offsetButtonY = 100
offsetButtonX = 200

class RemoteControll():
	def __init__(self, offsetButtonX = 200, offsetButtonY = 100):
		self.counter = 0
		self.timer = 100
		self.remoteControllMode = False
		self.centerX = 0
		self.centerY = 0
		self.offsetButtonX = offsetButtonX
		self.offsetButtonY = offsetButtonY

	def getMeasures(self, handMark):
		centerY =  (handLandmarks[0][2] + handLandmarks[12][2]) / 2
		centerX =  (handLandmarks[4][1] + handLandmarks[20][1]) / 2
		x1, y1 = handLandmarks[8][1], handLandmarks[8][2]
		x2, y2 = handLandmarks[12][1], handLandmarks[12][2]	
		x3, y3 = handLandmarks[4][1], handLandmarks[4][2]	
		p0 = (x1, y1)
		p1 = (x2, y2)
		p2 = (x3, y3)
		triangle = [p0, p1, p2]
		size = (handLandmarks[0][2] - handLandmarks[12][2])/2
		size = size if size > 0 else 0
		return centerY, centerX, triangle, size	

	def drawOverlayFigures(self, centerX, centerY, size, triangle):
		lineBegin = triangle[0]
		lineEnd = triangle[1]
		line3 = triangle[2]
		cv2.circle(image, (int(centerX), int(centerY)), int(size), (255, 0, 255), int(size/10))
		cv2.line(image, lineBegin, lineEnd, (255, 0, 0), 3)
		cv2.line(image, lineBegin, line3, (0, 255, 255), 3)
		length = math.hypot(lineEnd[0]-lineBegin[0], lineEnd[1]-lineBegin[1])
		return length			

	def holdStill(self, length, expected, offset):
		print(self.counter)
		if(length < expected+offset and length > expected-offset):
			self.counter += 1
			if (self.counter > self.timer):
				self.findCenter()
				return True
			else:
				return False
		else:
			self.counter = 0
			return False
			
	def switchState(self):
		self.remoteControllMode = not(self.remoteControllMode)
		self.counter = 0

	def findCenter(self):
		self.centerY =  (handLandmarks[0][2] + handLandmarks[12][2]) / 2
		self.centerX =  (handLandmarks[4][1] + handLandmarks[20][1]) / 2

	def drawRCLines(self):
		if(self.remoteControllMode):
			cv2.circle(image, (int(self.centerX), int(self.centerY)), 15, (0, 0, 255), cv2.FILLED)
			cv2.circle(image, (int(self.centerX), int(self.centerY+self.offsetButtonY)), 15, (255, 0, 0), cv2.FILLED)			 
			cv2.circle(image, (int(self.centerX), int(self.centerY-self.offsetButtonY)), 15, (255, 0, 0), cv2.FILLED)			 
			cv2.circle(image, (int(self.centerX+self.offsetButtonX), int(self.centerY)), 15, (255, 0, 0), cv2.FILLED)			 
			cv2.circle(image, (int(self.centerX-self.offsetButtonX), int(self.centerY)), 15, (255, 0, 0), cv2.FILLED)			 

rc = RemoteControll()
while True:
	status, image = webcamFeed.read()
	handLandmarks = handDetector.findHandLandMarks(image=image, draw=True)
	if(len(handLandmarks) != 0):	
		centerY, centerX, triangle, size = rc.getMeasures(handLandmarks)
		length = rc.drawOverlayFigures(centerX, centerY, size, triangle)	
		if(rc.holdStill(length, expected, offset)):
			rc.switchState()
		rc.drawRCLines()
	

	cv2.waitKey(1)	
	cv2.imshow('win1', image)

