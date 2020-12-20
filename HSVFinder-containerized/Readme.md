# Containerized HSV Finder 
## Author: Agastya Asthana
---
## How to Use

The source files created here can be used to build the docker image but is 
not neccesarry because the image needed is already uploaded to cloud and can be be pulled down by running the file in `runMe.sh`.
Just copy & paste the command in `runMe.sh` into a raspberry pi terminal connected to internet to see the magic!

---
## About This
This project took me several days and countless failures to achieve. 

The base image for this project comes from 
`francoisgervais/opencv-python:4.3.0`. The base image is a debian-based image 
which has OpenCV built-in with python3. This eased my effort a lot since not having to worry about installing opencv and making 
it work with python3.

 
The hardest part was setting up the `docker run` command to pass in camera and 
setup the GUI to show. There were ways to achieve this by ssh'ing into the 
container and launching a vnc server but I wanted to build a container that 
didn't require any action from the user. I luckily found an article by 
**Saravanan Sundaramoorthy** on *Running GUI Applications inside Docker Containers*. 
This article talked on how to to share host's network info, host's XServer, and 
host's DISPLAY environment variable with the container. Using this information 
and Docker docs I was able to compose the runMe shell script which encompasses 
all this. 
