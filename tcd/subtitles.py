#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from datetime import timedelta

from .settings import settings


class Subtitle(object):
    @staticmethod
    def encode(input):
        if sys.version_info > (3, 0):
            return input
        else:
            return input.encode('utf-8')

    @staticmethod
    def new_file(video_id, format):
        if not os.path.exists(settings['directory']):
            os.makedirs(settings['directory'])

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
        offset = str(timedelta(seconds=seconds))
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
    def _rgb_to_bgr(color):
        return color[4:6] + color[2:4] + color[0:2]

    @staticmethod
    def _color(text, color):
        return '{\\c&H' + color + '&}' + text + '{\\c&HFFFFFF&}'

    def add(self, comment):
        offset = comment.offset
        color = self._rgb_to_bgr(comment.color)

        self.file.write(self.line.format(
            start=self._offset(offset)[:-4],
            end=self._offset(offset + settings['subtitle_duration'])[:-4],
            user=self.encode(self._color(comment.user, color)),
            message=self.encode(comment.message)
        ))


class SubtitlesSRT(Subtitle):
    def __init__(self, video_id):
        super(SubtitlesSRT, self).__init__(video_id, "srt")
        self.count = 0

    def add(self, comment):
        time = comment.offset

        self.file.write(str(self.count) + '\n')
        self.file.write("{start} --> {end}\n".format(
            start=self._offset(time, ',')[:-3],
            end=self._offset(time + settings['subtitle_duration'], ',')[:-3]
        ))
        self.file.write("{user}: {message}\n\n".format(
            user=self.encode(comment.user),
            message=self.encode(comment.message)
        ))

        self.count += 1


class SubtitlesIRC(Subtitle):
    def __init__(self, video_id):
        super(SubtitlesIRC, self).__init__(video_id, "irc")

    def add(self, comment):
        self.file.write("[{start}] <{user}> {message}\n".format(
            start=self._offset(comment.offset, ',')[:-3],
            user=self.encode(comment.user),
            message=self.encode(comment.message)
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
