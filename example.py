from hx711 import HX711		# import the class HX711
import RPi.GPIO as GPIO		# import GPIO
import time

try:
	# Create an object hx which represents your real hx711 chip
	# Required input parameters are only 'dout_pin' and 'pd_sck_pin'
	# If you do not pass any argument 'gain_channel_A' then the default value is 128
	# If you do not pass any argument 'set_channel' then the default value is 'A'
	# you can set a gain for channel A even though you want to currently select channel B
	hx = HX711(dout_pin=20, pd_sck_pin=21, gain_channel_A=128, select_channel='B')
	
	result = hx.reset()		# Before we start, reset the hx711 ( not necessary)
	if result:			# you can check if the reset was successful
		print('Ready to use')
	else:
		print('not ready')
	
	hx.set_gain_A(gain=64)		# You can change the gain for channel A  at any time.
	hx.select_channel(channel='A')	# Select desired channel. Either 'A' or 'B' at any time.
	
	# Read data several, or only one, time and return mean value
	# it just returns exactly the number which hx711 sends
	# argument times is not required default value is 1
	data = hx.get_raw_data_mean(times=1)
	
	if data != False:	# always check if you get correct value or only False
		print('Raw data: ' + str(data))
	else:
		print('invalid data')
	
	# measure tare and save the value as offset for current channel
	# and gain selected. That means channel A and gain 64
	result = hx.zero(times=10)
	
	# Read data several, or only one, time and return mean value.
	# It subtracts offset value for particular channel from the mean value.
	# This value is still just a number from HX711 without any conversion
	# to units such as grams or kg.
	data = hx.get_data_mean(times=10)
	
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
		print('Mean value from HX711 subtracted by offset: ' + str(data))
		known_weight_grams = input('Write how many grams it was and press Enter: ')
		try:
			value = int(known_weight_grams)
			print(str(value) + ' grams')
		except ValueError:
			print('Expected integer and I have got: '\
					+ str(known_weight_grams))

		# set scale ratio for particular channel and gain which is 
		# used to calculate the conversion to units. To set this 
		# you must have known weight first. Required argument is only
		# scale ratio. Without arguments 'channel' and 'gain_A' it sets 
		# the ratio for current channel and gain.
		ratio = data / value 	# calculate the ratio for channel A and gain 64
		hx.set_scale_ratio(scale_ratio=ratio)	# set ratio for current channel
		print('Ratio is set.')
	else:
		raise ValueError('Cannot calculate mean value. Try debug mode.')
		

	# Read data several, or only one, time and return mean value
	# subtracted by offset and converted by scale ratio to 
	# desired units. In my case in grams.
	print('Current weight on the scale in grams is: ')
	print(str(hx.get_weight_mean(6)) + ' g') 
	
	# if you need the data fast without doing average or filtering them.
	# do some kind of loop and do not pass any argument. Default 'times' is 1
	# be aware that HX711 sometimes return invalid or wrong data.
	# you can probably see it now
	print('Now I will print data quickly, but sometimes wrong.')
	input('That is why I recommend always passing argument times=5 or higher value')
	for i in range(40):
		# the value will vary because it is only one immediate reading.
		# the default speed for hx711 is 10 samples per second
		print(str(hx.get_weight_mean()) + ' g')
	
	# if you are not sure which gain is currently set on channel A you can call
	print('Current gain on channel A: ' + str(hx.get_current_gain_A()))
	
	# to get currently selected channel
	print('Current channel is: ' + str(hx.get_current_channel()))
	
	# to get current offset for a particular channel
	offset =  hx.get_current_offset(channel='A', gain_A=128)
	print('Current offset for channel A and gain 128: ' + str(offset))
	# if no arguments passed then it return offset for the currently selected channel and gain
	offset =  hx.get_current_offset()
	print('Current offset for channel A and gain 128: ' + str(offset))
	offset =  hx.get_current_offset(channel='B')	# for channel B no argument gain_A
	print('Current offset for channel A and gain 128: ' + str(offset))
	
	# set offset manually for particulari channel and gain. If you want to 
	# set offset for channel B then gain_A is not required
	# if no arguments 'channel' and 'gain_A' provided. The offset is
	# set for the current channel and gain
	#hx.set_offset(offset=15000)
	
	input('Now I will show you how it looks if you turn on debug mode. Press ENTER')
	# turns on debug mode. It prints many things so you can find problem
	hx.set_debug_mode(flag=True)
	print(hx.get_raw_data_mean(5))	# now you can see many intermediate steps and values
	hx.set_debug_mode(False)	
	
	#hx.power_down()		# turns off the hx711. Low power consumption
	#hx.power_up()			# turns on the hx711.
	#hx.reset()			# resets the hx711 and get it ready for 
					# reading of the currently selected channel
	for i in range(2):
		# without argument default is 1
		print ('-> Weight channel A gain 64: ' + str(hx.get_weight_mean(10)) + ' g')
		print ('-> Raw data channel A gain 64: ' + str(hx.get_raw_data_mean(10)))
		print('--------------------------------------------')
		
		result = hx.set_gain_A(128)
		if result:
			# without argument default is 1
			print ('-> Weight channel A gain 128: ' + str(hx.get_weight_mean(10)) + ' g')
			print ('-> Raw data channel A gain 128: ' + str(hx.get_raw_data_mean(10)))
			print('--------------------------------------------')
		else:
			print('cannot set gain 128')
		
		result = hx.select_channel('B')
		if result:
			print('Channel B selected')
			# without argument default is 1
			print ('-> Weight channel B gain 32: ' + str(hx.get_weight_mean(10)) + ' g\n')
			print ('-> Raw data channel B gain 32: ' + str(hx.get_raw_data_mean()))
		else:
			print('cannot select channel B')
		
		# you can also get the last raw data read for each channel and gain without reading it again
		# without an argument it return raw data for currently set channel and gain, so channel B
		last_value = hx.get_last_raw_data()
		print('I remember last raw data for channel B: ' + str(last_value))	
		last_value = hx.get_last_raw_data(channel='A', gain_A=64)
		print('I remember last raw data for channel A gain 64: ' + str(last_value))	
		last_value = hx.get_last_raw_data(channel='A', gain_A=128)
		print('I remember last raw data for channel A gain 128: ' + str(last_value) + '\n')
		# now I turn OFF Population standard deviation filter
		if hx.set_pstdev_filter(False):
			print('Population standard deviation filter is turned OFF.' + '\n')
		
	
except (KeyboardInterrupt, SystemExit):
	print('Bye :)')
	
finally:
	GPIO.cleanup()

