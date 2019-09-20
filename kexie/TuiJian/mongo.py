import pymongo
import json
from .define import *

def search_user_from_momgodb(id):
    client = pymongo.MongoClient()
    db = client[MONGODB_DB]
    collection = db[USER_IMAGE]
    user = collection.find_one({"id": id})
    return user
def update_mongo_accord_user_id(user_id,channel_list):
    try:
        client = pymongo.MongoClient()
        db = client[MONGODB_DB]
        collection = db[USER_IMAGE]
        collection.update_one({"id":user_id},{'$set':{'channelList':channel_list}})
    except Exception as err:
        print('更新mongodb中的用户画像失败')
        print(err)

kexie_leader = {
            "万钢":100,
            "怀进鹏":100,
            "徐延豪":100,
            "孟庆海":100,
            "束为":100,
            "宋军":100,
            "王守东":100,
            "殷皓":100,
            "马伟明":100,
            "王曦":100,
            "邓秀新":100,
            "李华":100,
            "李洪":100,
            "李静海":100,
            "何华武":100,
            "沈岩":100,
            "陈左宁":100,
            "周守为":100,
            "郑晓静":100,
            "赵玉沛":100,
            "施一公":100,
            "袁亚湘":100,
            "高松":100,
            "潘建伟":100
        }
def search_kexie_leader_keywords(id = '2000000283'):
    client = pymongo.MongoClient()
    db = client['kexie']
    collection = db[ORG_IMAMGE]
    leader_keywords_dict  = collection.find_one({"id":id})
    return leader_keywords_dict

def save_kexie_leader():
    client = pymongo.MongoClient()
    db = client[MONGODB_DB]
    collection = db[ORG_IMAMGE]
    collection.create_index([("id", 1)], unique=True)
    data ={}
    data['id'] = '2000000283'
    temp_list =[]
    for label,score in kexie_leader.items():
        temp_dict ={}
        temp_dict['label'] = label
        temp_dict['score'] = score
        temp_list.append(temp_dict)
    data['keywords'] = temp_list
    try:
        collection.insert_one(data)
    except Exception as err:
        print('插入失败')
        print(err)
