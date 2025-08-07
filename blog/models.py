import uuid
from django.db import models

# Create your models here.

class Articles (models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField("标题",max_length=200)
    content = models.CharField("内容")
    total_views = models.IntegerField("总阅读数",default=0,)
    unique_visitors = models.IntegerField("用户人次",default=0)
    pub_date = models.DateTimeField("发布日期")

    def __str__(self):
        return self.title