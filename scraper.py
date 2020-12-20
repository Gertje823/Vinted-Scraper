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
#USER_ID = 3918287


#Import users
with open('users.txt', 'r', encoding='utf-8') as list_of_users:
            userids = list_of_users.readlines()
#database
sqlite_file = 'data.sqlite'
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS Data
             (ID, User_id, Sold, Gender, Category, subcategory, size, State, Brand, Colors, Price, Image, Images, Description, Title)''')

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
    USER_ID = USER_ID.strip('\n')
    url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page=1&per_page=200000'
    print('ID=' + str(USER_ID))

    r = s.get(url)
    jsonresponse = r.json()
    print(jsonresponse)
    products = jsonresponse['items']
    if products:
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
        print('User does not exists or has no products')
    else:
        print("Downloaded all images")
conn.close()
