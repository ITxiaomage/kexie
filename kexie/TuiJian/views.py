from django.shortcuts import render
from django.http import HttpResponse
from . import spider
from .models import *
from . import initData
from . import  handle_cast
import json
from .define import *
from .organiza import *
from .mongo import *
from .cal_similar_news import  *
from datetime import datetime



####################################根据部门和频道获取到推荐的新闻##################################################
#根据部门和频道获
def channel_branch(request):
    result_list= []
    #获取频道错误就设置为时政要闻
    try:
        channel =  request.GET.get('channel')
        if channel not in get_all_channel():
            channel = CHANNEL_SZYW
    except Exception as err:
        print("获取频道出现错误，因此设为默认值:{0}".format(CHANNEL_SZYW))
        channel = CHANNEL_SZYW
        print(err)

    #获取部门错误就设置为办公厅
    try:
        branch = request.GET.get('branch')
        if branch not in num_dfkx() and  branch not in num_kxjg() and branch not in num_xuehui():
            branch = BGT
    except Exception as err:
        print("获取部门出现错误，因此设为默认值:{0}".format(BGT))
        branch = BGT
        print(err)

    #根据频道得到数据库表名
    db_table = ChannelToDatabase.objects.filter(channel=channel).values_list('database')
    #根据数据库表名获取到模型
    mymodels = table_to_models(db_table[0][0])

    #时政频道特殊处理一下,先获取到一条置顶的新闻
    # if channel == CHANNEL_SZYW:
    #     result_list.extend(search_data_from_mysql(ChinaTopNews, n=1))
    #全国学会的用户在全国学会频道应该就只有他们自己的新闻，地方科协也一样
    if branch in num_xuehui() and channel == CHANNEL_QGXH:
        #根据部门ID取得部门名称
        department = accord_number_get_department(branch)
    elif branch in num_dfkx() and channel == CHANNEL_DFKX:
        department = accord_number_get_department(branch)
    else:
        department = None
    #将部门名称作为条件去查询，要不然就默认按照时间
    result_list.extend(search_data_from_mysql(mymodels, n= MSX_SEARCH_NEWS,source=department))

    #如果取到的日期和当前的日期之间相差7天以上就删除
    recent_news_list = diff_time(result_list)

    #按照当前用户的id，检索用户的历史记录，将得到的新闻进行算法排序,得到第一次的新闻推荐列表
    first_news_list = sort_all_news(recent_news_list,branch,channel)

    #检测新闻数量是否足够，如果不够就在补充到足够的数量
    get_enough_news(first_news_list,mymodels)

    return HttpResponse(json.dumps(first_news_list, ensure_ascii=False))


#补充到足够数量的新闻
def get_enough_news(first_news_list,mymodels):
    while(True):
        num_news = len(first_news_list)
        if num_news >= MAX_NEWS_NUMBER:
            break
        n = MAX_NEWS_NUMBER - num_news
        #现获取到信息的id
        id_list =[]
        for one_news in first_news_list:
            news_id = one_news['news_id']
            index = news_id.rindex("_")
            number = news_id[index + 1:]
            id_list.append(int(number))
        first_news_list.extend(search_data_from_mysql(mymodels,n=n,id__list=id_list))


#刚开始过滤掉一周以前的新闻
def diff_time(news_list):
    result_list = []
    for one_news in news_list:
        news_time = one_news['news_time']
        try:
            diff = datetime.today().date() - datetime.strptime(news_time, '%Y-%m-%d').date()
            if diff.days < WEEK:
                result_list.append(one_news)
        except:
            pass
    return result_list

#按照关键字进行排序，先检索和科协领导相关的
def sort_all_news(news_list,branch,channel):
    return []



#获取所有的频道
def get_all_channel():
    result_list =[]
    temp_list  =  ChannelToDatabase.objects.values_list('channel')
    for one in temp_list:
        result_list.append(one[0])
    return result_list

#按照条件数据，返回一个列表
def search_data_from_mysql(myModel,n = MAX_NEWS_NUMBER,source = None,id__list=[]):
    result = []
    data = None
    if  source :
        try:
            data = myModel.objects.filter(hidden=1).exclude(id__in= id__list).values_list('id','title','img','time','source','comment','like').order_by('-time')[:n]
            ChannelToDatabase.objects.exclude()
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
    else:
        try:
            data = myModel.objects.filter(hidden=1).filter(source=source).values_list('id','title','img','time','source','comment','like').order_by('-time')[:n]
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
    if data:
        for one in data:
            temp_dict ={}
            news_id = str(myModel._meta.db_table) + '_' +str (one[0])
            temp_dict['news_id'] = news_id
            temp_dict['news_title'] = one[1]
            temp_dict['news_img']= str(one[2])
            temp_dict['news_time'] = one[3]
            temp_dict['source'] = one[4]
            temp_dict['comment'] = one[5]
            temp_dict['like'] = one[6]
            result.append(temp_dict)
    return result
####################################获取的中央领导人接口##################################################
def get_china_top_news(request):
    result_dict ={}
    try:
        chinaTopNews =  ChinaTopNews.objects.all().order_by('-time')[0]
        result_dict['title'] = chinaTopNews.title
        result_dict['time'] = chinaTopNews.time
        result_dict['img'] = str(chinaTopNews.img)
        result_dict['source'] = chinaTopNews.source
        result_dict['news_id'] = str(ChinaTopNews._meta.db_table) + '_'+ str(chinaTopNews.id)
    except Exception as err:
        print('读取置顶中央新闻失败')
        print(err)
    return HttpResponse(json.dumps(result_dict, ensure_ascii=False))


####################################新闻id返回新闻 内容，并记录用户画像###########################################
#根据新闻id返回内容,并记录用户画像
def news_content(request):
    news_id = request.GET.get('news_id')
    try:
        user_id = request.GET.get('user_id')
    except Exception as err:
        user_id = None
        print(err)
    #根据新闻id获取到新闻的详情
    news_info_list = accord_news_id_get_content_list(news_id)

    # 找到user_id才进行用户画像
    if user_id:
        db_table, number = get_table_and_id(news_id)
        # 只有科技热点和时政新闻记录用户画像
        if db_table == 'news' or db_table == 'tech':
            #根据db_table获取到频道
            cur_channel = ChannelToDatabase.objects.filter(database=db_table).values_list('channel')[0][0]
        else:
            cur_channel =None
        if cur_channel:
                record_user_image(user_id,cur_channel,news_info_list['keywords_list'].split(' '))
    #取出字典里的关键词列表
    news_info_list.pop("keywords_list")
    return HttpResponse(json.dumps(news_info_list, ensure_ascii=False))

#根据新闻id,获取当前新闻的信息
def accord_news_id_get_content_list(news_id):
    db_table, number = get_table_and_id(news_id)
    #根据db_table获取到models
    mymodels = table_to_models(db_table)
    #查到数据
    contents = mymodels.objects.filter(id=number).values_list('content','like','comment','keywords','title')
    #保存结果
    result_dict = {}
    for one in contents:
        result_dict['content'] = one[0]
        result_dict['like'] = one[1]
        result_dict['comment'] = one[2]
        result_dict['keywords_list']= one[3]
        result_dict['title'] = one[4]
    return result_dict

#根据新闻id获取到数据表和在表中的id
def get_table_and_id(news_id):
    index = news_id.rindex('_')
    db_table = news_id[:index]
    number = news_id[index+1:]
    return db_table,number

#记录用户画像
def record_user_image(user_id,cur_channel,keywords_list):
    #先检查mongondb中是否有该用户
    user = search_user_from_momgodb(id=user_id)
    #如果没有此用户，则创建新的用户
    if not user:
        create_new_user_in_mongo(user_id,cur_channel,keywords_list)
        return
    #如果有用户，则更新用户的画像记录
    update_uesr_iamges_accord_keywords_channel(user,cur_channel,keywords_list)

####################################新闻id返回相似新闻的列表####################################
#返回相似的新闻列表
def similar_news_list(request):
    news_id = request.GET.get("news_id")
    if news_id:
        data = similar_news(news_id)
        return HttpResponse(json.dumps(data,ensure_ascii=False))
    else:
        return HttpResponse('news_id错误')

####################################以下都是爬虫更新入库函数####################################


#######################置顶的时政新闻入库###################
def update_china_top_news(request):
    #置顶的时政新闻
    try:
        data = spider.china_top_news()
        china_top_news = ChinaTopNews(**data)
    except Exception as  err:
        print('获取置顶的时政新闻失败')
        china_top_news = None
        print(err)
    #置顶时政新闻入库
    if china_top_news:
        try:
            china_top_news.save()
        except Exception as err:
            print('插入置顶的时政新闻失败')
            print(err)
    return HttpResponse('置顶的时政新闻入库成功')


####################################科协官网数据入库###################
def update_kexie_news_into_mysql(request):
    try :
        news_list =spider.update_kexie_news()
    except Exception as err:
        print('selenium获取科协官网失败')
        print(err)
        try:
            news_list  = spider.get_kexie_news_data_list()
        except Exception as err:
                print('bs4获取科协官网失败')
                news_list = []
                print(err)
    if news_list:
        for one_news in news_list:
            kx =  KX(**one_news)
            try:
                kx.save()
            except Exception as e:
                print(e)
    #return render(request,'news.html',{'news_list':news_list})
    return HttpResponse('科协官网新闻入库成功')

####################################人民网时政数据更新入库函数###################
def updata_get_rmw_news_data(request):
    try:
        news_list = spider.get_rmw_news_data()
    except Exception as err:
        print('人民网时政数据错误')
        news_list =None
        print(err)
    if news_list:
        for one_news in news_list:
            news=  News(**one_news)
            try:
                news.save()
            except Exception as e:
                print(e)
    #return  HttpResponse('人民网时政新闻入库成功')
    return render(request,'news.html',{'news_list':news_list})
####################################人民网科技数据更新入库函数###################
def update_get_rmw_kj_data(requsts):
    try:
        news_list = spider.get_rmw_kj_data()
    except Exception as err:
        print('人民网科技数据错误')
        news_list =None
        print(err)
    if news_list:
        for one_news in news_list:
            news=  TECH(**one_news)
            try:
                news.save()
            except Exception as e:
                print(e)
    return  HttpResponse('人民网科技数据入库成功')
####################################清洗科协的cast数据库中的科技热点和时政要闻入库###########################
def hanle_cast_into_mysql(request):
    try:
        handle_cast.start()
    except Exception as err:
        print('清洗cast数据库入库出错')
        print(err)
    try:
        handle_cast.sz_kj()
    except Exception as e:
        print("时政和科技热点数据入库出错")
        print(e)
    return HttpResponse('cast数据库清洗入库成功')

####################################初始化相关函数###########################################

############初始化科协机关、事业单位、地方科协和全国学会的组织结构代码和名称###############
def save_org_into_mysql(request):
    try:
        initData.handle_organization()
    except Exception as e:
        return HttpResponse('初始化科协机构成功:{0}'.format(e))
    return HttpResponse('初始化科协机构成功')
#save_kexie_leader给mongodb插入一个样例
def save_leader(request):
    try:
        save_kexie_leader()
    except Exception as err:
        print('初始化科协领导')
        print(err)
    return HttpResponse('初始化科协领导成功')







