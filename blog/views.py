import json
import traceback
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseServerError

from blog.models import Articles, UserArticleViews, User
from blog.services.database import DatabaseService
from blog.services.redis import RedisService

# Create your views here.


def index(request):
    """文章列表"""
    artlist = Articles.objects.all()
    context = {"articles_list": artlist}
    return render(request, "blog/index.html", context)


# @params user_id 应该由session 或 jwt 校验后获取
def detail(request, article_id, user_id):
    """文章详情页"""
    article = get_object_or_404(Articles, pk=article_id)
    user = get_object_or_404(User, pk=user_id)
    try:
        cache = RedisService()
        cache.increment_total_views(article_id)
        cache.increment_user_view(user_id, article_id)
    except Exception as e:
        # TODO 完善异常处理
        traceback.print_exc()
        print("降级处理,直接存储数据库")
        try:
            DatabaseService.increment_total_views(article_id)
            DatabaseService.increment_user_view(user_id, article_id)
        except Exception as e:
            # TODO 记录日志, 防止数据丢失
            return HttpResponseServerError(e)
    return render(request, "blog/detail.html", {"article": article})


def statistics(request, article_id, user_id):
    """阅读量相关统计数据"""
    try:
        cache = RedisService()
        data = cache.get_article_stats(article_id, user_id)
        return JsonResponse(data)
    except Exception as e:
        traceback.print_exc()
        print("降级处理,直接读取数据库")
        user = User.objects.get(id=user_id)
        article = get_object_or_404(Articles, pk=article_id)
        record = UserArticleViews.objects.filter(user=user, article=article).first()
        result = {}
        if record:
            result = {
                "total_views": record.article.total_views,
                "unique_visitors": record.article.unique_visitors,
                "user_view_count": record.view_count,
            }
        return JsonResponse(result, safe=False)
