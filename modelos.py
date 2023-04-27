from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///data.sqlite')


class User(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    gender = Column(String)
    given_item_count = Column(Integer)
    taken_item_count = Column(Integer)
    followers_count = Column(Integer)
    following_count = Column(Integer)
    positive_feedback_count = Column(Integer)
    negative_feedback_count = Column(Integer)
    feedback_reputation = Column(Integer)
    avatar = Column(String)
    created_at = Column(Integer)
    last_logged_on_ts = Column(Integer)
    city_id = Column(Integer)
    city = Column(String)
    country_title = Column(String)
    verification_email = Column(String)
    verification_facebook = Column(String)
    verification_google = Column(String)
    verification_phone = Column(String)
    platform = Column(String)

    data = relationship("Data", back_populates="user")

    @staticmethod
    def extract_user(data):
        fields = ["id", "username", "gender", "given_item_count", "taken_item_count",
                  "followers_count", "following_count", "positive_feedback_count", "negative_feedback_count",
                  "feedback_reputation", "avatar", "created_at", "last_logged_on_ts", "city_id", "city", "country_title",
                  "verification_email", "verification_facebook", "verification_google", "verification_phone", "platform"]
        user_data = {k: v for k, v in data.items() if k in fields}
        user_data['username'] = data['login']
        user_data['verification_email'] = data['verification']['email']['valid']
        user_data['verification_facebook'] = data['verification']['facebook']['valid']
        user_data['verification_google'] = data['verification']['google']['valid']
        user_data['verification_phone'] = data['verification']['phone']['valid']
        return User(**user_data)


class Data(Base):
    __tablename__ = 'Data'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    sold = Column(String)
    gender = Column(String)
    category = Column(String)
    subcategory = Column(String)
    size = Column(String)
    state = Column(String)
    brand = Column(String)
    colors = Column(String)
    price = Column(String)
    image = Column(String)
    images = Column(String)
    description = Column(String)
    title = Column(String)
    platform = Column(String)

    user = relationship("User", back_populates="data")

    @staticmethod
    def extract_product(data):
        fields = ["id", "user_id", "sold", "gender", "category", "subcategory", "size", "state",
                  "brand", "colors", "price", "image", "images", "description", "title", "platform"]
        product_data = {k: v for k, v in data.items() if k in fields}
        product_data['price'] = f"{product_data['price']['amount']} {product_data['price']['currency_code']}"
        product_data['gender']= data['user']['gender']
        return Data(**product_data)
