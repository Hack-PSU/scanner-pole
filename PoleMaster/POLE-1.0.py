# Prequistes (Should be included in image):
# SPI: https://github.com/lthiery/SPI-Py
# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
#Follow this link for set-up:
#https://pimylifeup.com/raspberry-pi-rfid-rc522/
#https://github.com/pimylifeup/MFRC522-python/tree/master/mfrc522

#Must be root or su!!!# PREREQUISITES (Should be included in image):
#=====FOR LIGHT RING========
# SPI: https://github.com/lthiery/SPI-Py
# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
#=====FOR RFID MODULE========
#  https://pimylifeup.com/raspberry-pi-rfid-rc522/
# https://github.com/pimylifeup/MFRC522-python/tree/master/mfrc522

###MUST RUN AS SU OR ROOT!!!!!!!

####IMPORTS####==============================================================================================
###LIGHT RING IMPORT###
import time
import board
import neopixel
import threading
###LOGIC IMPORT###
import urllib
import sys
import os
import multiprocessing
###RFID IMPORT########
from time import sleep
import sys
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
###SEVER IMPORT###
import requests
import configparser

####GLOBAL AND RESEVERES WARNING####
# global active, available
# global LockState
AdminKeys = [138561430561, "key 2 serial", "Key N serial"] #Insert Admin token IDs in here
LockState = False
FirstTimeStartup = True
ServerParameters = ["Lunch"]  # server prams will be store as globs, not currently implemented
url = "http://130.203.168.83:3000" #address for redis
#http://104.39.243.21:3000
api_key = "e44c5a46-d404-401d-8e55-cfa4a0ff71c2"  ####API key is curently obtained through a config file I don't belive this is used right now
pin = "1633"
config = configparser.ConfigParser()
config.read("config.ini")

###OUTLINE###===============================================================================================
"""
# PREREQUISITES 
==IMPORTS
----###LIGHT RING IMPORT
----###LOGIC IMPORT
----###RFID IMPORT
----###SEVER IMPORT
####OUTLINE
####GLOBAL AND RESERVES WARNING
####SYSTEM LOGIC
----CORE LOGIC
----STARTUP LOGIC
----SAVE TO FILE
----LOAD FROM FILE
----RESTORE
----INTERNET CHECK
----LOCK AND ADMIN
####SERVER LOGIC
----GET DEFAULT VALUES FOR GLOBAL VARIABLES
----OBTAIN API KEY
--- GET EVENT LOCATION AND DATA
----CORE INFORMATION TRANSMISSION
####END SERVER LOGIC
####RFID STRUCTURE
####END RFID STRUCTURE
####LIGHT RING STRUCTURE
----Custom
----Patterns
----States​
----Light Function
###END LIGHT RING STRUCTURE
###DAS MAIN####
###SPOOPY EXTRAS AND MOREEEEEEE
"""

####SYSTEM LOGIC####=========================================================================================================================================

# --------------CORE LOGIC-------------------------

def core():
    light(0) #sets light to blue
    global FirstTimeStartup
    time.sleep(1.5) #adds a delay between reads can be reduced if seems to run too slow
    currentTag = SearchforTag(FirstTimeStartup) #This will read for the tag and output it as an int
    print("STATUS: Read tag " + str(currentTag))
    if boxLockCheck(currentTag) == True: #this will check if the box is locked and change the lock state if an admin token is presented
        main() #if it was locked it will loop back to the top of this
    light(1) #sets light to yellow spinny ring for loading

    critical, status, admit = SendToServer(currentTag, ServerParameters[0])  # bolean,string,boleanz ## takes in the tag as an int and the server params but it doesn't really use the server parmeters
    time.sleep(1)
    if critical:  # may add Soft Reset Proceedure on multi-fail???
        print("WARNING: Crit Error from server reply: " + str(status)) #if timeout, not admit then it will give an error that normally means something needs restarted somewhere
        light(4)
        time.sleep(2)
        light(3)
        time.sleep(1)
        light(4)
        time.sleep(2)
        light(0)
        main()

    if admit == False:
        light(3)
        time.sleep(2)  # Pretty self explaintory here
        light(0)
        main()
    else:
        light(2)
        time.sleep(2)
        light(0)
        main()


## --------------STARTUP LOGIC-------------------------
def startUp(FirstTimeStartup):
    setDefaultGlobals()
    check = SearchforTag(FirstTimeStartup)
    if check != "-10000":  # -10000 will be returned to check when the reader times out 5 times  ##I did it 10/24/19 maz
        print("STATUS: Setup Has concluded going into autonomous mode")
        internet_test()
        restore()  # will load old config no setup if any tag is presented (10/20/19 completed -maz)
        light(2)
        return

    internet_test()
    meal = input("INPUT REQUIRED: Input what meal this is \n")
    # [andrew] did it 10/24/19
    Events = 3 #str(getEventLocation("Lunch"))
    #Events = meal #demo code

    print("STATUS: " + str(Events) + " Slected")  # This will print the event given by the sever its implmenation does really effect anything

    # selection = input("INPUT REQUIRED: Select event ID as a ## number")  ###I belive this is dead code but it may be implemented if more user feedback is required for event slection
    # while True:
    # if selection in Events: ##needs fixed with more info

    print("STATUS: Config Choosen as: " + str(Events))
    print("STATUS: API key: " + str(api_key))
    print("STATUS: Admin Tokens are: " + str(AdminKeys)) #displays what the config is

    Con = input("INPUT REQUIRED: Confirm setup with any key, 'N' will abort all \n") # confirmation to proceed to normal opps
    if Con == "N":
        sys.exit()
    global ServerParameters
    ServerParameters.append(Events)
    ServerParameters.append(api_key)
    ServerParameters.append(AdminKeys)
    print("STATUS: Setup has concluded going into autonomous mode")
    # save slection parmeters to global
    ServerParameters = [Events]  ###BUG CHECK after we know paremeters #fixed but need rechecked 9/24/19 ## still not really impemented at alpha 10/27/19 -maz
    # save section with save() function
    Save()
    # break
#       else:
#           print("WARNING: Config " + selection + "Is not a valid selection") ##not currently implemented
#           selection = input("INPUT REQUIRED: Select event ID as a ## number")


#########Save, load and restore function but their implemenation is not essential to opps
## --------------SAVE TO FILE--------------------------
# A function that will Creates or Edit a text file in the Present working dir. that takes no arguments but using the current global varible for server parameters
def Save():
    global ServerParameters
    Dir = os.getcwd()
    f = open(os.path.join(Dir, 'ServerParameters.txt'), 'w')
    f.write(str(ServerParameters))
    f.close()

## --------------LOAD FROM FILE-------------------------
# A function that will open and read a text file in the Present working dir. that returns nothing but will store the server parameters for current global varible
def Load():
    global ServerParameters
    Dir = os.getcwd()
    f = open(os.path.join(Dir, 'ServerParameters.txt'), 'r')
    out = f.read()
    ServerParameters = out.strip('][').split(', ')  ###MAJOR BUG### Needs a for loop for casting once we know what "parsmters" look like
    f.close()
    # print(ServerParameters)

## --------------RESTORE--------------------------------
def restore():
    Load()
    global FirstTimeStartup
    FirstTimeStartup = False

## --------------INTERNET CHECK-------------------------

def internet_test():
    print("STATUS: TESTING INTERNET")
    #url = "http://time.gov"  # global url var is hack server Com. out this line on deployment
    print("STATUS: CONECTING TO " + url)

    try:
        urllib.request.urlopen(url, timeout = 15)
    except urllib.error.URLError or requests.exceptions.Timeout as e:
        print("WARNING: TIME OUT")
        print("ERROR: Network Down, soft reset recommended")
        time.sleep(15)
        sys.exit()

    print("STATUS: Connection Pass, we can see " + url)


# --------------LOCK AND ADMIN-------------------------
# Function takes atributes rfidserial as a string and AdminKeys as a list of stings, Returns Bol of lock status
def boxLockCheck(RfidSerial):
    global AdminKeys, LockState
    if RfidSerial in AdminKeys:
        light(2) #green
        print("WARNING: LOCK STATUS HAS BEEN UPDATED")
        time.sleep(2)
        LockState = not LockState
        return True
    if LockState == True:
        light(3) #red
        light(4) #yellow
        light(3) #red
        time.sleep(1)
        return True
    else:
        return False


####END SYSTEM LOGIC####==============================================================================================

####SERVER LOGIC####=============================================================================++++=================

# ------------------------GET DEFAULT VALUES FOR GLOBAL VARIABLES---------

# uses config.ini to get some initial data from the last run
# for example, the api_key can be obtained so that we have a possibly valid key

def setDefaultGlobals():
    global api_key, pin, url

    # reading
    api_key = config.get("default", "api_key")
    pin = config.get("default", "pin")
    url = config.get("default", "url")
    # location = config.get("default","location")

    return


# ---------------------------OBTAIN API KEY--------------------------

# running this function obtains an API key that will last for about 3 days
# requires obtaining a pin value from adding scanner in redis site

def getApiKey():
    response = requests.post(API_Website, data={'pin': pin})

    # returns if status is error
    status = response.status_code
    if status < 200 or status > 299:
        try:
            data = response.json()
            print("ERROR WHEN REGISTERING API KEY: status code " + str(status))
            print("description: " + data[
                "message"] + "\n this error might be due to the API key already existing, if it runs fine then ignore it. If not make a new Scanner in redis-server and change the pin in config.ini")
        except:
            print("ERROR WHEN REGISTERING API KEY: status code " + str(status))
            print(
                "description: " + response.text + "\n this error might be due to the API key already existing, if it runs fine then ignore it. If not make a new Scanner in redis-server and change the pin in config.ini")
        return 0

    data = response.json()
    global api_key
    api_key = data["data"]["apikey"]
    config.set("default", "api_key", api_key)
    print(api_key)
    return


# --------------------------- GET EVENT LOCATION AND DATA--------------------------------

# function to get the event location if given a event title, used for the location in SendToServer
# We will probably want to run this at start, with something like getEventLocation("Lunch")
# all food events should return the same location unless its not all at the same place

def getEventLocation(eventTitle):
    Location_Website = url + "/scanner/events"
    try:
        response = requests.get(Location_Website, timeout=15)
    except requests.exceptions.Timeout as e:
        print("CRITICAL: SERVER TIMEOUT 1")
        return 0

    # returns if status is error
    status = response.status_code
    if status < 200 or status > 299:
        try:
            data = response.json()
            print("ERROR WHEN GETTING EVENT LOCATION: status code " + str(status))
            print("description: " + data["message"])
        except:
            print("ERROR WHEN GETTING EVENT LOCATION: status code " + str(status))
            print("description: " + response.text)
        return 0

    # filtering what data to output
    data = response.json()
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
    try:
        response = requests.post(Scan_Website, data=arguments, timeout=15)
    except requests.exceptions.Timeout as e:
        return True, "CRITICAL: SERVER TIMEOUT 2", False

    status = response.status_code

    # returns if status is error
    if status < 200 or status > 299:
        critical = True
        try:
            data = response.json()
            print("ERROR WHEN SENDING TO SERVER: status code " + str(status))
            print("description1: " + data["message"])
        except:
            print("ERROR WHEN SENDING TO SERVER: status code " + str(status))
            print("description2: " + response.text)
        return critical, status, admit

    # if no error, admit checks isRepeat and returns
    data = response.json()
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
def reading():
    reader = SimpleMFRC522()
    data = reader.read()
    Dir = os.getcwd()
    f = open(os.path.join(Dir, 'cache.txt'), 'w') # Look I know this is hacky as heck, but i could not for my life figure out how to return multiproceses without interupts - maz
    f.write(str(data[0]))
    f.close()


def SearchforTag(FirstTime):
    reader = SimpleMFRC522()
    # Try reading data from wrist band
    try:
        while True:
            count = 0
            data = [0]
            id = 0
            Dir = os.getcwd()
            while FirstTime:
                #Only on first time set up will the reader have a time out functionality. There seems to be no benifit having this is the normal opps code, but if it was found out to be needed for any reason its here
                #This is accoplished by reading the data as a multiprocess with a time inerput and a vaild reads data is ~cringe~ saved to a txt file named cached because pythons GIL makes sharing and returning V. hard  -maz
                p = multiprocessing.Process(target=reading)  # Start reader.read as a process
                p.start()
                p.join(3)  # Wait for 3 seconds or until process finishes
                if p.is_alive():  # If thread is still active
                    count = count + 1
                    print("WARNING: STARTUP READER TIMEOUT (" + str(count) + "/5)")
                    p.terminate()  # Terminate
                    p.join()
                else:
                    f = open(os.path.join(Dir, 'cache.txt'),'r')
                    id = int(f.read())
                    f.close()
                    new = str(hex(id))[2:10] #takes out the first 8 hex bits
                    id = int(new[6:8] + new[4:6] + new[2:4] + new[0:2],16) #flips it
                    print(id)
                if id != 0:
                    return id
                if count == 5:
                    return "-10000"

            CardDataImpdata = reader.read()
            id = CardDataImpdata[0]
            new = str(hex(id))[2:10] #takes out the first 8 hex bits
            id = int(new[6:8] + new[4:6] + new[2:4] + new[0:2],16) #flips it
            if id:
                return id
    finally:
        GPIO.cleanup()


####END RFID STRUCTURE####=============================================================================================


####LIGHT RING STRUCTURE###===========================================================================================
# LED strip configuration:
LED_COUNT = 24  # Number of LED pixels.
LED_BRIGHTNESS = 10  # Set to 0 for darkest and 255 for brightest
# LED_CHANNEL = 0
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
    global FirstTimeStartup  #If the program is just starting up it will go into setup mode, every other time a call to main is the same as a call to core
    if FirstTimeStartup:
        startUp(FirstTimeStartup)
        FirstTimeStartup = False
    core()

###SPOOPY EXTRAS AND MOREEEEEEE==========================================================================================
def PLUS():
    #This took me alot of time to put together so you better apperciate it. please include the revision number in here AND YES IT SAYS SPOOPY THIS WAS A HALLOW WEEKEND HACKATHON
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
            |-(=-=-=-=-=-(|=====/=_-=/\.           Fall 2019 Alpha Release 1.0.1 - Point Of Location for Eating (POLE)
            | |=_-= _=- _=| -_=/=_-_/__\.
            | |- _ =_-  _-|=_- |]#| I II                        Technology Director - Julia M McCarthy
            |=|_/ \_-_= - |- = |]#| I II                     RFID Program Lead - Michael S Maslakowski (maz)
            | /  _/ \. -_=| =__|]!!!I_II!!                    
           _|/-'/  ` \_/ \|/' _ ^^^^`.==_^.                                   RFID Team:
         _/  _/`-./`-; `-.\_ / \_'\`. `. ===`.                  Andrew Feng (Light Ring/Network Logic)
        / .-'  __/_   `.   _/.' .-' `-. ; ====;\.                  Divya Rustagi (RFID Interpriter)
       /.   `./    \ `. \ / -  /  .-'.' ====='  >                    Daniel Melo Cruz (Debugging)
      /  \  /  .-' `--.  / .' /  `-.' ======.' /               Michael S Maslakowski (Core/Startup/Main)
                                                                    Stanley Kwok (Redis and Severs)

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
