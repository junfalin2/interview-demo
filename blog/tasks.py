from blog.models import (
    Articles,
    UserArticleViews,
    TOTAL_VIEWS_KEY,
    UNIQUE_VISITORS_KEY,
    VIEW_COUNT_KEY,
)
from django.db import transaction, models

import logging

from blog.services.database import DatabaseService
from blog.services.redis import RedisService

logger = logging.getLogger(__name__)


def sync_articles_to_db():
    """同步redis统计信息到数据库"""
    try:
        # 文章阅读数和用户人次
        cache = RedisService()
        data = cache.get_articles_cache("*")
        article_ids = data.keys()
        articles = Articles.objects.filter(id__in=article_ids)

        for article in articles:
            article.total_views = data[article.id][TOTAL_VIEWS_KEY]
            article.unique_visitors = data[article.id][UNIQUE_VISITORS_KEY]

        Articles.objects.bulk_update(
            articles, [TOTAL_VIEWS_KEY, UNIQUE_VISITORS_KEY], batch_size=1000
        )
    except Exception as e:
        raise e

    try:
        # 用户阅读文章次数
        data = cache.get_user_view_count("*")
        to_update = []
        for uid, art_viewcount in data.items():
            for aid, viewcount in art_viewcount.items():
                obj, _ = UserArticleViews.objects.get_or_create(
                    user_id=uid, article_id=aid
                )
                obj.view_count = viewcount
                to_update.append(obj)

        UserArticleViews.objects.bulk_update(
            to_update, [VIEW_COUNT_KEY], batch_size=1000
        )
    except Exception as e:
        raise e


def update_view_count(article_id,user_id):
    """增加阅读次数"""
    try:
        DatabaseService.increment_user_view(user_id, article_id)
        DatabaseService.increment_total_views(article_id)
    except Exception as e:
        raise e