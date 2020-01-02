import cscore
import networktables as nt 

import cv2 
import time
import numpy as np 

time.sleep(15)

cs = cscore.CameraServer.getInstance()
cs.enableLogging()

try:
    nt.NetworkTables.initialize(server="10.12.59.2")
    print("NetworkTable found!")
    SmartDashboard = nt.NetworkTables.getTable("SmartDashboard")
except:
    print("No network table found continuing with the rest of the code")

Back = cs.startAutomaticCapture(name = "BackCamera", path = "/dev/v4l/by-path/platform-3f980000.usb-usb-0:1.3:1.0-video-index0")
Back.setResolution(640, 480)

Front = cs.startAutomaticCapture(name = "FrontCamera", path = "/dev/v4l/by-path/platform-3f980000.usb-usb-0:1.2:1.0-video-index0")
Front.setResolution(640, 480)

server = cs.addSwitchedCamera("SwitchedCamera")

print("Assigning Variables")
FrontCameraSetup = True
BackCameraSetup = False


def Vision():

    global FrontCameraSetup
    global BackCameraSetup

    try:
    	cameraFeed = SmartDashboard.getNumber("cameraFeed", 0)
    except:
        cameraFeed = 0
        print("Couldn't get cameraFeed value because no network table was found\nDefault to 0")

    if cameraFeed == 0:
        
        print("Using front camera")

        try:
            SmartDashboard.putString("VisionCodeSelected", "0")
        except:
            print("Cannot put string because network table was not found")
        #server.setSource(Front)
        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)

        #mjpegServer = cscore.MjpegServer("httpserver", 8081)
        #mjpegServer.setSource(Front)

        cvSink = cscore.CvSink("FrontSink")
        cvSink.setSource(Front)

        cvSource = cscore.CvSource("FrontCVSource", cscore.VideoMode.PixelFormat.kMJPEG, 640, 480, 30)
        #cvMjpegServer = cscore.MjpegServer("FrontHttpServer", 8082)
        #cvMjpegServer.setSource(cvSource)
            
        img = np.zeros(shape=(640, 480, 3), dtype=np.uint8)
                
        time, img = cvSink.grabFrame(img)
        cvSource.putFrame(img)

    if cameraFeed == 1:

        print("Using back camera")

        try:
            SmartDashboard.putString("VisionCodeSelected", "1")
        except:
            print("Cannot put string because network table was not found")

        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)


while True:
	Vision()

    
