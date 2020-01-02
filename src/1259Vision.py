import cscore
import networktables as nt 

import cv2 
import time
import numpy as np 
import math

#time.sleep(15)

cs = cscore.CameraServer.getInstance()
cs.enableLogging()

try:
    nt.NetworkTables.initialize(server="10.12.59.2")
    print("NetworkTable found!")
    SmartDashboard = nt.NetworkTables.getTable("SmartDashboard")
except:
    print("No network table found continuing with the rest of the code")

Back = cs.startAutomaticCapture(name = "BackCamera", path = "/dev/v4l/by-path/platform-3f980000.usb-usb-0:1.2:1.0-video-index0")
Back.setResolution(640, 480)

Front = cs.startAutomaticCapture(name = "FrontCamera", path = "/dev/v4l/by-path/platform-3f980000.usb-usb-0:1.1:1.0-video-index0")
Front.setResolution(640, 480)

server = cs.addSwitchedCamera("SwitchedCamera")

print("Starting code stuff")

#Camera width and height will essentially equal the resolution that has been hardcoded
camWid = 640
camHgt = 480

#Variables that will be needed to do distance calculations - FIRST Gen. Variables 
DefaultImageHeight = 240
DefaultBallHeightPixel = 121.243 
DefaultPixelsPerInch = 17.32  
CalibrationDistanceInch = 12 

MaxPossibleAngle = 60 # MEASURED IN DEGREES 
MaxPossibleDistance = 120 # MEASURED IN INCHES

#Variables needed to distance calculations - SECOND Gen. Variables
MaxPossibleRadius = (DefaultImageHeight / 2) #MEASURED IN INCHES 
MinPossibleRadius = 0   #WE NEED TO CALCULATE THIS

#Maximum and minimum possible HSV values to detect the ball
minHSVBall = np.array([18, 100, 100])
maxHSVBall = np.array([40, 255, 255])

#X and Y coordinate of the center of the image
imageCenterX = camWid / 2
imageCenterY = camHgt / 2

#Scaling the image
img = np.zeros(shape=(640, 480, 3), dtype=np.uint8)
scale_percent = 50 # percent of original size
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)
dim = (width, height)

runCalculation = True

visionCounter = 0


def Vision():

    global img

    try:
    	cameraFeed = SmartDashboard.getNumber("cameraFeed", 0)
    except:
        cameraFeed = 0
        print("Couldn't get cameraFeed value because no network table was found\nDefault to 0")

    if cameraFeed == 0:
        
        print("Using front camera")
        visionCounter += 1

        try:
            SmartDashboard.putString("VisionCodeSelected", "0")
        except:
            print("Cannot put string because network table was not found")
       
        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)

        cvSink = cscore.CvSink("FrontSink")
        cvSink.setSource(Front)

        cvSource = cscore.CvSource("FrontCVSource", cscore.VideoMode.PixelFormat.kMJPEG, 640, 480, 30)
                
        time, img = cvSink.grabFrame(img)

        img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

        #Convert the RGB image to HSV
        imHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        #Find pixels in the blurred image that fit in range and turn them white and others black                                          
        InRange = cv2.inRange(imHSV, minHSVBall, maxHSVBall)

        InRange = cv2.GaussianBlur(InRange, (5, 5), cv2.BORDER_DEFAULT)

        circles = cv2.HoughCircles(InRange, cv2.HOUGH_GRADIENT, 1, int(height/10), 100, 25, 5, int(height/2))
        circles = np.uint16(np.around(circles))

        biggest_radius = 0;
        for i in circles[0,:]:
            try:

                if (biggest_radius < i[2]):
                    biggest_radius = i[2]
                    biggestX = i[0]
                    biggestY = i[1]
            except IndexError:
                print("No ball found")
                runCalculation = False
                continue
        
        if runCalculation:
            
            ActualBallHeightPixel = DefaultBallHeightPixel / (DefaultImageHeight / height)
            ActualPixelsPerInch = DefaultPixelsPerInch / (DefaultImageHeight / height)

            DirectDistanceBallInch = ((ActualBallHeightPixel / (2 * biggest_radius)) * CalibrationDistanceInch)
            XDisaplacementPixel = biggestX - (width / 2)
            YDisplacmentPixel = biggestY - (height / 2)
            YAngle = math.atan(YDisplacmentPixel/(ActualPixelsPerInch * DefaultPixelsPerInch)) #MEASURED IN RADIANS
            XAngle = math.atan(XDisplacement/(ActualPixelsPerInch * DefaultPixelsPerInch)) * (180/np.pi) #MEASURED IN DEGREES

            ZDistance = DirectDistanceBallInch * math.cos(YAngle) #ROBOT DISTANCE TO BALL
            

            try:
                SmartDashboard.putNumber("VisionCounter", visionCounter) 
                SmartDashboard.putNumber("ZDistance", ZDistance)
                SmartDashboard.putNumber("DirectDistance", XAngle)

            draw = cv2.circle(draw, (biggestX, biggestY), biggest_radius, (255, 0, 0), 5)

        else:
            print("could not find any object so decided to skip calculations as well")


    if cameraFeed == 1:

        print("Using back camera")
        visionCounter += 1

        try:
            SmartDashboard.putNumber("VisionCounter", visionCounter)
            SmartDashboard.putString("VisionCodeSelected", "1")
        except:
            print("Cannot put string because network table was not found")

        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)


while True:
	Vision()

    
