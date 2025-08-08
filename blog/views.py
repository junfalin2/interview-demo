from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,HttpResponseServerError

from blog.models import Articles
from blog.services.database import DatabaseService
# Create your views here.


def index(request):
    """文章列表"""
    artlist = Articles.objects.all()
    context = {"articles_list":artlist}
    return render(request,"blog/index.html",context)

# @params user_id 应该由session 或 jwt 校验后获取
def detail(request,article_id,user_id):
    """文章详情页"""
    #TODO 读取缓存
    article = get_object_or_404(Articles, pk=article_id)
    try:
        DatabaseService.increment_total_views(article_id)
        DatabaseService.increment_user_view(user_id,article_id)
        return render(request, "blog/detail.html", {"article": article})
    except Exception as e:
        # TODO 完善异常处理
        return HttpResponseServerError(e)
