from apscheduler.scheduler import Scheduler
from . import views
sched = Scheduler()

@sched.interval_schedule(hours=10)
def my_task1():
    print('定时任务启动')
    #中央新闻
    views.update_china_top_news()
    #科协官网
    views.update_kexie_news_into_mysql()
    #cast数据库
    views.hanle_cast_into_mysql()
    #人名网时政
    views.updata_get_rmw_news_data()
    #人民网科技
    views.update_get_rmw_kj_data()
    print('定时任务结束')


