import requests
import os
from path_manager import PathManager

class DataExtractor:
    
    @staticmethod
    def download_images(images, USER_ID):
        for image in images:
            full_size_url = image['full_size_url']
            img_name = image['high_resolution']['id']
            filepath = 'downloads/'+ str(USER_ID) +'/' + img_name +'.jpeg'
            if not os.path.isfile(filepath):
                PathManager.create_dowloads()
                #print(full_size_url)
                req = requests.get(full_size_url)
                # INSERT PRODUCT INTO DB
                with open(filepath, 'wb') as f:
                    f.write(req.content)

    @staticmethod
    def dowload_avatar(data):
        photo_url = data['full_size_url']
        photo_id = data['id']
        req = requests.get(photo_url)
        filepath = f'downloads/Avatars/{photo_id}.jpeg'
        if not os.path.isfile(filepath):
            PathManager.create_avatars()
            with open(filepath, 'wb') as f:
                f.write(req.content)
