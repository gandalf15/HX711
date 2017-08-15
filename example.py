import sys
from hx711 import HX711		# import the class HX711
import RPi.GPIO as GPIO		# import GPIO
import time

# function clean_exit cleans and exit...
def clean_exit():
	GPIO.cleanup()
	print ("\nBye")
	sys.exit()

try:
	# Create an object hx which represents your real hx711 chip
	# Required input parameters are only 'dout_pin' and 'pd_sck_pin'
	# If you do not pass any argument 'gain_channel_A' then the default value is 128
	# If you do not pass any argument 'set_channel' then the default value is 'A'
	hx = HX711(dout_pin=19, pd_sck_pin=13, gain_channel_A=128, select_channel='B')
	
	result = hx.reset()		# Before we start, lets reset the hx711
	if result:
		print('Ready to use')
	else:
		print('not ready')
	
	hx.set_gain_A(gain=64)		# You can change the gain on channel A any time.
	hx.select_channel(channel='A')	# Select desired channel. Either 'A' or 'B' at any time.
	
	# Read data several, or only one, time and return mean (average)
	# No subtraction of offset. Even if the scale is set to zero
	# it just returns exactly the number which hx711 sends
	data = hx.get_raw_data_mean(times=1)
	
	if data != False:	# always check if you get correct value or only False
		print('Raw data: ' + str(data))
	else:
		print('invalid data')
	
	# measure tare and save the value as offset for current channel
	# and gain selected.
	result = hx.zero(times=10)
	
	# Read data several, or only one, time and return mean (average).
	# It subtract offset for particular channel from the mean value.
	# This value is still just a number from HX711 without any conversion
	# to units such as grams or kg.
	data = hx.get_data_mean(times=1)
	
	if data  != False:	# always check if you get correct value or only False
		# now the value is close to 0
		print('Data subtracted by offset but still not converted to any unit: '\
			 + str(data))
	else:
		print('invalid data')

	# In order to calculate the conversion ratioto some units, in my case I want grams,
	# you must have known weight.
	input('Put known weight on the scale and then press Enter')
	#hx.set_debug_mode(True)
	data = hx.get_data_mean(times=10)
	if data != False:
		print(data)
		known_weight_grams = input('Write how many grams it was and press Enter: ')
		try:
			value = int(known_weight_grams)
			print(value)
		except ValueError:
			print('Expected integer and I have got: '\
					+ str(known_weight_grams))

		# set scale ratio for particular channel and gain which is 
		# used to calculate the conversion to units. To set this 
		# you must have known weight first. Required argument is only
		# scale ratio. Without arguments 'channel' and 'gain_A' it sets 
		# the ratio for current channel and gain.
		ratio = data / value 
		hx.set_scale_ratio(scale_ratio=ratio)
		print('Ratio is set.')
	else:
		print('Sorry try again.')
		clean_exit()

	# Read data several, or only one, time and return mean (average)
	# subtracted by offset and converted by scale ratio to 
	# desired units. For example grams.
	print('Current weight on the scale in grams is: ')
	print(hx.get_weight_mean(3)) 
	
	# if you need the data fast without doing average just do this
	for i in range(30):
		# the value will vary because it is only one immediate reading.
		# the default speed for hx711 is 10 samples / sec
		print(str(hx.get_weight_mean(times=1)) + ' g')
	
	# if you are not sure which gain is currently set on channel A you can call
	print('Current gain on channel A: ' + str(hx.get_current_gain_A()))
	
	
	# set offset manually for particulari channel and gain. If you want to 
	# set offset for channel B then gain_A is not required
	# if no arguments 'channel' and 'gain_A' provided. The offset is
	# set for the current channel and gain
	#hx.set_offset(offset=15000)	
	#print('Now I changed the offset for channel A and for gain currently used')
	#print(hx.get_data_mean(3))
	# turns on debug mode. It prints many things so you can find problem
	#hx.set_debug_mode(flag=True)
	
	#print(hx.get_raw_data_mean())	# now you can see many intermediate steps and values
	
	#hx.power_down()			# turns off the hx711. Low power consumption
	#hx.power_up()			# turns on the hx711.
	
	#hx.reset()			# resets the hx711 and get it ready for 
					# reading of the currently selected channel
		
	
	
	while True:
		result = hx.select_channel('A')
		if result:
			print('channel A selected')
		else:
			print('cannot select channel A')

		result = hx.set_gain_A(64)
		if result:
			# without argument default is 1
			print ('-> Raw data channel A gain 64: ' + str(hx.get_raw_data_mean(10)))
			print ('-> Weight channel A gain 64: ' + str(hx.get_weight_mean(10)))
			print('--------------------------------------------')
		else:
			print('cannot set gain 64')
		
		result = hx.set_gain_A(128)
		if result:
			# without argument default is 1
			print ('-> Raw data channel A gain 128: ' + str(hx.get_raw_data_mean(10)))
			print ('-> Weight channel A gain 128: ' + str(hx.get_weight_mean(10)))
			print('--------------------------------------------')
		else:
			print('cannot set gain 128')
		
		result = hx.select_channel('B')
		if result:
			print('Channel B selected')
			# without argument default is 1
			print ('-> Raw data channel B gain 32: ' + str(hx.get_raw_data_mean())+'\n')
		else:
			print('cannot select channel B')
		
except (KeyboardInterrupt, SystemExit):
	clean_exit()
