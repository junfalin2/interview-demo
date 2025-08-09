import traceback
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseServerError
from django_q.tasks import async_task

from blog.models import Articles, User
from blog.services.database import DatabaseService
from blog.services.redis import RedisService
from blog.tasks import update_view_count

# Create your views here.


def index(request):
    """文章列表"""
    artlist = Articles.objects.all()
    context = {"articles_list": artlist}
    return render(request, "blog/index.html", context)


# @params user_id 应该由session 或 jwt 校验后获取
def detail(request, article_id, user_id):
    """文章详情页"""
    # TODO 幂等校验
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
            async_task(
                update_view_count,article_id,user_id, task_name="increment_user_view_and_total_views"
            )
        except Exception as e:
            # TODO 记录日志, 防止数据丢失
            return HttpResponseServerError(e)
    return render(request, "blog/detail.html", {"article": article})


def statistics(request):
    """阅读量相关统计数据"""
    try:
        cache = RedisService()
        data = cache.get_statistics("*", "*")
        return JsonResponse(data)
    except Exception as e:
        traceback.print_exc()
        print("降级处理,直接读取数据库")
        try:
            data = DatabaseService.get_statistics()
            return JsonResponse(data, safe=False)
        except Exception as e:
            # TODO 记录日志
            return HttpResponseServerError(e)
