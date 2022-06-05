"""
 Copyright (c) 2021 Alan Yorinks All rights reserved.

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
import asyncio
import time
import sys

from telemetrix_aio import telemetrix_aio

"""
Run a motor continuously without acceleration
"""


async def step_continuous(the_board):
    # create an accelstepper instance for a TB6600 motor driver
    motor = await the_board.set_pin_mode_stepper(interface=1, pin1=5, pin2=4)

    # if you are using a 28BYJ-48 Stepper Motor with ULN2003
    # comment out the line above and uncomment out the line below.
    # motor = await the_board.set_pin_mode_stepper(interface=4, pin1=5, pin2=4, pin3=14,
    # pin4=12)

    # set the max speed and speed
    await the_board.stepper_set_max_speed(motor, 900)
    await the_board.stepper_set_speed(motor, 800)
    # run the motor
    await the_board.stepper_run_speed(motor)

    # keep application running
    while True:
        try:
            await asyncio.sleep(.0002)
        except KeyboardInterrupt:
            await the_board.shutdown()
            sys.exit(0)

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix_aio
board = telemetrix_aio.TelemetrixAIO(ip_address='192.168.2.112')

try:
    # start the main function
    loop.run_until_complete(step_continuous(board))
    loop.run_until_complete(board.shutdown())

except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
