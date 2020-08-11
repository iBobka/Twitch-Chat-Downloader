#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import os
import textwrap

from datetime import timedelta, datetime as dtt

from .settings import settings


class Subtitle(object):
    @staticmethod
    def new_file(video_id, format):
        if not os.path.exists(settings['directory']):
            os.makedirs(settings['directory'])

        filename = settings['filename_format'].format(
            directory=settings['directory'],
            video_id=video_id,
            format=format
        )

        return io.open(filename, mode='w+', encoding='UTF8')

    def __init__(self, video_id, format):
        self.file = self.new_file(video_id, format)

    @staticmethod
    def _duration(msg):
        T_MIN = settings['subtitle_duration']
        T_MAX = settings['dynamic_duration']['max']
        MSG_MAX = settings['dynamic_duration']['max_length']

        if settings['dynamic_duration']['enabled']:
            part = (MSG_MAX - min(len(msg), MSG_MAX)) / MSG_MAX
            return T_MAX - (T_MAX - T_MIN) * part
        else:
            return T_MIN

    @staticmethod
    def ftime(seconds: float) -> str:
        t = dtt.strptime("00:00", "%H:%M") + timedelta(seconds=seconds)
        ts = dtt.strftime(t, '%H:%M:%S.%f')
        return ts[1:] if ts.startswith('00') else ts

    @staticmethod
    def wrap(username, text):
        max_width = settings['max_width']
        full_text = username + ': ' + text

        if len(full_text) <= max_width or max_width <= 0:
            return text

        text = textwrap.wrap(full_text, max_width, drop_whitespace=False)
        text = '\n'.join(text).replace('\n ', ' \n')
        text = text[len(username)+2:]

        return text

    def close(self):
        self.file.flush()
        self.file.close()


class SubtitlesASS(Subtitle):
    def __init__(self, video_id, format="ass"):
        super(SubtitlesASS, self).__init__(video_id, format)

        self.line = settings['ssa_events_line_format'] + '\n'

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
    def _rgb_to_bgr(color):
        return color[4:6] + color[2:4] + color[0:2]

    @staticmethod
    def _color(text, color):
        return '{\\c&H' + color + '&}' + text + '{\\c&HFFFFFF&}'

    @staticmethod
    def wrap(username, message):
        return Subtitle.wrap(username, message).replace('\n', '\\N')

    @staticmethod
    def ftime(seconds: float) -> str:
        return Subtitle.ftime(seconds)[:-4]

    def add(self, comment):
        offset = round(comment.offset, 2)
        color = self._rgb_to_bgr(comment.color)

        self.file.write(self.line.format(
            start=self.ftime(offset),
            end=self.ftime(offset + self._duration(comment.message)),
            user=self._color(comment.user, color),
            message=self.wrap(comment.user, comment.message)
        ))


class SubtitlesSRT(Subtitle):
    def __init__(self, video_id):
        super(SubtitlesSRT, self).__init__(video_id, "srt")
        self.count = 0

    @staticmethod
    def ftime(seconds):
        return Subtitle.ftime(seconds)[:-3].replace('.', ',')

    def add(self, comment):
        time = comment.offset

        self.file.write(str(self.count) + '\n')
        self.file.write("{start} --> {end}\n".format(
            start=self.ftime(time),
            end=self.ftime(time + self._duration(comment.message))
        ))
        self.file.write("{user}: {message}\n\n".format(
            user=comment.user,
            message=comment.message
        ))

        self.count += 1


class SubtitlesIRC(Subtitle):
    def __init__(self, video_id):
        super(SubtitlesIRC, self).__init__(video_id, "irc")

    @staticmethod
    def ftime(seconds):
        return Subtitle.ftime(seconds)[:-3].replace('.', ',')

    def add(self, comment):
        self.file.write("[{start}] <{user}> {message}\n".format(
            start=self.ftime(comment.offset),
            user=comment.user,
            message=comment.message
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
