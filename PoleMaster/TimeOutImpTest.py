# Prequistes (Should be included in image):
# SPI: https://github.com/lthiery/SPI-Py
# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
#Follow this link for set-up:
#https://pimylifeup.com/raspberry-pi-rfid-rc522/
#https://github.com/pimylifeup/MFRC522-python/tree/master/mfrc522

#Must be root or su!!!
###GLOBAL AND RESEVERES WARNING####
#global active, available
#global LockState
AdminKeys = [138561430561,"key 2 serial", "Key N serial"]
LockState = False
FirstTimeStartup = True
ServerParameters = ["hack"] #server prameters will be store as globs
url = "http://104.39.243.21:3000"
api_key = "940469cc-4f9e-445c-833c-54f7ad106011" ####BUG  obtained from adding scanner to redis-server
pin = ""


#
####LIGHT RING STRUCTURE IMPORT###====================================================================================
import time
import board
import neopixel
import threading
###LOGIC IMPORT###
import urllib
import sys
import os
import multiprocessing
#this is to read the serial number from the tag
###RFID IMPORT########
from time import sleep #check me
import sys
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
###SEVER IMPORT###
import requests



####SYSTEM LOGIC####==================================================================================================

# --------------CORE LOGIC-------------------------

def core():
    light(0)
    global FirstTimeStartup
    time.sleep(1.5)
    currentTag = SearchforTag(FirstTimeStartup)
    print("STATUS: Read tag " + str(currentTag))
    if boxLockCheck(currentTag) == True:
        main()

    critical, status, admit = SendToServer(currentTag,ServerParameters[0]) #bolean,string,bolean

    if critical:                                                        #may add Soft Reset Proceedure on multi-fail???
        print("WARNING: Crit Error from server reply:" + status)
        light(4)
        time.sleep(2)
        light(0)
        main()

    if admit == False:
        light(3)
        time.sleep(2) #add to in between all
        light(0)
        main()
    else:
        light(2)
        time.sleep(2)
        light(0)
        main()
## --------------STARTUP LOGIC-------------------------
def startUp(FirstTimeStartup):
    check = SearchforTag(FirstTimeStartup)
    if check == "-10000": #case return needs to be defined later  ##I did 10/24/19 maz
        print("STATUS: Setup Has concluded going into autonomous mode")
        restore() #X Not definded yet will load old config (10/20/19 completed -maz)
        light(2)
        return

    internet_test()
    meal = input("INPUT REQUIRED: Input what meal this is \n")
    #Events = GetMealEvents() #Not definded yet Daninels  or [andrew] job 10/24/19
    #Events = getEventLocation(meal) uncomit after done
    Events = meal

#       Print("INPUT REQUIRRED: \n")
#       Print("\n")

    print("STATUS: " + Events + " Slected") # some kind of graphical unpack will go here when we know what were dealing with

    #selection = input("INPUT REQUIRED: Select event ID as a ## number")


    #while True:
        #if selection in Events: ##needs fixed with more info

    print("STATUS: Config Choosen as " + Events)
    Con = input("INPUT REQUIRED: Confirm setup with any key, 'N' will abort all \n")
    if Con == "N":
        sys.exit()
    print("STATUS: Setup has concluded going into autonomous mode")
    #save slection parmeters to global
    global ServerParameters
    ServerParameters = [Events] ###BUG CHECK after we know paremeters #fixed but need rechecked 9/24/19
    #save slection with save() function
    Save()
        #break

 #       else:
 #           print("WARNING: Config " + selection + "Is not a valid selection")
 #           selection = input("INPUT REQUIRED: Select event ID as a ## number")

## --------------SAVE TO FILE--------------------------
#A function that will Creates or Edit a text file in the Present working dir. that takes no arguments but using the current global varible for server parameters
def Save():
    global ServerParameters
    Dir = os.getcwd()
    f = open(os.path.join(Dir, 'ServerParameters.txt'), 'w')
    f.write(str(ServerParameters))
    f.close()
## --------------LOAD FROM FILE-------------------------
#A function that will open and read a text file in the Present working dir. that returns nothing but will store the server parameters for current global varible
def Load():
    global ServerParameters
    Dir = os.getcwd()
    f = open(os.path.join(Dir, 'ServerParameters.txt'), 'r')
    out = f.read()
    ServerParameters = out.strip('][').split(', ')  ###MAJOR BUG### Needs a for loop for casting once we know what "parsmters" look like
    f.close()
    #print(ServerParameters)

## --------------RESTORE--------------------------------
def restore():
    Load()
    global FirstTimeStartup
    FirstTimeStartup = False
## --------------INTERNET CHECK-------------------------

def internet_test():

    print("STATUS: TESTING INTERNET")
    url = "http://google.com" #change to hack server
    try:
        urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        print("WARNING: " + e.reason)
        print("ERROR: Network Down, soft reset recommended")
        time.wait(1500)
        sys.exit()

    print("STATUS: Connection Pass, we can see " + url)


# --------------LOCK AND ADMIN-------------------------
#Function takes atributes rfidserial as a string and AdminKeys as a list of stings, Returns Bol of lock status
def boxLockCheck(RfidSerial):
    global AdminKeys, LockState
    if RfidSerial in AdminKeys:
        light(2)
        time.sleep(2)
        LockState = not LockState
        return True
    if LockState == True:
        light(3)
        time.sleep(1)
        return True
    else:
        return False


####END SYSTEM LOGIC####==============================================================================================

####SERVER LOGIC####=============================================================================++++=================

# --------------------------- GET EVENT LOCATION AND DATA--------------------------------

# function to get the event location if given a event title, used for the location in SendToServer
# We will probably want to run this at start, with something like getEventLocation("Lunch")
# all food events should return the same location unless its not all at the same place

def getEventLocation(eventTitle):
    foodLocation = 3
    Location_Website = url + "/scanner/events"
    # obtains the json data
    response = requests.get(Location_Website)
    data = response.json()

    # returns if status is error
    status = response.status_code
    if status < 200 or status > 299:
        print("ERROR: " + status)
        return 0

    # filtering what data to output
    body = data["locations"]
    for body in body:
        if body["event_title"] == eventTitle:
            # food[body["event_title"]] = body["uid"] #change this to choose what data to add to the output
            return body["event_location"]


# ----------------------------CORE INFORMATION TRANSMISSION-----------------------------

# function to check if the person has already has lunch or not
# insert the wid from scan and food event location to return whats needed
# NOTE - currently the only available location is 3 untill stan fixes it
def SendToServer(wid, location):
    Scan_Website = url + "/scanner/scan"
    arguments = {'wid': wid, 'location': location, 'apikey': api_key}
    critical = False
    admit = False

    # obtains the json data and code
    response = requests.post(Scan_Website, data=arguments)
    data = response.json()
    status = response.status_code

    # returns if status is error
    if status < 200 or status > 299:
        critical = True
        return critical, status, admit

    # if no error, admit checks isRepeat and returns
    admit = data["data"]["isRepeat"]
    return critical, status, admit


# if __name__ == "__main__":
#     location = getEventLocation("Lunch")
#
#     wid = 1695694065  # obtained from wristband scan
#     critical, status, admit = SendToServer(wid, 3)
#     print(critical)
#     print(status)
#     print(admit)
####END SERVER LOGIC####==============================================================================================


####RFID STRUCTURE####===============================================================================================

def SearchforTag(FirstTime):

    reader = SimpleMFRC522()

    # Try reading data from wrist band
    try:
        while True:
            count = 0
            id = 0
            while FirstTime:
                p = multiprocessing.Process(target=reader.read)# Start reader.read as a process
                p.start()
                p.join(10)# Wait for 10 seconds or until process finishes
                if p.is_alive(): # If thread is still active
                    print("running... let's kill it...")
                    p.terminate()  # Terminate
                    p.join()
                else:
                    #data = reader.read()
                    id = p[0]
                    time.sleep(1)
                    count =+ 1
                if id !=0:
                    return id
                if count == 10:
                    return "-10000"

            data = reader.read()
            id = data[0]
            if id:
               return id ##BUG ALLERT###  #figure out wich one we need? # reslolved 1/26/19 maz
    finally:
        GPIO.cleanup()

####END RFID STRUCTURE####===============================================================================================


####LIGHT RING STRUCTURE###===========================================================================================
# LED strip configuration:
LED_COUNT = 24  # Number of LED pixels.
LED_BRIGHTNESS = 10  # Set to 0 for darkest and 255 for brightest
#LED_CHANNEL = 0
# --------------Custom-------------------------

# Change D18 to D## if switching pins, I recommend using a pin with PWM
pixels = neopixel.NeoPixel(board.D18, LED_COUNT)

# used to check if there is an ongoing pattern and if the next pattern can be started
# essentially:
# 	> pattern starts
#	> active = true, available = false
#	> next pattern inputted
#	> active = false
#	> ongoing pattern will immediately return from their function
#	> available = true
#	repeat
active = False
available = True

# --------------Patterns-------------------------


# turns of the LED at i
def off(i):
    pixels[i] = (0, 0, 0)


# Set all pixels to the RGB color value
def setColor(red, green, blue):
    for i in range(LED_COUNT):
        pixels[i] = (red, green, blue)
    global available
    available = True



# Used if wait_ms is high, allows checking if active = true while sleeping
def sleepChecking(wait_ms):
    current = 0
    while active and current < wait_ms:
        time.sleep(10 / 1000)
        current += 10



# Displays a circular moving pattern of color
def circleColor(red, green, blue, wait_ms=50):
    # determines how many LED will be on and circulating
    start = 0
    end = 8

    # turns on the initial LED from start to end
    for j in range(LED_COUNT):
        off(j)
    for i in range(start + 1, end):
        pixels[i] = (red, green, blue)

    # afterwards, continue circulating the LED
    while active:
        if (start > LED_COUNT - 2):
            start = -1
        if (end > LED_COUNT - 2):
            end = -1
        start += 1
        end += 1
        pixels[end] = (red, green, blue)
        off(start)
        time.sleep(wait_ms / 1000.0)
    global available
    available = True


# Displays a breathing effect of color
def breathingColor(red, green, blue, wait_ms=50):
    brightness = 0
    increasing = True  # determines if brightness is increasing or decreasing
    while active:
        if brightness == LED_BRIGHTNESS: increasing = False
        if brightness == 0: increasing = True

        if increasing:
            brightness += 1
        else:
            brightness -= 1

        # Currently, only applies to blue since it is only for standby
        blue = brightness
        for i in range(LED_COUNT):
            pixels[i] = (red, green, blue)
        time.sleep(wait_ms / 1000.0)
    global available
    available = True


# Displays a blinking pattern of color
def blinkingColor(red, green, blue, wait_ms=1000):
    while active:
        for j in range(LED_COUNT):
            off(j)
        sleepChecking(wait_ms)
        for i in range(LED_COUNT):
            pixels[i] = (red, green, blue)
        sleepChecking(wait_ms)
    global available
    available = True

# --------------States----------------------------------​

# Displays Breathing Blue when on standby
def LED_standby():
    breathingColor(0, 0, LED_BRIGHTNESS)


# Displays circling Yellow when processing
def LED_processing():
    processing = True
    circleColor(LED_BRIGHTNESS, int(LED_BRIGHTNESS / 2), 0)
    processing = False


# Displays green when user is accepted
def LED_accepted():
    setColor(0, LED_BRIGHTNESS, 0)



# Displays red when user is denied
def LED_denied():
    setColor(LED_BRIGHTNESS, 0, 0)



# Displays blinking Yellow when an error occurs
def LED_error():
    blinkingColor(LED_BRIGHTNESS, int(LED_BRIGHTNESS / 2), 0)

# Turns all LED off and allows safe exit
def LED_exit():
    setColor(0, 0, 0)

# --------------Light Function-------------------------


# Signals
#    0 - standby
#    1 - processing
#    2 - accepted
#    3 - denied
#    4 - error
#	 5 - exit
def light(signal):
    switcher = {
        0: LED_standby,
        1: LED_processing,
        2: LED_accepted,
        3: LED_denied,
        4: LED_error,
        5: LED_exit
    }
    func = switcher.get(signal, LED_error)

    # explained at active and available insatiation, scroll up
    global active
    global available
    if active:
        active = False
        while not available:
            time.sleep(10 / 1000)
    active = True
    available = False
    t = threading.Thread(target=func, daemon=True)
    t.start()
    return

# ----------------------------------------------------

# testing
# if __name__ == '__main__':
#     print('Press Ctrl-C to quit.')
#     while True:
#         state = input()
#         light(int(state))
####END LIGHT RING STRUCTURE###===========================================================================================

###DAS MAIN####
def main():
    global FirstTimeStartup
    if FirstTimeStartup:
        startUp(FirstTimeStartup)
        FirstTimeStartup = False
    core()



def PLUS():
    print("""
                               .-----.
                             .'       `. 
                            :           :
                            :           :   ('-. .-.   ('-.               .-. .-')    _ (`-.   .-')                
                            '           '   ( OO )  /  ( OO ).-.           \  ( OO )  ( (OO  ) ( OO ).              
             |~        www   `.       .'    ,--. ,--.  / . --. /   .-----. ,--. ,--. _.`     \(_)---\_) ,--. ,--.   
            /.\       /#^^\_   `-/\--'      |  | |  |  | \-.  \   '  .--./ |  .'   /(__...--''/    _ |  |  | |  |   
           /#  \     /#%    \   /# \        |   .|  |.-'-'  |  |  |  |('-. |      /, |  /  | |\  :` `.  |  | | .-') 
          /#%   \   /#%______\ /#%__\       |       | \| |_.'  | /_) |OO  )|     ' _)|  |_.' | '..`''.) |  |_|( OO )
         /#%     \   |= I I ||  |- |        |  .-.  |  |  .-.  | ||  |`-'| |  .   \  |  .___.'.-._)   \ |  | | `-' / 
         ~~|~~~|~~   |_=_-__|'  |[]|        |  | |  |  |  | |  |(_'  '--'\ |  |\   \ |  |     \       /('  '-'(_.-'  
           |[] |_______\__|/_ _ |= |`.      `--' `--'  `--' `--'   `-----' `--' '--' `--'      `-----'   `-----'  
    ^V^    |-  /= __   __    /-\|= | :;
           |= /- /\/  /\/   /=- \.-' :;        _____                                  ______            __   ______          __ 
           | /_.=========._/_.-._\  .:'       / ___/____  ____  ____  ____  __  __   / ____/___  ____  / /  / ____/___  ____/ /__
           |= |-.'.- .'.- |  /|\ |.:'         \__ \/ __ \/ __ \/ __ \/ __ \/ / / /  / /   / __ \/ __ \/ /  / /   / __ \/ __  / _ \ 
           \  |=|:|= |:| =| |~|~||'|         ___/ / /_/ / /_/ / /_/ / /_/ / /_/ /  / /___/ /_/ / /_/ / /  / /___/ /_/ / /_/ /  __/ 
            |~|-|:| -|:|  |-|~|~||=|   ^V^  /____/ .___/\____/\____/ .___/\__, /   \____/\____/\____/_/   \____/\____/\__,_/\___/ 
            |=|=|:|- |:|- | |~|~|| |            /_/               /_/    /____/                                                        
            | |-_~__=_~__=|_^^^^^|/___
            |-(=-=-=-=-=-(|=====/=_-=/\.             Fall 2019 Alpha Release 1.0 - Point Of Location for Eating (POLE)
            | |=_-= _=- _=| -_=/=_-_/__\.
            | |- _ =_-  _-|=_- |]#| I II                        Technology Director - Julia M McCarthy
            |=|_/ \_-_= - |- = |]#| I II                       RFID Project Lead - Michael S Maslakowski
            | /  _/ \. -_=| =__|]!!!I_II!!                    
           _|/-'/  ` \_/ \|/' _ ^^^^`.==_^.                                   RFID Team:
         _/  _/`-./`-; `-.\_ / \_'\`. `. ===`.                  Andrew Feng (Light Ring/Network Logic)
        / .-'  __/_   `.   _/.' .-' `-. ; ====;\.                  Divya Rustagi (RFID Interpriter)
       /.   `./    \ `. \ / -  /  .-'.' ====='  >                    Daniel Melo Cruz (Debugging)
      /  \  /  .-' `--.  / .' /  `-.' ======.' /               Michael S Maslakowski (Core/Startup/Main)

========================================================================================================================================
    """)
if __name__ == '__main__':
    PLUS()
    main()


# print(" ('-. .-.   ('-.               .-. .-')    _ (`-.   .-')                ")
# print("( OO )  /  ( OO ).-.           \  ( OO )  ( (OO  ) ( OO ).              ")
# print(",--. ,--.  / . --. /   .-----. ,--. ,--. _.`     \(_)---\_) ,--. ,--.   ")
# print("|  | |  |  | \-.  \   '  .--./ |  .'   /(__...--''/    _ |  |  | |  |   ")
# print("|   .|  |.-'-'  |  |  |  |('-. |      /, |  /  | |\  :` `.  |  | | .-') ")
# print("|       | \| |_.'  | /_) |OO  )|     ' _)|  |_.' | '..`''.) |  |_|( OO )")
# print("|  .-.  |  |  .-.  | ||  |`-'| |  .   \  |  .___.'.-._)   \ |  | | `-' /")
# print("|  | |  |  |  | |  |(_'  '--'\ |  |\   \ |  |     \       /('  '-'(_.-' ")
# print("`--' `--'  `--' `--'   `-----' `--' '--' `--'      `-----'   `-----'    ")
#
#
#
# print("""
#                            .-----.
#                          .'       `.
#                         :           :
#                         :           :   ('-. .-.   ('-.               .-. .-')    _ (`-.   .-')
#                         '           '   ( OO )  /  ( OO ).-.           \  ( OO )  ( (OO  ) ( OO ).
#          |~        www   `.       .'    ,--. ,--.  / . --. /   .-----. ,--. ,--. _.`     \(_)---\_) ,--. ,--.
#         /.\       /#^^\_   `-/\--'      |  | |  |  | \-.  \   '  .--./ |  .'   /(__...--''/    _ |  |  | |  |
#        /#  \     /#%    \   /# \        |   .|  |.-'-'  |  |  |  |('-. |      /, |  /  | |\  :` `.  |  | | .-')
#       /#%   \   /#%______\ /#%__\       |       | \| |_.'  | /_) |OO  )|     ' _)|  |_.' | '..`''.) |  |_|( OO )
#      /#%     \   |= I I ||  |- |        |  .-.  |  |  .-.  | ||  |`-'| |  .   \  |  .___.'.-._)   \ |  | | `-' /
#      ~~|~~~|~~   |_=_-__|'  |[]|        |  | |  |  |  | |  |(_'  '--'\ |  |\   \ |  |     \       /('  '-'(_.-'
#        |[] |_______\__|/_ _ |= |`.      `--' `--'  `--' `--'   `-----' `--' '--' `--'      `-----'   `-----'
# ^V^    |-  /= __   __    /-\|= | :;
#        |= /- /\/  /\/   /=- \.-' :;        _____                                  ______            __   ______          __
#        | /_.=========._/_.-._\  .:'       / ___/____  ____  ____  ____  __  __   / ____/___  ____  / /  / ____/___  ____/ /__
#        |= |-.'.- .'.- |  /|\ |.:'         \__ \/ __ \/ __ \/ __ \/ __ \/ / / /  / /   / __ \/ __ \/ /  / /   / __ \/ __  / _ \
#        \  |=|:|= |:| =| |~|~||'|         ___/ / /_/ / /_/ / /_/ / /_/ / /_/ /  / /___/ /_/ / /_/ / /  / /___/ /_/ / /_/ /  __/
#         |~|-|:| -|:|  |-|~|~||=|   ^V^  /____/ .___/\____/\____/ .___/\__, /   \____/\____/\____/_/   \____/\____/\__,_/\___/
#         |=|=|:|- |:|- | |~|~|| |            /_/               /_/    /____/
#         | |-_~__=_~__=|_^^^^^|/___
#         |-(=-=-=-=-=-(|=====/=_-=/\
#         | |=_-= _=- _=| -_=/=_-_/__\
#         | |- _ =_-  _-|=_- |]#| I II
#         |=|_/ \_-_= - |- = |]#| I II
#         | /  _/ \. -_=| =__|]!!!I_II!!
#        _|/-'/  ` \_/ \|/' _ ^^^^`.==_^.
#      _/  _/`-./`-; `-.\_ / \_'\`. `. ===`.
#     / .-'  __/_   `.   _/.' .-' `-. ; ====;\
#    /.   `./    \ `. \ / -  /  .-'.' ====='  >
#   /  \  /  .-' `--.  / .' /  `-.' ======.' /
# """)
