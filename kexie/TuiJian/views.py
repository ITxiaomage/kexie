from django.shortcuts import render
from django.http import HttpResponse
from . import spider
from . import initData
from . import handle_cast
from .organiza import *
from .mongo import *
from .cal_similar_news import *
from datetime import datetime
from operator import itemgetter
import json
from simhash import Simhash
from django.db.models import Q

####################################定时任务#########################
from apscheduler.scheduler import Scheduler
sched = Scheduler()  # 实例化，固定格式


@sched.interval_schedule(hours=60)  # 装饰器，seconds=60意思为该函数为1分钟运行一次
def mytask():
    print('定时任务启动,时间为：{0}'.format(datetime.now().strftime("%Y-%m-%d")))
    # 中央新闻
    update_china_top_news()
    # 科协官网
    update_kexie_news_into_mysql()
    # cast数据库
    hanle_cast_into_mysql()
    # 人名网时政
    updata_get_rmw_news_data()
    # 人民网科技
    update_get_rmw_kj_data()
    print('定时任务结束,时间为：{0}'.format(datetime.now().strftime("%Y-%m-%d")))
sched.start()  # 启动该脚本

#开启定时任务
# try:
#     #实例化调度器
#     scheduler = BackgroundScheduler()
#     scheduler.add_jobstore(DjangoJobStore(),'default')
#     @register_job(scheduler,"interval",hours = 8)
#     def my_job():
#         print('定时任务启动,时间为：{0}'.format(datetime.datetime.now().strftime("%Y-%m-%d")))
#         # 中央新闻
#         update_china_top_news()
#         # 科协官网
#         update_kexie_news_into_mysql()
#         # cast数据库
#         hanle_cast_into_mysql()
#         # 人名网时政
#         updata_get_rmw_news_data()
#         # 人民网科技
#         update_get_rmw_kj_data()
#         print('定时任务结束,时间为：{0}'.format(datetime.datetime.now().strftime("%Y-%m-%d")))
#     register_events(scheduler)
#     scheduler.start()
# except Exception as err:
#     print(err)
#     scheduler.shutdown()


#########################根据用户id、department和用户记录返回新闻列表###############
def get_user_news_list(request):
    # 获取频道错误就设置第一个频道
    try:
        channel = request.GET.get('channel')
        if channel not in get_all_channel():
            channel = ChannelToDatabase.objects.all().values_list('channel')[0][0]
    except Exception as err:
        channel = ChannelToDatabase.objects.all().values_list('channel')[0][0]
        print("获取频道出现错误，因此设为默认值:{0}".format(channel))
        print(err)

    # 获取部门错误就设置为第一个部门
    try:
        branch = request.GET.get('branch')
        if branch not in num_dfkx() and branch not in num_kxjg() and branch not in num_xuehui():
            branch = AgencyJg.objects.all().values_list('department')[0][0]
    except Exception as err:
        branch = AgencyJg.objects.all().values_list('department')[0][0]
        print("获取部门出现错误，因此设为默认值:{0}".format(branch))
        print(err)

    # 获取用户id
    try:
        user_id = request.GET.get('user_id')
    except Exception as err:
        print("获取用户id出现错误")
        user_id = None
        print(err)
    # 获取用户department列表
    try:
        department = request.GET.get('department')
        if department:
            department = json.loads(department)
    except Exception as err:
        print("获取用户department列表出现错误")
        department = []
        print(err)

    # 有用户id就按照用户id推送，并进行用户画像记录
    if user_id:
        result_list = accord_user_id_get_news_list(user_id, department, channel)
    else:  # 没有用户id,就按照部门推送，不进行用户画像记录
        result_list = channel_branch(channel, branch)
    print(len(result_list))
    return HttpResponse(json.dumps(result_list, ensure_ascii=False))


# 根据用户id和department和channel获取到新闻推荐的列表
def accord_user_id_get_news_list(user_id, department, channel):
    # 在时政要闻和科技热点进行个性化推荐
    if channel == CHANNEL_SZYW or channel == CHANNEL_KJRD:
        result_list = individual(user_id, channel)
    # 中国科协
    elif channel == CHANNEL_ZGKX:
        result_list = search_kx_data_from_mysql()
    # 当前频道为全国学会，并且用户department有学会，就按照department，否则按时间检索
    elif channel == CHANNEL_QGXH:
        result_list = get_qgxh_news_list(department)

    # 当前频道为地方科协，并且用户department有地方科协，就就按照department，否则按时间检索
    elif channel == CHANNEL_DFKX:
        result_list = get_dfkx_news_list(department)
    else:
        result_list = []
    return result_list


# 个性化推荐算法
def individual(user_id, channel):
    result_list = []

    # 根据频道得到数据库表名
    db_table = ChannelToDatabase.objects.filter(channel=channel).values_list('database')
    # 根据数据库表名获取到模型
    mymodels = table_to_models(db_table[0][0])

    # 先检测用户是否存在，不存在就创建新的用户，按照时间返回新闻
    user = search_user_from_momgodb(id=user_id)
    # 如果没有此用户，则创建新的用户
    if not user:
        create_new_user_in_mongo(user_id=user_id)
        # 按时间返回新闻
        result_list.extend(search_data_from_mysql(mymodels, MAX_SEARCH_NEWS))
        return result_list
    # 有用户就根据用户画像检索新闻
    user_images_dict = get_user_images_accord_user_id_channel(user_id, channel)
    result_list.extend(get_news_list_accord_user_images(mymodels, user_images_dict))
    return result_list


# 根据用户画像返回一个新闻列表
def get_news_list_accord_user_images(mymodels, user_images_dict):
    """
    :param mymodels:模型类
    :param user_images_dict: 用户画像的字典
    :return: 新闻列表
    """
    result_list = []
    label_list = user_images_dict['labelList']
    if label_list:
        for one_label in label_list:
            label = one_label['label']
            score = one_label['score']
            # 计算label的词向量
            label_vec = cal_d2v(label)

            # 获取候选新闻列表，根据新闻id获取新闻详情，然后计算相似性
            first_news_list = search_data_from_mysql(mymodels, MAX_SEARCH_NEWS)
            for one_news in first_news_list:
                news_id = one_news['news_id']
                news_info = accord_news_id_get_content_list(news_id)
                news_keywords = news_info["keywords_list"]
                if not news_keywords:
                    continue
                news_keywords_vec = cal_d2v(news_keywords)
                # 相似性大于0.8以上就认为是同一篇文章，相似性小于0.2就认为相似性太低，就不需要了，找到最相似的前10篇文章
                similar_score = xiangsidu(news_keywords_vec, label_vec)
                if SIMILIAR > similar_score > MIN_SIMILIAR:
                    # 这里的规则为相似性*10 +score得分
                    news_score = similar_score * 10 + score
                    one_news['news_score'] = news_score
                    result_list.append(one_news)
    if result_list:
        # 先按优先级，然后按照时间排序，然后按照相似性排序
        second_result_list = sorted(result_list, key=itemgetter('priority', 'news_time', 'score'), reverse=True)
    else:
        second_result_list = []
    final_result_list =[]
    while True:
        # 在这里将结果利用simhash去重
        final_result_list.extend(simhash_remove_similar(second_result_list))
        #新闻数量不够就一直补充
        if len(final_result_list)  < MAX_NEWS_NUMBER:
            get_enough_news(final_result_list,mymodels)
        else:
            break
    return final_result_list


# simhash算法去重
def simhash_remove_similar(news_list):
    result_list= []
    #需要两两比较simhash值
    len_news_list = len(news_list)
    for i in range(len_news_list):
        news_i_id =  news_list[i]['news_id']
        news_i_news_content =  accord_news_id_get_content_list(news_i_id)['news_content']
        sim_hash1 = Simhash(news_i_news_content)
        for j in range(1,len_news_list):
            #已经被打过标记的不判断
            if 'del' in news_list[j]:
                continue
            news_j_id = news_list[j]['news_id']
            news_j_news_content = accord_news_id_get_content_list(news_j_id)['news_content']
            sim_hash2 = Simhash(news_j_news_content)
            #如果两个新闻的汉明距离小于 10 则按照顺序只保留一个
            if sim_hash1.distance(sim_hash2) <= SIMHASH_DISTINCT:
                #表示不要这个新闻了
                news_list[j]['del'] = 'yes'
    for news in news_list:
        if 'del' not in news:
            result_list.append(news)
    return result_list

# # 中国科协频道算法
# def get_zgkx_news_list():
#     # 找到mysql中科协领导人
#     kx_leaders_list = get_kx_leaders_from_mysql()
#     # 从数据库取出最新的数据
#     news_list = search_data_from_mysql(KX, MAX_SEARCH_NEWS)
#     # 如果取到的日期和当前的日期之间相差7天以上就删除
#     recent_news_list = diff_time(news_list)
#
#     # 检索出科协领导人的新闻，然后按照时间排序,得到第一次的新闻推荐列表
#     first_news_list = sort_kx_news(news_list=recent_news_list, keywords_list=kx_leaders_list)
#
#     # 科协领导人的新闻最多三条
#     if len(first_news_list) > 3:
#         first_news_list = first_news_list[:3]
#     else:
#         first_news_list = first_news_list
#     final_result_list = []
#     while True:
#         # 在这里将结果利用simhash去重
#         final_result_list.extend(simhash_remove_similar(first_news_list))
#         #新闻数量不够就一直补充
#         if len(final_result_list)  < MAX_NEWS_NUMBER:
#             get_enough_news(final_result_list,KX)
#         else:
#             break
#     return final_result_list



# 找出news_list中包含科协领导人的新闻，并返回
def sort_kx_news(news_list, keywords_list):
    result_list = []
    for one_news in news_list:
        news_id = one_news['news_id']
        # 根据新闻id获取到新闻的详情
        news_info_dict = accord_news_id_get_content_list(news_id)
        for name in keywords_list:
            title = news_info_dict['news_title']
            content = news_info_dict['news_content']
            if name in title or name in content:
                score = title.count(name) * 10 + content.count(name)
                one_news['news_score'] = score
                result_list.append(one_news)
    # 按照时间排序,然后按照得分排序
    final_result_list = sorted(result_list, key=itemgetter('priority', 'news_time', 'news_score'), reverse=True)
    return final_result_list


# 获取科协领导人
def get_kx_leaders_from_mysql():
    result_list = []
    try:
        data = KxLeaders.objects.filter(hidden=1).values_list('name')
    except Exception as err:
        data = None
        print("{0}数据库检索不到数据".format(KxLeaders._meta.db_table))
        print(err)
    if data:
        for one in data:
            result_list.append(one[0])
    return result_list


# 全国学会频道推荐算法
def get_qgxh_news_list(department):
    qgxh_dep_numben_list = num_xuehui()
    result_list = []
    # 找到用户兼职的所有全国学会单位，并根据这些单位去检索新闻。
    for one_dep in department:
        one_dep = str(one_dep)
        if one_dep in qgxh_dep_numben_list:
            source = accord_number_get_department(one_dep)
            result_list.extend(search_data_from_mysql(QGXH, source=source))
    # 如果result_list为空，说明用户没有在全国学会兼职，那么返回数据库最新的新闻
    if not result_list:
        result_list.extend(search_data_from_mysql(QGXH))
    final_result_list = sorted(result_list, key=itemgetter('priority', 'news_time'), reverse=True)
    while True:
        # 在这里将结果利用simhash去重
        final_result_list.extend(simhash_remove_similar(result_list))
        #新闻数量不够就一直补充
        if len(final_result_list)  < MAX_NEWS_NUMBER:
            get_enough_news(final_result_list,QGXH)
        else:
            final_result_list = final_result_list[:MAX_NEWS_NUMBER]
            break
    return final_result_list



# 地方科协频道推荐算法
def get_dfkx_news_list(department):
    dfkx_dep_numben_list = num_dfkx()
    result_list = []
    # 找到用户兼职的所有地方科协单位，并根据这些单位去检索新闻。
    for one_dep in department:
        one_dep = str(one_dep)
        if one_dep in dfkx_dep_numben_list:
            source = accord_number_get_department(one_dep)
            result_list.extend(search_data_from_mysql(DFKX, source=source))
    # 如果result_list为空，说明用户没有在地方科协兼职，那么返回数据库最新的新闻
    if not result_list:
        result_list.extend(search_data_from_mysql(DFKX))
    final_result_list = sorted(result_list, key=itemgetter('priority', 'news_time'), reverse=True)
    while True:
        # 在这里将结果利用simhash去重
        final_result_list.extend(simhash_remove_similar(result_list))
        #新闻数量不够就一直补充
        if len(final_result_list)  < MAX_NEWS_NUMBER:
            get_enough_news(final_result_list,DFKX)
        else:
            final_result_list = final_result_list[:MAX_NEWS_NUMBER]
            break
    return final_result_list


# 根据部门和频道获
def channel_branch(channel, branch):
    result_list = []
    # 根据频道得到数据库表名
    db_table = ChannelToDatabase.objects.filter(channel=channel).values_list('database')
    # 根据数据库表名获取到模型
    mymodels = table_to_models(db_table[0][0])

    # 时政频道特殊处理一下,先获取到一条置顶的新闻
    # if channel == CHANNEL_SZYW:
    #     result_list.extend(search_data_from_mysql(ChinaTopNews, n=1))

    #中国科协的频道单独推送
    # 如果是中国科协频道，那么必须由三部分组成：要闻、视频和通知
    if channel == CHANNEL_ZGKX:
        result_list.extend(search_kx_data_from_mysql())
        return  result_list
    # 全国学会的用户在全国学会频道应该就只有他们自己的新闻，地方科协也一样
    if branch in num_xuehui() and channel == CHANNEL_QGXH:
        # 根据部门ID取得部门名称
        department = accord_number_get_department(branch)
    elif branch in num_dfkx() and channel == CHANNEL_DFKX:
        department = accord_number_get_department(branch)
    else:
        department = None
    # 将部门名称作为条件去查询，要不然就默认按照时间
    result_list.extend(search_data_from_mysql(mymodels, n=MAX_SEARCH_NEWS, source=department))

    # 如果取到的日期和当前的日期之间相差7天以上就删除
    recent_news_list = diff_time(result_list)

    # 按照当前用户的id，检索用户的历史记录，将得到的新闻进行算法排序,得到第一次的新闻推荐列表
    sort_all_news(news_list=recent_news_list, branch=branch, channel=channel)

    # 检测新闻数量是否足够，如果不够就在补充到足够的数量,得到第二个新闻推荐列表
    get_enough_news(recent_news_list, mymodels)
    if len(recent_news_list) >= MAX_NEWS_NUMBER:
        final_result_list = recent_news_list[:MAX_NEWS_NUMBER]
    else:
        final_result_list = recent_news_list
    return final_result_list

#搜索科协的数据
def search_kx_data_from_mysql():
    result_list =[]
    #要闻五条search_data_from_mysql
    result_list.extend(search_data_from_mysql(myModel=KX,n=LIMIT_NEWS,label=KXTT))
    result_list.extend(search_data_from_mysql(myModel=KX, n=LIMIT_NEWS, label=KXYW))
    #就这十条数据，还剩按照领导人数据排个序吧
    kx_leaders_list = get_kx_leaders_from_mysql()
    first_news_list = sort_kx_news(news_list=result_list, keywords_list=kx_leaders_list)

    #标签统一为要闻
    for one_news in first_news_list:
        one_news['label'] = KXYW
    if len(first_news_list) > LIMIT_NEWS:
        result_list = first_news_list[:LIMIT_NEWS]
    else:
        result_list = first_news_list
    #通知五条
    result_list.extend(search_data_from_mysql(myModel=KX, n=LIMIT_NEWS, label=KXTZ))
    #视频五条
    result_list.extend(search_data_from_mysql(myModel=KX, n=LIMIT_NEWS, label=KXSP))
    # 按照时间检索找五张img字段不为空的数据,用于轮播图
    temp_list= search_data_from_mysql(myModel=KX, n=LIMIT_NEWS, LB = True)
    #标签统一为要闻
    for one_news in temp_list:
        one_news['label'] = LB
    result_list.extend(temp_list)
    return result_list

# 补充到足够数量的新闻
def get_enough_news(news_list, mymodels):
    while True:
        num_news = len(news_list)
        if num_news >= MAX_NEWS_NUMBER:
            break
        n = MAX_NEWS_NUMBER - num_news
        # 现获取到信息的id
        id_list = []
        for one_news in news_list:
            news_id = one_news['news_id']
            index = news_id.rindex("_")
            number = news_id[index + 1:]
            id_list.append(int(number))
        news_list.extend(search_data_from_mysql(mymodels, n=n, id__list=id_list))


# 刚开始过滤掉一周以前的新闻
def diff_time(news_list):
    result_list = []
    for one_news in news_list:
        news_time = one_news['news_time']
        try:
            diff = datetime.today().date() - datetime.strptime(news_time, '%Y-%m-%d').date()
            if diff.days < WEEK:
                result_list.append(one_news)
        except Exception as err:
            print(err)
    return result_list


# 按照规则排序
def sort_all_news(news_list, branch=None, channel=None, keywords_list=[]):
    return []


# 获取所有的频道
def get_all_channel():
    result_list = []
    temp_list = ChannelToDatabase.objects.values_list('channel')
    for one in temp_list:
        result_list.append(one[0])
    return result_list


# 按照条件数据，返回一个列表
def search_data_from_mysql(myModel, n=MAX_NEWS_NUMBER, source=None, id__list=[],label =None,LB = False):
    result = []
    data = None
    #先按照科协的label检索
    if label:
        try:
            data = myModel.objects.filter(hidden=1).filter(label = label).exclude(id__in=id__list).values_list('id', 'title', 'img', 'time',
                                                                                         'source', 'comment', 'like',
                                                                                         'priority','label').order_by('-time')[:n]
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
    elif LB:#找轮播图
        try:
            data = KX.objects.filter(~Q(img=None)).filter(~Q(img='')).values_list('id', 'title', 'img', 'time',
                                                                                         'source', 'comment', 'like',
                                                                                         'priority','label').order_by('-time')[:n]
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
    elif not source:
        try:
            data = myModel.objects.filter(hidden=1).exclude(id__in=id__list).values_list('id', 'title', 'img', 'time',
                                                                                         'source', 'comment', 'like',
                                                                                         'priority','label').order_by('-time')[:n]
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
    else:
        try:
            data = myModel.objects.filter(hidden=1).filter(source=source).values_list('id', 'title', 'img', 'time',
                                                                                      'source', 'comment', 'like',
                                                                                      'priority','label').order_by('-time')[:n]
        except Exception as err:
            print("{0}数据库检索不到数据".format(myModel._meta.db_table))
            print(err)
    if data:
        for one in data:
            temp_dict = {}
            news_id = str(myModel._meta.db_table) + '_' + str(one[0])
            temp_dict['news_id'] = news_id
            temp_dict['news_title'] = one[1]
            temp_dict['news_img'] = one[2]
            temp_dict['news_time'] = one[3]
            temp_dict['news_source'] = one[4]
            temp_dict['comment'] = one[5]
            temp_dict['like'] = one[6]
            temp_dict['priority'] = one[7]
            temp_dict['label'] = one[8]
            result.append(temp_dict)
    return result


####################################获取的中央领导人接口##################################################
def get_china_top_news(request):
    result_dict = {}
    try:
        chinaTopNews = ChinaTopNews.objects.all().order_by('-time')[0]
        result_dict['news_title'] = chinaTopNews.title
        result_dict['news_time'] = chinaTopNews.time
        result_dict['news_img'] = str(chinaTopNews.img)
        result_dict['news_source'] = chinaTopNews.source
        result_dict['news_id'] = str(ChinaTopNews._meta.db_table) + '_' + str(chinaTopNews.id)
    except Exception as err:
        print('读取置顶中央新闻失败')
        print(err)
    return HttpResponse(json.dumps(result_dict, ensure_ascii=False))


####################################新闻id返回新闻 内容，并记录用户画像###########################################
# 根据新闻id返回内容,并记录用户画像
def news_content(request):
    news_id = request.GET.get('news_id')
    try:
        user_id = request.GET.get('user_id')
    except Exception as err:
        user_id = None
        print(err)
    # 根据新闻id获取到新闻的详情
    news_info_dict = accord_news_id_get_content_list(news_id)

    # 找到user_id才进行用户画像
    if user_id:
        db_table, number = get_table_and_id(news_id)
        # 只有科技热点和时政新闻记录用户画像
        if db_table == News._meta.db_table or db_table == TECH._meta.db_table:
            # 根据db_table获取到频道
            cur_channel = ChannelToDatabase.objects.filter(database=db_table).values_list('channel')[0][0]
        else:
            cur_channel = None
        if cur_channel:
            record_user_image(user_id, cur_channel, news_info_dict['keywords_list'].split(' '))
    # 取出字典里的关键词列表
    news_info_dict.pop("keywords_list")
    return HttpResponse(json.dumps(news_info_dict, ensure_ascii=False))


# 根据新闻id,获取当前新闻的信息
def accord_news_id_get_content_list(news_id):
    db_table, number = get_table_and_id(news_id)
    # 根据db_table获取到models
    mymodels = table_to_models(db_table)
    # 查到数据
    contents = mymodels.objects.filter(id=number).values_list('content', 'like', 'comment', 'keywords', 'title')
    # 保存结果
    result_dict = {}
    for one in contents:
        result_dict['news_content'] = one[0]
        result_dict['like'] = one[1]
        result_dict['comment'] = one[2]
        result_dict['keywords_list'] = one[3]
        result_dict['news_title'] = one[4]
    return result_dict


# 根据新闻id获取到数据表和在表中的id
def get_table_and_id(news_id):
    index = news_id.rindex('_')
    db_table = news_id[:index]
    number = news_id[index + 1:]
    return db_table, number


# 记录用户画像
def record_user_image(user_id, cur_channel, keywords_list):
    # 根据id搜索到用户
    user = search_user_from_momgodb(id=user_id)
    # 更新用户的画像
    update_uesr_iamges_accord_keywords_channel(user, cur_channel, keywords_list)


####################################新闻id返回相似新闻的列表####################################
# 返回相似的新闻列表
def similar_news_list(request):
    news_id = request.GET.get("news_id")
    if news_id:
        data = similar_news(news_id)
        return HttpResponse(json.dumps(data, ensure_ascii=False))
    else:
        return HttpResponse('news_id错误')


####################################以下都是爬虫更新入库函数####################################


#######################置顶的时政新闻入库###################
def update_china_top_news():
    # 置顶的时政新闻
    try:
        data = spider.china_top_news()
        china_top_news = ChinaTopNews(**data)
    except Exception as err:
        print('获取置顶的时政新闻失败')
        china_top_news = None
        print(err)
    # 置顶时政新闻入库
    if china_top_news:
        try:
            china_top_news.save()
            print('Successful')
        except Exception as err:
            print('插入置顶的时政新闻失败')
            print(err)


####################################科协官网数据入库###################
def update_kexie_news_into_mysql():
    try:
        news_list = spider.update_kexie_news()
    except Exception as err:
        print('selenium获取科协官网失败')
        print(err)
        try:
            news_list = spider.get_kexie_news_data_list()
        except Exception as err:
            print('bs4获取科协官网失败')
            news_list = []
            print(err)
    if news_list:
        for one_news in news_list:
            kx = KX(**one_news)
            try:
                kx.save()
                print('Successful')
            except Exception as e:
                print(e)
    #return HttpResponse('成功')


####################################人民网时政数据更新入库函数###################
def updata_get_rmw_news_data():
    try:
        news_list = spider.get_rmw_news_data()
    except Exception as err:
        print('人民网时政数据错误')
        news_list = None
        print(err)
    if news_list:
        for one_news in news_list:
            news = News(**one_news)
            try:
                news.save()
                print('Successful')
            except Exception as e:
                print(e)
    #return HttpResponse('人民网时政新闻入库成功')
    #return render(request,'news.html',{'news_list':news_list})


####################################人民网科技数据更新入库函数###################
def update_get_rmw_kj_data():
    try:
        news_list = spider.get_rmw_kj_data()
    except Exception as err:
        print('人民网科技数据错误')
        news_list = None
        print(err)
    if news_list:
        for one_news in news_list:
            news = TECH(**one_news)
            try:
                news.save()
                print('Successful')
            except Exception as e:
                print(e)
    #return HttpResponse('人民网科技数据入库成功')


####################################清洗科协的cast数据库中的科技热点和时政要闻入库###########################
def hanle_cast_into_mysql():
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


####################################初始化相关函数###########################################

############初始化科协机关、事业单位、地方科协和全国学会的组织结构代码和名称###############
def save_org_into_mysql(request):
    try:
        initData.handle_organization()
    except Exception as e:
        return HttpResponse('初始化科协机构成功:{0}'.format(e))
    return HttpResponse('初始化科协机构成功')


# save_kexie_leader给mongodb插入一个样例
def save_leader(request):
    try:
        for name in kexie_leader.keys():
            kxLeader = KxLeaders(name=name)
            try:
                kxLeader.save()
            except Exception as e:
                print(e)
    except Exception as err:
        print('初始化科协领导')
        print(err)
    return HttpResponse('初始化科协领导成功')
