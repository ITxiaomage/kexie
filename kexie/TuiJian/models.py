from django.db import models
#最大最小值验证器
from django.core.validators import MaxValueValidator,MinValueValidator

# Create your models here.
class NewsBase(models.Model):
    title = models.CharField(max_length=255,null=False,unique=True)
    url = models.CharField(max_length=255,null=True)
    img =  models.CharField(max_length=255,null=True)
    content = models.TextField(null=False)
    author = models.CharField(max_length=255,null=True)
    keywords = models.CharField(max_length=255,null=True)
    time = models.CharField(max_length=255,null=True)
    source = models.CharField(max_length=255,null=True)
    #标签，科协下分的：智库、学术、科普、党建。还有单独表明的ring
    label = models.CharField(max_length=255,null=True)
    comment = models.IntegerField(default= 0)
    like = models.IntegerField(default=0)
    #限制人工干预优先级的最大值是10，最小值是0
    priority =  models.IntegerField(default= 0,validators=[MaxValueValidator(10),MinValueValidator(0)])
    #屏蔽新闻的标志,默认不屏蔽设置为1，屏蔽就设置为0
    hidden = models.BooleanField(default= True)
    #今天推送的新闻的排序，值越大，新闻的优先级越高
    today = models.IntegerField(default= 0,validators=[MaxValueValidator(100),MinValueValidator(0)])
    class Meta:
        managed =True
        abstract = True

class News(NewsBase):
    class Meta:
        db_table = "news"
        verbose_name = "时政要闻"
        verbose_name_plural = "时政要闻"

class KX(NewsBase):
    class Meta:
        db_table = "kx"
        verbose_name = "中国科协"
        verbose_name_plural = "中国科协"

class DFKX(NewsBase):
    class Meta:
        db_table = "dfkx"
        verbose_name = "地方科协"
        verbose_name_plural = "地方科协"

class QGXH(NewsBase):
    class Meta:
        db_table = "qgxh"
        verbose_name = "全国学会"
        verbose_name_plural = "全国学会"
class TECH(NewsBase):
    class Meta:
        db_table = "tech"
        verbose_name = "科技热点"
        verbose_name_plural = "科技热点"

class ChinaTopNews(NewsBase):
    class Meta:
        db_table = "chinaTopNews"
        verbose_name = "中央领导人新闻"
        verbose_name_plural = "中央领导人新闻"

class AgencyBase(models.Model):
    number = models.CharField(max_length=255,null= False,unique=True)
    department = models.CharField(max_length=255, null=False, unique=True)
    index = models.CharField(max_length=255)
    #当前部门是否可用，可用为1，不可用为0
    hidden = models.BooleanField(default= True)
    class Meta:
        abstract = True


class AgencyJg(AgencyBase):
    class Meta:
        db_table = 'agency_jg'
        verbose_name = "科协机关及事业单位"
        verbose_name_plural = "科协机关及事业单位"

class AgencyDfkx(AgencyBase):
    class Meta:
        db_table = 'agency_dfkx'
        verbose_name = "地方科协"
        verbose_name_plural = "地方科协"


class AgencyQgxh(AgencyBase):
    class Meta:
        db_table = 'agency_qgxh'
        verbose_name = "全国学会"
        verbose_name_plural = "全国学会"


class ChannelToDatabase(models.Model):
    channel = models.CharField(max_length=255,unique=True,null=False)
    database =  models.CharField(max_length=255,unique=True,null=False)
    class Meta:
        db_table = 'channelToDatabase'
        verbose_name = "频道和数据库的映射"
        verbose_name_plural = "频道和数据库的映射"


