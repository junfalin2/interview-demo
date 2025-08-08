from django.contrib import admin

# Register your models here.
from .models import Articles,User,UserArticleViews

admin.site.register(Articles)
admin.site.register(User)
admin.site.register(UserArticleViews)