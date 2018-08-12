#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from .twitch import Messages, Channel
from .subtitles import SubtitleWriter


parser = ArgumentParser(description='Download VOD chats from Twitch.')

sg = parser.add_mutually_exclusive_group(required=True)
sg.add_argument('-c', '--channel', type=str, nargs='?',
                help=('Name of channel to download ALL chats from. '
                      'Example: twitch.tv/{channel}.'))
sg.add_argument('-v', '--video', type=int, nargs='?',
                help='ID of VOD. Example: twitch.tv/videos/{video}.')
sg.add_argument('video_id', type=int, nargs='?',
                help='Alias for -v/--video (for backward compatibility).')

cg = parser.add_argument_group('Channel Mode Settings',
                               ('These options will only work with '
                                '-c/--channel.'))
cg.add_argument('--video-min', type=int, nargs='?', default=0,
                help='ID of the earliest VOD to download.')
cg.add_argument('--video-max', type=int, nargs='?', default=None,
                help='ID of the latest VOD to download.')
cg.add_argument('--video-count', type=int, nargs='?', default=None,
                help='Download N the most recent VODs.')


def download(video):
    writer = SubtitleWriter(video)
    for comment in Messages(video):
        writer.add(comment)
    writer.close()


def download_all(channel, args):
    videos = Channel(channel).videos()
    to_download = list()

    for video in videos:
        if not args.video_max or video <= args.video_max:
            if video >= args.video_min:
                to_download.append(video)

        if args.video_count and len(to_download) >= args.video_count:
            break

    for video in to_download:
        download(video)


def main():
    args = parser.parse_args()

    if args.video or args.video_id:
        download(args.video or args.video_id)
    elif args.channel:
        download_all(args.channel, args)


if __name__ == "__main__":
    main()
