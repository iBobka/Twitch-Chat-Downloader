#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from .twitch import Messages
from .subtitles import SubtitleWriter


parser = ArgumentParser(description='Download VOD chats from Twitch.')
parser.add_argument('video', type=int, nargs='?',
                    help='ID of VOD (twitch.tv/videos/{video})')


def download(video_id):
    writer = SubtitleWriter(video_id)
    for comment in Messages(video_id):
        writer.add(comment)
    writer.close()


def main():
    args = parser.parse_args()

    if args.video:
        download(args.video)


if __name__ == "__main__":
    main()
