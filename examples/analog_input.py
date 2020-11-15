"""
 Copyright (c) 2020 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import asyncio
import sys
import time

from telemetrix_aio import telemetrix_aio

"""
This file demonstrates analog input using both callbacks and
polling. Time stamps are provided in both "cooked" and raw form
"""

# Setup a pin for analog input and monitor its changes
ANALOG_PIN = 2  # arduino pin number
POLL_TIME = 5  # number of seconds between polls

# Callback data indices
CB_PIN_MODE = 0
CB_PIN = 1
CB_VALUE = 2
CB_TIME = 3


async def the_callback(data):
    """
    A callback function to report data changes.

    :param data: [pin_mode, pin, current_reported_value,  timestamp]
    """

    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[CB_TIME]))
    print(f'Analog Call Input Callback: pin={data[CB_PIN]}, '
          f'Value={data[CB_VALUE]} Time={formatted_time} '
          f'(Raw Time={data[CB_TIME]})')


async def analog_in(my_board, pin):
    """
    This function establishes the pin as an
    analog input. Any changes on this pin will
    be reported through the call back function.

    Every 5 seconds the last value and time stamp is polled
    and printed.

    Also, the differential parameter is being used.
    The callback will only be called when there is
    difference of 5 or more between the current and
    last value reported.

    :param my_board: a pymata_express instance

    :param pin: Arduino pin number
    """
    await my_board.set_pin_mode_analog_input(pin, 5, the_callback)

    # await asyncio.sleep(5)
    # await my_board.disable_analog_reporting()
    # await asyncio.sleep(5)
    # await my_board.enable_analog_reporting()

    # run forever waiting for input changes
    try:
        while True:
            await asyncio.sleep(.001)

    except KeyboardInterrupt:
        await my_board.shutdown()
        sys.exit(0)


# get the event loop
loop = asyncio.get_event_loop()

# instantiate pymata_express
board = telemetrix_aio.TelemetrixAIO()

try:
    # start the main function
    loop.run_until_complete(analog_in(board, ANALOG_PIN))
except (KeyboardInterrupt, RuntimeError) as e:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
