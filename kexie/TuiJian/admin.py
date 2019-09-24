from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import  *

# Register your models here.


class OrgBaseClass(admin.ModelAdmin):
    # 显示的字段
    list_display = ['number', 'department']
    #每页显示的数量
    list_per_page = 50
    list_display_links = ['number', 'department']
    #操作选项
    actions_on_top = True
    #过滤器
    #list_filter = ['number', 'department']
    #搜索器
    search_fields = ['number', 'department']
    #显示
    fields = ['number', 'department']
    #排序
    ordering = ('id',)
    #设置不可编辑字段，指进入详情也不可编辑
    def get_readonly_fields(self, request, obj=None):
        """  重新定义此函数，限制普通用户所能修改的字段  """
        if request.user.is_superuser:
            self.readonly_fields = []
        return self.readonly_fields

    readonly_fields = ('number', 'department')

class  NewsBaseClass ( admin.ModelAdmin ) :
    #设置不可编辑字段，指进入详情也不可编辑
    def get_readonly_fields(self, request, obj=None):
        """  重新定义此函数，限制普通用户所能修改的字段  """
        if request.user.is_superuser:
            self.readonly_fields = []
        return self.readonly_fields

    #显示缩略图
    def img_data(self, obj):
        if obj.img and hasattr(obj.img, 'url'):
            if 'http' in obj.img.url:
                return format_html('<img src="{0}" width="150px" height="150px"/>'.format(obj.img))
            else:
                return format_html('<img src="{0}" width="150px" height="150px"/>'.format(obj.img.url))
        else:
            return None
    img_data.short_description = '新闻图片'
    #自定义的action函数
    # 新建一个批量操作的函数，其中有三个参数：
    # 第一个参数是模型管理类，第二个request是请求，第三个queryset表示你选中的所有记录，
    # 这个函数里面会处理所有选中的queryset，所以要在操作之前用搜索或者过滤来选出需要修改的记录
    def del_img(self,request,queryset):
        queryset.update(img=None)
    del_img.short_description = "删除图片"

    def change_priority(self,request,queryset):
        queryset.update(priority=0)
    change_priority.short_description = "优先级调整为0"

    #自定义action
    actions = ["del_img",change_priority]
    #普通用户只可以修改
    readonly_fields = ('comment', 'like')
    # 显示的字段
    list_display = ['title','img_data','time', 'source','priority', 'hidden']
    list_editable = ['priority', 'hidden']
    ordering = ('-time',)
    #每页显示的数量
    list_per_page = 50
    #跳转连接
    list_display_links = ['title', 'time', 'source']
    #设置空值
    empty_value_display ='无'
    #操作选项
    actions_on_top = True
    #过滤器
    list_filter = ['source','time']
    #搜索器
    search_fields = ['title', 'time', 'source','content']
    #跳转字段
    #fields = ['time']
    #分组显示
    fieldsets = (
        ('基本', {'fields': ['title', 'img','time','source']}),
        ('高级', {
            'fields': ['like', 'comment','url','content','author','label'],
            'classes': ('collapse',)  # 是否折叠显示
        })
    )

@admin.register(KX)
class BookInfoAdmin(NewsBaseClass):
    pass
@admin.register(DFKX)
class BookInfoAdmin(NewsBaseClass):
    pass


@admin.register(QGXH)
class BookInfoAdmin(NewsBaseClass):
    pass
@admin.register(TECH)
class BookInfoAdmin(NewsBaseClass):
    pass

@admin.register(News)
class BookInfoAdmin(NewsBaseClass):
    pass
@admin.register(ChinaTopNews)
class BookInfoAdmin(NewsBaseClass):
    pass
@admin.register(AgencyJg)
class BookInfoAdmin(OrgBaseClass):
    pass
@admin.register(AgencyDfkx)
class BookInfoAdmin(OrgBaseClass):
    pass
@admin.register(AgencyQgxh)
class BookInfoAdmin(OrgBaseClass):
    pass



#admin.site.register(KX)
# admin.site.register(News)
# admin.site.register(DFKX)
# admin.site.register(QGXH)
# admin.site.register(TECH)
# admin.site.register(ChinaTopNews)
# admin.site.register(AgencyJg)
# admin.site.register(AgencyDfkx)
# admin.site.register(AgencyQgxh)
# admin.site.register(ChannelToDatabase)
admin.site.site_header = '新闻管理系统'
admin.site.site_title = '新闻管理系统'
admin.site.index_title = '欢迎使用新闻管理系统'