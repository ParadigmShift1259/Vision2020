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
    #print("")

#Smoothening class where you can smoothen out values
class SmoothenClass:
    def __init__(self, order):
        self.order = order
        self.x = np.arange(8.0)
        self.y = np.arange(8.0)


    def AddValue(self, string, index, float):
        if string == "Y": #make y
            self.y[index] = float
        if string == "X": # make x
            self.x[index] = float

    def AppendValues(self, string, float):
        if string == "Y":
            self.y = np.delete(self.y, 0)
            self.y = np.append(self.y, float)
        if string == "X":
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

#Open the file that contains match number
f = open("1259VisionMatchNumber.txt", "r")
MatchNumber = int(f.read())
#Increment MatchNumber variable by 1
MatchNumber += 1
#Close the file
f.close()
f = open("1259VisionMatchNumber.txt", "w")
#Write incrementation back to the file
f.write(str(MatchNumber))
#Print/Log just for safety
print(MatchNumber)
#Match number message
msgMatchNumber = "We are in match: %d" % MatchNumber
logging.info(msgMatchNumber)
#Close the file
f.close()

#Create a file with the following name
filename = "/home/pi/Vision2020/src/1259VisionLogMatch%d.log" % MatchNumber
print("running logging")
logging.basicConfig(level=logging.INFO, filename=filename, format='%(asctime)s :: %(levelname)s :: %(message)s')


#Function to set up the front camera
def SetupFrontCamera():
    global Front
    Front = cs.startAutomaticCapture(name = "FrontCamera", path = "/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0-video-index0")
    Front.setResolution(640, 480) # 640 x 352
    print("Setting up front camera")
#Actually set the front camera up
SetupFrontCamera()



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
minHSVBall = np.array([20, 76, 55])
maxHSVBall = np.array([45, 255, 255])
#minHSVBall = np.array([25, 125, 125])
#maxHSVBall = np.array([35, 255, 255])

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
saveImage = True
#Helps in labeling images so that they are not overwritten
imageCounter = 0
#How many time to repeat adding value to x and y lists
repeatPolyFit = 0
#Counter to tell whether vision has stopped working or not
VisionCounter = 0
#Timer for the x-value of plotting direction
startTime = time.time()

#Smoothening class which takes the order as a perimeter - SMOOTHING DISTANCE
SmoothDistance = SmoothenClass(1)
#Smoothening class which takes the order as a perimeter - SMOOTHING ANGLE
SmoothAngle = SmoothenClass(1)

def Vision():

    #Timer used to determine how many seconds it took to run vision helps with FPS
    t0 = time.time()

    #Variables that needed to be global so the function could use them 
    global img
    global imageCounter
    global VisionCounter
    global repeatPolyFit
    global SmoothDistance
    global SmoothAngle
    global runCalculation

    #Incrementing the image counter so that every image is renamed different
    imageCounter += 1
    #Increment this counter so that changing values represent working vision
    VisionCounter += 1

    #If getting camera feed from network table is an issue then default to using front camera
    try:
        # Reset the amount of times the program has not gotten the ball
        getNewBall = 0
        # Essentially resetting the flag that tells the code to calculate stuff
        runCalculation = True
        SmartDashboard.putNumber("VisionCounter", VisionCounter)

    except:
        #Do the stuff in the try block except Network Table stuff
        getNewBall = 0
        runCalculation = True
        print("Couldn't get cameraFeed value because no network table was found\nDefault to 0")

    #If network tables is causing issue then report it
    try:
        SmartDashboard.putString("VisionCodeSelected", "0")
    except:
        print("Cannot put string because network table was not found")
        logging.warning("Network Tables not found")

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
    #if saveImage:
    #    if(imageCounter % 150 == 0):
    #        cv2.imwrite("Inrange%d.png" % imageCounter, InRange)

    # Hough circle transformation looks in InRange file to find circles given the parameters below
    circles = cv2.HoughCircles(InRange, cv2.HOUGH_GRADIENT, 1, int(width/10), param1=180, param2=10, minRadius=5, maxRadius=50)
        
    try:
        #Convert the array to unsigned 16 integers
        circles = np.uint16(np.around(circles))
    except AttributeError:
        #If nothing in array then:
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

                if saveImage:
                    if(imageCounter % 150 == 0):
                        # draw the outer circle
                        cv2.circle(img,(biggestX,biggestY),biggest_radius,(0,255,0),2)
                        # draw the center of the circle
                        cv2.circle(img, (biggestX,biggestY),2,(0,0,255),3)

            except IndexError:
                #If no ball in array
                print("No ball found")
                logging.warning("No values in the hough circle array")

        # Flag for saving images
        if saveImage:
            if(imageCounter % 150 == 0):
                filename = "Image%d-%d.jpg" % (MatchNumber, imageCounter)
                cv2.imwrite(filename, img)
                msgFilewrite = "Look at %s" % filename
                logging.info(msgFilewrite)
            
        #See the PDF on github to understand how distance calculations are done
        ActualBallHeightPixel = DefaultBallHeightPixel / (DefaultImageHeight / height)
        ActualPixelsPerInch = DefaultPixelsPerInch / (DefaultImageHeight / height)

        DirectDistanceBallInch = ((ActualBallHeightPixel / (2 * biggest_radius)) * CalibrationDistanceInch)
        XDisaplacementPixel = biggestX - (width / 2)
        YDisplacmentPixel = biggestY - (height / 2)
        YAngle = math.atan(YDisplacmentPixel/(ActualPixelsPerInch * DefaultPixelsPerInch)) #MEASURED IN RADIANS

        XAngle = math.atan(XDisaplacementPixel/(ActualPixelsPerInch * DefaultPixelsPerInch)) * (180/np.pi) #MEASURED IN DEGREES

        ZDistance = DirectDistanceBallInch * math.cos((CameraMountingAngleRadians - YAngle))
            
        #Calculate the relative end time which is NOW
        relativeEndTime = time.time()
        #Subtract to find how many seconds have passed since we found the start time
        timeLapsed = relativeEndTime - startTime
        #Automatically set that we are not ready for any prediction
        readyForPrediction = False

        #run the following code if we have missed less than 4 balls
        if(getNewBall < 4):
            #Fill the array 8 times
            if(repeatPolyFit < 8):
                #Add distance and angle values to the smoothening class
                SmoothDistance.AddValue("Y", repeatPolyFit, ZDistance)
                SmoothDistance.AddValue("X", repeatPolyFit, timeLapsed)
                SmoothAngle.AddValue("Y", repeatPolyFit, XAngle)
                SmoothAngle.AddValue("X", repeatPolyFit, timeLapsed)
                #Increment since we have a value now
                repeatPolyFit += 1
            else:
                #If we have filled the array, then we are ready for prediction
                readyForPrediction = True
                print("We are ready for prediction")

            #Run when we are ready for getting predictions
            if (readyForPrediction):
                #Get a prediction from the smoothening class
                answer = SmoothDistance.ReturnPrediction()
                answerAngle = SmoothAngle.ReturnPrediction()
                print("ZDistance = " + str(ZDistance))
                msgRawDistance = "RawDistance: %d" % ZDistance
                logging.info(msgRawDistance)
                print("XAngle = " + str(XAngle))
                msgRawAngle = "RawAngle: %d" % XAngle
                logging.info(msgRawAngle)
                print("PredtionDistance = " + str(answer))
                print("PredictionAngle = " + str(answerAngle))

                if (abs(ZDistance - answer) < 6.56 ):
                    SmoothDistance.AppendValues("Y", ZDistance)
                    ZDistance = answer
                    endTime = time.time()
                    elapsedTime = endTime - startTime
                    print("FeedingTime = " + str(elapsedTime))
                    SmoothDistance.AppendValues("X", elapsedTime)
                elif (abs(ZDistance - answer) > 6.56 ):
                    getNewBall += 1
                    answer = 0
                    SmoothDistance.AppendValues("Y", ZDistance)
                    endTime = time.time()
                    elapsedTime = endTime - startTime
                    SmoothDistance.AppendValues("X", elapsedTime)
                elif (abs(XAngle - answerAngle) < 2.0):
                    SmoothAngle.AppendValues("Y", XAngle)
                    XAngle = answerAngle
                    endTime = time.time()
                    elapsedTime = endTime - startTime
                    SmoothAngle.AppendValues("X", elapsedTime)
                elif (abs(ZDistance - answer) > 2.0 ):
                    getNewBall += 1
                    answer = 0
                    SmoothAngle.AppendValues("Y", XAngle)
                    endTime = time.time()
                    elapsedTime = endTime - startTime
                    SmoothAngle.AppendValues("X", elapsedTime)

        elif(getNewBall == 4):
            repeatPolyFit = 0
            getNewBall = 0
            ZDistance = 0
            XAngle = 0
            startTime = time.time()
            
        SmartDashboard.putNumber("ZDistance", ZDistance)
        msgDistance = "Predicted distance: %d" % ZDistance
        logging.info(msgDistance)
        SmartDashboard.putNumber("XAngle", XAngle)
        msgAngle = "XAngle: %d" % XAngle
        logging.info(msgAngle)

    else:
        print("could not find any object so decided to skip calculations as well")
        ZDistance = 0
        XAngle = 0
        SmartDashboard.putNumber("ZDistance", ZDistance)
        print("ZDistance = " + str(ZDistance))
        SmartDashboard.putNumber("XAngle", XAngle)
        print("XAngle = " + str(XAngle))
            
    print("The time it took " + str(time.time()-t0))


while True:
    #time.sleep(2)
    Vision()

    
