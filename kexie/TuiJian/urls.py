
from django.urls import path
from . import views,handle_cast


app_name = "TuiJian"
urlpatterns = [


    # 根据channel和branch返回数据
    path('get_news_list', views.channel_branch, name="newsList"),

    # 根据新闻id获取新闻内容
    path('newsContent', views.news_content,name = "newsContent"),

    # 根据新闻id获取相似新闻列表
    path('similarNews', views.similar_news_list, name="similarNews"),

    #获取置顶的中央领导人接口
    path('china', views.get_china_top_news, name="chinaTopNews"),


    # 更新置顶的中央新闻入库
    path('ctn', views.update_china_top_news, name="ctn"),

    #科协官网数据库入库
    path('kx', views.update_kexie_news_into_mysql, name="kx"),

    #清洗cast数据库入库
    path('cast', views.hanle_cast_into_mysql, name="cast"),

    # 人民网时政数据
    path('rmwsz', views.updata_get_rmw_news_data, name="rmw_sz"),

    # 人民网科技数据
    path('rmwkj', views.update_get_rmw_kj_data, name="rmw_kj"),

    ############初始化的函数，只需要执行一次##########
    #初始化组织机构
    path('org', views.save_org_into_mysql, name="org"),
    #科协领导
    path('leader', views.save_leader, name="leader"),





]
