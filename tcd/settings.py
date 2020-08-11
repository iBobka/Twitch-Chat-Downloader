#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import inspect
from argparse import ArgumentParser


SELF = inspect.getfile(inspect.currentframe())
ROOT = os.path.dirname(os.path.abspath(SELF))

settings_file_default = 'settings.json'
if not os.path.isfile(settings_file_default):
    settings_file_default = ROOT + '/example.settings.json'


def _pre_init_parser(help=False):
    parser = ArgumentParser(
        description='Download VOD chats from Twitch.', add_help=help)
    parser.add_argument(
        '-s', '--settings', metavar='settings.json',
        default=settings_file_default,
        help='Override path to settings.json.')
    return parser


args, unknown_args = _pre_init_parser().parse_known_args()
settings_file = args.settings

# Read settings from file
with open(settings_file, 'r') as settings_file:
    settings = json.load(settings_file)

# Check for outdated settings.json
if settings['version'].startswith("1"):
    print("Please update your settings.json " +
          "(see example.settings.json for examples)")
    sys.exit(1)

if 'group_repeating_emotes' not in settings:
    settings['group_repeating_emotes'] = {'enabled': False,
                                          'threshold': 3,
                                          'collocations': 1,
                                          'format': '{emote} x{count}'}
if 'collocations' not in settings['group_repeating_emotes']:
    settings['group_repeating_emotes']['collocations'] = 1
if 'collocations_threshold' not in settings['group_repeating_emotes']:
    settings['group_repeating_emotes']['collocations_threshold'] = \
        settings['group_repeating_emotes']['collocations']
if 'video_types' not in settings:
    settings['video_types'] = 'archive'
if 'dynamic_duration' not in settings:
    settings['dynamic_duration'] = {'enabled': False, 'max': 5,
                                    'max_length': 100}
if 'max_width' not in settings:
    settings['max_width'] = -1

#
# Post-init settings overrides
#


def _post_init_parser(help=False):
    parser = _pre_init_parser(help)

    settings_group = parser.add_argument_group(
        'Settings', 'These options will override values from settings.json.')
    settings_group.add_argument(
        '--client-id', metavar='ID', type=str, default=settings['client_id'],
        help='Twitch API Client-ID headers.')
    settings_group.add_argument(
        '--cooldown', metavar='msec', type=int, default=settings['cooldown'],
        help='Delay (in milliseconds) between API calls.')

    progress = settings_group.add_mutually_exclusive_group(required=False)
    progress.add_argument(
        '--progress', action='store_true', dest='progress',
        default=settings['display_progress'],
        help='Display progress bar while downloading chat.')
    progress.add_argument(
        '--no-progress', action='store_false', dest='progress',
        help='Opposite of --progress.')

    settings_group.add_argument(
        '-f', '--formats', metavar='FORMAT', type=lambda s: s.split(','),
        default=settings['formats'],
        help='Comma-separated list of subtitle formats.')
    settings_group.add_argument(
        '-t', '--directory', metavar='PATH', type=str,
        default=settings['directory'],
        help='Target directory to save all generated subtitles.')
    settings_group.add_argument(
        '--filename-format', metavar='FORMAT', type=str,
        default=settings['filename_format'],
        help=('Python str.format for generating output file names. Available '
              'variables: {directory}, {video_id} and {format}.'))
    settings_group.add_argument(
        '--max-width', metavar='chars', type=int,
        default=settings['max_width'],
        help=('Add line breaks to fit messages into specified width. '
              'Note: Implemented only for SSA/ASS subtitles.'))
    settings_group.add_argument(
        '--subtitle-duration', metavar='sec', type=int,
        default=settings['subtitle_duration'],
        help=('Time (in seconds) to display each comment on the screen. '
              'Will be ignored by some subtitle formats (irc).'))
    settings_group.add_argument(
        '--dynamic-duration', action='store_true', dest='dynamic',
        default=settings['dynamic_duration']['enabled'],
        help='Increase subtitle duration based on message length.')
    settings_group.add_argument(
        '--no-dynamic-duration', action='store_false', dest='dynamic',
        help='Opposite of --dynamic-duration.')
    settings_group.add_argument(
        '--dynamic-duration-max', metavar='sec', type=int,
        default=settings['dynamic_duration']['max'],
        help='Maximum duration of subtitle message.')
    settings_group.add_argument(
        '--dynamic-duration-max-length', metavar='chars', type=int,
        default=settings['dynamic_duration']['max_length'],
        help='Maximum length of subtitle message.')

    group = settings_group.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--group', action='store_true', dest='group',
        default=settings['group_repeating_emotes']['enabled'],
        help=('Group repeating emotes in all messages. '
              'Example: Kappa Kappa Kappa → Kappa x3.'))
    group.add_argument(
        '--no-group', action='store_false', dest='group',
        help='Opposite of --group.')

    settings_group.add_argument(
        '--group-threshold', metavar='repeats', type=int,
        default=settings['group_repeating_emotes']['threshold'],
        help='Minimal number of repeating emotes to group.')
    settings_group.add_argument(
        '--group-collocations', metavar='words', type=int,
        default=settings['group_repeating_emotes']['collocations'],
        help=('Maximum number of words in repeating collocations '
              '(default: 1, more is slower).'))
    settings_group.add_argument(
        '--group-collocations-threshold', metavar='repeats', type=int,
        default=settings['group_repeating_emotes']['collocations_threshold'],
        help=('Same logic as in --group-threshold, but applies only to '
              'repeating collocations.'))
    settings_group.add_argument(
        '--group-format', metavar='FORMAT', type=str,
        default=settings['group_repeating_emotes']['format'],
        help=('Python str.format for grouped emotes. Available '
              'variables: {emote} and {count}.'))

    channel_group = parser.add_argument_group(
        'Channel Mode Settings',
        'These options will only work with -c/--channel.')
    channel_group.add_argument(
        '--video-min', metavar='ID', type=int, default=0,
        help='ID of the earliest VOD to download.')
    channel_group.add_argument(
        '--video-max', metavar='ID', type=int, default=None,
        help='ID of the latest VOD to download.')
    channel_group.add_argument(
        '--video-count', metavar='N', type=int, default=None,
        help='Download N the most recent VODs.')
    channel_group.add_argument(
        '--video-types', metavar='type1,type2', type=str, default='archive',
        help=('Comma-separated list of VOD type to download. '
              'Available types: archive, upload, highlight, past_premiere.'))

    return parser


args, unknown_args = _post_init_parser(help=False).parse_known_args()
settings['client_id'] = args.client_id
settings['cooldown'] = args.cooldown
settings['display_progress'] = args.progress
settings['formats'] = args.formats
settings['directory'] = args.directory
settings['filename_format'] = args.filename_format
settings['max_width'] = args.max_width
settings['subtitle_duration'] = args.subtitle_duration
settings['dynamic_duration']['enabled'] = args.dynamic
settings['dynamic_duration']['max'] = args.dynamic_duration_max
settings['dynamic_duration']['max_length'] = args.dynamic_duration_max_length
settings['group_repeating_emotes']['enabled'] = args.group
settings['group_repeating_emotes']['threshold'] = args.group_threshold
settings['group_repeating_emotes']['collocations'] = args.group_collocations
settings['group_repeating_emotes']['collocations_threshold'] = args.group_collocations_threshold
settings['group_repeating_emotes']['format'] = args.group_format
settings['video_types'] = args.video_types


#
# Post-init arguments
#

argparser = _post_init_parser(help=True)

source_group = argparser.add_argument_group('Chat Sources')
exclusive_group = source_group.add_mutually_exclusive_group(required=True)
exclusive_group.add_argument(
    '-c', '--channel', metavar='NAME', type=str,
    help=('Name of channel to download ALL chats from. '
          'Example: twitch.tv/{channel}.'))
exclusive_group.add_argument(
    '-v', '--video', metavar='ID', type=int,
    help='ID of VOD. Example: twitch.tv/videos/{video}.')
exclusive_group.add_argument(
    'video_id', type=int, metavar='VIDEO_ID', nargs='?',
    help='Alias for -v/--video (for backward compatibility).')
exclusive_group.add_argument(
    '--generate-config', action='store_true',
    help=('Generate settings.json in current directory using defaults and '
          'command-line arguments.'))
