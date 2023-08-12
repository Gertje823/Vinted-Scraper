# Vinted & Depop Scraper/Downloader

This script allows you to download data from Vinted (and Depop in the future) using the command line. With this tool, you can easily download images and other data from any public Vinted profile. You can also download images from private messages, posts with specific tags, and more.

> Note: the v2 branch is still under development.

## Installation

To use this script, you'll need Python 3 installed on your computer. You can download it from the official website: [https://www.python.org/downloads/](https://www.python.org/downloads/)

You can install the necessary dependencies by running the following command in your terminal:

`pip install -r requirements.txt` 

## Usage

Here is the usage information for the script:

`main.py [-h] [--user_id USER_ID] [--private_msg] [--tags] [--disable-file-download] [--own_user_id OWN_USER_ID] [--session_id SESSION_ID]` 

### Optional arguments:

| Optional Argument                  | Description                                                |
|------------------------------------|------------------------------------------------------------|
| -h, --help                         | Show this help message and exit.                          |
| --user_id USER_ID, -u USER_ID      | User id of the profile you want to scrape.       |
| --private_msg, -p                  | Download images from your private Vinted messages (requires -o and -s). |
| --tags, -t                         | Download Vinted posts with tags.                        |
| --items, -i                        | Download Vinted items by id from items.txt.              |
| --favourites, -f                   | Download Vinted data from your favorites (requires -o and -s).    |
| --disable-file-download, -n        | Disable file download. (only write data to DB)                                     |
| --disable-category-update, -c      | Disable category update.                                   |
| --download-location, -l <download_location> | Set custom download location.       |
| --own_user_id, -o <own_user_id> | Your own Vinted user id.   |
| --session_id, -s <session_id>    | Session id cookie for Vinted (_vinted_fr_session). |

### Examples

Here are some examples of how you can use this script:

#### Downloading data from a public Vinted profile

`python main.py -u {USER_ID}` 

#### Downloading data from a list of Vinted profiles (users.txt)

`python main.py` 


#### Downloading data from a private Vinted message thread

`python main.py -p --own_user_id {OWN_USER_ID} --session_id {SESSION_ID}` 

#### Downloading data from Vinted posts with specific tags (from tags.txt)

`python main.py -t` 

#### Disabling file download

`python main.py -n -u {USER_ID}`

## Disclaimer
*This script is designed for educational purposes only. It is intended to demonstrate web scraping techniques and should not be used for any commercial or personal gain. Please note that using this software may violate the terms of service of Vinted and Depop websites, and you assume all responsibility for any consequences that may arise from its use. The creator of this script will not be held responsible for any damages, injuries, or losses that occur while using the software. Use at your own risk.*
