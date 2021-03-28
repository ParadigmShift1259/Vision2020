# Vision2020
OpenCV and Limelight related code
In the src folder there is a PDF file explaining exactly how the objects are masked and how locations are calculated. Just a TL:DR objects are massked using HSV filtering.

The second folder is a python script that shows you a live feed with HSV sliders to visually show what the masked image the camera will percieve giving better intuition to the operator. The first folder is an extension of that program. With the help of docker container the HSVFinder program can run on any raspberrypi with a camera and just running docker.

The src folder is where the actual code lies. There are multiple files available there but the production program is names "1259Vision.py" this folder contains .service files that complement that python script. The service files start their designated python script when the raspberrypi boots.
# Vision Setup
Part of vision this year will include a camera server running on the pi which sends a feed of the camera back to the driver station and the same feed is used for vision processing. 

In order to accomplish this task we have downloaded a python multiCameraServer.py example file which can be found here:

Go to: http://frcvision.local/
>* Select the Application tab
>* At the bottom you should see a button to download a Java example, C++ example, and a Python example
>* Download the Python example
>* Extract the multiCameraServer.py file from the zip file and upload the file by doing the following:
>	* In the Application Tab on the dashboard, there is an option to upload a file, upload that file
>	* On the file system this sile should show up as uploaded.py
>	* Changes made to this file will be applied after a reboot
