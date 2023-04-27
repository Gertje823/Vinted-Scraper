
import os 
class PathManager:
    
    @staticmethod
    def create():
        PathManager.create_dowloads()
        PathManager.create_avatars()
        PathManager.create_messages()
    
    @staticmethod
    def create_dowloads():
        # create downlods folders
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
            
    @staticmethod
    def create_avatars():
        try:
            os.mkdir(f"downloads/Avatars/")
        except OSError:
            print ("Creation of the directory failed or the folder already exists ")
    
    @staticmethod
    def create_messages():
        try:
            os.mkdir(f"downloads/Messages/")
        except OSError:
            print("Creation of the directory failed or the folder already exists ")
    
    @staticmethod
    def create_user_folder(USER_ID):
        # Download all products
        path= "downloads/" + str(USER_ID) +'/'
        try:
            os.mkdir(path)
        except OSError:
            print ("Creation of the directory %s failed or the folder already exists " % path)
        else:
            print ("Successfully created the directory %s " % path)
            
            