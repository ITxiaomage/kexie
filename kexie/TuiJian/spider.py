from bs4 import BeautifulSoup,Comment
import requests
import lxml
import datetime
import time
import jieba
import jieba.analyse
import re
from .define import *

def china_top_news():
    result_dict = {}
    url = r'http://www.china.com.cn/'
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50"}
    try:
        r = requests.get(url=url, headers=headers)
        html = r.text.encode(r.encoding).decode()
        soup = BeautifulSoup(html, 'lxml')
    except:
        return result_dict

    try:
        news = soup.select('.topNews > div > h1 > a')[0]
        news_title = news.text
        news_url = news['href']
        news_time = time.strftime('%Y-%m-%d')
    except Exception as err:
        print(err)

    try:
        r = requests.get(url=news_url, headers=headers)
        html = r.text.encode(r.encoding).decode()
        soup = BeautifulSoup(html, 'lxml')
        content = soup.select('.main')
        # 如果不为空就取内容
        if content:
            content = content[0]
        else:  # 为空的时候就需要下面的
            content = soup.select('.articleBody')[0]

        # 图片
        imgs = content.findAll("img")
        img_list = []
        for one in imgs:
            img = one.attrs['src']
            if img.split('/')[-1] == '161021-02.jpg' or img.split('/')[-1] == '161021-03.jpg' or img.split('/')[
                -1] == 'logo.gif':
                continue
            else:
                img_list.append(img)
        if not img_list:
            img_list.append(IMG)

        try:
            # 去除文章中的注释
            comments = soup.findAll(text=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            # 把新闻的开始的视频处理了
            content.select("#videoarea")[0].extract()

            # 防止最后出现的app
            content.select(".app")[0].extract()
            content.select("embed")[0].extract()

        except Exception as err:
            print(err)
    except Exception as err:
        print(err)

    # 把文章中记者的信息处理了
    content = re.sub(r"[（](.*?)[）]", '', str(content))

    result_dict['title'] = news_title
    result_dict['url'] = news_url
    # 获取到一张图片
    result_dict['img'] = (img_list[0])
    result_dict['content'] = content
    result_dict['keywords'] = TF_IDF(content,MAX_KEYWORDS)
    result_dict['time'] = news_time
    result_dict['source'] = "中国网新闻中心"

    return result_dict


#前n个用户关键字列表，关键字列表给用给用户画像
def TF_IDF(content,n):
    con = ' ' .join(re.findall('\w+', content))
    temp_list = jieba.analyse.extract_tags(con,topK = 10,withWeight = False,allowPOS=('n','ns','nr','nt','nz','v','vn'))
    if len(temp_list) > n:
        result =temp_list[:n]
    else:
        result = temp_list
    return result
