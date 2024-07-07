import requests
import json
import os.path
import os
import sqlite3
import argparse
import time
import cloudscraper
import re
# ArgParse
parser = argparse.ArgumentParser(description='Vinted & Depop Scraper/Downloader. Default downloads Vinted')
parser.add_argument('--depop','-d',dest='Depop', action='store_true', help='Download Depop data.')
parser.add_argument('--private_msg','-p',dest='priv_msg', action='store_true', help='Download images from private messages from Vinted')
parser.add_argument('--user_id','-u',dest='user_id', action='store', help='Your own userid', required=False)
parser.add_argument('--session_id','-s',dest='session_id', action='store', help='Session id cookie for Vinted', required=False)
parser.add_argument('--disable-file-download','-n',dest='disable_file_download', action='store_true', help='Disable file download (Currently only working for depop)', required=False)
parser.add_argument('--sold_items','-g',dest='sold_items', action='store_true', help='Also download sold items (depop)', required=False)
parser.add_argument('--start_from','-b',dest='start_from', action='store', help='Begin from a specific item (depop)', required=False)
args = parser.parse_args()

if args.disable_file_download and not args.Depop:
    print("-n only works with Depop. Use -n -d to disable filedownloads from Depop")
    exit(1)

# create downlods folders
if not os.path.exists('downloads'):
    os.makedirs('downloads')

try:
    os.mkdir(f"downloads/Avatars/")
except OSError:
    print("Creation of the directory failed or the folder already exists ")


#database
sqlite_file = 'data.sqlite'
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()
# Create Data table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS Data
             (ID, User_id, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Images, Description, Title, Platform)''')
c.execute('''CREATE TABLE IF NOT EXISTS Depop_Data
             (ID, User_id, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Description, Title, Platform, Address, discountedPriceAmount, dateUpdated)''')
# Create Users table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS Users
             (Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, Verification_google, Verification_phone, Platform)''')
c.execute('''CREATE TABLE IF NOT EXISTS Depop_Users
             (Username, User_id UNIQUE, bio, first_name, followers, following, initials, items_sold, last_name, last_seen, Avatar, reviews_rating, reviews_total, verified, website)''')
c.execute('''CREATE TABLE IF NOT EXISTS Vinted_Messages
             (thread_id, from_user_id, to_user_id, msg_id, body, photos)''')
conn.commit()

def extract_csrf_token(text):
    match = re.search(r'"CSRF_TOKEN":"([^"]+)"', text)
    if match:
        return match.group(1)
    else:
        return None

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
    print(session_id)
    data = s.get(f"https://www.vinted.nl/api/v2/users/{user_id}/msg_threads")
    if data.status_code ==403:
        # Access denied
        print(f"Error: Access Denied\nCan't get content from 'https://www.vinted.nl/api/v2/users/{user_id}/msg_threads'")
        exit(1)
    data = data.json()
    try:
        os.mkdir(f"downloads/Messages/")
    except OSError:
        print("Creation of the directory failed or the folder already exists ")
    if not "msg_threads" in data:
        print("Error: Can't find any messages.\nPlease make sure you entered the sessionid correctly")
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
                except OSError:
                    print ("Creation of the directory failed or the folder already exists ")

                from_user_id = message['entity']['user_id']
                msg_id = message['entity']['id']
                body = message['entity']['body']
                photo_list = []
                for photo in message['entity']['photos']:
                    req = requests.get(photo['full_size_url'])

                    filepath = f"downloads/Messages/{from_user_id}/{photo['id']}.jpeg"
                    photo_list.append(filepath)
                    if not os.path.isfile(filepath):
                        print(photo['id'])
                        with open(filepath, 'wb') as f:
                            f.write(req.content)
                        print(f"Image saved to {filepath}")
                    else:
                        print('File already exists, skipped.')
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

def get_all_items(s, USER_ID, total_pages, items):
    for page in range(int(total_pages)):
        page +=1
        url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page={page}&per_page=200000'
        r = s.get(url).json()
        print(f"Fetching page {page+1}/{r['pagination']['total_pages']}")
        items.extend(r['items'])

def download_vinted_data(userids, s):
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
            verification_email = data['verification']['email']['valid']
            verification_facebook = data['verification']['facebook']['valid']
            verification_google = data['verification']['google']['valid']
            verification_phone = data['verification']['phone']['valid']
            if data['photo']:
                photo = data['photo']['full_size_url']
                photo_id = data['photo']['id']
                try:
                    os.mkdir(f"downloads/Avatars/")
                except OSError:
                    print ("Creation of the directory failed or the folder already exists ")
                req = requests.get(photo)
                filepath = f'downloads/Avatars/{photo_id}.jpeg'
                if not os.path.isfile(filepath):
                    print(photo_id)
                    with open(filepath, 'wb') as f:
                        f.write(req.content)
                    print(f"Avatar saved to {filepath}")
                else:
                    print('File already exists, skipped.')
                params = (
                    username, USER_ID, gender, given_item_count, taken_item_count, followers_count, following_count,
                    positive_feedback_count, negative_feedback_count, feedback_reputation, filepath, created_at,
                    last_loged_on_ts, city_id, city, country_title, verification_email, verification_google,
                    verification_facebook, verification_phone)
                c.execute(
                    "INSERT INTO Users(Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, Verification_google, Verification_phone)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    params)
                conn.commit()

            else:
                # If no avatar put empty string in DB
                Avatar = ""
                params = (
                    username, USER_ID, gender, given_item_count, taken_item_count, followers_count, following_count,
                    positive_feedback_count, negative_feedback_count, feedback_reputation, Avatar, created_at,
                    last_loged_on_ts, city_id, city, country_title, verification_email, verification_google, verification_facebook,
                    verification_phone)
                c.execute(
                    "INSERT INTO Users(Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, Verification_google, Verification_phone)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    params)
                conn.commit()

            USER_ID = USER_ID.strip('\n')
            url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page=1&per_page=200000'
            print('ID=' + str(USER_ID))

            r = s.get(url)
            items = []
            print(f"Fetching page 1/{r.json()['pagination']['total_pages']}")
            items.extend(r.json()['items'])
            # products = jsonresponse['items']
            if r.json()['pagination']['total_pages'] > 1:
                print(f"User has more than {len(items)} items. fetching next page....")
                get_all_items(s, USER_ID, r.json()['pagination']['total_pages'], items)
            products = items
            print(f"Total items: {len(products)}")
            if r.status_code == 200:
                # print(jsonresponse)

                if products:
                    # Download all products
                    path= "downloads/" + str(USER_ID) +'/'
                    try:
                        os.mkdir(path)
                    except OSError:
                        print ("Creation of the directory %s failed or the folder already exists " % path)
                    else:
                        print ("Successfully created the directory %s " % path)
                    for product in products:
                            img = product['photos']
                            ID = product['id']
                            User_id = product['user_id']
                            description = product['description']
                            try:
                                Gender = product['user']['gender']
                            except KeyError:
                                Gender = None
                            Category = product['catalog_id']
                            size = product['size']
                            State = product['status']
                            Brand = product['brand']
                            Colors = product['color1']
                            Price = product['price']
                            Price = f"{Price['amount']} {Price['currency_code']}"
                            Images = product['photos']
                            title = product['title']
                            path= "downloads/" + str(User_id) +'/'

                            #print(img)
                            if Images:
                                for images in img:
                                    full_size_url = images['full_size_url']
                                    img_name = images['high_resolution']['id']
                                    #print(img_name)
                                    filepath = 'downloads/'+ str(USER_ID) +'/' + img_name +'.jpeg'
                                    if not os.path.isfile(filepath):
                                        #print(full_size_url)
                                        req = requests.get(full_size_url)
                                        params = (ID, User_id, Gender, Category, size, State, Brand, Colors, Price, filepath, description, title, Platform)
                                        c.execute("INSERT INTO Data(ID, User_id, Gender, Category, size, State, Brand, Colors, Price, Images, description, title, Platform)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", params)
                                        conn.commit()
                                        with open(filepath, 'wb') as f:
                                            f.write(req.content)
                                        print(f"Image saved to {filepath}")
                                    else:
                                        print('File already exists, skipped.')
                if not products:
                    print('User has no products')
            elif r.status_code == 429:
                print(f"Ratelimit waiting {r.headers['Retry-After']} seconds...")
                limit = round(int(r.headers['Retry-After']) / 2)
                for i in range(limit, 0, -1):
                    print(f"{i}", end="\r", flush=True)
                    time.sleep(1)
                continue

        elif r.status_code == 429:
            print(f"Ratelimit waiting {r.headers['Retry-After']} seconds...")
            limit = round(int(r.headers['Retry-After']) / 2)
            for i in range(limit, 0, -1):
                print(f"{i}", end="\r", flush=True)
                time.sleep(1)
            continue
        else:
            print(f"User {USER_ID} does not exists")
    conn.close()

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
        print(url)
        try:
            data = s.get(url).json()
            # print(data)
        except:
            print(s.get(url).text)
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
        print(url)
        try:
            data = s.get(url).json()
            # print(data)
        except:
            print(s.get(url).text)
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
        for item in search_data['objects']:
            if item['username'] == userid:
                print(f"User {userid} has userID {item['id']}")
                break
        real_userid = item['id']
        slugs = []
        # Get userid from username
        url = f"https://webapi.depop.com/api/v2/shop/{userid}/"
        url = f"https://api.depop.com/api/v1/users/{real_userid}/"
        print(url)
        #print(s.get(url).content)
        data = s.get(url).json()

        id = str(data['id'])

        # This data is only available for authenticated users via mobile API :(
        try:
            last_seen = str(data['last_seen'])
        except KeyError:
            last_seen = None
        try:
            bio = str(data['bio']).encode("UTF-8")
        except KeyError:
            bio = None
        try:
            followers = str(data['followers'])
        except KeyError:
            followers = None
        try:
            following = str(data['following'])
        except KeyError:
            following = None
        try:
            initials = str(data['initials']).encode("UTF-8")
        except UnicodeEncodeError:
            initials = None
        except KeyError:
            initials = None
        try:
            items_sold = str(data['items_sold'])
        except KeyError:
            items_sold = None
        last_name = str(data['last_name']).encode("UTF-8")
        first_name = str(data['first_name']).encode("UTF-8")
        try:
            reviews_rating = str(data['reviews_rating'])
        except KeyError:
            reviews_rating = None
        try:
            reviews_total = str(data['reviews_total'])
        except KeyError:
            reviews_total = None
        username = str(data['username'])
        try:
            verified = str(data['verified'])
        except KeyError:
            verified = None
        try:
            website = str(data['website'])
        except KeyError:
            website = None
        filepath = None
        try:

            if data['picture_data']:
                photo = data['picture_data']['formats']['U0']['url']
                print(photo)
                try:
                    os.mkdir(f"downloads/Avatars/")
                except OSError:
                    print("Creation of the directory failed or the folder already exists ")
                req = s.get(photo)
                filepath = f'downloads/Avatars/{id}.jpeg'
                if not os.path.isfile(filepath):
                    with open(filepath, 'wb') as f:
                        f.write(req.content)
                    print(f"Avatar saved to {filepath}")
            else:
                print('File already exists, skipped.')
        except KeyError:
            print("No avatar found")


        params = (username, id, bio, first_name, followers, following, initials, items_sold, last_name, last_seen, filepath, reviews_rating, reviews_total, verified,website)
        c.execute(
            "INSERT OR IGNORE INTO Depop_Users(Username, User_id, bio, first_name, followers, following, initials, items_sold, last_name, last_seen, Avatar, reviews_rating, reviews_total, verified, website) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            params)
        conn.commit()


        #baseurl = f"https://webapi.depop.com/api/v1/shop/{id}/products/?limit=200"
        baseurl = f"https://api.depop.com/api/v1/users/{real_userid}/products/?limit=200"
        data = s.get(baseurl).json()

        print("Fetching all produts...")
        begin = False
        product_ids = []
        product_ids = get_all_depop_items_moblile_api(data, baseurl, product_ids, args, begin, s)

        if args.sold_items:
            baseurl = f"https://webapi.depop.com/api/v1/shop/{id}/filteredProducts/sold?limit=200"
            baseurl = f"https://api.depop.com/api/v1/users/{real_userid}/filteredProducts/sold?limit=200"
            #baseurl = f"https://webapi.depop.com/api/v1/shop/{id}/filteredProducts/sold?limit=200"
            baseurl = f"https://api.depop.com/api/v1/users/{real_userid}/products/?limit=200"
            data = s.get(baseurl).json()
            get_all_depop_items(data, baseurl, product_ids, args, begin, s)
            get_all_depop_items_moblile_api(data, baseurl, product_ids, args, begin, s)

        print("Got all products. Start Downloading...")
        print(len(product_ids))
        path = "downloads/" + str(userid) + '/'
        try:
            os.mkdir(path)
        except OSError:
            print("Creation of the directory %s failed or the folder already exists " % path)
        for product_id_ in product_ids:
            print("Item", product_id_)
            #url = f"https://webapi.depop.com/api/v2/product/{slug}"
            url = f"https://api.depop.com/api/v1/products/{product_id_}/"
            try:
                product_data = s.get(url)
                #print(product_data)
                if product_data.status_code == 200:
                    product_data = product_data.json()
                elif product_data.status_code == 429:
                    print(f"Ratelimit waiting 60 seconds...")
                    limit = 60
                    for i in range(limit, 0, -1):
                        print(f"{i}", end="\r", flush=True)
                        time.sleep(1)
                    continue
                elif product_data.status_code == 404:
                    print("Product not found")
                    continue
            except ValueError:
                print("Error decoding JSON data. Skipping...")
                continue
            #print(json.dumps(product_data, indent=4))
            product_id = product_data['id']
            try:
                Gender = product_data['gender']
            except KeyError:
                Gender = None
            try:
                Gender = product_data['gender']
            except KeyError:
                Gender = None
            try:
                Category = product_data['group']
            except KeyError:
                Category = product_data['categoryId']
            try:
                subcategory = product_data['productType']
            except KeyError:
                subcategory = None
            address = product_data['address']
            dateUpdated = product_data['pub_date']
            try:
                State = product_data['condition']
            except KeyError:
                State = None

            Price = product_data['price_amount'] + product_data['price_currency']
            description = product_data['description']
            Sold = product_data['status']
            slug= product_data['slug']
            title = slug.replace("-"," ")

            Colors = []
            # Get discountedPriceAmount if available
            try:
               discountedPriceAmount = product_data['price']['discountedPriceAmount']
            except KeyError:
                discountedPriceAmount = None
                pass
            # Get colors if available
            try:
                for color in product_data['colour']:
                    Colors.append(color)
            except KeyError:
                pass

            # Get brand if available
            try:
                Brand = product_data['brand']
            except:
                Brand = None
            sizes = []
            # Get size if available
            try:
                for size in product_data['sizes']:
                    sizes.append(size['name'])
            except KeyError:
                pass


            # Download images
            for images in product_data['pictures_data']:
                # for i in images:
                full_size_url = images['formats']['P0']['url']
                img_name = images['id']

                filepath = 'downloads/' + str(userid) + '/' + str(img_name) + '.jpg'
                if not args.disable_file_download:
                    if not os.path.isfile(filepath):
                        c.execute(
                            f"SELECT ID FROM Depop_Data WHERE ID = {product_id}")
                        result = c.fetchone()
                        if result:
                            # Already exists
                            c.execute('''UPDATE Depop_Data SET Image = ? WHERE ID = ?''', (filepath, product_id))
                            conn.commit()
                            req = requests.get(full_size_url)
                            with open(filepath, 'wb') as f:
                                f.write(req.content)
                            print(f"Image saved to {filepath}")
                        else:
                            print(img_name)
                            print(full_size_url)
                            req = requests.get(full_size_url)
                            params = (
                            product_id, id, Sold, Gender, Category, subcategory, ','.join(sizes), State, Brand, ','.join(Colors), Price, filepath, description, title, Platform, address, discountedPriceAmount, dateUpdated)
                            c.execute(
                                "INSERT OR IGNORE INTO Depop_Data(ID, User_id, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Description, Title, Platform, Address, discountedPriceAmount, dateUpdated)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                params)
                            conn.commit()
                            with open(filepath, 'wb') as f:
                                f.write(req.content)
                            print(f"Image saved to {filepath}")
                    else:
                        print('File already exists, skipped.')
                elif args.disable_file_download:
                    c.execute(
                        f"SELECT ID FROM Depop_Data WHERE ID = {product_id}")
                    result = c.fetchone()
                    if result:
                        #Already exists
                        continue
                    else:
                        params = (
                            product_id, Sold, id, Gender, Category, subcategory, ','.join(sizes), State, Brand, ','.join(Colors),
                            Price, description, title, Platform, address, discountedPriceAmount, dateUpdated)
                        c.execute(
                            "INSERT OR IGNORE INTO Depop_Data(ID, Sold, User_id, Gender, Category, subcategory, size, State, Brand, Colors, Price, description, title, Platform, Address, discountedPriceAmount, dateUpdated)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            params)
                        conn.commit()

            # Download videos
            if len(product_data['videos']) > 0:
                for x in product_data['videos']:
                    for source in x['outputs']:
                        if source['format'] == 'MP4':
                            video_url = source['url']
                            file_name = video_url.split('/')[5]
                            filepath = 'downloads/' + str(userid) + '/' + str(file_name)
                            if not args.disable_file_download:
                                if not os.path.isfile(filepath):
                                    req = requests.get(video_url)
                                    #print(video_url)
                                    params = (
                                        product_id, Sold, id, Gender, Category, subcategory, ','.join(sizes), State, Brand,
                                        ','.join(Colors), Price, filepath, description, title, Platform, address, discountedPriceAmount, dateUpdated)
                                    c.execute(
                                        "INSERT OR IGNORE INTO Depop_Data(ID, Sold, User_id, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, description, title, Platform, Address, discountedPriceAmount, dateUpdated)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                        params)
                                    conn.commit()
                                    with open(filepath, 'wb') as f:
                                        f.write(req.content)
                                    print(f"Video saved to {filepath}")
                                else:
                                    if not args.disable_file_download:
                                        print('File already exists, skipped.')
                            elif args.disable_file_download:
                                c.execute(
                                    f"SELECT ID FROM Depop_Data WHERE ID = {product_id}")
                                result = c.fetchone()
                                if result:
                                    # Already exists
                                    continue
                                else:
                                    params = (
                                        product_id, Sold, id, Gender, Category, subcategory, ','.join(sizes), State,
                                        Brand, ','.join(Colors),
                                        Price, description, title, Platform, address, discountedPriceAmount, dateUpdated)
                                    c.execute(
                                        "INSERT OR IGNORE INTO Depop_Data(ID, Sold, User_id, Gender, Category, subcategory, size, State, Brand, Colors, Price, description, title, Platform, Address, discountedPriceAmount, dateUpdated)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                        params)
                                    conn.commit()





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
    session = vinted_session()
    download_vinted_data(userids, session)
