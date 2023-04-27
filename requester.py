from extractor import DataExtractor
from modelos import User, Data, Base

class DataRequester:

    @staticmethod
    def request_items(session, USER_ID, total_pages, items):
        for page in range(int(total_pages)):
            page += 1
            url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page={page}&per_page=200000'
            r = session.get(url).json()
            items.extend(r['items'])

    @staticmethod
    def request_user(session, USER_ID):
        # Get user profile data
        url = f"https://www.vinted.nl/api/v2/users/{USER_ID}"
        r = session.get(url)
        if r.status_code == 200:
            user_data = r.json()['user']
            if user_data:
                user = User.extract_user(user_data)
                # if user's avatar exists -> download it
                if 'photo' in user_data.keys() and user_data['photo']:
                    DataExtractor.dowload_avatar(user_data['photo'])
                return user

    @staticmethod
    def request_products(session, USER_ID):
        url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page=1&per_page=200000'
        r = session.get(url)
        items = []
        items.extend(r.json()['items'])
        # products = jsonresponse['items']
        if r.json()['pagination']['total_pages'] > 1:
            print(f"User has more than {len(items)} items. fetching next page....")
            
            def get_all_items(s, USER_ID, total_pages, items):
                for page in range(int(total_pages)):
                    page +=1
                    url = f'https://www.vinted.nl/api/v2/users/{USER_ID}/items?page={page}&per_page=200000'
                    r = s.get(url).json()
                    print(f"Fetching page {page+1}/{r['pagination']['total_pages']}")
                    items.extend(r['items'])
            get_all_items(session, USER_ID, r.json()['pagination']['total_pages'], items)
        products = items
        return products, r.status_code