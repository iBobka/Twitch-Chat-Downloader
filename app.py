#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import datetime

import requests


class Messages(list):
    def __init__(self, video_id):
        self.video_id = video_id
        self.base_url = "https://api.twitch.tv/v5/videos/%d/comments" % video_id

        self.client = requests.Session()
        self.client.headers["Acccept"] = "application/vnd.twitchtv.v5+json"
        self.client.headers["Client-ID"] = "jzkbprff40iqj646a697cyrvl0zt2m6"

    def __iter__(self):
        self.cursor = None
        self.stop = False
        return self

    def _load_more(self):
        if self.cursor is None:
            url = self.base_url + "?content_offset_seconds=0"
        else:
            url = self.base_url + "?cursor=" + self.cursor

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
    def __init__(self, file):
        self.file = open(file, mode='w+')

        self.file.writelines([
            '[Script Info]\n',
            '\n',
            'PlayResX: 1280\n',
            'PlayResY: 720\n',
            '\n',
            '[V4 Styles]\n',
            'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding\n',
            'Style: Default,Arial,20,65535,65535,65535,-2147483640,-1,0,1,3,0,1,5,0,5,0,0\n',
            '\n',
            '[Events]\n',
            'Format: Marked, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
        ])

        self.line_format = 'Dialogue: Marked=0, {start}, {end}, Default, {user}, , 0000, 0000, 0000, , {user}: {message}\n'

    def _date(self, seconds):
        result = str(datetime.timedelta(seconds=seconds))
        if '.' not in result:
            result += '.000000'
        return result

    def add(self, comment):
        time_offset = comment['content_offset_seconds']

        self.file.write(self.line_format.format(
            start=self._date(time_offset),
            end=self._date(time_offset + 2),
            user=comment['commenter']['display_name'].encode('utf-8'),
            message=comment['message']['body'].encode('utf-8')
        ))

    def close(self):
        self.file.flush()
        self.file.close()

if __name__ == "__main__":
    s = SubtitlesASS('test.ass')

    for comment in Messages(179882105):
        s.add(comment)

    s.close()
