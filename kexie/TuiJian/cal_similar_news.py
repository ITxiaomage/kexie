# -*-coding:utf-8 -*-
# 根据新闻id推送相似的新闻列表
import gensim
import numpy as np
from operator import itemgetter
from .spider import TF_IDF
from .models import *


# 加载进训练好的模型

#model = gensim.models.Word2Vec.load(w2v_path_model)
model =''
def similar_news(news_id):
    result_list = []
    # 根据id确定数据表和新闻id
    index = news_id.rindex("_")
    table = news_id[:index]
    number = news_id[index + 1:]
    mymodels = table_to_models(table)
    #当前新闻的内容
    content = mymodels.objects.filter(id=number).values_list('content')
    cur_keywords =  TF_IDF(str(content),10)
    cur_vec = cal_d2v(cur_keywords)

    data = mymodels.objects.all().order_by('-time')[:100].values_list('id','time','source','title','img','content')
    for one_data in data:
        print(one_data)
        temp_keywords = TF_IDF(str(one_data[5]),10)
        temp_vec = cal_d2v(temp_keywords)
        score = xiangsidu(cur_vec, temp_vec)
        if score > 0.5:
            temp_dict = {}
            temp_dict['news_id'] = one_data[0]
            temp_dict['news_time'] = one_data[1]
            temp_dict['news_source'] = one_data[2]
            temp_dict['news_title'] = one_data[3]
            temp_dict['news_img'] = one_data[4]
            temp_dict['news_score'] = score
            result_list.append(temp_dict)

    # 按照相似度排序 ,只需要取前五个
    temp_list = sorted(result_list, key=itemgetter('news_score'), reverse=True)
    if len(temp_list) > 5:
        result_list = temp_list[:5]
    else:
        result_list = temp_list
    return result_list

#根据db_table获取模型名字
def table_to_models(db_table):
    #只能用这种方法了
    if News._meta.db_table == db_table:
        mymodels = News
    elif KX._meta.db_table == db_table:
        mymodels = KX
    elif DFKX._meta.db_table == db_table:
        mymodels = DFKX
    elif QGXH._meta.db_table == db_table:
        mymodels = QGXH
    elif TECH._meta.db_table == db_table:
        mymodels = TECH
    elif ChinaTopNews._meta.db_table == db_table:
        mymodels = ChinaTopNews
    return mymodels

def cal_d2v(words):
    '''
    :param words: 一个列表
    :return: 通过词向量，加权平均值求句子的向量
    '''
    sum_vec = []
    for word in words:
        try:
            word2vec = model[word]
            sum_vec.append(word2vec)
        except:
            continue
    if sum_vec != []:
        doc2vec = np.mean(sum_vec, axis=0)  # 计算每一列的均值
    else:
        doc2vec = ""
    return doc2vec


def cal_cos(a_vec, b_vec):
    '''
    :param a_vec:
    :param b_vec:
    :return: 计算两个输入向量直接的cosine similarity
    '''
    a_vec = np.array(a_vec)
    b_vec = np.array(b_vec)
    l1 = np.sqrt(a_vec.dot(a_vec))
    l2 = np.sqrt(b_vec.dot(b_vec))
    cos_sim = float(a_vec.dot(b_vec) / (l1 * l2))
    return cos_sim


# 传入两个向量·，计算两个向量的cos
def xiangsidu(a_text_d2v, b_text_d2v):
    if a_text_d2v == "" or b_text_d2v == "":
        return 0
    else:
        return cal_cos(a_text_d2v, b_text_d2v)
