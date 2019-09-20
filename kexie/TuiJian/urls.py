
from django.urls import path
from . import views,handle_cast


app_name = "TuiJian"
urlpatterns = [


    # 根据channel和branch返回数据
    path('get_similar_news_data', views.channel_branch, name="newsList"),

    # 根据新闻id获取新闻内容
    path('newsContent', views.news_content,name = "newsContent"),

    # 根据新闻id获取相似新闻列表
    path('similarNews', views.similar_news_list, name="similarNews"),


    # 更新置顶的中央新闻数据库
    path('ctn', views.china_top_news, name="ctn"),

]
