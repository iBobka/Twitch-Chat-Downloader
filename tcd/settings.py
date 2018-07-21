#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import inspect


SELF = inspect.getfile(inspect.currentframe())
ROOT = os.path.dirname(os.path.abspath(SELF))

settings_file = 'settings.json'
if not os.path.isfile(settings_file):
    settings_file = ROOT + '/example.settings.json'

# Read settings from file
with open(settings_file, 'r') as settings_file:
    settings = json.load(settings_file)

# Check for outdated settings.json
if settings['version'].startswith("1"):
    print("Please update your settings.json " +
          "(see example.settings.json for examples)")
    sys.exit(1)
