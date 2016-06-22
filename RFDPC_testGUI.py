#####################################################################################
#   PC interface for RFD900_Pi_V7 over the RFD900 Modem using a baudrate of 57600   #
#   to send photos and real time data. Constructed for MSGC Borealis program.       #
#                                                                                   #
#   Author: Dylan Trafford      Created: 1/19/2015     Python Version: 2.7.9        #
#                               Edited: 6/16/2015      OS = Windows 8.1             #
#####################################################################################



#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Library Imports

        #Used Libraries

import time                         # = native time functions (ex. runtime)
import datetime
import serial                       # = RS232 software serial modules on Rx Tx pins
import base64                       # = encodes an image in b64 Strings (and decodes)
import hashlib                      # = generates hashes
import subprocess
import sys
import PIL.Image                    # = for image processing
import ImageTk
from Tkinter import *
import tkMessageBox

        #Optional Libraries - Unused at current, can replace b64 encoding

from StringIO import StringIO       # = for additional functionality, see io library 
from array import array             # = for generating a byte array 
import os                           # = ?? was required for io module to convert Image to bytes
import io                           # = creating a String or Byte Array of data (streaming images)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Global Variable Initialization and Definitions

#Serial Variables
port = "COM22"              #This is a computer dependent setting. Open Device Manager to determine which port the RFD900 Modem is plugged into
baud = 38400
timeout = 3                 #Sets the ser.read() timeout period, or when to continue in the code when no data is received after the timeout period (in seconds)

#Initializations
ser = serial.Serial(port = port, baudrate = baud, timeout = timeout)
wordlength = 10000          #Variable to determine spacing of checksum. Ex. wordlength = 1000 will send one thousand bits before calculating and verifying checksum
imagedatasize = 10000
extension = ".png"
timeupdateflag = 0          #determines whether to update timevar on the camera settings

#Camera Variables
width = 650
height = 450
sharpness = 0               #Default  =0; range = (-100 to 100)
brightness = 50             #Default = 50; range = (0 to 100)
contrast = 0                #Default = 0; range = (-100 to 100)
saturation = 0              #Default = 0; range = (-100 to 100)
iso = 0                   #Unknown Default; range = (100 to 800)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Modules/Callbacks

def updateslider():
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    global timeupdateflag
    try:
        widthslide.set(width)
        heightslide.set(height)
        sharpnessslide.set(sharpness)
        brightnessslide.set(brightness)
        contrastslide.set(contrast)
        saturationslide.set(saturation)
        isoslide.set(iso)
    except:
        print "error setting slides to new values"
        print "here are current values"
        print width
        print height
        print sharpness
        print brightness
        print contrast
        print saturation
        print iso
        sys.stdout.flush()
    try:
        if (timeupdateflag == 1):
            timevar.set("Last Updated: "+str(datetime.datetime.now().strftime("%Y/%m/%d @ %H:%M:%S")))
            timeupdateflag = 0
        else:
            timevar.set("No Recent Update")
        widthvar.set("Current Width = "+str(width))
        heightvar.set("Current Height = " + str(height))
        sharpnessvar.set("Current Sharpness = " + str(sharpness))
        brightnessvar.set("Current Brightness = " + str(brightness))
        contrastvar.set("Current Contrast = " + str(contrast))
        saturationvar.set("Current Saturation = " + str(saturation))
        isovar.set("Current ISO = " + str(iso))
    except:
        print "error setting slides to new values"
        print "here are current values"
        print width
        print height
        print sharpness
        print brightness
        print contrast
        print saturation
        print iso
    return

def reset_cam():
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    width = 650
    height = 450
    sharpness = 0               #Default  =0; range = (-100 to 100)
    brightness = 50             #Default = 50; range = (0 to 100)
    contrast = 0                #Default = 0; range = (-100 to 100)
    saturation = 0              #Default = 0; range = (-100 to 100)
    iso = 400                   #Unknown Default; range = (100 to 800)
    print "Default width:",width
    print "Default height:",height
    print "Default sharpness:",sharpness
    print "Default brightness:",brightness
    print "Default contrast:",contrast
    print "Default saturation:",saturation
    print "Default ISO:",iso
    sys.stdout.flush()
    try:
        widthslide.set(width)
        heightslide.set(height)
        sharpnessslide.set(sharpness)
        brightnessslide.set(brightness)
        contrastslide.set(contrast)
        saturationslide.set(saturation)
        isoslide.set(iso)
    except:
        print "error setting slides to new values"
        print "here are current values"
        print width
        print height
        print sharpness
        print brightness
        print contrast
        print saturation
        print iso
        sys.stdout.flush()
    return
    


def image_to_b64(path):                                             #Converts an image into a base64 encoded String (ASCII characters)
    with open(path,"rb") as imageFile:
        return base64.b64encode(imageFile.read())

def b64_to_image(data,savepath):                                    #Back converts a base64 String of ASCII characters into an image, the save path dictates image format
    fl = open(savepath, "wb")
    fl.write(data.decode('base64'))
    fl.close()

def gen_checksum(data):
    return hashlib.md5(data).hexdigest()                            #Generates a 32 character hash up to 10000 char length String(for checksum). If string is too long I've notice length irregularities in checksum

def sync():                                                         #This is module to ensure both sender and receiver at that the same point in their data streams to prevent a desync
    print "Attempting to Sync - This should take approx. 2 sec"
    sync = ""
    addsync0 = ""
    addsync1 = ""
    addsync2 = ""
    addsync3 = ""
    while(sync != "sync"):                                          #Program is held until no data is being sent (timeout) or until the pattern 's' 'y' 'n' 'c' is found
        addsync0 = ser.read()
        addsync0 = str(addsync0)
        if(addsync0 == ''):
            break
        sync = addsync3 + addsync2 + addsync1 + addsync0
        addsync3 = addsync2
        addsync2 = addsync1
        addsync1 = addsync0
    sync = ""
    ser.write('S')                                                  #Notifies sender that the receiving end is now synced 
    print "System Match"
    ser.flushInput()
    ser.flushOutput()
    return

def receive_image(savepath, wordlength):
    print "confirmed photo request"                                 #Notifies User we have entered the receiveimage() module
    sys.stdout.flush()
    
    #Module Specific Variables
    trycnt = 0                                                      #Initializes the checksum timeout (timeout value is not set here)
    finalstring = ""                                                #Initializes the data string so that the += function can be used
    done = False                                                    #Initializes the end condition
    
    #Retreive Data Loop (Will end when on timeout)
    while(done == False):
        print "Current Recieve Position: ", str(len(finalstring))
        checktheirs = ""
        checktheirs = ser.read(32)                                  #Asks first for checksum. Checksum is asked for first so that if data is less than wordlength, it won't error out the checksum data
        word = ser.read(wordlength)                                 #Retreives characters, wholes total string length is predetermined by variable wordlength
        checkours = gen_checksum(word)                              #Retreives a checksum based on the received data string
        
        #CHECKSUM
        if (checkours != checktheirs):
            if(trycnt < 5):                                         #This line sets the maximum number of checksum resends. Ex. trycnt = 5 will attempt to rereceive data 5 times before erroring out                                              #I've found that the main cause of checksum errors is a bit drop or add desync, this adds a 2 second delay and resyncs both systems 
                ser.write('N')
                trycnt += 1
                print "try number:", str(trycnt)
                print "\tresend last"                                 #This line is mostly used for troubleshooting, allows user to view that both devices are at the same position when a checksum error occurs
                print "\tpos @" , str(len(finalstring))
                sys.stdout.flush()
                sync()                                              #This corrects for bit deficits or excesses ######  THIS IS A MUST FOR DATA TRANSMISSION WITH THE RFD900s!!!! #####
            else:
                ser.write('N')                                      #Kind of a worst case, checksum trycnt is reached and so we save the image and end the receive, a partial image will render if enough data
                finalstring += word                                 
                done = True
                break
        else:
            trycnt = 0
            ser.write('Y')
            finalstring += word
        if(word == ""):
            done = True
            break
        if(checktheirs == ""):
            done = True
            break
    try:                                                            #This will attempt to save the image as the given filename, if it for some reason errors out, the image will go to the except line
        b64_to_image(finalstring,savepath)
        imagedisplay.set(savepath)
    except:
        print "Error with filename, saved as newimage" + extension
        sys.stdout.flush()
        b64_to_image(finalstring,"newimage" + extension)            #Save image as newimage.jpg due to a naming error
    
    print "Image Saved"
    sys.stdout.flush()


def cmd1():     #Get Most Recent Photo
    global im
    global photo
    global tmplabel
    global reim
    ser.write('1')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        ser.write('1')
    #sync()
    sendfilename = ""
    temp = 0
    while(temp <= 14):
        sendfilename += str(ser.read())
        temp += 1
    #sendfilename = "image" + sendfilename +extension
    imagepath = imagename.get()
    if (imagepath == ""):
        try:
            if(sendfilename[0] == "i"):
                imagepath = sendfilename
            else:
                imagepath = "image_%s%s" % (str(datetime.datetime.now().strftime("%Y%m%d_T%H%M%S")),extension)
        except:
            imagepath = "image_%s%s" % (str(datetime.datetime.now().strftime("%Y%m%d_T%H%M%S")),extension)
    else:
        imagepath = imagepath+extension
            
    print "Image will be saved as:", imagepath
    tkMessageBox.showinfo("In Progress..",message = "Image request recieved.\nImage will be saved as "+imagepath)
    timecheck = time.time()
    sys.stdout.flush()
    receive_image(str(imagepath), wordlength)
    im = PIL.Image.open(str(imagepath))
    reim = im.resize((650,450),PIL.Image.ANTIALIAS)
    photo = ImageTk.PhotoImage(reim)
    tmplabel.configure(image = photo)
    tmplabel.pack(fill=BOTH,expand = 1)
    print "Receive Time =", (time.time() - timecheck)
    sys.stdout.flush()
    return

def cmd2():     #reguest imagedata.txt
    try:
        listbox.delete(0,END)
    except:
        print "Failed to delete Listbox, window may have been destroyed"
        sys.stdout.flush()
    ser.write('2')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        ser.write('2')
    #sync()
    try:
        datafilepath = datafilename.get()
        if (datafilepath == ""):
            datafilepath = "imagedata"
        file = open(datafilepath+".txt","w")
    except:
        print "Error with opening file"
        sys.stdout.flush()
        return
    timecheck = time.time()
    temp = ser.readline()
    while(temp != ""):
        file.write(temp)
        try:
            listbox.insert(0,temp)
        except:
            print "error adding items"
            break
        temp = ser.readline()
    file.close()
    print "File Recieved, Attempting Listbox Update"
    sys.stdin.flush()
    subGui.lift()
    subGui.mainloop()
    return

def cmd3():     #reguest specific image
    global im
    global photo
    global tmplabel
    global reim
    item = map(int,listbox.curselection())
    try:
        data = listbox.get(ACTIVE)
    except:
        print "Nothing Selected"
        sys.stdout.flush()
        return
    data = data[0:15]
    print data[10]
    if (data[10] != 'b'):
        tkMessageBox.askquestion("W A R N I N G",message = "You have selected the high resolution image.\nAre you sure you want to continue?\nThis download could take 15+ min.",icon = "warning")
        if 'yes':
            ser.write('3')
            while (ser.read() != 'A'):
                print "Waiting for Acknowledge"
                sys.stdout.flush()
                ser.write('3')
            sync()
            imagepath = data
            ser.write(data)
            timecheck = time.time()
            tkMessageBox.showinfo("In Progress...",message = "Image request recieved.\nImage will be saved as "+imagepath)
            print "Image will be saved as:", imagepath
            sys.stdout.flush()
            receive_image(str(imagepath), wordlength)
            im = PIL.Image.open(imagepath)
            reim = im.resize((650,450),PIL.Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(reim)
            tmplabel.configure(image = photo)
            tmplabel.pack(fill=BOTH,expand = 1)
            print "Receive Time =", (time.time() - timecheck)
            return
        else:
            return
            
    else:
        ser.write('3')
        while (ser.read() != 'A'):
            print "Waiting for Acknowledge"
            sys.stdout.flush()
            ser.write('3')
        sync()
        imagepath = data
        ser.write(data)
        timecheck = time.time()
        tkMessageBox.showinfo("In Progress...",message = "Image request recieved.\nImage will be saved as "+imagepath)
        print "Image will be saved as:", imagepath
        sys.stdout.flush()
        receive_image(str(imagepath), wordlength)
        im = PIL.Image.open(imagepath)
        reim = im.resize((650,450),PIL.Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(reim)
        tmplabel.configure(image = photo)
        tmplabel.pack(fill=BOTH,expand = 1)
        print "Receive Time =", (time.time() - timecheck)
        return

def cmd4(): #Retrieve current settings
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    global timeupdateflag
    print "Retrieving Camera Settings"
    try:
        killtime = time.time()+10
        ser.write('4')
        while ((ser.read() != 'A') & (time.time()<killtime)):
            print "Waiting for Acknowledge"
            ser.write('4')
        #sync()
        timecheck = time.time()
        #tkMessageBox.showinfo("In Progress..",message = "Downloading Settings")
        try:
            file = open("camerasettings.txt","w")
            print "File Successfully Created"
        except:
            print "Error with opening file"
            sys.stdout.flush()
            return
        timecheck = time.time()
        sys.stdin.flush()
        temp = ser.read()
        while((temp != "\r") & (temp != "") ):
            file.write(temp)
            temp = ser.read()
        file.close()
        print "Receive Time =", (time.time() - timecheck)
        sys.stdout.flush()
        file = open("camerasettings.txt","r")
        twidth = file.readline()             #Default = (650,450); range up to
        width = int(twidth)
        print "width = ",width
        theight = file.readline()             #Default = (650,450); range up to
        height = int(theight)
        print "height = ",height
        tsharpness = file.readline()              #Default  =0; range = (-100 to 100)
        sharpness = int(tsharpness)
        print "sharpness = ",sharpness
        tbrightness = file.readline()             #Default = 50; range = (0 to 100)
        brightness = int(brightness)
        print "brightness = ", brightness
        tcontrast = file.readline()               #Default = 0; range = (-100 to 100)
        contrast = int(tcontrast)
        print "contrast = ",contrast
        tsaturation = file.readline()             #Default = 0; range = (-100 to 100)
        saturation = int(tsaturation)
        print "saturation = ",saturation
        tiso = file.readline()                      #Unknown Default; range = (100 to 800)
        iso = int(tiso)
        print "iso = ",iso
        file.close()
        timeupdateflag = 1
        updateslider()
    except:
        print "Camera Setting Retrieval Error"
    return

def cmd5():     #upload new settings
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    width = widthslide.get()
    height = heightslide.get()
    sharpness = sharpnessslide.get()
    brightness = brightnessslide.get()
    contrast = contrastslide.get()
    saturation = saturationslide.get()
    iso = isoslide.get()
    file = open("camerasettings.txt","w")
    file.write(str(width)+"\n")
    file.write(str(height)+"\n")
    file.write(str(sharpness)+"\n")
    file.write(str(brightness)+"\n")
    file.write(str(contrast)+"\n")
    file.write(str(saturation)+"\n")
    file.write(str(iso)+"\n")
    file.close()
    
    ser.write('5')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        #sys.stdin.flush()
        ser.write('5')
    #sync()
    timecheck = time.time()
    #tkMessageBox.showinfo("In Progress..",message = "Downloading Settings")
    try:
        file = open("camerasettings.txt","r")
    except:
        print "Error with opening file"
        sys.stdout.flush()
        return
    timecheck = time.time()
    temp = file.readline()
    while(temp != ""):
        ser.write(temp)
        temp = file.readline()
    file.close()
    error = time.time()
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        if(error+10<time.time()):
            print "Acknowledge not received"
            return
    print "Send Time =", (time.time() - timecheck)
    sys.stdout.flush()
    return

def time_sync():
    #ser.flushInput()
    ser.write('T')
    termtime = time.time() + 20
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        ser.write('T')
        if (termtime < time.time()):
            print "No Acknowledge Recieved, Connection Error"
            sys.stdout.flush()
            return
    localtime = str(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    rasptime = str(ser.readline())
    print "##################################\nRaspb Time = %s\nLocal Time = %s\n##################################" % (rasptime,localtime)
    sys.stdin.flush()
    connectiontest(10)
    return

def connectiontest(numping):
    ser.write('6')
    termtime = time.time() + 20
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        ser.write('6')
        if (termtime < time.time()):
            print "No Acknowledge Recieved, Connection Error"
            sys.stdout.flush()
            return
    avg = 0
    ser.write('P')
    temp = ""
    for x in range (1,numping):
        sendtime = time.time()
        receivetime = 0
        termtime = sendtime + 10
        while ((temp != 'P')&(time.time()<termtime)):
            ser.write('P')
            temp = ser.read()
            receivetime = time.time()
        if (receivetime == 0):
            print "Connection Error, No return ping within 10 seconds"
            ser.write('D')
            sys.stdout.flush()
            return
        else:
            temp = ""
            avg += receivetime - sendtime
            #print (avg/x)
    ser.write('D')
    avg = avg/numping
    print "Ping Response Time = " + str(avg)[0:4] + " seconds"
    sys.stdout.flush()
    return

def cmd7():
    ser.write('7')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        ser.write('7')
    #sync()
    timecheck = time.time()
    try:
        file = open("piruntimedata.txt","w")
    except:
        print"Error with opening file"
        sys.stdout.flush()
        return
    timecheck = time.time()
    sys.stdin.flush()
    termtime = time.time()+60
    temp = ser.readline()
    while(temp !="\r"):
        file.write(temp)
        temp = ser.readline()
        if (termtime < time.time()):
            print "Error recieving piruntimedata.txt"
            file.close()
            return
    file.close()
    print "piruntimedata.txt saved to local folder"
    print "Receive Time =", (time.time() - timecheck)
    sys.stdout.flush()
    return

def enable_camera_a():
    ser.write('8')
    while (ser.read() != 'A'):
        print 'Waiting for Acknowledge'
        ser.write('8')
    timecheck = time.time()
    return

def enable_camera_b():
    ser.write('9')
    while (ser.read() != 'A'):
        print 'Waiting for Acknowledge'
        ser.write('9')
    timecheck = time.time()
    return

'''
def enable_camera_c():
    ser.write('c')
    while (ser.read() != 'A'):
        print 'Waiting for Acknowledge'
        ser.write('c')
    timecheck = time.time()
    return
'''
'''
def run_ISO_test():
    ser.write('c')
    while (ser.read() != 'A'):
        print 'Waiting for Acknowledge'
        ser.write('c')
    timecheck = time.time()
    return
'''

def decrease_wordlength():
    ser.write('b')
    while (ser.read() != 'A'):
        print 'Waiting for Acknowledge'
        ser.write('b')
    timecheck = time.time()
    return

def increase_wordlength():
    ser.write('c')
    while (ser.read() != 'A'):
        print 'Waiting for Acknowledge'
        ser.write('c')
    timecheck = time.time()
    return

#class Unbuffered:
#    def __init__(self,stream):
#        self.stream = stream
#    def write(self,data):
#        pass
#        self.stream.write(data)
#        self.stream.flush()
#        logfile.write(data)
#        logfile.flush()
#    def flush(self):
#        pass
#        self.stream.flush()
#    def close(self):
#        self.stream.close()

class Unbuffered:
    def __init__(self,stream):
        self.stream = stream
    def write(self,data):
        self.stream.write(data)
        self.stream.flush()
        logfile.write(data)
        logfile.flush()
    def flush(self):
        self.stream.flush()
    def close(self):
        self.stream.close()
    
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Main

#Initialize main Gui
mGui = Tk()
mGui.iconbitmap(default="bc.ico")
imagename = StringVar()
datafilename = StringVar()
imagedisplay = StringVar()
pingcount = StringVar()

widthvar = StringVar()
heightvar = StringVar()
sharpnessvar = StringVar()
brightnessvar = StringVar()
contrastvar = StringVar()
saturationvar = StringVar()
isovar = StringVar()
timevar = StringVar()
logfile = open('runtimedata.txt','w')
logfile.close()
logfile = open('runtimedata.txt','a')
sys.stdout = Unbuffered(sys.stdout)

##
##sys.stdout = open("runtimedata.txt","w")
##sys.stdout.close()
##sys.stdout = open("runtimedata.txt","a")
mGui.geometry("1300x550+30+30")
mGui.title("Montana Space Grant Consortium Borealis Program")

mlabel = Label(text = "RFD900 Interface V7.0", fg = 'grey', font = "Verdana 10 bold")
mlabel.pack()

cmdtitle = Label(text = "Command Module", font = "Verdana 12 bold")
cmdtitle.place(x=30,y=20)

imagetitle = Label(textvariable = imagedisplay, font = "Verdana 12 bold")
imagetitle.place(x=300,y=20)


frame = Frame(master = mGui,width =665,height=465,borderwidth = 5,bg="black",colormap="new")
frame.place(x=295,y=45)
im = PIL.Image.open("MSGC2.jpg")
reim = im.resize((650,450),PIL.Image.ANTIALIAS)
photo = ImageTk.PhotoImage(reim)
tmplabel = Label(master = frame,image = photo)
tmplabel.pack(fill=BOTH,expand = 1)

#-------------------------------------------
    #Cmd1 Gui - Request Most Recent Image
cmd1button = Button(mGui, text = "Most Recent Photo", command = cmd1)
cmd1button.place(x=150,y=65)

cmd1label = Label(text = "Image Save Name : Default = image_XXXX_b" + extension, font = "Verdana 6 italic")
cmd1label.place(x=10,y=50)

imagename = Entry(mGui, textvariable=imagename)
imagename.place(x=10,y=70)
#-------------------------------------------
    #Cmd2 Gui - Request text file on image data
cmd2button = Button(mGui, text = "Request 'imagedata.txt'", command = cmd2)
cmd2button.place(x=150, y=115)

datafilename = Entry(mGui, textvariable=datafilename)
datafilename.place(x=10,y=120)

cmd2label = Label(text = "Data File Save Name: Default = imagedata.txt", font = "Verdana 6 italic")
cmd2label.place(x=10,y=100)
#-------------------------------------------
    #Cmd3 Gui - Request specific image
subGui = Tk()
subGui.iconbitmap(default="bc.ico")
listbox = Listbox(subGui,selectmode=BROWSE, font = "Vernada 10")
subGuibutton = Button(subGui, text = "Request Selected Image", command = cmd3)
direction = Label(master=subGui,text = "Click on the image you would like to request", font = "Vernada 12 bold")
subGui.geometry("620x400+20+20")
subGui.title("Image Data and Selection")
direction.pack()
scrollbar = Scrollbar(subGui)
scrollbar.pack(side=RIGHT, fill = Y)
listbox.pack(side=TOP, fill = BOTH, expand = 1)
subGuibutton.pack()
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)
def subGuiconfirm():
    if tkMessageBox.askokcancel("W A R N I N G",message = "You cannot reopen this window.\n Are you sure you want to close it?",icon = "warning"):
        subGui.destroy()
subGui.protocol('WM_DELETE_WINDOW',subGuiconfirm)


#-------------------------------------------
    #Cmd4 and Cmd 5 Gui - Camera Settings
camedge = Frame(mGui,height = 330,width = 250,background = "black",borderwidth=3)
camedge.place(x=1000,y=50)
camframe = Frame(camedge, height = 50, width = 40)
camframe.pack(fill=BOTH,expand = 1)
#camframe.place(x=1000,y=50)

cambot = Frame(camframe,borderwidth = 1)
cambot.pack(side=BOTTOM,fill=X,expand =1)
camleft = Frame(camframe)
camleft.pack(side=LEFT,fill=BOTH,expand=2)
camright = Frame(camframe)
camright.pack(side=RIGHT,fill=BOTH,expand=2)

widthslide = Scale(camleft,from_=1, to=2592,orient=HORIZONTAL)
widthslide.set(width)
widthslide.pack()

widlabel = Label(master = camright,textvariable = widthvar, font = "Verdana 8")
widlabel.pack(pady=19)

heightslide = Scale(camleft,from_=1, to=1944, orient=HORIZONTAL)
heightslide.set(height)
heightslide.pack()
heilabel = Label(master = camright,textvariable = heightvar, font = "Verdana 8")
heilabel.pack(pady=5)

sharpnessslide = Scale(camleft,from_=-100, to=100,orient=HORIZONTAL)
sharpnessslide.set(sharpness)
sharpnessslide.pack()
shalabel = Label(master = camright,textvariable = sharpnessvar, font = "Verdana 8")
shalabel.pack(pady=18)

brightnessslide = Scale(camleft,from_=0, to=100,orient=HORIZONTAL)
brightnessslide.set(brightness)
brightnessslide.pack()
brilabel = Label(master = camright,textvariable = brightnessvar, font = "Verdana 8")
brilabel.pack(pady=5)

contrastslide = Scale(camleft,from_=-100, to=100,orient=HORIZONTAL)
contrastslide.set(contrast)
contrastslide.pack()
conlabel = Label(master = camright,textvariable = contrastvar, font = "Verdana 8")
conlabel.pack(pady=18)

saturationslide = Scale(camleft,from_=-100, to=100,orient=HORIZONTAL)
saturationslide.set(saturation)
saturationslide.pack()
satlabel = Label(master = camright,textvariable = saturationvar, font = "Verdana 8")
satlabel.pack(pady=5)

isoslide = Scale(camleft,from_=100, to=800,orient=HORIZONTAL)
isoslide.set(iso)
isoslide.pack()
isolabel = Label(master = camright,textvariable = isovar, font = "Verdana 8")
isolabel.pack(pady=18)

cmd4button = Button(cambot, text = "Get Current Settings", command = cmd4,borderwidth = 2,background = "white",font = "Verdana 10")
cmd4button.grid(row = 1,column = 1)

cmd5button = Button(cambot, text = "Send New Settings", command = cmd5,borderwidth = 2,background = "white",font = "Verdana 10")
cmd5button.grid(row = 1,column = 0)

defaultbutton = Button(cambot,text = "Default Settings",command = reset_cam,borderwidth = 2,background = "white",font = "Verdana 10",width = 20)
defaultbutton.grid(row = 0,columnspan = 2,pady=5)

timelabel = Label(master = mGui,textvariable=timevar,font="Verdana 8")
timelabel.place(x=1020,y=27)

updateslider()
#-------------------------------------------
    #Cmd 6 - Gui setup for connection testing

conbutton = Button(mGui,text = "Connection Test",command = time_sync,borderwidth = 2,font = "Verdana 10",width = 25)
conbutton.place(x=25,y=490)
#-------------------------------------------
    #Cmd 7 - Gui setup for raspberry runtime file retrieval

#pirunbutton = Button(mGui,text = "Download Pi Runtime Data",command = cmd7,borderwidth = 2,font = "Verdana 10",width = 25)
#pirunbutton.place(x=25,y=520)


# -----  camera select GUI parts  ---------  camera enable/mux options  -----


#          camera selection gui config
cam_select = Frame(mGui, height = 80, width = 290, background = "light gray", borderwidth = 3)
cam_select.place(x = 1005, y = 445)
select_label = Label(master = cam_select, font = "Verdana 10 bold", text = 'Camera Select:')
#select_label.place(x = 20, y = 2)
select_label.grid(row = 0, columnspan = 2, padx = 30)

# radio buttons
a_button = Radiobutton(master = cam_select, text = 'Camera A', value = 1, bg = 'light gray',
                       indicatoron = 0, command = enable_camera_a)
a_button.grid(row = 1, padx = 30)

b_button = Radiobutton(master = cam_select, text = 'Camera B', value = 2, bg = 'light gray',
                       indicatoron = 0, command = enable_camera_b)
b_button.grid(row = 2, padx = 30)

c_button = Radiobutton(master = cam_select, text = 'Inc. WL', value = 3, bg = 'light gray',
                       indicatoron = 0, command = increase_wordlength)
c_button.grid(row = 1, column = 1, padx = 30)

d_button = Radiobutton(master = cam_select, text = 'Dec. WL', value = 4, bg = 'light gray',
                       indicatoron = 0, command = decrease_wordlength)
d_button.grid(row = 2, column = 1, padx =30)

# END -----  camera enable/mux options and commands  -----

#-------------------------------------------
    #HERE WE GO!!!

rframe = Frame(mGui,height = 40, width = 35)
runlistbox = Listbox(rframe,selectmode=BROWSE, font = "Vernada 8",width=35,height=20)
runscrollbar = Scrollbar(rframe)
runlistbox.config(yscrollcommand=runscrollbar.set)
runscrollbar.config(command=runlistbox.yview)
runscrollbar.pack(side=RIGHT,fill=Y)
runlistbox.pack(side=LEFT,fill=Y)
rframe.place(x=10,y=165)

def callback():
    global runlistbox
    global mGui
    try:
        runlistbox.delete(0,END)
    except:
        print "Failed to delete Listbox"
    print str(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    sys.stdout.flush()
    for line in reversed(list(open("runtimedata.txt"))):
        runlistbox.insert(END,line.rstrip())
    mGui.after(5000,callback)
    return

def mGuicloseall():    
    subGui.destroy()
    mGui.destroy()
    ser.close()
    print "Program Terminated"
    sys.stdout.close()
    return
mGui.protocol('WM_DELETE_WINDOW',mGuicloseall)
mGui.after(1000,time_sync())
callback()
mGui.mainloop()

