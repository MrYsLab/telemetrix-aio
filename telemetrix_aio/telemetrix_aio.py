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
import socket
import struct
import sys
import time
# noinspection PyPackageRequirements
from serial.tools import list_ports
# noinspection PyPackageRequirementscd
from serial.serialutil import SerialException

from telemetrix_aio.private_constants import PrivateConstants
from telemetrix_aio.telemtrix_aio_serial import TelemetrixAioSerial
from telemetrix_aio.telemetrix_aio_socket import TelemetrixAioSocket


class TelemetrixAIO:
    """
    This class exposes and implements the TelemetrixAIO API.
    It includes the public API methods as well as
    a set of private methods. This is an asyncio API.

    """

    # noinspection PyPep8,PyPep8
    def __init__(self, com_port=None,
                 arduino_instance_id=1, arduino_wait=4,
                 sleep_tune=0.0001, autostart=True,
                 loop=None, shutdown_on_exception=True,
                 close_loop_on_shutdown=True,
                 ip_address=None, ip_port=31335):

        """
        If you have a single Arduino connected to your computer,
        then you may accept all the default values.

        Otherwise, specify a unique arduino_instance id for each board in use.

        :param com_port: e.g. COM3 or /dev/ttyACM0.

        :param arduino_instance_id: Must match value in the Telemetrix4Arduino sketch

        :param arduino_wait: Amount of time to wait for an Arduino to
                             fully reset itself.

        :param sleep_tune: A tuning parameter (typically not changed by user)

        :param autostart: If you wish to call the start method within
                          your application, then set this to False.

        :param loop: optional user provided event loop

        :param shutdown_on_exception: call shutdown before raising
                                      a RunTimeError exception, or
                                      receiving a KeyboardInterrupt exception

        :param close_loop_on_shutdown: stop and close the event loop loop
                                       when a shutdown is called or a serial
                                       error occurs

        """
        # check to make sure that Python interpreter is version 3.8.3 or greater
        python_version = sys.version_info
        if python_version[0] >= 3:
            if python_version[1] >= 8:
                if python_version[2] >= 3:
                    pass
            else:
                raise RuntimeError("ERROR: Python 3.8.3 or greater is "
                                   "required for use of this program.")

        # save input parameters
        self.com_port = com_port
        self.arduino_instance_id = arduino_instance_id
        self.arduino_wait = arduino_wait
        self.sleep_tune = sleep_tune
        self.autostart = autostart
        self.ip_address = ip_address
        self.ip_port = ip_port

        # if tcp, this variable is set to the connected socket
        self.sock = None

        # set the event loop
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        self.shutdown_on_exception = shutdown_on_exception
        self.close_loop_on_shutdown = close_loop_on_shutdown

        # dictionaries to store the callbacks for each pin
        self.analog_callbacks = {}

        self.digital_callbacks = {}

        self.i2c_callback = None
        self.i2c_callback2 = None

        self.i2c_1_active = False
        self.i2c_2_active = False

        # debug loopback callback method
        self.loop_back_callback = None

        # the trigger pin will be the key to retrieve
        # the callback for a specific HC-SR04
        self.sonar_callbacks = {}

        self.sonar_count = 0

        self.dht_callbacks = {}

        self.dht_count = 0

        # serial port in use
        self.serial_port = None

        # generic asyncio task holder
        self.the_task = None

        # flag to indicate we are in shutdown mode
        self.shutdown_flag = False

        self.report_dispatch = {}

        # To add a command to the command dispatch table, append here.
        self.report_dispatch.update({PrivateConstants.LOOP_COMMAND: self._report_loop_data})
        self.report_dispatch.update({PrivateConstants.DEBUG_PRINT: self._report_debug_data})
        self.report_dispatch.update({PrivateConstants.DIGITAL_REPORT: self._digital_message})
        self.report_dispatch.update({PrivateConstants.ANALOG_REPORT: self._analog_message})
        self.report_dispatch.update({PrivateConstants.SERVO_UNAVAILABLE: self._servo_unavailable})
        self.report_dispatch.update({PrivateConstants.I2C_READ_REPORT: self._i2c_read_report})
        self.report_dispatch.update({PrivateConstants.I2C_TOO_FEW_BYTES_RCVD: self._i2c_too_few})
        self.report_dispatch.update({PrivateConstants.I2C_TOO_MANY_BYTES_RCVD: self._i2c_too_many})
        self.report_dispatch.update({PrivateConstants.SONAR_DISTANCE: self._sonar_distance_report})
        self.report_dispatch.update({PrivateConstants.DHT_REPORT: self._dht_report})

        print(f'TelemetrixAIO Version: {PrivateConstants.TELEMETRIX_AIO_VERSION}')
        print(f'Copyright (c) 2018-2020 Alan Yorinks All rights reserved.\n')

        if autostart:
            self.loop.run_until_complete(self.start_aio())

    async def start_aio(self):
        """
        This method may be called directly, if the autostart
        parameter in __init__ is set to false.

        This method instantiates the serial interface and then performs auto pin
        discovery if using a serial interface, or creates and connects to
        a TCP/IP enabled device running StandardFirmataWiFi.

        Use this method if you wish to start TelemetrixAIO manually from
        an asyncio function.
         """

        if not self.ip_address:
            if not self.com_port:
                # user did not specify a com_port
                try:
                    await self._find_arduino()
                except KeyboardInterrupt:
                    if self.shutdown_on_exception:
                        await self.shutdown()
            else:
                # com_port specified - set com_port and baud rate
                try:
                    await self._manual_open()
                except KeyboardInterrupt:
                    if self.shutdown_on_exception:
                        await self.shutdown()

            if self.com_port:
                print(f'Telemetrix4AIO found and connected to {self.com_port}')

                # no com_port found - raise a runtime exception
            else:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('No Arduino Found or User Aborted Program')
        # using tcp/ip
        else:
            self.sock = TelemetrixAioSocket(self.ip_address, self.ip_port, self.loop)
            await self.sock.start()
            # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.sock.connect((self.ip_address, self.ip_port))
            # print(f'Successfully connected to: {self.ip_address}:{self.ip_port}')

        # get arduino firmware version and print it
        firmware_version = await self._get_firmware_version()
        if not firmware_version:
            print('*** Firmware Version retrieval timed out. ***')
            print('\nDo you have Arduino connectivity and do you have the ')
            print('Telemetrix4Arduino sketch uploaded to the board and are connected')
            print('to the correct serial port.\n')
            print('To see a list of serial ports, type: '
                  '"list_serial_ports" in your console.')
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError
        else:
            print(f'Telemetrix4Arduino Version Number: {firmware_version[2]}.'
                  f'{firmware_version[3]}')
            # start the command dispatcher loop
            command = [PrivateConstants.ENABLE_ALL_REPORTS]
            await self._send_command(command)
            if not self.loop:
                self.loop = asyncio.get_event_loop()
            self.the_task = self.loop.create_task(self._arduino_report_dispatcher())

            # Have the server reset its data structures
            command = [PrivateConstants.RESET]
            await self._send_command(command)

    async def get_event_loop(self):
        """
        Return the currently active asyncio event loop

        :return: Active event loop

        """
        return self.loop

    async def _find_arduino(self):
        """
        This method will search all potential serial ports for an Arduino
        containing a sketch that has a matching arduino_instance_id as
        specified in the input parameters of this class.

        This is used explicitly with the FirmataExpress sketch.
        """

        # a list of serial ports to be checked
        serial_ports = []

        print('Opening all potential serial ports...')
        the_ports_list = list_ports.comports()
        for port in the_ports_list:
            if port.pid is None:
                continue
            print('\nChecking {}'.format(port.device))
            try:
                self.serial_port = TelemetrixAioSerial(port.device, 115200,
                                                       telemetrix_aio_instance=self,
                                                       close_loop_on_error=self.close_loop_on_shutdown)
            except SerialException:
                continue
            # create a list of serial ports that we opened
            serial_ports.append(self.serial_port)

            # display to the user
            print('\t' + port.device)

            # clear out any possible data in the input buffer
            await self.serial_port.reset_input_buffer()

        # wait for arduino to reset
        print('\nWaiting {} seconds(arduino_wait) for Arduino devices to '
              'reset...'.format(self.arduino_wait))
        await asyncio.sleep(self.arduino_wait)

        print('\nSearching for an Arduino configured with an arduino_instance = ',
              self.arduino_instance_id)

        for serial_port in serial_ports:
            self.serial_port = serial_port

            command = [PrivateConstants.ARE_U_THERE]
            await self._send_command(command)
            # provide time for the reply
            await asyncio.sleep(.1)

            i_am_here = await self.serial_port.read(3)

            if not i_am_here:
                continue

            # got an I am here message - is it the correct ID?
            if i_am_here[2] == self.arduino_instance_id:
                self.com_port = serial_port.com_port
                return

    async def _manual_open(self):
        """
        Com port was specified by the user - try to open up that port

        """
        # if port is not found, a serial exception will be thrown
        print('Opening {} ...'.format(self.com_port))
        self.serial_port = TelemetrixAioSerial(self.com_port, 115200,
                                               telemetrix_aio_instance=self,
                                               close_loop_on_error=self.close_loop_on_shutdown)

        print('Waiting {} seconds for the Arduino To Reset.'
              .format(self.arduino_wait))
        await asyncio.sleep(self.arduino_wait)
        command = [PrivateConstants.ARE_U_THERE]
        await self._send_command(command)
        # provide time for the reply
        await asyncio.sleep(.1)

        print(f'Searching for correct arduino_instance_id: {self.arduino_instance_id}')
        i_am_here = await self.serial_port.read(3)

        if not i_am_here:
            print(f'ERROR: correct arduino_instance_id not found')

        print('Correct arduino_instance_id found')

    async def _get_firmware_version(self):
        """
        This method retrieves the Arduino4Telemetrix firmware version

        :returns: Firmata firmware version
        """
        command = [PrivateConstants.GET_FIRMWARE_VERSION]
        await self._send_command(command)
        # provide time for the reply
        await asyncio.sleep(.1)
        if not self.ip_address:
            firmware_version = await self.serial_port.read(4)
        else:
            firmware_version = list(await self.sock.read(4))
        return firmware_version

    async def analog_write(self, pin, value):
        """
        Set the specified pin to the specified value.

        :param pin: arduino pin number

        :param value: pin value (maximum 16 bits)

        """
        value_msb = value >> 8
        value_lsb = value & 0xff
        command = [PrivateConstants.ANALOG_WRITE, pin, value_msb, value_lsb]
        await self._send_command(command)

    async def digital_write(self, pin, value):
        """
        Set the specified pin to the specified value.

        :param pin: arduino pin number

        :param value: pin value (1 or 0)

        """
        command = [PrivateConstants.DIGITAL_WRITE, pin, value]
        await self._send_command(command)

    async def i2c_read(self, address, register, number_of_bytes,
                       callback, i2c_port=0):
        """
        Read the specified number of bytes from the specified register for
        the i2c device.


        :param address: i2c device address

        :param register: i2c register (or None if no register selection is needed)

        :param number_of_bytes: number of bytes to be read

        :param callback: Required callback function to report i2c data as a
                   result of read command

        :param i2c_port: select the default port (0) or secondary port (1)


        callback returns a data list:
        [I2C_READ_REPORT, address, register, count of data bytes, data bytes, time-stamp]

        """
        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('i2c_read: A Callback must be specified')

        await self._i2c_read_request(address, register, number_of_bytes,
                                     callback=callback, i2c_port=i2c_port)

    async def i2c_read_restart_transmission(self, address, register,
                                            number_of_bytes,
                                            callback, i2c_port=0):
        """
        Read the specified number of bytes from the specified register for
        the i2c device. This restarts the transmission after the read. It is
        required for some i2c devices such as the MMA8452Q accelerometer.


        :param address: i2c device address

        :param register: i2c register (or None if no register
                                                    selection is needed)

        :param number_of_bytes: number of bytes to be read

        :param callback: Required callback function to report i2c data as a
                   result of read command

        :param i2c_port: select the default port (0) or secondary port (1)

        callback returns a data list:

        [I2C_READ_REPORT, address, register, count of data bytes, data bytes, time-stamp]

        """
        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('i2c_read_restart_transmission: A Callback must be specified')

        await self._i2c_read_request(address, register, number_of_bytes, stop_transmission=False,
                                     callback=callback, i2c_port=i2c_port)

    async def _i2c_read_request(self, address, register, number_of_bytes,
                                stop_transmission=True, callback=None, i2c_port=0):
        """
        This method requests the read of an i2c device. Results are retrieved
        via callback.

        :param address: i2c device address

        :param register: register number (or None if no register selection is needed)

        :param number_of_bytes: number of bytes expected to be returned

        :param stop_transmission: stop transmission after read

        :param callback: Required callback function to report i2c data as a
                   result of read command.

       :param i2c_port: select the default port (0) or secondary port (1)

        """
        if not i2c_port:
            if not self.i2c_1_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('I2C Read: set_pin_mode i2c never called for i2c port 1.')

        if i2c_port:
            if not self.i2c_2_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('I2C Read: set_pin_mode i2c never called for i2c port 2.')

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('I2C Read: A callback function must be specified.')

        if not i2c_port:
            self.i2c_callback = callback
        else:
            self.i2c_callback2 = callback

        if not register:
            register = 0

        # message contains:
        # 1. address
        # 2. register
        # 3. number of bytes
        # 4. restart_transmission - True or False
        # 5. i2c port

        command = [PrivateConstants.I2C_READ, address, register, number_of_bytes,
                   stop_transmission, i2c_port]
        await self._send_command(command)

    async def i2c_write(self, address, args, i2c_port=0):
        """
        Write data to an i2c device.

        :param address: i2c device address

        :param i2c_port: 0= port 1, 1 = port 2

        :param args: A variable number of bytes to be sent to the device
                     passed in as a list

        """
        if not i2c_port:
            if not self.i2c_1_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('I2C Write: set_pin_mode i2c never called for i2c port 1.')

        if i2c_port:
            if not self.i2c_2_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('I2C Write: set_pin_mode i2c never called for i2c port 2.')

        command = [PrivateConstants.I2C_WRITE, len(args), address, i2c_port]

        for item in args:
            command.append(item)

        await self._send_command(command)

    async def loop_back(self, start_character, callback):
        """
        This is a debugging method to send a character to the
        Arduino device, and have the device loop it back.

        :param start_character: The character to loop back. It should be
                                an integer.

        :param callback: Looped back character will appear in the callback method

        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('loop_back: A callback function must be specified.')
        command = [PrivateConstants.LOOP_COMMAND, ord(start_character)]
        self.loop_back_callback = callback
        await self._send_command(command)

    async def set_analog_scan_interval(self, interval):
        """
        Set the analog scanning interval.

        :param interval: value of 0 - 255 - milliseconds
        """

        if 0 <= interval <= 255:
            command = [PrivateConstants.SET_ANALOG_SCANNING_INTERVAL, interval]
            await self._send_command(command)
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Analog interval must be between 0 and 255')

    async def set_pin_mode_analog_input(self, pin_number, differential=0, callback=None):
        """
        Set a pin as an analog input.

        :param pin_number: arduino pin number

        :param callback: async callback function

        :param differential: difference in previous to current value before
                             report will be generated

        callback returns a data list:

        [pin_type, pin_number, pin_value, raw_time_stamp]

        The pin_type for analog input pins = 2

        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('set_pin_mode_analog_input: A callback function must be specified.')

        await self._set_pin_mode(pin_number, PrivateConstants.AT_ANALOG,
                                 differential, callback=callback)

    async def set_pin_mode_analog_output(self, pin_number):
        """

        Set a pin as a pwm (analog output) pin.

        :param pin_number:arduino pin number

        """

        await self._set_pin_mode(pin_number, PrivateConstants.AT_OUTPUT, differential=0, callback=None)

    async def set_pin_mode_digital_input(self, pin_number, callback):
        """
        Set a pin as a digital input.

        :param pin_number: arduino pin number

        :param callback: async callback function

        callback returns a data list:

        [pin_type, pin_number, pin_value, raw_time_stamp]

        The pin_type for digital input pins = 0

        """
        await self._set_pin_mode(pin_number, PrivateConstants.AT_INPUT, differential=0, callback=callback)

    async def set_pin_mode_digital_input_pullup(self, pin_number, callback):
        """
        Set a pin as a digital input with pullup enabled.

        :param pin_number: arduino pin number

        :param callback: async callback function

        callback returns a data list:

        [pin_type, pin_number, pin_value, raw_time_stamp]

        The pin_type for digital input pins with pullups enabled = 11

        """
        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('set_pin_mode_digital_input_pullup: A callback function must be specified.')

        await self._set_pin_mode(pin_number, PrivateConstants.AT_INPUT_PULLUP, differential=0, callback=callback)

    async def set_pin_mode_digital_output(self, pin_number):
        """
        Set a pin as a digital output pin.

        :param pin_number: arduino pin number
        """

        await self._set_pin_mode(pin_number, PrivateConstants.AT_OUTPUT, differential=0, callback=None)

    # noinspection PyIncorrectDocstring
    async def set_pin_mode_i2c(self, i2c_port=0):
        """
        Establish the standard Arduino i2c pins for i2c utilization.

        :param i2c_port: 0 = i2c1, 1 = i2c2

        NOTES: 1. THIS METHOD MUST BE CALLED BEFORE ANY I2C REQUEST IS MADE
               2. Callbacks are set within the individual i2c read methods of this
              API.

              See i2c_read, or i2c_read_restart_transmission.

        """
        # test for i2c port 2
        if i2c_port:
            # if not previously activated set it to activated
            # and the send a begin message for this port
            if not self.i2c_2_active:
                self.i2c_2_active = True
            else:
                return
        # port 1
        else:
            if not self.i2c_1_active:
                self.i2c_1_active = True
            else:
                return

        command = [PrivateConstants.I2C_BEGIN, i2c_port]
        await self._send_command(command)

    async def set_pin_mode_dht(self, pin, callback):
        """

        :param pin: connection pin

        :param callback: callback function

        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('set_pin_mode_dht: A Callback must be specified')

        if self.dht_count < PrivateConstants.MAX_DHTS - 1:
            self.dht_callbacks[pin] = callback
            self.dht_count += 1

            command = [PrivateConstants.DHT_NEW, pin]
            await self._send_command(command)
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(f'Maximum Number Of DHTs Exceeded - set_pin_mode_dht fails for pin {pin}')

    async def set_pin_mode_servo(self, pin_number, min_pulse=544, max_pulse=2400):
        """

        Attach a pin to a servo motor

        :param pin_number: pin

        :param min_pulse: minimum pulse width

        :param max_pulse: maximum pulse width

        """
        minv = (min_pulse).to_bytes(2, byteorder="big")
        maxv = (max_pulse).to_bytes(2, byteorder="big")

        command = [PrivateConstants.SERVO_ATTACH, pin_number,
                   minv[0], minv[1], maxv[0], maxv[1]]
        await self._send_command(command)

    async def set_pin_mode_sonar(self, trigger_pin, echo_pin,
                                 callback):
        """

        :param trigger_pin:

        :param echo_pin:

        :param callback:  callback

        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('set_pin_mode_sonar: A Callback must be specified')

        if self.sonar_count < PrivateConstants.MAX_SONARS - 1:
            self.sonar_callbacks[trigger_pin] = callback
            self.sonar_count += 1

            command = [PrivateConstants.SONAR_NEW, trigger_pin, echo_pin]
            await self._send_command(command)
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(f'Maximum Number Of Sonars Exceeded - set_pin_mode_sonar fails for pin {trigger_pin}')

    async def _set_pin_mode(self, pin_number, pin_state, differential, callback):
        """
        A private method to set the various pin modes.

        :param pin_number: arduino pin number

        :param pin_state: INPUT/OUTPUT/ANALOG/PWM/PULLUP - for SERVO use
                          servo_config()
                          For DHT   use: set_pin_mode_dht

       :param differential: for analog inputs - threshold
                             value to be achieved for report to
                             be generated

        :param callback: A reference to an async call back function to be
                         called when pin data value changes

        """
        if not callback and pin_state != PrivateConstants.AT_OUTPUT:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('_set_pin_mode: A Callback must be specified')
        else:
            if pin_state == PrivateConstants.AT_INPUT:
                self.digital_callbacks[pin_number] = callback
            elif pin_state == PrivateConstants.AT_INPUT_PULLUP:
                self.digital_callbacks[pin_number] = callback
            elif pin_state == PrivateConstants.AT_ANALOG:
                self.analog_callbacks[pin_number] = callback
            else:
                print('{} {}'.format('set_pin_mode: callback ignored for '
                                     'pin state:', pin_state))

        if pin_state == PrivateConstants.AT_INPUT:
            command = [PrivateConstants.SET_PIN_MODE, pin_number, PrivateConstants.AT_INPUT, 1]

        elif pin_state == PrivateConstants.AT_INPUT_PULLUP:
            command = [PrivateConstants.SET_PIN_MODE, pin_number, PrivateConstants.AT_INPUT_PULLUP, 1]

        elif pin_state == PrivateConstants.AT_OUTPUT:
            command = [PrivateConstants.SET_PIN_MODE, pin_number, PrivateConstants.AT_OUTPUT]

        elif pin_state == PrivateConstants.AT_ANALOG:
            command = [PrivateConstants.SET_PIN_MODE, pin_number, PrivateConstants.AT_ANALOG,
                       differential >> 8, differential & 0xff, 1]
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Unknown pin state')

        if command:
            await self._send_command(command)

        await asyncio.sleep(.05)

    async def servo_detach(self, pin_number):
        """
        Detach a servo for reuse
        :param pin_number: attached pin
        """
        command = [PrivateConstants.SERVO_DETACH, pin_number]
        await self._send_command(command)

    async def servo_write(self, pin_number, angle):
        """

        Set a servo attached to a pin to a given angle.

        :param pin_number: pin

        :param angle: angle (0-180)

        """
        command = [PrivateConstants.SERVO_WRITE, pin_number, angle]
        await self._send_command(command)

    async def shutdown(self):
        """
        This method attempts an orderly shutdown
        If any exceptions are thrown, they are ignored.

        """
        self.shutdown_flag = True
        # stop all reporting - both analog and digital
        try:
            if self.serial_port:
                command = [PrivateConstants.STOP_ALL_REPORTS]
                await self._send_command(command)

                time.sleep(.5)

                await self.serial_port.reset_input_buffer()
                await self.serial_port.close()
                if self.close_loop_on_shutdown:
                    self.loop.stop()
            elif self.sock:
                command = [PrivateConstants.STOP_ALL_REPORTS]
                await self._send_command(command)
                self.the_task.cancel()
                time.sleep(.5)
                if self.close_loop_on_shutdown:
                    self.loop.stop()
        except (RuntimeError, SerialException):
            pass

    async def disable_all_reporting(self):
        """
        Disable reporting for all digital and analog input pins
        """
        command = [PrivateConstants.MODIFY_REPORTING, PrivateConstants.REPORTING_DISABLE_ALL, 0]
        await self._send_command(command)

    async def disable_analog_reporting(self, pin):
        """
        Disables analog reporting for a single analog pin.

        :param pin: Analog pin number. For example for A0, the number is 0.

        """
        command = [PrivateConstants.MODIFY_REPORTING, PrivateConstants.REPORTING_ANALOG_DISABLE, pin]
        await self._send_command(command)

    async def disable_digital_reporting(self, pin):
        """
        Disables digital reporting for a single digital pin


        :param pin: pin number

        """
        command = [PrivateConstants.MODIFY_REPORTING, PrivateConstants.REPORTING_DIGITAL_DISABLE, pin]
        await self._send_command(command)

    async def enable_analog_reporting(self, pin):
        """
        Enables analog reporting for the specified pin.

        :param pin: Analog pin number. For example for A0, the number is 0.


        """
        command = [PrivateConstants.MODIFY_REPORTING, PrivateConstants.REPORTING_ANALOG_ENABLE, pin]
        await self._send_command(command)

    async def enable_digital_reporting(self, pin):
        """
        Enable reporting on the specified digital pin.

        :param pin: Pin number.
        """

        command = [PrivateConstants.MODIFY_REPORTING, PrivateConstants.REPORTING_DIGITAL_ENABLE, pin]
        await self._send_command(command)

    async def _arduino_report_dispatcher(self):
        """
        This is a private method.
        It continually accepts and interprets data coming from Telemetrix4Arduino,and then
        dispatches the correct handler to process the data.

        It first receives the length of the packet, and then reads in the rest of the
        packet. A packet consists of a length, report identifier and then the report data.
        Using the report identifier, the report handler is fetched from report_dispatch.

        :returns: This method never returns
        """

        while True:
            if self.shutdown_flag:
                break
            try:
                if not self.ip_address:
                    packet_length = await self.serial_port.read()
                else:

                    packet_length = ord(await self.sock.read())

            except TypeError:
                continue

            # get the rest of the packet
            if not self.ip_address:
                packet = await self.serial_port.read(packet_length)
            else:
                packet = list(await self.sock.read(packet_length))

            report = packet[0]
            # handle all other messages by looking them up in the
            # command dictionary

            await self.report_dispatch[report](packet[1:])
            await asyncio.sleep(self.sleep_tune)

    '''
    Report message handlers
    '''

    async def _report_loop_data(self, data):
        """
        Print data that was looped back

        :param data: byte of loop back data
        """
        if self.loop_back_callback:
            await self.loop_back_callback(data)

    async def _report_debug_data(self, data):
        """
        Print debug data sent from Arduino

        :param data: data[0] is a byte followed by 2
                     bytes that comprise an integer
        """
        value = (data[1] << 8) + data[2]
        print(f'DEBUG ID: {data[0]} Value: {value}')

    async def _analog_message(self, data):
        """
        This is a private message handler method.
        It is a message handler for analog messages.

        :param data: message data

        """
        pin = data[0]
        value = (data[1] << 8) + data[2]

        time_stamp = time.time()

        # append pin number, pin value, and pin type to return value and return as a list
        message = [PrivateConstants.AT_ANALOG, pin, value, time_stamp]

        await self.analog_callbacks[pin](message)

    async def _dht_report(self, data):
        """
        This is a private message handler for dht addition errors

        :param data:    data[0] = report sub type - DHT_DATA or DHT_ERROR

                        data[1] = pin number

                        data[2] = humidity high order byte or error value if DHT_ERROR

                        data[3] = humidity byte 2

                        data[4] = humidity byte 3

                        data[5] = humidity byte 4

                        data[6] = temperature high order byte for data

                        data[7] = temperature byte 2

                        data[8] = temperature byte 3

                        data[9] = temperature byte 4
        """

        if data[0]:
            # error report
            # data[0] = report sub type, data[1] = pin, data[2] = error message
            if self.dht_callbacks[data[1]]:
                message = [PrivateConstants.DHT_REPORT, data[0], data[1], data[2], time.time()]
                await self.dht_callbacks[data[1]](message)
        else:
            # got valid data
            f_humidity = bytearray(data[2:6])
            f_temperature = bytearray(data[6:])
            message = [PrivateConstants.DHT_REPORT, data[0], data[1],
                       (struct.unpack('<f', f_humidity))[0],
                       (struct.unpack('<f', f_temperature))[0],
                       time.time()]

            await self.dht_callbacks[data[1]](message)

    async def _digital_message(self, data):
        """
        This is a private message handler method.
        It is a message handler for Digital Messages.

        :param data: digital message

        """
        pin = data[0]
        value = data[1]

        time_stamp = time.time()
        if self.digital_callbacks[pin]:
            message = [PrivateConstants.DIGITAL_REPORT, pin, value, time_stamp]
            await self.digital_callbacks[pin](message)

    async def _servo_unavailable(self, report):
        """
        Message if no servos are available for use.

        :param report: pin number
        """
        if self.shutdown_on_exception:
            await self.shutdown()
        raise RuntimeError(f'Servo Attach For Pin {report[0]} Failed: No Available Servos')

    async def _i2c_read_report(self, data):
        """
        Execute callback for i2c reads.

        :param data: [I2C_READ_REPORT, i2c_port, number of bytes read, address, register, bytes read..., time-stamp]
        """

        # we receive [# data bytes, address, register, data bytes]
        # number of bytes of data returned

        # data[0] = number of bytes
        # data[1] = i2c_port
        # data[2] = number of bytes returned
        # data[3] = address
        # data[4] = register
        # data[5] ... all the data bytes

        cb_list = [PrivateConstants.I2C_READ_REPORT, data[0], data[1]] + data[2:]
        cb_list.append(time.time())

        if cb_list[1]:
            await self.i2c_callback2(cb_list)
        else:
            await self.i2c_callback(cb_list)

    async def _i2c_too_few(self, data):
        """
        I2c reports too few bytes received

        :param data: data[0] = device address
        """
        if self.shutdown_on_exception:
            await self.shutdown()
        raise RuntimeError(f'i2c too few bytes received from i2c port {data[0]} i2c address {data[1]}')

    async def _i2c_too_many(self, data):
        """
        I2c reports too few bytes received

        :param data: data[0] = device address
        """
        if self.shutdown_on_exception:
            await self.shutdown()
        raise RuntimeError(f'i2c too many bytes received from i2c port {data[0]} i2c address {data[1]}')

    async def _sonar_distance_report(self, report):
        """

        :param report: data[0] = trigger pin, data[1] and data[2] = distance

        callback report format: [PrivateConstants.SONAR_DISTANCE, trigger_pin, distance_value, time_stamp]
        """

        # get callback from pin number
        cb = self.sonar_callbacks[report[0]]

        # build report data
        cb_list = [PrivateConstants.SONAR_DISTANCE, report[0],
                   ((report[1] << 8) + report[2]), time.time()]

        await cb(cb_list)

    async def _send_command(self, command):
        """
        This is a private utility method.


        :param command:  command data in the form of a list

        :returns: number of bytes sent
        """
        # the length of the list is added at the head
        command.insert(0, len(command))
        # print(command)
        send_message = bytes(command)

        if not self.ip_address:
            await self.serial_port.write(send_message)
        else:
            await self.sock.write(send_message)
            # await asyncio.sleep(.1)
