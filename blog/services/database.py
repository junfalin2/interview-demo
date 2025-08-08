from blog.models import UserArticleViews, Articles
from django.db import transaction,models


class DatabaseService:
    @classmethod
    def increment_unique_visitors(cls,article_id):
        """增加用户人次"""
        try:
            with transaction.atomic():
                Articles.objects.filter(id=article_id).update(
                    unique_visitors=models.F("unique_visitors") + 1
                )
        except Exception as e:
            raise e

    @classmethod
    def increment_total_views(cls, article_id):
        """增加总阅读量"""
        try:
            with transaction.atomic():
                Articles.objects.filter(id=article_id).update(
                    total_views=models.F("total_views") + 1
                )
        except Exception as e:
            raise e

    @classmethod
    def increment_user_view(cls, user_id, article_id):
        """增加用户阅读某文章次数"""
        try:

            obj, created = UserArticleViews.objects.get_or_create(
                user_id=user_id, article_id=article_id, defaults={"view_count": 1}
            )
            if created:
                # 首次阅读计入文章用户人次
                cls.increment_unique_visitors(article_id)
            else:
                with transaction.atomic():
                    obj.view_count = models.F("view_count") + 1
                    obj.save(update_fields=["view_count"])
        except Exception as e:
            raise e
