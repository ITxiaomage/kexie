import pymongo
import json
from .define import *

def search_user_from_momgodb(id):
    client = pymongo.MongoClient()
    db = client[MONGODB_DB]
    collection = db[COLLECTION]
    user = collection.find_one({"id": id})
    return user
def update_mongo_accord_user_id(user_id,channel_list):
    try:
        client = pymongo.MongoClient()
        db = client[MONGODB_DB]
        collection = db[COLLECTION]
        collection.update_one({"id":user_id},{'$set':{'channelList':channel_list}})
    except Exception as err:
        print('更新mongodb中的用户画像失败')
        print(err)