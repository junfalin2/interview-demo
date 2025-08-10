from blog.exceptions.database import db_catch
from blog.models import (
    UserArticleViews,
    Articles,
    UNIQUE_VISITORS_KEY,
    TOTAL_VIEWS_KEY,
    VIEW_COUNT_KEY,
)
from django.db import transaction, models


class DatabaseService:
    @classmethod
    @db_catch
    def increment_unique_visitors(cls, article_id):
        """增加用户人次"""
        try:
            with transaction.atomic():
                Articles.objects.filter(id=article_id).update(
                    unique_visitors=models.F(UNIQUE_VISITORS_KEY) + 1
                )
        except Exception as e:
            raise e

    @classmethod
    @db_catch
    def increment_total_views(cls, article_id):
        """增加总阅读量"""
        try:
            with transaction.atomic():
                Articles.objects.filter(id=article_id).update(
                    total_views=models.F(TOTAL_VIEWS_KEY) + 1
                )
        except Exception as e:
            raise e

    @classmethod
    @db_catch
    def increment_user_view(cls, user_id, article_id):
        """增加用户阅读某文章次数"""
        try:

            obj, created = UserArticleViews.objects.get_or_create(
                user_id=user_id, article_id=article_id, defaults={VIEW_COUNT_KEY: 1}
            )
            if created:
                # 首次阅读计入文章用户人次
                cls.increment_unique_visitors(article_id)
            else:
                with transaction.atomic():
                    obj.view_count = models.F(VIEW_COUNT_KEY) + 1
                    obj.save(update_fields=[VIEW_COUNT_KEY])
        except Exception as e:
            raise e

    @classmethod
    @db_catch
    def get_statistics(
        cls,
    ):
        views = UserArticleViews.objects.select_related("user", "article").all()
        # 构造返回数据
        articles = {}
        user_view_count = {}
        for view in views:
            articles[view.article.id] = {
                TOTAL_VIEWS_KEY: view.article.total_views,
                UNIQUE_VISITORS_KEY: view.article.unique_visitors,
            }
            user_view_count.setdefault(view.user.id, {})[
                view.article.id
            ] = view.view_count
        return {
            "articles": articles,
            "user_view_count": user_view_count,
        }
