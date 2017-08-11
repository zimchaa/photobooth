#!/usr/bin/env python
# modified by jaison.miller@gmail.com
# original by chris@drumminhands.com
# see original instructions at http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/

# Modified for my buddy Bronek's wedding - adding more personal graphics and driving a printer from the platform as well.
# I've removed the tumblr upload and gif processing, and changed it to a colour capture.
# I'm also using the explorerhat and flotilla from Pimoroni to provide button processing and appropriate lighting.
# I like Chris's underlaying design because it actually uses picamera and a clear config file - I'll be extending on the usage of that to help with printing etc.

# 2017-08-09 - making some updates to allow the setup to tweet the final pictures
# using code from my tweetycamera thingy

import os
#import glob
import time
import traceback
from time import sleep
import picamera # http://picamera.readthedocs.org/en/release-1.4/install2.html
from multiprocessing import Process
import atexit
import sys
import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
import config # this is the config python file config.py
#from signal import alarm, signal, SIGALRM, SIGKILL
# import explorerhat
import flotilla


########################
### Variables Config ###
########################

total_pics = 4 # number of pics to be taken
capture_delay = 3 # delay between pics
prep_delay = 4 # number of seconds at step 1 as users prep to have photo taken
restart_delay = 3 # how long to display finished message before beginning a new session
tweet_on = 1

# full frame of v1 camera is 2592x1944. Wide screen max is 2592,1555
# if you run into resource issues, try smaller, like 1920x1152. 
# or increase memory http://picamera.readthedocs.io/en/release-1.12/fov.html#hardware-limits
high_res_w = 1024 # width of high res image, if taken
high_res_h = 768 # height of high res image, if taken

single_res_w = 1640
single_res_h = 1232

#############################
### Variables that Change ###
#############################
# Do not change these variables, as the code will change it anyway
transform_x = config.monitor_w # how wide to scale the jpg when replaying
transfrom_y = config.monitor_h # how high to scale the jpg when replaying
offset_x = 0 # how far off to left corner to display photos
offset_y = 0 # how far off to left corner to display photos
replay_delay = 1 # how much to wait in-between showing pics on-screen after taking
replay_cycles = 2 # how many times to show each photo on-screen after taking

####################
### Other Config ###
####################
real_path = os.path.dirname(os.path.realpath(__file__))

# initialise flotilla - rainbow on the second port - will error if this is not connected
client = flotilla.Client(
  requires={
		'one': flotilla.Touch,
		'two': flotilla.Rainbow
  })

while not dock.ready:
    pass

touch = dock.first(flotilla.Touch)
rainbow = dock.first(flotilla.Rainbow)  

# initialize pygame
pygame.init()
pygame.display.set_mode((config.monitor_w, config.monitor_h))
screen = pygame.display.get_surface()
pygame.display.set_caption('Photo Booth Pics')
pygame.mouse.set_visible(False) #hide the mouse cursor
pygame.display.toggle_fullscreen()

#################
### Functions ###
#################

# clean up running programs as needed when main program exits
def cleanup():
  print('Ended abruptly')
  clear_screen()
  pygame.display.quit()
  pygame.quit()
  client.stop() # cleanup flotilla
  sys.exit()
  
atexit.register(cleanup)

# set variables to properly display the image on screen at right ratio
def set_demensions(img_w, img_h):
	# Note this only works when in booting in desktop mode. 
	# When running in terminal, the size is not correct (it displays small). Why?

    # connect to global vars
    global transform_y, transform_x, offset_y, offset_x

    # based on output screen resolution, calculate how to display
    ratio_h = (config.monitor_w * img_h) / img_w 

    if (ratio_h < config.monitor_h):
        #Use horizontal black bars
        #print "horizontal black bars"
        transform_y = ratio_h
        transform_x = config.monitor_w
        offset_y = (config.monitor_h - ratio_h) / 2
        offset_x = 0
    elif (ratio_h > config.monitor_h):
        #Use vertical black bars
        #print "vertical black bars"
        transform_x = (config.monitor_h * img_w) / img_h
        transform_y = config.monitor_h
        offset_x = (config.monitor_w - transform_x) / 2
        offset_y = 0
    else:
        #No need for black bars as photo ratio equals screen ratio
        #print "no black bars"
        transform_x = config.monitor_w
        transform_y = config.monitor_h
        offset_y = offset_x = 0

    # uncomment these lines to troubleshoot screen ratios
#     print str(img_w) + " x " + str(img_h)
#     print "ratio_h: "+ str(ratio_h)
#     print "transform_x: "+ str(transform_x)
#     print "transform_y: "+ str(transform_y)
#     print "offset_y: "+ str(offset_y)
#     print "offset_x: "+ str(offset_x)

# display one image on screen
def show_image(image_path):

	# clear the screen
	screen.fill( (0,0,0) )

	# load the image
	img = pygame.image.load(image_path)
	img = img.convert() 

	# set pixel dimensions based on image
	set_demensions(img.get_width(), img.get_height())

	# rescale the image to fit the current display
	img = pygame.transform.scale(img, (transform_x,transfrom_y))
	screen.blit(img,(offset_x,offset_y))
	pygame.display.flip()

# display a blank screen
def clear_screen():
	screen.fill( (0,0,0) )
	pygame.display.flip()

# display a group of images
def display_pics(jpg_group, total_pics):
    for i in range(0, replay_cycles): #show pics a few times
		for i in range(1, total_pics+1): #show each pic
			show_image(config.file_path + jpg_group + "-0" + str(i) + ".jpg")
			time.sleep(replay_delay) # pause 
				
def generate_montage(jpg_group):

    montage_cmd = "montage " + config.file_path + jpg_group + "-0[1234].jpg -gravity center -background silver +polaroid -background white -geometry '1x1-60-100<' -shadow -tile 2x " + config.file_path + "montages/montage_" + jpg_group + "_raw.jpg"
    print(montage_cmd)

    composite_cmd = "composite -gravity center " + config.file_path + "miller20th_centre_frame.jpeg " + config.file_path + "montages/montage_" + jpg_group + "_raw.jpg " + config.file_path + "montages/montage_" + jpg_group + "_final.jpg"
    print(composite_cmd)
    
    lineprint_cmd = "lpr " + config.file_path + "montages/montage_" + jpg_group + "_final.jpg"
    print(lineprint_cmd)

    os.system(montage_cmd) #make the raw montage
    os.system(composite_cmd) #add the finishing touches
    os.system(lineprint_cmd) #print the resulting image!
 
    print "Done with file processing!!!"    
    
def generate_single(jpg_group):
        
    # montage_cmd = "montage " + config.file_path + jpg_group + "-0[1234].jpg -gravity center -background silver +polaroid -background white -geometry '1x1-60-100<' -shadow -tile 2x " + config.file_path + "montages/montage_" + jpg_group + "_raw.jpg"
    # print(montage_cmd)
        
    composite_cmd = "composite -gravity SouthEast " + config.file_path + "miller20th_centre_frame.jpeg " + config.file_path + jpg_group + "-01.jpg " + config.file_path + "montages/montage_" + jpg_group + "_final.jpg"
    print(composite_cmd)
                        
    lineprint_cmd = "lpr " + config.file_path + "montages/montage_" + jpg_group + "_final.jpg"
    print(lineprint_cmd)
                        
    # os.system(montage_cmd) #make the raw montage
    os.system(composite_cmd) #add the finishing touches
    os.system(lineprint_cmd) #print the resulting image!
                
    print "Done with file processing!!!"

# define the photo taking function for when the big button is pressed 
def start_photobooth(total_pics, tweet_on): 

	################################# Begin Step 1 #################################
	
	print "Get Ready!"
	print("total_pics: " + total_pics)
	print("tweet_on: " + tweet_on)
	
	# GPIO.output(led_pin,False);
	#if pin.name == "one":
		# red button pressed
        # explorerhat.output[0].pulse(1, 1, 1, 0)
		#print "red button pressed"
		#total_pics = 4
	#if pin.name == "three":
		# blue button pressed
		# explorerhat.output[1].pulse(1, 1, 1, 0)
		#print "blue button pressed"
		#total_pics = 1

	show_image(real_path + "/instructions.png")
	sleep(prep_delay)
	
	# clear the screen
	# clear_screen()
	
	camera = picamera.PiCamera()  
	camera.vflip = True
	# camera.hflip = False # flip for preview, showing users a mirror image
	# camera.saturation = -100 # comment out this line if you want color images
	# camera.iso = config.camera_iso
	
	pixel_width = 0 # local variable declaration
	pixel_height = 0 # local variable declaration
	
	# if pin.name == "one":
	if total_pics == 4
		# montage mode
		print("montage mode!")
		camera.resolution = (high_res_w, high_res_h) # set camera resolution to high res
	
	# if pin.name == "three":
	if total_pics == 1
		# single mode
		print("single mode!")
		camera.resolution = (single_res_w, single_res_h)	

	camera.awb_mode = 'incandescent'
    	# Start off with ridiculously low gains
    	##rg, bg = (1.8, 1.2)
    	#camera.awb_gains = (rg, bg)

	################################# Begin Step 2 #################################
	
	print "Taking Picture!"
	
	now = time.strftime("%Y-%m-%d-%H-%M-%S") #get the current date and time for the start of the filename
	
	if config.capture_count_pics:
		try: # take the photos
			for i in range(1,total_pics+1):
				# camera.stop_preview()
				# camera.hflip = False # preview a mirror image
				show_image(real_path + "/pose" + str(i) + ".png")
				camera.stop_preview()
				time.sleep(capture_delay) # pause in-between shots
				# clear_screen()
				camera.start_preview()
				time.sleep(2) #warm up camera
				#GPIO.output(led_pin,True) #turn on the LED
				filename = config.file_path + now + '-0' + str(i) + '.jpg'
                rainbow.set_all(255,255,255).update() # camera flash
				camera.capture(filename)
                rainbow.set_all(0,0,0).update() # camera unflash
				# print "Captured Picture!"
				print(filename)
				#GPIO.output(led_pin,False) #turn off the LED
				#camera.stop_preview()
				#show_image(real_path + "/pose" + str(i) + ".png")
				#time.sleep(capture_delay) # pause in-between shots
				#clear_screen()
				if i == total_pics+1:
					break
		finally:
			camera.close()
		
	########################### Begin Step 3 #################################
	
	# input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	
	show_image(real_path + "/processing.png")
	
	########################### Begin Step 4 #################################
	
	# input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	
	try:
		# if pin.name == "one":
		if total_pics == 4
			print "printing montage"
			# proc_gen_montage = Process(target = generate_montage, args = (now,))
     			# proc_gen_montage.start()
			generate_montage(now)
		       
		# if pin.name == "three":
		if total_pics == 1
			print "printing single"
			# proc_gen_single = Process(target = generate_single, args = (now,))
                        # proc_gen_single.start()
			generate_single(now)

		display_pics(now, total_pics)
	except Exception, e:
		tb = sys.exc_info()[2]
		traceback.print_exception(e.__class__, e, tb)
		pygame.quit()
		
	print "Done"
	
	show_image(real_path + "/finished2.png")
	
	# turn off the blinking buttons
	# explorerhat.output[0].off()
	# explorerhat.output[1].off()

	time.sleep(restart_delay)
	show_image(real_path + "/intro.png");
	# GPIO.output(led_pin,True) #turn on the LED

####################
### Main Program ###
####################

print "Photo booth app running..." 

show_image(real_path + "/intro.png");

# explorerhat.input.on_low(start_photobooth, 1000)
# explorerhat.touch.pressed(start_photobooth)

try:
    while True:
        if touch.one:
            print("1 tocuhed, do single photo with tweet")
			      start_photobooth(1, 1)
        if touch.two:
            print("2 touched, do single photo without tweet")
			      start_photobooth(1, 0)
        if touch.three:
			      print("3 touched, do 4 photo without tweet")
			      start_photobooth(4, 0)
        if touch.four:
            print("4 touched, do 4 photo with tweet")
			      start_photobooth(4, 1)

# explorerhat.pause()

