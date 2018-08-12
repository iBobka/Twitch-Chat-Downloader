#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .twitch import Messages, Channel
from .subtitles import SubtitleWriter
from .settings import argparser


def download(video):
    writer = SubtitleWriter(video)
    for comment in Messages(video):
        writer.add(comment)
    writer.close()


def download_all(channel, min=0, max=None, count=None):
    videos = Channel(channel).videos()
    to_download = list()

    for video in videos:
        if (not max or video <= max) and video >= min:
            to_download.append(video)

        if count and len(to_download) >= count:
            break

    for video in to_download:
        download(video)


def main():
    args = argparser.parse_args()

    if args.video or args.video_id:
        download(args.video or args.video_id)
    elif args.channel:
        download_all(args.channel, args.video_min,
                     args.video_max, args.video_count)


if __name__ == "__main__":
    main()
