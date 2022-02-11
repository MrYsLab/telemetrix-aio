#!/usr/bin/env python3

from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='telemetrix-aio',
    packages=['telemetrix_aio'],
    install_requires=['pyserial'],

    version='1.10',

    description="Remotely Control And Monitor Arduino-Core devices",
    long_description=long_description,
    long_description_content_type='text/markdown',

    author='Alan Yorinks',
    author_email='MisterYsLab@gmail.com',
    url='https://github.com/MrYsLab/telemetrix-aio',
    download_url='https://github.com/MrYsLab/telemetrix-aio',
    keywords=['telemetrix', 'Arduino', 'Protocol', 'Python'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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

