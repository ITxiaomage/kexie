from django.shortcuts import render
from django.http import  HttpResponse
from . import spider
from .models import *
from . import initData
from . import  handle_cast
import json
from .define import *
from .organiza import *
from .cal_similar_news import *
from .mongo import *
from .cal_similar_news import  *
import copy


#根据部门和频道获
def channel_branch(request):
    result_list= []
    #获取频道错误就设置为时政要闻
    try:
        channel =  request.GET.get('channel')
        if channel not in get_all_channel():
            channel = CHANNEL_SZYW
    except Exception as err:
        print("获取频道出现错误，获取到的数据为：{0}，因此设为默认值:{1}".format(channel,CHANNEL_SZYW))
        channel = CHANNEL_SZYW
        print(err)

    #获取部门错误就设置为办公厅
    try:
        branch = request.GET.get('branch')
        if branch not in num_dfkx() and  branch not in num_kxjg() and branch not in num_xuehui():
            branch = BGT
    except Exception as err:
        print("获取部门出现错误，获取到的数据为：{0}，因此设为默认值:{1}".format(branch, BGT))
        branch = BGT
        print(err)

    #根据频道得到数据库表名
    db_table = ChannelToDatabase.objects.filter(channel=channel).values_list('database')
    #根据数据库表名获取到模型
    mymodels = table_to_models(db_table[0][0])

    #时政频道特殊处理一下,先获取到一条置顶的新闻
    if channel == CHANNEL_SZYW:
        result_list.extend(search_data_from_mysql(ChinaTopNews, n=1))


    #全国学会的用户在全国学会频道应该就只有他们自己的新闻，地方科协也一样
    if branch in num_xuehui() and channel == CHANNEL_QGXH:
        #根据部门ID取得部门名称
        department = accord_number_get_department(branch)
    elif branch in num_dfkx() and channel == CHANNEL_DFKX:
        department = accord_number_get_department(branch)
    else:
        department = None
    #将部门名称作为条件去查询，要不然就默认按照时间
    result_list.extend(search_data_from_mysql(mymodels, source=department))

    #如果新闻数量不够，就按照时间去取
    num_news= len(result_list)
    if num_news < MAX_NEWS_NUMBER:
        n = MAX_NEWS_NUMBER - num_news
        #现获取到信息的id
        id_list =[]
        for one_news in result_list:
            news_id = one_news['news_id']
            index = news_id.rindex("_")
            number = news_id[index + 1:]
            id_list.append(int(number))
        result_list.extend(search_data_from_mysql(mymodels,n=n,id_list=id_list))
    return HttpResponse(json.dumps(result_list, ensure_ascii=False))

#获取所有的频道
def get_all_channel():
    result_list =[]
    temp_list  =  ChannelToDatabase.objects.values_list('channel')
    for one in temp_list:
        result_list.append(one[0])
    return result_list

#按照条件数据，返回一个列表
def search_data_from_mysql(myModel,n = MAX_NEWS_NUMBER,**kw):
    result = []
    if "source" in kw:
        source = kw['source']
    else:
        source = ''
    if 'id_list' in kw:
        id_list = kw['id_list']
    else:
        id_list=[]
    if not source :
        try:
            data = myModel.objects.filter(hidden=1).exclude(id__in= id_list).values_list('id','title','img','time','source').order_by('-time')[:n]
            ChannelToDatabase.objects.exclude()
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
            data = None
            print(err)
    else:
        try:
            data = myModel.objects.filter(hidden=1).filter(source=source).values_list('id','title','img','time','source','comment','like').order_by('-time')[:n]
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
            data = None
            print(err)

    for one in data:
        temp_dict ={}
        news_id = str(myModel._meta.db_table) + '_' +str (one[0])
        temp_dict['news_id'] = news_id
        temp_dict['news_title'] = one[1]
        temp_dict['news_img']= one[2]
        temp_dict['news_time'] = one[3]
        temp_dict['source'] = one[4]
        temp_dict['comment'] = one[5]
        temp_dict['like'] = one[6]
        result.append(temp_dict)
    return result

#根据新闻id返回内容,并记录用户画像
def news_content(request):
    news_id = request.GET.get('news_id')
    index = news_id.rindex('_')
    db_table = news_id[:index]
    number = news_id[index+1:]
    #根据db_table获取到models
    mymodels = table_to_models(db_table)
    #查到数据
    contents = mymodels.objects.filter(id=number).values_list('content','like','comment','keywords')
    #保存结果
    result_dict = {}
    for one in contents:
        result_dict['content'] = one[0]
        result_dict['like'] = one[1]
        result_dict['comment'] = one[2]
        result_dict['keywords_list']= one[3]

    try:
        user_id = request.GET.get('user_id')
    except Exception as err:
        user_id = None
        print(err)

    # 找到user_id才进行用户画像
    if user_id:
        # 只有科技热点和时政新闻记录用户画像
        if db_table == 'news' or db_table == 'tech':
            #根据db_table获取到频道
            cur_channel = ChannelToDatabase.objects.filter(database=db_table).values_list('channel')[0][0]
        else:
            cur_channel =None
        if cur_channel:
                record_user_image(user_id, cur_channel,result_dict['keywords_list'].split(' '))
    #取出字典里的关键词列表
    result_dict.pop("keywords_list")
    return HttpResponse(json.dumps(result_dict, ensure_ascii=False))

def record_user_image(user_id, cur_channel,keywords_list):
    user = search_user_from_momgodb(id=user_id)
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
                print(xsy)
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
    update_mongo_accord_user_id(user_id,user['channelList'])

#返回相似的新闻列表
def similar_news_list(request):
    news_id = request.GET.get("news_id")
    data = similar_news(news_id)
    return HttpResponse(json.dumps(data,ensure_ascii=False))


def china_top_news(request):
    data = spider.china_top_news()
    china_top_news = ChinaTopNews(**data)
    try:
        china_top_news.save()
    except Exception as e:
        return HttpResponse('sava data  Failed:{0}'.format(e))
    return HttpResponse('sava data sucessful')



def save_org_into_mysql(request):
    try:
        initData.handle_organization()
    except Exception as e:
        return HttpResponse('sava data  Failed:{0}'.format(e))
    return HttpResponse('sava data sucessful')

def hanle_cast_into_mysql(request):
    try:
        handle_cast.sz_kj()
    except Exception as e:
        return HttpResponse('sava data  Failed:{0}'.format(e))
    return HttpResponse('sava data sucessful')





