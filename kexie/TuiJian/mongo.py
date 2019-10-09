import pymongo
import json
import copy
from .define import *
from .cal_similar_news import *
#在mongo中创建新的用户
def create_new_user_in_mongo(user_id,cur_channel,keywords_list):
    client = pymongo.MongoClient()
    db = client[MONGODB_DB]
    collection = db[USER_IMAGE]
    #先初始化一个用户画像
    user_init_images = init_user_image(user_id)
    try:
        collection.insert_one(user_init_images)
    except Exception as err:
        print('初始化一个新用户失败')
    #
    user = search_user_from_momgodb(user_id)
    #更新频道的用户画像
    update_uesr_iamges_accord_keywords_channel(user, cur_channel, keywords_list)

#根据用户id查找用户信息
def search_user_from_momgodb(id):
    client = pymongo.MongoClient()
    db = client[MONGODB_DB]
    collection = db[USER_IMAGE]
    user = collection.find_one({"id": id})
    return user
#根据用户id和频道的关键字列表更新用户画像
def update_uesr_iamges_accord_keywords_channel(user,cur_channel,keywords_list):
    user_channel_list = user['channelList']
    cur_vec = cal_d2v(keywords_list)
    for one_channel in user_channel_list:
        if one_channel['name'] == cur_channel:
            #获取用户画像列表
            user_label_list = one_channel['labelList']
            #这里需要深拷贝
            temp_list = copy.deepcopy(user_label_list)
            #遍历用户画像，找到最相似的画像，如果大于0.8，就合并画像score+10，如果分数超过100，score =100
            # ，否则就加入显得画像，并设置score=10,flag=0
            simi_flag = False#是否有大于0.8的标志
            for one_user_label in user_label_list:
                label = one_user_label['label']
                score = one_user_label['score']
                one_label_vec = cal_d2v(label)
                #相似度大于0.8，
                xsy = xiangsidu(cur_vec,one_label_vec)
                if  xsy> SIMILIAR :
                    simi_flag = True#有相似的
                    score += 10
                    if score > 100:
                        score = 100
                        one_user_label['flag'] = 1#大于100就设置flag=1
                    one_user_label['score'] = score
            if not simi_flag:
                #增加新的画像
                temp_dict= {}
                temp_dict['label'] = keywords_list
                temp_dict['score'] = INIT_SCORE
                temp_dict['flag'] = 0
                temp_list.append(temp_dict)
                one_channel['labelList'] = temp_list
    #更新mongo数据库
    update_mongo_accord_user_id(user,user['channelList'])


#根据用户更新用户画像
def update_mongo_accord_user_id(user,channel_list):
    user_id = user['id']
    try:
        client = pymongo.MongoClient()
        db = client[MONGODB_DB]
        collection = db[USER_IMAGE]
        collection.update_one({"id":user_id},{'$set':{'channelList':channel_list}})
    except Exception as err:
        print('更新mongodb中的用户画像失败')
        print(err)

def search_kexie_leader_keywords(id = '2000000283'):
    client = pymongo.MongoClient()
    db = client[MONGODB_DB]
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

#根据uesr_id初始化一个用户
def init_user_image(user_id):
    user_images= {
	"id":user_id,
	"department":[],
	"channelList":[
		{
		"name":"时政要闻",
		"dataScore":[],
		"labelList":[],
		"hidden":1
		},
		{
		"name":"中国科协",
		"dataScore":[],
		"labelList":[],
		"hidden":1
		},
		{
		"name":"全国学会",
		"dataScore":[],
		"labelList":[],
		"hidden":1
		},
		{
		"name":"地方科协",
		"dataScore":[],
		"labelList":[],
		"hidden":1
		},
		{
		"name":"科技热点",
		"dataScore":[],
		"labelList":[],
		"hidden":1
		}
	]
    }
    return user_images

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