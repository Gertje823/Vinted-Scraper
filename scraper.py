import requests
import os.path
import os
import sqlite3
import argparse
import time
import cloudscraper
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ArgParse
parser = argparse.ArgumentParser(description='Vinted & Depop Scraper/Downloader. Default downloads Vinted')

# Define command line arguments
parser.add_argument('--depop','-d',dest='Depop', action='store_true', help='Download Depop data.')
parser.add_argument('--private_msg','-p',dest='priv_msg', action='store_true', help='Download images from private messages from Vinted')
parser.add_argument('--user_id','-u',dest='user_id', action='store', help='Your own userid', required=False)
parser.add_argument('--session_id','-s',dest='session_id', action='store', help='Session id cookie for Vinted', required=False)
parser.add_argument('--disable-file-download','-n',dest='disable_file_download', action='store_true', help='Disable file download (Currently only working for depop)', required=False)
parser.add_argument('--sold_items','-g',dest='sold_items', action='store_true', help='Also download sold items (depop)', required=False)
parser.add_argument('--start_from','-b',dest='start_from', action='store', help='Begin from a specific item (depop)', required=False)
parser.add_argument('--maximum_images','-i',dest='maximum_images', action='store', help='Set a maximum amount of image to download. 1 image by default (vinted)', required=False)

args = parser.parse_args()

# Check if disable file download is used correctly
if args.disable_file_download and not args.Depop:
    logging.error("-n only works with Depop. Use -n -d to disable filedownloads from Depop")
    exit(1)

# Create downloads folders if they do not exist
if not os.path.exists('downloads'):
    os.makedirs('downloads')

directory_path = "downloads/Avatars/"
try:
    os.mkdir(directory_path)
    logging.info(f"Directory created at {directory_path}")
except OSError as e:
    if os.path.exists(directory_path):
        logging.warning(f"Folder already exists at {directory_path}")
    else:
        logging.error(f"Creation of the directory failed at {directory_path}")
        logging.debug(f"Error: {e}")

# Connect to SQLite database
sqlite_file = 'data.sqlite'
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

# Create tables if they do not exist
c.execute('''CREATE TABLE IF NOT EXISTS Data
             (ID, User_id, Sold, Url, Favourite, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Images, Description, Title, Platform)''')

c.execute('''CREATE TABLE IF NOT EXISTS Depop_Data
             (ID, User_id, Url, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Description, Title, Platform, Address, discountedPriceAmount, dateUpdated)''')

c.execute('''CREATE TABLE IF NOT EXISTS Users
             (Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, Verification_google, Verification_phone, Platform)''')

c.execute('''CREATE TABLE IF NOT EXISTS Depop_Users
             (Username, User_id UNIQUE, bio, first_name, followers, following, initials, items_sold, last_name, last_seen, Avatar, reviews_rating, reviews_total, verified, website)''')

c.execute('''CREATE TABLE IF NOT EXISTS Vinted_Messages
             (thread_id, from_user_id, to_user_id, msg_id, body, photos)''')

conn.commit()

# Function to update columns of Data with new version of the script
def update_col():
    logging.info("Trying to update columns of Data Table with new version of the script : add Url and Favourite field")
    try:
        c.execute('''ALTER TABLE Data ADD Url;''')
        c.execute('''ALTER TABLE Data ADD Favourite;''')
        conn.commit()
        logging.info("Columns updated")
    except Exception as e:
        logging.error(f"Can't update columns: {e}")

# Function to extract CSRF token from HTML
def extract_csrf_token(text):
    match = re.search(r'"CSRF_TOKEN":"([^"]+)"', text)
    if match:
        return match.group(1)
    else:
        return None

# Function to create a Vinted session
def vinted_session():
    s = cloudscraper.create_scraper()
    s.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'DNT': '1',
        'Connection': 'keep-alive',
        'TE': 'Trailers',
    }
    req = s.get("https://www.vinted.nl/")
    csrfToken = extract_csrf_token(req.text)
    s.headers['X-CSRF-Token'] = csrfToken
    return s

# Function to download private messages from Vinted
def download_priv_msg(session_id, user_id):
    s = cloudscraper.create_scraper()
    s.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'DNT': '1',
        'Connection': 'keep-alive',
        'TE': 'Trailers',
        'Cookie': f"_vinted_fr_session={session_id};"
    }
    logging.info(f"Session ID: {session_id}")
    data = s.get(f"https://www.vinted.nl/api/v2/users/{user_id}/msg_threads")
    if data.status_code == 403:
        # Access denied
        logging.error(f"Error: Access Denied\nCan't get content from 'https://www.vinted.nl/api/v2/users/{user_id}/msg_threads'")
        exit(1)
    data = data.json()
    try:
        os.mkdir(f"downloads/Messages/")
    except OSError:
        if os.path.isdir(f"downloads/Messages/"):
            logging.warning("Directory already exists")
        else:
            logging.error("Creation of the directory failed")
    if not "msg_threads" in data:
        logging.error("Error: Can't find any messages.\nPlease make sure you entered the sessionid correctly")
        exit(1)
    for msg_threads in data['msg_threads']:
        id = msg_threads['id']
        msg_data = s.get(f"https://www.vinted.nl/api/v2/users/{user_id}/msg_threads/{id}").json()

        thread_id = msg_data['msg_thread']['id']
        for message in msg_data['msg_thread']['messages']:
            try:
                photo_data = message['entity']['photos']
            except:
                continue
            if len(photo_data) > 0:
                try:
                    os.mkdir(f"downloads/Messages/{message['entity']['user_id']}")
                except OSError as e:
                    if os.path.isdir(f"downloads/Messages/{message['entity']['user_id']}"):
                        logging.warning(f"Directory already exists: downloads/Messages/{message['entity']['user_id']}")
                    else:
                        logging.error(f"Creation of the directory failed: {e}")

                from_user_id = message['entity']['user_id']
                msg_id = message['entity']['id']
                body = message['entity']['body']
                photo_list = []
                for photo in message['entity']['photos']:
                    req = requests.get(photo['full_size_url'])

                    filepath = f"downloads/Messages/{from_user_id}/{photo['id']}.jpeg"
                    photo_list.append(filepath)
                    if not os.path.isfile(filepath):
                        logging.info(f"Downloading photo ID: {photo['id']}")
                        with open(filepath, 'wb') as f:
                            f.write(req.content)
                        logging.info(f"Image saved to {filepath}")
                    else:
                        logging.info('File already exists, skipped.')
                if int(from_user_id) == int(user_id):
                    to_user_id = msg_data['msg_thread']['opposite_user']['id']
                else:
                    to_user_id = user_id
                # Save to DB

                params = (thread_id, from_user_id, to_user_id, msg_id, body, str(photo_list))
                c.execute(
                    "INSERT INTO Vinted_Messages(thread_id, from_user_id, to_user_id, msg_id, body, photos)VALUES (?,?,?,?,?,?)",
                    params)
                conn.commit()

# Function to get all items from a user on Vinted
def get_all_items(s, USER_ID, total_pages, items):
    for page in range(int(total_pages)):
        page += 1
        url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page={page}&per_page=200000'
        r = s.get(url).json()
        logging.info(f"Fetching page {page + 1}/{r['pagination']['total_pages']}")
        items.extend(r['items'])

# Function to download data from Vinted for a list of user IDs
def download_vinted_data(userids, s):
    """
    Download data from Vinted for a list of user IDs.

    Args:
        userids (list): List of user IDs to download data for.
        s (requests.Session): Session object to make requests.

    Returns:
        None
    """
    Platform = "Vinted"
    for USER_ID in userids:
        USER_ID = USER_ID.strip()
        
        # Get user profile data
        url = f"https://www.vinted.nl/api/v2/users/{USER_ID}"
        r = s.get(url)
        
        if r.status_code == 200:
            jsonresponse = r.json()
            data = jsonresponse['user']
            #get data
            username = data['login']
            try:
                gender = data['gender']
            except:
                gender = None
            given_item_count = data['given_item_count']
            taken_item_count = data['taken_item_count']
            followers_count = data['followers_count']
            following_count = data['following_count']
            positive_feedback_count = data['positive_feedback_count']
            negative_feedback_count = data['negative_feedback_count']
            feedback_reputation = data['feedback_reputation']
            try:
                created_at = data['created_at']
            except KeyError:
                created_at = ""
            last_loged_on_ts = data['last_loged_on_ts']
            city_id = data['city_id']
            city = data['city']
            country_title = data['country_title']
            verification_email = data.get('verification', {}).get('email', {}).get('valid', None)
            verification_facebook = data.get('verification', {}).get('facebook', {}).get('valid', None)
            verification_google = data.get('verification', {}).get('google', {}).get('valid', None)
            verification_phone = data.get('verification', {}).get('phone', {}).get('valid', None)

            # Handle user avatar
            if data['photo']:
                photo = data['photo']['full_size_url']
                photo_id = data['photo']['id']
                
                try:
                    os.mkdir("downloads/Avatars/")
                    logging.info("Directory created at downloads/Avatars/")
                except OSError as e:
                    if os.path.exists("downloads/Avatars/"):
                        logging.warning("Folder already exists at downloads/Avatars/")
                    else:
                        logging.error("Creation of the directory failed")
                        logging.debug(f"Error: {e}")
                
                req = requests.get(photo)
                filepath = f'downloads/Avatars/{photo_id}.jpeg'
                
                if not os.path.isfile(filepath):
                    with open(filepath, 'wb') as f:
                        f.write(req.content)
                    logging.info(f"Avatar saved to {filepath}")
                else:
                    logging.info('File already exists, skipped.')
                
                avatar_path = filepath
            else:
                avatar_path = ""

            # Save user data to database
            params = (
                username, USER_ID, gender, given_item_count, taken_item_count, followers_count, following_count,
                positive_feedback_count, negative_feedback_count, feedback_reputation, avatar_path, created_at,
                last_loged_on_ts, city_id, city, country_title, verification_email, verification_google,
                verification_facebook, verification_phone
            )
            
            c.execute(
                "INSERT INTO Users(Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, "
                "Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, "
                "Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, "
                "Verification_google, Verification_phone) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                params
            )
            conn.commit()

            # Fetch user items
            USER_ID = USER_ID.strip('\n')
            url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page=1&per_page=200000'
            logging.info('ID=' + str(USER_ID))

            r = s.get(url)
            items = []
            logging.info(f"Fetching page 1/{r.json()['pagination']['total_pages']}")
            if r.status_code == 404:
                print(f"User '{USER_ID}' not found")
                continue
            print(f"Fetching page 1/{r.json()['pagination']['total_pages']}")
            items.extend(r.json()['items'])
            
            if r.json()['pagination']['total_pages'] > 1:
                logging.info(f"User has more than {len(items)} items. fetching next page....")
                get_all_items(s, USER_ID, r.json()['pagination']['total_pages'], items)
            
            products = items
            logging.info(f"Total items: {len(products)}")

            if r.status_code == 200:
                if products:
                    # Download all products
                    path = f"downloads/{USER_ID}/"
                    
                    try:
                        os.mkdir(path)
                    except OSError as e:
                        if os.path.exists(path):
                            logging.warning(f"Folder already exists at {path}")
                        else:
                            logging.error(f"Creation of the directory {path} failed: {e}")
                    else:
                        logging.info(f"Successfully created the directory {path}")

                    for product in products:
                        img = product['photos']
                        ID = product['id']
                        User_id = product['user_id']
                        Url = product['url']
                        Favourite = product['favourite_count']
                        description = product['description']
                        Gender = product['user'].get('gender', None)
                        Category = product['catalog_id']
                        size = product['size']
                        State = product['status']
                        Brand = product['brand']
                        Colors = product['color1']
                        Price = product['price']
                        Price = f"{Price['amount']} {Price['currency_code']}"
                        Images = product['photos']
                        title = product['title']
                        path = f"downloads/{User_id}/"

                        if Images:
                            # If parameter -i download a maximum of n images
                            if args.maximum_images:
                                count_img = int(args.maximum_images)
                                if count_img > len(img):
                                    count_img = len(img)
                            else:
                                count_img = len(img)

                            for image in Images[:count_img]:
                                full_size_url = image['full_size_url']
                                img_name = image['high_resolution']['id']
                                filepath = f'downloads/{USER_ID}/{img_name}.jpeg'
                                
                                if not os.path.isfile(filepath):
                                    req = requests.get(full_size_url)
                                    params = (
                                        ID, User_id, Url, Favourite, Gender, Category, size, State, Brand, Colors, Price,
                                        filepath, description, title, Platform
                                    )
                                    
                                    try:
                                        c.execute(
                                            "INSERT INTO Data(ID, User_id, Url, Favourite, Gender, Category, size, State, "
                                            "Brand, Colors, Price, Images, description, title, Platform) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                            params
                                        )
                                    except Exception as e:
                                        logging.error(f"Can't execute query : {e}")
                                        update_col()
                                    finally:
                                        c.execute(
                                            "INSERT INTO Data(ID, User_id, Url, Favourite, Gender, Category, size, State, "
                                            "Brand, Colors, Price, Images, description, title, Platform) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                            params
                                        )
                                        conn.commit()
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(req.content)
                                    logging.info(f"Image saved to {filepath}")
                                else:
                                    logging.info('File already exists, skipped.')
                else:
                    logging.info('User has no products')
            elif r.status_code == 429:
                logging.info(f"Ratelimit waiting {r.headers['Retry-After']} seconds...")
                limit = round(int(r.headers['Retry-After']) / 2)
                
                for i in range(limit, 0, -1):
                    logging.info(f"{i}", end="\r", flush=True)
                    time.sleep(1)
                continue
        else:
            logging.info(f"User {USER_ID} does not exist")
    
    conn.close()

# Function to get all items from a user on Depop
def get_all_depop_items(data, baseurl, slugs, args, begin, s):
    # Start from slug args.start_from (-b)
    if args.start_from:
        for i in data['products']:
            # Prevent duplicates
            if not i['slug'] in slugs:
                if args.start_from == i['slug'] or begin == True:
                    begin = True
                    slugs.append(i['slug'])
    else:
        # start from 0
        for i in data['products']:
            # Prevent duplicates
            if not i['slug'] in slugs:
                slugs.append(i['slug'])
    while True:

        url = baseurl + f"&offset_id={data['meta']['last_offset_id']}"
        logging.info(url)
        try:
            data = s.get(url).json()
            # print(data)
        except:
            logging.error(s.get(url).text)
            exit()
            break
        # Start from slug args.start_from (-b)
        if args.start_from:
            for i in data['products']:
                # Prevent duplicates
                if not i['slug'] in slugs:
                    if args.start_from == i['slug'] or begin == True:
                        begin = True
                        slugs.append(i['slug'])
            if data['meta']['end'] == True:
                break
        else:
            # start from 0
            for i in data['products']:
                # Prevent duplicates
                if not i['slug'] in slugs:
                    slugs.append(i['slug'])
            if data['meta']['end'] == True:
                break
    return slugs

# Function to get all items from a user on Depop using mobile API
def get_all_depop_items_moblile_api(data, baseurl, slugs, args, begin, s):
    # Start from slug args.start_from (-b)
    if args.start_from:
        for i in data['objects']:
            # Prevent duplicates
            if not i['slug'] in slugs:
                if args.start_from == i['slug'] or begin == True:
                    begin = True
                    slugs.append(i['slug'])
    else:
        # start from 0
        for i in data['objects']:
            # Prevent duplicates
            if not i['id'] in slugs:
                slugs.append(i['id'])
    while True:
        if data['meta']['end']:
            return slugs
        url = baseurl + f"&offset_id={data['meta']['last_offset_id']}"
        logging.info(url)
        try:
            data = s.get(url).json()
            # print(data)
        except:
            logging.error(s.get(url).text)
            exit()
            break
        # Start from slug args.start_from (-b)
        if args.start_from:
            for i in data['objects']:
                # Prevent duplicates
                if not i['id'] in slugs:
                    if args.start_from == i['id'] or begin == True:
                        begin = True
                        slugs.append(i['id'])
            if data['meta']['end'] == True:
                break
        else:
            # start from 0
            for i in data['objects']:
                # Prevent duplicates
                if not i['id'] in slugs:
                    slugs.append(i['id'])
            if data['meta']['end'] == True:
                break
    return slugs

def download_depop_data(userids):
    Platform = "Depop"
    headers = {"referer":"https://www.depop.com/"}
    s = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'desktop': True
    })
    s.headers.update(headers)
    s.get("https://depop.com")
    for userid in userids:
        userid = userid.strip()
        # convert username to user id
        search_data = s.get(f"https://api.depop.com/api/v1/search/users/top/?q={userid}").json()
        real_userid = None
        for item in search_data.get('objects', []):
            if item['username'] == userid:
                real_userid = item['id']
                print(f"User {userid} has userID {real_userid}")
                break
        
        if not real_userid:
            print(f"Could not find user ID for {userid}")
            continue

        # Get user data
        url = f"https://api.depop.com/api/v1/users/{real_userid}/"
        print(url)
        data = s.get(url).json()

        # Process user data
        user_data = {
            'id': str(data['id']),
            'username': str(data['username']),
            'first_name': str(data.get('first_name', '')).encode("UTF-8"),
            'last_name': str(data.get('last_name', '')).encode("UTF-8"),
            'bio': str(data.get('bio', '')).encode("UTF-8"),
            'followers': str(data.get('followers', '')),
            'following': str(data.get('following', '')),
            'items_sold': str(data.get('items_sold', '')),
            'last_seen': str(data.get('last_seen', '')),
            'reviews_rating': str(data.get('reviews_rating', '')),
            'reviews_total': str(data.get('reviews_total', '')),
            'verified': str(data.get('verified', '')),
            'website': str(data.get('website', ''))
        }

        # Download avatar
        filepath = None
        if data.get('picture_data'):
            photo = data['picture_data']['formats']['U0']['url']
            try:
                os.makedirs("downloads/Avatars/", exist_ok=True)
            except OSError as e:
                print(f"Error creating Avatars directory: {e}")

            filepath = f'downloads/Avatars/{user_data["id"]}.jpeg'
            if not os.path.isfile(filepath):
                req = s.get(photo)
                with open(filepath, 'wb') as f:
                    f.write(req.content)
                print(f"Avatar saved to {filepath}")
            else:
                print('Avatar file already exists, skipped.')

        # Save user data to database
        params = tuple(user_data.values()) + (filepath,)
        c.execute(
            "INSERT OR REPLACE INTO Depop_Users(User_id, Username, first_name, last_name, bio, followers, following, items_sold, last_seen, reviews_rating, reviews_total, verified, website, Avatar) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            params)
        conn.commit()

        # Get all products
        product_ids = []
        baseurl = f"https://api.depop.com/api/v1/users/{real_userid}/products/?limit=200"
        
        while True:
            data = s.get(baseurl).json()
            new_ids = [item['id'] for item in data.get('objects', [])]
            product_ids.extend(new_ids)
            
            if data.get('meta', {}).get('end', True):
                break
            
            baseurl = f"https://api.depop.com/api/v1/users/{real_userid}/products/?limit=200&offset_id={data['meta']['last_offset_id']}"

        print(f"Got {len(product_ids)} products. Start Downloading...")

        # Create user directory
        path = f"downloads/{userid}/"
        os.makedirs(path, exist_ok=True)

        # Process each product
        for product_id in product_ids:
            print(f"Processing Item {product_id}")
            url = f"https://api.depop.com/api/v1/products/{product_id}/"
            
            try:
                product_data = s.get(url)
                if product_data.status_code == 200:
                    product_data = product_data.json()
                elif product_data.status_code == 429:
                    print(f"Rate limit reached. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                elif product_data.status_code == 404:
                    print(f"Product {product_id} not found")
                    continue
            except ValueError:
                print(f"Error decoding JSON data for product {product_id}. Skipping...")
                continue

            # Extract product information
            product_info = {
                'id': product_data['id'],
                'user_id': user_data['id'],
                'sold': product_data['status'],
                'gender': product_data.get('gender'),
                'category': product_data.get('categoryId'),
                'subcategory': product_data.get('productType'),
                'size': ','.join(size['name'] for size in product_data.get('sizes', [])),
                'state': product_data.get('condition'),
                'brand': product_data.get('brand'),
                'colors': ','.join(product_data.get('colour', [])),
                'price': f"{product_data['price_amount']} {product_data['price_currency']}",
                'description': product_data['description'],
                'title': product_data['slug'].replace("-", " "),
                'platform': Platform,
                'address': product_data.get('address'),
                'discounted_price': product_data.get('price', {}).get('discountedPriceAmount'),
                'date_updated': product_data['pub_date']
            }

            # Download images and videos
            media_files = []
            for img in product_data.get('pictures_data', []):
                full_size_url = img['formats']['P0']['url']
                img_name = img['id']
                filepath = f'{path}{img_name}.jpg'
                media_files.append(filepath)

                if not args.disable_file_download and not os.path.isfile(filepath):
                    req = s.get(full_size_url)
                    with open(filepath, 'wb') as f:
                        f.write(req.content)
                    print(f"Image saved to {filepath}")

            for video in product_data.get('videos', []):
                for source in video.get('outputs', []):
                    if source['format'] == 'MP4':
                        video_url = source['url']
                        file_name = video_url.split('/')[-1]
                        filepath = f'{path}{file_name}'
                        media_files.append(filepath)

                        if not args.disable_file_download and not os.path.isfile(filepath):
                            req = s.get(video_url)
                            with open(filepath, 'wb') as f:
                                f.write(req.content)
                            print(f"Video saved to {filepath}")

            # Save product data to database
            params = tuple(product_info.values()) + (','.join(media_files),)
            c.execute(
                "INSERT OR REPLACE INTO Depop_Data(ID, User_id, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Description, Title, Platform, Address, discountedPriceAmount, dateUpdated, Image) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                params)
            conn.commit()

    print("Finished processing all users and their products.")



#Import users from txt file
with open('users.txt', 'r', encoding='utf-8') as list_of_users:
            userids = list_of_users.readlines()

if args.Depop:
    download_depop_data(userids)
elif args.priv_msg:
    if args.user_id and args.session_id:
        user_id = args.user_id
        session_id = args.session_id
        download_priv_msg(session_id, user_id)
    else:
        print("Please use option -u and -s")
        exit()
else:
    if args.maximum_images:
        try:
            args.maximum_images = int(args.maximum_images)
            if args.maximum_images <= 0:
                logging.error("Maximum images must be greater than 0")
                exit()
        except ValueError:
            logging.error("Invalid value for maximum_images: This argument needs to be a number")
            exit()
            
    session = vinted_session()
    download_vinted_data(userids, session)