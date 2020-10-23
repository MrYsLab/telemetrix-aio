#!/usr/bin/env python3

from setuptools import setup


setup(
    name='telemetrix-aio',
    packages=['telemetrix_aio'],
    install_requires=['pyserial'],

    version='0.1.0',
    description="telemetrix-aio client and server",

    author='Alan Yorinks',
    author_email='MisterYsLab@gmail.com',
    url='https://github.com/MrYsLab/telemetrix-aio',
    download_url='https://github.com/MrYsLab/telemetrix-aio',
    keywords=['telemetrix', 'Arduino', 'Protocol', 'Python'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)

