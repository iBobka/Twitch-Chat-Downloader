# Twitch Chat Downloader

Neat python script to download chat messages from past broadcasts

## Requirements

* [Python 2.7 or 3.4+](https://www.python.org/downloads/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [python-requests](http://docs.python-requests.org/en/master/user/install/)

## Installation and usage

There are multiple ways to install this script.

```bash
# Install package with pip
pip install https://github.com/TheDrHax/Twitch-Chat-Downloader/archive/master.zip
python -m tcd <video_id>
```

```bash
# Run pip as root to install `tcd` for all users
sudo pip install https://github.com/TheDrHax/Twitch-Chat-Downloader/archive/master.zip
tcd <video_id>
```

```bash
# Start script directly from cloned repository
git clone https://github.com/TheDrHax/Twitch-Chat-Downloader.git
cd Twitch-Chat-Downloader
pip install -r requirements.txt

python -m tcd <video_id>
# or ...
python app.py <video_id>
```

## Settings

To override default options, run `python -m tcd --generate-config` and edit generated `settings.json` or just use console arguments listed below.

| Option | Type | Argument | Description |
| ------ | ---- | -------- | ----------- |
| client_id | *str* | `--client-id` | Twitch API Client-ID header. |
| cooldown | *int* | `--cooldown` | Delay (in milliseconds) between API calls. |
| display_progress | *bool* | `--[no-]progress` | Display animated progress bar in terminal. |
| formats | *str[]* | `-f/--formats` | List of formats to download. See Formats table below. |
| directory | *str* | `-t`/`--directory` | Name of directory to save all generated files. |
| filename_format | *str* | `--filename-format` | Full format of generated filenames. Possible arguments: `directory`, `video_id` and `format`. |
| subtitle_duration | *int* | `--subtitle-duration` | Duration (in seconds) of each line of subtitles. |
| group_repeating_emotes | *obj* |  | Convert `Kappa Kappa Kappa` to `Kappa x3`. |
| —.enabled | *bool* | `--[no-]group` | Enable or disable this function. |
| —.threshold | *int* | `--group-threshold` | Number of repeating emotes to trigger this function. |
| —.format | *str* | `--group-format` | Customize format of replaced emotes. |

## Formats

| Format | Description |
| ------ | ----------- |
| `ass` or `ssa` | Advanced SubStation Alpha |
| `srt` | SubRip |
| `irc` | IRC-style log |

## Notes

- Empty messages means the user has been timed out. There's no known way to get these.
- This script is using Twitch's API v5 that is [deprecated](https://dev.twitch.tv/docs/v5).
- Consider increasing the delay between API calls in `settings.json` to avoid a potential temporary block from Twitch for sending too many requests when downloading messages from very long streams.
