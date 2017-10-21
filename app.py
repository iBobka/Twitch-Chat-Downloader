#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
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
    print("Please update your settings.json " +
          "(see example.settings.json for examples)")
    sys.exit(1)

# Create destination directory
if not os.path.exists(settings['directory']):
    os.makedirs(settings['directory'])


class Messages(list):
    def __init__(self, video_id):
        self.video_id = video_id
        api_url = "https://api.twitch.tv/v5/videos/{id}/comments"
        self.base_url = api_url.format(id=video_id)

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
            time.sleep(settings['cooldown'] / 1000)

        response = self.client.get(url).json()

        for comment in response["comments"]:
            self.append(comment)

        if '_next' in response:
            self.cursor = response['_next']
        else:
            self.stop = True

    def __next__(self):
        if len(self) == 0:
            if self.stop is True:
                raise StopIteration
            else:
                self._load_more()

        return self.pop(0)

    next = __next__  # Python 2.x compatibility


class Subtitle(object):
    @staticmethod
    def encode(input):
        if sys.version_info > (3, 0):
            return input
        else:
            return input.encode('utf-8')

    @staticmethod
    def new_file(video_id, format):
        filename = settings['filename_format'].format(
            directory=settings['directory'],
            video_id=video_id,
            format=format
        )
        return open(filename, mode='w+')

    def __init__(self, video_id, format):
        self.file = self.new_file(video_id, format)

    @staticmethod
    def _offset(seconds, decimal_separator='.'):
        offset = str(datetime.timedelta(seconds=seconds))
        if '.' not in offset:
            offset += '.000000'

        if decimal_separator != '.':
            offset.replace('.', decimal_separator)

        return offset

    def close(self):
        self.file.flush()
        self.file.close()


class SubtitlesASS(Subtitle):
    def __init__(self, video_id, format="ass"):
        super(SubtitlesASS, self).__init__(video_id, format)

        self.line = self.encode(settings['ssa_events_line_format']) + '\n'

        self.file.writelines([
            '[Script Info]\n',
            'PlayResX: 1280\n',
            'PlayResY: 720\n',
            '\n',
            '[V4 Styles]\n',
            settings['ssa_style_format'],
            '\n',
            settings['ssa_style_default'],
            '\n\n',
            '[Events]\n',
            settings['ssa_events_format'],
            '\n'
        ])

    def add(self, comment):
        offset = comment['content_offset_seconds']

        self.file.write(self.line.format(
            start=self._offset(offset)[:-4],
            end=self._offset(offset + settings['subtitle_duration'])[:-4],
            user=self.encode(comment['commenter']['display_name']),
            message=self.encode(comment['message']['body'])
        ))


class SubtitlesSRT(Subtitle):
    def __init__(self, video_id):
        super(SubtitlesSRT, self).__init__(video_id, "srt")
        self.count = 0

    def add(self, comment):
        time = comment['content_offset_seconds']

        self.file.write(str(self.count) + '\n')
        self.file.write("{start} --> {end}\n".format(
            start=self._offset(time, ',')[:-3],
            end=self._offset(time + settings['subtitle_duration'], ',')[:-3]
        ))
        self.file.write("{user}: {message}\n\n".format(
            user=self.encode(comment['commenter']['display_name']),
            message=self.encode(comment['message']['body'])
        ))

        self.count += 1


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: " + sys.argv[0] + " <video_id>")
        sys.exit(1)

    video_id = int(sys.argv[1])

    subtitle_drivers = set()
    for format in settings['formats']:
        if format in ("ass", "ssa"):
            subtitle_drivers.add(SubtitlesASS(video_id, format))

        if format == "srt":
            subtitle_drivers.add(SubtitlesSRT(video_id))

    for comment in Messages(video_id):
        [driver.add(comment) for driver in subtitle_drivers]

    [driver.close() for driver in subtitle_drivers]
