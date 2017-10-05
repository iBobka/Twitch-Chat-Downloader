#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import datetime

import requests


settings_file = 'settings.json'
if not os.path.isfile(settings_file):
    settings_file = 'example.settings.json'

# Read settings from file
with open(settings_file, 'r') as settings_file:
    settings = json.load(settings_file)

# Check for outdated settings.json
if settings['version'].startswith("1"):
    print("Please update your settings.json (see example.settings.json for examples)")
    sys.exit(1)

# Create destination directory
if not os.path.exists(settings['directory']):
    os.makedirs(settings['directory'])


class Messages(list):
    def __init__(self, video_id):
        self.video_id = video_id
        self.base_url = "https://api.twitch.tv/v5/videos/%d/comments" % video_id

        self.client = requests.Session()
        self.client.headers["Acccept"] = "application/vnd.twitchtv.v5+json"
        self.client.headers["Client-ID"] = settings['client_id']

    def __iter__(self):
        self.cursor = None
        self.stop = False
        return self

    def _load_more(self):
        if self.cursor is None:
            url = self.base_url + "?content_offset_seconds=0"
        else:
            url = self.base_url + "?cursor=" + self.cursor

        if settings['cooldown'] > 0:
            time.sleep(settings['cooldown'])

        response = self.client.get(url).json()

        for comment in response["comments"]:
            self.append(comment)

        self.cursor = response["_next"]

        if self.cursor is None or len(self) == 0:
            self.stop = True

    def next(self):
        if len(self) == 0:
            if self.stop is True:
                raise StopIteration
            else:
                self._load_more();

        return self.pop(0)

class SubtitlesASS(object):
    def __init__(self, video_id):
        filename = settings['filename_format'].format(
            directory=settings['directory'],
            video_id=video_id,
            format='ass'
        )
        self.file = open(filename, mode='w+')

        self.file.writelines([
            '[Script Info]\n',
            'PlayResX: 1280\n',
            'PlayResY: 720\n',
            '\n',
            '[V4 Styles]\n',
            settings['ssa_style_format'],
            settings['ssa_style_default'],
            '\n\n',
            '[Events]\n',
            settings['ssa_events_format']
        ])

    def _date(self, seconds):
        result = str(datetime.timedelta(seconds=seconds))
        if '.' not in result:
            result += '.000000'
        return result

    def add(self, comment):
        time_offset = comment['content_offset_seconds']

        self.file.write(settings['ssa_events_line_format'].format(
            start=self._date(time_offset),
            end=self._date(time_offset + settings['subtitle_duration']),
            user=comment['commenter']['display_name'],
            message=comment['message']['body']
        ).encode('utf-8') + '\n')

    def close(self):
        self.file.flush()
        self.file.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: " + sys.argv[0] + " <video_id>")
        sys.exit(1)

    video_id = int(sys.argv[1])

    subtitle_drivers = set()
    for format in settings['formats']:
        if format == "ass":
            subtitle_drivers.add(SubtitlesASS(video_id))

    for comment in Messages(video_id):
        [driver.add(comment) for driver in subtitle_drivers]

    [driver.close() for driver in subtitle_drivers]
