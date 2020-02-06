# Importing required modules
from logging import Logger

import cv2
import numpy as np
import time
import math
import logging
import logging.config


class Vision1259:

    # Read logging configuration file
    logging.config.fileConfig('logging.yaml')

    # create logger
    logger: Logger = logging.getLogger('1259Vision')

    # Example of log statement usage in 'application' code
    # log severity level order from most verbose to least
    # debug->info->warning->error->critical
    # logging.debug('%s Love! %s', 'I', 'Python!')
    # logging.warning('warning message')

    radiansToDegrees = 180 / np.pi

    imageCenterX = 640 / 2
    imageCenterY = 480 / 2

    calibCameraDistInch = 51
    sizeOfFuelCellInch = 7
    sizeOfFuelCellPixel = 104

    focalLengthPixel = sizeOfFuelCellPixel * calibCameraDistInch / sizeOfFuelCellInch
    pixelsPerInch = (sizeOfFuelCellPixel / sizeOfFuelCellInch)
    focalLengthTimesFuelCellSize = focalLengthPixel * sizeOfFuelCellInch  # distance = focalLengthTimesFuelCellSize / fitted circle size in pixels

    # HSV values for the yellow game ball
    # minHSVBall = np.array([28,  76,  89])
    # maxHSVBall = np.array([36, 255, 255])
    minHSVBall = np.array([18, 90, 90])
    maxHSVBall = np.array([30, 255, 255])

    # Font that will be used to display the text on screen
    font = cv2.FONT_HERSHEY_SIMPLEX

    # start the camera
    vc = cv2.VideoCapture(0)

    # If camera is open and taking shots
    if vc.isOpened():
        rval, frame = vc.read()
    else:
        rval = False

    saveCount = 0
    elapsedAccum = 0
    elapsedAccumCamRead = 0
    loopCount = 1
    # Do this while reading images
    print("Using OpenCV version ", cv2.__version__)
    print("Sec per loop,Avg loop,Sec camera read,Avg camera read,Dist,HorzAngle")
    while rval:
        # start timing
        startTime = time.time()
        rval, frame = vc.read()
        endTime = time.time()
        elapsedCam = endTime - startTime

        # Convert the RGB image to HSV
        imHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Find pixels in the blurred image that fit in range and turn them white and others black
        InRange = cv2.inRange(imHSV, minHSVBall, maxHSVBall)

        # Using the black and white binary image, plot a point at every boundry pixel that is white
        _, contours, _ = cv2.findContours(InRange, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        # Find the biggest contour since that will be the object we are looking for
        try:
            areas = [cv2.contourArea(c) for c in contours]
            max_index = np.argmax(areas)
            cnt = contours[max_index]
        except:
            print("Could not find any contours")
            continue

        # Use openCV circle to estimate dist and angle
        center, radius = cv2.minEnclosingCircle(cnt)
        radiusInt = int(radius)
        centerInt = (int(center[0]), int(center[1]))
        height = 2 * radius
        # print("Height of image based on circle: " + str(height))

        DistZ = focalLengthTimesFuelCellSize / height

        horzDistPixel = center[0] - imageCenterX
        horzDistInch = horzDistPixel / pixelsPerInch
        horzAngleRadians = math.atan(horzDistInch / calibCameraDistInch)
        horzAngleDegree = horzAngleRadians * radiansToDegrees

        # if saveCount % 5 == 0:
        cv2.circle(frame, centerInt, radiusInt, [255, 0, 0], 3, cv2.LINE_AA)
        cv2.drawMarker(frame, (int(imageCenterX), int(imageCenterY)), [0, 0, 255], cv2.MARKER_CROSS)
        cv2.imwrite("InRange.jpg", InRange)
        cv2.imwrite("ImagingOutput.jpg", frame)

        saveCount = saveCount + 1

        # end timing
        endTime = time.time()
        elapsed = endTime - startTime
        elapsedAccum = elapsedAccum + elapsed
        elapsedAccumCamRead = elapsedAccumCamRead + elapsedCam
        print(elapsed, ",", elapsedAccum / loopCount, ",", elapsedCam, ",", elapsedAccumCamRead / loopCount, ",", DistZ,
              ",", horzAngleDegree)
        # Increment the loop counter
        loopCount = loopCount + 1