import uuid
from django.db import models

# Create your models here.

class Articles (models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField("标题",max_length=200)
    content = models.CharField("内容")
    total_views = models.IntegerField("总阅读数",default=0,)
    unique_visitors = models.IntegerField("用户人次",default=0)
    pub_date = models.DateTimeField("发布日期",auto_now_add=True)

    def __str__(self):
        return self.title

class User (models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField("用户名",max_length=200)

    def __str__(self):
        return self.name

class UserArticleViews (models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Articles, on_delete=models.CASCADE)
    view_count = models.IntegerField("每人对应的阅读次数",default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'article'],
                name='unique_user_article_view'
            )
        ]
        db_table = 'user_article_views'
        indexes = [
            models.Index(fields=['article', 'user']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.name} viewed {self.article.title} {self.view_count} times"