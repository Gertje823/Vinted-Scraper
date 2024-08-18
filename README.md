# Vinted-Scraper
This is a tool to download images and scrape data from Vinted & Depop and store it in a SQLite database.

-- *Currently working on [version 2.0](https://github.com/Gertje823/Vinted-Scraper/tree/v2)* (WIP) -- 

## How to use
1. Download/clone this repo
2. Download the dependencies using `pip install -r requirements.txt`
3. run the script `python scraper.py`
   
### Vinted
Put the user IDs of the accounts in the users.txt and run the script.
The script will download all the images and put it in the downloads folder.
The data will be stored in the SQLite database.

### Depop
Put the usernames of the accounts in the users.txt and run the script with `-d`.
The script will download all the images and videos and put it in the downloads folder.
The data will be stored in the SQLite database.

## Arguments
`-p` [Vinted] Scrape all images from your private messages. (requires `-s` to login and `-u` to set your userid)  
`-s "your_vinted_fr_session"` [Vinted] to login to your account. [how to get sessionid?](https://github.com/Gertje823/Vinted-Scraper/wiki/How-to-get-Vinted-sessionID%3F)   
`-u` [Vinted] Set your userid  
`-i` [Vinted] Define the maximum number of images to download. Minimum 1 image. (example: `-i 1` will download only the first image of the product)  
`-n` [Depop] Disable file download (Only scrape product info)  
`-g` [Depop] Also download sold items  
`-b` [Depop] Start from a specific item. (example: `python3 scraper.py -d -n -b "coose-navy-lee-sweatshirt-amazing-lee"`)



### Example:  
Download all images from private messages from your Vinted account  
`python scraper.py -p -u 123456789 -s "RS9KcmE1THMxV3NlclRsbEVRdU52ZVp4UG.......ASFe26"`

## Data that will be scraped
All the images of the products of the users will be downloaded. The avatar of the user will also be downloaded.

All the info will be stored in the sqlite db in the following tables:

### Vinted Users
 `Username`  
 `User_id`     
 `Gender`  
 `Given_item_count`  
 `Taken_item_count`  
 `Followers_count`  
 `Following_count`  
 `Positive_feedback_count`  
 `Negative_feedback_count`  
 `Feedback_reputation`  
 `Avatar`  
 `Created_at`  
 `Last_loged_on_ts`  
 `City_id`  
 `City`  
 `Country_title`  
 `Verification_email`   
 `Verification_facebook`  
 `Verification_google`  
 `Verification_phone`   

### Vinted Products
 `ID`  
 `User_id`    
 `Url`
 `Favourite`
 `Gender`  
 `Category`           
 `Size`         
 `State`  
 `Brand`  
 `Colors`  
 `Price`  
 `Images`  
 `Description`  
 `Title`  
 `Platform`  
 
 ### Depop Users
 `Username`  
 `User_id`     
 `Bio`  
 `first_name`  
 `followers`  
 `following`  
 `initials`  
 `items_sold`  
 `last_name`  
 `last_seen`  
 `Avatar`  
 `reviews_rating`  
 `reviews_total`  
 `verified`  
 `website`  
 ### Depop Products
 `ID`  
 `Sold`    
 `User_id`    
 `Gender`  
 `Category`           
 `Size`         
 `State`  
 `Brand`  
 `Colors`  
 `Price`  
 `Image`  
 `Description`  
 `Title`  
 `Platform`  
 `Address`  
 `discountedPriceAmount`  
 `dateUpdated`  
 
 If you have any feature requests don't hesitate to open an issue :)

## Disclaimer
*This script is designed for educational purposes only. It is intended to demonstrate web scraping techniques and should not be used for any commercial or personal gain. Please note that using this software may violate the terms of service of Vinted and Depop websites, and you assume all responsibility for any consequences that may arise from its use. The creator of this script will not be held responsible for any damages, injuries, or losses that occur while using the software. Use at your own risk.*
