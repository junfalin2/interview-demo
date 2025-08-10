from blog.models import (
    Articles,
    UserArticleViews,
    TOTAL_VIEWS_KEY,
    UNIQUE_VISITORS_KEY,
    VIEW_COUNT_KEY,
)
from django.db import transaction, models
import traceback

import logging

from blog.services.database import DatabaseService
from blog.services.redis import RedisService

logger = logging.getLogger(__name__)


def sync_articles_to_db():
    """同步redis统计信息到数据库"""
    try:
        # 文章阅读数
        cache = RedisService()
        with cache.sync_totalview() as data:
            article_ids = data.keys()
            articles = Articles.objects.filter(id__in=article_ids)

            for article in articles:
                article.total_views = (
                    models.F(TOTAL_VIEWS_KEY) + data[article.id]
                )
            Articles.objects.bulk_update(
                articles, [TOTAL_VIEWS_KEY], batch_size=1000
            )
    except Exception as e:
        traceback.print_exc()
        raise e


    try:
        # 用户次数
        cache = RedisService()
        with cache.sync_unique_visitors() as data:
            article_ids = data.keys()
            articles = Articles.objects.filter(id__in=article_ids)

            for article in articles:
                article.unique_visitors = (
                    models.F(UNIQUE_VISITORS_KEY) + data[article.id]
                )
            Articles.objects.bulk_update(
                articles, [UNIQUE_VISITORS_KEY], batch_size=1000
            )
    except Exception as e:
        traceback.print_exc()
        raise e
    

    try:
        # 用户阅读文章次数
        cache = RedisService()
        with cache.sync_view_count() as data:
            to_update = []
            for item in data:
                aid = item["article_id"]
                uid = item["user_id"]
                viewcount = item[VIEW_COUNT_KEY]
                obj, _ = UserArticleViews.objects.get_or_create(
                    user_id=uid, article_id=aid
                )
                obj.view_count = models.F(VIEW_COUNT_KEY) + viewcount
                to_update.append(obj)

            UserArticleViews.objects.bulk_update(
                to_update, [VIEW_COUNT_KEY], batch_size=1000
            )
    except Exception as e:
        traceback.print_exc()
        raise e


def update_view_count(article_id, user_id):
    """增加阅读次数"""
    try:
        DatabaseService.increment_user_view(user_id, article_id)
        DatabaseService.increment_total_views(article_id)
    except Exception as e:
        raise e
