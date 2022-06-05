# noinspection GrazieInspection
"""
 Copyright (c) 2021 Alan Yorinks All rights reserved.

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

"""
This example initializes an MPU9250 and then reads the accelerometer
and gyro values and prints them to the screen.

The processing of the data returned from the MPU9250 is done within 
the callback functions.
"""

import asyncio
import sys
import time

from telemetrix_aio import telemetrix_aio

# Instantiate the TelemetrixRpiPico class accepting all default parameters.
# board = telemetrix_aio.TelemetrixAIO(ip_address='192.168.2.112')


# Convenience values for the pins.
# Note that the CS value is within a list
# These are the standard pins for many Arduino AVR boards.
# Change to match your particular board.


# device select is GPIO 5
CS = [5]
CS_PIN = 5

# NodeMCU                MPU9250
# MOSI = GPIO13          SDA
# MISO = GPIO12          ADO
# SCLK = GPIO14          SCL
# CS = GPIO5             NCS
NUM_BYTES_TO_READ = 6

"""
 CALLBACKS
 
 These functions process the data returned from the MPU9250
"""


async def the_device_callback(report):
    """
    Verify the device ID
    :param report: [SPI_REPORT, read register, Number of bytes, device_id]
    """
    if report[3] == 0x71:
        print('MPU9250 Device ID confirmed.')
    else:
        print(f'Unexpected device ID: {report[3]}')


# noinspection GrazieInspection
async def accel_callback(report):
    """
    Print the AX, AY and AZ values.
    :param report: [SPI_REPORT, Register, Number of bytes, AX-msb, AX-lsb
    AY-msb, AY-lsb, AX-msb, AX-lsb]
    """
    print(f"AX = {int.from_bytes(report[3:5], byteorder='big', signed=True)}  "
          f"AY = {int.from_bytes(report[5:7], byteorder='big', signed=True)}  "
          f"AZ = {int.from_bytes(report[7:9], byteorder='big', signed=True)}  ")


async def gyro_callback(report):
    # noinspection GrazieInspection
    """
        Print the GX, GY, and GZ values.

        :param report: [SPI_REPORT, Register, Number of bytes, GX-msb, GX-lsb
        GY-msb, GY-lsb, GX-msb, GX-lsb]
        """

    print(f"GX = {int.from_bytes(report[3:5], byteorder='big', signed=True)}  "
          f"GY = {int.from_bytes(report[5:7], byteorder='big', signed=True)}  "
          f"GZ = {int.from_bytes(report[7:9], byteorder='big', signed=True)}  ")


# This is a utility function to read SPI data
async def read_data_from_device(register, number_of_bytes, callback):
    # noinspection GrazieInspection
    """
    This function reads the number of bytes using the register value.
    Data is returned via the specified callback.fg

    :param register: register value
    :param number_of_bytes: number of bytes to read
    :param callback: callback function
    """
    # the read bit is OR'ed in on the device sketch
    data = register

    # activate chip select
    await board.spi_cs_control(CS_PIN, 0)

    await board.spi_read_blocking(data, number_of_bytes, call_back=callback)

    # deactivate chip select
    await board.spi_cs_control(CS_PIN, 1)
    time.sleep(.1)


async def spi_example(the_board):

    # initialize the device
    await board.set_pin_mode_spi(CS)

    # reset the device
    await the_board.spi_cs_control(CS_PIN, 0)
    await the_board.spi_write_blocking([0x6B, 0])
    await the_board.spi_cs_control(CS_PIN, 1)

    await asyncio.sleep(.1)

    # get the device ID
    await read_data_from_device(0x75, 1, the_device_callback)

    while True:
        try:
            await asyncio.sleep(1)
            # get the acceleration values
            await read_data_from_device(0x3b, 6, accel_callback)
            await asyncio.sleep(.1)

            # get the gyro values
            await read_data_from_device(0x43, 6, gyro_callback)
            await asyncio.sleep(.1)
        except KeyboardInterrupt:
            await the_board.shutdown()
            sys.exit(0)

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix_aio
board = telemetrix_aio.TelemetrixAIO(ip_address='192.168.2.220')

try:
    # start the main function
    loop.run_until_complete(spi_example(board))
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
