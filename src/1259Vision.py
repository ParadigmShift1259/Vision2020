import cscore
import networktables as nt 

import cv2 
import time
import numpy as np 
import math

#time.sleep(15)

cs = cscore.CameraServer.getInstance()

#Exception block for handling network table initialization
try:
    nt.NetworkTables.initialize(server="10.12.59.2")
    print("NetworkTable found!")
    SmartDashboard = nt.NetworkTables.getTable("SmartDashboard")
except:
    print("No network table found continuing with the rest of the code")
    print("")


#Function to set up the back camera
def SetupBackCamera():
    global Back
    Back = cs.startAutomaticCapture(name = "BackCamera", path = "/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0-video-index0")
    Back.setResolution(640, 480)
    print("Setting up back camera")
#Actually set the back camera up
SetupBackCamera()


#Function to set up the front camera
def SetupFrontCamera():
    global Front
    Front = cs.startAutomaticCapture(name = "FrontCamera", path = "/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0-video-index0")
    Front.setResolution(640, 480)
    print("Setting up front camera")
#Actually set the front camera up
SetupFrontCamera()


#Adding cameras to switched camera so we can "Switch"
server = cs.addSwitchedCamera("SwitchedCamera")


#Just me and Jival having some fun 
def FunStuff():
    print("Starting code stuff")
    print("Bleep-boop-bleep")
    print("Contacting Skynet ...")
    print("Contacting Skynet ...")
    print("Ready to terminate Agastya and Jival ...")
    print("ERROR: CURRENT_DATE != 2025 ...")
    print("Hail Skynet ...")
#Do fun stuff
FunStuff()

#Camera width and height will essentially equal the resolution that has been hardcoded
camWid = 640
camHgt = 480

#Variables that will be needed to do distance calculations - FIRST Gen. Variables 
DefaultImageHeight = 240
DefaultBallRadiusInch = 3.5 
CalibrationDistanceInch = 16 
DefaultCameraViewAngle = 60     #Vertical angle for camera
HeightOfCamera = 18.3125
CameraMountingAngleRadians = 28.0 * (np.pi/180)

MaxPossibleAngle = 60 # MEASURED IN DEGREES 
MaxPossibleDistance = 120 # MEASURED IN INCHES

#Variables needed to distance calculations - SECOND Gen. Variables
MaxPossibleRadius = (DefaultImageHeight / 2) #MEASURED IN INCHES 
MinPossibleRadius = 0   #WE NEED TO CALCULATE THIS
DefaultPixelsPerInch = DefaultBallRadiusInch/(math.tan((DefaultCameraViewAngle/2) * (np.pi/180)) * CalibrationDistanceInch) * DefaultImageHeight
DefaultBallHeightPixel = (DefaultImageHeight/2)/(math.tan((DefaultCameraViewAngle/2) * (np.pi/180)) * CalibrationDistanceInch)

#Maximum and minimum possible HSV values to detect the ball
minHSVBall = np.array([20, 100, 55])
maxHSVBall = np.array([45, 255, 255])

#X and Y coordinate of the center of the image
imageCenterX = camWid / 2
imageCenterY = camHgt / 2

#Scaling the image
img = np.zeros(shape=(640, 480, 3), dtype=np.uint8)
scale_percent = 50 # percent of original size
width = int(img.shape[0] * scale_percent / 100)
height = int(img.shape[1] * scale_percent / 100)
dim = (width, height)

runCalculation = True
saveImage = True
imageCounter = 0

def Vision():

    global img
    global imageCounter
    global runCalculation

    imageCounter += 1

    try:
        cameraFeed = SmartDashboard.getNumber("cameraFeed", 0)
    except:
        cameraFeed = 0
        print("Couldn't get cameraFeed value because no network table was found\nDefault to 0")

    if cameraFeed == 0:

        try:
            SmartDashboard.putString("VisionCodeSelected", "0")
        except:
            print("Cannot put string because network table was not found")

        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)

        #cvSink = cscore.CvSink("FrontSink")
        cvSink = cscore.CvSink("cvsink")
        cvSink.setSource(Front)
                
        time0, img = cvSink.grabFrame(img)

        img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

        #Convert the RGB image to HSV
        imHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        #Find pixels in the blurred image that fit in range and turn them white and others black                                          
        InRange = cv2.inRange(imHSV, minHSVBall, maxHSVBall)

        InRange = cv2.GaussianBlur(InRange, (5, 5), cv2.BORDER_DEFAULT)
        if saveImage:
            if(imageCounter % 5 == 0):
                cv2.imwrite("Inrange%d.png" % imageCounter, InRange)

        #circles = cv2.HoughCircles(InRange, cv2.CV_HOUGH_GRADIENT, 2, int(height/10), 150, 50, 10, 60)
        circles = cv2.HoughCircles(InRange, cv2.HOUGH_GRADIENT, 1, int(width/10), param1=180, param2=10, minRadius=5, maxRadius=50)
        circles = np.uint16(np.around(circles))

        global biggest_radius
        global biggestX
        global biggestY
        biggest_radius = 0
        for i in circles[0,:]:
            try:

                if (biggest_radius < i[2]):
                    biggest_radius = i[2]
                    biggestX = i[0]
                    biggestY = i[1]


                    # draw the outer circle
                cv2.circle(img,(biggestX,biggestY),biggest_radius,(0,255,0),2)
                # draw the center of the circle
                cv2.circle(img, (biggestX,biggestY),2,(0,0,255),3)
                # draw the outer circle
                #cv2.circle(img,(i[0],i[1]),i[2],(0,255,0),2)
                # draw the center of the circle
                #cv2.circle(img,(i[0],i[1]),2,(0,0,255),3)
            except IndexError:
                print("No ball found")
                runCalculation = False
                continue
        #if saveImage:
        if(imageCounter % 5 == 0):
            cv2.imwrite("Image%d.jpg" % imageCounter, img)

        if runCalculation:

            #print("BiggestX = " + str(biggestX))
            #print("BiggestY = " + str(biggestY))
            #print("Biggest radius = " + str(biggest_radius))

            #if(imageCounter % 5 == 0):
              #  cv2.imwrite("Image%d.jpg" % imageCounter, img)
            
            ActualBallHeightPixel = DefaultBallHeightPixel / (DefaultImageHeight / height)
            ActualPixelsPerInch = DefaultPixelsPerInch / (DefaultImageHeight / height)

            DirectDistanceBallInch = ((ActualBallHeightPixel / (2 * biggest_radius)) * CalibrationDistanceInch)
            XDisaplacementPixel = biggestX - (width / 2)
            YDisplacmentPixel = biggestY - (height / 2)
            YAngle = math.atan(YDisplacmentPixel/(ActualPixelsPerInch * DefaultPixelsPerInch)) #MEASURED IN RADIANS

            XAngle = math.atan(XDisaplacementPixel/(ActualPixelsPerInch * DefaultPixelsPerInch)) * (180/np.pi) #MEASURED IN DEGREES

            #ZDistance = DirectDistanceBallInch * math.cos(YAngle) #ROBOT DISTANCE TO BALL
            #ZDistance = DirectDistanceBallInch * math.sin((CameraMountingAngleRadians - YAngle))
            ZDistance = (HeightOfCamera - DefaultBallRadiusInch)/math.tan((CameraMountingAngleRadians - YAngle))
            

            try:
                SmartDashboard.putNumber("ZDistance", ZDistance)
                print("ZDistance = " + ZDistance)
                SmartDashboard.putNumber("Xangle", XAngle)
                print("Xangle = " + XAngle)
            except:
                print("ZDistance = " + str(ZDistance))
                print("Xangle = " + str(XAngle))
                print("Could not find network tables")

            #img = cv2.circle(img, (biggestX, biggestY), biggest_radius, (255, 0, 0), 5
        else:
            print("could not find any object so decided to skip calculations as well")


    if cameraFeed == 1:

        print("Using back camera")

        try:
            SmartDashboard.putString("VisionCodeSelected", "1")
        except:
            print("Cannot put string because network table was not found")

        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)


while True:
    #time.sleep(2)
    Vision()

    
