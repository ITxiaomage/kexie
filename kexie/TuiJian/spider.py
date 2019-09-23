from bs4 import BeautifulSoup,Comment
import lxml
import datetime
import time
import jieba
import jieba.analyse
import re
import json
import time
import requests
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui  import WebDriverWait

from .define import *
img_list =[]
#################################人民网时政新闻爬虫##################################################
def get_rmw_news_data(url=r'http://www.people.com.cn/rss/rect_default.json',base_url = r'http://politics.people.com.cn'):
    data_json= requests.get(url=url).text
    data_dict = json.loads(data_json)
    news_list=data_dict['otherNews']
    result_list = []
    for one_news in news_list:
        try:
            content ,time,img,source = get_rmw_content_time_img(one_news['newsLink'],base_url)
            result_list.append(package_data_dict(title=one_news['title'],url=one_news['newsLink'],content=str(content),date=time,img=img,source=source))
        except Exception as err:
            print('爬取人民网时政新闻出错{0}'.format(one_news))
            print(err)
    return result_list

def get_rmw_content_time_img(news_url,base_url):
    print(news_url)
    soup = rm_spider_head(news_url)
    try:
        news_content = soup.select('#rwb_zw')[0]
        news_time_source = soup.select('.box01 > div')[0].text
        news_time = news_time_source.split(' ')[0]
        year,month,day = news_time[:4],news_time[5:7],news_time[8:10]
        news_time =  year+'_'+ month+'_'+ day
        news_source = news_time_source.split(' ')[-1].split('：')[-1]
        imgs = news_content.findAll('img')
        img = deal_imgs_and_a(base_url, content=news_content, imgs=imgs)
    except:
        try:
            news_content = soup.select('#picG')[0]
            news_time_source = soup.select('.page_c')[1].text
            news_source = news_time_source.split(' ')[0].split('：')[-1]
            news_time = news_time_source.split(' ')[-1]
            year,month,day = news_time[:4],news_time[5:7],news_time[8:10]
            news_time =  year+'_'+ month+'_'+ day
            img = ''
        except:
            news_content = ''
            news_time =''
            news_source=''
            img =''
    return news_content ,news_time,img,news_source

def rm_spider_head(url):
    headers = {"User_Agent": "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11"}
    try:
        response = requests.get(url=url, headers=headers)
        response.encoding=response.apparent_encoding
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception as err:
        print('rm_spider_head出错')
        soup = None
    return soup
##################################科协官网用selenium爬取##############################################
def update_kexie_news():
    result_list =[]
    try:
        browser = init_chrome()
        tt_url = r'http://www.cast.org.cn/col/col79/index.html'
        yw_url = r'http://www.cast.org.cn/col/col80/index.html'
        tzgc_url = r'http://www.cast.org.cn/col/col457/index.html'
        base_url = r'http://www.cast.org.cn'
        try:
            #头条
            result_list.extend(get_kx_data(browser, tt_url, base_url,KXTT))
        except Exception as err:
            print('头条新闻出错')
            print(err)
        try:
            #要闻
            result_list.extend(get_kx_data(browser, yw_url, base_url,KXYW))
        except Exception as err:
            print('要闻出错')
            print(err)
        try:
            #通知
            result_list.extend(get_kx_data(browser, tzgc_url, base_url,KXTZ))
        except Exception as err:
            print('通知出错')
            print(err)
            pass
    except Exception as err:
        print('爬取科协新闻出错')
        print(err)
    finally:
        browser.quit()
        return result_list

def init_chrome():
    #创建对象
    option = webdriver.ChromeOptions()
    option.add_argument('--no-sandbox')
    #headless就是谷歌的无头模式
    option.add_argument('--headless')
    #这里是禁用了GPU，谷歌浏览器GPU加速在虚拟机上可能导致黑屏
    option.add_argument('--disable-gpu')
    #传入最终的参数就行了
    browser = webdriver.Chrome(options = option )
    return browser

def get_kx_data(browser, url,base_url,label):
    print('进入官网。。。')
    try:
        # 进入科协官网新闻
        browser.get(url)
        time.sleep(1)
        # 获取列表
        info_list = browser.find_elements_by_xpath('//div[@class="bt-mod-wzpb-02"]/ul/li')
        info_list_len = len(info_list) + 1
    except:
        info_list_len =0
        print('进入科协官网出错。。。')

    # 存放结果的列表
    temp_list = []
    if info_list_len :
        print(info_list_len)
        for i in range(1, info_list_len):
            news_url = browser.find_element_by_xpath('//div[@class="bt-mod-wzpb-02"]/ul/li[{0}]//p/a'.format(i)).get_attribute('href')
            title = browser.find_element_by_xpath('//div[@class="bt-mod-wzpb-02"]/ul/li[{0}]//p'.format(i)).text
            day = browser.find_element_by_xpath('//div[@class="bt-mod-wzpb-02"]/ul/li[{0}]//h2'.format(i)).text
            year_month = browser.find_element_by_xpath('//div[@class="bt-mod-wzpb-02"]/ul/li[{0}]//h5'.format(i)).text
            news_time = year_month.split('/')[0] + '-' + year_month.split('/')[1] + '-' + day
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50"}
            # 获取新闻文本
            r = requests.get(url=news_url, headers=headers)
            r.encoding =  r.apparent_encoding
            soup = BeautifulSoup(r.text, 'lxml')
            content = soup.select('#zoom')[0]
            imgs = content.findAll('img')
            img_path = deal_imgs_and_a(base_url, content=content, imgs=imgs)
            print(i,title)
            temp_list.append(package_data_dict(title=title, url=news_url, img =img_path,content=str(content), date=news_time, source="中国科协",label = label))
    return temp_list

#########################3###########科协官网用bs4爬取#############################################################

def get_kexie_news_data_list():
    result_list = []
    tt_url = r'http://www.cast.org.cn/col/col79/index.html'
    yw_url = r'http://www.cast.org.cn/col/col80/index.html'
    tzgc_url = r'http://www.cast.org.cn/col/col457/index.html'
    base_url = r'http://www.cast.org.cn'
    result_list.extend(get_kx_news_list(tt_url, base_url))
    result_list.extend(get_kx_news_list(yw_url, base_url))
    result_list.extend(get_kx_news_list(tzgc_url, base_url))
    return result_list

def spider_head(url):
    headers = {"User_Agent": "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11"}
    try:
        response = requests.get(url=url, headers=headers)
        html = response.text.encode(response.encoding).decode()
        soup = BeautifulSoup(html, 'lxml')
    except Exception as err:
        print('spider_head出错')
        soup = None
    return soup


def get_content_time_img(news_url, base_url):
    soup = spider_head(news_url)
    content = soup.select('#zoom')[0]
    del content['style']
    news_time = soup.select('.time > span')[0]
    news_time.select('style')[0].extract()
    news_time = news_time.text.split('：')[1]
    imgs = content.findAll('img')
    img_path = deal_imgs_and_a(base_url, imgs=imgs)
    return news_time, img_path, content

def get_kx_news_list(url, base_url):
    result_list = []
    soup = spider_head(url=url)
    regx = re.compile(r'\<\!\[CDATA\[(.*?)\]\]\>', re.DOTALL)
    re_result = re.findall(regx, soup.text.strip())
    replace_list = [e.strip().replace('\t', '') for e in re_result]
    repalce_list_len = len(replace_list)
    for i in range(1, repalce_list_len):
        temp_dict = {}
        one_news_soup = BeautifulSoup(replace_list[i], 'lxml')
        news_url = base_url + one_news_soup.select('.list-title-bif > a')[0]['href']
        title = one_news_soup.select('.list-title > p')[0].text
        news_time, news_img, news_content = get_content_time_img(news_url, base_url)
        temp_content = news_content
        temp_dict['title'] = title
        temp_dict['url'] = news_url
        temp_dict['content'] = str(news_content)
        temp_dict['img'] = news_img
        temp_dict['time'] = news_time
        temp_dict['author'] = ' '
        temp_dict['keywords'] = ' '.join(TF_IDF(temp_content.text))
        temp_dict['source'] = '中国科协'
        result_list.append(temp_dict)
    return result_list

#处理图片链接和文件链接
def deal_imgs_and_a(base_url,content =None,imgs=None):
    img_path = ''
    if imgs:
        for img in imgs:
            img_path = img['src']
            if img_path[0] == '/':
                img_path = base_url + img_path
                img['src'] = img_path
        img_path =imgs[0]['src']
    try:
        a_hrefs = content.findAll('a')
    except Exception as err:
        print('文章中没有a链接')
        a_hrefs = None
    if a_hrefs:
        for a_href in a_hrefs:
            try:
                old_href = a_href['href']
            except Exception as err:
                print('a标签没有href属性')
                print(err)
                continue
            if old_href[0] == '/':
                new_href = base_url + old_href
                a_href['href'] = new_href
    return img_path

#########################3###########爬取每天的置顶时政新闻，来自与中国网#############################################################
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
        try:
            content = soup.select('.main')[0]
        except Exception as err:
            print('第一次失败')
            print(err)
            try:
                content = soup.select('.articleBody')[0]
            except Exception as err:
                print('第二次获取失败')
                print(err)
                try:
                    content = soup.select('.artiContent')[0]
                    img_list.append(IMG)
                except Exception as err:
                    print('第三次获取失败')
                    print(err)

        try:
            # 去除文章中的注释
            comments = soup.findAll(text=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            try:
                # 把新闻的开始的视频处理了
                content.select("#videoarea")[0].extract()
            except:
                pass
            try:
                # 防止最后出现的app
                content.select(".app")[0].extract()
            except:
                pass

            try:
                content.select("embed")[0].extract()
            except:
                pass
        except Exception as err:
            print(err)
    except Exception as err:
        print(err)

        # 图片
    imgs = content.findAll("img")
    if not img_list:
        for one in imgs:
            img = one.attrs['src']
            if img.split('/')[-1] == '161021-02.jpg' or img.split('/')[-1] == '161021-03.jpg' or img.split('/')[
                -1] == 'logo.gif':
                continue
            else:
                img_list.append(img)
        if not img_list:
            img_list.append(IMG)

    # 把文章中记者的信息处理了
    content = re.sub(r"[（](.*?)[）]", '', str(content))

    result_dict['title'] = news_title
    result_dict['url'] = news_url
    # 获取到一张图片
    result_dict['img'] = img_list[0]
    result_dict['content'] = content
    result_dict['time'] = news_time

    return result_dict
####################################新闻TF_IDF的提取#############################################################
#前n个用户关键字列表，关键字列表给用给用户画像
def TF_IDF(content,n = 3):
    con = ' ' .join(re.findall('\w+', content))
    temp_list = jieba.analyse.extract_tags(con,topK = 10,withWeight = False,allowPOS=('n','ns','nr','nt','nz','v','vn'))
    if len(temp_list) > n:
        result =temp_list[:n]
    else:
        result = temp_list
    return result
####################################将新闻相关信息打包为一个字典#############################################################
def package_data_dict(title=None, url=None, img =None,content=None, date=None, source=None,label =None):
    temp_dict = {}
    keywords = TF_IDF(content,MAX_KEYWORDS)
    if len(keywords) > 4:
        temp_dict['title'] = title
        temp_dict['url'] = url
        temp_dict['content'] = content
        temp_dict['img'] = img
        temp_dict['time'] = date
        temp_dict['author'] = ''
        temp_dict['label'] = label
        temp_dict['keywords'] = ' '.join(keywords)
        temp_dict['source'] = source
    return temp_dict


