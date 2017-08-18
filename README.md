HX711 class for Rasperry Pi written in Python 3


I decided to write my own python class simply because all what I found was not enough good for my purpose.

So what is the difference?
	- Do not require special libraries only default python 3 installation
	- If data is invalid it detect this event. Max and min values of HX711
	- It can quickly switch between channels and gains
	- It raises exceptions if wrong input provided
	- It has debug mode
	- It has separate offset and scale ratio for each channel and gain
	- It remembers last valid raw data for each channel and gain
	- It detects if pin pd_sck is high for longer than 60 us and therefore evalueates reading as Faulty. Then repeats. (60 us is important. Read Datasheet for more info.)
	- It has a simple filter (based on standard deviation) for detecting incorrect values. Therefore it provides better and more precise readings.

Datasheet: https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf

Great explanation of strain gauges: https://www.allaboutcircuits.com/textbook/direct-current/chpt-9/strain-gauges/

I was inspired by bogde: https://github.com/bogde/HX711

Sometime it is reading invalid data because the pin pd_sck is high for 60 us or longer.

To eliminate this problem I implemented simple filter which solve this problem.
See function get_raw_data_mean() in hx711.py

It is not perfect and I will implement this in C language in the future.
