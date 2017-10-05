# Twitch Chat Downloader

Neat python script to download chat messages from past broadcasts

## Requirements

* [Python 2.7 or 3.4+](https://www.python.org/downloads/)
* [python-requests](http://docs.python-requests.org/en/master/user/install/)

### Install requirements automatically

```
sudo apt-get install python-pip
sudo pip install -r requirements.txt
```

## Installation

```bash
git clone https://github.com/TheDrHax/Twitch-Chat-Downloader.git
cd Twitch-Chat-Downloader
pip install -r requirements.txt
```

## Usage

```bash
python app.py <video_id>
```

## Settings

To override default options, copy `example.config.json` into `example.json` and change it.

| Option | Value | Description |
| ------ | ------ | ----------- |
| client_id | *String* | Twitch API client_id. |
| cooldown | *Integer* | Delay (in milliseconds) between API calls. |
| formats | *String[]* | List of formats to download. See Formats table below. |
| directory | *String* | Name of directory to save all generated files. |
| filename_format | *String* | Full format of generated filenames. Possible arguments: `directory`, `video_id` and `format`. |
| subtitle_duration | *Integer* | Duration (in seconds) of each line of subtitles. |

## Formats

| Format | Description |
| ------- | ----------- |
| `ass` | Advanced SubStation Alpha |

## Notes

- Empty messages means the user has been timed out. There's no known way to get these.
- This script is using Twitch's API v5 that will be [removed](https://dev.twitch.tv/docs/v5) at the end of 2018.
- Consider increasing the delay between API calls in `settings.json` to avoid a potential temporary block from Twitch for sending too many requests when downloading messages from very long streams.
