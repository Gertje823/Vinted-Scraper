import cloudscraper
import sqlite3
import argparse
import os, time
import requests
import re
import json
from tqdm import tqdm

class vinted_scraper:

    def __init__(self, download_location='downloads'):
      """"
      Init Vinted Class
       - Create folders if not already exists
      """
      global Platform
      Platform = 'Vinted'
      self.download_location = download_location
      # create download folders
      if not os.path.exists(download_location):
          os.makedirs(download_location)

      if not os.path.exists(f'{download_location}/Avatars/'):
          os.makedirs(f'{download_location}/Avatars/')

    def init_database(self, sqlite_file='data.db'):
        """"
        Create database and tables if not already exists
        """
        conn = sqlite3.connect(sqlite_file)
        c = conn.cursor()
        # Create Data table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS Vinted_Data
                    (ID, User_id, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Images, Description, Title, Platform)''')
        # Create User table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS Vinted_Users
                    (Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, Verification_google, Verification_phone, Platform)''')
        # Create Private msg table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS Vinted_Messages
                    (thread_id, from_user_id, to_user_id, msg_id, body, photos)''')
        # Create Category teble if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS Vinted_Categories (Cat_id UNIQUE, Cat_title, Cat_code, Cat_size_group_id, Cat_size_group_ids, Cat_shippable, Cat_parent_id, Cat_item_count, Cat_url)''')

        conn.commit()
        return c, conn

    def update_categories(self, vinted_session, sqlite_file='data.db'):
      """"
      Scrape all categories
      """
      url = "https://www.vinted.com/data/search-json.js"
      response = vinted_session.get(url)

      pattern = "window\.search_form_data = ([^;]*);"
      json_data = re.findall(pattern, response.content.decode('utf-8'))
      json_data = json.loads(json_data[0])
      #print("Updating Categories....")
      pbar = tqdm(desc="Updating Categories", total=len(json_data['catalogs']), unit="items")
      y=0
      for x in json_data['catalogs']:
        y=+1
        pbar.update(y)
        cat_title = json_data['catalogs'][x]['title']
        cat_id = json_data['catalogs'][x]['id']
        cat_code = json_data['catalogs'][x]['code']
        cat_size_group_id = json_data['catalogs'][x]['size_group_id']
        cat_size_group_ids = json_data['catalogs'][x]['size_group_ids']
        cat_shippable = json_data['catalogs'][x]['shippable']
        cat_parent_id = json_data['catalogs'][x]['parent_id']
        cat_item_count = json_data['catalogs'][x]['item_count']
        cat_url = json_data['catalogs'][x]['url']

        # Add category data to DB
        values = [(cat_id, cat_title, cat_code, cat_size_group_id, str(cat_size_group_ids), cat_shippable, cat_parent_id, cat_item_count, cat_url)]
        columns = ['Cat_id', 'Cat_title', 'Cat_code', 'Cat_size_group_id', 'Cat_size_group_ids', 'Cat_shippable', 'Cat_parent_id', 'Cat_item_count', 'Cat_url']
        self.insert_into_db('Vinted_Categories', columns, values, sqlite_file)


    def create_session(self, _vinted_fr_session=None):
      s = cloudscraper.create_scraper()
      if _vinted_fr_session:
          s.headers = {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
              'Accept': 'application/json, text/plain, */*',
              'Accept-Language': 'en',
              'DNT': '1',
              'Connection': 'keep-alive',
              'TE': 'Trailers',
              'Cookie': f'_vinted_fr_session={_vinted_fr_session};'

          }
      else:
          s.headers = {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
              'Accept': 'application/json, text/plain, */*',
              'Accept-Language': 'en',
              'DNT': '1',
              'Connection': 'keep-alive',
              'TE': 'Trailers',
          }
      req = s.get("https://www.vinted.com/")
      csrfToken = req.text.split('<meta name="csrf-token" content="')[1].split('"')[0]
      s.headers['X-CSRF-Token'] = csrfToken
      return s

    def insert_into_db(self, table_name=None, columns=None, values=None, sqlite_file='data.db'):
        """"
        Dynamicly insert values to DB
        """
        conn = sqlite3.connect(sqlite_file)
        c = conn.cursor()
        query = f"INSERT OR REPLACE INTO {table_name}({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
        for val_tuple in values:
            c.execute(query, val_tuple)
        conn.commit()

    def get_all_items(self, s, total_pages, items, url):
        """"
        Loop over all item pages and return items
        """
        for page in range(int(total_pages)):
            page += 1
            #print(page)
            url1 = f'{url}page={page}&per_page=200000'
            #print(url1)
            r = s.get(url1)
            if r.status_code == 200:
                r = r.json()
                try:
                    items.extend(r['items'])
                    print(f"Fetching page {page + 1}/{r['pagination']['total_pages']}", end="\r", flush=True)
                except KeyError:
                    break
            elif r.status_code == 429:
                print(f"Ratelimit waiting {r.headers['Retry-After']} seconds...")
                limit = round(int(r.headers['Retry-After']) / 2)
                for i in range(limit, 0, -1):
                    print(f"{i}", end="\r", flush=True)
                    time.sleep(1)
                page-=1
                continue
            else:
                print(f"Error: code {r.status_code} on: {url}")

        return items

    def download_user_data(self, vinted_session, user_id, sqlite_file="data.db", disable_file_download=False):
        """"
        Download Vinted User Data
        """
        user_id = user_id.strip()
        # Get user profile data
        url = f"https://www.vinted.com/api/v2/users/{user_id}"
        r = vinted_session.get(url)
        if r.status_code == 200:
            data = r.json()['user']

            username = data['login']
            gender = data['gender']
            given_item_count = data['given_item_count']
            taken_item_count = data['taken_item_count']
            followers_count = data['followers_count']
            following_count = data['following_count']
            positive_feedback_count = data['positive_feedback_count']
            negative_feedback_count = data['negative_feedback_count']
            feedback_reputation = data['feedback_reputation']
            last_loged_on_ts = data['last_loged_on_ts']
            city_id = data['city_id']
            city = data['city']
            country_title = data['country_title']
            verification_email = data['verification']['email']['valid']
            verification_facebook = data['verification']['facebook']['valid']
            verification_google = data['verification']['google']['valid']
            verification_phone = data['verification']['phone']['valid']
            # Created date is not always available....
            try:
              created_at = data['created_at']
            except KeyError:
              created_at = ""

            # Download user avatar
            if data['photo']:
                photo = data['photo']['full_size_url']
                photo_id = data['photo']['id']
                req = requests.get(photo)
                filepath = f'{self.download_location}/Avatars/{photo_id}.jpeg'
                if not os.path.isfile(filepath) and not disable_file_download:
                  print(photo_id)
                  with open(filepath, 'wb') as f:
                      f.write(req.content)
                  print(f"Avatar saved to {filepath}")
                else:
                  print('File already exists, skipped.')
            else:
                # No avatar :(
                filepath = ""
            values = [(
              username, user_id, gender, given_item_count, taken_item_count, followers_count, following_count,
              positive_feedback_count, negative_feedback_count, feedback_reputation, filepath, created_at,
              last_loged_on_ts, city_id, city, country_title, verification_email, verification_google,
              verification_facebook, verification_phone)]
            columns = ['Username', 'User_id', 'Gender', 'Given_item_count', 'Taken_item_count', 'Followers_count', 'Following_count', 'Positive_feedback_count', 'Negative_feedback_count', 'Feedback_reputation', 'Avatar', 'Created_at', 'Last_loged_on_ts', 'City_id', 'City', 'Country_title', 'Verification_email', 'Verification_facebook', 'Verification_google', 'Verification_phone']
            self.insert_into_db('Vinted_Users', columns, values, sqlite_file)

    def download_item_data(self, vinted_session, user_id, sqlite_file="data.db", disable_file_download=False):
        url = f'https://www.vinted.com/api/v2/users/{user_id}/items?page=1&per_page=200000'
        r = vinted_session.get(url)
        x = 0
        if r.status_code == 200:
            items = []
            print(f"Fetching page 1/{r.json()['pagination']['total_pages']}")
            items.extend(r.json()['items'])
            if r.json()['pagination']['total_pages'] > 1:
                print(f"User has more than {len(items)} items. fetching next page....")
                items = self.get_all_items(vinted_session, r.json()['pagination']['total_pages'], items, f'https://www.vinted.com/api/v2/users/{user_id}/items?')

            print(f"Total items: {len(items)}")
            if items:
                path = f"{self.download_location}/{user_id}/"
                if not os.path.exists(path):
                    os.makedirs(path)
                pbar = tqdm(desc="Downloading Items", total=len(items), unit=" items")
                # Loop over all items
                for product in items:
                    x=+1
                    pbar.update(x)
                    img = product['photos']
                    ID = product['id']
                    User_id = product['user_id']
                    description = product['description']
                    Gender = product['user']['gender']
                    Category = product['catalog_id']
                    size = product['size']
                    State = product['status']
                    Brand = product['brand']
                    Colors = product['color1']
                    Price = product['price']
                    Price = f"{Price['amount']} {Price['currency_code']}"
                    Images = product['photos']
                    title = product['title']

                    # Download images
                    if Images:
                        for images in img:
                            full_size_url = images['full_size_url']
                            img_name = images['high_resolution']['id']
                            filepath = path + img_name + '.jpeg'
                            if not os.path.isfile(filepath):
                                pbar.write(f"Downloading {filepath}")
                                req = requests.get(full_size_url)
                                values = [(ID, User_id, Gender, Category, size, State, Brand, Colors, Price, filepath, description, title, Platform)]
                                columns = ['ID', 'User_id', 'Gender', 'Category', 'size', 'State', 'Brand', 'Colors', 'Price', 'Images', 'description', 'title', 'Platform']
                                self.insert_into_db('Vinted_Data', columns, values, sqlite_file)
                                if not disable_file_download:
                                    with open(filepath, 'wb') as f:
                                        f.write(req.content)
                            else:
                                pbar.write('File already exists, skipped.')
                pbar.close()
            else:
                print('User has no items')
        elif r.status_code == 429:
            print(f"Ratelimit waiting {r.headers['Retry-After']} seconds...")
            limit = round(int(r.headers['Retry-After']) / 2)
            for i in range(limit, 0, -1):
                print(f"{i}", end="\r", flush=True)
                time.sleep(1)
        else:
            print(f"User {user_id} does not exists")

    def download_priv_msg(self, vinted_session, own_user_id, session_id, sqlite_file="data.db", disable_file_download=False):
        download_location = self.download_location + '/Messages/'
        data = vinted_session.get(f"https://www.vinted.com/api/v2/inbox?page=1&per_page=20")
        if data.status_code == 403:
            # Access denied
            print(
                f"Error: Access Denied\nCan't get content from 'https://www.vinted.nl/api/v2/users/{own_user_id}/msg_threads'\nPlease ensure your entered a valid sessionid and userid")
            exit(1)

        data = data.json()
        if not os.path.exists(download_location):
            os.makedirs(download_location)
        if not "conversations" in data:
            print("Error: Can't find any messages.\nPlease make sure you entered the sessionid and userid correctly")
            exit(1)

        for msg_threads in data['conversations']:
            id = msg_threads['id']
            msg_data = vinted_session.get(f"https://www.vinted.com/api/v2/users/{own_user_id}/msg_threads/{id}").json()

            thread_id = msg_data['msg_thread']['id']
            for message in msg_data['msg_thread']['messages']:
                try:
                    photo_data = message['entity']['photos']
                except:
                    # message has no images. Skipping..
                    continue

                if len(photo_data) > 0:
                    # create user folder
                    if not os.path.exists(f"downloads/Messages/{message['entity']['user_id']}"):
                        os.makedirs(f"downloads/Messages/{message['entity']['user_id']}")

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
                    if int(from_user_id) == int(own_user_id):
                        to_user_id = msg_data['msg_thread']['opposite_user']['id']
                    else:
                        to_user_id = own_user_id
                    values = [(thread_id, from_user_id, to_user_id, msg_id, body, str(photo_list))]
                    columns = ['thread_id', 'from_user_id', 'to_user_id', 'msg_id', 'body', 'photos']
                    self.insert_into_db('Vinted_Messages', columns, values, sqlite_file)

    def download_vinted_tags(self, vinted_session, tags, sqlite_file="data.db", disable_file_download=False):
        """
        Downloads items by search tag.
        ** This feature is limited **
        Search does not provide much product info.
        TODO:
            - Find a better way to get product info from search
            - Find a way to get more than 3k items
        """
        Platform = "Vinted"
        for tag in tags:
            x = 0
            tag = tag.strip()
            r = vinted_session.get(f"https://www.vinted.com/api/v2/catalog/items?search_text={tag}&per_page=200000")
            if r.status_code == 200:
                items = []
                search_session_id = r.json()['search_tracking_params']['search_session_id']
                print(f"Fetching page 1/{r.json()['pagination']['total_pages']}")
                items.extend(r.json()['items'])
                if r.json()['pagination']['total_pages'] > 1:
                    print(f"There are more than {len(items)} items. fetching next page....")
                    self.get_all_items(vinted_session, r.json()['pagination']['total_pages'], items, f"https://www.vinted.com/api/v2/catalog/items?search_text={tag}&time={round(time.time())}&search_session_id={search_session_id}&")

                if len(items) > 0:
                    print(f"Found {len(items)} items")
                    path = self.download_location + '/tags/' + tag.lower() + '/'
                    if not os.path.exists(path):
                            os.makedirs(path)
                    kek = 0
                    pbar = tqdm(desc="Downloading Items", total=len(items), unit=" items")
                    for item in items:
                        x=+1
                        pbar.update(x)
                        ID = item['id']
                        User_id = item['user']['id']
                        # Description is not available in search
                        description = ''
                        # Gender is not available in search
                        Gender = ''
                        # Category is not available in search
                        Category = ''
                        size = item['size_title']
                        # State is not available in search
                        State = ''
                        Brand = item['brand_title']
                        # Color is not available in search
                        Colors = ''
                        Price = f"{item['price']} {item['currency']}"
                        title = item['title']

                        full_size_url = item['photo']['full_size_url']
                        img_name = item['photo']['high_resolution']['id']
                        filepath = path + img_name + '.jpeg'

                        if not os.path.isfile(filepath):
                            req = requests.get(full_size_url)
                            pbar.write(f"Downloading {filepath}")
                            # Write to DB
                            values = [(ID, User_id, Gender, Category, size, State, Brand, Colors, Price, filepath, description,title, Platform)]
                            columns = ['ID', 'User_id', 'Gender', 'Category', 'size', 'State', 'Brand', 'Colors', 'Price', 'Images', 'description', 'title', 'Platform']
                            self.insert_into_db('Vinted_Data', columns, values, sqlite_file)

                            with open(filepath, 'wb') as f:
                                f.write(req.content)
                            pbar.write(f"Image saved to {filepath}")
                     
                        else:
                            pbar.write('File already exists, skipped.')
                else:
                     print(f'No products found for tag "{tag}"')

            elif r.status_code == 429:
                print(f"Ratelimit waiting {r.headers['Retry-After']} seconds...")
                limit = round(int(r.headers['Retry-After']) / 2)
                for i in range(limit, 0, -1):
                    print(f"{i}", end="\r", flush=True)
                    time.sleep(1)
                continue