#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import datetime
import inspect

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry
from progressbar import ProgressBar

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

# Create destination directory
if not os.path.exists(settings['directory']):
    os.makedirs(settings['directory'])


class Messages(object):
    def __init__(self, video_id):
        self.video_id = video_id
        api_url = "https://api.twitch.tv/v5/videos/{id}/comments"
        self.base_url = api_url.format(id=video_id)

        self.client = requests.Session()
        self.client.headers["Acccept"] = "application/vnd.twitchtv.v5+json"
        self.client.headers["Client-ID"] = settings['client_id']

        # Configure retries for all requests
        retries = Retry(connect=5, read=2, redirect=5)
        http_adapter = HTTPAdapter(max_retries=retries)
        self.client.mount("http://", http_adapter)
        self.client.mount("https://", http_adapter)

        # Get video object from API
        if settings.get('display_progress') in [None, True]:
            api_video_url = 'https://api.twitch.tv/kraken/videos/{}'
            video = self.client.get(api_video_url.format(video_id)).json()
            self.duration = video['length']
            self.progressbar = ProgressBar(max_value=self.duration)
        else:
            self.progressbar = None

    def __iter__(self):
        url = self.base_url + "?content_offset_seconds=0"

        while True:
            response = self.client.get(url).json()

            for comment in response["comments"]:
                yield comment

            if self.progressbar and self.duration:
                offset = response['comments'][-1]['content_offset_seconds']
                self.progressbar.update(min(offset, self.duration))

            if '_next' not in response:
                if self.progressbar:
                    self.progressbar.finish()
                break

            url = self.base_url + "?cursor=" + response['_next']

            if settings['cooldown'] > 0:
                time.sleep(settings['cooldown'] / 1000)


class Subtitle(object):
    @staticmethod
    def group(message):
        prefs = settings.get('group_repeating_emotes')
        if prefs is None or not prefs['enabled']:
            return message

        words = []
        for word in message.split(' '):
            if len(words) > 0 and words[-1][0] == word:
                words[-1][1] += 1
            else:
                words.append([word, 1])

        result = []
        for word, count in words:
            if count >= prefs['threshold']:
                result.append(prefs['format'].format(emote=word, count=count))
            else:
                result += [word] * count

        return ' '.join(result)

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
        if sys.version_info > (3, 0):
            return open(filename, mode='w+', encoding='UTF8')
        else:
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

    @staticmethod
    def _get_color_bgr(message):
        color = 'FFFFFF'
        if message.get('user_color'):
            color = message['user_color'].replace('#', '')
        return color[4:6] + color[2:4] + color[0:2]  # RGB -> BGR

    @staticmethod
    def _color(text, color):
        return '{\\c&H' + color + '&}' + text + '{\\c&HFFFFFF&}'

    def add(self, comment):
        offset = comment['content_offset_seconds']
        color = self._get_color_bgr(comment['message'])

        username = self._color(comment['commenter']['display_name'], color)

        self.file.write(self.line.format(
            start=self._offset(offset)[:-4],
            end=self._offset(offset + settings['subtitle_duration'])[:-4],
            user=self.encode(username),
            message=self.encode(self.group(comment['message']['body']))
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
            message=self.encode(self.group(comment['message']['body']))
        ))

        self.count += 1


class SubtitlesIRC(Subtitle):
    def __init__(self, video_id):
        super(SubtitlesIRC, self).__init__(video_id, "irc")

    def add(self, comment):
        time = comment['content_offset_seconds']

        self.file.write("[{start}] <{user}> {message}\n".format(
            start=self._offset(time, ',')[:-3],
            user=self.encode(comment['commenter']['name']),
            message=self.encode(self.group(comment['message']['body']))
        ))


class SubtitleWriter:
    def __init__(self, video_id):
        self.drivers = set()

        for format in settings['formats']:
            if format in ("ass", "ssa"):
                self.drivers.add(SubtitlesASS(video_id, format))

            if format == "srt":
                self.drivers.add(SubtitlesSRT(video_id))

            if format == "irc":
                self.drivers.add(SubtitlesIRC(video_id))

    def add(self, comment):
        [driver.add(comment) for driver in self.drivers]

    def close(self):
        [driver.close() for driver in self.drivers]


def download(video_id):
    writer = SubtitleWriter(video_id)
    for comment in Messages(video_id):
        writer.add(comment)
    writer.close()


def main():
    if len(sys.argv) == 1:
        print("Usage: " + sys.argv[0] + " <video_id>")
        sys.exit(1)

    video_id = int(sys.argv[1])
    download(video_id)


if __name__ == "__main__":
    main()
