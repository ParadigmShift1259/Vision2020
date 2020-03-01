import cscore
import networktables as nt 

import cv2 
import time
import numpy as np 
import math
import logging

time.sleep(5)

cs = cscore.CameraServer.getInstance()

#Exception block for handling network table initialization
try:
    nt.NetworkTables.initialize(server="10.12.59.2")
    print("NetworkTable found!")
    SmartDashboard = nt.NetworkTables.getTable("SmartDashboard")
except:
    print("No network table found continuing with the rest of the code")
    print("")

class SmoothenClass:
    def __init__(self, order):
        self.order = order
        self.x = np.arange(8.0)
        self.y = np.arange(8.0)


    def AddValue(self, string, index, float):
        if string == "Distance":
            self.y[index] = float
        if string == "Time":
            self.x[index] = float

    def AppendValues(self, string, float):
        if string == "Distance":
            self.y = np.delete(self.y, 0)
            self.y = np.append(self.y, float)
        if string == "Time":
            self.x = np.delete(self.x, 0)
            self.x = np.append(self.x, float)

    def ReturnPrediction(self):
        endTime = time.time()
        timeLapsed = endTime - startTime
        #print("X Array: " + str(self.x))
        #print("Y Array: " + str(self.y))

        Regression = np.polyfit(self.x, self.y, self.order)
        Predictor = np.poly1d(Regression)
        return Predictor(timeLapsed)

f = open("1259VisionMatchNumber.txt", "r")
MatchNumber = int(f.read())
MatchNumber += 1
f.close()
f = open("1259VisionMatchNumber.txt", "w")
f.write(str(MatchNumber))
print(MatchNumber)
f.close()

filename = "1259VisionLogMatch%d.log" % MatchNumber
logging.basicConfig(level=logging.INFO, filename=filename, format='%(asctime)s :: %(levelname)s :: %(message)s')

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
DefaultCameraViewAngle = 36     #Vertical angle for camera 60
HeightOfCamera = 18.3125
CameraMountingAngleRadians = 28.0 * (np.pi/180) #CameraMounting angle

MaxPossibleAngle = 60 # MEASURED IN DEGREES 
MaxPossibleDistance = 120 # MEASURED IN INCHES

#Variables needed to distance calculations - SECOND Gen. Variables
MaxPossibleRadius = (DefaultImageHeight / 2) #MEASURED IN INCHES 
MinPossibleRadius = 0   #WE NEED TO CALCULATE THIS
DefaultPixelsPerInch = (DefaultImageHeight/2)/(math.tan((DefaultCameraViewAngle/2) * (np.pi/180)) * CalibrationDistanceInch)
DefaultBallHeightPixel = DefaultBallRadiusInch/(math.tan((DefaultCameraViewAngle/2) * (np.pi/180)) * CalibrationDistanceInch) * DefaultImageHeight
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

#Whether or not to do calculations
runCalculation = True
#Whether or not to save images
saveImage = False
#Helps in labeling images so that they are not overwritten
imageCounter = 0
#How many time to repeat adding value to x and y lists
repeatPolyFit = 0
#Counter to tell whether vision has stopped working or not
VisionCounter = 0
#Timer for the x-value of plotting direction
startTime = time.time()

#Smoothening class which takes the order as a perimeter
Smooth = SmoothenClass(1)

def Vision():

    #Timer used to determine how many seconds it took to run vision helps with FPS
    t0 = time.time()

    #Variables that needed to be global so the function could use them 
    global img
    global imageCounter
    global VisionCounter
    global repeatPolyFit
    global Smooth
    global runCalculation

    #Incrementing the image counter so that every image is renamed different
    imageCounter += 1
    #Increment this counter so that changing values represent working vision
    VisionCounter += 1

    #If getting camera feed from network table is an issue then default to using front camera
    try:
        cameraFeed = SmartDashboard.getNumber("cameraFeed", 0)
        getNewBall = 0
        runCalculation = True
        SmartDashboard.putNumber("VisionCounter", VisionCounter)

    except:
        cameraFeed = 0
        getNewBall = 0
        runCalculation = True
        print("Couldn't get cameraFeed value because no network table was found\nDefault to 0")

    #If using front camera
    if cameraFeed == 0:

        #If network tables is causing issue then report it
        try:
            SmartDashboard.putString("VisionCodeSelected", "0")
        except:
            print("Cannot put string because network table was not found")

        #Enable only front camera stream
        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)
        logging.info("Using front camera")

        #Creating an opencv sink 
        cvSink = cscore.CvSink("cvsink")
        cvSink.setSource(Front)
                
        #Grabbing an image and storing in img varibale
        time0, img = cvSink.grabFrame(img)

        img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

        #Convert the RGB image to HSV
        imHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        #Find pixels in the blurred image that fit in range and turn them white and others black                                          
        InRange = cv2.inRange(imHSV, minHSVBall, maxHSVBall)

        #Blurring the InRange so HoughCircles have an easier time finding balls
        InRange = cv2.GaussianBlur(InRange, (5, 5), cv2.BORDER_DEFAULT)

        #Save the inrange if told to do so
        if saveImage:
            if(imageCounter % 5 == 0):
                cv2.imwrite("Inrange%d.png" % imageCounter, InRange)

        #circles = cv2.HoughCircles(InRange, cv2.CV_HOUGH_GRADIENT, 2, int(height/10), 150, 50, 10, 60)
        circles = cv2.HoughCircles(InRange, cv2.HOUGH_GRADIENT, 1, int(width/10), param1=180, param2=10, minRadius=5, maxRadius=50)
        #circles = cv2.HoughCircles(InRange, cv2.HOUGH_GRADIENT, 1, int(width/10), param1=150, param2=35, minRadius=5, maxRadius=50)
        try:
            circles = np.uint16(np.around(circles))
        except AttributeError:
            runCalculation = False
            repeatPolyFit = 0
            logging.warning("No ball was found at this time")

        if runCalculation:
            global biggest_radius
            global biggestX
            global biggestY
            global startTime
            biggest_radius = 0
            for i in circles[0,:]:
                try:

                    if (biggest_radius < i[2]):
                        biggest_radius = i[2]
                        biggestX = i[0]
                        biggestY = i[1]

                    if(saveImage):
                        # draw the outer circle
                        cv2.circle(img,(biggestX,biggestY),biggest_radius,(0,255,0),2)
                        # draw the center of the circle
                        cv2.circle(img, (biggestX,biggestY),2,(0,0,255),3)

                except IndexError:
                    print("No ball found")
                    logging.warning("No values in the hough circle array")

            if saveImage:
                if(imageCounter % 5 == 0):
                    cv2.imwrite("Image%d.jpg" % imageCounter, img)

        
            #print("BiggestX = " + str(biggestX))
            #print("BiggestY = " + str(biggestY))
            #print("Biggest radius = " + str(biggest_radius))

            #if(imageCounter % 5 == 0):
                #  cv2.imwrite("Image%d.jpg" % imageCounter, img)
            
            ActualBallHeightPixel = DefaultBallHeightPixel / (DefaultImageHeight / height)
            ActualPixelsPerInch = DefaultPixelsPerInch / (DefaultImageHeight / height)

            DirectDistanceBallInch = ((ActualBallHeightPixel / (2 * biggest_radius)) * CalibrationDistanceInch)
            #print("DirectDistanceBallInch = " + str(DirectDistanceBallInch) + " Biggest Radius = " + str(biggest_radius))
            XDisaplacementPixel = biggestX - (width / 2)
            YDisplacmentPixel = biggestY - (height / 2)
            YAngle = math.atan(YDisplacmentPixel/(ActualPixelsPerInch * DefaultPixelsPerInch)) #MEASURED IN RADIANS

            XAngle = math.atan(XDisaplacementPixel/(ActualPixelsPerInch * DefaultPixelsPerInch)) * (180/np.pi) #MEASURED IN DEGREES

            ZDistance = DirectDistanceBallInch * math.cos((CameraMountingAngleRadians - YAngle))
            #print("getNewBall: " + str(getNewBall))
            #print("RepeatPolyFit: " + str(repeatPolyFit))
            #ZDistance = (HeightOfCamera - DefaultBallRadiusInch)/math.tan((CameraMountingAngleRadians - YAngle))
            
            relativeEndTime = time.time()
            timeLapsed = relativeEndTime - startTime
            readyForPrediction = False

            if(getNewBall < 4):
                if(repeatPolyFit < 8):
                    #print("Running 15 & ZDistance: " + str(ZDistance) + " TimeNEW: " + str(timeLapsed))
                    Smooth.AddValue("Distance", repeatPolyFit, ZDistance)
                    Smooth.AddValue("Time", repeatPolyFit, timeLapsed)
                    repeatPolyFit += 1
                else:
                    readyForPrediction = True
                    print("We are ready for prediction")

                if (readyForPrediction):
                    answer = Smooth.ReturnPrediction()
                    print("ZDistance = " + str(ZDistance))
                    msgRaw = "RawDistance: %d" % ZDistance
                    logging.info(msgRaw)
                    print("Predtion = " + str(answer))
                    #print("In range = " + str(abs(ZDistance - answer)))
                    if (abs(ZDistance - answer) < 6.56 ):
                        Smooth.AppendValues("Distance", ZDistance)
                        ZDistance = answer
                        endTime = time.time()
                        elapsedTime = endTime - startTime
                        print("FeedingTime = " + str(elapsedTime))
                        Smooth.AppendValues("Time", elapsedTime)
                    else:
                        getNewBall += 1
                        answer = 0
                        Smooth.AppendValues("Distance", ZDistance)
                        endTime = time.time()
                        elapsedTime = endTime - startTime
                        #print("FeedingTime = " + str(elapsedTime))
                        Smooth.AppendValues("Time", elapsedTime)


            elif(getNewBall == 4):
                repeatPolyFit = 0
                getNewBall = 0
                ZDistance = 0
                XAngle = 0
                startTime = time.time()
            
            SmartDashboard.putNumber("ZDistance", ZDistance)
            msgDistance = "Predicted distance: %d" % ZDistance
            logging.info(msgDistance)
            #print("ZDistance = " + str(ZDistance))
            SmartDashboard.putNumber("Xangle", XAngle)
            msgAngle = "XAngle: %d" % XAngle
            logging.info(msgAngle)
            #print("Xangle = " + str(XAngle))

        else:
            print("could not find any object so decided to skip calculations as well")
            ZDistance = 0
            XAngle = 0
            SmartDashboard.putNumber("ZDistance", ZDistance)
            print("ZDistance = " + str(ZDistance))
            SmartDashboard.putNumber("Xangle", XAngle)
            print("Xangle = " + str(XAngle))
            
        print("The time it took " + str(time.time()-t0))


    if cameraFeed == 1:

        print("Using back camera")

        try:
            SmartDashboard.putString("VisionCodeSelected", "1")
        except:
            print("Cannot put string because network table was not found")

        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)

        startTime = time.time()


while True:
    #time.sleep(2)
    Vision()

    
