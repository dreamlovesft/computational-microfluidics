####### script for microfluidic analysis of dinoflagellate eukaryotes using openCV & python
import os
import numpy as np
import cv2

#rhocut=3
#lines with a rho value below this number will not be considered lines, this is to get rid of the wall, the wall usually corresponds to -1<rho<3, but this could change between days or even sets of images on the same day if the chip/stage moves
horizontalcut=.02  #how close a line needs to be to pi/2 to be considered a line, we only want horizontal lines and this is one way to require that, this seems to work well and probably won't need to be adjusted
linethickness=5  #how thick each line is, if you get two lines through the same cell this should probably be increased unless the increase causes you to miss cells, increasing this will make it more likely you identify noise as a line
pixreqd=60  #how many pixels need to be lit up along a line before it is counted as a line, needs to be changed in conjunction with line thickness because a 5x60 checkerboard will be counted as a line so by increasing this you are more likely to cut noise

#at higher flowrates it may help to increase both linethickness and pixreqd
#note that at a thickness of 2+ the program will recognize a checkboard pattern as a line, meaning you do not need 2 continuous rows of pixels, but just 2 rows where each column has at least one pixel illuminated

invfilter=220  #this will cut out the brightest pixels because when you subtract the image you get mostly insanely bright pixels, pixels above this number are zeroed
binaryfilter=50  #this will cut everything below this pixel value to zero

# at higher flowrates it may help to reduce the invfilter and decrease the binary filter

rootdir = ''  # where the images I want to analyze are
resultfolder = os.path.split(rootdir)[0] + '/analysis images/'    #create the filepath for my analysis folder
os.makedirs(resultfolder)                           # make a folder in the directory above called analysis images

background = cv2.imread('')  #background image used to subtract from others, note this may need to be changed for experiments run on different days or possibly even between different recordings on the same day for the same pressure if the stage or the chip moves even a little bit
#use the two lines below in conjunction with lines 47-49 to look at the filtered images the program is trying to draw lines on
#thresholdfolder = os.path.split(rootdir)[0] + '/cleanedup images/'     #make a folder to look at the images the program is trying to draw lines from
os.makedirs(thresholdfolder)                           # make a folder in the directory above called analysis images

streaks=0               #keep track of how many streaks we've seen
pic = 0                 #we will use this to keep track of which picture we are on
lastrhos=[]                   #intialize empty matrix to store rho values for the last picture that had a line in it
currentrhos=[]              #intialize empty matrix to store rho values for current file
doublecount = 0         #keep track of how many streaks we've counted twice
for subdir, dirs, files in os.walk(rootdir):        #loop over all files in rootdir
    for file in files:                              # for each file do this

        pic+=1          #keep track of which picture we are on
        foundline = False       #we have not yet found a line in this file
        img = cv2.imread(os.path.join(rootdir,file))        # get image

        if img is not None:     #make sure the file is something
            newimg = img-background         #subtract the background
            gray = cv2.cvtColor(newimg,cv2.COLOR_BGR2GRAY)         # convert to grayscale
            #consider blurring here
            im_thresholded = cv2.threshold(gray, invfilter, 255, cv2.THRESH_TOZERO_INV)[1]  #get rid of super bright pixels, for some reason there are tons after the subtraction
            im_thresholded2 = cv2.threshold(im_thresholded, binaryfilter, 255, cv2.THRESH_BINARY)[1]    #get rid of dim background, make cut out some streaks if they are too dim but adjust cut with binaryfilter

            #uncomment lines 47-49 and lines 24-25 if you want to see the filtered images the program is looking at to find lines, note this will save them ALL you may want to do this if you play with the two filter variables at the top
#            threshfile = os.path.splitext(file)[0]+'_threshedge.jpg' # get original file name and add _threshedge
#            threshfile = os.path.join(thresholdfolder,threshfile)  # put the files in the threshold folder
#            cv2.imwrite(threshfile,im_thresholded2)          # write the image

            lines = []      #make sure the array we store the lines in is empty
            lines = cv2.HoughLines(im_thresholded2,linethickness,np.pi/60,pixreqd)      #fill the array with suspected lines

            if lines is not None:       #make sure there is something in the array
                for rho,theta in lines[:,0,:]: #loop over all the suspected lines and make sure they are good and then draw them  #any matrix, row=0, any column
                    if (np.pi/2-horizontalcut)<theta<(np.pi/2+horizontalcut):#      #theta cuts to only horizontal lines
                        foundline = True        #if the program gets here it means there is a line in the image that fits our criteria

                        #print "Pic:   "+str(pic)+"    "+"rho:   "+str(rho)
                        #the following lines turn the matrix element found with HoughLines into an actual line we can plot
                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a*rho
                        y0 = b*rho
                        x1 = int(x0 + 1000*(-b))
                        y1 = int(y0 + 1000*(a))
                        x2 = int(x0 - 1000*(-b))
                        y2 = int(y0 - 1000*(a))

                        #cv2.line(im_thresholded2,(x1,y1),(x2,y2),(0,200,0),1)  #draw the line we've found on our filtered image

                        cv2.line(img,(x1,y1),(x2,y2),(0,200,0),1) #draw the line we've found on our real image  #(img,draw line through pts 1to2,,(red,green,blue),thickness)

                        streaks+=1                              # keep track of flashes, every line is a flash hopefully

                        for j in lastrhos:      #loop over all the lines found in the last picture that had a streakline
                            if (pic-1)==lastline and (j-linethickness)<=rho<=(j+linethickness): #if the last picture had a line that has a neighboring rho value it is a doublecount, not that rho comes in increments of linethickness so if linethickness is 5, rho will go 2.5, 7.5, 12.5...
                                doublecount+=1         #keep track of how many doublecounts we have to subtract them
                                print "doublecount pictures:  "+str(pic-1)+"   "+str(pic)   #this line prints which pictures have the same cell in them, you can comment it out but its good for troubleshooting and making sure everythign is going fine
                        currentrhos.append(rho)     #add this rho to the list of rhos in this picture

                #in the lines below we are switching from the old "lastpic" to the new "lastpic"
                if foundline==True:     #if we found a line that meets our criteria in this image
                    lastline=pic        #this image becomes the last one we've found a line in
                    lastrhos=[]         #clear the old list of rhos from the previous last image we found lines in
                    lastrhos=currentrhos    #update the array of rhos for the last image we found rhos in with the current pictures rhos

#                        if (pic-1)==lastline and (lastrho-1)<=rho<=(lastrho+1):
#                            doublecount+=1
#                        lastline = pic
#                        lastrho = rho

                if foundline:                                   # only put new file in analysis folder if line was drawn
                    linefile = os.path.splitext(file)[0]+'_lines.jpg' # get original file name and add _lines to the new image with lines
                    linefile = os.path.join(resultfolder,linefile)  # create the correct filepath to put them in the new analysis folder
                    cv2.imwrite(linefile,img)          # write the image
        currentrhos=[]      #clear the array of rhos for the current image because we are going to the next one
    #                cv2.imwrite(threshfile,im_thresholded)          # write the image

print "streaks ="+str(streaks)      #print total number of streaks found
print "unique streaks ="+str(streaks-doublecount)       #print the number of streaks that correspond to unique cells
