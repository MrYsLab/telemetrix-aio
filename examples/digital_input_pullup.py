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
Setup a digital pin for input pullup and monitor its changes.
"""

# some globals
DIGITAL_PIN = 12  # arduino pin number
KILL_TIME = 5  # sleep time to keep forever loop open

# Callback data indices
# Callback data indices
CB_PIN_MODE = 0
CB_PIN = 1
CB_VALUE = 2
CB_TIME = 3


# Set up a pin for digital pin input and monitor its changes

async def the_callback(data):
    """
    A callback function to report data changes.
    This will print the pin number, its reported value and
    the date and time when the change occurred

    :param data: [pin, current reported value, pin_mode, timestamp]
    """
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[CB_TIME]))
    print(f'Pin: {data[CB_PIN]} Value: {data[CB_VALUE]} Time Stamp: {date}')


async def digital_in_pullup(my_board, pin):
    """
     This function establishes the pin as a
     digital input. Any changes on this pin will
     be reported through the call back function.

     :param my_board: a telemetrix_aio instance
     :param pin: Arduino pin number
     """

    # start monitoring the pin by setting its mode
    await my_board.set_pin_mode_digital_input_pullup(pin, the_callback)

    # get pin changes forever
    while True:
        try:
            await asyncio.sleep(KILL_TIME)
        except KeyboardInterrupt:
            await board.shutdown()
            sys.exit(0)


# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix_aio
board = telemetrix_aio.TelemetrixAIO()

try:
    # start the main function
    loop.run_until_complete(digital_in_pullup(board, 12))
except (KeyboardInterrupt, RuntimeError) as e:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
