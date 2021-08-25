#!/usr/bin/env python3
import RPi.GPIO as GPIO  # import GPIO
from hx711 import HX711  # import the class HX711
from hx711 import outliers_filter

try:
    GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering
    # Create an object hx which represents your real hx711 chip
    # Required input parameters are only 'dout_pin' and 'pd_sck_pin'
    # If you do not pass any argument 'gain_channel_A' then the default value is 128
    # If you do not pass any argument 'set_channel' then the default value is 'A'
    # you can set a gain for channel A even though you want to currently select channel B
    hx = HX711(
        dout_pin=21, pd_sck_pin=20, gain_channel_A=128, select_channel='B')

    err = hx.reset()  # Before we start, reset the hx711 ( not necessary)
    if err:  # you can check if the reset was successful
        print('not ready')
    else:
        print('Ready to use')

    hx.set_gain_A(
        gain=64)  # You can change the gain for channel A  at any time.
    hx.select_channel(
        channel='A')  # Select desired channel. Either 'A' or 'B' at any time.

    # Read data several, or only one, time and return mean value
    # argument "readings" is not required default value is 30
    data = hx.get_raw_data_mean(readings=30)

    if data:  # always check if you get correct value or only False
        print('Raw data:', data)
    else:
        print('invalid data')

    # measure tare and save the value as offset for current channel
    # and gain selected. That means channel A and gain 64
    result = hx.zero(readings=30)

    # Read data several, or only one, time and return mean value.
    # It subtracts offset value for particular channel from the mean value.
    # This value is still just a number from HX711 without any conversion
    # to units such as grams or kg.
    data = hx.get_data_mean(readings=30)

    if data:  # always check if you get correct value or only False
        # now the value is close to 0
        print('Data subtracted by offset but still not converted to any unit:',
              data)
    else:
        print('invalid data')

    # In order to calculate the conversion ratio to some units, in my case I want grams,
    # you must have known weight.
    input('Put known weight on the scale and then press Enter')
    data = hx.get_data_mean(readings=30)
    if data:
        print('Mean value from HX711 subtracted by offset:', data)
        known_weight_grams = input(
            'Write how many grams it was and press Enter: ')
        try:
            value = float(known_weight_grams)
            print(value, 'grams')
        except ValueError:
            print('Expected integer or float and I have got:',
                  known_weight_grams)

        # set scale ratio for particular channel and gain which is
        # used to calculate the conversion to units. Required argument is only
        # scale ratio. Without arguments 'channel' and 'gain_A' it sets
        # the ratio for current channel and gain.
        ratio = data / value  # calculate the ratio for channel A and gain 64
        hx.set_scale_ratio(ratio)  # set ratio for current channel
        print('Ratio is set.')
    else:
        raise ValueError('Cannot calculate mean value. Try debug mode.')

    # Read data several, or only one, time and return mean value
    # subtracted by offset and converted by scale ratio to
    # desired units. In my case in grams.
    print('Current weight on the scale in grams is: ')
    print(hx.get_weight_mean(30), 'g')

    # if you need the data fast without doing average or filtering them.
    # do some kind of loop and pass argument 'readings=1'. Default 'readings' is 30
    # be aware that HX711 sometimes return invalid or wrong data.
    # you can probably see it now
    print('Now I will print data quickly, but sometimes wrong.')
    input(
        'That is why I recommend always passing argument readings=20 or higher value'
    )
    for i in range(40):
        # the value will vary because it is only one immediate reading.
        # the default speed for hx711 is 10 samples per second
        print(hx.get_weight_mean(readings=1), 'g')

    # if you are not sure which gain is currently set on channel A you can call
    print('Current gain on channel A:', hx.get_current_gain_A())

    # to get currently selected channel
    print('Current channel is:', hx.get_current_channel())

    # to get current offset for a specific channel
    offset = hx.get_current_offset(channel='A', gain_A=128)
    print('Current offset for channel A and gain 128:', offset)
    # if no arguments passed then it return offset for the currently selected channel and gain
    offset = hx.get_current_offset()
    print('Current offset for channel A and the current gain (64):', offset)
    # for channel B
    offset = hx.get_current_offset(channel='B')
    print('Current offset for channel B:', offset)

    # to get current scale ratio
    current_ratio = hx.get_current_scale_ratio()
    print('Current scale ratio is set to:', current_ratio)

    # set offset manually for specific channel and gain. If you want to
    # set offset for channel B then argument 'gain_A' is not required
    # if no arguments 'channel' and 'gain_A' provided. The offset is
    # set for the current channel and gain. Such as:

    # hx.set_offset(offset=15000)

    input(
        'Now I will show you how it looks if you turn on debug mode. Press ENTER'
    )
    # turns on debug mode. It prints many things so you can find problem
    hx.set_debug_mode(flag=True)
    print(hx.get_raw_data_mean(
        4))  # now you can see many intermediate steps and values
    hx.set_debug_mode(False)

    #hx.power_down()        # turns off the hx711. Low power consumption
    #hx.power_up()            # turns on the hx711.
    #hx.reset()            # resets the hx711 and get it ready for
    # reading of the currently selected channel
    for i in range(2):
        # without argument 'readings' default is 30
        print('-> Weight channel A gain 64:', hx.get_weight_mean(20), 'g')
        print('-> Raw data channel A gain 64:', hx.get_raw_data_mean(20))
        print('--------------------------------------------')

        hx.set_gain_A(128)
        # without argument 'readings' default is 30
        print('-> Weight channel A gain 128:', hx.get_weight_mean(20), ' g')
        print('-> Raw data channel A gain 128:', hx.get_raw_data_mean(20))
        print('--------------------------------------------')
        
        hx.select_channel('B')
        print('Channel B selected')
        # without argument default is 1
        print('-> Weight channel B gain 32:', hx.get_weight_mean(20), 'g')
        print('-> Raw data channel B gain 32:', hx.get_raw_data_mean(20))
        
        # you can also get the last raw data read for each channel and gain without reading it again
        # without an argument it return raw data for currently set channel and gain, so channel B
        last_value = hx.get_last_raw_data()
        print('It remembers last raw data for channel B:', last_value)
        last_value = hx.get_last_raw_data(channel='A', gain_A=64)
        print('It remembers last raw data for channel A gain 64:', last_value)
        last_value = hx.get_last_raw_data(channel='A', gain_A=128)
        print('It remembers last raw data for channel A gain 128:', last_value)

    # To get the current data filter that is set
    current_filter = hx.get_data_filter()
    # To set a new data filter
    hx.set_data_filter(outliers_filter)
    # By default it is outliers_filter.
    # If you want to create your own filter, the requirement is simple.
    # It has to take a single argument that is a list of int and return list of int
    print('\nThat is all. Cleaning up.')
except (KeyboardInterrupt, SystemExit):
    print('Bye :)')

finally:
    GPIO.cleanup()
