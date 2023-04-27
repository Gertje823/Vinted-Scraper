from extractor import DataExtractor
from requester import DataRequester
from dbconnector import DatabaseConnection
import cloudscraper
from db import DBRepository
from modelos import Data
from path_manager import PathManager

class Session:

    @staticmethod
    def get_sess():
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
        csrfToken = req.text.split(
            '<meta name="csrf-token" content="')[1].split('"')[0]
        s.headers['X-CSRF-Token'] = csrfToken
        return s
    
class VintedScraper:
    
    def __init__(self):
        
        # INIT DATABASE
        self.init_db()
        with DatabaseConnection.get_session(self.engine) as db_session:
            self.repo = DBRepository(db_session)
            
        # INIT WEB CLIENT SESSION
        self.session = Session.get_sess()
        
    
    def init_db(self):
        # init engine
        self.engine = DatabaseConnection.get_engine()
        # init db tables
        DatabaseConnection.initialize_db(self.engine)
    
    def download_data(self, USER_ID):
        PathManager.create_user_folder(USER_ID)
        # extract user and insert into database
        user = DataRequester.request_user(self.session, USER_ID)
        self.repo.insert_register(user)
        USER_ID = USER_ID.strip('\n')
        # retrive user's products
        if user:
            products, s_code = DataRequester.request_products(self.session, USER_ID)
            if s_code == 200 and products:
                # Download all products
                for product in products:
                    
                    # Extract the current product and insert into db
                    p = Data.extract_product(product)
                    self.repo.insert_register(p)
                    # download the products' images
                    DataExtractor.download_images(product['photos'], USER_ID)
                
if __name__ == '__main__':
    #Import users from txt file
    PathManager.create()
    with open('users.txt', 'r', encoding='utf-8') as list_of_users:
        user_ids = list_of_users.readlines()
    vscraper = VintedScraper()
    for user_id in user_ids:
        id_ = user_id.strip()
        vscraper.download_data(id_)