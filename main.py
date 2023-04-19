from Vinted import vinted_scraper
import argparse, os, sys

parser = argparse.ArgumentParser(description='Vinted & Depop Scraper/Downloader. Default downloads Vinted')
# Modes:
parser.add_argument('--user_id','-u',dest='user_id', action='store', help='User id of the profile you want to scrape (Vinted)', required=False)
parser.add_argument('--private_msg','-p',dest='priv_msg', action='store_true', help='Download images from private messages from Vinted (Vinted)')
parser.add_argument('--tags','-t',dest='tags', action='store_true', help='Download post with tags (Vinted)', required=False)
# Options
parser.add_argument('--disable-file-download','-n',dest='disable_file_download', action='store_true', help='Disable file download', default=False, required=False)

# Only used when --private_msg
parser.add_argument('--own_user_id','-o',dest='own_user_id', action='store', help='Your own userid (Vinted)', required=False)
parser.add_argument('--session_id','-s',dest='session_id', action='store', help='Session id cookie for Vinted (Vinted)', required=False)
args = parser.parse_args()

v = vinted_scraper()
c, conn = v.init_database()
vinted_session = v.create_session()


if args.user_id:
    v.download_user_data(vinted_session, args.user_id, disable_file_download=args.disable_file_download)
    v.download_item_data(vinted_session, args.user_id, disable_file_download=args.disable_file_download)

elif args.priv_msg:
    if not args.own_user_id or not args.session_id:
        print("Please provide a valid sessionid and your own userid")
        exit(1)
    else:
        vinted_session = v.create_session(_vinted_fr_session=args.session_id)
        v.download_priv_msg(vinted_session, args.own_user_id, args.session_id, download_location='downloads/Messages/')

elif args.tags:
    # Check if tags.txt exists
    if os.path.exists('tags.txt'):
        with open('tags.txt', 'r', encoding='utf-8') as list_of_tags:
            tags = list_of_tags.readlines()
        v.download_vinted_tags(vinted_session, tags, disable_file_download=args.disable_file_download)
    else:
        print("tags.txt not found.\nPlease create tags.txt")
        sys.exit(1)


else:
    # Check if users.txt exists
    if os.path.exists('users.txt'):
        with open('users.txt', 'r', encoding='utf-8') as list_of_users:
            userids = list_of_users.readlines()
        for user_id in userids:
            v.download_user_data(vinted_session, user_id.strip(), disable_file_download=args.disable_file_download)
            v.download_item_data(vinted_session, user_id.strip(), disable_file_download=args.disable_file_download)
    else:
        print("users.txt not found.\nPlease create users.txt or user -u <userid>")
        sys.exit(1)
