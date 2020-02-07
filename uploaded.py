#!/usr/bin/env python3
#----------------------------------------------------------------------------
# Copyright (c) 2018 FIRST. All Rights Reserved.
# Open Source Software - may be modified and shared by FRC teams. The code
# must be accompanied by the FIRST BSD license file in the root directory of
# the project.
#
#This is how to understand the comments
#
#Gen. variable system:
#
#Generation variable system work on the fact that first generation variables 
#have values that we know of and second generation variables use values from 
#the first
#----------------------------------------------------------------------------

import json
import time
import math
import sys
import cv2
import numpy as np

from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer, VideoSink, CvSink
from networktables import NetworkTablesInstance
import ntcore

#   JSON format:
#   {
#       "team": <team number>,
#       "ntmode": <"client" or "server", "client" if unspecified>
#       "cameras": [
#           {
#               "name": <camera name>
#               "path": <path, e.g. "/dev/video0">
#               "pixel format": <"MJPEG", "YUYV", etc>   // optional
#               "width": <video mode width>              // optional
#               "height": <video mode height>            // optional
#               "fps": <video mode fps>                  // optional
#               "brightness": <percentage brightness>    // optional
#               "white balance": <"auto", "hold", value> // optional
#               "exposure": <"auto", "hold", value>      // optional
#               "properties": [                          // optional
#                   {
#                       "name": <property name>
#                       "value": <property value>
#                   }
#               ],
#               "stream": {                              // optional
#                   "properties": [
#                       {
#                           "name": <stream property name>
#                           "value": <stream property value>
#                       }
#                   ]
#               }
#           }
#       ]
#       "switched cameras": [
#           {
#               "name": <virtual camera name>
#               "key": <network table key used for selection>
#               // if NT value is a string, it's treated as a name
#               // if NT value is a double, it's treated as an integer index
#           }
#       ]
#   }

configFile = "/boot/frc.json"

class CameraConfig: pass

team = None
server = False
cameraConfigs = []
switchedCameraConfigs = []
cameras = []

def parseError(str):
    """Report parse error."""
    print("config error in '" + configFile + "': " + str, file=sys.stderr)

def readCameraConfig(config):
    """Read single camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read camera name")
        return False

    # path
    try:
        cam.path = config["path"]
    except KeyError:
        parseError("camera '{}': could not read path".format(cam.name))
        return False

    # stream properties
    cam.streamConfig = config.get("stream")

    cam.config = config

    cameraConfigs.append(cam)
    return True

def readSwitchedCameraConfig(config):
    """Read single switched camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read switched camera name")
        return False

    # path
    try:
        cam.key = config["key"]
    except KeyError:
        parseError("switched camera '{}': could not read key".format(cam.name))
        return False

    switchedCameraConfigs.append(cam)
    return True

def readConfig():
    """Read configuration file."""
    global team
    global server

    # parse file
    try:
        with open(configFile, "rt", encoding="utf-8") as f:
            j = json.load(f)
            print(type(j))
    except OSError as err:
        print("could not open '{}': {}".format(configFile, err), file=sys.stderr)
        return False

    # top level must be an object
    if not isinstance(j, dict):
        parseError("must be JSON object")
        return False

    # team number
    try:
        team = j["team"]
    except KeyError:
        parseError("could not read team number")
        return False

    # ntmode (optional)
    if "ntmode" in j:
        str = j["ntmode"]
        if str.lower() == "client":
            server = False
        elif str.lower() == "server":
            server = True
        else:
            parseError("could not understand ntmode value '{}'".format(str))

    # cameras
    try:
        cameras = j["cameras"]
    except KeyError:
        parseError("could not read cameras")
        return False
    for camera in cameras:
        if not readCameraConfig(camera):
            return False

    # switched cameras
    if "switched cameras" in j:
        for camera in j["switched cameras"]:
            if not readSwitchedCameraConfig(camera):
                return False

    return True

def startCamera(config):
    """Start running the camera."""
    print(type(config))
    print("Starting camera '{}' on {}".format(config.name, config.path))
    inst = CameraServer.getInstance()
    camera = UsbCamera(config.name, config.path)
    server = inst.startAutomaticCapture(camera=camera, return_server=True)

    camera.setConfigJson(json.dumps(config.config))
    camera.setConnectionStrategy(VideoSource.ConnectionStrategy.kKeepOpen)

    if config.streamConfig is not None:
        server.setConfigJson(json.dumps(config.streamConfig))

    return camera

def startSwitchedCamera(config):
    """Start running the switched camera."""
    print("Starting switched camera '{}' on {}".format(config.name, config.key))
    server = CameraServer.getInstance().addSwitchedCamera(config.name)

    def listener(fromobj, key, value, isNew):
        if isinstance(value, float):
            i = int(value)
            if i >= 0 and i < len(cameras):
              server.setSource(cameras[i])
        elif isinstance(value, str):
            for i in range(len(cameraConfigs)):
                if value == cameraConfigs[i].name:
                    server.setSource(cameras[i])
                    break

    NetworkTablesInstance.getDefault().getEntry(config.key).addListener(
        listener,
        ntcore.constants.NT_NOTIFY_IMMEDIATE |
        ntcore.constants.NT_NOTIFY_NEW |
        ntcore.constants.NT_NOTIFY_UPDATE)

    return server

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        configFile = sys.argv[1]

    # read configuration
    if not readConfig():
        sys.exit(1)

    # start NetworkTables
    ntinst = NetworkTablesInstance.getDefault()
    if server:
        print("Setting up NetworkTables server")
        ntinst.startServer()
    else:
        print("Setting up NetworkTables client for team {}".format(team))
        ntinst.startClientTeam(team)

    # start cameras
    for config in cameraConfigs:
        cameras.append(startCamera(config))

    # start switched cameras
    for config in switchedCameraConfigs:
        startSwitchedCamera(config)


    """
    EVERYTHING BELOW THIS IS ADDITIONAL CODE THAT HAS BEEN LATER DECIDED TO BE ADDEED
    TO THIS PYTHON FILE
    """

    #Print statements let operator know whether a camera has been added or not
    print("Size of cameras: " + str(len(cameras)))
    print("Size of cameraConfigs: " + str(len(cameraConfigs)))
    print("Size of switchedCameraConfigs: " + str(len(switchedCameraConfigs)))
    
    #Getting CameraServer instance and starting capture
    cs = CameraServer.getInstance()
    camera = cs.startAutomaticCapture()
    #Setting Resolution
    camera.setResolution(640, 480)

    # Get a CvSink. This will capture images from the camera
    cvSink = cs.getVideo()

    #Camera width and height will essentially equal the resolution that has been hardcoded
    camWid = 640
    camHgt = 480

    #Print statement for debugging
    print("Starting 1259Vision.py")

    #Variables that will be needed to do distance calculations - FIRST Gen. Variables 
    DefaultImageHeight = 480
    DefaultBallHeightPixel = 100 """ WE NEED TO CALCULATE THIS"""
    DefaultPixelsPerInch = 50 """ WE NEED TO CALCULATE THIS """
    CalibrationDistanceInch = 24 

    MaxPossibleAngle = 60 """ MEASURED IN DEGREES """
    MaxPossibleDistance = 120 """ MEASURED IN INCHES """
    

    #Image saving switch
    SaveImages = False

    #Variables needed to distance calculations - SECOND Gen. Variables
    MaxPossibleRadius = (DefaultImageHeight / 2) """ MEASURED IN INCHES """
    MinPossibleRadius = 0   """ WE NEED TO CALCULATE THIS """

    #Checking whether OpenCV works on the system, printing the version number
    print("Using OpenCV version ", cv2.__version__)

    #Maximum and minimum possible HSV values to detect the ball
    minHSVBall = np.array([18, 100, 100])
    maxHSVBall = np.array([40, 255, 255])

    #X and Y coordinate of the center of the image
    imageCenterX = camWid / 2
    imageCenterY = camHgt / 2

    #Printing Camera information
    print("FPS,AvgFPS,LoopTime [ms],AvgLoopTime [ms],CameraReadTime [ms],AvgCameraRead [ms],Dist [in],HorzAngle [deg]")

    #Pre defining an empty image for the program to use/fill
    img = np.zeros(shape=(480, 640, 3), dtype=np.uint8)

    scale_percent = 50 # percent of original size
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)

    
    print("Starting main loop")
    # loop forever
    while True:

        #Grabbing image as a vatriable from opencv sink
        time0, draw = cvSink.grabFrame(img)

        draw = cv2.resize(draw, dim, interpolation = cv2.INTER_AREA)
        
        #Convert the RGB image to HSV
        imHSV = cv2.cvtColor(draw, cv2.COLOR_BGR2HSV)
        #Find pixels in the blurred image that fit in range and turn them white and others black                                          
        InRange = cv2.inRange(imHSV, minHSVBall, maxHSVBall)

        InRange = cv2.GaussianBlur(InRange, (5, 5), cv2.BORDER_DEFAULT)

        circles = cv2.HoughCircles(InRange, cv2.HOUGH_GRADIENT, 1, int(height/10), 100, 25, 5, int(height/2))
        circles = np.uint16(np.around(circles))

        biggest_radius = 0;
        for i in circles[0,:]:
            if (biggest_radius < i[2]):
                biggest_radius = i[2]
                biggestX = i[0]
                biggestY = i[1]
            
        ActualBallHeightPixel = DefaultBallHeightPixel / (DefaultImageHeight / height)
        ActualPixelsPerInch = DefaultPixelsPerInch / (DefaultImageHeight / height)

        DirectDistanceBallInch = ((ActualBallHeightPixel / (2 * biggest_radius)) * CalibrationDistanceInch)
        XDisaplacementPixel = biggestX - (width / 2)
        YDisplacmentPixel = biggestY - (height / 2)

        #Using moments to find the center of the image
        if SaveImages:
            loopCount += 1
            cv2.imwrite("SomeImage%d.jpg" % (loopCount), draw)
            #Wait time if needed
            time.sleep(0.5)
        #try:
        #M = cv2.moments(box)
        #cX = int(M["m10"] / M["m00"])
        #cY = int(M["m01"] / M["m00"])

        
