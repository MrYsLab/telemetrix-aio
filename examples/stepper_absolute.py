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

"""
import asyncio
import sys
import time

from telemetrix_aio import telemetrix_aio

"""
Run a motor to an absolute position. Server will send a callback notification 
when motion is complete.
"""


async def the_callback(data):
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[2]))
    print(f'Motor {data[1]} absolute motion completed at: {date}.')


async def running_callback(data):
    if data[1]:
        print('The motor is running.')
    else:
        print('The motor IS NOT running.')


async def step_absolute(the_board):

    # create an accelstepper instance for a TB6600 motor driver
    motor = await the_board.set_pin_mode_stepper(interface=1, pin1=8, pin2=9)

    # if you are using a 28BYJ-48 Stepper Motor with ULN2003
    # comment out the line above and uncomment out the line below.
    # motor = the_board.set_pin_mode_stepper(interface=4, pin1=5, pin2=4, pin3=14,
    # pin4=12)

    await the_board.stepper_is_running(motor, callback=running_callback)
    await asyncio.sleep(.2)

    # set the max speed and acceleration
    await the_board.stepper_set_max_speed(motor, 400)
    await the_board.stepper_set_acceleration(motor, 800)

    # set the absolute position in steps
    await the_board.stepper_move_to(motor, -2000)

    # run the motor
    print('Starting motor...')
    await the_board.stepper_run(motor, completion_callback=the_callback)
    await asyncio.sleep(.2)
    await the_board.stepper_is_running(motor, callback=running_callback)
    await asyncio.sleep(.2)

    # keep application running
    while True:
        try:
            await asyncio.sleep(.2)

        except KeyboardInterrupt:
            await the_board.shutdown()
            sys.exit(0)

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix_aio
board = telemetrix_aio.TelemetrixAIO()
try:
    # start the main function
    loop.run_until_complete(step_absolute(board))
    loop.run_until_complete(board.shutdown())

except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
