#!/usr/bin/python
 
 
import smtplib
import StringIO
import subprocess
import os
import time
from datetime import datetime
from PIL import Image
from email.mime.text import MIMEText
 
 
 
 
 
                                ### CAMERA CONFIGURATION ###
 
 
# Motion detection settings:
# Threshold          - how much a pixel has to change by to be marked as "changed"
# Sensitivity        - how many changed pixels before capturing an image, needs to be higher if noisy view
# ForceCapture       - whether to force an image to be captured every forceCaptureTime seconds, values True or False
# filepath           - location of folder to save photos
# filenamePrefix     - string that prefixes the file name for easier identification of files.
# diskSpaceToReserve - Delete oldest images to avoid filling disk. How much byte to keep free on disk.
# cameraSettings     - "" = no extra settings; "-hf" = Set horizontal flip of image; "-vf" = Set vertical flip; "-hf -vf" = both horizontal and vertical flip
 
threshold = 100
sensitivity = 100
forceCapture = True
forceCaptureTime = 60 * 60 # Once an hour
filepath = "/home/pi/www/picam"
filenamePrefix = "capture"
diskSpaceToReserve = 40 * 1024 * 1024 # Keep 40 mb free on disk
cameraSettings = ""
 
 
# settings of the photos to save
# saveWidth   = 1296
# saveHeight  = 972
# saveQuality = 15 # Set jpeg quality (0 to 100)
 
# Test-Image settings
testWidth = 100
testHeight = 75
 
# this is the default setting, if the whole image should be scanned for changed pixel
testAreaCount = 1
testBorders = [ [[1,testWidth],[1,testHeight]] ]  # [ [[start pixel on left side,end pixel on right side],[start pixel on top side,stop pixel on bottom side]] ]
 
 
                                ### EMAIL CONFIGURATION  ###
 
TO = 'random@random.com'
SUBJECT = 'ALLARM'
TEXT = 'MOTION DETECTED'
 
#GMail Credential
 
gmail_sender = 'media2014services@gmail.com'
gmail_passwd = 'albertluca123'
 
 
 
server = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()
server.starttls()
server.ehlo
server.login(gmail_sender, gmail_passwd)
 
BODY = '\r\n'.join([
        'To: %s' %TO,
        'From: %s' %gmail_sender,
        'Subject: %s' % SUBJECT,
        '',
        TEXT
        ])
 
 
 
#server.quit()
 
 
                                ### FUNCTIONS CONFIGURATION  ###
 
 
# Capture a small test image (MOTION DETACTION)
 
def captureTestImage(settings, width, height):
    command = "raspistill %s -w %s -h %s -t 200 -e bmp -n -o -" % (settings, width, height)
    imageData = StringIO.StringIO()
    imageData.write(subprocess.check_output(command, shell=True))
    imageData.seek(0)
    im = Image.open(imageData)
    buffer = im.load()
    imageData.close()
    return im, buffer
 
 
# Save a full size image to disk
def saveImage(settings, width, height, quality, diskSpaceToReserve):
    keepDiskSpaceFree(diskSpaceToReserve)
    time = datetime.now()
    filename = filepath + "/" + filenamePrefix + "-%04d%02d%02d-%02d%02d%02d.jpg" % (time.year, time.month, time.day, time.hour, time.minute, time.second)
    subprocess.call("raspistill %s -w %s -h %s -t 200 -e jpg -q %s -n -o %s" % (settings, width, height, quality, filename), shell=True)
    print "Captured %s" % filename
 
 
# Get first image
image1, buffer1 = captureTestImage(cameraSettings, testWidth, testHeight)
 
 
# Reset last capture time
lastCapture = time.time()
 
 
 
 
 
                                   ### MOTION DETECTION ALGORITHM ###
 
 
debugMode = False # use during the TEST
 
cameraRecording = False;
count = 1;
 
while (True):
   
    # Get comparison image
    image2, buffer2 = captureTestImage(cameraSettings, testWidth, testHeight)
 
    # Count changed pixels
    changedPixels = 0
    detectMotion = False
   
    if (debugMode): # in debug mode, save a bitmap-file with marked changed pixels and with visible testarea-borders
        debugimage = Image.new("RGB",(testWidth, testHeight))
        debugim = debugimage.load()
 
    for z in xrange(0, testAreaCount): # = xrange(0,1) with default-values = z will only have the value of 0 = only one scan-area = whole picture
        for x in xrange(testBorders[z][0][0]-1, testBorders[z][0][1]): # = xrange(0,100) with default-values
            for y in xrange(testBorders[z][1][0]-1, testBorders[z][1][1]):   # = xrange(0,75) with default-values; testBorders are NOT zero-based, buffer1[x,y] are zero-based (0,0 is top left of image, testWidth-1,testHeight-1 is botton right)
 
                if (debugMode):
                    debugim[x,y] = buffer2[x,y]
                    if ((x == testBorders[z][0][0]-1) or (x == testBorders[z][0][1]-1) or (y == testBorders[z][1][0]-1) or (y == testBorders[z][1][1]-1)):
                        # print "Border %s %s" % (x,y)
                        debugim[x,y] = (0, 0, 255) # in debug mode, mark all border pixel to blue
                # Just check green channel as it's the highest quality channel
                pixdiff = abs(buffer1[x,y][1] - buffer2[x,y][1])
               
                if pixdiff > threshold:
                    changedPixels += 1
                    if (debugMode):
                        debugim[x,y] = (0, 255, 0) # in debug mode, mark all changed pixel to green
               
                if (changedPixels > sensitivity):
                   
                    detectMotion = True
               
                if ((debugMode == False) and (changedPixels > sensitivity)):
                    break  # break the y loop
            if ((debugMode == False) and (changedPixels > sensitivity)):
                break  # break the x loop
        if ((debugMode == False) and (changedPixels > sensitivity)):
            break  # break the z loop
 
    if (debugMode):
        debugimage.save(filepath + "/debug.bmp") # save debug image as bmp
        print "debug.bmp saved, %s changed pixel" % changedPixels
 
                               
 
 
                                ### VIDEO RECORDING ALGORITHM ###
 
 
    if forceCapture:
        if time.time() - lastCapture > forceCaptureTime:
            detectMotion = True
 
    if detectMotion:
        if (cameraRecording == False) :              
            print "MOTION DETECTED: START video"
            lastCapture = time.time()
            filename = filepath + "/" + "Video_" + "%d" % count
            count = count +1  
            cameraRecording = True
            subprocess.call("raspivid -o %s.mp4 -t 5000 -p 100,100,600,500" % filename, shell=True)
       
            cameraRecording = False
            
            try:
                server.sendmail(gmail_sender, [TO], BODY)
                print 'email sent'
            except:
                print 'error'