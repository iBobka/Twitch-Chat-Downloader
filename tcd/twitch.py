#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
from progressbar import ProgressBar
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry

from .settings import settings


client = Session()
client.headers["Acccept"] = "application/vnd.twitchtv.v5+json"
client.headers["Client-ID"] = settings['client_id']

# Configure retries for all requests
retries = Retry(connect=5, read=2, redirect=5)
http_adapter = HTTPAdapter(max_retries=retries)
client.mount("http://", http_adapter)
client.mount("https://", http_adapter)


class Message(object):
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

    def __init__(self, comment):
        self.user = comment['commenter']['display_name']
        self.message = self.group(comment['message']['body'])
        self.offset = comment['content_offset_seconds']

        if 'user_color' in comment['message']:
            self.color = comment['message']['user_color'][1:]
        else:
            self.color = 'FFFFFF'


class Messages(object):
    def __init__(self, video_id):
        self.video_id = video_id
        api_url = "https://api.twitch.tv/v5/videos/{id}/comments"
        self.base_url = api_url.format(id=video_id)

        # Get video object from API
        if settings.get('display_progress') in [None, True]:
            api_video_url = 'https://api.twitch.tv/v5/videos/{}'
            video = client.get(api_video_url.format(video_id)).json()
            self.duration = video['length']
            self.progressbar = ProgressBar(max_value=self.duration)
        else:
            self.progressbar = None

    def __iter__(self):
        url = self.base_url + "?content_offset_seconds=0"

        while True:
            response = client.get(url).json()

            for comment in response["comments"]:
                try:
                    yield Message(comment)
                except Exception:
                    continue

            if self.progressbar and self.duration:
                offset = response['comments'][-1]['content_offset_seconds']
                self.progressbar.update(min(offset, self.duration))

            if '_next' not in response:
                if self.progressbar:
                    self.progressbar.finish()
                break

            url = self.base_url + "?cursor=" + response['_next']

            if settings['cooldown'] > 0:
                sleep(settings['cooldown'] / 1000)


class Channel(object):
    def __init__(self, channel):
        self.name = channel
        api_url = "https://api.twitch.tv/kraken/channels/{}"
        self.base_url = api_url.format(channel)

    def _videos(self, types, offset=0, limit=100):
        url = self.base_url + '/videos?limit={}'.format(limit)
        url += '&broadcast_type=' + types
        url += '&offset={}'.format(offset)

        r = client.get(url).json()

        for video in r['videos']:
            yield video
        
        if r['_total'] > limit + offset:
            for video in self._videos(types, offset + limit, limit):
                yield video

    def videos(self, offset=0):
        """Get VOD IDs"""
        for video in self._videos(settings['video_types'], offset):
            yield int(video['_id'][1:])

    def live_vod(self):
        """Get ID of ongoing stream"""
        video = self._videos('archive', limit=5).__next__()

        if video.get('status') == 'recording':
            return video['_id'][1:]
        else:
            return None