# Point Of Location for Eating (POLE)
Fall 2019 Alpha Release 1.0 

# Instruction's to install
Apply .img file to the SD card of your raspberry Pi, or following all the websites within the top part of the code
The SSH password for this image is U: pi P: LnrBldShr

Follow this diagram for wiring your RC522 RFID Reader up to the pi.
https://cdn.pimylifeup.com/wp-content/uploads/2017/10/RFID-Fritz-v2.png

Place the data in for the neo-pixel light ring into GPIO18 (pin 12) and give it 5v and ground from any other available source.

This code was Written in python 3 and requires elevated privileges to use the light ring. 
MUST BE SUPER USER OR ROOT

Edit the API key and sever address information in the Declaration section of the code to meet your parameters

# Functionalities

On start up program will make 5 attempts to read anything. If it does it will automatically use the last configuration. If not It will prompt and confirm the operator for that information. 

You can lock and unlock the unit by using an admin token on it. These tokens cannot be used as anything else.

Green means admit, Red is Deny and a blinking yellow-red means a critical error has occurred or connection drop

Please reference the Boxes documentation as its behaviour is meant to emulate what the box would do for meal events.
That's pretty much it any other questions please reference the in line documentations
