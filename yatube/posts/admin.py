from django.contrib import admin

from .models import Comment, Follow, Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """ Настройки отображения модели Post на странице администрирования."""

    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)
    empty_value_display = '-пусто-'


admin.site.register(Group)
admin.site.register(Follow)
admin.site.register(Comment)
