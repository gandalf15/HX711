#!/usr/bin/env python3

"""
This file holds HX711 class
"""

import statistics as stat
from time import sleep, perf_counter
from typing import List, Union

import RPi.GPIO as GPIO


class HX711:

    def __init__(self, dout_pin: int, pd_sck_pin: int,
                 gain_channel_A: int = 128,
                 select_channel: str = "A", debug: bool = False):
        """
        Init a new instance of HX711

        Args:
            dout_pin: pin number of Data pin
            pd_sck_pin: pin number of Clock pin
            gain_channel_A: options: 128, 64
            select_channel: options: 'A', 'B'
            debug: true to active debug_mode

        Raises:
            TypeError: if pd_sck_pin or dout_pin are not int type
        """
        # Check for the pins
        if (isinstance(dout_pin, int)):
            if (isinstance(pd_sck_pin, int)):
                self.pd_sck = pd_sck_pin
                self.dout = dout_pin
            else:
                raise TypeError('pd_sck_pin must be type int. '
                                'Received pd_sck_pin: {}'.format(pd_sck_pin))
        else:
            raise TypeError('dout_pin must be type int. '
                            'Received dout_pin: {}'.format(dout_pin))

        # Initialize variables
        self.gain_channel_A = 0
        self.offset_A_128 = 0  # offset channel A, gain 128
        self.offset_A_64 = 0  # offset channel A, gain 64
        self.offset_B = 0  # offset channel B
        self.last_raw_data_A_128 = 0
        self.last_raw_data_A_64 = 0
        self.last_raw_data_B = 0
        self.wanted_channel = ''
        self.current_channel = ''
        self.scale_ratio_A_128 = 1  # scale ratio channel A, gain 128
        self.scale_ratio_A_64 = 1  # scale ratio channel A, gain 64
        self.scale_ratio_B = 1  # scale ratio channel B
        self.debug_mode = debug
        self.data_filter = outliers_filter
        self.channel_options = 'A', 'B'
        self.gain_options = 64, 128

        # Setup GPIO
        GPIO.setup(self.pd_sck, GPIO.OUT)  # pin _pd_sck is output only
        GPIO.setup(self.dout, GPIO.IN)  # pin _dout is input only
        self.select_channel(select_channel)
        self.set_gain_A(gain_channel_A)

    def select_channel(self, channel: str):
        """
        select_channel method evaluates if the desired channel
        is valid and then sets the _wanted_channel variable.

        Args:
            channel: the channel to select. Options: 'A', 'B'
        Raises:
            ValueError: if channel is not 'A' or 'B'
        """
        channel = channel.capitalize()
        if channel in self.channel_options:
            self.wanted_channel = channel
        else:
            raise ValueError('Parameter "channel" has to be "A" or "B". '
                             'Received: {}'.format(channel))

        # After changing channel or gain it has to wait 50 ms to allow
        # adjustment. The data before is garbage and cannot be used.
        self.read()
        sleep(0.5)

    def set_gain_A(self, gain: int):
        """
        set_gain_A method sets gain for channel A.

        Args:
            gain: Gain for channel A. Options: 128, 64

        Raises:
            ValueError: if gain is different than 128 or 64
        """

        # Set the gain
        if gain in self.gain_options:
            self.gain_channel_A = gain
        else:
            raise ValueError(f'"gain" has to be 128 or 64. Received: {gain}')

        # After changing channel or gain it has to wait 50 ms to allow
        # adjustment. The data before is garbage and cannot be used.
        self.read()
        sleep(0.5)

    def zero(self, readings: int = 30) -> bool:
        """
        zero is a method which sets the current data as
        an offset for particulart channel. It can be used for
        subtracting the weight of the packaging. Also known as tare.

        Args:
            readings: Number of readings for mean. Allowed values 1..99

        Raises:
            ValueError: if readings are not in range 1..99

        Returns: True if error occured.
        """

        if readings in range(1, 100):
            result = self.get_raw_data_mean(readings)
            if result != False:
                if self.current_channel == 'A' and self.gain_channel_A == 128:
                    self.offset_A_128 = result
                    return False
                elif self.current_channel == 'A' and self.gain_channel_A == 64:
                    self.offset_A_64 = result
                    return False
                elif self.current_channel == 'B':
                    self.offset_B = result
                    return False
                else:
                    if self.debug_mode:
                        print('Cannot zero() channel and gain mismatch.\n'
                              f'current channel: {self.current_channel}\n'
                              f'gain A: {self.gain_channel_A}\n')
                    return True
            else:
                if self.debug_mode:
                    print('From method "zero()".\n'
                          'get_raw_data_mean(readings) returned False.\n')
                return True
        else:
            raise ValueError('Parameter "readings" can be '
                             f'in range 1 up to 99. Received: {readings}')

    def set_offset(self, offset: int, channel: str = '', gain_A: int = 0):
        """
        set offset method sets desired offset for specific
        channel and gain. Optional, by default it sets offset for current
        channel and gain.

        Args:
            offset: specific offset for channel
            channel: options: 'A', 'B', '' (current_channel)

        Raises:
            ValueError: if channel is not ('A' || 'B' || '')
            TypeError: if offset is not int type
        """
        channel = channel.capitalize()
        if isinstance(offset, int):
            if channel == '':
                channel = self.current_channel
            if channel == 'A' and gain_A == 128:
                self.offset_A_128 = offset
                return
            elif channel == 'A' and gain_A == 64:
                self.offset_A_64 = offset
                return
            elif channel == 'B':
                self.offset_B = offset
                return
            else:
                raise ValueError('Parameter "channel" has to be "A" or "B". '
                                 f'Received: {channel}')
        else:
            raise TypeError('Parameter "offset" has to be integer. '
                            f'Received: {offset}\n')

    def set_scale_ratio(self, scale_ratio: float, channel: str = '',
                        gain_A: int = 0):
        """
        set_scale_ratio method sets the ratio for calculating
        weight in desired units. In order to find this ratio for
        example to grams or kg. You must have known weight.

        Args:
            scale_ratio: number > 0.0 that is used for conversion to grams
            channel: Options: 'A', 'B'
            gain_A: Options: 128, 64
        Raises:
            ValueError: if channel is not ('A' || 'B' || '')
            TypeError: if offset is not int type
        """
        channel = channel.capitalize()
        if isinstance(gain_A, int):
            if channel == '':
                channel = self.current_channel
            if channel == 'A' and gain_A == 128:
                self.scale_ratio_A_128 = scale_ratio
                return
            elif channel == 'A' and gain_A == 64:
                self.scale_ratio_A_64 = scale_ratio
                return
            elif channel == 'B':
                self.scale_ratio_B = scale_ratio
                return

                if channel == 'A' and self.gain_channel_A == 128:
                    self.scale_ratio_A_128 = scale_ratio
                    return
                elif channel == 'A' and self.gain_channel_A == 64:
                    self.scale_ratio_A_64 = scale_ratio
                    return
                else:
                    self.scale_ratio_B = scale_ratio
                    return
            else:
                raise ValueError('Parameter "channel" has to be "A" or "B". '
                                 f'Received: {channel}\n')
        else:
            raise TypeError('Parameter "gain_A" has to be integer. '
                            f'Received: {gain_A}\n')

    def set_data_filter(self, data_filter: callable):
        """
        set_data_filter method sets data filter that is passed as an argument.

        Args:
            data_filter: Data filter that takes list of int numbers and
                         returns a list of filtered int numbers.

        Raises:
            TypeError: if filter is not a function.
        """
        if callable(data_filter):
            self.data_filter = data_filter
        else:
            raise TypeError('Parameter "data_filter" must be a function. '
                            f'Received: {data_filter}')

    def set_debug_mode(self, flag: bool):
        """
        set_debug_mode method is for turning on and off
        debug mode.

        Args:
            flag: True turns on the debug mode. False turns it off.

        Raises:
            ValueError: if fag is not bool type
        """
        if flag == False:
            self.debug_mode = False
            print('Debug mode DISABLED')
            return
        elif flag == True:
            self.debug_mode = True
            print('Debug mode ENABLED')
            return
        else:
            raise ValueError('Parameter "flag" can be only bool value. '
                             f'Received: {flag}')

    def save_last_raw_data(self, channel: str, gain_A: int,
                            data: int) -> bool:
        """
        _save_last_raw_data saves the last raw data for specific channel
        and gain.

        Returns: False if error occured
        """
        if channel == 'A' and gain_A == 128:
            self.last_raw_data_A_128 = data
            return True
        elif channel == 'A' and gain_A == 64:
            self.last_raw_data_A_64 = data
            return True
        elif channel == 'B':
            self.last_raw_data_B = data
            return True
        else:
            return False

    def ready(self) -> bool:
        """
        _ready method check if data is prepared for reading from HX711

        Returns: bool True if ready else False when not ready        
        """

        # if DOUT pin is low data is ready for reading
        return not GPIO.input(self.dout)

    def set_channel_gain(self, num: int) -> bool:
        """
        _set_channel_gain is called only from _read method.
        It finishes the data transmission for HX711 which sets
        the next required gain and channel.

        Args:
            num: how many ones it sends to HX711 (1...3)

        Returns: True if HX711 is ready for the next reading
                 False if HX711 is not ready for the next reading
        """
        for _ in range(num):
            start_counter = perf_counter()
            GPIO.output(self.pd_sck, True)
            GPIO.output(self.pd_sck, False)
            end_counter = perf_counter()
            # check if HX711 did not turn off...
            if end_counter - start_counter >= 0.00006:
                # if pd_sck pin is HIGH for 60 us and more than
                # the HX711 enters power down mode.
                if self.debug_mode:
                    print('Not enough fast while setting gain and channel')
                    print(f'Time elapsed: {end_counter - start_counter}')
                # HX711 has turned off. First few readings are inaccurate.
                # Despite it, this reading was ok and data can be used.
                result = self.get_raw_data_mean(6)  # set for the next reading
                if result == False:
                    return False
        return True

    def read(self) -> Union[int, bool]:
        """
        _read method reads bits from hx711, converts to INT
        and validate the data.

        Returns: if it returns False then it is false reading.
                 if it returns int then the reading was correct
        """

        # Start by setting the pd_sck to 0
        GPIO.output(self.pd_sck, False)
        ready_counter = 0

        # Check if the sensor is ready
        while (not self.ready() and ready_counter <= 40):
            sleep(0.01)  # sleep for 10 ms because data is not ready
            ready_counter += 1
            if ready_counter == 40:
                if self.debug_mode:
                    print('self.read() not ready after 40 trials\n')
                return False

        # Read first 24 bits of data
        data_in = 0  # 2's complement data from HX711
        for _ in range(24):
            start_counter = perf_counter()
            # Request next bit from HX711
            GPIO.output(self.pd_sck, True)
            GPIO.output(self.pd_sck, False)
            end_counter = perf_counter()
            # Check if the hx 711 did not turn off...
            if end_counter - start_counter >= 0.00006:
                # if pd_sck pin is HIGH for 60 us and more than
                # the HX 711 enters power down mode.
                if self.debug_mode:
                    print('Not enough fast while reading data')
                    print(f'Time elapsed: {end_counter - start_counter}')
                return False
            # Shift the bits as they come to data_in variable.
            # Left shift by one bit then bitwise OR with the new bit.
            data_in = (data_in << 1) | GPIO.input(self.dout)

        if self.wanted_channel == 'A' and self.gain_channel_A == 128:
            if not self.set_channel_gain(1):  # send only one bit which is 1
                return False  # channel was not set properly
            else:
                self.current_channel = 'A'  # set current channel variable
                self.gain_channel_A = 128  # and gain
        elif self.wanted_channel == 'A' and self.gain_channel_A == 64:
            if not self.set_channel_gain(3):  # send three ones
                return False  # channel was not set properly
            else:
                self.current_channel = 'A'  # set current channel variable
                self.gain_channel_A = 64  # and gain
        else:
            if not self.set_channel_gain(2):  # send two ones
                return False  # channel was not set properly
            else:
                self.current_channel = 'B'  # set current channel variable

        if self.debug_mode:  # print 2's complement value
            print(f'Binary value as received: {bin(data_in)}\n')

        # Check if data is valid
        if (data_in == 0x7fffff or data_in == 0x800000):
            # 0x7fffff is the highest possible value from HX711
            # 0x800000 is the lowest possible value from HX711
            if self.debug_mode:
                print(f'Invalid data detected: {data_in}\n')
            return False  # the data is invalid

        # calculate int from 2's complement
        signed_data = 0
        # 0b1000 0000 0000 0000 0000 0000
        # check if the sign bit is 1. Negative number.
        if (data_in & 0x800000):
            # convert from 2's complement to int
            signed_data = -((data_in ^ 0xffffff) + 1)
        else:
            # else do not do anything the value is positive number
            signed_data = data_in

        if self.debug_mode:
            print(f'Converted 2\'s complement value: {signed_data}\n')

        return signed_data

    def get_raw_data_mean(self, readings: int = 30) -> Union[bool, int]:
        """
        get_raw_data_mean returns mean value of readings.

        Args:
            readings: Number of readings for mean.

        Returns: if False then reading is invalid.
                 if it returns int then reading is valid
        """

        # do backup of current channel befor reading for later use
        backup_channel = self.current_channel
        backup_gain = self.gain_channel_A
        data_list = []

        # do required number of readings
        for _ in range(readings):
            data_list.append(self.read())
        data_mean = False
        if readings > 2 and self.data_filter:
            filtered_data = self.data_filter(data_list)
            if self.debug_mode:
                print('data_list:', data_list)
                print('filtered_data list:', filtered_data)
                print('data_mean:', stat.mean(filtered_data))
            data_mean = stat.mean(filtered_data)
        else:
            data_mean = stat.mean(data_list)
        self.save_last_raw_data(backup_channel, backup_gain, data_mean)
        return int(data_mean)

    def get_data_mean(self, readings: int = 30) -> Union[bool, int]:
        """
        get_data_mean returns average value of readings minus
        offset for the channel which was read.

        Args:
            readings: Number of readings for mean

        Returns: False if reading was not ok.
                 If it returns int then reading was ok
        """

        result = self.get_raw_data_mean(readings)
        if result != False:
            if self.current_channel == 'A' and self.gain_channel_A == 128:
                return result - self.offset_A_128
            elif self.current_channel == 'A' and self.gain_channel_A == 64:
                return result - self.offset_A_64
            else:
                return result - self.offset_B
        else:
            return False

    def get_weight_mean(self, readings: int = 30) -> Union[bool, float]:
        """
        get_weight_mean returns average value of readings minus
        offset divided by scale ratio for a specific channel
        and gain.

        Args:
            readings: Number of readings for mean

        Returns: False if reading was not ok.
                 If it returns float then reading was ok
        """

        result = self.get_raw_data_mean(readings)
        if result != False:
            if self.current_channel == 'A' and self.gain_channel_A == 128:
                return float(
                    (result - self.offset_A_128) / self.scale_ratio_A_128)
            elif self.current_channel == 'A' and self.gain_channel_A == 64:
                return float(
                    (result - self.offset_A_64) / self.scale_ratio_A_64)
            else:
                return float((result - self.offset_B) / self.scale_ratio_B)
        else:
            return False

    def get_last_raw_data(self, channel: str = '', gain_A: int=0) -> int:
        """
        get last raw data returns the last read data for a
        channel and gain. By default for current one.

        Args:
            channel: options: 'A', 'B'
            gain_A: options: 128, 64

        Raises:
            ValueError: if channel or gain are not in list

        Returns: the last data that was received for the chosen
                 channel and gain
        """

        channel = channel.capitalize()
        if channel == '':
            channel = self.current_channel
        if channel == 'A' and gain_A == 128:
            return self.last_raw_data_A_128
        elif channel == 'A' and gain_A == 64:
            return self.last_raw_data_A_64
        elif channel == 'B':
            return self.last_raw_data_B
        else:
            raise ValueError('Parameter "channel" has to be "A" or "B". '
                             f'Received: {channel} \nParameter "gain_A" has to be 128'
                             f'or 64. Received {gain_A}')

    def get_current_offset(self, channel: str = '', gain_A: int=0) -> int:
        """
        get current offset returns the current offset for
        a particular channel and gain. By default the current one.

        Args:
            channel: options: 'A', 'B', '' (current)
            gain_A: options: 128, 64, 0 (current)

        Raises:
            ValueError: if channel or gain are not in list

        Returns: int the offset for the chosen channel and gain
        """
        channel = channel.capitalize()
        if channel == '':
            channel = self.current_channel
        if channel == 'A' and gain_A == 128:
            return self.offset_A_128
        elif channel == 'A' and gain_A == 64:
            return self.offset_A_64
        elif channel == 'B':
            return self.offset_B
        else:
            raise ValueError(
                'Parameter "channel" has to be "A" or "B". '
                f'Received: {channel} \nParameter "gain_A" has to be '
                f'128 or 64. Received {gain_A}')

    def get_current_scale_ratio(self, channel: str = '', gain_A: int=0) -> int:
        """
        get current scale ratio returns the current scale ratio
        for a particular channel and gain. By default
        the current one.

        Args:
            channel: options:  'A', 'B'
            gain_A: options: 128, 64

        Returns: the scale ratio for the chosen channel and gain
        """
        channel = channel.capitalize()
        if channel == '':
            channel = self.current_channel
        if channel == 'A' and gain_A == 128:
            return self.scale_ratio_A_128
        elif channel == 'A' and gain_A == 64:
            return self.scale_ratio_A_64
        elif channel == 'B':
            return self.scale_ratio_B
        else:
            raise ValueError(
                'Parameter "channel" has to be "A" or "B". '
                f'Received: {channel} \nParameter "gain_A" has to be'
                f' 128 or 64. Received {gain_A}')

    def power_down(self):
        """
        power down method turns off the hx711.
        """
        GPIO.output(self.pd_sck, False)
        GPIO.output(self.pd_sck, True)
        sleep(0.01)

    def power_up(self):
        """
        power up function turns on the hx711.
        """
        GPIO.output(self.pd_sck, False)
        sleep(0.01)

    def reset(self) -> bool:
        """
        reset method resets the hx711 and prepare it for the next reading.

        Returns: True if error encountered
        """
        self.power_down()
        self.power_up()
        result = self.get_raw_data_mean(6)
        if result:
            return False
        else:
            return True


def outliers_filter(data: List[Union[int, bool]], m: float = 1.5) -> List[int]:
    """
    It filters out outliers from the provided list of int.
    Median is used as an estimator of outliers.

    Args:
        data_list: data to be filtered
        m: the maximum ratio (default = 1.0)
        NB. if max_ratio is bigger, more outliers are keep; if it's
            smaller, more outliers are deleted

    Returns: list of filtered data. Excluding outliers.
    """

    # Remove non integer data
    data = list(filter(lambda x: x, data))

    # Check if all values are the same
    if all([n == data[0] for n in data]):
        return data[0]

    # Calculate the median
    median = stat.median(data)

    # Calculate the absolute distance for each number from the
    # median and calculate the median of the distances
    distance = [abs(n - median) for n in data]
    m_distance = stat.median(distance)

    # Calculate the ratio between the distance from the median
    # and the median distance for each number
    r = [d / m_distance for d in distance]

    # Return all the numbers that aren't outliers
    return [data[i] for i in range(len(data)) if r[i] < m]
