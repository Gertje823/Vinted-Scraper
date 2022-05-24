import requests
import json
import os.path
import os
import sqlite3
import argparse
import time

# ArgParse
parser = argparse.ArgumentParser(description='Vinted & Depop Scraper/Downloader. Default downloads Vinted')
parser.add_argument('--depop','-d',dest='Depop', action='store_true', help='Download Depop data.')
args = parser.parse_args()

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
# Create Users table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS Users
             (Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, Verification_google, Verification_phone, Platform)''')
c.execute('''CREATE TABLE IF NOT EXISTS Depop_Users
             (Username, User_id, bio, first_name, followers, following, initials, items_sold, last_name, last_seen, Avatar, reviews_rating, reviews_total, verified, website)''')



def vinted_session():
    s = requests.Session()
    s.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'DNT': '1',
        'Connection': 'keep-alive',
        'TE': 'Trailers',
    }
    req = s.get("https://www.vinted.nl/member/13396883-wiwi2812")
    csrfToken = req.text.split('<meta name="csrf-token" content="')[1].split('"')[0]
    s.headers['X-CSRF-Token'] = csrfToken
    params = (
        ('localize', 'true'),
    )
    return s, params

def download_vinted_data(userids, s, params):
    Platform = "Vinted"
    for USER_ID in userids:
        # Get user profile data
        url = f"https://www.vinted.nl/api/v2/users/{USER_ID.strip()}"
        r = s.get(url, params=params)
        if r.status_code == 200:
            jsonresponse = r.json()
            data = jsonresponse['user']
            #get data
            username = data['login']
            gender = data['gender']
            given_item_count = data['given_item_count']
            taken_item_count = data['taken_item_count']
            followers_count = data['followers_count']
            following_count = data['following_count']
            positive_feedback_count = data['positive_feedback_count']
            negative_feedback_count = data['negative_feedback_count']
            feedback_reputation = data['feedback_reputation']
            created_at = data['created_at']
            last_loged_on_ts = data['last_loged_on_ts']
            city_id = data['city_id']
            city = data['city']
            country_title = data['country_title']
            verification_email = data['verification']['email']['valid']
            verification_facebook = data['verification']['facebook']['valid']
            verification_google = data['verification']['google']['valid']
            verification_phone = data['verification']['phone']['valid']
            if data['photo']:
                photo = data['photo']['url']
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
            jsonresponse = r.json()
            #print(jsonresponse)
            products = jsonresponse['items']
            if products:
                # Download all products
                path= "downloads/" + str(USER_ID) +'/'
                try:
                    os.mkdir(path)
                except OSError:
                    print ("Creation of the directory %s failed or the folder already exists " % path)
                else:
                    print ("Successfully created the directory %s " % path)
                for product in jsonresponse['items']:
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
            else:
                print("Downloaded all images")
        else:
            print(f"User {USER_ID} does not exists")
    conn.close()

def download_depop_data(userids):
    Platform = "Depop"
    for userid in userids:
        userid = userid.strip()
        print(userid)
        slugs = []
        # Get userid from username
        url = f"https://webapi.depop.com/api/v1/shop/{userid}/"
        print(url)
        data = requests.get(url).json()

        id = str(data['id'])
        last_seen = str(data['last_seen'])
        bio = str(data['bio']).encode("UTF-8")
        followers = str(data['followers'])
        following = str(data['following'])
        try:
            initials = str(data['initials']).encode("UTF-8")
        except UnicodeEncodeError:
            initials = None
        items_sold = str(data['items_sold'])
        last_name = str(data['last_name']).encode("UTF-8")
        first_name = str(data['first_name']).encode("UTF-8")
        reviews_rating = str(data['reviews_rating'])
        reviews_total = str(data['reviews_total'])
        username = str(data['username'])
        verified = str(data['verified'])
        website = str(data['website'])
        filepath = None
        if len(data['picture']) > 0:
            photo = data['picture']['300'][:-6] + "U0.jpg"
            print(photo)
            try:
                os.mkdir(f"downloads/Avatars/")
            except OSError:
                print("Creation of the directory failed or the folder already exists ")
            req = requests.get(photo)
            filepath = f'downloads/Avatars/{id}.jpeg'
            if not os.path.isfile(filepath):
                with open(filepath, 'wb') as f:
                    f.write(req.content)
                print(f"Avatar saved to {filepath}")
        else:
            print('File already exists, skipped.')
        params = (username, id, bio, first_name, followers, following, initials, items_sold, last_name, last_seen, filepath, reviews_rating, reviews_total, verified,website)
        c.execute(
            "INSERT OR IGNORE INTO Depop_Users(Username, User_id, bio, first_name, followers, following, initials, items_sold, last_name, last_seen, Avatar, reviews_rating, reviews_total, verified, website) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            params)
        conn.commit()



        baseurl = f"https://webapi.depop.com/api/v1/shop/{id}/products/?limit=200"
        data = requests.get(baseurl).json()
        print("Fetching all produts...")
        for i in data['products']:
            slugs.append(i['slug'])
        while True:

            url = baseurl + f"&offset_id={data['meta']['last_offset_id']}"

            print(url)
            try:
                data = requests.get(url).json()
                #print(data)
            except:
                print(requests.get(url).text)
                exit()
                break
            for i in data['products']:
                slugs.append(i['slug'])
            if data['meta']['end'] == True:
                print("Got all products. Start Downloading...")
                break
        print(len(slugs))
        path = "downloads/" + str(userid) + '/'
        try:
            os.mkdir(path)
        except OSError:
            print("Creation of the directory %s failed or the folder already exists " % path)
        for slug in slugs:
            url = f"https://webapi.depop.com/api/v2/product/{slug}"
            #print(url)
            try:
                product_data = requests.get(url).json()
            except ValueError:
                print("Error decoding JSON data. Skipping...")
                pass

            product_id = product_data['id']
            try:
                Gender = product_data['gender']
            except KeyError:
                Gender = None
            Category = product_data['categoryId']
            try:
                State = product_data['condition']['name']
            except KeyError:
                State = None

            Price = product_data['price']['priceAmount'] + product_data['price']['currencyName']
            description = product_data['description']
            Sold = product_data['status']
            title = slug.replace("-"," ")

            Colors = []
            # Get colors if available
            try:
                for color in product_data['colour']:
                    Colors.append(color['name'])
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



            for images in product_data['pictures']:
                for i in images:
                    full_size_url = i['url']
                    img_name = i['id']
                print(img_name)
                filepath = 'downloads/' + str(userid) + '/' + str(img_name) + '.jpg'
                if not os.path.isfile(filepath):
                    print(full_size_url)
                    req = requests.get(full_size_url)
                    params = (
                    product_id, Sold, id, Gender, Category, ','.join(sizes), State, Brand, ','.join(Colors), Price, filepath, description, title, Platform)
                    c.execute(
                        "INSERT OR IGNORE INTO Data(ID, Sold, User_id, Gender, Category, size, State, Brand, Colors, Price, Images, description, title, Platform)VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        params)
                    conn.commit()
                    with open(filepath, 'wb') as f:
                        f.write(req.content)
                    print(f"Image saved to {filepath}")
                else:
                    print('File already exists, skipped.')

#Import users from txt file
with open('users.txt', 'r', encoding='utf-8') as list_of_users:
            userids = list_of_users.readlines()

if args.Depop:
    download_depop_data(userids)
else:
    session, params = vinted_session()
    download_vinted_data(userids, session, params)
