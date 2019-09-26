
#默认的中央领导人照片
IMG = 'http://paper.people.com.cn/rmrb/res/1/20190904/1567536994561_1.jpg'

#训练好的词向量模型路径
w2v_path_model ='E:\推荐相关\model/w2v.model'
#w2v_path_model ='/home/BH_TuiJian/kexie/w2v.model'
#存放科协机构的文件路径
jiggou_path = r'E:\推荐相关\机构.xls'
#jiggou_path = r'/home/BH_TuiJian/kexie/机构.xls'

#每篇文章提取的关键字最大数，用户设置用户画像
MAX_KEYWORDS = 5

#提取的新闻的最大数量
MAX_NEWS_NUMBER = 10
#去数据库检索数据的最大值
MSX_SEARCH_NEWS= 1000
#定义一周的时间
WEEK= 7

#模型名字和数据库的设计
models_to_db_table = {"news":"News","kx":"KX","dfkx":"DFKX","qgxh":"QGXH","tech":"TECH","chinaTopNews":"ChinaTopNews"}
#定义全国学会频道
CHANNEL_QGXH='全国学会'
#定义地方科协频道
CHANNEL_DFKX='地方科协'

#定义时政要闻频道
CHANNEL_SZYW='时政要闻'

#科协头条
KXTT='头条'
#科协要闻
KXYW='要闻'
#科协通知
KXTZ='通知'

#定义办公厅ID
BGT= '2000000309'

#定义mongodb的数据库
MONGODB_DB = 'kexie'
#定义mongodb上的用户画像collection
USER_IMAGE = 'user_image'
#定义机构画像
ORG_IMAMGE= 'org_image'

#定义用户画像中相似度的值
SIMILIAR = 0.8
#用户画像分数初始值
INIT_SCORE = 50
