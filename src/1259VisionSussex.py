import cscore
import networktables as nt 

import cv2 
import time
import numpy as np 
import math

#time.sleep(5)

cs = cscore.CameraServer.getInstance()
#cs.enableLogging()
time.sleep(3)


try:
    nt.NetworkTables.initialize(server="10.12.59.2")
    print("NetworkTable found!")
    SmartDashboard = nt.NetworkTables.getTable("SmartDashboard")
except:
    print("No network table found continuing with the rest of the code")

Back = cs.startAutomaticCapture(name = "BackCamera", path = "/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0-video-index0")
Back.setResolution(640, 480)

Front = cs.startAutomaticCapture(name = "FrontCamera", path = "/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0-video-index0")
Front.setResolution(640, 480)

server = cs.addSwitchedCamera("SwitchedCamera")

print("Starting code stuff")

#visionCounter = 0



def Vision():
    global visionCounter

    try:
    	cameraFeed = SmartDashboard.getNumber("cameraFeed", 0)
    except:
        cameraFeed = 0
        print("Couldn't get cameraFeed value because no network table was found\nDefault to 0")

    if cameraFeed == 0:
        
        #print("Using front camera")
        visionCounter = 0

        try:
            #SmartDashboard.putNumber("VisionCounter", visionCounter)
            SmartDashboard.putString("VisionCodeSelected", "0")
        except:
            print("Cannot put string because network table was not found")
       
        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)
            


    if cameraFeed == 1:

        print("Using back camera")
        #visionCounter += 1

        try:
            #SmartDashboard.putNumber("VisionCounter", visionCounter)
            SmartDashboard.putString("VisionCodeSelected", "1")
        except:
            print("Cannot put string because network table was not found")

        Front.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kForceClose)
        Back.setConnectionStrategy(cscore.VideoSource.ConnectionStrategy.kKeepOpen)


while True:
	Vision()

    
