#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='twitch-chat-downloader',
      version='2.1.1',

      author='Dmitry Karikh',
      author_email='the.dr.hax@gmail.com',
      license='MIT',
      url='https://github.com/TheDrHax/Twitch-Chat-Downloader',

      install_requires=['requests', 'progressbar2'],

      packages=find_packages(),
      package_data={'tcd': ['example.settings.json']},
      include_package_data=True,

      entry_points='''
        [console_scripts]
        tcd=tcd:main
      ''',
      )
