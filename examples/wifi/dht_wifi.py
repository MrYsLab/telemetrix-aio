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

import sys
import time
import asyncio
from telemetrix_aio import telemetrix_aio

"""
This program monitors a DHT 22 sensor. 
"""

# indices into callback data for valid data
REPORT_TYPE = 0
PIN = 1
HUMIDITY = 2
TEMPERATURE = 3
TIME = 4


# indices into callback data for error report
# REPORT_TYPE = 0
# PIN = 1
# ERROR_VALUE = 2

# A callback function to display the distance
async def the_callback(data):
    """
    The callback function to display the change in distance
    :param data: [report_type = PrivateConstants.DHT, pin number, humidity, temperature timestamp]
                 if this is an error report:
                 [report_type = PrivateConstants.DHT, pin number, error value timestamp]
    """
    if data[1]:
        # error message
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[4]))
        print(f'DHT Error Report:'
              f'Pin: {data[2]} Error: {data[3]}  Time: {date}')
    else:
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[5]))
        print(f'DHT Valid Data Report:'
              f'Pin: {data[2]} Humidity: {data[3]} Temperature: {data[4]} Time: {date}')


async def dht(my_board, pin, callback):
    """
    Set the pin mode for a DHT 22 device. Results will appear via the
    callback.

    :param my_board: telemetrix-aio instance
    :param pin: Arduino pin number
    :param callback: The callback function
    """

    # set the pin mode for the trigger and echo pins
    await my_board.set_pin_mode_dht(pin, callback)
    # wait forever
    while True:
        try:
            await asyncio.sleep(.01)
        except KeyboardInterrupt:
            await my_board.shutdown()
            sys.exit(0)


# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix_aio
board = telemetrix_aio.TelemetrixAIO(ip_address='192.168.2.220')

try:
    # start the main function
    loop.run_until_complete(dht(board, 5, the_callback))
except (KeyboardInterrupt, RuntimeError) as e:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
