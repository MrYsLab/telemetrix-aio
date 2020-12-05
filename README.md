# The Telemetrix Project

Telemetry is a system for collecting data on a remote device and then automatically transmitting the 
collected data back to local receiving equipment for processing.

The Telemetrix Project is a telemetry system explicitly designed for Arduino Core-based MCUs, using 
Python on the local client and an 
Arduino Core sketch, called 
[Telemetrix4Arduino](https://github.com/MrYsLab/Telemetrix4Arduino) on the Microcontroller Unit (MCU).

In addition, WiFi is supported for the ESP8266 when used in conjunction with 
[Telemetrix4Esp8266](https://github.com/MrYsLab/Telemetrix4Esp8266).

Telemetrix-AIO is a Python asyncio client for the Telemetrix Project. A non-asyncio version may be found
 [here](https://github.com/MrYsLab/telemetrix).

It is designed to be user extensible so that you may add support for sensors and actuators
of your choosing.

A [User's Guide](https://mryslab.github.io/telemetrix/) explaining installation and use is available online.

A Python API for may be found [here.](https://htmlpreview.github.com/?https://github.com/MrYsLab/telemetrix-aio/blob/master/html/telemetrix_aio/index.html)

