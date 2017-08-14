import sys
from hx711 import HX711		# import the class HX711

# function clean_exit cleans and exit...
def clean_exit():
	print ("Cleaning...")
	GPIO.cleanup()
	print ("Bye")
	sys.exit()

try:
	# Create an object hx which represents your real hx711 chip
	# Required input parameters are only 'dout_pin' and 'pd_sck_pin'
	# If you do not pass any argument 'gain_channel_A' then the default value is 128
	# If you do not pass any argument 'set_channel' then the default value is 'A'
	hx = HX711(dout_pin=19, pd_sck_pin=13, gain_channel_A=64, select_channel='B')
	
	hx.reset()			# Before we start, lets reset the hx711
	hx.set_gain_A(gain=128)		# You can change the gain on channel A any time.
	
	# Read data several, or only one, time and return mean (average)
	# No subtraction of offset. Even if the scale is set to zero
	# it just returns exactly the number which hx711 sends
	data = hx.get_raw_data_mean(times=1)
	
	if data != False
		print(data)
	else:
		print('invalid data')
	
	hx.zero(times=10)	# measire tare and save the value as offset for current channel
				# and gain selected.
	
	# Read data several, or only one, time and return mean (average).
	# It subtract offset for particular channel from the mean value.
	# This value is still just a number from HX711 without any conversion
	# to units such as grams or kg.
	data = hx.get_data_mean(times=1)
	
	if data  != False:
		print(data)
	else:
		print('invalid data')
	
	# set scale ratio for particular channel and gain which is used to calculate the conversion
	# to units. To set this you must have known weight first.
	# 
	hx.set_scale_ratio(channel='A', gain_A=128,scale_ratio=1)  
	
	# Read data several, or only one, time and return mean (average)
	# subtracted by offset and converted by scale ratio to 
	# desired units. For example grams.
	hx.get_weight_mean(times=1)
	
	
	#hx.set_offset(offset=15000, channel='A', gain_A=128)	# set offset manually for particular
								# channel and gain. If you want to 
								# set offset for channel B then gain_A
								# is not required
	

	#hx.set_debug_mode(flag=False)	# turns on debug mode. It prints many things so you can find problem
	
	#hx.power_down()			# turns off the hx711. Low power consumption
	#hx.power_up()			# turns on the hx711.
	
	#hx.reset()			# resets the hx711 and get it ready for 
					# reading of the currently selected channel
		
	
	hx.select_channel(channel='A')	# Select desired channel. Either 'A' or 'B' at any time.
	
	while result == False:
		time.sleep(0.1)
		result = hx.zero_scale(10)
	
	while True:
		try:
			print(str(hx.get_weight_mean()) + ' g') # without argument default is 1
			print (hx.get_raw_data_mean(3))	# without argument default is 1
			print(hx.get_data_mean(3)) 	# without argument default is 1
			
		
		
except (KeyboardInterrupt, SystemExit):
	cleanAndExit()
