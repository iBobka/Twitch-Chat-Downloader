#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from .twitch import Messages
from .subtitles import SubtitleWriter


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
