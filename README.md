# HX711 class for Rasperry Pi Zero, 2 and 3 written in Python 3.

I dropped support for Python 2 and changed the implementation in Python 3. Therefore, it is not backward compatible. The implementation in C is not completely finished but can be considered as beta version.

I decided to write my own python class simply because all what I found was not enough good for my purpose.

So what is the difference?
- Raspberry Pi sometimes reads invalid data because the pin pd_sck is high for 60 micro seconds or longer. To eliminate this problem I implemented simple filter which solves this problem. Therefore it provides better and more precise readings.
- It does not require additional libraries only Python 3.6 or higher.
- If data is invalid (Max and Min values of HX711) it detects it.
- It can quickly switch between channels and gains.
- It raises exceptions if wrong input provided.
- It has debug mode.
- It has separate offset and scale ratio for each channel and gain.
- It remembers last valid raw data for each channel and gain.
- It detects if pin pd_sck is high for longer than 60 micro seconds and therefore evalueates reading as Faulty. (only for Python 3 class)(60 us is important. Read Datasheet for more info.)

I recommend to connect pin 15(RATE) of HX711 to VCC (+3.3V) in order to get 80 samples per second. By default it is only 10.
If you have a cheap green breakout board as I have, you have to desolder and bend the pin 15(RATE) upwards. Then soldeer short wire to VCC.

Great explanation of strain gauges: https://www.allaboutcircuits.com/textbook/direct-current/chpt-9/strain-gauges/

## Install

The python class HX711 is can be installed with the following command:
   
   `pip3 install 'git+https://github.com/bytedisciple/HX711.git#egg=HX711&subdirectory=HX711_Python3'`
   
Once installed instantiate a HX711 object with the following:

      import RPi.GPIO as GPIO                # import GPIO
      from hx711 import HX711                # import the class HX711
      
      GPIO.setmode(GPIO.BCM)                 # set GPIO pin mode to BCM numbering
      hx = HX711(dout_pin=5, pd_sck_pin=6)
    

