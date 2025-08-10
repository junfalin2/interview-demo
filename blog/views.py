import json
import logging
import traceback
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseServerError
from django_q.tasks import async_task

from blog.exceptions.database import DatabaseError
from blog.exceptions.redis import CacheError
from blog.models import Articles, User
from blog.services.database import DatabaseService
from blog.services.redis import RedisService
from blog.services.worker import Worker
from blog.tasks import update_view_count

# Create your views here.
logger = logging.getLogger("blog")


def index(request):
    """文章列表"""
    artlist = Articles.objects.all()
    context = {"articles_list": artlist}
    return render(request, "blog/index.html", context)


# @params user_id 应该由session 或 jwt 校验后获取
def detail(request, article_id, user_id):
    """文章详情页"""
    # TODO 幂等校验
    article = None

    def _get_article_from_db():
        """从数据库获取文章并转换为字典"""
        article_obj = get_object_or_404(Articles, pk=article_id)
        return {
            "title": article_obj.title,
            "content": article_obj.content,
            "pub_date": article_obj.pub_date.strftime("%Y-%m-%d"),
        }

    try:
        # 尝试从缓存中获取
        cache = RedisService()
        article = cache.get_article_content(article_id)
    except CacheError as e:
        logger.error(f"{e}")

    # 缓存未命中或解析失败：从数据库获取并更新缓存
    if article is None:
        article = _get_article_from_db()
    try:
        cache = RedisService()
        cache.set_article_content(article_id, article)
        cache.increment_total_views(article_id)
        cache.increment_user_view(user_id, article_id)
    except CacheError as e:
        logger.error(f"{article_id}: {e}")
        try:
            # 异步更新数据库
            async_task(
                update_view_count,
                article_id,
                user_id,
                task_name="increment_user_view_and_total_views",
            )
        except Exception as task_e:
            logger.error(f"{article_id}: {task_e}")
            Worker.enqueue(
                "db",
                {
                    "action": "update_view_count",
                    "article_id": article_id,
                    "user_id": user_id,
                },
            )

    return render(request, "blog/detail.html", {"article": article})


def statistics(request):
    """阅读量相关统计数据"""
    data = None
    try:
        cache = RedisService()
        data = cache.get_statistics("*", "*")
    except CacheError as e:
        data = None
        logger.error(f"{e}")
    if data is None:
        try:
            data = DatabaseService.get_statistics()
            return JsonResponse(data)
        except DatabaseError as e:
            # TODO 记录日志
            logger.error(f"{e}")
    return JsonResponse(data)
