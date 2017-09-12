#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import statistics as stat
class HX711:
	def __init__(self, dout_pin, pd_sck_pin, gain_channel_A=128, select_channel='A'):
		if (isinstance(dout_pin, int) and 
			isinstance(pd_sck_pin, int)): 	# just chack of it is integer
			self._pd_sck = pd_sck_pin 	# init pd_sck pin number
			self._dout = dout_pin 		# init data pin number
		else:
			raise TypeError('dout_pin and pd_sck_pin have to be pin numbers.\nI have got dout_pin: '\
					 + str(dout_pin) + \
					' and pd_sck_pin: ' + str(pd_sck_pin) + '\n')
		
		self._gain_channel_A = 0 	# init to 0	
		self._offset_A_128 = 0		# init offset for channel A and gain 128
		self._offset_A_64 = 0		# init offset for channel A and gain 64
		self._offset_B = 0 		# init offset for channel B
		self._last_raw_data_A_128 = 0	# init last data to 0 for channel A and gain 128
		self._last_raw_data_A_64 = 0 	# init last data to 0 for channelA and gain 64
		self._last_raw_data_B = 0 	# init last data to 0 for channel B	
		self._wanted_channel = ''	# init to empty string
		self._current_channel = ''	# init to empty string
		self._scale_ratio_A_128 = 1	# init to 1
		self._scale_ratio_A_64 = 1	# init to 1
		self._scale_ratio_B = 1		# init to 1
		self._debug_mode = False	# init debug mode to False
		self._pstdev_filter = True	# pstdev filter is by default ON
		
		GPIO.setmode(GPIO.BCM) 			# set GPIO pin mode to BCM numbering
		GPIO.setup(self._pd_sck, GPIO.OUT)	# pin _pd_sck is output only
		GPIO.setup(self._dout, GPIO.IN)		# pin _dout is input only
		self.select_channel(select_channel)	# call select channel function
		self.set_gain_A(gain_channel_A) 	# init gain for channel A
			
	############################################################
	# select_channel function evaluates if the desired channel #
	# is valid and then sets the _wanted_channel.		   #
	# If returns True then OK 				   #
	# INPUTS: channel ('A'|'B') 				   #
	# OUTPUTS: BOOL  					   #
	############################################################
	def select_channel(self, channel):
		if (channel == 'A'):
			self._wanted_channel = 'A'
		elif (channel == 'B'):
			self._wanted_channel = 'B'
		else:
			raise ValueError('channel has to be "A" or "B".\nI have got: '\
						+ str(channel))
		# after changing channel or gain it has to wait 50 ms to allow adjustment.
		# the data before is garbage and cannot be used.
		self._read()
		time.sleep(0.5)
		return True
		
	############################################################
	# set_gain_A function sets gain for channel A. 		   #
	# allowed values are 128 or 64. If return True then OK	   #
	# INPUTS: gain (64|128) 				   #
	# OUTPUTS: BOOL 					   #
	############################################################
	def set_gain_A(self, gain):
		if gain == 128:
			self._gain_channel_A = gain
		elif gain == 64:
			self._gain_channel_A = gain
		else:
			raise ValueError('gain has to be 128 or 64.\nI have got: '
						+ str(gain))
		# after changing channel or gain it has to wait 50 ms to allow adjustment.
		# the data before is garbage and cannot be used.
		self._read()
		time.sleep(0.5)
		return True
		
	############################################################
	# zero is function which sets the current data as 	   #
	# an offset for particulart channel. It can be used for    #
	# subtracting the weight of the packaging. 		   #
	# max value of times parameter is 99. min 1. Default 10.   #
	# INPUTS: times # how many times do reading and then mean  #
	# OUTPUTS: BOOL 	# if True it is OK		   #
	############################################################
	def zero(self, times=10):
		if times > 0 and times < 100:
			result = self.get_raw_data_mean(times)
			if result != False:
				if (self._current_channel == 'A' and 
					self._gain_channel_A == 128):
					self._offset_A_128 = result
					return True
				elif (self._current_channel == 'A' and 
					self._gain_channel_A == 64):
					self._offset_A_64 = result
					return True
				elif (self._current_channel == 'B'):
					self._offset_B = result
					return True
				else:
					if self._debug_mode:
						print('Cannot zero() channel and gain mismatch.\n'\
							+ 'current channel: ' + str(self._current_channel)\
							+ 'gain A: ' + str(self._gain_channel_A) + '\n')
					return False
			else:
				if self._debug_mode:
					print('zero() got False back.\n')
				return False
		else:
			raise ValueError('In function "zero" parameter "times" can be in range 1 up to 99. '\
						+ 'I have got: ' + str(times) + '\n')
	
	############################################################
	# set offset function sets desired offset for particular   #
	# channel and gain. By default it sets offset for current  #
	# channel and gain.					   #
	# INPUTS: offset, channel (a|A|b|B), gain (128|64)	   #
	# OUTPUTS: BOOL 	# return true it is ok		   #
	############################################################
	def set_offset(self, offset, channel='', gain_A=0):
		if isinstance(offset, int):
			if channel == 'A' and gain_A == 128: 
				self._offset_A_128 = offset
				return True
			elif channel == 'A' and gain_A == 64:
				self._offset_A_64 = offset
				return True
			elif channel == 'B':
				self._offset_B = offset
				return True
			else:
				if self._current_channel == 'A' and self._gain_channel_A == 128:
					self._offset_A_128 = offset
					return True
				elif self._current_channel == 'A' and self._gain_channel_A == 64:
					self._offset_A_64 = offset
					return True
				else:
					self._offset_B = offset
					return True
		else:
			raise TypeError('function "set_offset" parameter "offset" has to be integer. '\
					+ 'I have got: ' + str(offset) + '\n')
		
	############################################################
	# set_scale_ratio function sets the ratio for calculating  #
	# weight in desired units. In order to find this ratio for #
	# example to grams or kg. You must have known weight. 	   #
	# Function returns True if it is ok. Else raises exception #
	# INPUTS: channel('A'|'B'|empty), gain_A(128|64|empty),	   #
	# 		scale_ratio(0.0..1,..)			   #
	# OUTPUTS: BOOL		# if True it is OK 		   #
	############################################################
	def set_scale_ratio(self, channel='', gain_A=0, scale_ratio=1.0):
		if (scale_ratio > 0.0):
			if channel == 'A' and gain_A == 128: 
				self._scale_ratio_A_128 = scale_ratio
				return True
			elif channel == 'A' and gain_A == 64:
				self._scale_ratio_A_64 = scale_ratio
				return True
			elif channel == 'B':
				self._scale_ratio_B = scale_ratio
				return True
			else:
				if self._current_channel == 'A' and self._gain_channel_A == 128:
					self._scale_ratio_A_128 = scale_ratio
					return True
				elif self._current_channel == 'A' and self._gain_channel_A == 64:
					self._scale_ratio_A_64 = scale_ratio
					return True
				else:
					self._scale_ratio_B = scale_ratio
					return True
		else:
			raise ValueError('In function "set_scale_ratio" parameter "scale_ratio" has to be '\
					+ 'positive number.\nI have got: ' + str(scale_ratio) + '\n')
	
	############################################################
	# set_pstdev_filter function is for turning on and off 	   #
	# population standard deviation filter.			   #
	# INPUTS: flag(BOOL)					   #
	# OUTPUTS: BOOL 	# if True then it is executed ok   #
	############################################################
	def set_pstdev_filter(self, flag=True):
		if flag == False:
			self._pstdev_filter = False
			if self._debug_mode:
				print('Population standard deviation filter DISABLED')
			return True
		elif flag == True:
			self._pstdev_filter = True
			if self._debug_mode:
				print('Population standatd deviation filter ENABLED')
			return True
		else:
			raise ValueError('In function "set_pstdev_filter" parameter "flag" can be only BOOL value.\n'
					+ 'I have got: ' + str(flag) + '\n' )
	
	############################################################
	# set_debug_mode function is for turning on and off 	   #
	# debug mode.						   #
	# INPUTS: flag(BOOL)					   #
	# OUTPUTS: BOOL 	# if True then it is executed ok   #
	############################################################
	def set_debug_mode(self, flag=False):
		if flag == False:
			self._debug_mode = False
			print('Debug mode DISABLED')
			return True
		elif flag == True:
			self._debug_mode = True
			print('Debug mode ENABLED')
			return True
		else:
			raise ValueError('In function "set_debug_mode" parameter "flag" can be only BOOL value.\n'
					+ 'I have got: ' + str(flag) + '\n' )
	
	############################################################
	# save last raw data does exactly how it looks.		   #
	# If return False something is wrong. Try debug mode.	   #
	# INPUTS: channel('A'|'B'), gain_A(64|128)		   #
	# OUTPUTS: BOOL						   #
	############################################################
	def _save_last_raw_data(self, channel, gain_A, data):
		if channel == 'A' and gain_A == 128:
			self._last_raw_data_A_128 = data
		elif channel == 'A' and gain_A == 64:
			self._last_raw_data_A_64 = data
		elif channel == 'B':
			self._last_raw_data_B = data
		else:
			return False
	
	############################################################
	# _ready function check if data is prepared for reading.   #
	# It returns Boolean value. True means that data is ready  #
	# INPUTS: none						   #
	# OUTPUTS: BOOL						   #
	############################################################
	def _ready(self):
		if GPIO.input(self._dout) == 0:	# if DOUT pin is low data is ready for reading
			return True
		else:
			return False
	
	############################################################
	# _set_channel_gain is called only from _read function.    #
	# It finishes the data transmission for hx711 which sets   #
	# the next required gain and channel.			   #
	# If it return True it is OK. 				   #
	# INPUT: num (1|2|3)	# how many ones it sends	   #
	# OUTPUTS: BOOL 					   #
	############################################################
	def _set_channel_gain(self, num):
			for i in range(num):
				start_counter = time.perf_counter() # start timer now.
				GPIO.output(self._pd_sck, True) # set high
				GPIO.output(self._pd_sck, False) # set low
				end_counter = time.perf_counter() # stop timer
				if end_counter-start_counter >= 0.00006: # check if hx 711 did not turn off...
				# if pd_sck pin is HIGH for 60 us and more than the HX 711 enters power down mode.
					if self._debug_mode:
						print('Not enough fast while setting gain and channel')
						print('Time elapsed: ' + str(end_counter - start_counter))
					# hx711 has turned off. First few readings are inaccurate.
					# Despite it this reading was ok and data can be used.
					result = self.get_raw_data_mean(6) # set for the next reading.
					if result == False:
						return False
			return True
	
	############################################################
	# _read function reads bits from hx711, converts to INT    #
	# and validate the data. 				   #
	# If it returns int it is OK. If False something is wrong  #
	# INPUT: none						   #
	# OUTPUTS: BOOL | INT 					   #
	############################################################
	def _read(self):
		GPIO.output(self._pd_sck, False) # start by setting the pd_sck to false
		ready_counter = 0		# init the counter to 0
		while (not self._ready() and ready_counter <= 40): 
			time.sleep(0.01)	# sleep for 10 ms because data is not ready
			ready_counter += 1 	# increment counter
			if ready_counter == 50: # if counter reached max value then return False
				if self._debug_mode:
					print('self._read() not ready after 40 trials\n')
				return False
		
		# read first 24 bits of data
		data_in = 0	# 2's complement data from hx 711
		for i in range(24):
			start_counter = time.perf_counter() 	# start timer
			GPIO.output(self._pd_sck, True) 	# request next bit from hx 711
			GPIO.output(self._pd_sck, False)
			end_counter = time.perf_counter()	# stop timer
			if end_counter - start_counter >= 0.00006: # check if the hx 711 did not turn off...
			# if pd_sck pin is HIGH for 60 us and more than the HX 711 enters power down mode.
				if self._debug_mode:
					print('Not enough fast while reading data')
					print ('Time elapsed: ' + str(end_counter - start_counter))
				return False
			# Shift the bits as they come to data_in variable.
			# Left shift by one bit then bitwise OR with the new bit. 
			data_in = (data_in<<1) | GPIO.input(self._dout)
			
		if self._wanted_channel == 'A' and self._gain_channel_A == 128:
			if not self._set_channel_gain(1):	# send only one bit which is 1
				return False			# return False because channel was not set properly
			else:
				self._current_channel = 'A'	# else set current channel variable
				self._gain_channel_A = 128	# and gain
		elif self._wanted_channel == 'A' and self._gain_channel_A == 64:
			if not self._set_channel_gain(3):	# send three ones
				return False			# return False because channel was not set properly
			else:
				self._current_channel = 'A'	# else set current channel variable
				self._gain_channel_A = 64
		else:
			if  not self._set_channel_gain(2): 	# send two ones 
				return False			# return False because channel was not set properly
			else:
				self._current_channel = 'B'	# else set current channel variable
		
		if self._debug_mode:	# print 2's complement value
			print('Binary value as it has come: ' + str(bin(data_in)) + '\n')
		
		#check if data is valid
		if (data_in == 0x7fffff or 		# 0x7fffff is the highest possible value from hx711
			data_in == 0x800000):	# 0x800000 is the lowest possible value from hx711
			if self._debug_mode:
				print('Invalid data detected: ' + str(data_in) + '\n')
			return False			# rturn false because the data is invalid
		
		# calculate int from 2's complement 
		signed_data = 0
		if (data_in & 0x800000): # 0b1000 0000 0000 0000 0000 0000 check if the sign bit is 1. Negative number.
			signed_data = -((data_in ^ 0xffffff) + 1) # convert from 2's complement to int
		else:	# else do not do anything the value is positive number
			signed_data = data_in
		
		if self._debug_mode:
			print('Converted 2\'s complement value: ' + str(signed_data) + '\n')
		
		return signed_data
	
	############################################################
	# get_raw_data_mean returns mean value of readings.	   #
	# If return False something is wrong. Try debug mode.	   #
	# INPUTS: times # how many times to read data. Default 1   #
	# OUTPUTS: INT | BOOL					   #
	############################################################
	def get_raw_data_mean(self, times=1):
		backup_channel = self._current_channel 		# do backup of current channel befor reading for later use
		backup_gain = self._gain_channel_A		# backup of gain channel A
		if times > 0 and times < 100:		# check if times is in required range 
			data_list = []			# create empty list
			for i in range(times):		# for number of times read and add up all readings.
				data_list.append(self._read())	# append every read value to the list
			if times > 2 and self._pstdev_filter:			# if times is > 2 filter the data
				data_pstdev = stat.pstdev(data_list)	# calculate population standard deviation from the data
				data_mean = stat.mean(data_list)	# calculate mean from the collected data
				max_num = data_mean + data_pstdev	# calculate max number which is within pstdev
				min_num = data_mean - data_pstdev	# calculate min number which is within pstdev
				filtered_data = []			# create new list for filtered data
				
				if data_pstdev <=100:			# is pstdev is less than 100 it is ok
					self._save_last_raw_data(backup_channel, backup_gain, data_mean)	# save last data
					return data_mean		# just return the calculated mean

				for index,num in enumerate(data_list):	# now I know that pstdev is greater then iterate through the list
					if (num > min_num and num < max_num):	# check if the number is within pstdev
						filtered_data.append(num)	# then append to the filtered data list
				if self._debug_mode:
					print('data_list: ' + str(data_list))
					print('filtered_data lsit: ' + str(filtered_data))
					print('pstdev data: ' + str(data_pstdev))
					print('pstdev filtered data: ' + str(stat.pstdev(filtered_data)))
					print('mean data_list: ' + str(stat.mean(data_list)))
					print('mean filtered_data: ' + str(stat.mean(filtered_data)))
				f_data_mean = stat.mean(filtered_data)		# calculate mean from filtered data
				self._save_last_raw_data(backup_channel, backup_gain, f_data_mean)	# save last data
				return f_data_mean		# return mean from filtered data
			else: 
				data_mean = stat.mean(data_list)		# calculate mean from the list
				self._save_last_raw_data(backup_channel, backup_gain, data_mean)	# save last data
				return data_mean		# times was 2 or less just return mean
		else:
			raise ValueError('function "get_raw_data_mean" parameter "times" has to be in range 1 up to 99.\n I have got: '\
						+ str(times))
	
	############################################################
	# get_data_mean returns average value of readings minus    #
	# offset for the particular channel which was read.	   #
	# If return False something is wrong. Try debug mode.	   #
	# INPUTS: times # how many times to read data. Default 1   #
	# OUTPUTS: INT | BOOL					   #
	############################################################
	def get_data_mean(self, times=1):
		result = self.get_raw_data_mean(times)
		if result != False:
			if self._current_channel =='A' and self._gain_channel_A == 128:
				return result- self._offset_A_128
			elif self._current_channel == 'A' and self._gain_channel_A == 64:
				return result - self._offset_A_64
			else:
				return result - self._offset_B
		else:
			return False
	
	############################################################
	# get_weight_mean returns average value of readings minus  #
	# offset divided by scale ratio for a particular channel   #
	# and gain.						   #
	# If return False something is wrong. Try debug mode.	   #
	# INPUTS: times # how many times to read data. Default 1   #
	# OUTPUTS: INT | BOOL 					   #
	############################################################
	def get_weight_mean(self, times=1):
		result = self.get_raw_data_mean(times)
		if result != False:
			if self._current_channel =='A' and self._gain_channel_A == 128:
				return (result - self._offset_A_128) / self._scale_ratio_A_128
			elif self._current_channel == 'A' and self._gain_channel_A == 64:
				return (result - self._offset_A_64) / self._scale_ratio_A_64
			else:
				return (result - self._offset_B) / self._scale_ratio_B
		else:
			return False
	
	############################################################
	# get current channel returns the value of currently	   #
	# chosen channel					   #
	# INPUTS: none						   #
	# OUTPUTS: STRING('A'|'B')				   #
	############################################################
	def get_current_channel(self):
		return self._current_channel 
	
	############################################################
	# get pstdev filter status returns True if turned on.	   #
	# INPUTS: none						   #
	# OUTPUTS: INT						   #
	############################################################
	def get_pstdev_filter_status(self):
		return self._pstdev_filter
	
	############################################################
	# get current gain A returns the value of current gain on  #
	# the channel A						   #
	# INPUTS: none						   #
	# OUTPUTS: INT						   #
	############################################################
	def get_current_gain_A(self):
		return self._gain_channel_A
	
	############################################################
	# get last raw data returns the last read data for a 	   #
	# channel and gain. By default for currently chosen one.   #
	# INPUTS: channel('A'|'B'), gain(64|128)		   #
	# OUTPUTS: INT						   #
	############################################################
	def get_last_raw_data(self, channel='', gain_A=0):
		if channel == 'A' and gain_A == 128: 
			return self._last_raw_data_A_128
		elif channel == 'A' and gain_A == 64:
			return self._last_raw_data_A_64
		elif channel == 'B':
			return self._last_raw_data_B
		else:
			if self._current_channel == 'A' and self._gain_channel_A == 128:
				return self._last_raw_data_A_128
			elif self._current_channel == 'A' and self._gain_channel_A == 64:
				return self._last_raw_data_A_64
			else:
				return self._last_raw_data_B
	
	############################################################
	# get current offset returns the current offset for	   #
	# a particular channel and gain. By default the currently  #
	# chosen one.						   #
	# INPUTS: Channel('A'|'B'), Gain(64|128)		   #
	# OUTPUTS: INT						   #
	############################################################
	def get_current_offset(self, channel='', gain_A=0):
		if channel == 'A' and gain_A == 128: 
			return self._offset_A_128
		elif channel == 'A' and gain_A == 64:
			return self._offset_A_64
		elif channel == 'B':
			return self._offset_B
		else:
			if self._current_channel == 'A' and self._gain_channel_A == 128:
				return self._offset_A_128
			elif self._current_channel == 'A' and self._gain_channel_A == 64:
				return self._offset_A_64
			else:
				return self._offset_B
	
	############################################################
	# get current scale ratio returns the current scale ratio  #
	# for a particular channel and gain. By default 	   #
	# the currently chosen one.				   #
	# INPUTS: Channel('A'|'B'), Gain(64|128)		   #
	# OUTPUTS: INT						   #
	############################################################
	def get_current_scale_ratio(self, channel='', gain_A=0):
		if channel == 'A' and gain_A == 128: 
			return self._scale_ratio_A_128
		elif channel == 'A' and gain_A == 64:
			return self._scale_ratio_A_64
		elif channel == 'B':
			return self._scale_ratio_B
		else:
			if self._current_channel == 'A' and self._gain_channel_A == 128:
				return self._scale_ratio_A_128
			elif self._current_channel == 'A' and self._gain_channel_A == 64:
				return self._scale_ratio_A_64
			else:
				return self._scale_ratio_B
	
	############################################################
	# power down function turns off the hx711.		   #
	# INPUTS: none						   #
	# OUTPUTS: BOOL		# True then it is executed	   #
	############################################################
	def power_down(self):
		GPIO.output(self._pd_sck, False)
		GPIO.output(self._pd_sck, True)
		time.sleep(0.01)
		return True

	############################################################
	# power up function turns on the hx711.			   #
	# INPUTS: none						   #
	# OUTPUTS: BOOL 	# True then it is executed	   #
	############################################################
	def power_up(self):
		GPIO.output(self._pd_sck, False)
		time.sleep(0.01)
		return True

	############################################################
	# reset function resets the hx711 and prepare it for 	   #
	# the next reading.					   #
	# INPUTS: none						   #
	# OUTPUTS: BOOL 	# True then it is executed	   #
	############################################################
	def reset(self):
		self.power_down()
		self.power_up()
		result = self.get_raw_data_mean(6)
		if result != False:
			return True
		else:
			return False
