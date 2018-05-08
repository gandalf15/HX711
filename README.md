HX711 class for Rasperry Pi 2 and 3 written in Python 3 and Python 2.7

If you like this, please click the Star. :) Thanks

I decided to write my own python class simply because all what I found was not enough good for my purpose.

So what is the difference?

	Do not require special libraries only default python 3 installation.
	This is not true for class in Python 2.7. It requires NumPy (www.numpy.org).
	If data is invalid (Max and min values of HX711) it detects it.
	It can quickly switch between channels and gains.
	It raises exceptions if wrong input provided.
	It has debug mode.
	It has separate offset and scale ratio for each channel and gain.
	It remembers last valid raw data for each channel and gain.
	It detects if pin pd_sck is high for longer than 60 us and therefore evalueates reading as Faulty. (only for Python 3 class)(60 us is important. Read Datasheet for more info.)
	It has a simple filter (based on standard deviation) for detecting incorrect values. Therefore it provides better and more precise readings.

I recommend to connect pin 15(RATE) of HX711 to VCC (+3.3V) in order to get 80 samples per second. By default it is only 10.
If you have a cheap green breakout board as I have, you have to desolder and bend the pin 15(RATE) upwards. Then soldeer short wire to VCC.

Datasheet: https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf

Great explanation of strain gauges: https://www.allaboutcircuits.com/textbook/direct-current/chpt-9/strain-gauges/

I was inspired by bogde: https://github.com/bogde/HX711

Sometime it is reading invalid data because the pin pd_sck is high for 60 us or longer.

To eliminate this problem I implemented simple filter which solve this problem.
See function get_raw_data_mean() in hx711.py
