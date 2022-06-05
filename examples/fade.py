"""
 Copyright (c) 2020 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,f
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 DHT support courtesy of Martyn Wheeler
 Based on the DHTNew library - https://github.com/RobTillaart/DHTNew
"""

import sys
import time
import asyncio

from telemetrix_aio import telemetrix_aio

"""
Setup a pin for output and fade its intensity
"""

# some globals
# make sure to select a PWM pin
DIGITAL_PIN = 6


async def fade(the_board, pin):
    # Set the DIGITAL_PIN as an output pin
    await the_board.set_pin_mode_analog_output(pin)

    # When hitting control-c to end the program
    # in this loop, we are likely to get a KeyboardInterrupt
    # exception. Catch the exception and exit gracefully.

    try:
        print('Fading up...')
        for i in range(255):
            await the_board.analog_write(DIGITAL_PIN, i)
            await asyncio.sleep(.005)
        print('Fading down...')
        for i in range(255, -1, -1):
            await the_board.analog_write(DIGITAL_PIN, i)
            await asyncio.sleep(.005)
    except KeyboardInterrupt:
        the_board.shutdown()
        sys.exit(0)

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix_aio
board = telemetrix_aio.TelemetrixAIO()

try:
    # start the main function
    loop.run_until_complete(fade(board, DIGITAL_PIN))
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
