import requests
import json
import os.path
import os
import sqlite3
from argparse import ArgumentParser
import time
from fake_useragent import UserAgent


if not os.path.exists('downloads'):
    os.makedirs('downloads')

#Import users
with open('users.txt', 'r', encoding='utf-8') as list_of_users:
            userids = list_of_users.readlines()
#database
sqlite_file = 'data.sqlite'
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()
# Create Data table
c.execute('''CREATE TABLE IF NOT EXISTS Data
             (ID, User_id, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Images, Description, Title)''')
# Create Users table
c.execute('''CREATE TABLE IF NOT EXISTS Users
             (Username, User_id, Gender, Given_item_count, Taken_item_count, Followers_count, Following_count, Positive_feedback_count, Negative_feedback_count, Feedback_reputation, Avatar, Created_at, Last_loged_on_ts, City_id, City, Country_title, Verification_email, Verification_facebook, Verification_google, Verification_phone)''')

s = requests.Session()
ua = UserAgent()
s.headers = {
    'User-Agent': ua.firefox,
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

for USER_ID in userids:
    # Get user profile data
    url = f"https://www.vinted.nl/api/v2/users/{USER_ID}"
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
        print(jsonresponse)
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


                    print(img)
                    if Images:
                        for images in img:
                            full_size_url = images['full_size_url']
                            img_name = images['high_resolution']['id']
                            print(img_name)
                            filepath = 'downloads/'+ str(USER_ID) +'/' + img_name +'.jpeg'
                            if not os.path.isfile(filepath):
                                print(full_size_url)
                                req = requests.get(full_size_url)
                                params = (ID, User_id, Gender, Category, size, State, Brand, Colors, Price, filepath, description, title)
                                c.execute("INSERT INTO Data(ID, User_id, Gender, Category, size, State, Brand, Colors, Price, Images, description, title)VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", params)
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
        print("User does not exists")
conn.close()
